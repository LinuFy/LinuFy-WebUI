# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, Response

from linufy.libs import regions, configurations
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin


@admin.route('/regions')
@login_required
@breadcrumb('Regions/Sites', root=True)
@require_permission('regions.list')
def regions_list():
    return render_template('regions.html', title_page=gettext("Regions/Sites"), regions=regions.get_all())


@admin.route('/regions/new')
@login_required
@breadcrumb('New')
@require_permission('regions.edit')
def regions_new():
    return render_template('new-region.html', title_page=gettext("Regions/Sites"), redis_instances=configurations.get_redis_instances())


@admin.route('/regions/new', methods=['POST'])
@login_required
@require_permission('regions.edit')
def regions_new_post():
    name = request.form.get('name')
    description = request.form.get('description')
    redis_id = request.form.get('instance_id')
    new_region = regions.add(name, description, redis_id)
    if new_region:
        return redirect(url_for('admin.regions_edit', region_id=new_region.id))
    return redirect(url_for('admin.regions_new'))


@admin.route('/regions/edit/<region_id>')
@login_required
@breadcrumb('Edition')
@require_permission('regions.edit')
def regions_edit(region_id):
    return render_template('edit-region.html', title_page=gettext("Regions/Sites"), region=regions.get(region_id))


@admin.route('/regions/edit/<region_id>', methods=['POST'])
@login_required
@require_permission('regions.edit')
def regions_edit_post(region_id):
    name = request.form.get('name')
    description = request.form.get('description')
    regions.edit(region_id, name, description)
    return redirect(url_for('admin.regions_edit', region_id=region_id))


@admin.route('/regions/delete/<region_id>')
@login_required
@require_permission('regions.edit')
def regions_delete(region_id):
    regions.delete(region_id)
    return redirect(url_for('admin.regions_list'))


@admin.route('/regions/download/config/<region_id>')
@login_required
@require_permission('regions.edit')
def regions_download_config(region_id):
    get_region = regions.get(region_id)
    generator = """[config]
ACCESS_KEY = {}
SECRET_KEY = {}""".format(get_region.access_key, get_region.secret_key)

    return Response(generator,
        mimetype="text/plain",
        headers={"Content-Disposition":
            "attachment;filename=region.conf"})