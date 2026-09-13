from flask import (
    Blueprint, render_template, request, redirect, url_for, jsonify,
    current_app,
)
from datetime import datetime
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.extensions import db
from app.services import habits as habit_service
from app.services.calendar_grid import build_year

habits_bp = Blueprint('habits', __name__)


def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _object_id(value):
    """Parse a habit id, or None when it is missing or malformed.

    ObjectId(None) mints a brand new id rather than failing, which would send
    an update off to a document that does not exist, so empty input is
    rejected before it gets there.
    """
    if not value:
        return None
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _int_field(value, default, low, high):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _board(today):
    """Today's active board, annotated — the same set both pages render."""
    habits = [h for h in db.habits.find({'active': True, 'deleted': {'$ne': True}})]
    for habit in habits:
        habit_service.annotate(habit, today)
    return [h for h in habits if not h.get('should_retire')]


def _card_response(habit_id, action, today):
    """One habit's fresh cards, plus the totals a logging action moves.

    The cards come back as rendered HTML from the same macro the pages use, so
    patching one in place cannot drift from the server's own markup. Scoring is
    a full replay, so a single toggle changes points, tier, credits and the
    day's totals together — they all travel in one response.

    Both days are rendered because a habit can appear twice at once: once on
    today's board and once on yesterday's while that day is still open. Ticking
    either changes the score both of them display.
    """
    board = _board(today)
    habit = next((h for h in board if h['_id'] == habit_id), None)
    metrics = habit_service.metrics(board, today)

    macros = current_app.jinja_env.get_template('components/_macros.html')
    # A habit that just retired itself off the board has no card to show.
    today_card = macros.module.habit_card(habit, 'today') if habit else None
    # Yesterday's card only stands while that day is unresolved.
    late_card = (
        macros.module.habit_card(habit, 'yesterday')
        if habit and habit.get('yesterday_open') else None
    )

    return jsonify({
        'status': 'success',
        'action': action,
        'id': str(habit_id),
        'card': today_card,
        'late_card': late_card,
        'score': habit_service.daily_score(board, today),
        # The dashboard's running total and weekly delta, which a tick moves.
        'points': metrics['points'],
        'points_delta': metrics['points_delta'],
    })


@habits_bp.route('/habits')
def habits():
    today = datetime.now()

    all_raw = list(db.habits.find())
    visible = [h for h in all_raw if not h.get('deleted')]
    for habit in visible:
        habit_service.annotate(habit, today)

    active = [h for h in visible if h.get('active', True)]

    # A habit left dead long enough drops off the board and reads as an idea
    # again. This is presentation only: nothing is written, so reactivating one
    # sticks and a stray GET cannot quietly retire it.
    for habit in visible:
        if habit.get('should_retire'):
            habit['active'] = False
    active = [h for h in active if not h.get('should_retire')]

    selected_name = request.args.get('habit')
    is_overall = not selected_name or selected_name == 'overall'
    selected = None
    if not is_overall:
        selected = next((h for h in active if h['name'] == selected_name), None)
        is_overall = selected is None

    selected_year = _int_field(request.args.get('year'), today.year, 1970, 2999)

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
        # Charts read every tracked habit, so retiring one does not erase
        # the history it contributed.
        score=habit_service.metrics(visible, today, active=active),
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
            'credit_every': _int_field(request.form.get('credit_every'), 5, 0, 30),
            'credit_amount': _int_field(request.form.get('credit_amount'), 1, 0, 7),
            'rest_days': [],
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'history': [],
        })

    if _wants_json():
        return jsonify({'status': 'success', 'name': name})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/toggle', methods=['POST'])
def toggle_habit():
    habit_id = _object_id(request.form.get('habit_id'))
    if not habit_id:
        return jsonify({'error': 'Invalid habit'}), 400
    is_active = request.form.get('active') == 'on'

    db.habits.update_one({'_id': habit_id}, {'$set': {'active': is_active}})

    if _wants_json():
        return jsonify({'status': 'success', 'id': str(habit_id), 'active': is_active})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/delete', methods=['POST'])
def delete_habit():
    habit_id = _object_id(request.form.get('habit_id'))
    if not habit_id:
        return jsonify({'error': 'Invalid habit'}), 400

    db.habits.update_one(
        {'_id': habit_id},
        {'$set': {
            'deleted': True,
            'deleted_at': datetime.now().strftime('%Y-%m-%d'),
            'active': False,
        }},
    )

    if _wants_json():
        return jsonify({'status': 'success', 'id': str(habit_id)})
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/log', methods=['POST'])
def log_habit():
    habit_id = _object_id(request.form.get('habit_id'))
    if not habit_id:
        return jsonify({'error': 'Invalid habit'}), 400
    today = datetime.now()
    date_str = request.form.get('date') or today.strftime('%Y-%m-%d')

    habit = db.habits.find_one({'_id': habit_id})
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
        return _card_response(habit_id, action, today)
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/rest', methods=['POST'])
def rest_day():
    """Spend a credit to claim a day off without breaking the streak."""
    habit_id = _object_id(request.form.get('habit_id'))
    if not habit_id:
        return jsonify({'error': 'Invalid habit'}), 400
    today = datetime.now()
    date_str = request.form.get('date') or today.strftime('%Y-%m-%d')

    habit = db.habits.find_one({'_id': habit_id})
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404

    if date_str in habit.get('rest_days', []):
        db.habits.update_one({'_id': habit['_id']}, {'$pull': {'rest_days': date_str}})
        action = 'removed'
    else:
        if not habit_service.habit_state(habit, today).credits:
            return jsonify({'error': 'No credits available'}), 400
        db.habits.update_one({'_id': habit['_id']}, {'$addToSet': {'rest_days': date_str}})
        action = 'added'

    if _wants_json():
        return _card_response(habit_id, action, today)
    return redirect(url_for('habits.habits'))


@habits_bp.route('/habits/credit-rate', methods=['POST'])
def set_credit_rate():
    habit_id = _object_id(request.form.get('habit_id'))
    if not habit_id:
        return jsonify({'error': 'Invalid habit'}), 400
    every = _int_field(request.form.get('credit_every'), 5, 0, 30)
    amount = _int_field(request.form.get('credit_amount'), 1, 0, 7)

    db.habits.update_one(
        {'_id': habit_id},
        {'$set': {'credit_every': every, 'credit_amount': amount}},
    )

    if _wants_json():
        return jsonify({'status': 'success', 'id': str(habit_id),
                        'credit_every': every, 'credit_amount': amount})
    return redirect(url_for('habits.habits'))
