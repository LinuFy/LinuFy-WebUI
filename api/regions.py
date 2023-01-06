# -*- coding: utf-8 -*-

import json

from flask import request
from flask_login import current_user
from sqlalchemy import func

from linufy.api.auth import token_required
from linufy.libs.roles import require_permission
from linufy.api.routes import api
from linufy.models import object_as_dict

from linufy.libs import assets, regions, password_manager, crypto, validator


@api.route('/api/regions/<region_id>/inventory')
@token_required
@require_permission('regions.list')
def get_region_inventory(region_id):
	if region_id == 'current':
		region_id = current_user.id
	if regions.get(region_id):
		assets_result = {}
		for asset in assets.get_by_region(region_id):
			asset_meta = assets.get_meta(asset.id)
			if 'password_manager_id' in asset_meta:
				password = password_manager.password.get(asset_meta['password_manager_id'])
				if validator.is_valid_ssh_private_key(crypto.decrypt(password.password)):
					ansible_method = 'ansible_ssh_private_key_file'
				else:
					ansible_method = 'ansible_password'
			assets_result[str(asset.id)] = {'ansible_port': 22, 'ansible_host': asset.ip_address.ip_address, 'ansible_user': password.username, ansible_method: crypto.decrypt(password.password), 'asset_id': str(asset.id)}
		return {'status': 200, 'data': json.dumps(assets_result)}
	return {'status': 100, 'message': 'This region does not exist.'}, 404
