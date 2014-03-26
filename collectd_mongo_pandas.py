#!/usr/bin/env python

from bson import json_util
from datetime import datetime as dtm
from datetime import timedelta as delta

import csv
import json
import os
import pandas as pd
import pandas.tools as tl
import pymongo
import sys

end = dtm.now()
endmidnight = end.replace (hour=0, minute=0, second=0, microsecond=0)

# For testing purpose reduced the duration to a few hours
#start = end + delta (days=-1)
start = end + delta (hours=-4)

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

hypqry = {'timestamp': endmidnight}
fields = {'_id': 0}

try:
    # Get the list of hypervisors
    hvsrs = hy.find (hypqry, fields)

    for h in hvsrs:
        info = {}
        cpuqry = {"time" : { "$gte" : start, "$lte" : end }, "host": h['name']}
        print cpuqry
        print dtm.now()
        cpudocs = cpu.find (cpuqry, fields)
        print dtm.now()
        if cpudocs.count() != 0:  # This statement is slow; trying to figure out a solution
            cpulist = list(cpudocs)
            #Need to use json_util.default to handle conversion of datetime into jason.  
            df = pd.read_json(json.dumps(cpulist, default=json_util.default))
            print df.head()
        else:
            print "No data for " + h['name']
        print dtm.now()
        '''
        loadqry = {"time" : { "$gte" : start, "$lte" : end }, "host": h['name']}
        #print loadqry
        loaddocs = load.find (loadqry, fields)
        loadlist = list(loaddocs)
        if loadlist:
            #Need to use json_util.default to handle conversion of datetime into jason.  
            df = pd.read_json(json.dumps(loadlist, default=json_util.default))
            print df.head()
            print ''
        '''

except pymongo.errors.PyMongoError as e:
    print str(end) + ': Error:', e

