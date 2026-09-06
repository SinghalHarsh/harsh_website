from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from bson.objectid import ObjectId

from app.extensions import db
from app.services import supplements as supplement_service
from app.services.calendar_grid import build_year

supplements_bp = Blueprint('supplements', __name__)


def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def active_supplements(annotated=False):
    active = [s for s in db.supplements.find() if not s.get('deleted')]
    if annotated:
        today = datetime.now()
        for supplement in active:
            supplement_service.annotate(supplement, today)
    return active


def enabled_slots():
    """The times of day supplements are marked at, from the settings document."""
    stored = db.supplement_settings.find_one({'_id': 'counts'}) or {}
    return supplement_service.normalise_slots(
        stored.get('slots', supplement_service.DEFAULT_SLOTS)
    )


@supplements_bp.route('/supplements')
def supplements():
    today = datetime.now()
    today_iso = today.strftime('%Y-%m-%d')

    active = active_supplements(annotated=True)
    slots = enabled_slots()

    selected_name = request.args.get('supplement', 'overall')
    selected = next((s for s in active if s['name'] == selected_name), None)
    is_overall = selected is None

    try:
        selected_year = int(request.args.get('year', today.year))
    except ValueError:
        selected_year = today.year

    if is_overall:
        taken_by_day = {}
        for supplement in active:
            for date_str in supplement_service.taken_days(supplement.get('history', [])):
                taken_by_day[date_str] = taken_by_day.get(date_str, 0) + 1
        payload = lambda date_str, _: {'taken_count': taken_by_day.get(date_str, 0)}
        future = {'taken_count': 0}
    else:
        days = supplement_service.taken_days(selected.get('history', []))
        payload = lambda date_str, _: {'taken': date_str in days}
        future = {'taken': False}

    return render_template(
        'pages/supplements.html',
        supplements=sorted(active, key=lambda s: s['name'].lower()),
        slots=slots,
        all_slots=supplement_service.ALL_SLOTS,
        slot_icons=supplement_service.SLOT_ICONS,
        today_date=today.strftime('%A, %B %d, %Y'),
        today_iso=today_iso,
        months_data=build_year(selected_year, today, payload, future),
        selected_year=selected_year,
        selected_supplement=selected,
        is_overall=is_overall,
    )


@supplements_bp.route('/supplements/add', methods=['POST'])
def add_supplement():
    name = request.form.get('name', '').strip()
    if name:
        slot = request.form.get('slot', supplement_service.EITHER)
        if slot not in supplement_service.ALL_SLOTS + (supplement_service.EITHER,):
            slot = supplement_service.EITHER

        db.supplements.insert_one({
            'name': name,
            'slot': slot,
            'note': request.form.get('note', '').strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'history': [],
        })

    if _wants_json():
        return jsonify({'status': 'success', 'name': name})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/delete', methods=['POST'])
def delete_supplement():
    supplement_id = request.form.get('supplement_id')
    if supplement_id:
        db.supplements.update_one(
            {'_id': ObjectId(supplement_id)},
            {'$set': {
                'deleted': True,
                'deleted_at': datetime.now().strftime('%Y-%m-%d'),
            }},
        )

    if _wants_json():
        return jsonify({'status': 'success', 'id': supplement_id})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/slots', methods=['POST'])
def update_slots():
    """Turn the times of day on or off."""
    slots = supplement_service.normalise_slots(request.form.getlist('slots'))
    db.supplement_settings.update_one(
        {'_id': 'counts'}, {'$set': {'slots': list(slots)}}, upsert=True
    )

    if _wants_json():
        return jsonify({'status': 'success', 'slots': list(slots)})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/slot', methods=['POST'])
def update_slot():
    supplement_id = request.form.get('supplement_id')
    slot = request.form.get('slot')
    if slot not in supplement_service.ALL_SLOTS + (supplement_service.EITHER,):
        return jsonify({'error': 'Invalid slot'}), 400

    db.supplements.update_one(
        {'_id': ObjectId(supplement_id)}, {'$set': {'slot': slot}}
    )

    if _wants_json():
        return jsonify({'status': 'success', 'id': supplement_id, 'slot': slot})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/log', methods=['POST'])
def log_supplement():
    supplement_id = request.form.get('supplement_id')
    date_str = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')

    # Any known slot logs, not just the enabled ones — a dose recorded before a
    # slot was switched off must still be reversible.
    slot = request.form.get('slot')
    if slot not in supplement_service.ALL_SLOTS:
        return jsonify({'error': 'Invalid slot'}), 400

    supplement = db.supplements.find_one({'_id': ObjectId(supplement_id)})
    if not supplement:
        return jsonify({'error': 'Supplement not found'}), 404

    key = supplement_service.entry(date_str, slot)
    history = supplement.get('history', [])

    # Atomic toggle — avoids the lost-update race of rewriting the whole array.
    if key in history:
        db.supplements.update_one(
            {'_id': supplement['_id']}, {'$pull': {'history': key}}
        )
        action = 'removed'
    else:
        db.supplements.update_one(
            {'_id': supplement['_id']}, {'$addToSet': {'history': key}},
        )
        # Clear any pre-slot entry for the same day so it isn't counted twice.
        db.supplements.update_one(
            {'_id': supplement['_id']}, {'$pull': {'history': date_str}}
        )
        action = 'added'

    fresh = db.supplements.find_one({'_id': supplement['_id']})
    if _wants_json():
        return jsonify({
            'status': 'success',
            'action': action,
            'id': supplement_id,
            'slot': slot,
            'streak': supplement_service.streak(fresh.get('history', []), datetime.now()),
            'times_taken': len(fresh.get('history', [])),
        })
    return redirect(url_for('supplements.supplements'))
