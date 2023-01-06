# -*- coding: utf-8 -*-

from flask import flash
from flask_login import current_user
from flask_babel import gettext
from sqlalchemy.sql import null

from linufy.models import Region, Redis, Discovery, Subnet

from linufy.app import db

from . import tasks


def get_all():
    return Region.query.filter_by(organization_id=current_user.get_organization).all()


def get(region_id):
    return Region.query.filter_by(id=region_id, organization_id=current_user.get_organization).first()


def add(name, description, redis_id):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False
    if Region.query.filter_by(name=name, organization_id=current_user.get_organization).first():
        flash(gettext(
            'This region/site is already exist. Please use another name.'), 'warning')
        return False
    redis_instance = Redis.query.filter_by(id=redis_id).first()
    if not redis_instance:
        flash(gettext(
            'This redis instance does not exist. Please use another redis instance.'), 'warning')
        return False
    if Region.query.filter_by(redis_id=redis_id).count() == redis_instance.db_number:
        flash(gettext(
            'This redis instance no longer has a database available. Please use another redis instance.'), 'warning')
        return False

    redis_db = None

    for i in range(1, redis_instance.db_number):
        if not Region.query.filter_by(redis_id=redis_id, redis_db=i).first():
            redis_db = i
            break

    if redis_db == None:
        flash(gettext(
            'This redis instance no longer has a database available. Please use another redis instance.'), 'warning')
        return False

    # create a new region
    new_region = Region(name=name, description=description, organization_id=current_user.get_organization, redis_id=redis_id, redis_db=redis_db)

    # add the new region to the database
    db.session.add(new_region)
    db.session.commit()
    flash(gettext('Your region/site has been successfully created.'), 'success')
    return new_region


def edit(region_id, name, description):
    if not name and not description:
        flash(gettext('Please set name and description values'), 'warning')
    else:
        Region.query.filter_by(id=region_id, organization_id=current_user.get_organization).update(dict(name=name, description=description))
        db.session.commit()
        flash(gettext('Your region/site has been successfully edited.'), 'success')
        return True
    return False


def delete(region_id):
    if Region.query.filter_by(id=region_id, organization_id=current_user.get_organization).first():
        if Subnet.query.filter_by(region_id=region_id, organization_id=current_user.get_organization).count():
            flash(gettext("You cannot delete this region/site because the subnets are linked. Please remove subnets before delete this region/site."), 'warning')
            return False
        Discovery.query.filter_by(region_id=region_id).update(dict(region_id=null()))
        Region.query.filter_by(id=region_id, organization_id=current_user.get_organization).delete()
        db.session.commit()
        flash(gettext('Your region/site has been successfully deleted.'), 'success')
        return True
    flash(gettext("This region/site does not exist."), 'warning')
    return False


def count():
    return Region.query.filter_by(organization_id=current_user.get_organization).count()