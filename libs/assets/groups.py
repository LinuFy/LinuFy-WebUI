# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext

from linufy.models import AssetGroup

from linufy.app import db


def get_all():
    return AssetGroup.query.filter_by(organization_id=current_user.get_organization).all()


def get(assets_group_id):
    return AssetGroup.query.filter_by(id=assets_group_id, organization_id=current_user.get_organization).first()


def add(name, description):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False

    if AssetGroup.query.filter_by(name=name, organization_id=current_user.get_organization).first():
        flash(gettext(
            'This assets group is already exist. Please use another name.'), 'warning')
        return False

    # create a new assets group
    new_assets_group = AssetGroup(name=name, description=description, organization_id=current_user.get_organization)

    # add the new assets group to the database
    db.session.add(new_assets_group)
    db.session.commit()

    flash(gettext('Your assets group has been successfully created.'), 'success')
    return new_assets_group


def edit(assets_group_id, name, description):
    if not name and not description:
        flash(gettext('Please set name and description values'), 'warning')
    else:
        get_assets_group = get(assets_group_id)
        AssetGroup.query.filter_by(id=assets_group_id, organization_id=current_user.get_organization).update(dict(name=name, description=description))
        db.session.commit()
        flash(gettext('Your assets group has been successfully edited.'), 'success')
        return True
    return False


def delete(assets_group_id):
    AssetGroup.query.filter_by(id=assets_group_id, organization_id=current_user.get_organization).delete()
    db.session.commit()
    flash(gettext('Your assets group has been successfully deleted.'), 'success')
    return True