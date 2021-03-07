## Website Monitor
Website Monitor is simple monitoring tool to check website status and store result
into database.

It leverages Apache Kafka to distribute website status log and
stores check result into PostgreSQL database. It is written in python3.6

## Version
- 06-Feb-2021 1.0 initial version

## required packages installation via apt
- python3-requests
- python3-daemon
- python3-psycopg2

## Component
- checker - check websites status and forward result to kafka. It is Kafka producer.
- writer - fetch result from kafka and store into database. It is Kafka consumer.


## Configuration syntax
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
google:
    url: website url
    pattern: pattern to search in website content
```

## Usage
```
usage: run_checker.py [-h] [--daemon] [--debug] [--interval INTERVAL]

Website monitor

optional arguments:
  -h, --help           show this help message and exit
  --daemon             daemon mode
  --debug              enable debug
  --interval INTERVAL  checking interval
```
```
usage: run_writer.py [-h] [--daemon] [--debug]

Website monitor

optional arguments:
  -h, --help  show this help message and exit
  --daemon    daemon mode
  --debug     enable debug
```

## Database tables
tables are created automatically when you run writer.py
```
CREATE TABLE IF NOT EXISTS topic (
    name VARCHAR (32) PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    topic_offset BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS website (
    name VARCHAR (128) PRIMARY KEY,
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
```

## Note
make sure one partition for a topic.

## To fix
- daemon mode does not work

## Contributing
Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.
Please make sure to update tests as appropriate.

## License
Apache License 2.0
