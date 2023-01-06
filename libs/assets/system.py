# -*- coding: utf-8 -*-

from redis import Redis
from rq import Queue
import json

from linufy.models import AssetSystemUser, AssetSystemStorage, AssetSystemInterface, AssetMeta

from linufy.libs import assets, tasks
from linufy.app import db


def reboot(asset_id):
    assets_result = assets.get_ansible_asset(asset_id)
    asset = assets_result[0]
    assets_result = assets_result[1]
    queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
    queue.enqueue(tasks.assets.playbook, 'reboot_server', assets_result)


def poweroff(asset_id):
    assets_result = assets.get_ansible_asset(asset_id)
    asset = assets_result[0]
    assets_result = assets_result[1]
    queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
    queue.enqueue(tasks.assets.playbook, 'poweroff_server', assets_result)


def set_timezone(asset_id, timezone):
    assets_result = assets.get_ansible_asset(asset_id)
    asset = assets_result[0]
    assets_result = assets_result[1]
    queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
    queue.enqueue(tasks.assets.playbook, 'set_timezone', assets_result, {'timezone': timezone})


def set_hostname(asset_id, hostname):
    assets_result = assets.get_ansible_asset(asset_id)
    asset = assets_result[0]
    assets_result = assets_result[1]
    queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
    queue.enqueue(tasks.assets.playbook, 'set_hostname', assets_result, {'hostname': hostname})


def update(asset_id, package):
    assets_result = assets.get_ansible_asset(asset_id)
    asset = assets_result[0]
    assets_result = assets_result[1]
    queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
    queue.enqueue(tasks.assets.playbook, 'update_server', assets_result, {'package': package})


def set_selinux(asset_id, state):
    if state in ['enforcing', 'permissive', 'disabled']:
        assets_result = assets.get_ansible_asset(asset_id)
        asset = assets_result[0]
        assets_result = assets_result[1]
        queue = Queue(asset.ip_address.subnet.region.access_key, connection=Redis(host=asset.ip_address.subnet.region.redis.hostname, port=asset.ip_address.subnet.region.redis.port))
        queue.enqueue(tasks.assets.playbook, 'set_selinux', assets_result, {'state': state})
        return True
    return False


def get_users(asset_id):
    return AssetSystemUser.query.filter_by(asset_id=asset_id).all()


def add_users(asset_id, users):
    AssetSystemUser.query.filter_by(asset_id=asset_id).delete()
    for user in users:
        users[user]
        new_asset_user = AssetSystemUser(asset_id=asset_id, name=user, uid=users[user][1], gid=users[user][2], description=users[user][3], homedir=users[user][4], shell=users[user][5])
        db.session.add(new_asset_user)
    db.session.commit()
    return True


def get_storages(asset_id):
    return AssetSystemStorage.query.filter_by(asset_id=asset_id).all()


def add_storage(asset_id, storage):
    AssetSystemStorage.query.filter_by(asset_id=asset_id).delete()
    for line in storage:
        if not 'Filesystem' in line:
            storage_parsed = line.split()
            new_asset_storage = AssetSystemStorage(asset_id=asset_id, filesystem=storage_parsed[0], mountpoint=storage_parsed[5], available=storage_parsed[1], used=storage_parsed[2])
            db.session.add(new_asset_storage)
    db.session.commit()
    return True


def get_interfaces(asset_id):
    return AssetSystemInterface.query.filter_by(asset_id=asset_id).all()


def add_interfaces(asset_id, interfaces):
    AssetSystemInterface.query.filter_by(asset_id=asset_id).delete()
    for interface in interfaces:
        interface = interface['msg']
        new_asset_interface = AssetSystemInterface(asset_id=asset_id, device=interface['device'], macaddress=interface['macaddress'], mtu=interface['mtu'], active=interface['active'])
        db.session.add(new_asset_interface)
    db.session.commit()
    return True


def get_packages(asset_id):
    packages = AssetMeta.query.filter_by(asset_id=asset_id, name='packages').first().value
    upgradable = AssetMeta.query.filter_by(asset_id=asset_id, name='upgradable_packages').first().value
    if packages:
        packages = json.loads(packages)
    if upgradable:
        upgradable = json.loads(upgradable)
    for package in upgradable:
        package_name = package.split('/')[0]
        if package_name in packages:
            version = package.split(' ')[1]
            packages[package_name][0]['upgradable_version'] = version
    return packages