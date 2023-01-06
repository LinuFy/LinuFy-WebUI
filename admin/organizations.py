# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, Response, session

from linufy.libs import organizations, configurations
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin


@admin.route('/organization')
@login_required
@breadcrumb('Organization', root=True)
def organization():
    return render_template('organization.html', title_page=gettext("Organization"))


@admin.route('/organizations')
@login_required
@breadcrumb('Organizations', root=True)
@require_permission('organizations.list')
def organizations_list():
    return render_template('organizations.html', title_page=gettext("Organizations"), organizations=organizations.get_all())


@admin.route('/organizations/new')
@login_required
@breadcrumb('New')
@require_permission('organizations.edit')
def organizations_new():
    return render_template('new-organization.html', title_page=gettext("Organizations"))


@admin.route('/organizations/new', methods=['POST'])
@login_required
@require_permission('organizations.edit')
def organizations_new_post():
    name = request.form.get('name')
    type_of = request.form.get('type_of')
    email = request.form.get('email')
    new_organization = organizations.add(name, type_of, email)
    return redirect(url_for('admin.organizations_list'))
    if new_organization:
        return redirect(url_for('admin.organizations_edit', organization_id=new_organization.id))
    return redirect(url_for('admin.organizations_new'))


@admin.route('/organizations/edit/<organization_id>')
@login_required
@breadcrumb('Edition')
@require_permission('organizations.edit')
def organizations_edit(organization_id):
    return render_template('edit-organization.html', title_page=gettext("Organizations"), organization=organizations.get(organization_id))


@admin.route('/organizations/edit/<organization_id>', methods=['POST'])
@login_required
@require_permission('organizations.edit')
def organizations_edit_post(organization_id):
    name = request.form.get('name')
    organizations.edit(organization_id, name)
    return redirect(url_for('admin.organizations_edit', organization_id=organization_id))


@admin.route('/organizations/delete/<organization_id>')
@login_required
@require_permission('regions.edit')
def organizations_delete(organization_id):
    organizations.delete(organization_id)
    return redirect(url_for('admin.organizations_list'))


@admin.route('/organizations/support/<organization_id>')
@login_required
@breadcrumb('Edition')
@require_permission('support')
def organizations_support(organization_id):
    session['in_support'] = True
    session['support_organization_id'] = organization_id
    return redirect(url_for('admin.index'))


@admin.route('/organizations/support/close')
@login_required
@breadcrumb('Edition')
@require_permission('support')
def organizations_close_support():
    if 'in_support' in session:
        del session['in_support']
    if 'support_organization_id' in session:
        del session['support_organization_id']
    return redirect(url_for('admin.organizations_list'))
