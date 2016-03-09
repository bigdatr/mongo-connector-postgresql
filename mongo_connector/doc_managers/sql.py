#!/usr/bin/env python
# coding: utf8
from mongo_connector.doc_managers.mappings import get_mapped_document
from mongo_connector.doc_managers.utils import extract_creation_date, get_array_fields, db_and_collection


def to_sql_list(items):
    return ' ({0}) '.format(','.join(items))


def sql_table_exists(cursor, table):
    cursor.execute(""
                   "SELECT EXISTS ("
                   "        SELECT 1 "
                   "FROM   information_schema.tables "
                   "WHERE  table_schema = 'public' "
                   "AND    table_name = '" + table.lower() + "' );")
    return cursor.fetchone()[0]


def sql_delete_rows(cursor, table):
    cursor.execute(u"DELETE FROM {0}".format(table.lower()))


def sql_create_table(cursor, tableName, columns):
    sql = u"CREATE TABLE {0} {1}".format(tableName.lower(), to_sql_list(columns))
    cursor.execute(sql)


def sql_bulk_insert(cursor, mappings, namespace, documents):
    if not documents:
        return

    db, collection = db_and_collection(namespace)

    primary_key = mappings[db][collection]['pk']
    keys = [v['dest'] for k, v in mappings[db][collection].iteritems() if 'dest' in v and v['type'] != '_ARRAY']
    values = []

    for document in documents:
        mapped_document = get_mapped_document(mappings, document, namespace)
        document_values = [to_sql_value(extract_creation_date(mapped_document, mappings[db][collection]['pk']))]

        for key in keys:
            if key in mapped_document:
                document_values.append(to_sql_value(mapped_document[key]))
            else:
                document_values.append(to_sql_value(None))
        values.append(u"({0})".format(u','.join(document_values)))

        for arrayField in get_array_fields(mappings, db, collection, document):
            dest = mappings[db][collection][arrayField]['dest']
            fk = mappings[db][collection][arrayField]['fk']
            linked_documents = document[arrayField]
            for linked_document in linked_documents:
                linked_document[fk] = mapped_document[primary_key]

            sql_bulk_insert(cursor, mappings, "{0}.{1}".format(db, dest), linked_documents)

    sql = u"INSERT INTO {0} ({1}) VALUES {2}".format(collection, u','.join(['_creationDate'] + keys), u",".join(values))
    cursor.execute(sql)


def sql_insert(cursor, tableName, document, primary_key, logger):
    creationDate = extract_creation_date(document, primary_key)
    if creationDate is not None:
        document['_creationDate'] = creationDate

    keys = document.keys()
    valuesPlaceholder = ("%(" + column_name + ")s" for column_name in keys)

    if primary_key in document:
        sql = u"INSERT INTO {0} {1} VALUES {2} ON CONFLICT ({3}) DO UPDATE SET {1} = {2}".format(
                tableName,
                to_sql_list(keys),
                to_sql_list(valuesPlaceholder),
                primary_key
        )
    else:
        sql = u"INSERT INTO {0} {1} VALUES {2}".format(
                tableName,
                to_sql_list(keys),
                to_sql_list(valuesPlaceholder),
                primary_key
        )

    try:
        cursor.execute(sql, document)
    except Exception as e:
        logger.error(u"Impossible to upsert the following document %s : %s", document, e)


def to_sql_value(value):
    if value is None:
        return 'NULL'

    if isinstance(value, (int, long, float, complex)):
        return str(value)

    if isinstance(value, bool):
        return str(value).upper()

    if isinstance(value, basestring):
        escaped_value = value.replace("'", "''")
        return u"'{0}'".format(escaped_value)

    return u"'{0}'".format(str(value))
