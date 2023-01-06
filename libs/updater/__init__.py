# -*- coding: utf-8 -*-

from flask import current_app
from requests import get

from linufy.libs import configurations


def get_last_release():
    try:
        if configurations.get('proxy_required').value == "True" and configurations.get('proxy_host').value != "" and configurations.get('proxy_port').value != "":
            proxies = {
                'http': 'http://{}:{}'.format(configurations.get('proxy_host').value, configurations.get('proxy_port').value),
                'https': 'http://{}:{}'.format(configurations.get('proxy_host').value, configurations.get('proxy_port').value),
            }
        else:
            proxies = {}
        response = get("https://api.github.com/repos/LinuFy/LinuFy/releases/latest", proxies=proxies)
        return response.json()["name"]
    except:
        return None


def new_version_available():
    current_version = current_app.config['VERSION']
    last_version = get_last_release()
    if last_version != None and last_version != current_version:
        return last_version
    else:
        return False