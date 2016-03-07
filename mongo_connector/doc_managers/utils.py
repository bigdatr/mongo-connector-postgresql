from bson.objectid import ObjectId


def extractDocumentCreationDate(document):
    if '_id' in document:
        objectId = document['_id']

        if ObjectId.is_valid(objectId):
            return ObjectId(objectId).generation_time

    return None


def isCollectionMapped(d, keys):
    if "." in keys:
        key, rest = keys.split(".", 1)
        return False if key not in d else isCollectionMapped(d[key], rest)
    else:
        return keys in d


def isFieldMapped(mappings, db, collection, key):
    return isCollectionMapped(mappings, db + "." + collection + "." + key)


def keepPrimitiveFields(mappings, db, collection, document, keepArrays):
    return dict(
            (k.replace(".", "_"), objectIdToString(v)) for k, v in document.items()
            if isFieldMapped(mappings, db, collection, k)
            and (keepArrays or not isinstance(v, list))
    )


def getArrayFields(mappings, db, collection, document):
    return dict(
            (k.replace(".", "_"), objectIdToString(v)) for k, v in document.items()
            if isFieldMapped(mappings, db, collection, k)
            and isinstance(v, list)
    )


def objectIdToString(value):
    return value if not isinstance(value, ObjectId) else str(value)

