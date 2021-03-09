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
        self.log.info(f'start checking {self.name}, url={self.url}')
        while True:
            if self.stop_flag:
                break
            try:
                start_time = time.time()
                r = requests.get(self.url)
                response_time = time.time() - start_time
                content_check = bool(pattern.search(r.text)) # check pattern
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
                result_str = json.dumps(result).encode('utf-8')
                self.log.debug(f'{r.status_code} - {self.url}')
                self.result_queue.put(result_str)
            except Exception as e:
                self.log.error(e)
            time.sleep(self.interval)

    def stop(self):
        self.stop_flag = True


def main(args, log):
    log.info(f'Checker start.')
    checkers = []  # store website checker threads
    config_file = './config.ini' # default config file name
    website_yaml_file = './website.yaml' # default website yaml file name
    result_queue = Queue()  # queue to forward result to main thread
    db = None
    try:
        check_interval = float(args.interval)
        if check_interval < 1:
            log.warning(f'interval too small, set to 1.')
            check_interval = 1
        log.info(f'website check interval: {check_interval} seconds.')

        kf_cfg = get_config('kafka', filepath=config_file) # read kafka config
        kf = Kafka(kf_cfg['host'],
                   kf_cfg['port'],
                   kf_cfg['cafile'],
                   kf_cfg['certfile'],
                   kf_cfg['keyfile'],
                   log)
        if kf.set_client() == False:
            raise Exception("error to set kafka client.")
        topic = kf.get_topic(kf_cfg['topic']) # get Kafka topic
        if topic == False:
            raise Exception("error to get kafka topic.")

        # run website checker threads
        websites = read_yaml(website_yaml_file)
        for name, info in websites.items():
            checker = WebsiteChecker(name,
                                     info['url'],
                                     info['pattern'],
                                     result_queue,
                                     log,
                                     interval=check_interval)
            checker.start()
            checkers.append(checker)

        # send check result to kafka
        log.info(f'produce result to kafka')
        with topic.get_sync_producer() as producer:
            while True:
                result = result_queue.get() # get result from queue
                log.debug(f'produce - {result}')
                producer.produce(bytes(result))
    except Exception as e:
        log.error(e)
    except KeyboardInterrupt:
        log.info("Checker exiting.")
    finally:
        for checker in checkers:
            checker.stop()


if __name__ == "__main__":
    parser = ArgumentParser(description='Website monitor - checker')
    parser.add_argument('--daemon', action='store_true', help='daemon mode')
    parser.add_argument('--debug', action='store_true', help='enable debug')
    parser.add_argument('--interval', default=10, help='checking interval')
    args = parser.parse_args()
    if args.debug:
        log = get_log(level=logging.DEBUG)
    else:
        log = get_log()
    if args.daemon: # run in deamon mode
        with daemon.DaemonContext(working_directory=os.getcwd()):
            main(args, log)
    else:
        main(args, log)
