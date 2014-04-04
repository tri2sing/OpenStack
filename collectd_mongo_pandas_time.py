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


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

end = dtm.now()
endmidnight = end.replace (hour=0, minute=0, second=0, microsecond=0)

# For testing purpose reduced the duration to a few hours
#start = end + delta (days=-1)
start = end + delta (hours=-8)

# The MongoDB should not be set to use a usename and password for access
MONGO_URL = os.environ['MONGO_URL']

try:
    conn = pymongo.Connection (MONGO_URL, safe=True)
except pymongo.errors.ConnectionFailure as e:
    print 'Error: check  your MongoDB connectivity'
    print 'Error:', e
    sys.exit()

# Databases to use
db2 = conn.collectd

# Collections to use
cpu = db2.cpu
disk = db2.disk
load = db2.load

cpuqry = {"time" : { "$gte" : start, "$lte" : end }, 'type_instance': 'system'}
cpufields = {'_id': 0, 'time': 1, 'host': 1, 'plugin_instance': 1, 'values': 1}

try:
    print dtm.now()
    cpudocs = cpu.find (cpuqry, cpufields)
    if cpudocs.count() != 0:  # This statement is slow; trying to figure out a solution
        print cpudocs.count()
        cpulist = list(cpudocs)
        #jsoncpu = json.dumps(cpulist, default=json_util.default)
        jsoncpu = json.dumps(cpulist, default=date_handler)
        df = pd.read_json(jsoncpu)
        #print df.describe()
        print df.head()
        print df.tail()
        print ''
    else:
        print "No cpu data for time range" 
    print dtm.now()

except pymongo.errors.PyMongoError as e:
    print str(end) + ': Error:', e

