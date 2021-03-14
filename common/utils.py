#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import sys
import os
import yaml

from logging.handlers import RotatingFileHandler
from configparser import ConfigParser
from collections import OrderedDict


def get_log(name='logger', level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
            filelog=False
            ):
    if filelog:
        return get_rotating_file_log(name=name,
                                     level=level,
                                     format=format,
                                     logfile=f'{name}.log')
    logging.basicConfig(level=level, format=format)
    return logging


def get_rotating_file_log(name, level, format, logfile,
                          maxBytes=10240000,  # 10MB
                          backupCount=2,
                          delay=True
                          ):
    handler = RotatingFileHandler(logfile,
                                  maxBytes=maxBytes,
                                  backupCount=backupCount,
                                  delay=delay
                                  )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format))

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


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
