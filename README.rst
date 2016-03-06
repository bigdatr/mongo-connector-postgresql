mongo-connector-postgresql is used to make the bridge between Postgresql and mongodb. It should act as a river from mongodb to Postgresql.

This connector is a plugin for `Mongo Connector <https://github.com/10gen-labs/mongo-connector/wiki>`__ and all the credits goes to them.

DISCLAIMER
----------

Please note: all tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. We disclaim any and all warranties, either express or implied, including but not limited to any warranty of noninfringement, merchantability, and/ or fitness for a particular purpose. We do not warrant that the technology will meet your requirements, that the operation thereof will be uninterrupted or error-free, or that any errors will be corrected.
Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.


System Overview
---------------

`mongo-connector-postgresql` creates a pipeline from a MongoDB cluster to Postgresql.  It
synchronizes data in MongoDB to the target then tails the MongoDB oplog, keeping
up with operations in MongoDB in real-time. It has been tested with Python 2.7 and Postgresql 9.5.

All the works of tailing the oplog, performing the initial sync is made by the `mongo-connector
<https://github.com/10gen-labs/mongo-connector/wiki>`__. So the first documentation you should read is on their website.

Getting Started
---------------

Installation
~~~~~~~~~~~~

The easiest way to install mongo-connector is with:

  pip install mongo-connector

Next, you have to install this project. It is not available on PyPi right now, so you have to build it from source:

  git clone https://github.com/Hopwork/mongo-connector-postgresql.git
  cd mongo-connector-postgresql
  python setup.py install

You may have to run ``python setup.py install`` with ``sudo``, depending
on where you're installing mongo-connector-postgresql and what privileges you have.

Using this connector
~~~~~~~~~~~~

Just call the mongo-connector and specify this plugin with the option "-d":

  mongo-connector  -t postgresql://localhost -d postgresql_manager -c config.json

The url could follow any of the syntax defined by `libpq connection string <http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING>`__.

This connector use its own mapping file to determine the fields that should be written in postgresl and their types.
This file should be named mappings.json. Here is a sample :

    {
      "my_schema": {
        "my_table" : {
          "_id" : {"dest" : "_id", "type" : "TEXT CONSTRAINT mytable_PK PRIMARY KEY"},
          "description" : {"dest" : "description", "type" : "TEXT"},
          "enable" : {"dest" : "enable", "type" : "boolean"},
          "myobject_subproperty" : {"dest" : "subproperty", "type" : "TEXT"}
        }
      }
    }

Note: it is possible to rename fields if you specify another field name in 'dest'.

Note 2: if the original document in mongodb has a embedded document, everything is flattened to be inserted in postgresql.

- Example : {myobject : { subproperty : "something"} } becomes   myobject_subproperty = "something"


Limitations
~~~~~~~~~~~~

This code is not perfect, it was written quickly in a "proof of concept" perspective. So there is a a lot of missing features :
- it is not possible to handle rollback of mongodb, search and get_last_doc are not implemented.
- it is not possible to handle system commands (create collection and so on), handle_command is not implemented
- the code to perform bulk_upsert is not optimized and I think it won't work on large volume
- chunk_size is not used
- it is only possible to work on the "public" schema" of postgresql
- this plugin don't handle correctly embedded arrays.


