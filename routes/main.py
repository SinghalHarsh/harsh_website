from flask import Blueprint, render_template, current_app, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import random
from datetime import datetime
from database import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Habits Stats
    today_str = datetime.now().strftime('%Y-%m-%d')
    all_habits = list(db.habits.find({"active": True}))
    habits_completed = 0
    pending_habits = []
    
    for h in all_habits:
        if today_str in h.get('history', []):
            habits_completed += 1
        else:
            pending_habits.append(h)
            
    habits_total = len(all_habits)
    
    # Goals Stats
    active_goals_cursor = db.goals.find({"completed": {"$ne": True}})
    active_goals = list(active_goals_cursor)
    active_goals_count = len(active_goals)
    
    # Reminders Today
    reminders = list(db.reminders.find())
    todays_reminders = []
    
    def is_skipped(reminder, target_date_str):
        skipped = reminder.get('skipped_dates', [])
        return target_date_str in skipped

    for r in reminders:
        if r.get('date') == today_str:
             if not is_skipped(r, today_str):
                 todays_reminders.append(r)
        elif r.get('recurrence') == 'yearly' and r.get('date')[5:] == today_str[5:]:
             if not is_skipped(r, today_str):
                 todays_reminders.append(r)

    reminders_today_count = len(todays_reminders)

    # Quotes Logic (Random Quote)
    text_quotes = list(db.quotes.find())
    images_dir = os.path.join(current_app.static_folder, 'images', 'quotes')
    image_quotes = []
    if os.path.exists(images_dir):
        image_quotes = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    all_content = []
    for q in text_quotes:
        all_content.append({'type': 'text', 'data': q})
    for img in image_quotes:
        all_content.append({'type': 'image', 'filename': img})
    
    selected_quote = random.choice(all_content) if all_content else None

    return render_template('index.html', 
                           habits_completed=habits_completed, 
                           habits_total=habits_total,
                           pending_habits=pending_habits,
                           active_goals_count=active_goals_count,
                           active_goals=active_goals,
                           reminders_today_count=reminders_today_count,
                           todays_reminders=todays_reminders,
                           selected_quote=selected_quote)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/blog')
def blog():
    posts = list(db.blogs.find())
    return render_template('blog.html', posts=posts)

@main_bp.route('/quotes')
def quotes():
    # 1. Get text quotes from DB
    text_quotes = list(db.quotes.find())
    
    # 2. Get image quotes from static folder
    images_dir = os.path.join(current_app.static_folder, 'images', 'quotes')
    image_quotes = []
    if os.path.exists(images_dir):
        image_quotes = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    all_content = []
    for q in text_quotes:
        all_content.append({'type': 'text', 'data': q})
        
    for img in image_quotes:
        all_content.append({'type': 'image', 'filename': img})
    
    # 4. Pick one random item
    selected_content = random.choice(all_content) if all_content else None
    
    return render_template('quotes.html', content=selected_content, total_quotes=len(all_content))

@main_bp.route('/quotes/upload', methods=['POST'])
def upload_quote():
    if 'file' not in request.files:
        return redirect(url_for('main.quotes'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('main.quotes'))
    if file:
        filename = secure_filename(file.filename)
        images_dir = os.path.join(current_app.static_folder, 'images', 'quotes')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        file.save(os.path.join(images_dir, filename))
    return redirect(url_for('main.quotes'))
