# -*- coding: utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.event import listen
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from flask_qrcode import QRcode
from flask_mail import Mail

from os import path

from linufy.libs import crypto

app = Flask(__name__)
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
babel = Babel()
mail = Mail()

def create_app():
    app.config.from_pyfile('config.py')

    app.config['VERSION'] = '1.0.0'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['DEFAULT_FOLDER'] = path.abspath(path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = path.join(
    app.config['DEFAULT_FOLDER'], 'uploads')
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'languages'
    app.config['REGION_ABILITIES'] = ['assets.list', 'assets.edit', 'ipam.list', 'ipam.edit', 'regions.list']
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 10, 'pool_recycle': 60, 'pool_pre_ping': True}

    app.config["fd"] = None
    app.config["child_pid"] = None
    app.config["cmd"] = "bash"

    db.init_app(app)
    migrate.init_app(app, db)

    from .models import Configuration, User, create_tables

    login_manager = LoginManager()
    login_manager.blueprint_login_views = {
        'admin': '/login'
    }
    login_manager.init_app(app)

    csrf.init_app(app)

    babel.init_app(app)

    QRcode(app)

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(user_id)

    with app.app_context():
        # init database
        create_tables()

        # blueprint for admin routes
        from .admin import routes as admin_blueprint
        app.register_blueprint(admin_blueprint.admin)

        from .api import routes as api_blueprint
        app.register_blueprint(api_blueprint.api)

        app.config['TEMPLATE'] = 'admin'

        app.config['MAIL_SERVER'] = Configuration.query.filter_by(
            name='mail_host').first().value
        
        app.config['MAIL_PORT'] = Configuration.query.filter_by(
            name='mail_port').first().value
        
        app.config['MAIL_USERNAME'] = Configuration.query.filter_by(
            name='mail_username').first().value
        
        if Configuration.query.filter_by(name='mail_password').first().value != '':
            app.config['MAIL_PASSWORD'] = crypto.decrypt(Configuration.query.filter_by(
            name='mail_password').first().value)
        else:
            app.config['MAIL_PASSWORD'] = None

        if Configuration.query.filter_by(name='mail_secure').first().value == 'TLS':
            app.config['MAIL_USE_TLS'] = True
            app.config['MAIL_USE_SSL'] = False
        elif Configuration.query.filter_by(name='mail_secure').first().value == 'SSL':
            app.config['MAIL_USE_TLS'] = False
            app.config['MAIL_USE_SSL'] = True
        else:
            app.config['MAIL_USE_TLS'] = False
            app.config['MAIL_USE_SSL'] = False
        mail.app = app
        mail.state = mail.init_app(app)

    return app
