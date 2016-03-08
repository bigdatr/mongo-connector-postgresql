#!/usr/bin/env python
# coding: utf8
from psycopg2._psycopg import IntegrityError

from doc_managers.utils import extract_creation_date


def to_sql_list(items):
    return ' ({0}) '.format(','.join(items))


def sql_table_exists(cursor, tableName):
    cursor.execute(""
                   "SELECT EXISTS ( "
                   "        SELECT 1 "
                   "FROM   information_schema.tables "
                   "WHERE  table_schema = 'public' "
                   "AND    table_name = '" + tableName.lower() + "' );")
    return cursor.fetchone()[0]


def sql_create_table(cursor, tableName, columns):
    sql = "CREATE TABLE {0} {1}".format(tableName.lower(), to_sql_list(columns))
    cursor.execute(sql)


def sql_insert(cursor, tableName, document, primary_key, logger):
    creationDate = extract_creation_date(document, primary_key)
    if creationDate is not None:
        document['_creationDate'] = creationDate

    keys = document.keys()
    valuesPlaceholder = ("%(" + column_name + ")s" for column_name in keys)

    if primary_key in document:
        sql = "INSERT INTO {0} {1} VALUES {2} ON CONFLICT ({3}) DO UPDATE SET {1} = {2}".format(
                tableName,
                to_sql_list(keys),
                to_sql_list(valuesPlaceholder),
                primary_key
        )
    else:
        sql = "INSERT INTO {0} {1} VALUES {2}".format(
                tableName,
                to_sql_list(keys),
                to_sql_list(valuesPlaceholder),
                primary_key
        )

    try:
        cursor.execute(sql, document)
    except IntegrityError:
        logger.error("Impossible to upsert the following document %s", document)
