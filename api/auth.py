# -*- coding: utf-8 -*-

import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError
import datetime

from functools import wraps
from flask.views import MethodView
from flask import current_app, request, jsonify
from flask_login import login_user

from linufy.app import csrf
from linufy.models import Region, ApiKey, User
from linufy.api.routes import api


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return {'status': 'error', 'message': 'X-Access-Token is missing in header'}, 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        except InvalidSignatureError:
            return {'status': 'error', 'message': 'Token is invalid'}, 401
        except ExpiredSignatureError:
            return {'status': 'error', 'message': 'Token is expired'}, 401

        try:
            if data['type'] == 'region':
                current_region = Region.query.filter_by(id=data['id']).first()
                if current_region is None:
                    return {'status': 'error', 'message': 'Invalid authentication token'}, 401
                else:
                    login_user(current_region)
            elif data['type'] == 'user':
                current_user = User.query.filter_by(id=data['id']).first()
                if current_user is None:
                    data['role_id'] = current_user.role_id
                    return {'status': 'error', 'message': 'Invalid authentication token'}, 401
                else:
                    login_user(current_user)
            else:
                return {'status': 'error', 'message': 'Token is invalid'}, 401
            return f(*args, **kwargs)
        except:
            if current_app.config['DEBUG'] == True:
                import traceback
                return traceback.print_exc()
            return {'status': 'error', 'message': 'An unknown error has occurred'}, 500
    return decorator


@api.route('/api/auth/', methods=['GET', 'POST'])
@csrf.exempt
def auth_user():
    if request.method == 'GET':
        parameters = request.args
    else:
        parameters = request.get_json(force=True)

    if not 'access_key' in parameters:
        return jsonify({'status': 'error', 'message': 'Access_Key not found in arguments'})
    
    if not 'organization_key' in parameters and not 'secret_key' in parameters:
        return jsonify({'status': 'error', 'message': 'Organization_Key or Secret_Key not found in arguments'})

    token = None

    if 'secret_key' in parameters:
        get_region = Region.query.filter_by(access_key=parameters['access_key'], secret_key=parameters['secret_key']).first()
        if not get_region is None:
            token = jwt.encode({'type': 'region', 'permission': 'full', 'id': str(get_region.id), 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, current_app.config['SECRET_KEY'], algorithm="HS256")
    elif 'organization_key' in parameters:
        get_user_api = ApiKey.query.filter_by(key=parameters['access_key']).first()
        if not get_user_api is None and str(get_user_api.user.organization_id) == parameters['organization_key']:
            token = jwt.encode({'type': 'user', 'permission': get_user_api.permission,  'id': str(get_user_api.user_id), 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    if not token:
        return jsonify({'status': 'error', 'message': 'Authentication failed, please try again'})
    
    return jsonify({'status': 'success', 'token' : token})
