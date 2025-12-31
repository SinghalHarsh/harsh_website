from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

goal = {
    "title": "Launch Personal Website",
    "status": "In Progress",
    "deadline": "2026-01-31",
    "progress": 40
}

db.goals.insert_one(goal)
print("Sample goal inserted.")
