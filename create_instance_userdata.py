#!/usr/bin/env python

import argparse
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

VERSION = 2

# As the credential information is sensiteive information, I assume it is set in environment variable 
# on the host where this script runs and this script fails when the variables are not set.

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

# Glance does not easy allow creating a client like nova and cinder.
def get_glance_client():
        kstone = ksc.Client (**get_kston_info())
        glanceendpoint = kstone.service_catalog.url_for(service_type='image', endpoint_type='internalURL')
        glance = gct.Client('1', glanceendpoint, token=kstone.auth_token, cacert=kstone.verify_cert)
        return glance


def main(count=1, flavor='Large-B', image='WS08R2_ApplicationServer', zone='az1', host=os.uname()[1], network='External3', prefix='sameer', userdatafile=''):
    
    random.seed()
    
    try:
        nova = nc.Client (VERSION, **get_nova_info())
        cinder = cct.Client (VERSION, **get_cinder_info())
        glance = get_glance_client()

        # There are some requirements for the find function to work.
        # 1) The name/label you use in the search match exactly one object.
        # 2) A unique object exist that matches the search criterion.
        fvr = nova.flavors.find (name = flavor)
        net = nova.networks.find (label=network)
    
        # Initially the image search in nova worked as the requirements abive were satisfied.
        # Then two images with the same name were created so I needed another criterion.
        #img = nova.images.find (name=image)
        #sizegb = int(getattr(img, 'OS-EXT-IMG-SIZE:size'))/(1024*1024*1000)

        # Using two criteria required querying glance instead of nova.
        # Glance returns an iterator rather than a list of objects.
        # We ensure that our filter criteria return one and only one object.
        images = list(glance.images.list (filters = {'name': image, 'disk_format': 'raw'}))
        img = images[0]
        sizegb = img.size/(1024*1024*1000)
    
        # I am creating one instance at a time instead of the using the max_count parameter.
        # Using max_count creates VMs appended with GUID in their names and makes them very long.

        for i in range(count):
    
            nme = prefix + str(int(random.random()*10000))
            
            vol1 = cinder.volumes.create(sizegb, imageRef=img.id)
            status = vol1.status
            while status != 'available':
                time.sleep (5)
                vol1 = cinder.volumes.get (vol1.id)
                status = vol1.status
        
            if userdatafile:
                userdata=open(userdatafile).read().replace('hostnamereplace', nme)
            else:
                userdata = ''
                
            instance = nova.servers.create (
                name=nme, 
                image=img, 
                flavor=fvr, 
                nics=[{'net-id': net.id}], 
                availability_zone=zone+':'+host, 
                block_device_mapping={'vda': vol1.id},
                userdata=userdata
                )
        
            status = instance.status
            while status == 'BUILD':
                time.sleep(5)
                # Retrieve instance again to update status field
                instance = nova.servers.get (instance.id)
                status = instance.status

            rightnow = datetime.datetime.now()
            print nme, ": nova done at ", rightnow

    except nexc.ClientException as exc:
        print vars(exc)
        sys.exit()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument ('-c', '--count', type=int, default=1, help='the number of instances to create') 
    parser.add_argument ('-f', '--flavor', default='Large-B', help='name of the flavor to use for the instance')
    parser.add_argument ('-i', '--image', default='WS08R2_ApplicationServer', help='name of the image to use for the instance')
    parser.add_argument ('-az', '--zone', default='az1', help='availability zone to launch the instance on')
    parser.add_argument ('-t', '--host', default=os.uname()[1], help='name of the host to launch the instance on')
    parser.add_argument ('-n', '--network', default='External3', help='name of the network to use for the instance')
    parser.add_argument ('-p', '--prefix', default='sameer', help='prefix to use for the name of the instance, the remainder will be a random number')
    parser.add_argument ('-u', '--userdatafile', default='', help='path to file to run at the instance on intial boot, usually for customization')
    args = parser.parse_args()
    main(
        count=args.count, 
        flavor=args.flavor, 
        image=args.image, 
        zone=args.zone, 
        host=args.host, 
        network=args.network, 
        prefix=args.prefix, 
        userdatafile=args.userdatafile
        )
