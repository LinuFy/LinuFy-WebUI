# -*- coding: utf-8 -*-

from flask import request

from linufy.api.auth import token_required
from linufy.libs.roles import require_permission
from linufy.api.routes import api
from linufy.models import object_as_dict

from linufy.libs import discovery


@api.route('/api/discovery/<discovery_id>')
@token_required
@require_permission('assets.list')
def get_discovery(discovery_id):
	discovery_task = discovery.get(discovery_id)
	if discovery_task:
		return {'status': 200, 'data': object_as_dict(discovery_task)}
	return {'status': 100, 'message': 'This discovery action does not exist.'}, 404


@api.route('/api/discovery/<discovery_id>', methods=['PUT'])
@token_required
@require_permission('assets.list')
def set_discovery(discovery_id):
	status = request.get_json()['status']
	if discovery.set_status(discovery_id, status):
		return {'status': 200, 'data': object_as_dict(discovery.get(discovery_id))}
	return {'status': 100, 'message': 'This discovery action does not exist.'}, 404


@api.route('/api/discovery/<discovery_id>/discovered_asset', methods=['POST'])
@token_required
@require_permission('assets.list')
def set_discovered_asset(discovery_id):
	name = request.get_json()['name']
	ip_address = request.get_json()['ip_address']
	new_discovered_asset = discovery.add_discovered_asset(discovery_id, name, ip_address)
	if new_discovered_asset:
		return {'status': 200, 'data': object_as_dict(new_discovered_asset)}
	return {'status': 100, 'message': 'This new discovered asset cannot be created.'}, 500