# -*- coding: utf-8 -*-

import json

from flask_login import login_required
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash
from pytz import all_timezones

from linufy.libs import assets, regions, password_manager, validator, parser
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin

from .functions import add_schedule_tasks

from linufy.app import db


@admin.route('/assets/groups')
@login_required
@breadcrumb('Assets Groups', root=True)
@require_permission('assets.list')
def assets_groups_list():
    return render_template('assets-groups.html', title_page=gettext("Assets Groups"), assets_groups=assets.groups.get_all())


@admin.route('/assets/groups/new')
@login_required
@breadcrumb('New')
@require_permission('assets.edit')
def assets_group_new():
    return render_template('new-assets-group.html', title_page=gettext("Assets Groups"))


@admin.route('/assets/groups/new', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_group_new_post():
    name = request.form.get('name')
    description = request.form.get('description')
    new_assets_group = assets.groups.add(name, description)
    if new_assets_group:
        return redirect(url_for('admin.assets_group_edit', assets_group_id=new_assets_group.id))
    return redirect(url_for('admin.assets_new'))


@admin.route('/assets/groups/edit/<assets_group_id>')
@login_required
@breadcrumb('Edition')
@require_permission('assets.edit')
def assets_group_edit(assets_group_id):
    return render_template('edit-assets-group.html', title_page=gettext("Assets Group"), assets_group=assets.groups.get(assets_group_id))


@admin.route('/assets/groups/edit/<assets_group_id>', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_group_edit_post(assets_group_id):
    name = request.form.get('name')
    description = request.form.get('description')
    assets.groups.edit(assets_group_id, name, description)
    return redirect(url_for('admin.assets_group_edit', assets_group_id=assets_group_id))


@admin.route('/assets/groups/edit/rule/<assets_group_id>')
@login_required
@breadcrumb('Rule Edition')
@require_permission('assets.edit')
def assets_group_edit_rule(assets_group_id):
    return render_template('edit-rule-assets-group.html', title_page=gettext("Assets Group"))


@admin.route('/assets/groups/edit/rule/<assets_group_id>', methods=['POST'])
@login_required
@breadcrumb('Rule Edition')
@require_permission('assets.edit')
def assets_group_edit_rule_post(assets_group_id):
    name = request.form.get('name')
    description = request.form.get('description')
    rule_type = request.form.get('rule_type')
    if not rule_type in ['region', 'subnet']:
        flash(gettext('This rule type does not exist. Please select another.'), 'warning')
    if rule_type == 'region':
        return render_template('edit-rule-region-assets-group.html', title_page=gettext("Assets Group"), name=name, description=description, rule_type=rule_type, regions=regions.get_all(), groups=password_manager.get_all())
    elif rule_type == 'subnet':
        return render_template('edit-rule-subnet-assets-group.html', title_page=gettext("Assets Group"), name=name, description=description, rule_type=rule_type, regions=regions.get_all(), groups=password_manager.get_all())
    return redirect(url_for('admin.assets_group_edit_rule', assets_group_id=assets_group_id))



@admin.route('/assets/groups/delete/<assets_group_id>')
@login_required
@require_permission('assets.edit')
def assets_group_delete(assets_group_id):
    assets.groups.delete(assets_group_id)
    return redirect(url_for('admin.assets_groups_list'))


@admin.route('/assets')
@login_required
@breadcrumb('Assets', root=True)
@require_permission('assets.list')
def assets_list():
    return render_template('assets.html', title_page=gettext("Assets"), assets=assets.get_all())


@admin.route('/assets/view/<asset_id>')
@login_required
@breadcrumb('View')
@require_permission('assets.edit')
def assets_get(asset_id):
    page=request.args.get('page', type=int, default=1)
    per_page=request.args.get('per_page', type=int, default=100)
    mounted = assets.system.get_storages(asset_id)
    users = assets.system.get_users(asset_id)
    meta = assets.get_meta(asset_id)
    interfaces = assets.system.get_interfaces(asset_id)
    if 'password_manager_id' in meta:
        password = password_manager.password.get(meta['password_manager_id'])
    else:
        password = None
    bandwidth = parser.bandwidth_interfaces(meta['bandwidth_interfaces'])
    return render_template('asset.html', title_page=gettext("Assets"), asset=assets.get(asset_id), meta=meta, process_usage=json.loads(meta['process_usage']), users=users,
        password_manager=password, timezones=all_timezones, mounted=mounted, interfaces=interfaces, bandwidth=bandwidth, groups=password_manager.get_all(), packages=assets.system.get_packages(asset_id) )


@admin.route('/assets/view/<asset_id>', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_get_post(asset_id):
    block =  request.form.get('block')
    if block == 'credential':
        password_manager_group_id = request.form.get('password_manager_group_id')
        password_manager_id = request.form.get('password_manager_id')
        if password_manager.password.get(password_manager_id):
            flash(gettext('New credentials have been set for this asset.'), 'success')
            assets.add_meta(asset_id, 'password_manager_id', password_manager_id)
        else:
            flash(gettext('New credentials have not been set for this asset. Please select another.'), 'warning')
        ssh_port = int(request.form.get('ssh_port'))
        if validator.network_port(ssh_port):
            assets.add_meta(asset_id, 'ssh_port', ssh_port)

        privilege_escalation = request.form.get('privilege_escalation')
        if privilege_escalation == 'True':
            privilege_escalation_password_manager_group_id = request.form.get('privilege_escalation_password_manager_group_id')
            privilege_escalation_password_manager_id = request.form.get('privilege_escalation_password_manager_id')
            if password_manager.password.get(privilege_escalation_password_manager_id):
                assets.add_meta(asset_id, 'privilege_escalation_password_manager_id', privilege_escalation_password_manager_id)

    elif block == 'timezone':
        timezone = request.form.get('timezone')
        assets.system.set_timezone(asset_id, timezone)
        flash(gettext('Updated timezone configuration.'), 'success')
    elif block == 'hostname':
        hostname = request.form.get('hostname')
        assets.system.set_hostname(asset_id, hostname)
        flash(gettext('Updated hostname configuration.'), 'success')
    elif block == 'selinux':
        state = request.form.get('state')
        assets.system.set_selinux(asset_id, state)
        flash(gettext('Updated SELinux configuration.'), 'success')
    return redirect(url_for('admin.assets_get', asset_id=asset_id))


@admin.route('/assets/new')
@login_required
@breadcrumb('New')
@require_permission('assets.edit')
def assets_new():
    return render_template('new-asset.html', title_page=gettext("Assets"), regions=regions.get_all())


@admin.route('/assets/new', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_new_post():
    name = request.form.get('name')
    description = request.form.get('description')
    new_asset = assets.add(name, description)
    if new_asset:
        return redirect(url_for('admin.assets_edit', asset_id=new_asset.id))
    return redirect(url_for('admin.assets_new'))


@admin.route('/assets/delete/<asset_id>')
@login_required
@require_permission('assets.edit')
def assets_delete(asset_id):
    assets.delete(asset_id)
    return redirect(url_for('admin.assets_list'))


@admin.route('/assets/view/<asset_id>/reboot')
@login_required
@breadcrumb('View')
@require_permission('assets.edit')
def assets_reboot(asset_id):
    assets.system.reboot(asset_id)
    flash(gettext('Server restart initiated.'), 'success')
    return redirect(url_for('admin.assets_get', asset_id=asset_id))


@admin.route('/assets/view/<asset_id>/poweroff')
@login_required
@breadcrumb('View')
@require_permission('assets.edit')
def assets_poweroff(asset_id):
    assets.system.poweroff(asset_id)
    flash(gettext('Server poweroff initiated.'), 'success')
    return redirect(url_for('admin.assets_get', asset_id=asset_id))


@admin.route('/assets/view/<asset_id>/update/<package>')
@login_required
@breadcrumb('View')
@require_permission('assets.edit')
def assets_update_package(asset_id, package):
    if package == 'all':
        package = '*'
    assets.system.update(asset_id, package)
    flash(gettext('Server update initiated.'), 'success')
    return redirect(url_for('admin.assets_get', asset_id=asset_id))
