#!/usr/bin/env python

import datetime
import os
import random
import sys
import time

from cinderclient import client as cct
from glanceclient import client as gct
from keystoneclient.v2_0 import client as ksc
from novaclient import client as nc
from novaclient import exceptions as nexc

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

VERSION = 2

def get_kston_info():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['cacert' ] = os.environ['OS_CACERT']
    return d

def get_cinder_info():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['service_type'] = 'volume'
    d['cacert' ] = os.environ['OS_CACERT']
    return d

def get_nova_info():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['cacert' ] = os.environ['OS_CACERT']
    d['service_type'] = 'compute'
    d['no_cache'] = True
    return d

random.seed()

try:
    nova = nc.Client (VERSION, **get_nova_info())
    cinder = cct.Client (VERSION, **get_cinder_info())

    # It is required that any of the search terms used in find functions
    # match  objects that already exist in the OpenStack environment.
    img = nova.images.find (name = 'Ubuntu_12.04')
    #img = nova.images.find (name = 'WS08R2_ApplicationServer')
    size = int(getattr(img, 'OS-EXT-IMG-SIZE:size'))
    sizegb = size/(1024*1024*1000)
    fvr = nova.flavors.find (name = 'Small-A')
    net = nova.networks.find (label='StressTest')


    # I am creating one instance at a time instead of the using the max_count parameter.
    # Using max_count creates VMs appended with GUID in their names and makes them very long.

    ranstr =  str(int(random.random()*1000))
    #nme = 'sameer' + computer[-5:] + ranstr
    nme = 'poctest01'
    
    vol1 = cinder.volumes.create(sizegb, imageRef=img.id)
    status = vol1.status
    while status != 'available':
        time.sleep (5)
        vol1 = cinder.volumes.get (vol1.id)
        status = vol1.status

    instance = nova.servers.create (
        name=nme, 
        image=img, 
        flavor=fvr, 
        nics=[{'net-id': net.id}], 
        #availability_zone='nova:'+computer, 
        block_device_mapping={'vda': vol1.id},
        userdata=open('min-lnx').read()
        )

    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        # Retrieve instance again to update status field
        instance = nova.servers.get (instance.id)
        status = instance.status
except nexc.ClientException as exc:
    print vars(exc)
    sys.exit()


