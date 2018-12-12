This tool helps you manage a [NYC-DB][] instance via Docker containers.

[NYC-DB]: https://github.com/aepyornis/nyc-db

## Quick start

### Install dependencies

You will need Python 3.7 and Docker.

First, create a virtualenv and enter it:

```
python3 -m venv venv
source venv/bin/activate   # Or 'venv\Scripts\activate' on Windows
```

Then install dependencies:

```
pip install -r requirements.txt
```

### Configuration

Create an `.env` file from the example:

```
cp .env.example .env       # Or 'copy .env.example .env' on Windows
```

Now edit the file as needed.

#### Using AWS (optional)

Make sure you've edited your `.env` to contain values for
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`NYCDB_DOCKER_MACHINE_NAME`.

Run the following to provision an EC2 instance for your NYC-DB:

```
python bud.py machine:aws-create
```

If you ever want to undo this action, you can run:

```
python bud.py machine:rm
```

You can also find your EC2 instance in the [AWS EC2 console][]: it will
have the same name as your `NYCDB_DOCKER_MACHINE_NAME` setting.

**Note:** You will also want to make sure that the `docker-machine` security
group supports inbound connections on port 5432 (Postgres). You can do
this by visiting the [AWS EC2 security groups console][].

[AWS EC2 console]: https://console.aws.amazon.com/ec2/v2/home
[AWS EC2 security groups console]: https://console.aws.amazon.com/ec2/v2/home#SecurityGroups:search=docker-machine

### Populating your NYC-DB

To populate your NYC-DB, run:

```
python bud.py populate
```

Note that this command just kicks off the process, so it will return
relatively quickly. If you're using AWS, you're free to put your computer
to sleep, since all the hard work is being done in the cloud.

To check the status of the process, run:

```
python bud.py populate:status
```

## Tests

```
pytest && mypy . && echo "yay everything works"
```
