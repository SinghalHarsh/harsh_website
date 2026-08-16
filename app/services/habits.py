"""Habit streak, status and scoring logic."""

from datetime import timedelta

# A streak stops adding to the score past this many days, so a single very
# old habit cannot dominate the daily figure.
STREAK_CAP = 30


def streak_length(history, today):
    """Consecutive days ending today, or yesterday if today is not yet done."""
    today_str = today.strftime('%Y-%m-%d')
    cursor = today if today_str in history else today - timedelta(days=1)

    length = 0
    while cursor.strftime('%Y-%m-%d') in history:
        length += 1
        cursor -= timedelta(days=1)
    return length


def annotate(habit, today):
    """Attach derived display fields to a habit document in place."""
    history = set(habit.get('history', []))
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    habit['completed_today'] = today_str in history
    habit['streak'] = streak_length(history, today)
    habit['days_in_current_year'] = sum(
        1 for d in history if d.startswith(today.strftime('%Y'))
    )

    if habit['completed_today']:
        habit['status'] = 'Completed today'
    elif yesterday_str in history:
        habit['status'] = 'Pending today'
    else:
        habit['status'] = 'Missed yesterday'

    return habit


def daily_score(habits, today):
    """Today's score as a 0-100 percentage.

    Each habit contributes its completion today, weighted by streak momentum
    so that maintaining a long streak counts for more than a one-off tick.
    """
    if not habits:
        return {'score': 0, 'completed': 0, 'total': 0, 'streak_bonus': 0}

    today_str = today.strftime('%Y-%m-%d')
    completed = [h for h in habits if today_str in h.get('history', [])]

    base = len(completed) / len(habits) * 100

    # Momentum: mean capped streak across completed habits, worth up to 100.
    if completed:
        streaks = [
            min(streak_length(set(h.get('history', [])), today), STREAK_CAP)
            for h in completed
        ]
        momentum = sum(streaks) / len(streaks) / STREAK_CAP * 100
    else:
        momentum = 0

    return {
        'score': round(base * 0.7 + momentum * 0.3),
        'completed': len(completed),
        'total': len(habits),
        'streak_bonus': round(momentum),
    }
