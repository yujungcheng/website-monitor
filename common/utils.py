#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import sys
import os
import yaml

from configparser import ConfigParser
from collections import OrderedDict


def get_log(level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            logfile='/var/log/web_monitor.log'):
    logging.basicConfig(level=level, format=format)
    return logging


def get_config(section_name, filepath='./config.ini'):
    try:
        if not os.path.exists(filepath):
            raise Exception("monitor config file not found.")
        conf = dict()
        parser = ConfigParser()
        parser.read(filepath)
        if parser.has_section(section_name):
            options = parser.items(section_name)
            for option in options:
                conf[option[0]] = option[1]
        return conf
    except Exception as e:
        print(e)
        sys.exit(1)


def read_yaml(filepath='./website.yaml'):
    try:
        if not os.path.exists(filepath):
            raise Exception("website config file not found.")
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return OrderedDict(data)
    except Exception as e:
        print(e)
        sys.exit(1)
