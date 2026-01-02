from pymongo import MongoClient
from pymongo.errors import ConfigurationError
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
try:
    db = client.get_database()
except ConfigurationError:
    db = client.get_database("harsh_website")
