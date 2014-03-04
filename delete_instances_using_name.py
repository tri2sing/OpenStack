#!/usr/bin/env python

import os
import sys

from novaclient import client as nc
from novaclient import exceptions as nexc

VERSION = 2

def get_nova_info():
	d = {}
	d['username'] = os.environ['OS_USERNAME']
	d['api_key'] = os.environ['OS_PASSWORD']
	d['project_id'] = os.environ['OS_TENANT_NAME']
	d['auth_url'] = os.environ['OS_AUTH_URL']
	d['service_type'] = 'compute'
	d['no_cache'] = True
	return d

try:
	nova = nc.Client (VERSION, **get_nova_info())
	instances = nova.servers.list()
	mine = [inst for inst in instances if inst.name.startswith('sameer')]
	for m in mine:
		print m.name
		m.delete()
except nexc.ClientException as exc:
	print exc.message
	sys.exit()


