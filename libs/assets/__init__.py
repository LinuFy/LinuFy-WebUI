# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext

from linufy.models import Asset, AssetMeta, IPAddress, Subnet

from linufy.libs import password_manager, validator, crypto

from linufy.app import db

from . import groups
from . import system


def get_all():
    return Asset.query.filter_by(organization_id=current_user.get_organization).all()


def get(asset_id):
    return Asset.query.filter_by(id=asset_id, organization_id=current_user.get_organization).first()


def get_ansible_asset(asset_id):
    asset = get(asset_id)
    if asset:
        assets_result = {}
        asset_meta = get_meta(asset_id)
        if 'password_manager_id' in asset_meta:
            password = password_manager.password.get(asset_meta['password_manager_id'])
            if validator.is_valid_ssh_private_key(crypto.decrypt(password.password)):
                ansible_method = 'ansible_ssh_private_key_file'
            else:
                ansible_method = 'ansible_password'
        if 'ssh_port' in asset_meta:
            ssh_port = asset_meta['ssh_port']
        else:
            ssh_port = 22
        if ansible_method == 'ansible_password':
            assets_result[str(asset.id)] = {'ansible_port': ssh_port, 'ansible_host': asset.ip_address.ip_address, 'ansible_user': password.username, ansible_method: crypto.decrypt(password.password), 'asset_id': str(asset.id), 'ansible_become_password': crypto.decrypt(password.password)}
        else:
            assets_result[str(asset.id)] = {'ansible_port': ssh_port, 'ansible_host': asset.ip_address.ip_address, 'ansible_user': password.username, ansible_method: crypto.decrypt(password.password), 'asset_id': str(asset.id)}
        return [asset, assets_result]
    return False


def get_by_region(region_id):
    return Asset.query.join(IPAddress).filter(IPAddress.subnet_id == Subnet.id, Subnet.region_id == region_id).all()


def get_meta(asset_id):
    asset = get(asset_id)
    result = {}
    for meta in asset.meta:
        result[meta.name] = meta.value
    return result


def add(name, description, ip_address_id=None):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False
    if Asset.query.filter_by(name=name, organization_id=current_user.get_organization).first():
        flash(gettext(
            'This asset is already exist. Please use another name.'), 'warning')
        return False

    # create a new asset
    new_asset = Asset(name=name, description=description, organization_id=current_user.get_organization, ip_address_id=ip_address_id)

    # add the new asset to the database
    db.session.add(new_asset)
    db.session.commit()
    
    add_meta(new_asset.id, 'last_sync', '')
    add_meta(new_asset.id, 'system', 'unknown')
    
    flash(gettext('Your asset has been successfully created.'), 'success')
    return new_asset


def add_meta(asset_id, name, value):
    if AssetMeta.query.filter_by(asset_id=asset_id, name=name).first():
        new_asset_meta = AssetMeta.query.filter_by(asset_id=asset_id, name=name).update(dict(value=value))
    else:
        new_asset_meta = AssetMeta(asset_id=asset_id, name=name, value=value)
        db.session.add(new_asset_meta)
    db.session.commit()
    return new_asset_meta

def edit(asset_id, name, description):
    if not name and not description:
        flash(gettext('Please set name and description values'), 'warning')
    else:
        get_asset = get(asset_id)
        if get_asset.ip_address_id:
                IPAddress.query.filter_by(id=get_asset.ip_address_id).update(dict(name=name, description=description))
        Asset.query.filter_by(id=asset_id, organization_id=current_user.get_organization).update(dict(name=name, description=description))
        db.session.commit()
        flash(gettext('Your asset has been successfully edited.'), 'success')
        return True
    return False


def delete(asset_id):
    Asset.query.filter_by(id=asset_id, organization_id=current_user.get_organization).delete()
    db.session.commit()
    flash(gettext('Your asset has been successfully deleted.'), 'success')
    return True


def count():
    return Asset.query.filter_by(organization_id=current_user.get_organization).count()
