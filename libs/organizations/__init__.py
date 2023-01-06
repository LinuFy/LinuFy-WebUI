# -*- coding: utf-8 -*-

from flask import flash, session, url_for, request
from flask_babel import gettext
from flask_login import current_user

from linufy.models import Organization, User
from linufy.libs import validator, mail, roles

from linufy.app import db

def get_all():
    return Organization.query.all()


def get(organization_id):
    return Organization.query.filter_by(id=organization_id).first()


def add(name, type_of, email=None):
    if email != None: 
        if not validator.email(email):
            flash(gettext(
                'This e-mail address is not valid. Please use another.'), 'warning')
            return False
        if User.query.filter_by(email=email).first():
            flash(gettext(
                'This email address is already associated with a user. Please use another one.'), 'warning')
            return False

    if Organization.query.filter_by(name=name).first():
        flash(gettext(
            'This organization is already exist. Please use another name.'), 'warning')
        return False

    if not type_of in ['global', 'reseller', 'customer']:
        flash(gettext(
            'This type of organization is not valid. Please use another type of organization.'), 'warning')
        return False

    if User.query.count() == 0:
        type_of = 'global'

    # create a new organization
    new_organization = Organization(name=name, type_of=type_of)

    # add the new organization to the database
    db.session.add(new_organization)
    db.session.commit()

    if email != None: 
        mail.send_with_action(gettext('Register your organization'), gettext('The creation of your organization was initiated by the administrator. Please finalize the creation by clicking on the link below.'), gettext('Create my organization'), '{}{}'.format(request.url_root, url_for('admin.signup_organization', organization_id=new_organization.id, email=email) ), [ email ])


    if User.query.count() == 0:
        new_role = roles.add('Super-Administrators', True, True, new_organization.id)
        abilities = ['54ad1d3d08184085af4cb48b42fd8eb0', #assets.edit
        '9fadeec875974bcdb3f367ae31954a0c', #assets.list
        '34ad1d3d08184085af4cb48b42fd8eb0', #ipam.edit
        '7fadeec875974bcdb3f367ae31954a0c', #ipam.list
        '969e0c103445471886c15f5eb8f52ea1', #password_manager.edit
        '969e0c103445471886c15f5eb8f52eac', #password_manager.list
        'e4e7b07446dc4d16b9f2036a4eb966f3', #regions.edit
        '70a5aff1e4ae4844977278e7d4f85ae1', #regions.list
        'c2fd2319e62e46cd98c4fafd912ef5e7', #roles.edit
        'c2952f1411cd44bba128e811b32a2c5c', #roles.list
        '54ad1d3d01184085af4cb48b42fd9eb0', #users.edit
        '9fadeec875974bcdb3f362ae31954a1c', #users.list
        '1ee1d47275eb4f9f8086de176f6898f9', #configuration
        '9424c4b829a44bf4b537d27bcd6d769f', #organizations.edit
        'fe4afeab515148b885964993b6081adb' #organizations.list
        ]
    else:
        new_role = roles.add('Administrators', True, True, new_organization.id)
        abilities = ['54ad1d3d08184085af4cb48b42fd8eb0', #assets.edit
        '9fadeec875974bcdb3f367ae31954a0c', #assets.list
        '34ad1d3d08184085af4cb48b42fd8eb0', #ipam.edit
        '7fadeec875974bcdb3f367ae31954a0c', #ipam.list
        '969e0c103445471886c15f5eb8f52ea1', #password_manager.edit
        '969e0c103445471886c15f5eb8f52eac', #password_manager.list
        'e4e7b07446dc4d16b9f2036a4eb966f3', #regions.edit
        '70a5aff1e4ae4844977278e7d4f85ae1', #regions.list
        'c2fd2319e62e46cd98c4fafd912ef5e7', #roles.edit
        'c2952f1411cd44bba128e811b32a2c5c', #roles.list
        '54ad1d3d01184085af4cb48b42fd9eb0', #users.edit
        '9fadeec875974bcdb3f362ae31954a1c' #users.list
        ]

    if new_role:
        for ability in abilities:
            roles.add_ability(new_role.id, ability)

    return new_organization


def edit(organization_id, name):
    if not name:
        flash(gettext('Please set name value.'), 'warning')
    else:
        Organization.query.filter_by(id=organization_id).update(dict(name=name))
        db.session.commit()
        flash(gettext('Your organization has been successfully edited.'), 'success')
        return True
    return False


def delete(organization_id):
    flash(gettext('This function is not yet implemented.'), 'warning')
    return False
