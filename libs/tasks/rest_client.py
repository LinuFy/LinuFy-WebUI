# -*- coding: utf-8 -*-

import requests
import urllib3
import os
from distutils.util import strtobool


class RestClient:
	def __init__(self):
		self.access_key = os.environ['ACCESS_KEY']
		self.secret_key = os.environ['SECRET_KEY']
		self.api_url = os.environ['LINUFY_URL']
		self.allow_unsafe_url = strtobool(os.environ['ALLOW_UNSAFE_SSL'])
		self.headers = {'Content-Type': 'application/json', 'User-Agent': 'LinuFy-Region/1.0', 'X-Access-Token': None}


	def auth(self):
		data = {'access_key' : self.access_key, 'secret_key': self.secret_key}
		if self.allow_unsafe_url == True:
			urllib3.disable_warnings()
			response = requests.post("{}/api/auth".format(self.api_url, ), verify=False, json=data)
		else:
			response = requests.post("{}/api/auth".format(self.api_url, ), verify=True, json=data)
		if response.status_code == 200:
			result = response.json()
			if result['status'] == "success":
				self.headers['X-Access-Token'] = result['token']
				return True
		return False


	def get(self, endpoint):
		if self.allow_unsafe_url == True:
			urllib3.disable_warnings()
			response = requests.get("{}/api/{}".format(self.api_url, endpoint), verify=False, headers=self.headers)
		else:
			response = requests.get("{}/api/{}".format(self.api_url, endpoint), verify=True, headers=self.headers)
		return response.json()


	def post(self, endpoint, params):
		if self.allow_unsafe_url == True:
			urllib3.disable_warnings()
			response = requests.post("{}/api/{}".format(self.api_url, endpoint), verify=False, headers=self.headers, json=params)
		else:
			response = requests.post("{}/api/{}".format(self.api_url, endpoint), verify=True, headers=self.headers, json=params)
		return response.json()


	def put(self, endpoint, params):
		if self.allow_unsafe_url == True:
			urllib3.disable_warnings()
			response = requests.put("{}/api/{}".format(self.api_url, endpoint), verify=False, headers=self.headers, json=params)
		else:
			response = requests.put("{}/api/{}".format(self.api_url, endpoint), verify=True, headers=self.headers, json=params)
		return response.json()


	def delete(self, endpoint):
		if self.allow_unsafe_url == True:
			urllib3.disable_warnings()
			response = requests.delete("{}/api/{}".format(self.api_url, endpoint), verify=False, headers=self.headers)
		else:
			response = requests.delete("{}/api/{}".format(self.api_url, endpoint), verify=True, headers=self.headers)
		return response.json()
