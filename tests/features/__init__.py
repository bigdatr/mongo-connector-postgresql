# -*- coding: utf-8 -*-

from contextlib import contextmanager
from aloe import world, step, around
from testing.postgresql import PostgresqlFactory

from psycopg2 import connect as pg_connect
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient

from future.moves.urllib.parse import urlparse, parse_qs
from time import sleep
import subprocess
import requests
import json
import os


@around.all
@contextmanager
def handle_pg_factory():
    world.DEVNULL = open('/dev/null', 'w')
    world.Postgresql = PostgresqlFactory(cache_initialized_db=True)
    world.Postgresql.clear_cache()
    yield
    world.Postgresql.clear_cache()
    world.DEVNULL.close()


@around.each_example
@contextmanager
def handle_databases(scenario, outline, steps):
    world.initial_dir = os.getcwd()
    world.result = {}
    world.envvars = {}

    info = requests.post(
        'http://localhost:8889/replica_sets',
        data=json.dumps({
            'id': 'rs0',
            'members': [{}]
        })
    )

    assert info.status_code == 200, \
        "Impossible to create replicat set: {}".format(info.status_code)

    world.mongo_server = info.json().get('server_id')
    world.mongo_uri = info.json().get('mongodb_uri')
    world.mongo_conn = MongoClient(world.mongo_uri, w=1, j=True)

    world.pg_server = world.Postgresql()
    world.pg_uri = world.pg_server.url()
    world.pg_conn = pg_connect(world.pg_uri)

    try:
        yield

    finally:
        world.mongo_conn.close()
        world.pg_conn.close()

        if hasattr(world, 'mongo_connector'):
            world.mongo_connector.terminate()
            world.mongo_connector.wait()

        ret = requests.delete(
            'http://localhost:8889/replica_sets/rs0'
        )
        assert ret.status_code == 204, \
            "Impossible to delete replica set: {}".format(ret.status_code)

        del world.mongo_server
        del world.mongo_uri

        world.pg_server.stop()

        os.chdir(world.initial_dir)
        del world.result
        del world.envvars


@step('I have the environment "([^"]*)"')
def initialize_environ(self, environ):
    os.chdir(os.path.join('tests', 'features', 'envs', environ))

    with open('envvars.json') as f:
        world.envvars = json.load(f)

    config = {
        'mainAddress': world.mongo_uri,
        'docManagers': [
            {
                'docManager': 'postgresql_manager',
                'targetURL': world.pg_uri,
                'args': {
                    'mongoUrl': world.mongo_uri
                }
            }
        ]
    }

    with open('config.json', 'w') as f:
        json.dump(config, f)

    parts = urlparse(world.mongo_uri)
    mongo_host = parts.hostname
    mongo_port = parts.port
    retcode = subprocess.call(
        'mongorestore -h rs0/{} --port {} -d {} dump'.format(
            mongo_host,
            mongo_port,
            world.envvars['DBNAME']
        ),
        stdout=world.DEVNULL,
        stderr=world.DEVNULL,
        shell=True
    )
    assert retcode == 0, "Impossible to insert dump in MongoDB database"


@step('I run mongo-connector')
def run_mongo_connector(self):
    trailing = ['mongo-connector.log', 'oplog.timestamp']
    for filename in trailing:
        if os.path.exists(filename):
            os.remove(filename)

    world.mongo_connector = subprocess.Popen(
        "mongo-connector -c {0}/config.json".format(os.getcwd()),
        shell=True,
        stdout=world.DEVNULL,
        stderr=world.DEVNULL,
    )


@step('I wait (\d+) seconds for the replication to be done')
def wait_for_replication(self, seconds):
    sleep(int(seconds))


@step('I delete documents from the collection')
def delete_collection(self):
    db = world.mongo_conn[world.envvars['DBNAME']]
    collection = db[world.envvars['COLLECTION']]
    spec = world.envvars.get('SPEC', {})
    collection.delete_many(spec)


@step('I update the collection')
def update_collection(self):
    db = world.mongo_conn[world.envvars['DBNAME']]
    collection = db[world.envvars['COLLECTION']]
    spec = world.envvars.get('SPEC', {})
    update = world.envvars['UPDATE']
    collection.update_many(spec, update)


@step('I run the SQL queries')
def run_sql_queries(self):
    for query in world.envvars['QUERIES']:
        with world.pg_conn.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(query['sql'])
            world.result[query['name']] = cursor.fetchall()


@step('the SQL queries should return the appropriate results')
def check_queries(self):
    for query in world.envvars['QUERIES']:
        qname = query['name']
        result = world.result[qname]
        expected = query['expected']
        msg = 'Query {0} did not return appropriate result: {1}'.format(
            qname,
            result
        )

        assert result == expected, msg
