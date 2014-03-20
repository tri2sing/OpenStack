#!/usr/bin/env python

from keystoneclient.v2_0 import client as ksc
from novaclient import client as nc
from novaclient import exceptions as nexc

import datetime
import os
import pymongo
import pyodbc
import sys

today = datetime.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

# The MongoDB should not be set to use a usename and password for access
MONGO_URL = os.environ['MONGO_URL']
#MONGO_URL = 'mongodb://mongodb-us-sw-in.icloud.intel.com'

def get_cdis_info():
    d = {}
    d['name'] = os.environ['CDIS_NAME']
    d['pass'] = os.environ['CDIS_PASS']
    return d

def get_org_info(idsidslist):

    orginfo = []
    if not idsidslist:
        return orginfo

    # Build the string that has the SQL format and will used in CDIS query
    namesquotes = ", ".join(["'"+idsid+"'" for idsid in idsidslist])
    
    cdis = get_cdis_info()
    query = "SELECT * FROM WorkerOrgLevel WHERE LOWER(ShortID) IN(" + namesquotes + ")"
    
    try:
        cxn = pyodbc.connect('DSN=cdis;UID=' + cdis['name'] + ';PWD=' + cdis['pass']) 
        csr = cxn.cursor()
        csr.execute(query)
        cols = [item[0] for item in csr.description]
        rows = csr.fetchall()
        # If CDIS returns results create dict for each row that uses column names as keys, and the corresponding row data as values.
        if rows:
            orginfo = [dict(zip(cols, row)) for row in rows]
    except pyodbc.Error as per:
        print str(today) + per
    
    return orginfo

# Need an OS account that has admin access to all tenants
VERSION = 2

def get_kston_creds():
    '''Get the details of the OS_ variables for keystone from the environment variables'''

    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['cacert'] = os.environ['OS_CACERT']
    return d

def get_nova_info():
    '''Get the details of the OS_ variables for nova from the environment variables'''

    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['cacert'] = os.environ['OS_CACERT']
    d['service_type'] = 'compute'
    d['no_cache'] = True
    return d

def get_tenants_map ():
    '''Return a dictionary which maps tenant ID to name'''

    kstone = ksc.Client (**get_kston_creds())
    tenants = kstone.tenants.list ()
    if tenants:
        tenantsdict = {tenant.id: tenant.name for tenant in tenants}
    else:
        tenantsdict = {}
    return tenantsdict
    
def get_users_map_and_reverse ():
    '''Return a dictionary which maps user ID to name and email and a dictionary which maps a name to ID'''

    kstone = ksc.Client (**get_kston_creds())
    users = kstone.users.list ()
    if users:
        id_to_name = {user.id: {'name': user.name, 'email': user.email} if hasattr(user, 'email') else {'name': user.name, 'email': None} for user in users}
        name_to_id = {user.name[3:].lower(): user.id for user in users if user.name.startswith('ad_')}
        idsids = [user.name[3:].lower() for user in users if user.name.startswith('ad_')]
    else:
        id_to_name = {}
        name_to_id = {}

    return id_to_name, name_to_id, idsids

def modify_user_map_with_org(users_id_to_name, users_name_to_id, org_info):

    # If CDIS returned values, append the org info to the user_map.
    if org_info:
        for emp in org_info:
            idsid = emp['ShortID'].strip().lower()
            users_id_to_name[users_name_to_id[idsid]]['Level3'] = emp['LVLDESCR3'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level4'] = emp['LVLDESCR4'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level5'] = emp['LVLDESCR5'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level6'] = emp['LVLDESCR6'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level7'] = emp['LVLDESCR7'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level8'] = emp['LVLDESCR8'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level9'] = emp['LVLDESCR9'].strip()
            users_id_to_name[users_name_to_id[idsid]]['Level10'] = emp['LVLDESCR10'].strip()
    
    # If there are users who are not in the form ad_idsid then we append empty strings for the org information for them.
    for id in users_id_to_name:
        if 'Level3' not in users_id_to_name[id]:
            users_id_to_name[id]['Level3'] = ''
            users_id_to_name[id]['Level4'] = ''
            users_id_to_name[id]['Level5'] = ''
            users_id_to_name[id]['Level6'] = ''
            users_id_to_name[id]['Level7'] = ''
            users_id_to_name[id]['Level8'] = ''
            users_id_to_name[id]['Level9'] = ''
            users_id_to_name[id]['Level10'] = ''

