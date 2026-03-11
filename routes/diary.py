from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from database import db
from bson.objectid import ObjectId

diary_bp = Blueprint('diary', __name__)

@diary_bp.route('/diary')
def diary():
    entries = list(db.diary.find().sort('created_at', -1))
    return render_template('diary.html', entries=entries)

@diary_bp.route('/diary/save', methods=['POST'])
def save_entry():
    data = request.get_json()
    month = data.get('month', '')
    week = data.get('week', '')
    answers = data.get('answers', {})

    if not month or not week:
        return jsonify({'error': 'Month and week are required'}), 400

    existing = db.diary.find_one({'month': month, 'week': week})
    if existing:
        db.diary.update_one(
            {'_id': existing['_id']},
            {'$set': {'answers': answers, 'updated_at': datetime.now()}}
        )
    else:
        db.diary.insert_one({
            'month': month,
            'week': week,
            'answers': answers,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })

    return jsonify({'success': True})

@diary_bp.route('/diary/load')
def load_entry():
    month = request.args.get('month', '')
    week = request.args.get('week', '')
    entry = db.diary.find_one({'month': month, 'week': week})
    if entry:
        return jsonify({'answers': entry.get('answers', {}), 'found': True})
    return jsonify({'answers': {}, 'found': False})

@diary_bp.route('/diary/delete', methods=['POST'])
def delete_entry():
    data = request.get_json()
    month = data.get('month', '')
    week = data.get('week', '')
    db.diary.delete_one({'month': month, 'week': week})
    return jsonify({'success': True})
