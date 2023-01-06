# -*- coding: utf-8 -*-
"""Module for back-office LinuFy"""

from os import path

from flask_login import login_required
from flask import render_template, current_app, session, redirect, url_for, send_from_directory

from linufy.libs.roles import register_context_processors
from linufy.libs.users import count as users_count
from linufy.libs.regions import count as regions_count
from linufy.libs.assets import count as assets_count

from .routes import admin
from . import organizations
from . import users
from . import configurations
from . import notifications
from . import roles
from . import functions
from . import regions
from . import ipam
from . import password_manager
from . import assets
from . import discovery


register_context_processors()


@admin.route('/')
@admin.route('/index')
@login_required
def index():
    return render_template('index.html', users_count=users_count(), regions_count=regions_count(), assets_count=assets_count())


@admin.app_errorhandler(404)
def page_not_found(error):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@admin.app_errorhandler(403)
def page_forbidden(error):
    # note that we set the 403 status explicitly
    return render_template('403.html'), 403


@admin.route("/lang/<language_code>")
def set_language(language_code):
    if language_code in current_app.config['LANGUAGES']:
        session['lang'] = language_code
    return redirect(url_for('main.index'))


@admin.route('/assets/<filename>')
def assets_img(filename):
    asset_path = path.join(
        current_app.config['DEFAULT_FOLDER'], ("templates/{}/assets/").format(current_app.config['TEMPLATE']) )
    return send_from_directory(asset_path, filename)


@admin.route('/assets/distro/<filename>')
def assets_img_distro(filename):
    asset_path = path.join(
        current_app.config['DEFAULT_FOLDER'], ("templates/{}/assets/distro/").format(current_app.config['TEMPLATE']) )
    if not path.exists(asset_path + filename + ".png"):
        filename = "unknown"
    return send_from_directory(asset_path, filename + ".png")

@admin.route('/uploads/<filename>')
def uploaded_files(filename):
    path = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(path, filename)