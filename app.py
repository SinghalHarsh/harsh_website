from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import calendar

load_dotenv()

app = Flask(__name__)

@app.context_processor
def inject_site_info():
    return {'site_name': 'Harsh Singhal'}

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

@app.route('/')
def home():
    stats = list(db.dashboard_stats.find())
    return render_template('index.html', stats=stats)

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
    
    todays_reminders = []
    for r in reminders:
        if r.get('date') == today_str:
            todays_reminders.append(r)
        elif r.get('recurrence') == 'yearly' and r.get('date')[5:] == today_str[5:]:
            todays_reminders.append(r)
            
    # Simple upcoming logic (needs improvement for recurring, but keeping basic for now)
    upcoming_reminders = [r for r in reminders if r.get('date') > today_str]

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
        # monthrange returns (weekday, num_days) where Mon=0
        first_weekday, num_days = calendar.monthrange(selected_year, m)
        
        month_days = []
        # Padding
        for _ in range(first_weekday):
            month_days.append(None)
            
        # Actual days
        for d in range(1, num_days + 1):
            date_obj = datetime(selected_year, m, d)
            date_str = date_obj.strftime('%Y-%m-%d')
            
            # Filter reminders for this day (Exact date OR Recurring yearly)
            reminders_for_day = []
            for r in reminders:
                r_date = r.get('date')
                if r_date == date_str:
                    reminders_for_day.append(r)
                elif r.get('recurrence') == 'yearly':
                    # Check if Month and Day match
                    if r_date[5:] == date_str[5:]:
                        reminders_for_day.append(r)
            
            month_days.append({
                'date': date_str,
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
                           today_date=today_date.strftime('%Y-%m-%d'))

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
            
        db.reminders.insert_one(reminder_data)
        
    return redirect(url_for('reminder'))

@app.route('/quotes')
def quotes():
    quote = db.quotes.find_one()
    return render_template('quotes.html', quote=quote)

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
    
    # Get selected habit or default to first active one
    selected_habit_name = request.args.get('habit')
    selected_habit = None
    
    if active_habits:
        if selected_habit_name:
            selected_habit = next((h for h in active_habits if h['name'] == selected_habit_name), active_habits[0])
        else:
            selected_habit = active_habits[0]
            
    # Year Selection Logic (same as reminders)
    year_arg = request.args.get('year')
    current_year = datetime.now().year
    selected_year = int(year_arg) if year_arg else current_year
    # today_date is already defined above

    # Generate Heatmap Data for Selected Habit
    months_data = []
    
    if selected_habit:
        habit_history = set(selected_habit.get('history', []))
        
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
                
                is_completed = date_str in habit_history
                
                month_days.append({
                    'date': date_str,
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
                           months_data=months_data,
                           selected_year=selected_year,
                           today_date=today_date.strftime('%Y-%m-%d'))

@app.route('/habits/toggle', methods=['POST'])
def toggle_habit():
    habit_name = request.form.get('habit_name')
    is_active = request.form.get('active') == 'on'
    
    db.habits.update_one(
        {"name": habit_name},
        {"$set": {"active": is_active}}
    )
    return redirect(url_for('habits'))

@app.route('/habits/add', methods=['POST'])
def add_habit():
    name = request.form.get('name')
    color = request.form.get('color')
    
    if name:
        db.habits.insert_one({
            "name": name,
            "streak": "0 Days",
            "status": "New",
            "color": color if color else "text-blue",
            "active": True,
            "history": []
        })
    return redirect(url_for('habits'))

@app.route('/habits/delete', methods=['POST'])
def delete_habit():
    habit_name = request.form.get('habit_name')
    if habit_name:
        db.habits.delete_one({"name": habit_name})
    return redirect(url_for('habits'))

@app.route('/habits/log', methods=['POST'])
def log_habit():
    habit_name = request.form.get('habit_name')
    date_str = request.form.get('date') # YYYY-MM-DD
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    habit = db.habits.find_one({"name": habit_name})
    if habit:
        history = habit.get('history', [])
        if date_str in history:
            history.remove(date_str) # Toggle off
        else:
            history.append(date_str) # Toggle on
            
        # Update DB
        db.habits.update_one(
            {"name": habit_name},
            {"$set": {"history": history}}
        )
        
    return redirect(url_for('habits'))

@app.route('/goals')
def goals():
    goals_list = list(db.goals.find())
    return render_template('goals.html', goals=goals_list)

if __name__ == '__main__':
    app.run(debug=True)
