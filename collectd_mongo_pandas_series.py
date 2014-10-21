#!/usr/bin/env python

import datetime as dt
import pandas as pd
import pandas.tools as tl
import pymongo
import os
import sys
import csv

today = dt.datetime.utcnow()
today = today.replace (hour=0, minute=0, second=0, microsecond=0)

MONGO_URL = os.environ['MONGO_URL']

try:
    conn = pymongo.Connection (MONGO_URL, safe=True)
except pymongo.errors.ConnectionFailure as e:
    print 'Error: check  your MongoDB connectivity'
    print 'Error:', e
    sys.exit()

# Set the mongo database to the one for inventory information
db = conn.collectd

# Set the Mongo collection to the one for flavor information
diskcol = db.disk
cpucol = db.cpu

query = {"time" : { "$gte" : dt.datetime(2014,1,1, 0, 0), "$lte" : dt.datetime(2014,1,1, 0, 5) } }
selector = {'_id': 0}

try:
    # Input 1: Get data from disk collection
    diskdocs = diskcol.find (query, selector).sort("time", pymongo.DESCENDING).limit(500)
    # Input 2: Get data from cpu collection
    cpudocs = cpucol.find (query, selector).sort("time", pymongo.DESCENDING).limit(500)

except pymongo.errors.PyMongoError as e:
    print 'Error: unable to query for instance info'
    print 'Error:', e

# Transform the collectd JSON data to tabular form.
disklist = list(diskdocs)
cpulist = list(cpudocs)
# The disk metrics have both read and write values in the same document.
# We split the values based on their position in the list.
diskfirst = [{key: val[0] if type(val) is list else val for key, val in elem.items()} for elem in disklist]
disksecond = [{key: val[1] if type(val) is list else val for key, val in elem.items()} for elem in disklist]
# CPU metrics only have one value but it is stored as a list with one element.
cpu = [{key: val[0] if type(val) is list else val for key, val in elem.items()} for elem in cpulist]

print diskfirst[0]
print disksecond[0]
print cpu[0]

df1 = pd.DataFrame (diskfirst)
df2 = pd.DataFrame (disksecond)
df3 = pd.DataFrame (cpu)

merged = pd.concat ([df1, df2, df3], ignore_index=True)
print merged.shape
print merged.head()
print merged.tail()

merged.to_csv('collectd.csv')
#pivoted = tl.pivot.pivot_table (merged, rows=['time', 'host'], cols=['plugin', 'plugin_instance', 'type', 'type_instance'], values='values')
#print pivoted.head()
