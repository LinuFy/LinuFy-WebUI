# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext
import ipaddress

from linufy.libs import regions, validator

from linufy.models import Subnet, IPAddress

from linufy.app import db

from . import ip_address

def get_all():
    return Subnet.query.filter_by(organization_id=current_user.get_organization).all()


def get_all_by_region(region_id):
    return Subnet.query.filter_by(region_id=region_id, organization_id=current_user.get_organization).all()


def get(subnet_id):
    return Subnet.query.filter_by(id=subnet_id, organization_id=current_user.get_organization).first()


def add(name, description, vlan, subnet, mask, region_id):
    if name == None or vlan == None or subnet == None or mask == None or region_id == None:
        flash(gettext('Please set name and vlan and subnet and mask and region values.'), 'warning')
        return False
    if not regions.get(region_id):
        flash(gettext('This region is not valid. Please set another region.'), 'warning')
        return False
    if Subnet.query.filter_by(name=subnet, mask=mask, region_id=region_id).first():
        flash(gettext(
            'This subnet is already exist in this region. Please set another subnet.'), 'warning')
        return False

    try:
        network = ipaddress.ip_network('{}/{}'.format(subnet, mask))

        if isinstance(network, ipaddress.IPv4Network):
            ip_type = "IPv4"
        elif isinstance(network, ipaddress.IPv6Network):
            ip_type = "IPv6"
    except ValueError:
        flash(gettext('This subnet is not valid IPv4 or IPv6. Please set another subnet.'), 'warning')
        return False

    if not validator.vlan(int(vlan)):
        flash(gettext('This vlan is not valid. Please set another vlan.'), 'warning')
        return False

    # create a new subnet
    new_subnet = Subnet(name=name,
        description=description,
        vlan=vlan,
        subnet=subnet,
        mask=mask,
        ip_type=ip_type,
        region_id=region_id,
        organization_id=current_user.get_organization)

    # add the new region to the database
    db.session.add(new_subnet)
    db.session.commit()
    flash(gettext('Your subnet has been successfully created.'), 'success')
    return new_subnet


def edit(subnet_id, name, description, vlan, subnet, mask, region_id):
    if name == None or vlan == None or subnet == None or mask == None or region_id == None:
        flash(gettext('Please set name and vlan and subnet and mask and region values.'), 'warning')
        return False
    if not regions.get(region_id):
        flash(gettext('This region is not valid. Please set another region.'), 'warning')
        return False

    get_subnet = Subnet.query.filter_by(subnet=subnet, mask=mask, region_id=region_id).first()

    if get_subnet is not None and str(get_subnet.id) != subnet_id:
        flash(gettext(
            'This subnet is already exist in this region. Please set another subnet.'), 'warning')
        return False

    try:
        network = ipaddress.ip_network('{}/{}'.format(subnet, mask))

        if isinstance(network, ipaddress.IPv4Network):
            ip_type = "IPv4"
        elif isinstance(network, ipaddress.IPv6Network):
            ip_type = "IPv6"
    except ValueError:
        flash(gettext('This subnet is not valid IPv4 or IPv6. Please set another subnet.'), 'warning')
        return False

    if not validator.vlan(int(vlan)):
        flash(gettext('This vlan is not valid. Please set another vlan.'), 'warning')
        return False

    Subnet.query.filter_by(id=subnet_id).update(dict(name=name,
        description=description,
        vlan=vlan,
        subnet=subnet,
        mask=mask,
        ip_type=ip_type,
        region_id=region_id))

    db.session.commit()
    flash(gettext('Your subnet has been successfully edited.'), 'success')
    return True


def delete(subnet_id):
    if IPAddress.query.filter_by(subnet_id=subnet_id).first() is not None:
        flash(gettext('Your network contains one or more assets. You cannot delete it.'), 'warning')
        return False
    Subnet.query.filter_by(id=subnet_id, organization_id=current_user.get_organization).delete()
    db.session.commit()
    flash(gettext('Your subnet has been successfully deleted.'), 'success')
    return True