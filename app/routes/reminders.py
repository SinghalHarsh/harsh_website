from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from bson.objectid import ObjectId

from app.extensions import db
from app.services import reminders as service
from app.services.calendar_grid import build_year

reminders_bp = Blueprint('reminders', __name__)


def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@reminders_bp.route('/reminder')
def reminder():
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    all_reminders = list(db.reminders.find().sort('date', 1))

    def payload(date_str, _):
        occurring = service.active_on(all_reminders, date_str)
        return {'count': len(occurring), 'reminders': occurring}

    selected_year = int(request.args.get('year', today.year))

    return render_template(
        'pages/reminder.html',
        todays_reminders=service.active_on(all_reminders, today_str),
        missed_reminders=service.missed(all_reminders, today),
        months_data=build_year(selected_year, today, payload,
                               future_payload={'count': 0, 'reminders': []}),
        selected_year=selected_year,
        today_date=today.strftime('%A, %B %d, %Y'),
        today_iso=today_str,
    )


@reminders_bp.route('/reminder/add', methods=['POST'])
def add_reminder():
    title = request.form.get('title', '').strip()
    date = request.form.get('date')

    if not (title and date):
        return redirect(url_for('reminders.reminder'))

    data = {
        'title': title,
        'date': date,
        'recurrence': request.form.get('recurrence') or None,
        'category': request.form.get('category'),
        'created_at': datetime.now(),
    }
    remind_days = request.form.get('remind_days')
    if remind_days:
        data['remind_days_before'] = int(remind_days)

    result = db.reminders.insert_one(data)

    if _wants_json():
        return jsonify({'status': 'success', 'id': str(result.inserted_id), **{
            k: v for k, v in data.items() if k != 'created_at'
        }})
    return redirect(url_for('reminders.reminder'))


@reminders_bp.route('/reminder/complete', methods=['POST'])
def complete_reminder():
    reminder_id = request.form.get('id')
    date_completed = request.form.get('date')

    if reminder_id and date_completed:
        db.reminders.update_one(
            {'_id': ObjectId(reminder_id)},
            {'$addToSet': {'completed_dates': date_completed}},
        )
        if _wants_json():
            return jsonify({'status': 'success', 'id': reminder_id, 'date': date_completed})

    return redirect(url_for('reminders.reminder'))


@reminders_bp.route('/reminder/delete', methods=['POST'])
def delete_reminder():
    reminder_id = request.form.get('id')
    mode = request.form.get('mode')  # 'instance' skips one date, else delete series
    date_to_skip = request.form.get('date')

    if reminder_id:
        if mode == 'instance' and date_to_skip:
            db.reminders.update_one(
                {'_id': ObjectId(reminder_id)},
                {'$addToSet': {'skipped_dates': date_to_skip}},
            )
        else:
            db.reminders.delete_one({'_id': ObjectId(reminder_id)})

    if _wants_json():
        return jsonify({'status': 'success', 'id': reminder_id})
    return redirect(url_for('reminders.reminder'))
