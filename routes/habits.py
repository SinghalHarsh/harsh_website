from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
import calendar
from database import db

habits_bp = Blueprint('habits', __name__)

@habits_bp.route('/habits')
def habits():
    # Fetch all habits including soft-deleted ones for calculation
    all_raw_habits = list(db.habits.find())
    
    # Filter for display (exclude deleted)
    all_habits = [h for h in all_raw_habits if not h.get('deleted')]
    
    today_date = datetime.now()
    today_str = today_date.strftime('%Y-%m-%d')
    yesterday_str = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')

    # Process habits (calculate streak and check today's status)
    for h in all_habits:
        history = set(h.get('history', []))
        h['completed_today'] = today_str in history
        
        # Calculate Streak
        streak = 0
        check_date = today_date
        # If not done today, check if done yesterday to keep streak alive
        if today_str not in history:
            check_date = today_date - timedelta(days=1)
            
        while check_date.strftime('%Y-%m-%d') in history:
            streak += 1
            check_date -= timedelta(days=1)
            
        h['streak'] = streak  # Store as integer for cleaner template usage if needed, or keep string
        
        # Calculate days completed in current year
        current_year_prefix = today_date.strftime('%Y')
        days_in_current_year = sum(1 for date in history if date.startswith(current_year_prefix))
        h['days_in_current_year'] = days_in_current_year

        # Update status text
        if h['completed_today']:
            h['status'] = "Completed today"
        elif yesterday_str in history:
            h['status'] = "Pending today"
        else:
            h['status'] = "Missed yesterday"

    active_habits = [h for h in all_habits if h.get('active', True)]
    
    # Get selected habit or default to overall
    selected_habit_name = request.args.get('habit')
    selected_habit = None
    is_overall = False
    
    if not selected_habit_name or selected_habit_name == 'overall':
        is_overall = True
    elif active_habits:
        selected_habit = next((h for h in active_habits if h['name'] == selected_habit_name), None)
        if not selected_habit:
            is_overall = True
            
    # Year Selection Logic (same as reminders)
    year_arg = request.args.get('year')
    current_year = datetime.now().year
    selected_year = int(year_arg) if year_arg else current_year
    # today_date is already defined above

    # Generate Heatmap Data for Selected Habit
    months_data = []
    
    if selected_habit or is_overall:
        search_target_habits = [selected_habit] if selected_habit else all_raw_habits # use all_raw_habits for overall to include deleted
        
        for m in range(1, 13):
            first_weekday, num_days = calendar.monthrange(selected_year, m)
            
            month_days = []
            # Padding
            for _ in range(first_weekday):
                month_days.append(None)
                
            # Actual days
            for d in range(1, num_days + 1):
                date_obj = datetime(selected_year, m, d)
                date_str = date_obj.strftime('%Y-%m-%d')
                display_date = date_obj.strftime('%a, %b %d, %Y')
                
                # Don't show future dates
                if date_obj > today_date and date_obj.date() > today_date.date():
                    month_days.append({
                        'date': date_str,
                        'display_date': display_date,
                        'day': d,
                        'future': True
                    })
                    continue

                if is_overall:
                    # Logic simplified: Just count how many habits were completed on this day.
                    # No longer calculating "active" denominator which was causing confusion.
                    completed_count = 0
                    for h in search_target_habits:
                        if date_str in h.get('history', []):
                            completed_count += 1
                    
                    month_days.append({
                        'date': date_str,
                        'display_date': display_date,
                        'day': d,
                        'completed_count': completed_count
                    })
                else:
                    habit_history = set(selected_habit.get('history', [])) if selected_habit else set()
                    is_completed = date_str in habit_history
                    month_days.append({
                        'date': date_str,
                        'display_date': display_date,
                        'day': d,
                        'completed': is_completed
                    })
                
            months_data.append({
                'name': calendar.month_abbr[m],
                'days': month_days
            })

    return render_template('habits.html', 
                           habits=active_habits,
                           all_habits=all_habits,
                           selected_habit=selected_habit,
                           is_overall=is_overall,
                           months_data=months_data,
                           selected_year=selected_year,
                           today_date=today_date.strftime('%A, %B %d, %Y'),
                           today_iso=today_date.strftime('%Y-%m-%d'))

@habits_bp.route('/habits/toggle', methods=['POST'])
def toggle_habit():
    habit_name = request.form.get('habit_name')
    is_active = request.form.get('active') == 'on'
    
    db.habits.update_one(
        {"name": habit_name},
        {"$set": {"active": is_active}}
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": habit_name, "active": is_active})

    return redirect(url_for('habits.habits'))

@habits_bp.route('/habits/add', methods=['POST'])
def add_habit():
    name = request.form.get('name')
    color = request.form.get('color')
    active_status = request.form.get('active') == 'true'
    
    if name:
        today = datetime.now().strftime('%Y-%m-%d')
        
        db.habits.insert_one({
            "name": name,
            "streak": "0 Days",
            "status": "New",
            "color": color if color else "text-blue",
            "active": active_status,
            "created_at": today,
            "history": []
        })
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": name})

    return redirect(url_for('habits.habits'))

@habits_bp.route('/habits/delete', methods=['POST'])
def delete_habit():
    habit_name = request.form.get('habit_name')
    if habit_name:
        # Soft delete instead of remove
        today = datetime.now().strftime('%Y-%m-%d')
        
        db.habits.update_one(
            {"name": habit_name},
            {"$set": {
                "deleted": True, 
                "deleted_at": today,
                "active": False # Ensure it is marked inactive
            }}
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": habit_name})
        
    return redirect(url_for('habits.habits'))

@habits_bp.route('/habits/log', methods=['POST'])
def log_habit():
    habit_name = request.form.get('habit_name')
    date_str = request.form.get('date') # YYYY-MM-DD
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    habit = db.habits.find_one({"name": habit_name})
    status = "unchanged"
    if habit:
        history = habit.get('history', [])
        if date_str in history:
            history.remove(date_str) # Toggle off
            status = "removed"
        else:
            history.append(date_str) # Toggle on
            status = "added"
            
        # Update DB
        db.habits.update_one(
            {"name": habit_name},
            {"$set": {"history": history}}
        )
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "action": status, "habit_name": habit_name})
        
    return redirect(url_for('habits.habits'))
