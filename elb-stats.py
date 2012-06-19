#!/usr/bin/env python

import re
import boto
import os
import httplib
import argparse
import sys
import socket
import dns.resolver
import time
import yaml

from boto.ec2.elb import *
from boto.ec2.instance import *

def req(server):
    http_conn = httplib.HTTPConnection(server, timeout=10)
    t1 = time.time()
    http_conn.request('GET', test_url)
    r = http_conn.getresponse()
    t2 = time.time()
    return r,t1,t2

def load_env(env_vars):
    for k, v in env_vars.iteritems():
        os.putenv(k, v)

def get_color(test):
    return {True: '\033[1;32m', False: '\033[1;31m'}[test]


if __name__ == "__main__":
    comma_list = ''
    elb_dns = ''
    slist = []
    t = []
    is_instance = False

    parser = argparse.ArgumentParser()
    parser.add_argument('action', help='aditional arguments', default=False, nargs='?', choices=('ping','oneline','hostname'))
    args = parser.parse_args()

    f = open('elb-stats.yml')
    yml_vars = yaml.load(f)
    f.close()

    load_env(yml_vars['environment'])
    test_server = yml_vars['settings']['test_server']
    elb_region = yml_vars['settings']['elb_region']
    elb_name_regex = yml_vars['settings']['elb_name_regex']
    test_url = yml_vars['settings']['test_url']

    os.system(os.getenv('EC2_HOME') + 'bin/ec2din --region ' + elb_region + ' > /tmp/srv.tmp')
    f = open('/tmp/srv.tmp', 'r')

    for line in f:
        field = line.split("\t")
        if field[0] == "RESERVATION":
            if t:
                slist.append(t)
                t = []
        if field[0] == "INSTANCE":
            t.append(field[1])
            t.append(field[3])
            t.append(field[4].split('.')[0])
            t.append(field[10])
        if field[0] == "TAG" and field[3] == "Name":
            t.append(field[4].rstrip('\n'))

    if t:
        slist.append(t)
        t = []

    f.close()
    os.remove('/tmp/srv.tmp')

    for rdata in dns.resolver.query(test_server, 'CNAME'):
        elb_dns = rdata.target

    conn = boto.ec2.elb.connect_to_region(elb_region)
    lbs = conn.get_all_load_balancers()
    for lb in lbs:
        out = ''
        if str(elb_dns).rstrip('.') == lb.dns_name:
            out = '\033[1;32m<= On Duty\033[1;m'
        if re.match(elb_name_regex, lb.name):
            if str(lb.name) not in str(elb_dns): continue
            if args.action == 'ping':
                try:
                    r,t1,t2 = req(lb.dns_name)
                    print lb.name,'\t',elb_dns,'\t',out,'\t',get_color(r.status == 200),r.status,'\033[1;m','\t',round((t2 - t1) * 1000,2),'ms'
                except:
                    print lb.name,'\t',elb_dns,out,'\t\033[1;31mTimeout\033[1;m'
            elif args.action != 'oneline':
                print lb.name,out

            instances = conn.describe_instance_health(lb.name)
            for i in instances:
                for s in slist:
                    if s[0] == i.instance_id:
                        if args.action == 'oneline':
                            comma_list = comma_list + s[1] + ','
                        elif args.action == 'ping':
                            try:
                                r,t1,t2 = req(s[1])
                                print s[0],'\t',s[1],'\t',i.state,'\t',get_color(r.status == 200),r.status,'\033[1;m','\t',round((t2 - t1) * 1000,2),'ms','\t',s[3],'\t',s[4]
                            except:
                                print s[0],'\t',s[1],'\t',i.state,'\t\033[1;31mTimeout\033[1;m'
                        elif args.action == 'hostname':
                            print s[0],'\t',s[1],'\t',s[2],'\t',i.state
                        else:
                            print s[0],'\t',s[1],'\t',i.state

                        break

    if args.action == 'oneline': print comma_list.rstrip(',')
