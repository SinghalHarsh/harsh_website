"""Shared reminder-occurrence logic used by both the dashboard and the
reminders page. All date fields are guarded because documents in the wild
may be missing `date` entirely."""

from datetime import datetime


def is_skipped(reminder, date_str):
    return date_str in reminder.get('skipped_dates', [])


def is_completed(reminder, date_str):
    return date_str in reminder.get('completed_dates', [])


def occurs_on(reminder, date_str):
    """True if `reminder` falls on `date_str`, honouring recurrence."""
    r_date = reminder.get('date')
    if not r_date or len(r_date) != 10:
        return False

    recurrence = reminder.get('recurrence')
    if r_date == date_str:
        return True
    if recurrence == 'yearly':
        return r_date[5:] == date_str[5:]
    if recurrence == 'monthly':
        return r_date[8:] == date_str[8:]
    return False


def active_on(reminders, date_str):
    """Reminders occurring on a date, excluding skipped ones, each annotated
    with its completion state for that date."""
    result = []
    for r in reminders:
        if occurs_on(r, date_str) and not is_skipped(r, date_str):
            entry = r.copy()
            entry['completed'] = is_completed(r, date_str)
            result.append(entry)
    return result


def last_occurrence(reminder, today):
    """Most recent occurrence strictly before today, or None."""
    r_date = reminder.get('date')
    if not r_date or len(r_date) != 10:
        return None

    recurrence = reminder.get('recurrence')
    try:
        base = datetime.strptime(r_date, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None

    if recurrence == 'monthly':
        for year, month in ((today.year, today.month),
                            (today.year - 1, 12) if today.month == 1
                            else (today.year, today.month - 1)):
            try:
                candidate = base.replace(year=year, month=month)
            except ValueError:
                continue
            if candidate.date() < today.date():
                return candidate
        return None

    if recurrence == 'yearly':
        for year in (today.year, today.year - 1):
            try:
                candidate = base.replace(year=year)
            except ValueError:
                continue
            if candidate.date() < today.date():
                return candidate
        return None

    return base if base.date() < today.date() else None


def missed(reminders, today):
    """Reminders whose last occurrence was neither completed nor skipped,
    most recent first."""
    result = []
    for r in reminders:
        occurrence = last_occurrence(r, today)
        if not occurrence:
            continue
        date_str = occurrence.strftime('%Y-%m-%d')
        if is_completed(r, date_str) or is_skipped(r, date_str):
            continue
        entry = r.copy()
        entry['date'] = date_str
        if r.get('recurrence'):
            entry['original_id'] = str(r['_id'])
        result.append(entry)

    result.sort(key=lambda x: x['date'], reverse=True)
    return result
