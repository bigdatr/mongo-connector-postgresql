#!/usr/bin/env python
# coding: utf8
from doc_managers.utils import extractDocumentCreationDate


def toSQLList(items):
    return ' ({0}) '.format(','.join(items))

def sqlTableExists(cursor, tableName):
    cursor.execute(""
                   "SELECT EXISTS ( "
                   "        SELECT 1 "
                   "FROM   information_schema.tables "
                   "WHERE  table_schema = 'public' "
                   "AND    table_name = '" + tableName.lower() + "' );")
    return cursor.fetchone()[0]


def sqlCreateTable(cursor, tableName, columns):
    sql = "CREATE TABLE {0} {1}".format(tableName.lower(), toSQLList(columns))
    cursor.execute(sql)


def sqlInsert(cursor, tableName, document):
    document['_creationDate'] = extractDocumentCreationDate(document)

    keys = document.keys()
    valuesPlaceholder = ("%(" + column_name + ")s" for column_name in keys)
    sql = "INSERT INTO {0} {1} VALUES {2}".format(tableName, toSQLList(keys), toSQLList(valuesPlaceholder))

    cursor.execute(sql, document)
