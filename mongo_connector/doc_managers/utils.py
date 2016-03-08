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
    return dict(
            (k.replace(".", "_"), map_value_to_pgsql(v)) for k, v in document.items()
            if is_field_mapped(mappings, db, collection, k)
            and isinstance(v, list)
    )


def map_value_to_pgsql(value):
    return value if not isinstance(value, ObjectId) else str(value)

