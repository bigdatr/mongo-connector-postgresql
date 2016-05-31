mongo-connector-postgresql is used to make the bridge between Postgresql and mongodb.
It acts as a river from mongodb to Postgresql.

This connector is a plugin for `Mongo Connector <https://github.com/10gen-labs/mongo-connector/wiki>`__ and all the
credits goes to them.

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

The easiest way to install mongo-connector and our extension is with:

    pip install mongo-connector pg-mongo-connector

Using this connector
~~~~~~~~~~~~~~~~~~~~

Please check out the `mongo-connector documentation<https://github.com/mongodb-labs/mongo-connector/wiki>`_ beforehand
since only the ``pg-mongo-connector`` specifics are written here.

Just call the mongo-connector and specify this plugin with the option "-d":

  mongo-connector  -t postgresql://localhost -d postgresql_manager -c config.json

The url could follow any of the syntax defined by `libpq connection string <http://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING>`__.

This connector use its own mapping file to determine the fields that should be written in postgresl and their types.
This file should be named mappings.json. Here is a sample :

    {
    	"my_mongo_database": {
    		"my_mongo_collection": {
    		    "pk": "id",
                 "indices": [
                     "UNIQUE INDEX category_idx ON LeadMonitoring(category)",
                     "UNIQUE INDEX conversationDate_idx ON LeadMonitoring(conversation_date)"
                ],
    			"_id": {
    				"dest": "id",
    				"type": "TEXT"
    			},
    			"description": {
    				"dest": "description",
    				"type": "TEXT"
    			},
    			"enable": {
    				"dest": "enabled",
    				"type": "BOOLEAN"
    			},
    			"myobject.subproperty": {
    				"dest": "subproperty",
    				"type": "TEXT"
    			}
    		}
    	}
    }

Please notice the following :

- The ``pk`` field is mandatory and should point to the destination's primary key
- If the original document in mongodb has a embedded document, everything is flattened to be inserted in postgresql.

The connector also support arrays of documents. Let say your Mongo database stores the following documents :

    {
    	"posts": {
    		"name": "Check out the mongo -> postgres connector",
    		"content": "Inspiring blog post",
    		"comments": [{
    			"user": "Elon Musk",
    			"comment": "What a revolution !"
    		}, {
    			"user": "Kevin P. Ryan",
    			"comment": "Nice !"
    		}]
    	}
    }

To allow the connector to map the post objects AND its comments, you should use the following mapping :

    {
        "my_mongo_database": {
            "posts": {
                "pk": "id",
                "_id": {
                    "dest": "id",
                    "type": "TEXT"
                },
                "content": {
                    "dest": "description",
                    "type": "TEXT"
                },
                "comments": {
                    "dest": "comments",
                    "type": "_ARRAY",
                    "fk": "post_id"
                }
            },
            "comments": {
                "pk": "id",
                 "post_id": {
                    "dest": "post_id",
                    "type": "TEXT"
                },
                "user": {
                    "dest": "user",
                    "type": "TEXT"
                },
                "comment": {
                    "dest": "comment",
                    "type": "TEXT"
                }
            }
        }
    }

Please notice the following :

- The type ``_ARRAY`` is used to indicate to the connector that the field is an array
- The additional field ``fk`` is provided to indicate to the connector where to store the root document id. This field is mandatory for an array
- The comments' mapping declares only the primary key but no mapping exists. The connector will generate the identifier automatically
- The foreign key must be declared in the comments table so it's created with the schema initialization

Contribution / Limitations
--------------------------

We searched for a software like this for quiet a time and we are confident that other people would need it.
However, some features/improvements are currently lacking :

- Their is no way to map a mongo collection to a differently named postgres table
- There is virtually no error handling, especially if the mapping is wrong (e.g. missing pk field)
- The connector does not support arrays of scalars (but do support arrays of documents)
- Rollbacks are not supported
- System commands are not supported (e.g. create collection)
- Only operations on the 'public' schema are allowed
- Currently, because of our use of the ON CONFLICT directive, only PostgreSQL >= 9.5 can be used

Even if this code is battle tested (we use it in production and fix for bugs every time we see one), it is far from
perfect. Indeed, it was written quickly, by Python aware (but still Java specialized) developers in a "proof of concept"
perspective. Therefore, one can easily improve the code quality, the test coverage (which is currently 0%),
the architecture or write more 'Pythonic' code.