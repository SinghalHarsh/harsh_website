from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from bson.objectid import ObjectId

from app.extensions import db

goals_bp = Blueprint('goals', __name__)


@goals_bp.route('/goals')
def goals():
    all_goals = list(db.goals.find())
    return render_template(
        'pages/goals.html',
        active_goals=[g for g in all_goals if not g.get('completed')],
        completed_goals=[g for g in all_goals if g.get('completed')],
        now=datetime.now(),
    )


@goals_bp.route('/goals/add', methods=['POST'])
def add_goal():
    title = request.form.get('title', '').strip()
    if title:
        db.goals.insert_one({'title': title, 'created_at': datetime.now()})
    return redirect(url_for('goals.goals'))


@goals_bp.route('/goals/edit', methods=['POST'])
def edit_goal():
    goal_id = request.form.get('goal_id')
    title = request.form.get('title', '').strip()

    if not (goal_id and title):
        return jsonify({'error': 'Goal id and title are required'}), 400

    db.goals.update_one(
        {'_id': ObjectId(goal_id)},
        {'$set': {'title': title, 'updated_at': datetime.now()}},
    )
    return jsonify({'status': 'success', 'title': title})


@goals_bp.route('/goals/complete', methods=['POST'])
def complete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.update_one(
            {'_id': ObjectId(goal_id)},
            {'$set': {'completed': True, 'completed_at': datetime.now()}},
        )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'id': goal_id})
    return redirect(url_for('goals.goals'))


@goals_bp.route('/goals/delete', methods=['POST'])
def delete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.delete_one({'_id': ObjectId(goal_id)})
    return redirect(url_for('goals.goals'))
