#!/usr/bin/python

from novaclient import client as nc

import datetime
import json
import os
import sys

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

VERSION = 2

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
	hvsrs = nova.hypervisors.list ()
	print vars(hvsrs[0])
	print '-'*80
except Exception as exc:
	print exc.message
	sys.exit()

print 'Name', ',', 
print 'ID', ',', 
print 'Type', ',', 
print 'Version', ',', 
print 'VMs', ',', 
print 'CPU Vendor', ',', 
print 'Model', ',', 
print 'Arch', ',', 
print 'Cores', ',', 
print 'Threads', ',', 
print 'VCPUS (Host)', ',', 
print 'VCPUS (VMs)', ',', 
print 'RAM (MB)', ',', 
print 'RAM Used (MB)', ',', 
print 'RAM Free (MB)', ',', 
print 'Disk (GB)', ',', 
print 'Disk Used (GB)', ',', 
print 'Disk Free (GB)' 

for hv in hvsrs:
	print hv.hypervisor_hostname, ',',
	print hv.id, ',',
	print hv.hypervisor_type, ',',
	print hv.hypervisor_version, ',',
	print hv.running_vms, ',',
	cpu = json.loads (hv.cpu_info)
	print cpu['vendor'], ',',
	print cpu['model'], ',',
	print cpu['arch'], ',',
	print cpu['topology']['cores'], ',',
	print cpu['topology']['threads'], ',',
	print hv.vcpus, ',',
	print hv.vcpus_used, ',',
	print hv.memory_mb, ',',
	print hv.memory_mb_used, ',',
	print hv.free_ram_mb, ',',
	print hv.local_gb, ',',
	print hv.local_gb_used, ',',
	print hv.free_disk_gb 
