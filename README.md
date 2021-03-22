## Website Monitor
Website Monitor is simple monitoring tool to check website status and store result
into database.

It leverages Apache Kafka to distribute website status log and
stores check result into PostgreSQL database. It is written in python3.6

## Version
- 06-Feb-2021 1.0 initial version

## Required packages installation
- python3-requests 2.18.4
- python3-daemon 2.1.2
- python3-psycopg2 2.7.4
- pykafka 2.8.0

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
                      [--debug] [--filelog] [--interval INTERVAL]

Website monitor - checker

optional arguments:
  -h, --help           show this help message and exit
  --daemon             daemon mode
  --config CONFIG      config file path
  --website WEBSITE    webiste list file
  --debug              enable debug
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
  --filelog        log to file

```

## Database tables
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

## License
Apache License 2.0
