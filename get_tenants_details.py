#!/usr/bin/env python

import os

from keystoneclient.v2_0 import client as ksc

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

def main():
    kstone = ksc.Client (**get_kston_info())
    tenants = kstone.tenants.list ()
    if tenants:
        for tenant in tenants:
            print tenant.name +', ',
            try:
                if tenant.createdby.startswith('ad_'):
                    print tenant.createdby[3:]
                else:
                    print tenant.createdby
            except AttributeError:
                print 'NotDefined'

if __name__ == '__main__':
    main()

