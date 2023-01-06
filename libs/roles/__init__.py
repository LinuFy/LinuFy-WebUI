# -*- coding: utf-8 -*-

from functools import wraps
from flask import current_app, flash
from flask_babel import gettext
from flask_login import current_user, AnonymousUserMixin
from werkzeug.exceptions import Forbidden

from linufy.models import Role, Ability, RoleAbility, User, Region
from linufy.libs import configurations, organizations
from linufy.app import db


def require_permission(permission):

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            is_allowed = False

            if isinstance(current_user, Region):
                if permission in current_app.config['REGION_ABILITIES']:
                    return func(*args, **kwargs)
                else:
                    return {'status': 'error', 'message': 'Not allowed'}, 403

            if current_user.organization.type_of == "global":
                is_allowed = True

            user_role = current_user.role_id

            abilities = Ability.query.join(RoleAbility).join(Role).filter(
                Role.id == user_role, RoleAbility.role_id == Role.id, Ability.id == RoleAbility.ability_id).all()

            for ability in abilities:
                if ability.name == permission:
                    is_allowed = True
                    break

            if is_allowed:
                return func(*args, **kwargs)
            else:
                raise Forbidden('Not allowed')

        return wrapper
    return decorate


def require_permission_in_template(permission):

    is_allowed = False

    organization = organizations.get(current_user.get_organization)

    if organization.type_of == "global":
        is_allowed = True

    user_role = current_user.role_id

    abilities = Ability.query.join(RoleAbility).join(Role).filter(
        Role.id == user_role, RoleAbility.role_id == Role.id, Ability.id == RoleAbility.ability_id).all()

    for ability in abilities:
        if ability.name == permission:
            is_allowed = True
            break

    return is_allowed


def default_context_processors():
    return {
        'require_permission': require_permission_in_template,
    }


def register_context_processors():
    """Register default context processors to app."""
    current_app.context_processor(default_context_processors)


def get_ability(ability_name):
    return Ability.query.filter_by(name=ability_name).first()


def get_all(organization_id=None):
    if organization_id == None:
        organization_id = current_user.get_organization
    return Role.query.filter_by(organization_id=organization_id).all()


def get_all_abilities():
    return Ability.query.all()


def get_abilities_by_role(role_id):
    abilities = Ability.query.join(RoleAbility).filter(
        RoleAbility.role_id == role_id, Ability.id == RoleAbility.ability_id).all()
    return abilities


def get(role_id):
    if isinstance(current_user, AnonymousUserMixin):
        return Role.query.filter_by(id=role_id).first()
    else:
        return Role.query.filter_by(id=role_id, organization_id=current_user.get_organization).first()


def add(role, protected=False, by_default=False, organization_id=None):
    if not role:
        flash(gettext('This role is empty. Please change role.'), 'warning')
    elif organization_id != None:
        if Role.query.filter_by(role=role, organization_id=organization_id).first():
            flash(gettext('This role is already in use. Please change role.'), 'warning')
            return False

    if organization_id == None:
        organization_id = current_user.get_organization
    new_role = Role(role=role, organization_id=organization_id, protected=protected, by_default=by_default)

    # add the new role to the database
    db.session.add(new_role)
    db.session.commit()

    if new_role:
        flash(gettext('Your role has been successfully created.'), 'success')
        return new_role
    return False


def add_ability(role_id, ability_id):
    data = locals()
    insert = False
    if isinstance(current_user, AnonymousUserMixin):
        insert = True

    if insert == False and role_id != current_user.role_id:
        insert = True

    if insert == True and not RoleAbility.query.filter_by(role_id=data['role_id'], ability_id=data['ability_id']).first():
        new_ability = RoleAbility(role_id=data['role_id'], ability_id=data['ability_id'])
        # add the new role to the database
        db.session.add(new_ability)
        db.session.commit()
        return True
    return False


def edit(role_id, role):
    data = locals()

    get_role = get(data['role_id'])

    user_role = current_user.role_id

    if not data['role']:
        flash(gettext('This role is empty. Please change role.'), 'warning')
    elif get_role is not None and str(get_role.id) != data['role_id']:
        flash(gettext('This role is already in use. Please change role.'), 'warning')
    elif get_role is not None and get_role.id == user_role:
        flash(gettext("You cannot edit your own role."), 'warning')
    else:
        Role.query.filter_by(id=data['role_id']).update(dict(role=data['role']))
        db.session.commit()
        flash(gettext('Your role has been successfully edited.'), 'success')
        return True
    return False


def delete(role_id):
    role = get(role_id)
    if User.query.filter_by(role=role.role).count() != 0:
        flash(gettext('This role is used by users. You can\'t delete it.'), 'warning')
    else:
        RoleAbility.query.filter_by(role_id=role_id, organization_id=current_user.get_organization).delete()
        db.session.commit()        
        Role.query.filter_by(id=role_id).delete()
        db.session.commit()
        flash(gettext('Your role has been successfully deleted.'), 'success')


def delete_ability(role_id, ability_id):
    data = locals()
    get_role = get(data['role_id'])
    user_role = current_user.role_id
    if get_role.id != user_role:
        RoleAbility.query.filter_by(role_id=data['role_id'], ability_id=data['ability_id']).delete()
        db.session.commit()
