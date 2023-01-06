# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_paginate import Pagination

from linufy.libs import ipam, regions, assets, breadcrumb
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb
from linufy.models import object_as_dict

from .routes import admin


@admin.route('/subnets')
@login_required
@breadcrumb('IP Address Management', root=True)
@require_permission('ipam.list')
def ipam_subnet_list():
    return render_template('subnets.html', title_page=gettext("IP Address Management"), subnets=ipam.get_all())


@admin.route('/subnets/new')
@login_required
@breadcrumb('New')
@require_permission('ipam.edit')
def ipam_subnet_new():
    return render_template('new-subnet.html', title_page=gettext("IP Address Management"), regions=regions.get_all())


@admin.route('/subnets/new', methods=['POST'])
@login_required
@require_permission('ipam.edit')
def ipam_subnet_new_post():
    name = request.form.get('name')
    description = request.form.get('description')
    vlan = request.form.get('vlan')
    subnet = request.form.get('subnet')
    mask = request.form.get('mask')
    region_id = request.form.get('region_id')
    new_subnet = ipam.add(name, description, vlan, subnet, mask, region_id)
    if new_subnet:
        return redirect(url_for('admin.ipam_subnet_edit', subnet_id=new_subnet.id))
    return redirect(url_for('admin.ipam_subnet_list'))


@admin.route('/subnets/edit/<subnet_id>')
@login_required
@breadcrumb('Edition')
@require_permission('ipam.edit')
def ipam_subnet_edit(subnet_id):
    return render_template('edit-subnet.html', title_page=gettext("IP Address Management"), subnet=ipam.get(subnet_id), regions=regions.get_all())


@admin.route('/subnets/edit/<subnet_id>', methods=['POST'])
@login_required
@require_permission('ipam.edit')
def ipam_subnet_edit_post(subnet_id):
    name = request.form.get('name')
    description = request.form.get('description')
    vlan = request.form.get('vlan')
    subnet = request.form.get('subnet')
    mask = request.form.get('mask')
    region_id = request.form.get('region_id')
    ipam.edit(subnet_id, name, description, vlan, subnet, mask, region_id)
    return redirect(url_for('admin.ipam_subnet_edit', subnet_id=subnet_id))


@admin.route('/subnets/delete/<subnet_id>')
@login_required
@require_permission('ipam.edit')
def ipam_subnet_delete(subnet_id):
    ipam.delete(subnet_id)
    return redirect(url_for('admin.ipam_subnet_list'))


@admin.route('/subnets/<subnet_id>/ip_addresses')
@login_required
@breadcrumb('IP Addresses')
@require_permission('ipam.list')
def ipam_ip_address_list(subnet_id):
    page=request.args.get('page', type=int, default=1)
    per_page=request.args.get('per_page', type=int, default=100)
    ip_addresses = ipam.ip_address.get_all(subnet_id, page=page, per_page=per_page)
    pages = Pagination(page=page,
        per_page=per_page,
        total=ipam.ip_address.count(subnet_id),
        record_name=gettext('IP addresses'),
        display_msg='<p class="text-right mt-3">' + gettext("<b>{start} - {end}</b> {record_name} of <b>{total}</b>") + '</p>',
        alignment='right')
    return render_template('ip-addresses.html', title_page=gettext("IP Address Management"), subnet_id=subnet_id, ip_addresses=ip_addresses, pages=pages)


@admin.route('/subnets/<subnet_id>/ip_addresses/new')
@login_required
@breadcrumb('New')
@require_permission('ipam.edit')
def ipam_ip_address_new(subnet_id):
    return render_template('new-ip-address.html', title_page=gettext("IP Address Management"))


@admin.route('/subnets/<subnet_id>/ip_addresses/new', methods=['POST'])
@login_required
@require_permission('ipam.edit')
def ipam_ip_address_new_post(subnet_id):
    name = request.form.get('name')
    description = request.form.get('description')
    ip_address = request.form.get('ip_address')
    status = request.form.get('status')
    create_asset = request.form.get('create_asset')
    new_ip_address = ipam.ip_address.add(name, description, ip_address, status, subnet_id)
    if new_ip_address:
        if create_asset:
            assets.add(name, description, new_ip_address.id)
        return redirect(url_for('admin.ipam_ip_address_edit', subnet_id=subnet_id, ip_address_id=new_ip_address.id))
    return redirect(url_for('admin.ipam_ip_address_list', subnet_id=subnet_id))


@admin.route('/subnets/<subnet_id>/ip_addresses/edit/<ip_address_id>')
@login_required
@breadcrumb('Edition')
@require_permission('ipam.edit')
def ipam_ip_address_edit(subnet_id, ip_address_id):
    return render_template('edit-ip-address.html', title_page=gettext("IP Address Management"), subnet_id=subnet_id, ip_address=ipam.ip_address.get(subnet_id, ip_address_id))


@admin.route('/subnets/<subnet_id>/ip_addresses/edit/<ip_address_id>', methods=['POST'])
@login_required
@require_permission('ipam.edit')
def ipam_ip_address_edit_post(subnet_id, ip_address_id):
    name = request.form.get('name')
    description = request.form.get('description')
    ip_address = request.form.get('ip_address')
    status = request.form.get('status')
    ipam.ip_address.edit(ip_address_id, name, description, ip_address, status, subnet_id)
    return redirect(url_for('admin.ipam_ip_address_edit', subnet_id=subnet_id, ip_address_id=ip_address_id))


@admin.route('/subnets/<subnet_id>/ip_addresses/delete/<ip_address_id>')
@login_required
@require_permission('ipam.edit')
def ipam_ip_address_delete(subnet_id, ip_address_id):
    ipam.ip_address.delete(subnet_id, ip_address_id)
    return redirect(url_for('admin.ipam_ip_address_list', subnet_id=subnet_id))

@admin.route('/regions/subnets/<region_id>/ajax')
@login_required
@require_permission('password_manager.edit')
def ipam_subnet_list_ajax(region_id):
    get_region = regions.get(region_id)
    if current_user.organization_id == get_region.organization_id:
        subnets = ipam.get_all_by_region(region_id)
        result = []
        for subnet in subnets:
            print(subnet)
            result.append(object_as_dict(subnet))
        return jsonify(result)
    abort(403)