#!/usr/bin/env python

from keystoneclient.v2_0 import client as ksc
from novaclient import client as nc
from novaclient import exceptions as nexc

import datetime
import os
import sys

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

# Need an OS account that has admin access to all tenants
VERSION = 2

def get_kston_info():
	d = {}
	d['username'] = os.environ['OS_USERNAME']
	d['password'] = os.environ['OS_PASSWORD']
	d['tenant_name'] = os.environ['OS_TENANT_NAME']
	d['auth_url'] = os.environ['OS_AUTH_URL']
	d['cacert'] = os.environ['OS_CACERT']
	return d

def get_nova_info():
	d = {}
	d['username'] = os.environ['OS_USERNAME']
	d['api_key'] = os.environ['OS_PASSWORD']
	d['project_id'] = os.environ['OS_TENANT_NAME']
	d['auth_url'] = os.environ['OS_AUTH_URL']
	d['cacert'] = os.environ['OS_CACERT']
	d['service_type'] = 'compute'
	d['no_cache'] = True
	return d

# Get the list of tenants from OpenStack
kstone = ksc.Client (**get_kston_info())
tenants = kstone.tenants.list ()
tenantsdict = {tenant.id: tenant.name for tenant in tenants}
users = kstone.users.list ()
usersdict = {user.id: {'name': user.name, 'email': user.email} if hasattr(user, 'email') else {'name': user.name, 'email': None} for user in users}

nova = nc.Client (VERSION, **get_nova_info())
try:
	servers = nova.servers.list (True, {'all_tenants': True})
except Exception as exc:
	print exc.message
	sys.exit()

# Get the set of flavor ids that are present for the servers
flavorids = {s.flavor['id'] for s in servers if s.flavor}
flavors = {}
for id in flavorids:
	try:
		flavors[id] = nova.flavors.get(id).__dict__['_info']
	except nexc.NotFound:
		flavors[id] = {}

# Get the set of image ids that are present for the servers
imageids = {s.image['id'] for s in servers if s.image}
images = {}
for id in imageids:
	try:
		images[id] = nova.images.get(id).__dict__
	except nexc.NotFound:
		images[id] = {}

print 'date', ',',
print 'vm_name', ',',
print 'tenant', ',',
print 'user', ',',
print 'email', ',',
print 'instance_name', ',',
print 'vm_state', ',',
print 'power_state', ',',
print 'hypervisor', ',',
print 'flavor_name', ',',
print 'vcpus', ',',
print 'memory_mb', ',',
print 'ephemeral_gb', ',',
print 'image_name', ','

for server in servers:
	print today, ',',
	print server.name, ',',
	try:
		print  tenantsdict[server.tenant_id], ',',
	except KeyError:
		print 'None', ',',
	try:
		print  usersdict[server.user_id]['name'], ',',
	except KeyError:
		print 'None', ',',
	try:
		print  usersdict[server.user_id]['email'], ',',
	except KeyError:
		print 'None', ',',
	print getattr(server, 'OS-EXT-SRV-ATTR:instance_name'), ',',
	print getattr(server, 'OS-EXT-STS:vm_state'), ',',
	print getattr(server, 'OS-EXT-STS:power_state'), ',',
	print getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname'), ',',
	if server.flavor:
		print flavors[server.flavor['id']]['name'], ',',
		print flavors[server.flavor['id']]['vcpus'], ',',
		print flavors[server.flavor['id']]['ram'], ',',
		print flavors[server.flavor['id']]['OS-FLV-EXT-DATA:ephemeral'], ',',
	else:
		print 'None', ',', 'None', ',', 'None', ',', 'None', ',', 
	if server.image:
		print images[server.image['id']]['name'], ','
	else:
		print 'None', ','
