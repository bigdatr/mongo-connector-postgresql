# coding: utf8

from bson.objectid import ObjectId


def extract_creation_date(document, primary_key):
    if primary_key in document:
        objectId = document[primary_key]

        if ObjectId.is_valid(objectId):
            return ObjectId(objectId).generation_time

    return None


def is_collection_mapped(d, keys):
    if "." in keys:
        key, rest = keys.split(".", 1)
        return False if key not in d else is_collection_mapped(d[key], rest)
    else:
        return keys in d


def is_field_mapped(mappings, db, collection, key):
    return is_collection_mapped(mappings, db + "." + collection + "." + key)


def get_array_fields(mappings, db, collection, document):
    return [k for k, v in mappings[db][collection].iteritems() if k in document and v['type'] == '_ARRAY']


def is_array_field(mappings, db, collection, field):
    if not is_field_mapped(mappings, db, collection, field):
        return False

    return mappings[db][collection][field]['type'] == '_ARRAY'


def map_value_to_pgsql(value):
    return value if not isinstance(value, ObjectId) else str(value)


def db_and_collection(namespace):
    return namespace.split('.', 1)


def get_array_field_collection(mappings, db, collection, field):
    return mappings[db][collection][field]['dest']


def get_foreign_key(mappings, db, collection, field):
    return mappings[db][collection][field]['fk']
