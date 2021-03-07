## Web Monitor
Web Monitor is simple monitoring tool to check website status and store result
into database.

It leverages Apache Kafka to distribute website status log and
stores check result into PostgreSQL database. It is written in python3.6

## Version
- 06-Feb-2021 1.0 initial version

## required packages installation via apt
- python3-requests
- python3-daemon
- python3-psycopg2

## Configuration example
- config.ini
```
[kafka]
    host = kafka host url
    port = kafka port number
    cafile = /path/to/cafile
    certfile = /path/to/service.cert
    keyfile = /path/to/service.key
    topic = topic name

[postgre]
    host = postgre database host url
    port = port number
    dbname = database name
    user = database username
    password = database password

```
- website.yaml
```
google:
    url: https://google.com
    pattern: Google
```

## Usage
```

```

## Database
```

```

## Note
make sure one partition for a topic.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.
Please make sure to update tests as appropriate.

## License
Apache License 2.0
