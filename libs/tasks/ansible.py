# -*- coding: utf-8 -*-

import json
import re
import ansible_runner
import os
import shutil


def run(playbook, inventory, extravars=dict()):
	runner = ansible_runner.interface.run(json_mode=True, quiet=True, suppress_env_files=True, playbook='/runner/project/{}.yml'.format(playbook), inventory=inventory, envvars={' ANSIBLE_KEEP_REMOTE_FILES': True, 'ANSIBLE_NOCOLOR':True}, extravars=extravars)
	return runner

def parse(container_output):
	result = dict()
	task = None

	for line in container_output:
		if line['event'] == 'playbook_on_task_start':
			event  = re.findall('\[(.*?)\]', line['stdout'])[0]
		elif line['event'] == 'runner_on_ok' or line['event'] == 'runner_on_unreachable':
			asset = line['event_data']['host']
			stdout = line['stdout']
			status = stdout.split(':')[0]

			if '=>' in stdout:
				try:
					msg = json.loads(stdout.split('=>')[1].strip())['msg']
				except:
					status = 'error_parsing_log'
					msg = ''
			else:
				if 'results' in line['event_data']['res']:
					msg = line['event_data']['res']['results']
				else:
					msg = ''

			if not asset in result:
				result[asset] = dict()
			result[asset][event] = {'status': status, 'asset': asset, 'result': msg}

	return result


def clear():
	for base, dirs, files in os.walk('/tmp'):
		for file in files:
			os.remove('/tmp/{}'.format(file))
		for directory in dirs:
			shutil.rmtree('/tmp/{}'.format(directory))