def get_instances_details():
    '''Returns the details of virtual server instances in the environment'''

    nova = nc.Client (VERSION, **get_nova_info())
    try:
        servers = nova.servers.list (True, {'all_tenants': True})
    except Exception as exc:
        print str(today) + exc
        sys.exit()
    return servers

def get_flavors_map(flavorids):
    '''Returns the details for each flavor in a list given the ID of the flavor'''

    if not flavorids:
        return {}
    nova = nc.Client (VERSION, **get_nova_info())
    flavors = {}
    for id in flavorids:
        try:
            flavors[id] = nova.flavors.get(id).__dict__['_info']
            if 'links' in flavors[id]: del flavors[id]['links']
        except nexc.NotFound:
            flavors[id] = {}
    return flavors

def get_images_map(imageids):
    '''Returns the details for each image in a list given the ID of the image'''

    if not imageids:
        return {}
    nova = nc.Client (VERSION, **get_nova_info())
    images = {}
    for id in imageids:
        try:
            images[id] = nova.images.get(id).__dict__['_info']
            if 'links' in images[id]: del images[id]['links']
            if 'metadata' in images[id]: del images[id]['metadata']
            if 'server' in images[id]: del images[id]['server']
        except nexc.NotFound:
            images[id] = {}
    return images

def get_instances_map (instances_list, flavors_map, images_map, tenants_map, users_map):
    ''' Returns a dictionary of the form instance_map['id'].
        Builds the map by correlating information in the instances_list with the data in other maps.
    '''
    instances_map = {}
    for instance in instances_list:
        info = {}
        info['timestamp'] = today
        info['name'] = instance.name
        info['created'] = instance.created
        try:
            info['tenant'] = tenants_map[instance.tenant_id]
        except KeyError:
            info['tenant'] = None
        try:
            info['user'] =  users_map[instance.user_id]['name']
        except KeyError:
            info['user'] = None
        try:
            info['email'] =  users_map[instance.user_id]['email']
        except KeyError:
            info['email'] = None
        try:
            info.update({key: users_map[instance.user_id][key] for key in users_map[instance.user_id] if key.startswith('Level')})
        except KeyError:
            info.update({'Level' + str(num):'' for num in range(3, 11)})

        info['instance_id'] =  getattr(instance, 'OS-EXT-SRV-ATTR:instance_name')
        info['vm_state'] =  getattr(instance, 'OS-EXT-STS:vm_state')
        info['power_state'] =  getattr(instance, 'OS-EXT-STS:power_state')
        if instance.image:
            info['image'] =  images_map[instance.image['id']]
        else:
            info['image'] = {}
        if instance.flavor:
            info['flavor'] = flavors_map[instance.flavor['id']]
        else:
            info['flavor'] = {}
        info['hypervisor'] =  getattr(instance, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
        instances_map[instance.id] = info
    return instances_map

def insert_data_mongo (collectionname, datadict):
    ''' Inserts data into collection.
        collectionname: name of the collection
        datadict: a dictionary containing the records to be inserted which has has entries of the form data['id']
    '''

    try:
        connection = pymongo.Connection (MONGO_URL, safe=True)
    except pymongo.errors.ConnectionFailure as e:
        print 'Error: check  your MongoDB connectivty'
        print 'Error:',  e
        sys.exit()
    db = connection['inventory']
    collection = db[collectionname]
    for id in datadict:
        try:
            datadict[id]['timestamp'] = today
            collection.update ({'id':id, 'timestamp':today}, datadict[id], upsert=True) 
        except pymongo.errors.PyMongoError as e:
            print str(today) + 'Error:', e

def print_dict(indict):
    for k in indict:
        print indict[k]

if __name__ == '__main__':

    tenants_map = get_tenants_map()
    #print_dict(tenants_map)
    users_id_to_name, users_name_to_id, idsids = get_users_map_and_reverse() 
    org_info = get_org_info(idsids)
    modify_user_map_with_org(users_id_to_name, users_name_to_id, org_info)
    #print_dict(users_id_to_name)
    instances_list = get_instances_details()

    flavorids = {s.flavor['id'] for s in instances_list if s.flavor}
    flavors_map = get_flavors_map(flavorids)
    #print_dict(flavors_map)
    #insert_data_mongo ('flavors', flavors_map)

    imageids = {s.image['id'] for s in instances_list if s.image}
    images_map = get_images_map(imageids)
    #print_dict(images_map)
    #insert_data_mongo ('images', images_map)

    instances_map = get_instances_map(instances_list, flavors_map, images_map, tenants_map, users_id_to_name)
    print_dict(instances_map)
    #insert_data_mongo ('instances', instances_map)


