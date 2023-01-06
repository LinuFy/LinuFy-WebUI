# -*- coding: utf-8 -*-

import csv
from os import path, remove

from flask import flash, request, current_app
from flask_login import current_user
from flask_babel import gettext

from linufy.models import PasswordManager, PasswordManagerGroup

from linufy.libs import password_manager, crypto

from linufy.app import db

def get_all(group_id):
    return PasswordManager.query.filter_by(group_id=group_id).all()


def get(password_id):
    return PasswordManager.query.filter_by(id=password_id).first()


def add(name, description, username, password, url, group_id):
    if name == None or password == None:
        flash(gettext('Please set name and password values'), 'warning')
        return False

    if password_manager.get(group_id) is None:
        flash(gettext(
            'This group is not exist. Please use another name.'), 'warning')
        return False

    password = crypto.encrypt(password)

    # create a new password manager group
    new_password_manager = PasswordManager(name=name, description=description, username=username, password=password, url=url, group_id=group_id)

    # add the new password manager group to the database
    db.session.add(new_password_manager)
    db.session.commit()
    flash(gettext('Your password has been successfully created.'), 'success')
    return new_password_manager


def edit(password_id, name, description, username, password, url, group_id):
    if not name and not description:
        flash(gettext('Please set name and password values'), 'warning')
    else:
        if password is None or password == '':
            PasswordManager.query.filter_by(id=password_id).update(dict(name=name, description=description, username=username, url=url, group_id=group_id))
        else:
            password = crypto.encrypt(password)
            PasswordManager.query.filter_by(id=password_id).update(dict(name=name, description=description, username=username, password=password, url=url, group_id=group_id))
        db.session.commit()
        flash(gettext('Your password has been successfully edited.'), 'success')
        return True
    return False


def delete(password_id):
    PasswordManager.query.filter_by(id=password_id).delete()
    db.session.commit()
    flash(gettext('Your password has been successfully deleted.'), 'success')
    return True


def import_from_file(file):
    file = file['file']
    if file.filename != '':
        extension = file.filename.rsplit('.', 1)[1].lower()
        if extension == 'csv':
            file_path = path.join(current_app.config['UPLOAD_FOLDER'], "import.csv")
            file.save(file_path)
            file.close()

            group = password_manager.add('Import', 'Import from {}'.format(file.filename))

            with open(file_path) as csv_reader:
                csv_reader = csv.DictReader(csv_reader)
                for row in csv_reader:
                    add(row['Name'], row['Description'], row['Username'], row['Password'], row['URL'], group.id)
            remove(file_path)
    return False
