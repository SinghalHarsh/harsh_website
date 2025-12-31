
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv
import os
import random
from datetime import datetime, timedelta
import calendar
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)

@app.context_processor
def inject_site_info():
    return {'site_name': 'Harsh Singhal'}


@app.context_processor
def inject_public_env():
    # Only expose env vars explicitly marked as public to avoid leaking secrets.
    public_env = {k: v for k, v in os.environ.items() if k.startswith('PUBLIC_')}
    return {'env': public_env}

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
try:
    db = client.get_database()
except ConfigurationError:
    db = client.get_database("harsh_website")



@app.route('/goals/add', methods=['POST'])
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
    return redirect(url_for('goals'))


@app.route('/')
def home():
    # Habits Stats
    today_str = datetime.now().strftime('%Y-%m-%d')
    all_habits = list(db.habits.find({"active": True}))
    habits_completed = 0
    pending_habits = []
    
    for h in all_habits:
        if today_str in h.get('history', []):
            habits_completed += 1
        else:
            pending_habits.append(h)
            
    habits_total = len(all_habits)
    
    # Goals Stats
    active_goals_cursor = db.goals.find({"completed": {"$ne": True}})
    active_goals = list(active_goals_cursor)
    active_goals_count = len(active_goals)
    
    # Reminders Today
    reminders = list(db.reminders.find())
    todays_reminders = []
    
    def is_skipped(reminder, target_date_str):
        skipped = reminder.get('skipped_dates', [])
        return target_date_str in skipped

    for r in reminders:
        if r.get('date') == today_str:
             if not is_skipped(r, today_str):
                 todays_reminders.append(r)
        elif r.get('recurrence') == 'yearly' and r.get('date')[5:] == today_str[5:]:
             if not is_skipped(r, today_str):
                 todays_reminders.append(r)

    reminders_today_count = len(todays_reminders)

    # Quotes Logic (Random Quote)
    text_quotes = list(db.quotes.find())
    images_dir = os.path.join(app.static_folder, 'images', 'quotes')
    image_quotes = []
    if os.path.exists(images_dir):
        image_quotes = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    all_content = []
    for q in text_quotes:
        all_content.append({'type': 'text', 'data': q})
    for img in image_quotes:
        all_content.append({'type': 'image', 'filename': img})
    
    selected_quote = random.choice(all_content) if all_content else None

    return render_template('index.html', 
                           habits_completed=habits_completed, 
                           habits_total=habits_total,
                           pending_habits=pending_habits,
                           active_goals_count=active_goals_count,
                           active_goals=active_goals,
                           reminders_today_count=reminders_today_count,
                           todays_reminders=todays_reminders,
                           selected_quote=selected_quote)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    posts = list(db.blogs.find())
    return render_template('blog.html', posts=posts)

