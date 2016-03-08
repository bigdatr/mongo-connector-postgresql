#!/usr/bin/env python
# coding: utf8

from doc_managers.utils import extract_creation_date


def to_sql_list(items):
    return ' ({0}) '.format(','.join(items))


def sql_table_exists(cursor, table):
    cursor.execute(""
                   "SELECT EXISTS ( "
                   "        SELECT 1 "
                   "FROM   information_schema.tables "
                   "WHERE  table_schema = 'public' "
                   "AND    table_name = '" + table.lower() + "' );")
    return cursor.fetchone()[0]


def sql_delete_rows(cursor, table):
    cursor.execute("DELETE FROM {0}".format(table.lower()))


def sql_create_table(cursor, tableName, columns):
    sql = "CREATE TABLE {0} {1}".format(tableName.lower(), to_sql_list(columns))
    cursor.execute(sql)


def sql_bulk_insert(cursor, mappings, db, tableName, documents):
    keys = [v['dest'] for k, v in mappings[db][tableName].iteritems() if 'dest' in v]
    values = []

    for document in documents:
        document_values = [to_sql_value(extract_creation_date(document, mappings[db][tableName]['pk']))]

        for key in keys:
            if key in document:
                document_values.append(to_sql_value(document[key]))
            else:
                document_values.append(to_sql_value(None))
        values.append("({0})".format(','.join(document_values)))

    sql = "INSERT INTO {0} ({1}) VALUES {2}".format(tableName, ','.join(['_creationDate'] + keys), ",".join(values))
    cursor.execute(sql, document)


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
    except Exception as e:
        logger.error("Impossible to upsert the following document %s : %s", document, e)


def to_sql_value(value):
    if value is None:
        return 'NULL'

    if isinstance(value, (int, long, float, complex)):
        return str(value)

    if isinstance(value, bool):
        return str(value).upper()

    return "'{0}'".format(str(value))
