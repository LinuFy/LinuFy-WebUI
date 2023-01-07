# -*- coding: utf-8 -*-
""" Module used for manage configurations data"""

from flask_login import login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, current_app

from linufy.libs.roles import require_permission
from linufy.libs import configurations, mail, roles, crypto

from .routes import admin
from linufy.app import app
from linufy.app import mail as flask_mail


@admin.route('/configuration')
@login_required
@require_permission('configuration')
def configurations_edit():
    return render_template('configuration.html', title_page="Configurations", config=configurations.get_all(), roles=roles.get_all(), redis_instances=configurations.get_redis_instances())


@admin.route('/configuration', methods=['POST'])
@login_required
@require_permission('configuration')
def configurations_edit_post():
    for key in request.form:
        if key != 'csrf_token':
            if key == 'mail_host':
                flask_mail.state.server = request.form.get(key)
            elif key == 'mail_port':
                flask_mail.state.port = request.form.get(key)
            elif key == 'mail_username':
                flask_mail.state.username = request.form.get(key)
            elif key == 'mail_password':
                if request.form.get(key) != '':
                    flask_mail.state.password = request.form.get(key)
            elif key == 'mail_secure':
                if request.form.get(key) == 'TLS':
                    flask_mail.state.use_tls = True
                    flask_mail.state.use_ssl = False
                elif request.form.get(key) == 'SSL':
                    flask_mail.state.use_tls = False
                    flask_mail.state.use_ssl = True
                else:
                    flask_mail.state.use_tls = False
                    flask_mail.state.use_ssl = False

            if key != 'mail_password' and request.form.get(key) is not None:
                configurations.edit(key, request.form.get(key))
            elif key == 'mail_password' and request.form.get(key) != '':
                configurations.edit(key, crypto.encrypt( request.form.get(key) ))

    flash('Your configuration has been successfully edited.', 'success')
    return redirect(url_for('admin.configurations_edit'))


@admin.route('/configuration/emailtesting')
@login_required
@require_permission('configuration')
def configurations_mail_test():
    if mail.send_without_action('Test message -- LinuFy', 'This is an email test, your server is ready to send emails.', [ current_user.email ]):
        flash('Test email sent successfully.', 'success')
    else:
        flash('Failed to send email.', 'warning')
    return redirect(url_for('admin.configurations_edit'))


@admin.route('/configuration/redis/new')
@login_required
@require_permission('configuration')
def redis_new_instance():
    return render_template('new-redis-instance.html', title_page=gettext('Redis Configuration'))


@admin.route('/configuration/redis/new', methods=['POST'])
@login_required
@require_permission('configuration')
def redis_new_instance_post():
    name = request.form.get('name')
    description = request.form.get('description')
    hostname = request.form.get('hostname')
    port = request.form.get('port', type=int)

    new_redis_instance = configurations.add_redis_instance(name, description, hostname, port)
    if new_redis_instance:
        flash('Your redis instance has been successfully created.', 'success')
        return redirect(url_for('admin.redis_edit_instance', instance_id=new_redis_instance.id))
    return redirect(url_for('admin.redis_new_instance'))


@admin.route('/configuration/redis/edit/<instance_id>')
@login_required
@require_permission('configuration')
def redis_edit_instance(instance_id):
    return render_template('edit-redis-instance.html', title_page=gettext('Redis Configuration'), redis_instance=configurations.get_redis_instance(instance_id))


@admin.route('/configuration/redis/edit/<instance_id>', methods=['POST'])
@login_required
@require_permission('configuration')
def redis_edit_instance_post(instance_id):
    name = request.form.get('name')
    description = request.form.get('description')
    hostname = request.form.get('hostname')
    port = request.form.get('port', type=int)

    if not configurations.get_redis_instance(instance_id):
        flash(gettext("You cannot edit this redis instance."), 'warning')
    else:
        configurations.edit_redis_instance(instance_id, name, description, hostname, port)
        flash(gettext('Your redis instance has been successfully edited.'), 'success')

    return redirect(url_for('admin.configurations_edit'))


@admin.route('/configuration/redis/delete/<instance_id>')
@login_required
@require_permission('configuration')
def redis_delete_instance(instance_id):
    configurations.delete_redis_instance(instance_id)
    flash(gettext('Your redis instance has been successfully deleted.'), 'success')
    return redirect(url_for('admin.configurations_edit'))
