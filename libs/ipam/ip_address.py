# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext
from sqlalchemy.sql import null

from linufy.libs import ipam, validator
import ipaddress

from linufy.models import Subnet, IPAddress, Asset

from linufy.app import db

def get_all(subnet_id, page=1, per_page=50):
    subnet = ipam.get(subnet_id)
    ip_network = ipaddress.ip_network('{}/{}'.format(subnet.subnet, subnet.mask))

    ip_addresses = dict()
    
    if isinstance(ip_network, ipaddress.IPv4Network):
        if page == 1:
            network = int(ip_network.network_address)
        else:
            page = page-1
            network = int(ip_network.network_address) + (page * per_page)

        broadcast = int(ip_network.broadcast_address)
        if broadcast > ( network + (page * per_page) ):
            broadcast = ( network + (page * per_page) ) + 1

        for x in range(network + 1, broadcast):
            ip_address = str(ip_network._address_class(x))
            ip_addresses[ip_address] = {'ip_address': ip_address, 'reserved': False, 'used': False, 'gateway': False, 'name': '-', 'description': '-'}

    elif isinstance(ip_network, ipaddress.IPv6Network):
        if page == 1:
            network = int(ip_network.network_address)
        else:
            page = page-1
            network = int(ip_network.network_address) + (page * per_page)

        broadcast = int(ip_network.broadcast_address)
        if broadcast > ( network + (page * per_page) ):
            broadcast = ( network + (page * per_page) ) + 1

        for x in range(network + 1, broadcast + 1):
            ip_address = str(ip_network._address_class(x))
            ip_addresses[ip_address] = {'ip_address': ip_address, 'reserved': False, 'used': False, 'gateway': False, 'name': '-', 'description': '-'}
    
    used_ip_addresses = IPAddress.query.filter_by(subnet_id=subnet_id).all()
    if len(used_ip_addresses) != 0:
        for used_ip_address in used_ip_addresses:
            if used_ip_address.ip_address in ip_addresses:
                ip_addresses[used_ip_address.ip_address] = {'ip_address': str(used_ip_address.ip_address),
                'reserved': used_ip_address.reserved,
                'used': used_ip_address.used,
                'name': used_ip_address.name,
                'description': used_ip_address.description,
                'id': used_ip_address.id}
    return list(ip_addresses.values())


def get(subnet_id, ip_address_id):
    return IPAddress.query.filter_by(id=ip_address_id, subnet_id=subnet_id).first()


def add(name, description, ip_address, status, subnet_id):
    if name == None or ip_address == None or (status == None or status not in ['reserved', 'used', 'gateway']) or subnet_id == None:
        flash(gettext('Please set name and ip_address and status values.'), 'warning')
        return False

    subnet = ipam.get(subnet_id)

    if not subnet:
        flash(gettext('This subnet is not valid. Please set another region.'), 'warning')
        return False
    if IPAddress.query.filter_by(ip_address=ip_address, subnet_id=subnet_id).first():
        flash(gettext(
            'This IP address is already exist in this subnet. Please set another IP address.'), 'warning')
        return False

    try:
        ip = ipaddress.ip_address(ip_address)

        if isinstance(ip, ipaddress.IPv4Address):
            ip_type = "IPv4"
        elif isinstance(ip, ipaddress.IPv6Address):
            ip_type = "IPv6"
    except ValueError:
        flash(gettext('This IP address is not valid IPv4 or IPv6. Please set another IP address.'), 'warning')
        return False

    if ip_type != subnet.ip_type or ipaddress.ip_address(ip_address) not in ipaddress.ip_network('{}/{}'.format(subnet.subnet, subnet.mask)):
        flash(gettext('This IP address is not valid in this subnet. Please set another IP address.'), 'warning')
        return False

    if status == 'gateway':
        used = True
        reserved = False
    elif status == 'used':
        used = True
        reserved = False
    elif status == 'reserved':
        used = False
        reserved = True

    # create a new ip address
    new_ip_address = IPAddress(name=name,
        description=description,
        ip_address=ip_address,
        used=used,
        reserved=reserved,
        subnet_id=subnet_id)

    # add the new ip address to the database
    db.session.add(new_ip_address)
    db.session.commit()
    
    if status == 'gateway':
        Subnet.query.filter_by(id=subnet_id).update(dict(gateway_id=new_ip_address.id))
    
    db.session.commit()
    
    flash(gettext('Your IP address has been successfully created.'), 'success')
    return new_ip_address


def edit(ip_address_id, name, description, ip_address, status, subnet_id):
    if name == None or ip_address == None or (status == None or status not in ['reserved', 'used', 'gateway']):
        flash(gettext('Please set name and ip_address and status values.'), 'warning')
        return False

    subnet = ipam.get(subnet_id)

    get_ip_address = IPAddress.query.filter_by(ip_address=ip_address, subnet_id=subnet_id).first()

    if get_ip_address is not None and str(get_ip_address.id) != ip_address_id:
        flash(gettext(
            'This IP address is already exist in this subnet. Please set another IP address.'), 'warning')
        return False

    try:
        ip = ipaddress.ip_address(ip_address)

        if isinstance(ip, ipaddress.IPv4Address):
            ip_type = "IPv4"
        elif isinstance(ip, ipaddress.IPv6Address):
            ip_type = "IPv6"
    except ValueError:
        flash(gettext('This IP address is not valid IPv4 or IPv6. Please set another IP address.'), 'warning')
        return False

    if ip_type != subnet.ip_type or ipaddress.ip_address(ip_address) not in ipaddress.ip_network('{}/{}'.format(subnet.subnet, subnet.mask)):
        flash(gettext('This IP address is not valid in this subnet. Please set another IP address.'), 'warning')
        return False

    if status == 'gateway':
        used = True
        gateway = True
        reserved = False
    elif status == 'used':
        used = True
        gateway = False
        reserved = False
    elif status == 'reserved':
        used = False
        gateway = False
        reserved = True

    IPAddress.query.filter_by(id=ip_address_id).update(dict(name=name,
        description=description,
        ip_address=ip_address,
        used=used,
        reserved=reserved))

    if gateway == True:
        Subnet.query.filter_by(id=subnet_id).update(dict(gateway_id=ip_address_id))

    Asset.query.filter_by(ip_address_id=ip_address_id, organization_id=current_user.get_organization).update(dict(name=name, description=description))
    
    db.session.commit()
    flash(gettext('Your IP address has been successfully edited.'), 'success')
    return True


def delete(subnet_id, ip_address_id):
    subnet = ipam.get(subnet_id)
    if str(subnet.gateway_id) == ip_address_id:
        Subnet.query.filter_by(id=subnet_id).update(dict(gateway_id=null()))
    IPAddress.query.filter_by(subnet_id=subnet_id, id=ip_address_id).delete()
    db.session.commit()
    flash(gettext('Your IP address has been successfully deleted.'), 'success')
    return True


def count(subnet_id):
    subnet = ipam.get(subnet_id)
    ip_network = ipaddress.ip_network('{}/{}'.format(subnet.subnet, subnet.mask))

    if isinstance(ip_network, ipaddress.IPv4Network):
        network = int(ip_network.network_address) + 1
        broadcast = int(ip_network.broadcast_address)
        return broadcast - network
    elif isinstance(ip_network, ipaddress.IPv6Network):
        network = int(ip_network.network_address)
        broadcast = int(ip_network.broadcast_address)
        return broadcast - network
    else:
        return 0