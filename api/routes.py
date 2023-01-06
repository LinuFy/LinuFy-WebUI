# -*- coding: utf-8 -*-
""" Route module used for initialize blueprint API instance"""

from flask import Blueprint
from linufy.app import csrf

api = Blueprint('api', __name__)
csrf.exempt(api)