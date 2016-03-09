import json
import logging
import os.path

import psycopg2
from mongo_connector.compat import u
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DocumentFlattener

from mongo_connector import errors
from mongo_connector.doc_managers.sql import sql_table_exists, sql_create_table, sql_insert, sql_delete_rows, \
    sql_bulk_insert
from mongo_connector.doc_managers.utils import get_array_fields

MAPPINGS_JSON_FILE_NAME = 'mappings.json'


class DocManager(DocManagerBase):
    """DocManager that connects to any SQL database"""

    def insert_file(self, f, namespace, timestamp):
        pass

    def __init__(self, url, unique_key='_id', auto_commit_interval=None, chunk_size=100, **kwargs):
        self.url = url
        self.unique_key = unique_key
        self.auto_commit_interval = auto_commit_interval
        self.chunk_size = chunk_size
        self._formatter = DocumentFlattener()
        self.pgsql = psycopg2.connect(url)
        self.insert_accumulator = {}

        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
        steam_handler = logging.StreamHandler()
        steam_handler.setFormatter(formatter)
        steam_handler.setLevel(logging.DEBUG)

        self.logger = logging.getLogger('SQLDocManager')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(steam_handler)

        if not os.path.isfile(MAPPINGS_JSON_FILE_NAME):
            raise errors.InvalidConfiguration("no mapping file found")

        with open(MAPPINGS_JSON_FILE_NAME) as mappings_file:
            self.mappings = json.load(mappings_file)

        self._init_schema()

    def _init_schema(self):
        for database in self.mappings:
            for collection in self.mappings[database]:
                self.insert_accumulator[collection] = 0

                with self.pgsql.cursor() as cursor:

                    if not sql_table_exists(cursor, collection):
                        with self.pgsql.cursor() as cur:
                            pk_found = False
                            pk_name = self.mappings[database][collection]['pk']
                            columns = ['_creationdate TIMESTAMP']

                            for column in self.mappings[database][collection]:
                                if 'dest' in self.mappings[database][collection][column]:
                                    name = self.mappings[database][collection][column]['dest']
                                    column_type = self.mappings[database][collection][column]['type']

                                    constraints = ''
                                    if name == pk_name:
                                        constraints = "CONSTRAINT {0}_PK PRIMARY KEY".format(collection.upper())
                                        pk_found = True

                                    if column_type != '_ARRAY':
                                        columns.append(name + ' ' + column_type + ' ' + constraints)

                            if not pk_found:
                                columns.append(pk_name + ' SERIAL CONSTRAINT ' + collection.upper() + '_PK PRIMARY KEY')

                            sql_create_table(cur, collection, columns)
                            self.commit()

    def stop(self):
        pass

    def upsert(self, doc, namespace, timestamp):
        if not self._is_mapped(namespace):
            return

        with self.pgsql.cursor() as cursor:
            self._upsert(namespace, doc, cursor, timestamp)
            self.commit()

    def _upsert(self, namespace, document, cursor, timestamp):
        db, collection = self._db_and_collection(namespace)

        mapped_document = self._mapped_document(document, namespace)
        sql_insert(cursor, collection, mapped_document, self.mappings[db][collection]['pk'], self.logger)

        for arrayField in get_array_fields(self.mappings, db, collection, document):
            dest = self.mappings[db][collection][arrayField]['dest']
            fk = self.mappings[db][collection][arrayField]['fk']
            values = document[arrayField]

            self.insert_linked_documents(fk, str(document['_id']), db, dest, values, timestamp)

    def bulk_upsert(self, documents, namespace, timestamp):
        self.logger.info('Inspecting %s...', namespace)

        if self._is_mapped(namespace):
            self.logger.info('Mapping found for %s !...', namespace)
            self.logger.info('Deleting all rows before update %s !...', namespace)

            db, collection = self._db_and_collection(namespace)
            sql_delete_rows(self.pgsql.cursor(), collection)
            self.commit()

            self._bulk_upsert(documents, namespace, timestamp)
            self.logger.info('%s done.', namespace)

    def _bulk_upsert(self, documents, namespace, timestamp):
        db, collection = self._db_and_collection(namespace)

        with self.pgsql.cursor() as cursor:
            document_buffer = []
            for document in documents:
                document_buffer.append(self._mapped_document(document, namespace))
                self.insert_accumulator[collection] += 1

                if self.insert_accumulator[collection] % self.chunk_size == 0:
                    sql_bulk_insert(cursor, self.mappings, db, collection, document_buffer)
                    self.commit()
                    document_buffer = []

                    self.logger.info('%s %s copied...', self.insert_accumulator[collection], namespace)

            sql_bulk_insert(cursor, self.mappings, db, collection, document_buffer)
            self.commit()

    def insert_linked_documents(self, fk_name, source_id, db, table, documents, timestamp):
        for document in documents:
            document[fk_name] = source_id

        self._bulk_upsert(documents, db + '.' + table, timestamp)

    def update(self, document_id, update_spec, namespace, timestamp):
        if not self._is_mapped(namespace):
            return

        db, collection = self._db_and_collection(namespace)
        primary_key = self.mappings[db][collection]['pk']

        update_conds = []
        updates = {primary_key: str(document_id)}
        if "$set" in update_spec:
            updates.update(update_spec["$set"])
            for update in updates:
                if self._is_mapped(namespace, update):
                    update_conds.append(self._get_mapped_field(namespace, update) + " = %(" + update + ")s")

        if "$unset" in update_spec:
            removes = update_spec["$unset"]
            for remove in removes:
                if self._is_mapped(namespace, remove):
                    update_conds.append(self._get_mapped_field(namespace, remove) + " = NULL")

        if "$inc" in update_spec:
            increments = update_spec["$inc"]
            for increment in increments:
                if self._is_mapped(namespace, increment):
                    mapped_fied = self._get_mapped_field(namespace, increment)
                    update_conds.append(mapped_fied + "= " + mapped_fied + " + 1")

        if not update_conds:
            return

        sql = "UPDATE {0} SET {1} WHERE {2} = %({2})s".format(collection, ",".join(update_conds), primary_key)
        with self.pgsql.cursor() as cursor:
            cursor.execute(sql, updates)
            self.commit()

    def remove(self, document_id, namespace, timestamp):
        if not self._is_mapped(namespace):
            return

        with self.pgsql.cursor() as cursor:
            db, collection = self._db_and_collection(namespace)
            primary_key = self.mappings[db][collection]['pk']
            cursor.execute(
                    "DELETE from {0} WHERE {1} = '{2}';".format(collection.lower(), primary_key, str(document_id))
            )
            self.commit()

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

    def _clean_and_flatten_doc(self, doc, namespace):
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

                return dict((k, v) for k, v in flat_doc.items() if include_field(k))
        return {}

    def _mapped_document(self, document, namespace):
        flat_document = self._clean_and_flatten_doc(document, namespace)

        db, collection = self._db_and_collection(namespace)
        keys = flat_document.keys()

        for key in keys:
            if 'dest' in self.mappings[db][collection][key]:
                mappedKey = self.mappings[db][collection][key]['dest']
                flat_document[mappedKey] = flat_document.pop(key)

        return flat_document

    def _get_mapped_field(self, namespace, field_name):
        db, collection = self._db_and_collection(namespace)
        return self.mappings[db][collection][field_name]['dest']

    def _is_mapped(self, namespace, field_name=None):
        db, collection = self._db_and_collection(namespace)
        return db in self.mappings and collection in self.mappings[db] and \
               (field_name is None or field_name in self.mappings[db][collection])
