# -*- coding: utf-8 -*-

import json
import uuid
import os

from .rest_client import RestClient


def format_inventory(inventory):
	if inventory:
		for asset in inventory:
			if 'ansible_ssh_private_key_file' in inventory[asset]:
				name = str(uuid.uuid4())
				f = open('/tmp/{}'.format(name), 'w')
				f.write(inventory[asset]['ansible_ssh_private_key_file'])
				f.close()
				os.chmod('/tmp/{}'.format(name), 0o600)
				inventory[asset]['ansible_ssh_private_key_file'] = '/tmp/{}'.format(name)
		inventory = {'all': {'hosts': inventory}}
	return inventory


def get_region_inventory():
	rest_client = RestClient()
	rest_client.auth()

	inventory = rest_client.get('regions/current/inventory')

	if inventory['status'] == 200:
		inventory = json.loads(inventory['data'])
		return format_inventory(inventory)
	else:
		return {'all': {'hosts': {} }}
