from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from bson.objectid import ObjectId

from app.extensions import db
from app.services import habits as habit_service
from app.services.calendar_grid import build_year

habits_bp = Blueprint('habits', __name__)


def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@habits_bp.route('/habits')
def habits():
    today = datetime.now()

    all_raw = list(db.habits.find())
    visible = [h for h in all_raw if not h.get('deleted')]
    for habit in visible:
        habit_service.annotate(habit, today)

    active = [h for h in visible if h.get('active', True)]

    selected_name = request.args.get('habit')
    is_overall = not selected_name or selected_name == 'overall'
    selected = None
    if not is_overall:
        selected = next((h for h in active if h['name'] == selected_name), None)
        is_overall = selected is None

    selected_year = int(request.args.get('year', today.year))

    if is_overall:
        def payload(date_str, _):
            return {'completed_count': sum(
                1 for h in all_raw if date_str in h.get('history', [])
            )}
    else:
        history = set(selected.get('history', []))

        def payload(date_str, _):
            return {'completed': date_str in history}

    return render_template(
        'pages/habits.html',
        habits=active,
        all_habits=visible,
        selected_habit=selected,
        is_overall=is_overall,
        months_data=build_year(
            selected_year, today, payload,
            future_payload={'completed_count': 0} if is_overall else {'completed': False},
        ),
        selected_year=selected_year,
        score=habit_service.daily_score(active, today),
        today_date=today.strftime('%A, %B %d, %Y'),
        today_iso=today.strftime('%Y-%m-%d'),
    )


@habits_bp.route('/habits/add', methods=['POST'])
def add_habit():
    name = request.form.get('name', '').strip()
    if name:
        db.habits.insert_one({
            'name': name,
            'color': request.form.get('color') or 'text-blue',
            'active': request.form.get('active') == 'true',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'history': [],
        })

    if _wants_json():
        return jsonify({'status': 'success', 'name': name})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/toggle', methods=['POST'])
def toggle_habit():
    habit_id = request.form.get('habit_id')
    is_active = request.form.get('active') == 'on'

    db.habits.update_one({'_id': ObjectId(habit_id)}, {'$set': {'active': is_active}})

    if _wants_json():
        return jsonify({'status': 'success', 'id': habit_id, 'active': is_active})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/delete', methods=['POST'])
def delete_habit():
    habit_id = request.form.get('habit_id')
    if habit_id:
        db.habits.update_one(
            {'_id': ObjectId(habit_id)},
            {'$set': {
                'deleted': True,
                'deleted_at': datetime.now().strftime('%Y-%m-%d'),
                'active': False,
            }},
        )

    if _wants_json():
        return jsonify({'status': 'success', 'id': habit_id})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/log', methods=['POST'])
def log_habit():
    habit_id = request.form.get('habit_id')
    date_str = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')

    habit = db.habits.find_one({'_id': ObjectId(habit_id)})
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404

    # Atomic toggle — avoids the lost-update race of rewriting the whole array.
    if date_str in habit.get('history', []):
        db.habits.update_one({'_id': habit['_id']}, {'$pull': {'history': date_str}})
        action = 'removed'
    else:
        db.habits.update_one({'_id': habit['_id']}, {'$addToSet': {'history': date_str}})
        action = 'added'

    if _wants_json():
        return jsonify({'status': 'success', 'action': action, 'id': habit_id})
    return redirect(url_for('habits.habits'))
