#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pykafka import KafkaClient, SslConfig
from pykafka.common import OffsetType


class Kafka():
    def __init__(self, host, port, cafile, certfile, keyfile, log):
        self.host = host
        self.port = port
        self.cafile = cafile
        self.certfile = certfile
        self.keyfile = keyfile
        self.log = log
        self.client = None
        self.offset_type = OffsetType

    def set_client(self, tls=True):
        try:
            hosts = f'{self.host}:{self.port}'
            if tls:
                ssl_config = SslConfig(cafile=self.cafile,
                                    certfile=self.certfile,
                                    keyfile=self.keyfile)
                self.client = KafkaClient(hosts=hosts, ssl_config=ssl_config)
            else:
                self.client = KafkaClient(hosts=hosts)
            return True
        except Exception as e:
            self.log.error(e)
            return False

    def get_topic(self, topic):
        try:
            return self.client.topics[topic]
        except Exception as e:
            self.log.error(e)
            return False
