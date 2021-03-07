#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import extras


class PostgreSQL():
    def __init__(self, host, port, dbname, user, password, log):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.log = log
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(host=self.host,
                                         port=self.port,
                                         dbname=self.dbname,
                                         user=self.user,
                                         password=self.password)
            return True
        except Exception as e:
            self.log.error(e)
            return False

    def disconnect(self):
        if self.conn != None:
            return self.conn.close()

    def initialise_database(self):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS topic (
                    name VARCHAR (32) PRIMARY KEY,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    topic_offset BIGINT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS website (
                    name VARCHAR (128) PRIMARY KEY,
                    created_at TIMESTAMP,
                    url VARCHAR (128) NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS status_history (
                    id bigserial PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    website_name VARCHAR (32) NOT NULL,
                    status_code INT NOT NULL,
                    response_time FLOAT (3) NOT NULL,
                    content_check BOOLEAN,
                    CONSTRAINT fk_website
                        FOREIGN KEY(website_name)
                            REFERENCES website(name)
                );
            """)
            self.conn.commit()
            return True
        except Exception as e:
            self.log.error(e)
            return False
        finally:
            cur.close()

    def get_website(self, name=None, url=None):
        try:
            cur = self.conn.cursor()
            if name == None and url == None:
                cur.execute("""
                    SELECT
                        name,
                        url
                    FROM
                        website
                """)
            else:
                cur.execute("""
                    SELECT
                        name,
                        url
                    FROM
                        website
                    WHERE
                        name='%s'
                    AND
                        url='%s'
                """ % (name, url))
            return cur.fetchall()
        except Exception as e:
            self.log.error(e)
            return False
        finally:
            cur.close()

    def add_website(self, created_at, name, url):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO website (
                    created_at,
                    name,
                    url
                )
                VALUES('%s', '%s', '%s')
            """ % (created_at, name, url))
            self.conn.commit()
            return True
        except Exception as e:
            self.log.error(e)
            return False
        finally:
            cur.close()

    def add_topic(self, name, created_at):
        """ create
        """
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO topic (
                    name,
                    created_at,
                    topic_offset
                )
                VALUES ('%s', '%s', 0);
            """ % (name, created_at))
            self.conn.commit()
            return True
        except Exception as e:
            self.log.error(e)
            return False
        finally:
            cur.close()

    def get_topic_offset(self, name):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT
                    topic_offset
                FROM
                    topic
                WHERE
                    name = '%s'
            """ % name)
            ret =  cur.fetchone()
            if ret == None:
                return False
            return ret
        except Exception as e:
            self.log.error(e)
            return False
        finally:
            cur.close()

    def add_check_results(self, results, topic_name, topic_offset):
        """ Insert bulk status data and
            update offset value in topic
            Arguments:
            - results: [(...), ]
            - topic_name: str
            - topic_offset: int
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                INSERT INTO status_history (
                    created_at,
                    website_name,
                    status_code,
                    response_time,
                    content_check
                )
                VALUES %s
                """
                extras.execute_values(cur, query, results)
                cur.execute("""
                    UPDATE topic
                    SET topic_offset = %s
                    WHERE name = '%s'
                """ % (topic_offset, topic_name))
            self.conn.commit()
            return True
        except Exception as e:
            self.log.error(e)
            return False
