# -*- coding: utf-8 -*-

from flask import redirect, url_for, flash
from flask_babel import gettext
from flask_login import current_user
from redis import Redis
from rq import Queue
from urllib.parse import urlparse

from linufy.libs import tasks, regions, password_manager, crypto, ipam, assets
from linufy.models import Discovery, DiscoveredAsset, Region, User
from linufy.app import db


def get_all():
    return Discovery.query.join(Region).filter(Region.organization_id==current_user.get_organization).all()


def get(discovery_id):
    discovery = Discovery.query.filter_by(id=discovery_id).first()
    if discovery.region.organization_id == current_user.get_organization:
        return discovery
    else:
        return False


def get_discovered_assets(discovery_id):
    if get(discovery_id):
        return DiscoveredAsset.query.filter_by(discovery_id=discovery_id).all()
    return False


def get_discovered_asset(discovery_id, discovered_asset_id):
    if get(discovery_id):
        return DiscoveredAsset.query.filter_by(discovery_id=discovery_id, id=discovered_asset_id).first()
    return False


def add_discovered_asset(discovery_id, name, ip_address):
    if get(discovery_id):
        if not DiscoveredAsset.query.filter_by(name=name).first():
            new_discovered_asset = DiscoveredAsset(discovery_id=discovery_id, name=name, ip_address=ip_address)
            db.session.add(new_discovered_asset)
            db.session.commit()
            return new_discovered_asset
    return False


def convert_discovered_asset(discovery_id, discovered_asset_id, name, description, subnet_id):
    get_new_asset = get_discovered_asset(discovery_id, discovered_asset_id)
    if get_discovered_asset(discovery_id, discovered_asset_id):
        new_ip_address = ipam.ip_address.add(name, description, get_new_asset.ip_address, "used", subnet_id)
        if new_ip_address:
            new_asset = assets.add(name, description, new_ip_address.id)
            DiscoveredAsset.query.filter_by(id=discovered_asset_id).update(dict(status='imported'))
            db.session.commit()
            return new_asset
    return False


def set_status(discovery_id, status):
    if get(discovery_id):
        if status in ['created', 'running', 'success', 'error']:
            Discovery.query.filter_by(id=discovery_id).update(dict(status=status))
            db.session.commit()
            return True
        return False
    else:
        return False


def network(region_id, name, target):
    region = regions.get(region_id)
    if not region:
        flash(gettext('This region does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))
    queue = Queue(connection=Redis(host=region.redis.hostname, port=region.redis.port, db=region.redis_db-1))
    new_discovery = Discovery(name=name, discovery_method='network', region_id=region_id)
    db.session.add(new_discovery)
    db.session.commit()
    if queue.enqueue(tasks.discover.network, new_discovery.id, target):
        flash(gettext('Network discovery scan was sent successfully.'), 'success')
        return True
    else:
        Discovery.query.filter_by(id=new_discovery.id).delete()
        db.session.commit()
    flash(gettext('Network discovery scan was not sent successfully.'), 'warning')
    return False


def vmware(region_id, name, url, credential_id):
    region = regions.get(region_id)
    if not region:
        flash(gettext('This region does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))

    credential = password_manager.password.get(credential_id)
    get_group = password_manager.get(credential.group_id)
    if get_group.organization_id == current_user.get_organization:
        host = urlparse(url).netloc
        queue = Queue(connection=Redis(host=region.redis.hostname, port=region.redis.port, db=region.redis_db-1))
        new_discovery = Discovery(name=name, discovery_method='vcenter', region_id=region_id)
        db.session.add(new_discovery)
        db.session.commit()
        if queue.enqueue(tasks.discover.vmware, new_discovery.id, host, credential.username, crypto.decrypt(credential.password)):
            flash(gettext('VMWare discovery scan was sent successfully.'), 'success')
            return True
        else:
            Discovery.query.filter_by(id=new_discovery.id).delete()
            db.session.commit()
        flash(gettext('VMWare discovery scan was not sent successfully.'), 'warning')
        return False
    else:
        flash(gettext('This credential does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))


def zabbix(region_id, name, url, credential_id):
    region = regions.get(region_id)
    if not region:
        flash(gettext('This region does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))

    credential = password_manager.password.get(credential_id)
    get_group = password_manager.get(credential.group_id)
    if get_group.organization_id == current_user.get_organization:
        queue = Queue(connection=Redis(host=region.redis.hostname, port=region.redis.port, db=region.redis_db-1))
        new_discovery = Discovery(name=name, discovery_method='zabbix', region_id=region_id)
        db.session.add(new_discovery)
        db.session.commit()
        if queue.enqueue(tasks.discover.zabbix, new_discovery.id, url, credential.username, crypto.decrypt(credential.password)):
            flash(gettext('Zabbix discovery scan was sent successfully.'), 'success')
            return True
        else:
            Discovery.query.filter_by(id=new_discovery.id).delete()
            db.session.commit()
        flash(gettext('Zabbix discovery scan was not sent successfully.'), 'warning')
        return False
    else:
        flash(gettext('This credential does not exist. Please select another.'), 'warning')
        return redirect(url_for('admin.assets_discovery_new'))