#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys

from common.database import PostgreSQL
from common.kafka import Kafka
from common.utils import get_config, get_log, read_yaml


def test_get_config():
    db_config = get_config('config.ini', 'postgre')
    assert isinstance(db_config, dict)
    assert 'host' in db_config
    assert 'port' in db_config
    assert 'dbname' in db_config
    assert 'user' in db_config
    assert 'password' in db_config

    kf_config = get_config('config.ini', 'kafka')
    assert isinstance(kf_config, dict)
    assert 'host' in kf_config
    assert 'port' in kf_config
    assert 'cafile' in kf_config
    assert 'certfile' in kf_config
    assert 'keyfile' in kf_config
    assert 'topic' in kf_config

def test_read_yaml():
    websites = read_yaml('website.yaml')
    assert isinstance(websites, dict)
    for key, values in websites.items():
        assert 'url' in values
        assert 'pattern' in values

def test_website_checker():
    import json
    from run_checker import WebsiteChecker
    from queue import Queue

    queue = Queue(1)
    checker = WebsiteChecker('test',
                             'https://google.com',
                             'google',
                             queue,
                             logging,
                             interval=1)
    checker.start()
    checker.stop()
    result = queue.get()
    result = json.loads(result.decode('utf-8'))
    assert isinstance(result, dict)
    assert 'name' in result
    assert 'url' in result
    assert 'created_at' in result
    assert 'response_time' in result
    assert 'status_code' in result
    assert 'content_check' in result


if __name__ == '__main__':
    test_get_config()
    test_read_yaml()
    test_website_checker()
