from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

# Data to seed
blogs = [
    {
        "title": "WhatsApp Chat 📱 — Analyze 🔍, Visualize 📊",
        "date": "2020-08-09",
        "categories": "EDA, Data Analysis",
        "link": "https://medium.com/analytics-vidhya/whatsapp-chat-analyze-visualize-68e4d30be729",
        "image": "WhatsApp Chat   Analyze  Visualize.jpg"
    },
    {
        "title": "Historical Returns of NIFTY50, NIFTY Midcap50, NIFTY Smallcap50 Companies",
        "date": "2020-09-13",
        "categories": "Stock Market, Data Analysis",
        "link": "https://medium.com/@harshsinghal726/nifty50-stocks-performance-in-the-last-decade-2010-2019-e25097245c36",
        "image": "Historical Returns of NIFTY50 NIFTY Midcap50 NIFTY Smallcap50 Companies.jpg"
    },
    {
        "title": "NIFTY in the last decade (2010–2019) — Historical Analysis",
        "date": "2020-09-04",
        "categories": "EDA, Data Analysis, Stock Market",
        "link": "https://medium.com/analytics-vidhya/nifty-in-the-last-decade-2010-2019-historical-analysis-9d681e6e0b21",
        "image": "NIFTY in the last decade 20102019  Historical Analysis.jpg"
    },
    {
        "title": "Statistics — Moments of a distribution",
        "date": "2020-06-07",
        "categories": "Statistics",
        "link": "https://medium.com/analytics-vidhya/statistics-moments-of-a-distribution-1bcfc4cbbd48",
        "image": "Statistics  Moments of a distribution.jpg"
    },
    {
        "title": "Git — Most frequently used commands",
        "date": "2020-03-25",
        "categories": "Git",
        "link": "https://medium.com/analytics-vidhya/whatsapp-chat-analyze-visualize-68e4d30be729",
        "image": "Git  Most frequently used commands.jpg"
    },
    {
        "title": "FIRST WORLD TEST CHAMPIONSHIP [2019–2021]",
        "date": "2019-11-23",
        "categories": "Cricket",
        "link": "https://medium.com/@harshsinghal726/first-world-test-championship-2019-2021-d852a0bd75ae",
        "image": "FIRST WORLD TEST CHAMPIONSHIP 20192021.jpg"
    },
    {
        "title": "Convolutional Neural Network with TensorFlow implementation",
        "date": "2017-06-17",
        "categories": "Deep Learning, CNN",
        "link": "https://medium.com/data-science-group-iitr/building-a-convolutional-neural-network-in-python-with-tensorflow-d251c3ca8117",
        "image": "Convolutional Neural Network with TensorFlow implementation.jpg"
    }
]

quotes = [
    {
        "text": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs"
    }
]

habits = [
    {
        "name": "Reading",
        "streak": "5 Days",
        "status": "Streak",
        "color": "text-green",
        "active": True,
        "history": [
            "2025-01-01", "2025-01-02", "2025-01-05", "2025-01-06", "2025-01-07",
            "2025-02-10", "2025-02-11", "2025-02-12", "2025-03-01", "2025-03-05",
            "2025-12-25", "2025-12-26", "2025-12-27", "2025-12-28", "2025-12-29"
        ]
    },
    {
        "name": "Coding",
        "streak": "12 Days",
        "status": "Streak",
        "color": "text-blue",
        "active": True,
        "history": [
            "2025-01-10", "2025-01-11", "2025-01-12", "2025-01-13", "2025-01-14",
            "2025-04-01", "2025-04-02", "2025-04-03", "2025-05-20", "2025-05-21"
        ]
    },
    {
        "name": "Exercise",
        "streak": "0 Days",
        "status": "Missed today",
        "color": "text-red",
        "active": True,
        "history": [
            "2025-01-01", "2025-01-03", "2025-01-05", "2025-01-07", "2025-01-09"
        ]
    },
    {
        "name": "Meditation",
        "streak": "0 Days",
        "status": "Inactive",
        "color": "text-gray",
        "active": False,
        "history": []
    }
]

dashboard_stats = [
    {
        "title": "Total Projects",
        "value": "12",
        "sub_text": "3 Active currently",
        "color": "text-blue"
    },
    {
        "title": "GitHub Commits",
        "value": "1,240",
        "sub_text": "In the last year",
        "color": "text-green"
    },
    {
        "title": "Pending Tasks",
        "value": "5",
        "sub_text": "High priority items",
        "color": "text-red"
    },
    {
        "title": "Articles Read",
        "value": "45",
        "sub_text": "This month",
        "color": "text-blue"
    }
]

reminders = [
    {
        "title": "Project Deadline",
        "date": "2025-12-30",
        "type": "Work"
    },
    {
        "title": "Mom's Birthday",
        "date": "2026-01-15",
        "type": "Personal"
    },
    {
        "title": "Doctor Appointment",
        "date": "2026-02-01",
        "type": "Health"
    }
]

goals = [
    {
        "title": "Learn Rust",
        "status": "In Progress",
        "deadline": "2026-06-01",
        "progress": 30
    },
    {
        "title": "Run a Marathon",
        "status": "Not Started",
        "deadline": "2026-12-01",
        "progress": 0
    },
    {
        "title": "Read 24 Books",
        "status": "In Progress",
        "deadline": "2026-12-31",
        "progress": 15
    }
]

# Clear existing collections
db.blogs.drop()
db.quotes.drop()
db.habits.drop()
db.dashboard_stats.drop()
db.reminders.drop()
db.goals.drop()

# Insert new data
db.blogs.insert_many(blogs)
db.quotes.insert_many(quotes)
db.habits.insert_many(habits)
db.dashboard_stats.insert_many(dashboard_stats)
db.reminders.insert_many(reminders)
db.goals.insert_many(goals)

print("Database seeded successfully!")
