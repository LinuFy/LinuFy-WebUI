# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, abort, jsonify
from password_generator import PasswordGenerator

from linufy.libs import password_manager, crypto, roles, validator
from linufy.libs.roles import require_permission
from linufy.models import Role, PasswordManagerGroupRole, object_as_dict
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin


@admin.route('/password_manager')
@login_required
@breadcrumb('Password Manager', root=True)
@require_permission('password_manager.list')
def password_manager_list():
    return render_template('password-manager.html', title_page=gettext("Password Manager"), groups=password_manager.get_all())


@admin.route('/password_manager', methods=['POST'])
@login_required
@require_permission('password_manager.list')
def password_manager_import_from_file():
    if 'file' in request.files:
        password_manager.password.import_from_file(request.files)
    else:
        flash(gettext('Please select a file to import'), 'warning')
    return render_template('password-manager.html', title_page=gettext("Password Manager"), groups=password_manager.get_all())


@admin.route('/password_manager/group/new')
@login_required
@breadcrumb('New')
@require_permission('password_manager.edit')
def password_manager_group_new():
    return render_template('new-password-manager-group.html', title_page=gettext("Password Manager"))


@admin.route('/password_manager/group/new', methods=['POST'])
@login_required
@require_permission('password_manager.edit')
def password_manager_group_new_post():
    name = request.form.get('name')
    description = request.form.get('description')
    new_password_manager_group = password_manager.add(name, description)
    if new_password_manager_group:
        return redirect(url_for('admin.password_manager_group_edit', group_id=new_password_manager_group.id))
    return redirect(url_for('admin.password_manager_group_new'))


@admin.route('/password_manager/group/edit/<group_id>')
@login_required
@breadcrumb('Edition')
@require_permission('password_manager.edit')
def password_manager_group_edit(group_id):
    password_manager_group_roles = Role.query.join(PasswordManagerGroupRole).filter(
        PasswordManagerGroupRole.password_manager_group_id == group_id).all()
    return render_template('edit-password-manager-group.html',
        title_page=gettext("Password Manager"),
        group=password_manager.get(group_id),
        roles=roles.get_all(),
        password_manager_group_roles=password_manager_group_roles)


@admin.route('/password_manager/group/edit/<group_id>', methods=['POST'])
@login_required
@require_permission('password_manager.edit')
def password_manager_group_edit_post(group_id):
    name = request.form.get('name')
    description = request.form.get('description')
    roles_id = request.form.getlist('roles_id')
    password_manager.edit(group_id, name, description, roles_id)
    return redirect(url_for('admin.password_manager_group_edit', group_id=group_id))


@admin.route('/password_manager/group/delete/<group_id>')
@login_required
@require_permission('password_manager.edit')
def password_manager_group_delete(group_id):
    password_manager.delete(group_id)
    return redirect(url_for('admin.password_manager_list'))


@admin.route('/password_manager/group/<group_id>/entry/new')
@login_required
@breadcrumb('New Entry')
@require_permission('password_manager.edit')
def password_manager_new(group_id):
    pwo = PasswordGenerator()
    pwo.minlen = 16
    pwo.maxlen = 32
    return render_template('new-password-manager.html', title_page=gettext("Password Manager"), groups=password_manager.get_all(), default_password=pwo.generate())


@admin.route('/password_manager/group/<group_id>/entry/new', methods=['POST'])
@login_required
@require_permission('password_manager.edit')
def password_manager_new_post(group_id):
    name = request.form.get('name')
    description = request.form.get('description')
    username = request.form.get('username')
    password_type = request.form.get('password_type')
    if password_type == 'ssh_key':
        if validator.is_valid_ssh_private_key(request.form.get('ssh_key')):
            password = request.form.get('ssh_key')
        else:
            flash(gettext('Invalid SSH Private Key format. Please use another.'), 'warning')
            return redirect(url_for('admin.password_manager_new'))
    else:
        password = request.form.get('password')
    url = request.form.get('url')
    new_password_manager = password_manager.password.add(name, description, username, password, url, group_id)
    if new_password_manager:
        return redirect(url_for('admin.password_manager_edit', group_id=group_id, password_id=new_password_manager.id))
    return redirect(url_for('admin.password_manager_new'))


@admin.route('/password_manager/group/<group_id>/entry/edit/<password_id>')
@login_required
@breadcrumb('Edit Entry')
@require_permission('password_manager.edit')
def password_manager_edit(group_id, password_id):
    password = password_manager.password.get(password_id)
    print(password)
    get_group = password_manager.get(group_id)
    if group_id == str(password.group_id) and current_user.organization_id == get_group.organization_id:
        if validator.is_valid_ssh_private_key(crypto.decrypt(password.password)):
            password_type = 'ssh_key'
        else:
            password_type = 'password'
        return render_template('edit-password-manager.html', title_page=gettext("Password Manager"), password_type=password_type, password=password_manager.password.get(password_id), groups=password_manager.get_all())
    return abort(403)


@admin.route('/password_manager/group/<group_id>/entry/edit/<password_id>', methods=['POST'])
@login_required
@require_permission('password_manager.edit')
def password_manager_edit_post(group_id, password_id):
    name = request.form.get('name')
    description = request.form.get('description')
    username = request.form.get('username')
    url = request.form.get('url')
    new_group_id = request.form.get('group_id')
    password = password_manager.password.get(password_id)
    get_group = password_manager.get(group_id)

    password_type = request.form.get('password_type')
    if password_type == 'ssh_key':
        if validator.is_valid_ssh_private_key(request.form.get('ssh_key')) or request.form.get('ssh_key') == '':
            new_password = request.form.get('ssh_key')
        else:
            flash(gettext('Invalid SSH Private Key format. Please use another.'), 'warning')
            return redirect(url_for('admin.password_manager_edit', group_id=group_id, password_id=password_id))
    else:
        new_password = request.form.get('password')

    if get_group.id == password.group_id and current_user.organization_id == get_group.organization_id:

        password_manager.password.edit(password_id, name, description, username, new_password, url, new_group_id)
        return redirect(url_for('admin.password_manager_edit', group_id=group_id, password_id=password_id))
    return abort(403)


@admin.route('/password_manager/group/<group_id>/entry/delete/<password_id>')
@login_required
@require_permission('password_manager.edit')
def password_manager_delete(group_id, password_id):
    password = password_manager.password.get(password_id)
    get_group = password_manager.get(group_id)
    if group_id == str(password.group_id) and current_user.organization_id == get_group.organization_id:
        password_manager.password.delete(password_id)
        return redirect(url_for('admin.password_manager_list'))
    return abort(403)


@admin.route('/password_manager/group/<group_id>/entry/ajax/<password_id>')
@login_required
@require_permission('password_manager.edit')
def password_manager_ajax(group_id, password_id):
    password = password_manager.password.get(password_id)
    get_group = password_manager.get(group_id)
    if group_id == str(password.group_id) and current_user.organization_id == get_group.organization_id:
        return crypto.decrypt(password.password)
    abort(403)


@admin.route('/password_manager/group/<group_id>/ajax')
@login_required
@require_permission('password_manager.edit')
def password_manager_list_ajax(group_id):
    get_group = password_manager.get(group_id)
    if current_user.organization_id == get_group.organization_id:
        passwords = password_manager.password.get_all(group_id)
        result = []
        for password in passwords:
            result.append(object_as_dict(password))
        return jsonify(result)
    abort(403)
