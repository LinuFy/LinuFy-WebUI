# -*- coding: utf-8 -*-

from flask_login import login_required
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash
from pytz import all_timezones

from linufy.libs import regions, password_manager, discovery, ipam
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin


@admin.route('/assets/discover')
@login_required
@breadcrumb("Discovery")
@require_permission('assets.edit')
def assets_discovery():
    return render_template('discover.html', title_page=gettext("Discovery"), discovery=discovery.get_all())


@admin.route('/assets/discover/<discovery_id>')
@login_required
@breadcrumb("Discovered Assets")
@require_permission('assets.edit')
def discovered_assets(discovery_id):
    return render_template('discovered-assets.html', title_page=gettext("Discovered Assets"), discovery_id=discovery_id, discovered_assets=discovery.get_discovered_assets(discovery_id))


@admin.route('/assets/discover/new')
@login_required
@breadcrumb("Discovery")
@require_permission('assets.edit')
def assets_discovery_new():
    return render_template('new-discover.html', title_page=gettext("Discovery"), regions=regions.get_all())


@admin.route('/assets/discover/new', methods=['POST'])
@login_required
@breadcrumb("Discovery")
@require_permission('assets.edit')
def assets_discovery_new_post():
    region_id = request.form.get('region_id')
    discovery_method = request.form.get('discovery_method')
    if not regions.get(region_id):
        flash(gettext('This region does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    if not discovery_method in ['vcenter', 'esx', 'proxmox', 'aws', 'azure', 'gcp', 'openstack', 'network', 'ldap', 'zabbix']:
        flash(gettext('This method of discovery does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    if discovery_method == 'vcenter':
        return render_template('new-discover-vcenter.html', title_page=gettext("vCenter Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'proxmox':
        return render_template('new-discover-proxmox.html', title_page=gettext("Proxmox Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'aws':
        return render_template('new-discover-aws.html', title_page=gettext("Amazon Web Service Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'azure':
        return render_template('new-discover-azure.html', title_page=gettext("Microsoft Azure Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'gcp':
        return render_template('new-discover-gcp.html', title_page=gettext("Google Cloud Platform Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'gcp':
        return render_template('new-discover-gcp.html', title_page=gettext("Google Cloud Platform Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'openstack':
        return render_template('new-discover-openstack.html', title_page=gettext("Openstack Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'network':
        return render_template('new-discover-network.html', title_page=gettext("Network Discovery"), region_id=region_id)
    elif discovery_method == 'ldap':
        return render_template('new-discover-ldap.html', title_page=gettext("LDAP/Active Directory Discovery"), groups=password_manager.get_all(), region_id=region_id)
    elif discovery_method == 'zabbix':
        return render_template('new-discover-zabbix.html', title_page=gettext("Zabbix Discovery"), groups=password_manager.get_all(), region_id=region_id)


@admin.route('/assets/discover/new/network', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_discovery_new_network_post():
    region_id = request.form.get('region_id')
    discovery_method = request.form.get('discovery_method')
    name = request.form.get('name')
    target = request.form.get('target')
    if discovery_method != "network":
        flash(gettext('This method of discovery does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    discovery.network(region_id, name, target)
    return redirect(url_for('admin.assets_discovery'))


@admin.route('/assets/discover/new/vcenter', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_discovery_new_vcenter_post():
    region_id = request.form.get('region_id')
    discovery_method = request.form.get('discovery_method')
    name = request.form.get('name')
    url = request.form.get('url')
    credential_id = request.form.get('password_manager_id')
    if discovery_method != "vcenter":
        flash(gettext('This method of discovery does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    discovery.vmware(region_id, name, url, credential_id)
    return redirect(url_for('admin.assets_discovery'))


@admin.route('/assets/discover/new/zabbix', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assets_discovery_new_zabbix_post():
    region_id = request.form.get('region_id')
    discovery_method = request.form.get('discovery_method')
    name = request.form.get('name')
    url = request.form.get('url')
    credential_id = request.form.get('password_manager_id')
    if discovery_method != "zabbix":
        flash(gettext('This method of discovery does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    discovery.zabbix(region_id, name, url, credential_id)
    return redirect(url_for('admin.assets_discovery'))


@admin.route('/assets/discover/<discovery_id>/asset/<discovered_asset_id>')
@login_required
@breadcrumb("New discovered asset")
@require_permission('assets.edit')
def discovered_assets_add(discovery_id, discovered_asset_id):
    get_discovery = discovery.get(discovery_id)
    return render_template('discovered-asset-add.html', title_page=gettext("New discovered asset"), subnets=ipam.get_all_by_region(get_discovery.region_id), discovered_asset=discovery.get_discovered_asset(discovery_id, discovered_asset_id))


@admin.route('/assets/discover/<discovery_id>/asset/<discovered_asset_id>', methods=['POST'])
@login_required
@require_permission('assets.edit')
def discovered_assets_add_post(discovery_id, discovered_asset_id):
    get_discovery = discovery.get(discovery_id)
    name = request.form.get('name')
    description = request.form.get('description')
    subnet_id = request.form.get('subnet_id')
    new_asset = discovery.convert_discovered_asset(discovery_id, discovered_asset_id, name, description, subnet_id)
    if new_asset:
        return redirect(url_for('admin.assets_get', asset_id=new_asset.id))
    flash(gettext('This asset cannot be created.'), 'warning')
    return redirect(url_for('admin.discovered_assets_add', discovery_id=discovery_id, discovered_asset_id=discovered_asset_id))