# -*- coding: utf-8 -*-

import os
from distutils.util import strtobool
import requests
import json

import nmap3
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from .rest_client import RestClient

def network(new_discovery_id, subnet):
	rest_client = RestClient()
	rest_client.auth()

	rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'running'})

	nmap = nmap3.Nmap()

	result = nmap.nmap_subnet_scan(subnet)

	for discovered_asset in result:
		if 'state' in result[discovered_asset]:
			if result[discovered_asset]['state']['state'] == 'up':
				rest_client.post('discovery/{}/discovered_asset'.format(new_discovery_id, ), {'name': result[discovered_asset]['hostname'][0]['name'], 'ip_address': discovered_asset})

	rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'success'})

	return True


def vmware(new_discovery_id, host, user, password):
	rest_client = RestClient()
	rest_client.auth()

	rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'running'})

	try:
		if strtobool(os.environ['ALLOW_UNSAFE_SSL']) == True:
			service_instance = SmartConnect(host=host, user=user, pwd=password, disableSslCertValidation=True)
		else:
			service_instance = SmartConnect(host=host, user=user, pwd=password)
		
		content = service_instance.RetrieveContent()

		container = content.rootFolder  # starting point to look into
		view_type = [vim.VirtualMachine]  # object types to look for
		recursive = True  # whether we should look into it recursively
		container_view = content.viewManager.CreateContainerView(
			container, view_type, recursive)

		children = container_view.view

		for child in children:
			summary = child.summary
			if summary.guest is not None:
				ip_address = summary.guest.ipAddress
				if ip_address:
					rest_client.post('discovery/{}/discovered_asset'.format(new_discovery_id, ), {'name': summary.config.name, 'ip_address': ip_address})

		rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'success'})
		return True
	except:
		rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'error'})
		return False


def zabbix(new_discovery_id, host, user, password):
	rest_client = RestClient()
	rest_client.auth()

	rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'running'})

	try:
		if strtobool(os.environ['ALLOW_UNSAFE_SSL']) == True:
			r = requests.post('{}/api_jsonrpc.php'.format(host), verify=False, headers={'Content-Type': "application/json-rpc"}, json={
				"jsonrpc": "2.0",
				"method": "user.login",
				"params": {
				  "user": user,
				  "password": password},
				"id":1
				})
			token = r.json()['result']
			r = requests.post('{}/api_jsonrpc.php'.format(host), headers={'Content-Type': "application/json-rpc"}, json={
				"jsonrpc": "2.0",
				"method": "host.get",
				"params": {
				  "output": [
				    "host"
				  ]
				},
				"id":1,
				"auth": token
				})
		else:
			r = requests.post('{}/api_jsonrpc.php'.format(host), headers={'Content-Type': "application/json-rpc"}, json={
				"jsonrpc": "2.0",
				"method": "user.login",
				"params": {
				  "user": user,
				  "password": password},
				"id":1
				})
			token = r.json()['result']
			r = requests.post('{}/api_jsonrpc.php'.format(host), headers={'Content-Type': "application/json-rpc"}, json={
				"jsonrpc": "2.0",
				"method": "host.get",
				"params": {
				  "output": [
				    "host"
				  ]
				},
				"id":1,
				"auth": token
				})

		for discovered_asset in r.json()['result']:
			rest_client.post('discovery/{}/discovered_asset'.format(new_discovery_id, ), {'name': discovered_asset['host'], 'ip_address': ''})

		rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'success'})
		return True
	except:
		rest_client.put('discovery/{}'.format(new_discovery_id, ), {'status': 'error'})
		return False