@app.route('/reminder')
def reminder():
    reminders = list(db.reminders.find().sort("date", 1))
    today_date = datetime.now()
    today_str = today_date.strftime('%Y-%m-%d')
    
    # Helper to check if a date is skipped
    def is_skipped(reminder, target_date_str):
        skipped = reminder.get('skipped_dates', [])
        return target_date_str in skipped

    todays_reminders = []
    for r in reminders:
        if r.get('date') == today_str:
            if not is_skipped(r, today_str):
                todays_reminders.append(r)
        elif r.get('recurrence') == 'yearly' and r.get('date')[5:] == today_str[5:]:
            if not is_skipped(r, today_str):
                todays_reminders.append(r)
            
    # Show reminders where:
    # - The event date is within the next 5 days (regardless of remind_days_before)
    # - OR the notification date (event - remind_days_before) is within the next 'remind_days_before' days from today
    upcoming_reminders = []
    window_days = 5
    window_end = today_date + timedelta(days=window_days)
    for r in reminders:
        event_date = datetime.strptime(r.get('date'), '%Y-%m-%d')
        remind_days = int(r.get('remind_days_before', 0))
        notify_date = event_date - timedelta(days=remind_days)

        # For recurring yearly reminders, adjust the year if needed
        if r.get('recurrence') == 'yearly':
            event_date = event_date.replace(year=today_date.year)
            notify_date = event_date - timedelta(days=remind_days)

        # Show if event is within window, but not today
        show_event = event_date.date() > today_date.date() and event_date.date() <= window_end.date()
        # Show if today is after or on the notification date
        show_notify = notify_date.date() <= today_date.date()

        # Skip if event is today (already shown in today's reminders)
        if event_date.date() == today_date.date():
            continue

        if (show_event or show_notify) and not is_skipped(r, r.get('date')):
            r_copy = r.copy()
            r_copy['date'] = event_date.strftime('%Y-%m-%d')
            if r.get('recurrence') == 'yearly':
                r_copy['original_id'] = str(r['_id'])
            upcoming_reminders.append(r_copy)

    # Sort by event date
    upcoming_reminders.sort(key=lambda x: x['date'])

    # Year Selection Logic
    year_arg = request.args.get('year')
    current_year = datetime.now().year
    selected_year = int(year_arg) if year_arg else current_year

    # Year Selection Logic
    year_arg = request.args.get('year')
    current_year = datetime.now().year
    selected_year = int(year_arg) if year_arg else current_year

    # Generate Data Grouped by Month
    months_data = []
    
    for m in range(1, 13):
        # Get number of days in month and weekday of first day
        first_weekday, num_days = calendar.monthrange(selected_year, m)
        # Python's calendar: Monday=0, Sunday=6
        month_days = []
        # Padding for first week
        for _ in range(first_weekday):
            month_days.append(None)
        for d in range(1, num_days + 1):
            date_obj = datetime(selected_year, m, d)
            date_str = date_obj.strftime('%Y-%m-%d')
            display_date = date_obj.strftime('%a, %b %d, %Y')
            # Filter reminders for this day (Exact date OR Recurring yearly)
            reminders_for_day = []
            for r in reminders:
                r_date = r.get('date')
                if r_date == date_str:
                    if not is_skipped(r, date_str):
                        reminders_for_day.append(r)
                elif r.get('recurrence') == 'yearly':
                    # Check if Month and Day match
                    if r_date[5:] == date_str[5:]:
                        if not is_skipped(r, date_str):
                            reminders_for_day.append(r)
            month_days.append({
                'date': date_str,
                'display_date': display_date,
                'day': d,
                'count': len(reminders_for_day),
                'reminders': reminders_for_day
            })
        months_data.append({
            'name': calendar.month_abbr[m],
            'days': month_days
        })

    return render_template('reminder.html', 
                           todays_reminders=todays_reminders, 
                           upcoming_reminders=upcoming_reminders,
                           months_data=months_data,
                           selected_year=selected_year,
                           today_date=today_date.strftime('%A, %B %d, %Y'))

@app.route('/reminder/add', methods=['POST'])
def add_reminder():
    title = request.form.get('title')
    date = request.form.get('date')
    recurrence = request.form.get('recurrence') # 'yearly' or None
    remind_days = request.form.get('remind_days') # number or None
    
    if title and date:
        reminder_data = {
            "title": title,
            "date": date,
            "recurrence": recurrence,
            "created_at": datetime.now()
        }
        
        if remind_days:
            reminder_data["remind_days_before"] = int(remind_days)
            
        result = db.reminders.insert_one(reminder_data)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "status": "success", 
                "id": str(result.inserted_id),
                "title": title,
                "date": date,
                "recurrence": recurrence
            })
        
    return redirect(url_for('reminder'))

