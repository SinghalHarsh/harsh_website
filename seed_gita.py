import json
import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

def seed_gita_verses():
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("MONGO_URI not found in environment variables")
        return

    client = MongoClient(mongo_uri)
    try:
        db = client.get_database()
    except ConfigurationError:
        db = client.get_database("harsh_website")
    
    collection = db.gita_verses

    # Load JSON data
    try:
        with open('gita_full.json', 'r', encoding='utf-8') as f:
            verses = json.load(f)
    except FileNotFoundError:
        print("gita_full.json not found. Please run fetch_gita.py first.")
        return

    if not verses:
        print("No verses found in JSON file.")
        return

    print(f"Found {len(verses)} verses. Clearing existing collection...")
    collection.delete_many({})
    
    print("Inserting new verses...")
    collection.insert_many(verses)
    
    print(f"Successfully seeded {len(verses)} verses into 'gita_verses' collection.")

if __name__ == "__main__":
    seed_gita_verses()
