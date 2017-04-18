# -*- coding: utf-8 -*-

from mongo_connector.doc_managers import utils

from bson.objectid import ObjectId
from bson.tz_util import utc

from datetime import datetime
from calendar import timegm

from unittest import TestCase, main


class TestPostgreSQLUtils(TestCase):
    def test_extract_creation_date(self):
        now = datetime.now()

        doc = {
            '_id': ObjectId.from_datetime(now)
        }

        got = utils.extract_creation_date(doc, '_id')
        expected = now

        if expected.utcoffset() is not None:
            expected -= expected.utcoffset()

        expected = timegm(expected.timetuple())
        expected = datetime.fromtimestamp(expected, utc)

        self.assertEqual(expected, got)

        got = utils.extract_creation_date({}, '_id')
        self.assertIsNone(got)

    def test_is_collection_mapped(self):
        doc = {
            'foo': {
                'bar': {
                    'baz': 'biz'
                }
            }
        }

        got = utils.is_collection_mapped(doc, 'foo.bar.baz')
        self.assertTrue(got)

        doc = {
            'foo': {
                'bar': {}
            }
        }

        got = utils.is_collection_mapped(doc, 'foo.bar.baz')
        self.assertFalse(got)

    def test_is_field_mapped(self):
        mapping = {
            'foo': {
                'bar': {
                    'baz': 'biz'
                }
            }
        }

        got = utils.is_field_mapped(mapping, 'foo', 'bar', 'baz')
        self.assertTrue(got)

        mapping = {
            'foo': {
                'bar': {}
            }
        }

        got = utils.is_field_mapped(mapping, 'foo', 'bar', 'baz')
        self.assertFalse(got)

    def test_get_nested_field_from_document(self):
        got = utils.get_nested_field_from_document(None, None)
        self.assertIsNone(got)

        doc = {}
        got = utils.get_nested_field_from_document(doc, 'foo')
        self.assertIsNone(got)

        doc = {'foo': 'bar'}
        got = utils.get_nested_field_from_document(doc, 'foo')
        self.assertEqual(got, 'bar')

        doc = {
            'foo': {}
        }
        got = utils.get_nested_field_from_document(doc, 'foo.bar.baz')
        self.assertIsNone(got)

        doc = {
            'foo': {
                'bar': 'baz'
            }
        }
        got = utils.get_nested_field_from_document(doc, 'foo.bar')
        self.assertEqual(got, 'baz')

    def test_get_fields_of_type(self):
        mapping = {}
        got = utils.get_fields_of_type(mapping, 'foo', 'bar', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {'foo': {}}
        got = utils.get_fields_of_type(mapping, 'foo', 'bar', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {
            'foo': {
                'bar': {}
            }
        }
        got = utils.get_fields_of_type(mapping, 'foo', 'bar', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {
            'foo': {
                'bar': {
                    'test': {'test2': {}},
                    'test.test2': {'type': 'TEXT'}
                }
            }
        }
        got = utils.get_fields_of_type(mapping, 'foo', 'bar', {}, 'TEXT')
        self.assertEqual(got, [])

        doc = {'test': {'test2': 'test3'}}
        got = utils.get_fields_of_type(mapping, 'foo', 'bar', doc, 'TEXT')
        self.assertEqual(got, ['test.test2'])

    def test_get_array_fields(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {'type': '_ARRAY'}
                }
            }
        }
        got = utils.get_array_fields(mapping, 'foo', 'bar', {})
        self.assertEqual(got, [])

        doc = {'test': [{}]}
        got = utils.get_array_fields(mapping, 'foo', 'bar', doc)
        self.assertEqual(got, ['test'])

    def test_get_array_of_scalar_fields(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {'type': '_ARRAY_OF_SCALARS'}
                }
            }
        }
        got = utils.get_array_of_scalar_fields(mapping, 'foo', 'bar', {})
        self.assertEqual(got, [])

        doc = {'test': [1, 2, 3]}
        got = utils.get_array_of_scalar_fields(mapping, 'foo', 'bar', doc)
        self.assertEqual(got, ['test'])

    def test_get_any_array_fields(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {'type': '_ARRAY'},
                    'test2': {'type': '_ARRAY_OF_SCALARS'}
                }
            }
        }
        got = utils.get_any_array_fields(mapping, 'foo', 'bar', {})
        self.assertEqual(got, [])

        doc = {'test': [{}]}
        got = utils.get_any_array_fields(mapping, 'foo', 'bar', doc)
        self.assertEqual(got, ['test'])

        doc = {'test2': [1, 2, 3]}
        got = utils.get_any_array_fields(mapping, 'foo', 'bar', doc)
        self.assertEqual(got, ['test2'])

        doc = {
            'test': [{}],
            'test2': [1, 2, 3]
        }
        got = utils.get_any_array_fields(mapping, 'foo', 'bar', doc)
        self.assertIn('test', got)
        self.assertIn('test2', got)

    def test_is_array_field(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {
                        'test2': {},
                        'test3': {}
                    },
                    'test.test2': {'type': '_ARRAY'},
                    'test.test3': {'type': 'TEXT'}
                }
            }
        }

        got = utils.is_array_field(mapping, 'foo', 'bar', 'test.test2')
        self.assertTrue(got)

        got = utils.is_array_field(mapping, 'foo', 'bar', 'test.test3')
        self.assertFalse(got)

        got = utils.is_array_field(mapping, 'foo', 'bar', 'test.test4')
        self.assertFalse(got)

    def test_map_value_to_pgsql(self):
        _id = ObjectId('0123456789AB')
        got = utils.map_value_to_pgsql(_id)
        self.assertTrue(isinstance(got, str))

        _id = '0123456789AB'
        got = utils.map_value_to_pgsql(_id)
        self.assertTrue(isinstance(got, str))

    def test_db_and_collection(self):
        ns = 'foo.bar'
        got = utils.db_and_collection(ns)

        self.assertEqual(len(got), 2)
        self.assertEqual(got, ['foo', 'bar'])

    def test_get_array_field_collection(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {
                        'dest': 'test2'
                    }
                }
            }
        }
        got = utils.get_array_field_collection(mapping, 'foo', 'bar', 'test')
        self.assertEqual(got, 'test2')

    def test_get_foreign_key(self):
        mapping = {
            'foo': {
                'bar': {
                    'test': {
                        'fk': 'test2'
                    }
                }
            }
        }
        got = utils.get_foreign_key(mapping, 'foo', 'bar', 'test')
        self.assertEqual(got, 'test2')


if __name__ == '__main__':
    main()
