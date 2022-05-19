## Website Monitor
Website Monitor is simple monitoring tool to check website status and store result
into database.

It leverages Apache Kafka to distribute website status and
stores results to PostgreSQL database. It is written in python3.6

## Version
- 06-Feb-2021 1.0 initial version
- 19-May-2022 1.1 run without tls and several bugfix

## Required packages installation
- python3-requests 2.18.4
- python3-daemon 2.1.2
- python3-psycopg2 2.7.4
- python3-pykafka 2.8.0

## Component
- checker - check websites status and forward result to kafka. It is Kafka producer.
- writer - fetch result from kafka and store into database. It is Kafka consumer.

## Configuration file syntax
- config.ini
```
[kafka]
    host = kafka host address
    port = kafka port number
    cafile = /path/to/cafile
    certfile = /path/to/service.cert
    keyfile = /path/to/service.key
    topic = topic name

[postgre]
    host = postgre database host address
    port = port number
    dbname = database name
    user = database username
    password = database password

```
cafile, certfile and keyfile can be empty if running without TLS.

- website.yaml
```
<websit name>:
    url: <website url>
    pattern: <pattern to search in website content>
```
Maximum 32 characters for website name.
Maximum 128 characters for url.

## Usage
```
usage: run_checker.py [-h] [--daemon] [--config CONFIG] [--website WEBSITE]
                      [--debug] [--filelog] [--notls] [--interval INTERVAL]

Website monitor - checker

optional arguments:
  -h, --help           show this help message and exit
  --daemon             daemon mode
  --config CONFIG      config file path
  --website WEBSITE    webiste list file
  --debug              enable debug
  --notls              disable tls connection to kafka
  --filelog            log to file
  --interval INTERVAL  checking interval
```
```
usage: run_writer.py [-h] [--daemon] [--config CONFIG] [--debug] [--filelog]

Website monitor - writer

optional arguments:
  -h, --help       show this help message and exit
  --daemon         daemon mode
  --config CONFIG  config file path
  --debug          enable debug
  --notls          disable tls connection to kafka
  --filelog        log to file
```

## Database and tables
Create database
```
root@e55e688a4bf0:/# psql --username=postgres
psql (14.3 (Debian 14.3-1.pgdg110+1))
Type "help" for help.

postgres=# \list
                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges   
-----------+----------+----------+------------+------------+-----------------------
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 | 
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
(3 rows)

postgres=# CREATE DATABASE webmonitor;
CREATE DATABASE
```

Tables are created automatically when you run writer.py
```
CREATE TABLE IF NOT EXISTS topic (
    name VARCHAR (32) PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    topic_offset BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS website (
    name VARCHAR (32) PRIMARY KEY,
    created_at TIMESTAMP,
    url VARCHAR (128) NOT NULL
);

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


webmonitor=> select * from topic;
  name   |     created_at      | updated_at | topic_offset
---------+---------------------+------------+--------------
 monitor | 2021-06-03 20:25:17 |            |        44644
(1 row)

webmonitor=> select * from status_history ORDER BY id DESC limit 10;
  id   |     created_at      | website_name | status_code | response_time | content_check
-------+---------------------+--------------+-------------+---------------+---------------
 44911 | 2021-03-18 09:34:35 | google       |         200 |         0.493 | t
 44910 | 2021-03-18 09:34:25 | google       |         200 |         0.481 | t
 44909 | 2021-03-18 09:34:14 | google       |         200 |         0.511 | t
 44908 | 2021-03-18 09:34:04 | google       |         200 |         0.625 | t
 44907 | 2021-03-18 09:33:53 | google       |         200 |         0.498 | t
 44906 | 2021-03-18 09:33:42 | google       |         200 |         0.518 | t
 44905 | 2021-03-18 09:33:32 | google       |         200 |           0.5 | t
 44904 | 2021-03-18 09:33:21 | google       |         200 |         0.504 | t
 44903 | 2021-03-18 09:33:11 | google       |         200 |         0.496 | t
 44902 | 2021-03-18 09:33:00 | google       |         200 |         0.515 | t
(10 rows)

webmonitor=> select * from website;
   name    |     created_at      |          url          
-----------+---------------------+-----------------------
 google    | 2021-06-03 19:35:51 | https://google.com
 google.au | 2021-07-03 01:45:17 | https://google.com.au
(2 rows)
```

