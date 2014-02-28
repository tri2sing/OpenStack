#!/usr/bin/env python

from datetime import datetime as dt, timedelta
import logging as lg
import pandas as pd
import pandas.tools as tl
import pymongo
import sys
import csv

today = dt.now()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)
yesterday = today + timedelta (days=-1)

MONGO_URL = os.environ['MONGO_URL']

try:
    conn = pymongo.Connection (MONGO_URL, safe=True)
except pymongo.errors.ConnectionFailure as e:
    print 'Error: check  your MongoDB connectivity'
    print 'Error:', e
    sys.exit()

# Databases to use
db1 = conn.inventory
db2 = conn.collectd

# Collections to use
hy = db1.hypervisors
vms = db1.instances
caph = db1.hostcapacity
ld = db2.load

qry1 = {'timestamp': today}
sltr1 = {'_id': 0}
sltr2 = {'_id': 0}
sltr3 = {'_id': 0}

try:
    # Get the list of hypervisors
    hvsrs = hy.find (qry1, sltr1)
#    print 'timestamp', 'host_name', 'vms_count', 'host_ram', 'vms_ram_alloc', 'ratio_ram', 'host_cpus', 'vms_vcpu_alloc', 'ratio_cpu', 'host_load_total', 'host_load_per_cpu'

    for h in hvsrs:
        info = {}
        # Get the cpu load data which is of the form [short term, medium term, long term]
        # We focus on the long-term as the barometer of host compute capacity. 
        qry2 = {"time" : { "$gte" : yesterday, "$lte" : today }, "host": h['name']}
        lddocs = ld.find (qry2, sltr2)
        ldlist = list(lddocs)
        if ldlist:
            ldvals = [item["values"][2] for item in ldlist]
            lddf = pd.DataFrame(ldvals)
            ldmean = round(lddf.mean().tolist()[0], 4)
        else:
            ldmean = -1.0 * (float(h['host_os_cpus'])) 
            print str(today) + ': No load data for ' + h['name']

        info['timestamp'] = today
        info['host_name'] = h['name']
        info['host_load_total'] = ldmean
        info['vms_count'] = h['vms']
        info['host_ram'] = h['ram_mb']
        info['host_cpus'] = h['host_os_cpus']
        info['host_load_per_cpu'] =  round(ldmean/ float(h['host_os_cpus']), 4)

        if h['vms'] > 0:
            qry3 = {"timestamp" : today, "hypervisor": h['name']}
            vmdocs = vms.find (qry3, sltr3)
            vmlist = list(vmdocs)
            vmvals = [{"vcpus": item["flavor"]["vcpus"], "ram": item["flavor"]["ram"]} for item in vmlist]
            vmdf = pd.DataFrame(vmvals)
            totals = vmdf.sum()
            
            # We have to cast the values stored in totals[] to types that MongoDB can understand.
            # For example totals['vms_ram_alloc'] is of type numpy.int64 which we cannot insert into MongoDB.
            info['vms_ram_alloc'] = long(totals['ram'])
            info['vms_vcpu_alloc'] = long(totals['vcpus'])
            info['ratio_ram'] =  round(float(totals['ram'])/ float(h['ram_mb']), 4)
            info['ratio_cpu'] =  round(float(totals['vcpus'])/ float(h['host_os_cpus']), 4)

        else:
            info['vms_ram_alloc'] = 0
            info['vms_vcpu_alloc'] = 0
            info['ratio_ram'] =  0.0
            info['ratio_cpu'] =  0.0

        if info['host_load_per_cpu'] >= 0.75 or  info['vms_count'] >= 70:
            info['state'] = 'RED'
        elif info['host_load_per_cpu'] > 0.5 or  info['vms_count'] >= 60:
             info['state'] = 'YELLOW'
        else:
             info['state'] = 'GREEN'

        # To debug why MongoDB insert was failing printed the data types of values.
        #for k,v in info.items(): print k, type(v)

        caph.update({'host_name':h['name'], 'timestamp':today}, info, upsert=True)
#       print info['timestamp'], info['host_name'], info['vms_count'], info['host_ram'], info['vms_ram_alloc'], info['ratio_ram'], info['host_cpus'], info['vms_vcpu_alloc'], info['ratio_cpu'], info['host_load_total'], info['host_load_per_cpu']


except pymongo.errors.PyMongoError as e:
    print str(today) + ': Error: unable to query'
    print str(today) + ': Error:', e

