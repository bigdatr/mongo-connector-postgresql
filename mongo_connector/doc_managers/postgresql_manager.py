# coding: utf8

import json
import logging
import os.path
import traceback

import psycopg2
from bson.objectid import ObjectId
from mongo_connector.doc_managers.doc_manager_base import DocManagerBase
from mongo_connector.doc_managers.formatters import DocumentFlattener
from mongo_connector.errors import InvalidConfiguration
from psycopg2.extensions import register_adapter

from mongo_connector.doc_managers.mappings import is_mapped, get_mapped_field, get_mapped_document, get_primary_key
from mongo_connector.doc_managers.sql import sql_table_exists, sql_create_table, sql_insert, sql_delete_rows, \
    sql_bulk_insert, object_id_adapter
from mongo_connector.doc_managers.utils import get_array_fields, db_and_collection

MAPPINGS_JSON_FILE_NAME = 'mappings.json'

LOG = logging.getLogger(__name__)


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

        register_adapter(ObjectId, object_id_adapter)

        if not os.path.isfile(MAPPINGS_JSON_FILE_NAME):
            raise InvalidConfiguration("no mapping file found")

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
                            indices = [u"INDEX idx_{0}__creation_date ON {0} (_creationdate DESC)".format(collection)] + \
                                      self.mappings[database][collection].get('indices', [])

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

                            for index in indices:
                                cur.execute("CREATE " + index)

                            self.commit()

    def stop(self):
        pass

    def upsert(self, doc, namespace, timestamp):
        if not is_mapped(self.mappings, namespace):
            return

        try:
            with self.pgsql.cursor() as cursor:
                self._upsert(namespace, doc, cursor, timestamp)
                self.commit()
        except Exception as e:
            LOG.error("Impossible to upsert %s to %s\n%s", doc, namespace, traceback.format_exc())

    def _upsert(self, namespace, document, cursor, timestamp):
        db, collection = db_and_collection(namespace)

        mapped_document = get_mapped_document(self.mappings, document, namespace)

        if mapped_document:
            sql_insert(cursor, collection, mapped_document, self.mappings[db][collection]['pk'])

            for arrayField in get_array_fields(self.mappings, db, collection, document):
                dest = self.mappings[db][collection][arrayField]['dest']
                fk = self.mappings[db][collection][arrayField]['fk']
                dest_namespace = u"{0}.{1}".format(db, dest)

                for arrayItem in document[arrayField]:
                    arrayItem[fk] = mapped_document[get_primary_key(self.mappings, namespace)]
                    self._upsert(dest_namespace, document, cursor, timestamp)

    def get_linked_tables(self, database, collection):
        linked_tables = []

        for field in self.mappings[database][collection]:
            field_mapping = self.mappings[database][collection][field]

            if 'fk' in field_mapping:
                linked_tables.append(field_mapping['dest'])

        return linked_tables

    def bulk_upsert(self, documents, namespace, timestamp):
        LOG.info('Inspecting %s...', namespace)

        if is_mapped(self.mappings, namespace):
            LOG.info('Mapping found for %s !...', namespace)
            LOG.info('Deleting all rows before update %s !...', namespace)

            db, collection = db_and_collection(namespace)
            for linked_table in self.get_linked_tables(db, collection):
                sql_delete_rows(self.pgsql.cursor(), linked_table)

            sql_delete_rows(self.pgsql.cursor(), collection)
            self.commit()

            self._bulk_upsert(documents, namespace)
            LOG.info('%s done.', namespace)

    def _bulk_upsert(self, documents, namespace):
        with self.pgsql.cursor() as cursor:
            document_buffer = []
            insert_accumulator = 0

            for document in documents:
                document_buffer.append(document)
                insert_accumulator += 1

                if insert_accumulator % self.chunk_size == 0:
                    sql_bulk_insert(cursor, self.mappings, namespace, document_buffer)

                    self.commit()
                    document_buffer = []

                    LOG.info('%s %s copied...', insert_accumulator, namespace)

            sql_bulk_insert(cursor, self.mappings, namespace, document_buffer)
            self.commit()

    def update(self, document_id, update_spec, namespace, timestamp):
        if not is_mapped(self.mappings, namespace):
            return

        db, collection = db_and_collection(namespace)
        primary_key = self.mappings[db][collection]['pk']

        update_conds = []
        updates = {primary_key: str(document_id)}

        if not self.partial_update(update_spec):
            self.upsert(update_spec, namespace, timestamp)
            return

        if "$set" in update_spec:
            updates.update(update_spec["$set"])
            for update in updates:
                if is_mapped(self.mappings, namespace, update):
                    update_conds.append(get_mapped_field(self.mappings, namespace, update) + " = %(" + update + ")s")

        if "$unset" in update_spec:
            removes = update_spec["$unset"]
            for remove in removes:
                if is_mapped(self.mappings, namespace, remove):
                    update_conds.append(get_mapped_field(self.mappings, namespace, remove) + " = NULL")

        if "$inc" in update_spec:
            increments = update_spec["$inc"]
            for increment in increments:
                if is_mapped(self.mappings, namespace, increment):
                    mapped_fied = get_mapped_field(self.mappings, namespace, increment)
                    update_conds.append(mapped_fied + "= " + mapped_fied + " + 1")

        if not update_conds:
            return

        sql = "UPDATE {0} SET {1} WHERE {2} = %({2})s".format(collection, ",".join(update_conds), primary_key)
        with self.pgsql.cursor() as cursor:
            cursor.execute(sql, updates)
            self.commit()

    def partial_update(self, update_spec):
        return "$set" in update_spec or "$unset" in update_spec or "$inc" in update_spec \
               or "$mul" in update_spec or "$rename" in update_spec \
               or "$min" in update_spec or "$max" in update_spec

    def remove(self, document_id, namespace, timestamp):
        if not is_mapped(self.mappings, namespace):
            return

        with self.pgsql.cursor() as cursor:
            db, collection = db_and_collection(namespace)
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
