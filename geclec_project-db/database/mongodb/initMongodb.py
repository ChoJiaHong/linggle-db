from pymongo import MongoClient
import os, sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import main_config

_mongodbIp = main_config.mongodbIp
_mongodbPort = main_config.mongodbPort

if main_config.mongodbUsername:
    client = MongoClient(
        host=_mongodbIp,
        port=_mongodbPort,
        username=main_config.mongodbUsername,
        password=main_config.mongodbPassword,
    )
else:
    client = MongoClient(_mongodbIp, _mongodbPort)

db = client[main_config.mongodbDb]
collection = db[main_config.mongodbCollection]
