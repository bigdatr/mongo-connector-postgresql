import json
import os.path

import psycopg2
from mongo_connector.compat import u
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DocumentFlattener

from doc_managers.sql import sqlTableExists, sqlCreateTable, sqlInsert
from mongo_connector import errors
from utils import extractDocumentCreationDate, isCollectionMapped

MAPPINGS_JSON_FILE_NAME = 'mappings.json'


class DocManager(DocManagerBase):
    """DocManager that connects to any SQL database"""

    def __init__(self, url, unique_key='_id', auto_commit_interval=None, chunk_size=100, **kwargs):
        self.url = url
        self.unique_key = unique_key
        self.auto_commit_interval = auto_commit_interval
        self.chunk_size = chunk_size
        self._formatter = DocumentFlattener()
        self.pgsql = psycopg2.connect(url)

        if not os.path.isfile(MAPPINGS_JSON_FILE_NAME):
            raise errors.InvalidConfiguration("no mapping file found")

        with open(MAPPINGS_JSON_FILE_NAME) as mappings_file:
            self.mappings = json.load(mappings_file)

        self._init_schema()

    def _init_schema(self):
        for database in self.mappings:
            for collection in self.mappings[database]:

                with self.pgsql.cursor() as cursor:

                    if not sqlTableExists(cursor, collection):
                        with self.pgsql.cursor() as cur:

                            columns = ['_creationdate TIMESTAMP']

                            for column in self.mappings[database][collection]:
                                columns.append(column + " " + self.mappings[database][collection][column]["type"])

                            sqlCreateTable(cur, collection, columns)
                            self.commit()

    def stop(self):
        pass

    def upsert(self, doc, namespace, timestamp):
        # TODO: Refactor once bulkUpsert is done

        db, coll = self._db_and_collection(namespace)
        cleaned = self._clean_and_flatten_doc(doc, namespace, timestamp)
        columns = []
        for key in cleaned:
            columns.append(key)
        valuesPlaceholder = ("%(" + column_name + ")s" for column_name in columns)

        with self.pgsql.cursor() as cursor:
            sql = "INSERT INTO " + coll.lower() + " (" + (",").join(columns) + ") VALUES (" + (",").join(
                    valuesPlaceholder) + ")"
            cursor.execute(sql, cleaned)
            self.commit()

    def bulk_upsert(self, docs, namespace, timestamp):
        if isCollectionMapped(self.mappings, namespace):
            db, collection = self._db_and_collection(namespace)
            documents = (self._clean_and_flatten_doc(d, namespace, timestamp) for d in docs)

            for document in documents:
                values = document
                values['_creationdate'] = extractDocumentCreationDate(document)

                columns = []
                for key in document:
                    columns.append(key)

                with self.pgsql.cursor() as cursor:
                    sqlInsert(cursor, collection, columns, values)
                    self.commit()

    def update(self, document_id, update_spec, namespace, timestamp):
        db, coll = self._db_and_collection(namespace)

        update_conds = []
        updates = {"_id": document_id}
        if "$set" in update_spec:
            updates.update(update_spec["$set"])
            for update in updates:
                update_conds.append(update + "= %(" + update + ")s")
        if "$unset" in update_spec:
            removes = update_spec["$unset"]
            for remove in removes:
                update_conds.append(remove + "= NULL")
        if "$inc" in update_spec:
            increments = update_spec["$inc"]
            for increment in increments:
                update_conds.append(increment + "= " + increment + "+1")

        sql = "UPDATE " + coll + " SET " + ",".join(update_conds) + " WHERE _id = %(_id)s"
        with self.pgsql.cursor() as cursor:
            cursor.execute(sql, updates)
            self.commit()

    def remove(self, document_id, namespace, timestamp):
        with self.pgsql.cursor() as cursor:
            database, coll = self._db_and_collection(namespace)
            cursor.execute("DELETE from " + coll.lower() + " where id = %s;", document_id)

    def search(self, start_ts, end_ts):
        pass

    def commit(self):
        self.pgsql.commit()

    def get_last_doc(self):
        pass

    def handle_command(self, doc, namespace, timestamp):
        pass

    def _db_and_collection(self, namespace):
        return namespace.split('.', 1)

    def _clean_and_flatten_doc(self, doc, namespace, timestamp):
        """Reformats the given document before insertion into Solr.
        This method reformats the document in the following ways:
          - removes extraneous fields that aren't defined in schema.xml
          - unwinds arrays in order to find and later flatten sub-documents
          - flattens the document so that there are no sub-documents, and every
            value is associated with its dot-separated path of keys
          - inserts namespace and timestamp metadata into the document in order
            to handle rollbacks
        An example:
          {"a": 2,
           "b": {
             "c": {
               "d": 5
             }
           },
           "e": [6, 7, 8]
          }
        becomes:
          {"a": 2, "b.c.d": 5, "e.0": 6, "e.1": 7, "e.2": 8}
        """

        # Translate the _id field to whatever unique key we're using.
        if '_id' in doc:
            doc[self.unique_key] = u(doc.pop("_id"))

        # PGSQL cannot index fields within sub-documents, so flatten documents
        # with the dot-separated path to each value as the respective key
        flat_doc = self._formatter.format_document(doc)

        # Extract column names and mappings for this table
        db, coll = self._db_and_collection(namespace)
        if db in self.mappings:
            mappings_db = self.mappings[db]
            if coll in mappings_db:
                mappings_coll = mappings_db[coll]

                # Only include fields that are explicitly provided in the schema
                def include_field(field):
                    return field in mappings_coll

                return dict((k.replace(".", "_"), v) for k, v in flat_doc.items() if include_field(k))
        return {}
