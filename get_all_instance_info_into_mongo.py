#!/usr/bin/env python
# nova_mongo_v3.py

from keystoneclient.v2_0 import client as ksc
from novaclient import client as nc
from novaclient import exceptions as nexc

import datetime
import os
import pymongo
import sys

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

MONGO_URL = os.environ['MONGO_URL']

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

try:
	mongoconn = pymongo.Connection (MONGO_URL, safe=True)
except pymongo.errors.ConnectionFailure as e:
	print 'Error: check  your MongoDB connectivty'
	print 'Error:',  e
	sys.exit()

# Set the mongo database to the one for inventory information
mongodb = mongoconn.inventory

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
		if 'links' in flavors[id]: del flavors[id]['links']
	except nexc.NotFound:
		flavors[id] = {}

# Set the Mongo collection to the one for flavor information
mongocollection = mongodb.flavors

for id in flavors:
	try:
		flavors[id]['timestamp'] = today
		mongocollection.update ({'id':id, 'timestamp':today}, flavors[id], upsert=True) 
	except pymongo.errors.PyMongoError as e:
		print 'Error: unable to update flavor info for', row
		print 'Error:', e

# Get the set of image ids that are present for the servers
imageids = {s.image['id'] for s in servers if s.image}
images = {}
for id in imageids:
	try:
		images[id] = nova.images.get(id).__dict__['_info']
		if 'links' in images[id]: del images[id]['links']
		if 'metadata' in images[id]: del images[id]['metadata']
		if 'server' in images[id]: del images[id]['server']
	except nexc.NotFound:
		images[id] = {}

# Set the Mongo collection to the one for image information
mongocollection = mongodb.images

for id in images:
	try:
		images[id]['timestamp'] = today
		#print images[id]
		mongocollection.update ({'id':id, 'timestamp':today}, images[id], upsert=True) 
	except pymongo.errors.PyMongoError as e:
		print 'Error: unable to update image info for', row
		print 'Error:', e

# Set the Mongo collection to the one for instance information
mongocollection = mongodb.instances

for server in servers:
	info = {}
	info['timestamp'] = today
	info['name'] = server.name
	try:
		info['tenant'] = tenantsdict[server.tenant_id]
	except KeyError:
		info['tenant'] = None
	try:
		info['user'] =  usersdict[server.user_id]['name']
	except KeyError:
		info['user'] = None
	try:
		info['email'] =  usersdict[server.user_id]['email']
	except KeyError:
		info['email'] = None
	info['instance_id'] =  getattr(server, 'OS-EXT-SRV-ATTR:instance_name')
	info['vm_state'] =  getattr(server, 'OS-EXT-STS:vm_state')
	info['power_state'] =  getattr(server, 'OS-EXT-STS:power_state')
	if server.image:
		info['image'] =  images[server.image['id']]
	else:
		info['image'] = {}
	if server.flavor:
		info['flavor'] = flavors[server.flavor['id']]
	else:
		info['flavor'] = {}
	info['hypervisor'] =  getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
	try:
		mongocollection.update({'name':server.name, 'timestamp':today}, info, upsert=True)
	except pymongo.errors.PyMongoError as e:
		print 'Error: unable to update instance info for', info
		print 'Error:', e
