# -*- coding: utf-8 -*-

from redis import Redis
from rq import Queue

from linufy.app import app
from linufy.libs import tasks
from linufy.models import Region

import time


def get_base_informations():
	while True:
		with app.app_context():
			for region in Region.query.all():
				queue = Queue(region.access_key, connection=Redis(host=region.redis.hostname, port=region.redis.port))
				queue.enqueue(tasks.assets.base_refresh)
			time.sleep(180)


def clear_queues():
	with app.app_context():
		for region in Region.query.all():
			queue = Queue(region.access_key, connection=Redis(host=region.redis.hostname, port=region.redis.port))
			queue.empty()
