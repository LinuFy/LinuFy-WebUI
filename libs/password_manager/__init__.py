# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext

from linufy.models import PasswordManager, PasswordManagerGroup, PasswordManagerGroupRole

from linufy.app import db

from . import password

def get_all():
    return PasswordManagerGroup.query.join(PasswordManagerGroupRole).filter(PasswordManagerGroup.organization_id == current_user.get_organization,
        PasswordManagerGroupRole.password_manager_group_id == PasswordManagerGroup.id,
        PasswordManagerGroupRole.role_id == current_user.role_id).all()


def get(group_id):
    return PasswordManagerGroup.query.join(PasswordManagerGroupRole).filter(PasswordManagerGroup.id == group_id, PasswordManagerGroup.organization_id == current_user.get_organization,
        PasswordManagerGroupRole.password_manager_group_id == PasswordManagerGroup.id,
        PasswordManagerGroupRole.role_id == current_user.role_id).first()


def add(name, description):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False
    if PasswordManagerGroup.query.filter_by(name=name, organization_id=current_user.get_organization).first():
        flash(gettext(
            'This group is already exist. Please use another name.'), 'warning')
        return False

    # create a new password manager group
    new_password_manager_group = PasswordManagerGroup(name=name, description=description, organization_id=current_user.get_organization)
    db.session.add(new_password_manager_group)

    db.session.commit()

    # create a new password manager group role
    new_password_manager_group_role = PasswordManagerGroupRole(role_id=current_user.role_id, password_manager_group_id=new_password_manager_group.id)
    db.session.add(new_password_manager_group_role)

    db.session.commit()
    flash(gettext('Your group has been successfully created.'), 'success')
    return new_password_manager_group


def edit(group_id, name, description, roles_id):
    if not get(group_id):
        flash(gettext('This group password manager is not created'), 'warning')
    elif not name and not description:
        flash(gettext('Please set name and description values'), 'warning')
    else:
        PasswordManagerGroup.query.filter_by(id=group_id, organization_id=current_user.get_organization).update(dict(name=name, description=description))

        PasswordManagerGroupRole.query.filter_by(password_manager_group_id=group_id).delete()

        for role_id in roles_id:
            new_password_manager_group_role = PasswordManagerGroupRole(role_id=role_id, password_manager_group_id=group_id)
            db.session.add(new_password_manager_group_role)

        db.session.commit()
        flash(gettext('Your group has been successfully edited.'), 'success')
        return True
    return False


def delete(group_id):
    if PasswordManager.query.filter_by(group_id=group_id).first() is not None:
        flash(gettext('Your group one or more passwords. You cannot delete it.'), 'warning')
        return False
    PasswordManagerGroupRole.query.filter_by(password_manager_group_id=group_id).delete()
    PasswordManagerGroup.query.filter_by(id=group_id, organization_id=current_user.get_organization).delete()
    db.session.commit()
    flash(gettext('Your group has been successfully deleted.'), 'success')
    return True
