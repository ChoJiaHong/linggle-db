import json
import os, sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import redis
import main_config

_client = redis.Redis(
    host=main_config.redisHost,
    port=main_config.redisPort,
    db=main_config.redisDb,
    password=main_config.redisPassword or None,
    decode_responses=True,
)

_TTL_SECONDS = main_config.cacheTtlSeconds


def _term_key(hintWord):
    return f"gec:dict:term:{hintWord}"


def _prefix_key(hintWord):
    return f"gec:dict:prefix:{hintWord}"


def getTerm(hintWord):
    cached = _client.get(_term_key(hintWord))
    return json.loads(cached) if cached is not None else None


def setTerm(hintWord, result):
    _client.set(_term_key(hintWord), json.dumps(result), ex=_TTL_SECONDS)


def getPrefix(hintWord):
    cached = _client.get(_prefix_key(hintWord))
    return json.loads(cached) if cached is not None else None


def setPrefix(hintWord, result):
    _client.set(_prefix_key(hintWord), json.dumps(result), ex=_TTL_SECONDS)
