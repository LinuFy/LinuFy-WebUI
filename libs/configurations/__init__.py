# -*- coding: utf-8 -*-

from collections import namedtuple
from sqlalchemy.exc import PendingRollbackError
from flask import flash
from flask_babel import gettext

from linufy.app import db
from linufy.models import Configuration, Redis
from linufy.libs import validator


def get_all():
    config = {}
    try:
        configurations = Configuration.query.all()
    except PendingRollbackError:
        db.session.rollback()
        configurations = Configuration.query.all()
    for configuration in configurations:
        config[configuration.name] = configuration.value
    return namedtuple("Configuration", config.keys())(*config.values())


def get(name):
    try:
        return Configuration.query.filter_by(name=name).first()
    except:
        return {"name": name, "value": "False"}


def add(name, value):
    data = locals()
    new_configuration = Configuration(name=data['name'], value=data['value'])
    db.session.add(new_configuration)
    db.session.commit()
    return new_configuration


def edit(name, value):
    data = locals()
    Configuration.query.filter_by(
        name=data['name']).update(dict(value=data['value']))
    db.session.commit()
    return True


def delete(name):
    Configuration.query.filter_by(name=name).delete()
    db.session.commit()
    return True


def get_redis_instances():
    return Redis.query.all()


def get_redis_instance(instance_id):
    return Redis.query.filter_by(id=instance_id).first()


def add_redis_instance(name, description, hostname, port, db_number):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False

    if not validator.network_port(port):
        flash(gettext('Port is invalid'), 'warning')
        return False

    if not isinstance(db_number, int):
        flash(gettext('Number of DB is invalid'), 'warning')
        return False

    new_redis_instance = Redis(name=name, description=description, hostname=hostname, port=port, db_number=db_number)
    db.session.add(new_redis_instance)
    db.session.commit()
    return new_redis_instance


def edit_redis_instance(instance_id, name, description, hostname, port, db_number):
    if name == None or description == None:
        flash(gettext('Please set name and description values'), 'warning')
        return False

    if not validator.network_port(port):
        flash(gettext('Port is invalid'), 'warning')
        return False

    if not isinstance(db_number, int):
        flash(gettext('Number of DB is invalid'), 'warning')
        return False

    Redis.query.filter_by(
        id=instance_id).update(dict(name=name, description=description, hostname=hostname, port=port, db_number=db_number))
    db.session.commit()
    return True


def delete_redis_instance(instance_id):
    Redis.query.filter_by(id=instance_id).delete()
    db.session.commit()
    return True