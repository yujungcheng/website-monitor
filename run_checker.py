#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import daemon
import requests
import re
import os

from argparse import ArgumentParser
from threading import Thread
from queue import Queue
from datetime import datetime

from common.utils import *
from common.kafka import Kafka

from pykafka.exceptions import SocketDisconnectedError, LeaderNotAvailable


class WebsiteChecker(Thread):
    def __init__(self, name, url, pattern, result_queue, log, interval=10):
        Thread.__init__(self)
        self.name = name
        self.url = url
        self.pattern = pattern
        self.result_queue = result_queue
        self.log = log
        self.interval = interval
        self.stop_flag = False

    def run(self):
        pattern = re.compile(self.pattern)
        self.log.info(f'start checking {self.name}, url={self.url}, '
                      f'interval={self.interval}')
        while True:
            if self.stop_flag:
                break
            try:
                result = self.check_website(pattern)
                self.result_queue.put(result)
            except Exception as e:
                self.log.error(e)
            time.sleep(self.interval)

    def stop(self):
        self.stop_flag = True

    def check_website(self, pattern):
        start_time = time.time()
        r = requests.get(self.url)
        response_time = time.time() - start_time
        content_check = bool(pattern.search(r.text))  # check pattern
        time_tuple = time.localtime(start_time)
        created_at = time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)
        result = {
            'name': self.name,
            'url': self.url,
            'created_at': created_at,
            'response_time': f'{response_time:.3f}',
            'status_code': r.status_code,
            'content_check': content_check,
        }
        self.log.debug(f'{r.status_code} - {self.url}')
        return json.dumps(result).encode('utf-8')


def main(args, log):
    log.info(f'Checker start.')
    checkers = []  # store website checker threads
    config_file = './config.ini'  # default config file name
    website_yaml_file = './website.yaml'  # default website yaml file name
    result_queue = Queue(3000)  # queue to forward result to main thread
    kafka_tls = True  # enable tls connection to kafka
    try:
        check_interval = float(args.interval)
        if check_interval < 1:
            log.warning(f'interval too small, set to 1.')
            check_interval = 1
        log.info(f'website check interval: {check_interval} seconds.')
        if args.config != None:
            config_file = args.config
        log.info(f'configure file: {config_file}')
        if args.website != None:
            website_yaml_file = args.website
        log.info(f'website yaml file: {website_yaml_file}')
        if args.notls != None:
            kafka_tls = False
        log.info(f'kafka tls connection: {kafka_tls}')

        # connect kafka and get topic
        kf_cfg = get_config(config_file, 'kafka')  # read kafka config
        for key in ('host', 'port', 'cafile', 'certfile', 'keyfile', 'topic'):
            if key not in kf_cfg:
                raise(f'kafka config missing {key}.')
        kf = Kafka(kf_cfg['host'],
                   kf_cfg['port'],
                   kf_cfg['cafile'],
                   kf_cfg['certfile'],
                   kf_cfg['keyfile'],
                   log)
        if kf.set_client(tls=kafka_tls) == False:
            raise Exception("error to set kafka client.")
        topic = kf.get_topic(kf_cfg['topic'])  # get Kafka topic
        if topic == False:
            raise Exception("error to get kafka topic.")

        # run website checker threads
        websites = read_yaml(website_yaml_file)
        for name, info in websites.items():
            for key in ['url', 'pattern']:
                if key not in info:
                    raise(f'website config missing {key}')
            checker = WebsiteChecker(name,
                                     info['url'],
                                     info['pattern'],
                                     result_queue,
                                     log,
                                     interval=check_interval)
            checker.start()
            checkers.append(checker)
    except Exception as e:
        log.error(f'Exiting checker. {e}')
        for checker in checkers:
            checker.stop()
        exit(1)

    # produce check result to kafka
    log.info(f'producing result to kafka.')
    try:
        with topic.get_sync_producer() as producer:
            log.info(f'created sync producer.')
            while True:
                result = result_queue.get()  # get result from queue
                log.debug(f'produce - {result}')
                producer.produce(bytes(result))
    except (SocketDisconnectedError, LeaderNotAvailable) as e:
        log.error(f'{e}')
    except KeyboardInterrupt:
        log.info(f'Stop running checker.')
    except Exception as e:
        log.error(f'Unknown exception occur. {e}')
    finally:
        for checker in checkers:
            checker.stop()


if __name__ == "__main__":
    name = 'checker'
    parser = ArgumentParser(description=f'Website monitor - {name}')
    parser.add_argument('--daemon', action='store_true', help='daemon mode')
    parser.add_argument('--config', help='config file path')
    parser.add_argument('--website', help='webiste list file')
    parser.add_argument('--debug', action='store_true', help='enable debug')
    parser.add_argument('--notls', action='store_true', help='disable tls')
    parser.add_argument('--filelog', action='store_true', help='log to file')
    parser.add_argument('--interval', default=10, help='checking interval')
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