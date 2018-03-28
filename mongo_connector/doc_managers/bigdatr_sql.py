from mongo_connector.doc_managers.sql import to_sql_list, unique


def sql_create_table(cursor, tableName, columns):
    columns.sort()
    sql = u"CREATE TABLE IF NOT EXISTS {0} {1}".format(tableName.lower(), to_sql_list(unique(columns)))
    cursor.execute(sql)
