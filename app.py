from flask import Flask, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

@app.route('/')
def home():
    stats = list(db.dashboard_stats.find())
    return render_template('index.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    posts = list(db.blogs.find())
    return render_template('blog.html', posts=posts)

@app.route('/reminder')
def reminder():
    return render_template('reminder.html')

@app.route('/quotes')
def quotes():
    quote = db.quotes.find_one()
    return render_template('quotes.html', quote=quote)

@app.route('/habits')
def habits():
    habits_list = list(db.habits.find())
    return render_template('habits.html', habits=habits_list)

if __name__ == '__main__':
    app.run(debug=True)
