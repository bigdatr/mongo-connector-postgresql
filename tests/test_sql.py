# -*- coding: utf-8 -*-

from unittest import TestCase, main
from mock import MagicMock

from mongo_connector.doc_managers import sql


class TestPostgreSQL(TestCase):
    def test_to_sql_list(self):
        items = ['1', '2']
        got = sql.to_sql_list(items)
        self.assertEqual(got, ' (1,2) ')

    def test_sql_table_exists(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = [1]
        got = sql.sql_table_exists(cursor, 'foo')

        self.assertEqual(len(cursor.execute.call_args[0]), 1)
        self.assertIn('foo', cursor.execute.call_args[0][0])
        self.assertEqual(got, 1)

    def test_sql_delete_rows(self):
        cursor = MagicMock()
        sql.sql_delete_rows(cursor, 'foo')
        cursor.execute.assert_called_with('DELETE FROM foo')

    def test_sql_delete_rows_where(self):
        cursor = MagicMock()
        sql.sql_delete_rows_where(cursor, 'foo', 'id = 1')
        cursor.execute.assert_called_with('DELETE FROM foo WHERE id = 1')

    def test_sql_drop_table(self):
        cursor = MagicMock()
        sql.sql_drop_table(cursor, 'foo')
        cursor.execute.assert_called_with('DROP TABLE foo')

    def test_sql_create_table(self):
        cursor = MagicMock()
        columns = [
            'id INTEGER',
            'bar TEXT'
        ]
        sql.sql_create_table(cursor, 'foo', columns)
        cursor.execute.assert_called_with(
            'CREATE TABLE foo  (id INTEGER,bar TEXT) '
        )

    def test_sql_bulk_insert(self):
        cursor = MagicMock()

        mapping = {
            'foo': {
                'bar': {
                    'pk': '_id',
                    'test': {
                        'type': 'TEXT',
                        'dest': 'test'
                    },
                    'bar.baz': {
                        'type': 'TEXT',
                        'dest': 'bar_baz'
                    }
                }
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'foo.bar', [])

        cursor.execute.assert_not_called()

        doc = {
            '_id': 'foo',
            'test': 'bar'
        }

        sql.sql_bulk_insert(cursor, mapping, 'foo.bar', [doc])
        cursor.execute.assert_called_with(
            "INSERT INTO bar (_creationDate,test,bar_baz) VALUES (NULL,'bar',NULL)"
        )

        doc = {
            '_id': 'foo',
            'test': 'bar',
            'bar': {
                'baz': 'biz'
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'foo.bar', [doc])
        cursor.execute.assert_called_with(
            "INSERT INTO bar (_creationDate,test,bar_baz) VALUES (NULL,'bar','biz')"
        )

    def test_sql_bulk_insert_array(self):
        cursor = MagicMock()

        mapping = {
            'foo': {
                'bar': {
                    'pk': '_id',
                    '_id': {
                        'type': 'INT'
                    },
                    'test': {
                        'dest': 'test',
                        'type': '_ARRAY',
                        'fk': 'id_bar'
                    },
                    'test2': {
                        'dest': 'test_scalar',
                        'fk': 'id_bar',
                        'valueField': 'scalar',
                        'type': '_ARRAY_OF_SCALARS'
                    }
                },
                'test': {
                    'pk': '_id',
                    'test': {
                        'type': 'TEXT'
                    },
                    'id_bar': {
                        'type': 'INT'
                    }
                },
                'test_scalar': {
                    'pk': '_id',
                    'scalar': {
                        'type': 'INT'
                    },
                    'id_bar': {
                        'type': 'INT'
                    }
                }
            }
        }

        doc = {
            '_id': 1,
            'test': [
                {'test': 'test1'}
            ],
            'test2': [1, 2, 3]
        }

        sql.sql_bulk_insert(cursor, mapping, 'foo.bar', [doc])
        print(cursor.execute.mock_calls)


if __name__ == '__main__':
    main()
