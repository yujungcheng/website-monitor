#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys

from common.database import PostgreSQL
from common.kafka import Kafka
from common.utils import *


logging.basicConfig()
test_stop = False

config_file = './config.ini'
website_yaml_file = './website.yaml'

##--------------------------------------------------------
# Configuration file test
##--------------------------------------------------------
print("[ Verify configuration file ]")

try:
    db_config = get_config(config_file, 'postgre')
    for key in ('host', 'port', 'dbname', 'user', 'password'):
        if key not in db_config:
            raise(f'- database config missing {key}.')

    kf_config = get_config(config_file, 'kafka')
    for key in ('host', 'port', 'cafile', 'certfile', 'keyfile', 'topic'):
        if key not in kf_config:
            raise(f'- kafka config missing {key}.')

except Exception as e:
    test_stop = True
    print(e)

try:
    websites = read_yaml(website_yaml_file)
    if not isinstance(websites, dict):
        raise(f'unable to parser yaml file.')

    if len(websites) == 0:
        raise(f'no website defined in yaml file.')
except Exception as e:
    test_stop = True
    print(e)

if test_stop:
    sys.exit(1)
print("=> Test pass\n")

##--------------------------------------------------------
# Database test
##--------------------------------------------------------
print("[ Test database connection ]")

try:
    dbhost = db_config['host']
    dbport = db_config['port']
    dbname = db_config['dbname']
    dbuser = db_config['user']
    dbpassword = db_config['password']

    test_db = PostgreSQL(dbhost, dbport, dbname, dbuser, dbpassword, logging)
    if test_db.connect() != True:
        raise('- Fail to connect database.')
except Exception as e:
    test_stop = True
    print(e)

if test_stop:
    sys.exit(1)
print("=> Test pass\n")

##--------------------------------------------------------
# Kafka test
##--------------------------------------------------------
print("[ Test kafka ]")

try:
    kfhost = kf_config['host']
    kfport = kf_config['port']
    kfcafile = kf_config['cafile']
    kfcertfile = kf_config['certfile']
    kfkeyfile = kf_config['keyfile']
    kftopic = kf_config['topic']

    test_kf = Kafka(kfhost, kfport, kfcafile, kfcertfile, kfkeyfile, kftopic)
    if test_kf.set_client() == False:
        raise Exception("error to set kafka client.")

    test_topic = test_kf.get_topic(kftopic)
    if test_topic == False:
        raise Exception("error to get kafka topic.")

    # test producer
    try:
        producer = test_topic.get_sync_producer()
        producer.stop()
        producer = None
    except Exception as e:
        raise Exception(e)

    # test consumer
    try:
        count = 0
        consumer = test_topic.get_simple_consumer(consumer_timeout_ms=1000)
        message = consumer.consume()
    except Exception as e:
        raise Exception(e)

except Exception as e:
    test_stop = True
    print(e)

if test_stop:
    sys.exit(1)
print("=> Test pass\n")

##--------------------------------------------------------
# Test website monitor
##--------------------------------------------------------
print("[ Test website monitor ]")

try:
    import time, os, subprocess, signal

    checker = subprocess.Popen(["./run_checker.py"])
    writer = subprocess.Popen(["./run_writer.py"])

    time.sleep(10)

    os.kill(checker.pid, signal.SIGUSR1)
    os.kill(writer.pid, signal.SIGUSR1)
except Exception as e:
    test_stop = True
    print(e)

if test_stop:
    sys.exit(1)
print("=> Test pass\n")
