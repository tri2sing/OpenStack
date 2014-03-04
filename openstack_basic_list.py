#!/usr/bin/env python

import datetime
import os
import sys
import time  #In my PythonUtils repo on github

from keystoneclient.v2_0 import client as ksc
from novaclient import client as nc
from novaclient import exceptions as nexc
from timer import Timer


today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

VERSION = 2

def get_kston_info():
	d = {}
	d['username'] = os.environ['OS_USERNAME']
	d['password'] = os.environ['OS_PASSWORD']
	d['tenant_name'] = os.environ['OS_TENANT_NAME']
	d['auth_url'] = os.environ['OS_AUTH_URL']
	return d

def get_nova_info():
	d = {}
	d['username'] = os.environ['OS_USERNAME']
	d['api_key'] = os.environ['OS_PASSWORD']
	d['project_id'] = os.environ['OS_TENANT_NAME']
	d['auth_url'] = os.environ['OS_AUTH_URL']
	d['service_type'] = 'compute'
	d['no_cache'] = True
	return d

computer = os.uname()[1]
iterations = int(sys.argv[1])
sum = 0

for i in range(iterations):
	with Timer() as t:
		kstone = ksc.Client (**get_kston_info())
		nova = nc.Client (VERSION, **get_nova_info())
		tenants = kstone.tenants.list ()
		users = kstone.users.list ()
		images = nova.images.list()
		flavors = nova.flavors.list()
        hvsrs = nova.hypervisors.list ()
	
	print '%s iteration %s: %s ms' % (computer, i, t.msecs)
	sum += t.msecs

print '%s average %s: %s ms' % (computer, i, sum/iterations)
