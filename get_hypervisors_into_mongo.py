#!/usr/bin/python

from novaclient import client as nc

import datetime
import json
import os
import pymongo
import sys

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

VERSION = 2

MONGO_URL = os.environ['MONGO_URL']

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

nova = nc.Client (VERSION, **get_nova_info())

try:
	conn = pymongo.Connection (MONGO_URL, safe=True)
except pymongo.errors.ConnectionFailure as e:
	print 'Error: check  your MongoDB connectivty'
	print 'Error:',  e
	sys.exit()

# Set the mongo database to the one for inventory information
mdb = conn.inventory
mcl = mdb.hypervisors

try:
	hvsrs = nova.hypervisors.list ()
except Exception as exc:
	print exc.message
	sys.exit()

for hv in hvsrs:
	info = {}
	info['timestamp'] = today
	info['name'] = hv.hypervisor_hostname
	info['id'] = hv.id
	info['type'] = hv.hypervisor_type
	info['version'] = hv.hypervisor_version
	info['vms'] = hv.running_vms
	cpu = json.loads (hv.cpu_info)
	info['vendor'] = cpu['vendor']
	info['model'] = cpu['model']
	info['arch'] = cpu['arch']
	info['cores'] = cpu['topology']['cores']
	info['threads'] = cpu['topology']['threads']
	info['host_os_cpus'] = hv.vcpus
	info['vm_vcpus'] = hv.vcpus_used
	info['ram_mb'] = hv.memory_mb
	info['ram_used_mb'] = hv.memory_mb_used
	info['ram_free_mb'] = hv.free_ram_mb
	info['disk_gb'] = hv.local_gb
	info['disk_gb'] = hv.local_gb_used
	info['isk_free_gb'] = hv.free_disk_gb 
	try:
		mcl.update({'name':hv.hypervisor_hostname, 'timestamp':today}, info, upsert=True)
	except pymongo.errors.PyMongoError as e:
		print 'Error: unable to update instance info for', info
		print 'Error:', e
	#print info
