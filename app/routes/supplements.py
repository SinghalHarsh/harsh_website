from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from bson.objectid import ObjectId

from app.extensions import db
from app.services import supplements as supplement_service

supplements_bp = Blueprint('supplements', __name__)


def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _active_supplements():
    return [s for s in db.supplements.find() if not s.get('deleted')]


def _pick_for_today(active, today_iso, force=False):
    """Today's stored pick, rolling a new one only when missing or forced.

    Storing the roll keeps the recommendation stable across refreshes; the
    date is the document key so each day gets exactly one pick.
    """
    stored = db.supplement_picks.find_one({'date': today_iso})

    if stored and not force:
        chosen = next(
            (s for s in active if str(s['_id']) == stored['supplement_id']), None
        )
        if chosen:
            return chosen
        # The picked supplement was deleted since — fall through and re-roll.

    chosen = supplement_service.weighted_pick(active)
    if not chosen:
        return None

    db.supplement_picks.update_one(
        {'date': today_iso},
        {'$set': {
            'supplement_id': str(chosen['_id']),
            'name': chosen['name'],
            'picked_at': datetime.now(),
        }},
        upsert=True,
    )
    return chosen


@supplements_bp.route('/supplements')
def supplements():
    today = datetime.now()
    today_iso = today.strftime('%Y-%m-%d')

    active = _active_supplements()
    total = supplement_service.total_weight(active)
    for supplement in active:
        supplement_service.annotate(supplement, today, total)

    pick = _pick_for_today(active, today_iso)

    return render_template(
        'pages/supplements.html',
        supplements=sorted(active, key=lambda s: -s.get('weight', 0)),
        pick=pick,
        total_weight=total,
        today_date=today.strftime('%A, %B %d, %Y'),
        today_iso=today_iso,
    )


@supplements_bp.route('/supplements/add', methods=['POST'])
def add_supplement():
    name = request.form.get('name', '').strip()
    if name:
        try:
            weight = max(0, int(request.form.get('weight') or 10))
        except ValueError:
            weight = 10

        db.supplements.insert_one({
            'name': name,
            'weight': weight,
            'note': request.form.get('note', '').strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'history': [],
        })

    if _wants_json():
        return jsonify({'status': 'success', 'name': name})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/weight', methods=['POST'])
def update_weight():
    supplement_id = request.form.get('supplement_id')
    try:
        weight = max(0, int(request.form.get('weight')))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid weight'}), 400

    db.supplements.update_one(
        {'_id': ObjectId(supplement_id)}, {'$set': {'weight': weight}}
    )

    if _wants_json():
        return jsonify({'status': 'success', 'id': supplement_id, 'weight': weight})
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


@supplements_bp.route('/supplements/reroll', methods=['POST'])
def reroll():
    today_iso = datetime.now().strftime('%Y-%m-%d')
    pick = _pick_for_today(_active_supplements(), today_iso, force=True)

    if _wants_json():
        return jsonify({'status': 'success', 'name': pick['name'] if pick else None})
    return redirect(url_for('supplements.supplements'))


@supplements_bp.route('/supplements/log', methods=['POST'])
def log_supplement():
    supplement_id = request.form.get('supplement_id')
    date_str = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')

    supplement = db.supplements.find_one({'_id': ObjectId(supplement_id)})
    if not supplement:
        return jsonify({'error': 'Supplement not found'}), 404

    # Atomic toggle — avoids the lost-update race of rewriting the whole array.
    if date_str in supplement.get('history', []):
        db.supplements.update_one(
            {'_id': supplement['_id']}, {'$pull': {'history': date_str}}
        )
        action = 'removed'
    else:
        db.supplements.update_one(
            {'_id': supplement['_id']}, {'$addToSet': {'history': date_str}}
        )
        action = 'added'

    if _wants_json():
        return jsonify({'status': 'success', 'action': action, 'id': supplement_id})
    return redirect(url_for('supplements.supplements'))
