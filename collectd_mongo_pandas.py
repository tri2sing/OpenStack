#!/usr/bin/env python

from datetime import datetime as dt, timedelta
from bson import json_util
import json
import os
import pandas as pd
import pandas.tools as tl
import pymongo
import sys
import csv

today = dt.now()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)
yesterday = today + timedelta (days=-1)
# For testing purpose reduced the duration to a few hours
#yesterday = today + timedelta (hours=-1)

# The MongoDB should not be set to use a usename and password for access
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
cpu = db2.cpu
disk = db2.disk
load = db2.load

hypqry = {'timestamp': today}
fields = {'_id': 0}

try:
    # Get the list of hypervisors
    hvsrs = hy.find (hypqry, fields)

    for h in hvsrs:
        info = {}
        #cpuqry = {"time" : { "$gte" : yesterday, "$lte" : today }, "host": h['name'], "type_instance": "system"}
        '''
        cpuqry = {"time" : { "$gte" : yesterday, "$lte" : today }, "host": h['name']}
        print cpuqry
        cpudocs = cpu.find (cpuqry, fields)
        cpulist = list(cpudocs)
        if cpulist:
            df = pd.read_json(json.loads(cpulist))
            print df.head()
        '''
        loadqry = {"time" : { "$gte" : yesterday, "$lte" : today }, "host": h['name']}
        #print loadqry
        loaddocs = load.find (loadqry, fields)
        loadlist = list(loaddocs)
        if loadlist:
            #print json.dumps(loadlist[0], default=json_util.default)
            df = pd.read_json(json.dumps(loadlist, default=json_util.default))
            print df.head()
            print ''

except pymongo.errors.PyMongoError as e:
    print str(today) + ': Error: unable to query'
    print str(today) + ': Error:', e

