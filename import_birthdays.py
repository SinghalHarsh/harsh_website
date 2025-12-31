from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

raw_data = """
28	1	1995	Happy Birthday Harsh
9	7	0	Happy Birthday Abhishek Pathak
2	6	0	Birthday Hitesh Bhai
6	6	0	Birthday Simmi
24	7	0	Birthday KK
14	9	0	Birthday Kanha
16	10	0	Birthday Mahika
27	10	0	Birthday Abhishek Sir
9	11	0	Birthday Rahul
27	11	0	Birthday Jayesh
29	11	0	Birthday Sarvagya
18	1	0	Birthday Naval
1	4	0	Birthday Monu
22	3	0	Birthday Chani
21	9	0	Birthday Vignesh
14	10	0	Birthday Megha
21	11	0	Birthday RK
"""

def parse_and_insert():
    lines = raw_data.strip().split('\n')
    new_reminders = []
    
    for line in lines:
        parts = line.split('\t')
        # Handle cases where split might be by space if tabs fail, but user copy-paste usually preserves tabs or spaces
        if len(parts) < 4:
            parts = line.split() # Fallback to whitespace
            # Reconstruct title if it was split
            # Expected: Day Month Year Title...
            day = parts[0]
            month = parts[1]
            year = parts[2]
            title = " ".join(parts[3:])
        else:
            day = parts[0]
            month = parts[1]
            year = parts[2]
            title = parts[3]

        # Normalize Year
        y = int(year)
        if y == 0:
            y = 2000 # Default for year 0
            
        # Format Date
        date_str = f"{y}-{int(month):02d}-{int(day):02d}"
        
        reminder = {
            "title": title.strip(),
            "date": date_str,
            "recurrence": "yearly",
            "created_at": datetime.now()
        }
        new_reminders.append(reminder)
        
    if new_reminders:
        db.reminders.insert_many(new_reminders)
        print(f"Inserted {len(new_reminders)} birthdays.")

if __name__ == "__main__":
    parse_and_insert()
