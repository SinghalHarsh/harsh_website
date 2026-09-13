from flask import Blueprint, render_template, current_app, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import random
from datetime import datetime

from app.extensions import db
from app.services import habits as habit_service
from app.services import reminders as reminder_service
from app.services import supplements as supplement_service
from app.routes.supplements import active_supplements, enabled_slots

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

    # Only the fields scoring and the cards actually read: the dashboard does
    # not need every habit's whole document.
    active_habits = list(db.habits.find(
        {"active": True, "deleted": {"$ne": True}},
        {"name": 1, "color": 1, "history": 1, "rest_days": 1,
         "created_at": 1, "credit_every": 1, "credit_amount": 1},
    ))
    for habit in active_habits:
        habit_service.annotate(habit, today)

    # Long-dead habits read as ideas on the habits page — keep the board the same here.
    active_habits = [h for h in active_habits if not h.get('should_retire')]

    pending_habits = [h for h in active_habits if not h['completed_today']]
    score = habit_service.daily_score(active_habits, today)
    # The same running total and weekly delta the habits chart shows, so the
    # two pages never disagree.
    habit_metrics = habit_service.metrics(active_habits, today)
    habit_points = habit_metrics['points']
    habit_points_delta = habit_metrics['points_delta']

    todays_reminders = reminder_service.active_on(list(db.reminders.find()), today_str)

    supplement_slots = enabled_slots()
    supplements = sorted(
        active_supplements(annotated=True), key=lambda s: s['name'].lower()
    )

    return render_template(
        'pages/index.html',
        supplements=supplements,
        supplement_slots=supplement_slots,
        slots_for=supplement_service.slots_for,
        slot_icons=supplement_service.SLOT_ICONS,
        habits_completed=score['completed'],
        habits_total=score['total'],
        habit_score=score,
        habit_points=habit_points,
        habit_points_delta=habit_points_delta,
        habits=active_habits,
        pending_habits=pending_habits,
        reminders_today_count=len(todays_reminders),
        todays_reminders=todays_reminders,
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
