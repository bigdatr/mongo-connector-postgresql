#!/usr/bin/env python
# coding: utf8

from setuptools import setup

setup(
        name='mongo-connector-postgresql',
        version='1.1.1',
        description='Doc Manager Postgresl for Mongo connector Distribution Utilities',
        keywords=['mongo-connector', 'mongo', 'mongodb', 'postgresql'],
        platforms=["any"],
        author=u'Hugo Lassiège, Maxime Gaudin',
        author_email='hugo@hopwork.com, maxime@hopwork.com',
        install_requires=[
            'mongo_connector >= 2.5.1',
            'psycopg2 >= 2.6.1',
            'future >= 0.16.0',
            'jsonschema >= 2.6.0'
        ],
        tests_require=[
            'mock>=2.0.0',
            'aloe>=0.1.12',
            'testing.postgresql>=1.3.0',
            'mongo-orchestration>=0.6.9'
        ],
        license="http://www.apache.org/licenses/LICENSE-2.0.html",
        url='https://github.com/Hopwork/mongo-connector-postgresql',
        packages=["mongo_connector", "mongo_connector.doc_managers"],
        test_suite='tests'
)
