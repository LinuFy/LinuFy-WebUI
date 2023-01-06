# -*- coding: utf-8 -*-
"""Module for LinuFy"""

from threading import Thread
from redis import Redis
from rq import Queue

from flask import g, redirect, request, session
from flask_login import current_user
from linufy.libs import notifications, updater, configurations, assets, users, regions
from linufy.app import babel, app
import math


def get_notifications():
    return notifications.get_available()


def new_version_available():
    return updater.new_version_available()


def asset_get_meta(asset_id):
    return assets.get_meta(asset_id)


def currentuser_get_meta():
    return users.get_meta(current_user.id)

def get_tasks_in_queue(region_id):
    region = regions.get(region_id)
    if region:
        queue = Queue(region.access_key, connection=Redis(host=region.redis.hostname, port=region.redis.port))
        return queue.count
    return 0


def convert_size(size_bytes):
   size_bytes = int(size_bytes)
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


@app.context_processor
def utility_processor():
    return dict(get_notifications=get_notifications,
    new_version_available=new_version_available,
    asset_get_meta=asset_get_meta,
    currentuser_get_meta=currentuser_get_meta,
    convert_size=convert_size,
    get_tasks_in_queue=get_tasks_in_queue
    )


@app.before_request
def before_request_func():
    if hasattr(configurations.get('force_redirect_to_https'), 'value'): 
        if configurations.get('force_redirect_to_https').value == "True" and request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    g.linufy_config = configurations.get_all()


@app.after_request
def add_security_header(response):
    response.headers['X-Frame-Options'] = "SAMEORIGIN"
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers['Strict-Transport-Security'] = "max-age=63072000; includeSubDomains; preload"
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response


@app.before_first_request
def add_schedule_tasks():
    regions.tasks.clear_queues()
    thread = Thread(target=regions.tasks.get_base_informations)
    thread.start()


@babel.localeselector
def get_locale():
    if 'lang' in session and session['lang'] in app.config['LANGUAGES']:
        return session['lang']
    return request.accept_languages.best_match(app.config['LANGUAGES'])
