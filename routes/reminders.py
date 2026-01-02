from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import calendar
from bson.objectid import ObjectId
from database import db

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/reminder')
def reminder():
    reminders = list(db.reminders.find().sort("date", 1))
    today_date = datetime.now()
    today_str = today_date.strftime('%Y-%m-%d')
    
    # Helper to check if a date is skipped
    def is_skipped(reminder, target_date_str):
        skipped = reminder.get('skipped_dates', [])
        return target_date_str in skipped

    # Helper to check if a date is completed
    def is_completed(reminder, target_date_str):
        completed = reminder.get('completed_dates', [])
        return target_date_str in completed

    todays_reminders = []
    for r in reminders:
        if r.get('date') == today_str:
            if not is_skipped(r, today_str):
                r['completed'] = is_completed(r, today_str)
                todays_reminders.append(r)
        elif r.get('recurrence') == 'yearly' and r.get('date')[5:] == today_str[5:]:
            if not is_skipped(r, today_str):
                r['completed'] = is_completed(r, today_str)
                todays_reminders.append(r)
        elif r.get('recurrence') == 'monthly' and r.get('date')[8:] == today_str[8:]:
            if not is_skipped(r, today_str):
                r['completed'] = is_completed(r, today_str)
                todays_reminders.append(r)
            
    # Missed Reminders Logic
    missed_reminders = []
    for r in reminders:
        last_occurrence = None
        
        if r.get('recurrence') == 'monthly':
            try:
                day_of_month = int(r.get('date').split('-')[2])
                # Check current month
                try:
                    candidate = datetime(today_date.year, today_date.month, day_of_month)
                    if candidate.date() < today_date.date():
                        last_occurrence = candidate
                    else:
                        # Check previous month
                        m = today_date.month - 1
                        y = today_date.year
                        if m < 1:
                            m = 12
                            y -= 1
                        last_occurrence = datetime(y, m, day_of_month)
                except ValueError:
                    # If date doesn't exist in current/prev month (e.g. 31st), try previous valid
                    pass
            except: pass
            
        elif r.get('recurrence') == 'yearly':
            try:
                base_date = datetime.strptime(r.get('date'), '%Y-%m-%d')
                # Check current year
                try:
                    candidate = base_date.replace(year=today_date.year)
                    if candidate.date() < today_date.date():
                        last_occurrence = candidate
                    else:
                        last_occurrence = base_date.replace(year=today_date.year - 1)
                except ValueError: pass
            except: pass
            
        else: # One-time
            try:
                event_date = datetime.strptime(r.get('date'), '%Y-%m-%d')
                if event_date.date() < today_date.date():
                    last_occurrence = event_date
            except: pass
            
        if last_occurrence:
            last_occurrence_str = last_occurrence.strftime('%Y-%m-%d')
            if not is_completed(r, last_occurrence_str) and not is_skipped(r, last_occurrence_str):
                r_copy = r.copy()
                r_copy['date'] = last_occurrence_str
                if r.get('recurrence'):
                    r_copy['original_id'] = str(r['_id'])
                missed_reminders.append(r_copy)

    # Sort missed by date (descending - most recent missed first)
    missed_reminders.sort(key=lambda x: x['date'], reverse=True)

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
                        r_copy = r.copy()
                        r_copy['completed'] = is_completed(r, date_str)
                        reminders_for_day.append(r_copy)
                elif r.get('recurrence') == 'yearly':
                    # Check if Month and Day match
                    if r_date[5:] == date_str[5:]:
                        if not is_skipped(r, date_str):
                            r_copy = r.copy()
                            r_copy['completed'] = is_completed(r, date_str)
                            reminders_for_day.append(r_copy)
                elif r.get('recurrence') == 'monthly':
                    # Check if Day matches
                    if r_date[8:] == date_str[8:]:
                        if not is_skipped(r, date_str):
                            r_copy = r.copy()
                            r_copy['completed'] = is_completed(r, date_str)
                            reminders_for_day.append(r_copy)
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
                           missed_reminders=missed_reminders,
                           months_data=months_data,
                           selected_year=selected_year,
                           today_date=today_date.strftime('%A, %B %d, %Y'),
                           today_iso=today_str)

@reminders_bp.route('/reminder/complete', methods=['POST'])
def complete_reminder():
    reminder_id = request.form.get('id')
    date_completed = request.form.get('date')
    
    if reminder_id and date_completed:
        from bson.objectid import ObjectId
        db.reminders.update_one(
            {"_id": ObjectId(reminder_id)},
            {"$addToSet": {"completed_dates": date_completed}}
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "success", "id": reminder_id, "date": date_completed})
            
    return redirect(url_for('reminders.reminder'))

@reminders_bp.route('/reminder/add', methods=['POST'])
def add_reminder():
    title = request.form.get('title')
    date = request.form.get('date')
    recurrence = request.form.get('recurrence') # 'yearly' or None
    remind_days = request.form.get('remind_days') # number or None
    category = request.form.get('category') # 'Birthday', 'Anniversary', etc.
    
    if title and date:
        reminder_data = {
            "title": title,
            "date": date,
            "recurrence": recurrence,
            "category": category,
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
                "recurrence": recurrence,
                "category": category
            })
        
    return redirect(url_for('reminders.reminder'))

@reminders_bp.route('/reminder/delete', methods=['POST'])
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
        
    return redirect(url_for('reminders.reminder'))
