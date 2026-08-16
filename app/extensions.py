from pymongo import MongoClient
from pymongo.errors import ConfigurationError

from app.config import Config

_client = MongoClient(Config.MONGO_URI) if Config.MONGO_URI else None

try:
    db = _client.get_database() if _client else None
except ConfigurationError:
    # URI has no default database component
    db = _client.get_database(Config.MONGO_DB_NAME)
