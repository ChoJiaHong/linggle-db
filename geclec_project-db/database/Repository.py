import os, sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mongodb import mongodb
from cache import redis_cache


def getWithTerm(hintWord):
    cached = redis_cache.getTerm(hintWord)
    if cached is not None:
        return cached
    result = mongodb.findTerm(hintWord)
    redis_cache.setTerm(hintWord, result)
    return result


def getWithPrefix(hintWord):
    cached = redis_cache.getPrefix(hintWord)
    if cached is not None:
        return cached
    result = mongodb.findByPrefix(hintWord)
    redis_cache.setPrefix(hintWord, result)
    return result
