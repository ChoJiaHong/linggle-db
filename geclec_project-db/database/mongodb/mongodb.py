import re

import initMongodb

collection = initMongodb.collection


def findTerm(term):
    return list(collection.find({"term": term.lower()}, {"_id": 0, "term": 0}))


def findByPrefix(prefix, limit=20):
    pattern = f"^{re.escape(prefix.lower())}"
    return list(collection.find({"term": {"$regex": pattern}}, {"_id": 0}).limit(limit))