## Note
- make sure one partition for a topic.

## Troubleshoot
#### Get error with datestyle in PostgreSQL
```
[2022-05-19 15:33:16,982] [ERROR] [database] date/time field value out of range: "19-05-2022 15:33:16"
LINE 7:                 VALUES('19-05-2022 15:33:16', 'google', 'htt...
                               ^
HINT:  Perhaps you need a different "datestyle" setting.
```
```
webmonitor=# show datestyle;
 DateStyle 
-----------
 ISO, DMY
(1 row)
```
Make sure write timestamp in string 'yyyy-mm-dd HH:MM:SS' format. The PostgreSQL use ISO 8601 style date and time by default.


#### No leader for topic in single kafka docker instance environment.
```
[2022-05-19 00:59:15,448] [DEBUG] [cluster] Updating cluster, attempt 1/3
[2022-05-19 00:59:15,449] [DEBUG] [connection] Connecting to localhost:9092
[2022-05-19 00:59:15,451] [DEBUG] [connection] Successfully connected to localhost:9092
[2022-05-19 00:59:15,455] [WARNING] [broker] Leader not available for topic 'b'monitor'' partition 0.

I have no name!@kafka:/$ kafka-topics.sh --describe --topic monitor --bootstrap-server kafka:9092
Topic: monitor	TopicId: uCeI1w_CSj2vO047evpESQ	PartitionCount: 1	ReplicationFactor: 1	Configs: segment.bytes=1073741824
	Topic: monitor	Partition: 0	Leader: none	Replicas: 1001	Isr: 1001
```

Recreate the topic and ensure Leader is not none for the topic.
```
root@ubuntu:~/kafka# docker run --rm --network kafka-net -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181 bitnami/kafka:latest kafka-topics.sh --create --topic monitor --replication-factor 1 --partitions 1 --bootstrap-server kafka:9092
kafka 01:24:46.58 
kafka 01:24:46.59 Welcome to the Bitnami kafka container
kafka 01:24:46.59 Subscribe to project updates by watching https://github.com/bitnami/bitnami-docker-kafka
kafka 01:24:46.59 Submit issues and feature requests at https://github.com/bitnami/bitnami-docker-kafka/issues
kafka 01:24:46.59 

Created topic monitor.

root@ubuntu:~/kafka#  docker run --rm --network kafka-net -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181 bitnami/kafka:latest kafka-topics.sh --describe --topic monitor --bootstrap-server kafka:9092
kafka 01:25:19.15 
kafka 01:25:19.15 Welcome to the Bitnami kafka container
kafka 01:25:19.16 Subscribe to project updates by watching https://github.com/bitnami/bitnami-docker-kafka
kafka 01:25:19.16 Submit issues and feature requests at https://github.com/bitnami/bitnami-docker-kafka/issues
kafka 01:25:19.16 

Topic: monitor	TopicId: Jgz4Zb8WQ3yYSSyfmIBh7w	PartitionCount: 1	ReplicationFactor: 1	Configs: segment.bytes=1073741824
	Topic: monitor	Partition: 0	Leader: 1	Replicas: 1	Isr: 1
```

## To do
- add feature to create and write check result into specific table name.
- configuration verifying
- improve logging
- create topic automatically. seems like no library support to create topic.
  (https://github.com/Parsely/pykafka/issues/514)
- handle kafka connection loss
- handle postgre db connection loss
- website checking test
- prevent sql injection attach
- add "updated_at" column in website table, add feature to writer to update
  last update time.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.
Please make sure to update tests as appropriate.

## Reference
https://www.postgresql.org/docs/14/datatype-datetime.html

## License
Apache License 2.0