@app.route('/reminder/delete', methods=['POST'])
def delete_reminder():
    reminder_id = request.form.get('id')
    delete_mode = request.form.get('mode') # 'instance' or 'series'
    date_to_skip = request.form.get('date') # Required if mode is 'instance'
    
    if reminder_id:
        from bson.objectid import ObjectId
        
        if delete_mode == 'instance' and date_to_skip:
            # Add date to skipped_dates array
            db.reminders.update_one(
                {"_id": ObjectId(reminder_id)},
                {"$addToSet": {"skipped_dates": date_to_skip}}
            )
        else:
            # Default: Delete permanently
            db.reminders.delete_one({"_id": ObjectId(reminder_id)})
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "id": reminder_id})
        
    return redirect(url_for('reminder'))

@app.route('/goals/delete', methods=['POST'])
def delete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.delete_one({'_id': ObjectId(goal_id)})
    return redirect(url_for('goals'))

@app.route('/quotes')
def quotes():
    # 1. Get text quotes from DB
    text_quotes = list(db.quotes.find())
    
    # 2. Get image quotes from static folder
    images_dir = os.path.join(app.static_folder, 'images', 'quotes')
    image_quotes = []
    if os.path.exists(images_dir):
        image_quotes = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    all_content = []
    for q in text_quotes:
        all_content.append({'type': 'text', 'data': q})
        
    for img in image_quotes:
        all_content.append({'type': 'image', 'filename': img})
    
    # 4. Pick one random item
    selected_content = random.choice(all_content) if all_content else None
    
    return render_template('quotes.html', content=selected_content)

@app.route('/habits')
def habits():
    # Fetch all habits but separate active ones for display
    all_habits = list(db.habits.find())
    
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
            
        h['streak'] = f"{streak} Days"
        
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
        habit_history = set(selected_habit.get('history', [])) if selected_habit else set()
        
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
                
                if is_overall:
                    # Calculate completion for all active habits
                    completed_count = 0
                    total_active = len(active_habits)
                    for h in active_habits:
                        if date_str in h.get('history', []):
                            completed_count += 1
                    
                    completion_rate = (completed_count / total_active) if total_active > 0 else 0
                    
                    month_days.append({
                        'date': date_str,
                        'display_date': display_date,
                        'day': d,
                        'completed_count': completed_count,
                        'total_active': total_active,
                        'rate': completion_rate
                    })
                else:
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

@app.route('/habits/toggle', methods=['POST'])
def toggle_habit():
    habit_name = request.form.get('habit_name')
    is_active = request.form.get('active') == 'on'
    
    db.habits.update_one(
        {"name": habit_name},
        {"$set": {"active": is_active}}
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": habit_name, "active": is_active})

    return redirect(url_for('habits'))

@app.route('/habits/add', methods=['POST'])
def add_habit():
    name = request.form.get('name')
    color = request.form.get('color')
    active_status = request.form.get('active') == 'true'
    
    if name:
        db.habits.insert_one({
            "name": name,
            "streak": "0 Days",
            "status": "New",
            "color": color if color else "text-blue",
            "active": active_status,
            "history": []
        })
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": name})

    return redirect(url_for('habits'))

@app.route('/habits/delete', methods=['POST'])
def delete_habit():
    habit_name = request.form.get('habit_name')
    if habit_name:
        db.habits.delete_one({"name": habit_name})
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "success", "name": habit_name})
        
    return redirect(url_for('habits'))

@app.route('/habits/log', methods=['POST'])
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
        
    return redirect(url_for('habits'))

@app.route('/goals/complete', methods=['POST'])
def complete_goal():
    goal_id = request.form.get('goal_id')
    if goal_id:
        db.goals.update_one(
            {'_id': ObjectId(goal_id)},
            {'$set': {'completed': True, 'completed_at': datetime.now()}}
        )
    return redirect(url_for('goals'))

@app.route('/goals')
def goals():
    goals_list = list(db.goals.find())
    active_goals = [g for g in goals_list if not g.get('completed')]
    completed_goals = [g for g in goals_list if g.get('completed')]
    from datetime import datetime
    now = datetime.now()
    return render_template('goals.html', active_goals=active_goals, completed_goals=completed_goals, now=now)

if __name__ == '__main__':
    app.run(debug=True)
