from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from bson.objectid import ObjectId
from database import db

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/goals/add', methods=['POST'])
def add_goal():
    title = request.form.get('title')
    error = None
    if not title:
        error = 'Goal title is required.'
    else:
        try:
            db.goals.insert_one({
                'title': title,
                'created_at': datetime.now()
            })
        except Exception as e:
            error = f'Failed to add goal: {str(e)}'
    if error:
        # Re-render goals page with error message
        goals_list = list(db.goals.find())
        return render_template('goals.html', goals=goals_list, goal_error=error)
    return redirect(url_for('goals.goals'))

@goals_bp.route('/goals/delete', methods=['POST'])
def delete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.delete_one({'_id': ObjectId(goal_id)})
    return redirect(url_for('goals.goals'))

@goals_bp.route('/goals/complete', methods=['POST'])
def complete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.update_one(
            {'_id': ObjectId(goal_id)},
            {'$set': {'completed': True, 'completed_at': datetime.now()}}
        )
    return redirect(url_for('goals.goals'))

@goals_bp.route('/goals')
def goals():
    goals_list = list(db.goals.find())
    active_goals = [g for g in goals_list if not g.get('completed')]
    completed_goals = [g for g in goals_list if g.get('completed')]
    now = datetime.now()
    return render_template('goals.html', active_goals=active_goals, completed_goals=completed_goals, now=now)
