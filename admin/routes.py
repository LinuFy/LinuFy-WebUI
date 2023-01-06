# -*- coding: utf-8 -*-
""" Route module used for initialize blueprint admin instance"""

from os import path
from flask import Blueprint, current_app

admin = Blueprint('admin', __name__, template_folder=path.join(
    current_app.config['DEFAULT_FOLDER'], "templates/admin"))
