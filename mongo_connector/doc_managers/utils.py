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