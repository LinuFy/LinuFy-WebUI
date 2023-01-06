# -*- coding: utf-8 -*-

from flask import request
from sqlalchemy import func

from linufy.api.auth import token_required
from linufy.libs.roles import require_permission
from linufy.api.routes import api
from linufy.models import object_as_dict

from linufy.libs import assets


@api.route('/api/assets/<asset_id>')
@token_required
@require_permission('assets.list')
def get_asset(asset_id):
	get_asset = assets.get(asset_id)
	if get_asset:
		return {'status': 200, 'data': object_as_dict(get_asset)}
	return {'status': 100, 'message': 'This asset does not exist.'}, 404


@api.route('/api/assets/<asset_id>/meta', methods=['PUT'])
@token_required
@require_permission('assets.edit')
def set_asset(asset_id):
	if assets.get(asset_id):
		for key in request.get_json():
			assets.add_meta(asset_id, key, request.get_json()[key])
		assets.add_meta(asset_id, 'last_sync', func.now())
		return {'status': 200, 'data': object_as_dict(assets.get(asset_id))}
	return {'status': 100, 'message': 'This asset does not exist.'}, 404


@api.route('/api/assets/<asset_id>/users', methods=['PUT'])
@token_required
@require_permission('assets.edit')
def set_users_asset(asset_id):
	assets.system.add_users(asset_id, request.get_json())
	return {'status': 200, 'data': object_as_dict(assets.get(asset_id))}


@api.route('/api/assets/<asset_id>/storage', methods=['PUT'])
@token_required
@require_permission('assets.edit')
def set_storage_asset(asset_id):
	assets.system.add_storage(asset_id, request.get_json())
	return {'status': 200, 'data': object_as_dict(assets.get(asset_id))}


@api.route('/api/assets/<asset_id>/interfaces', methods=['PUT'])
@token_required
@require_permission('assets.edit')
def set_interfaces_asset(asset_id):
	assets.system.add_interfaces(asset_id, request.get_json())
	return {'status': 200, 'data': object_as_dict(assets.get(asset_id))}