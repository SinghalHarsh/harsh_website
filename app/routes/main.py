from flask import Blueprint, render_template, current_app, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import random
from datetime import datetime

from app.extensions import db
from app.services import habits as habit_service
from app.services import reminders as reminder_service

main_bp = Blueprint('main', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


def _quotes_dir():
    return os.path.join(current_app.static_folder, 'images', 'quotes')


def _all_quote_content():
    """Text quotes from Mongo plus image quotes from static/."""
    content = [{'type': 'text', 'data': q} for q in db.quotes.find()]

    images_dir = _quotes_dir()
    if os.path.isdir(images_dir):
        content += [
            {'type': 'image', 'filename': f}
            for f in os.listdir(images_dir)
            if os.path.splitext(f)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
        ]
    return content


@main_bp.route('/')
def home():
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')

    active_habits = list(db.habits.find({"active": True, "deleted": {"$ne": True}}))
    for habit in active_habits:
        habit_service.annotate(habit, today)

    pending_habits = [h for h in active_habits if not h['completed_today']]
    score = habit_service.daily_score(active_habits, today)

    active_goals = list(db.goals.find({"completed": {"$ne": True}}))
    todays_reminders = reminder_service.active_on(list(db.reminders.find()), today_str)

    all_content = _all_quote_content()

    return render_template(
        'pages/index.html',
        habits_completed=score['completed'],
        habits_total=score['total'],
        habit_score=score,
        pending_habits=pending_habits,
        active_goals_count=len(active_goals),
        active_goals=active_goals,
        reminders_today_count=len(todays_reminders),
        todays_reminders=todays_reminders,
        selected_quote=random.choice(all_content) if all_content else None,
        today_iso=today_str,
    )


@main_bp.route('/quotes')
def quotes():
    all_content = _all_quote_content()
    return render_template(
        'pages/quotes.html',
        content=random.choice(all_content) if all_content else None,
        total_quotes=len(all_content),
    )


@main_bp.route('/quotes/upload', methods=['POST'])
def upload_quote():
    file = request.files.get('file')
    if not file or not file.filename:
        return redirect(url_for('main.quotes'))

    if os.path.splitext(file.filename)[1].lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return redirect(url_for('main.quotes'))

    images_dir = _quotes_dir()
    os.makedirs(images_dir, exist_ok=True)
    file.save(os.path.join(images_dir, secure_filename(file.filename)))
    return redirect(url_for('main.quotes'))
