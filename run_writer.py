#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import daemon
import os

from datetime import datetime
from argparse import ArgumentParser

from common.utils import *
from common.kafka import Kafka
from common.database import PostgreSQL

from pykafka.exceptions import SocketDisconnectedError, LeaderNotAvailable


def main(argv, log):
    log.info(f'Writer start.')
    websites = dict()
    config_file = './config.ini'  # default config file name
    kafka_tls = True  # enable tls connection to kafka
    db = None
    kf = None
    try:
        if args.config != None:
            config_file = args.config
        log.info(f'configure file: {config_file}')
        if args.notls != None:
            kafka_tls = False
        log.info(f'kafka tls connection: {kafka_tls}')

        db_cfg = get_config(config_file, 'postgre')
        for key in ('host', 'port', 'dbname', 'user', 'password'):
            if key not in db_cfg:
                raise(f'database config missing {key}.')
        db = PostgreSQL(db_cfg['host'],
                        db_cfg['port'],
                        db_cfg['dbname'],
                        db_cfg['user'],
                        db_cfg['password'],
                        log=log)
        if db.connect() != True:  # set connection
            log.error("unable to connect database.")
            raise Exception("error to set kafka client.")
        db.initialise_database()  # create tables if not exist

        # get all websites from database
        rows = db.get_website()
        for row in rows:
            name = row[0]
            url = row[1]
            websites[name] = url
        log.info(f'websites in database: {websites}')

        # read kafka config
        kf_cfg = get_config(config_file, 'kafka')
        for key in ('host', 'port', 'cafile', 'certfile', 'keyfile', 'topic'):
            if key not in kf_cfg:
                raise(f'kafka config missing {key}.')
        kf = Kafka(kf_cfg['host'],
                   kf_cfg['port'],
                   kf_cfg['cafile'],
                   kf_cfg['certfile'],
                   kf_cfg['keyfile'],
                   log)
        if kf.set_client(tls=kafka_tls) == False:  # set kafka client
            raise Exception("error to set kafka client.")
        topic_name = kf_cfg['topic']
        topic = kf.get_topic(topic_name)
        if topic == False:
            raise Exception("error to get kafka topic.")

        # get topic offset from database.
        row = db.get_topic_offset(topic_name)
        if row == False:
            log.info(f'add topic to database. topic={topic_name}')
            now = datetime.now()
            created_time = now.strftime("%Y-%m-%d %H:%M:%S")
            db.add_topic(topic_name, created_time)
            db_offset = 0
        else:
            log.info(f'topic offset in database is {row}.')
            db_offset = int(row[0])

        # ger kafka topic consumer
        consumer_group_name = 'writer'
        log.info(f'get simple consumer, group={consumer_group_name}')
        consumer = topic.get_simple_consumer(
            consumer_group=consumer_group_name,
            consumer_timeout_ms=2000)

        log.info(f'start consuming messages.')
        while True:
            results = []  # bulk results to store into database
            for i in range(0, 100):
                try:
                    message = consumer.consume()
                    if message == None:
                        break
                except (SocketDisconnectedError) as e:
                    # handling connection loss
                    log.warning(f'consumer socket disconnect. {e}')
                    time.sleep(1)
                    consumer = topic.get_simple_consumer(
                        consumer_group=consumer_group_name,
                        consumer_timeout_ms=2000)
                    break
                except Exception as e:
                    log.warning(f'consumer exception occur. {e}')
                    break
                # processing message
                log.debug(f'consuming message, offset={message.offset}')
                result = json.loads(message.value.decode('utf-8'))
                name = result['name']
                url = result['url']

                # append new offset result to bulk result when offset value
                # in database is less than offset value in kafka topic
                if db_offset < message.offset:
                    if name not in websites:  # add new website to database
                        now = datetime.now()
                        created_time = now.strftime("%Y-%m-%d %H:%M:%S")
                        log.info(f'add new website {name}, {url}')
                        db.add_website(created_time, name, url)
                        websites[name] = url
                    created_at = result['created_at']
                    status_code = result['status_code']
                    response_time = result['response_time']
                    content_check = result['content_check']
                    values = (created_at, name, status_code,
                              response_time, content_check)
                    results.append(values)

            # write results to database
            if results != []:
                result_count = len(results)
                log.debug(f'write {result_count} new results to database.')
                db_offset += result_count
                db.add_check_results(results, topic_name, db_offset)

    except Exception as e:
        log.error(e)
    except KeyboardInterrupt:
        log.info("stop running writer.")
    finally:
        if db != None:
            db.disconnect()


if __name__ == "__main__":
    name = 'writer'
    parser = ArgumentParser(description=f'Website monitor - {name}')
    parser.add_argument('--daemon', action='store_true', help='daemon mode')
    parser.add_argument('--config', help='config file path')
    parser.add_argument('--debug', action='store_true', help='enable debug')
    parser.add_argument('--notls', action='store_true', help='disable tls')
    parser.add_argument('--filelog', action='store_true', help='log to file')
    args = parser.parse_args()
    if args.debug:
        if args.filelog:
            log = get_log(name=name, level=logging.DEBUG, filelog=True)
        else:
            log = get_log(name=name, level=logging.DEBUG)
    else:
        if args.filelog:
            log = get_log(name=name, filelog=True)
        else:
            log = get_log(name=name)

    if args.daemon:  # run in deamon mode
        with daemon.DaemonContext(working_directory=os.getcwd()):
            main(args, log)
    else:
        main(args, log)
