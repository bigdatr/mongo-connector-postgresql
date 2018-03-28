from mongo_connector.doc_managers.bigdatr_sql import sql_create_table
from mongo_connector.doc_managers.postgresql_manager import ARRAY_OF_SCALARS_TYPE
from mongo_connector.doc_managers.postgresql_manager import ARRAY_TYPE
from mongo_connector.doc_managers.postgresql_manager import DocManager


class DocManager(DocManager):
    def _init_schema(self):
        self.prepare_mappings()

        for database in self.mappings:
            for collection in self.mappings[database]:
                self.insert_accumulator[collection] = 0

                with self.pgsql.cursor() as cursor:
                    pk_found = False
                    pk_name = self.mappings[database][collection]['pk']
                    columns = ['_creationdate TIMESTAMP']
                    indices = [u"CREATE INDEX IF NOT EXISTS idx_{0}__creation_date ON {0} (_creationdate DESC)".format(
                        collection)] + \
                              self.mappings[database][collection].get('indices', [])

                    for column in self.mappings[database][collection]:
                        column_mapping = self.mappings[database][collection][column]

                        if 'dest' in column_mapping:
                            name = column_mapping['dest']
                            column_type = column_mapping['type']

                            constraints = ''
                            if name == pk_name:
                                constraints = "CONSTRAINT {0}_PK PRIMARY KEY".format(collection.upper())
                                pk_found = True

                            if column_type != ARRAY_TYPE and column_type != ARRAY_OF_SCALARS_TYPE:
                                columns.append(name + ' ' + column_type + ' ' + constraints)

                            if 'index' in column_mapping:
                                indices.append(
                                    u"CREATE INDEX IF NOT EXISTS idx_{2}_{0} ON {1} ({0})".format(name, collection,
                                                                                                  collection.replace(
                                                                                                      '.', '_')))
                    if not pk_found:
                        columns.append(pk_name + ' SERIAL CONSTRAINT ' + collection.upper() + '_PK PRIMARY KEY')

                    sql_create_table(cursor, collection, columns)

                    for index in indices:
                        cursor.execute(index)

                    self.commit()

    def stop(self):
        self.pgsql.close()
