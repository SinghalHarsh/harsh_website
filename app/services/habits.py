"""Habit scoring.

Every habit keeps a running score, replayed from its history on each read:

  * +1 for a day followed, -2 for a day missed
  * never below zero

Both figures scale with the habit's *net days*: days followed minus days
missed. Every `TIER_LENGTH` net days moves the habit up a tier, worth one
more point per day and one more penalty point per miss:

    net days  0-21   +1 / -2
    net days 22-42   +2 / -4
    net days 43-63   +3 / -6

Net days rise by one for every day followed and fall by one for every day
missed, so a single miss can drop a habit back a tier and a single good day
can win it back. It is not the streak: an occasional miss costs one net day,
not the whole climb.

Following a habit also earns credits — one per five days followed. Spending a
credit marks a day as a rest day: it counts as followed, so the streak survives
and the point is still earned. Days claimed as rest are stored in `rest_days`.
A day that is simply missed also spends a credit if one is available, so an
unclaimed slip is covered the same way.

Miss five days in a row, or sit at zero for ten, and the habit resets: its
score returns to zero. Leave it untouched for `RETIRE_AFTER_DEAD` days beyond
that and it drops out of the active list back into your ideas, so the board
only shows habits you are actually keeping.
"""

from datetime import timedelta

HIT = 1
MISS = -2

# Days of streak per tier. Each tier adds one point to a hit and two to a miss.
TIER_LENGTH = 21

CREDIT_EVERY = 5      # default days followed before rest days are earned
CREDIT_AMOUNT = 1     # default rest days earned each time
CREDIT_CAP = 10       # stops a long run banking an endless holiday
NO_REST = 9999        # a rate this high means the habit never earns rest days

RESET_AFTER_MISSES = 5
RESET_AFTER_DEAD = 10
RETIRE_AFTER_DEAD = 10   # further idle days before it leaves the active list


def tier_for(net_days):
    """Tier from net days: 1 up to 21, 2 from 22, 3 from 43, and so on."""
    if net_days <= 0:
        return 1
    return (net_days - 1) // TIER_LENGTH + 1


def rates_for(net_days):
    """Points gained per day followed and lost per day missed at this level."""
    tier = tier_for(net_days)
    return tier * HIT, tier * MISS


def credit_every(habit):
    """Days that must be followed before rest days are earned (default 5)."""
    try:
        value = int(habit.get('credit_every', CREDIT_EVERY))
    except (TypeError, ValueError):
        value = CREDIT_EVERY
    if value <= 0:
        return NO_REST
    return min(NO_REST, value)


def credit_amount(habit):
    """Rest days earned each time the threshold is reached (default 1).

    Zero means the habit never earns rest days: every miss costs.
    """
    try:
        value = int(habit.get('credit_amount', CREDIT_AMOUNT))
    except (TypeError, ValueError):
        value = CREDIT_AMOUNT
    return max(0, min(7, value))


class _State:
    """A habit's score as history is replayed over it."""

    def __init__(self, credit_every=CREDIT_EVERY, credit_amount=CREDIT_AMOUNT):
        self.credit_every = credit_every
        self.credit_amount = credit_amount
        self.score = 0
        self.credits = 0
        self.credits_used = 0
        self.followed = 0
        self.net_days = 0
        self.streak = 0
        self.best_streak = 0
        self.misses_in_row = 0
        self.days_at_zero = 0
        self.was_reset = False

    def follow(self, earns_credit=True):
        """Count a day as followed.

        `earns_credit` is False for days paid for with a credit: a rest day
        must not pay towards the next one, or a habit with a generous rate
        would fund its own neglect for ever.
        """
        # Net days rise first, so the day is paid at the tier it reaches.
        self.net_days += 1
        self.score += tier_for(self.net_days) * HIT
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        self.misses_in_row = 0
        self.days_at_zero = 0

        if not earns_credit:
            return

        self.followed += 1
        if self.credit_amount and self.followed % self.credit_every == 0:
            self.credits = min(CREDIT_CAP, self.credits + self.credit_amount)

    def spend_credit(self):
        """Take a rest day: costs a credit, counts as a day followed."""
        if not self.credits:
            return False
        self.credits -= 1
        self.credits_used += 1
        self.follow(earns_credit=False)
        return True

    def miss(self):
        """Spend a credit if there is one, otherwise take the penalty."""
        if self.spend_credit():
            return

        # Charged at the tier held before the miss, then net days drop.
        self.score = max(0, self.score + tier_for(self.net_days) * MISS)
        self.net_days = max(0, self.net_days - 1)
        self.streak = 0
        self.misses_in_row += 1
        if self.score == 0:
            self.days_at_zero += 1

        if (self.misses_in_row >= RESET_AFTER_MISSES
                or self.days_at_zero >= RESET_AFTER_DEAD):
            self.reset()

    def reset(self):
        """Back to zero. The habit stays tracked and starts over when followed.

        `best_streak` deliberately survives — it is an all-time record of what
        you managed, not a property of the current run.
        """
        self.was_reset = True
        self.score = 0
        self.streak = 0
        self.net_days = 0
        self.credits = 0
        self.followed = 0

def _start_date(habit, today):
    """When the habit began counting: its creation date, or its first entry."""
    stamps = [str(habit['created_at'])[:10]] if habit.get('created_at') else []
    history = sorted(habit.get('history', []))
    if history:
        stamps.append(history[0])
    if not stamps:
        return today

    try:
        year, month, day = (int(part) for part in min(stamps).split('-'))
        return today.replace(year=year, month=month, day=day)
    except (ValueError, TypeError):
        return today


def _replay_days(habit, today):
    """Daily habit: walk each day from its start date to today."""
    history = set(habit.get('history', []))
    rest = set(habit.get('rest_days', []))
    state = _State(credit_every(habit), credit_amount(habit))

    date = _start_date(habit, today)
    while date <= today:
        date_str = date.strftime('%Y-%m-%d')
        done = date_str in history

        if done:
            state.follow()
        elif date_str in rest:
            # Claimed as a rest day: spend a credit if one is banked, otherwise
            # the claim is unaffordable and the day counts as missed.
            if not state.spend_credit():
                state.miss()
        elif date < today:
            # Today is still open, so an untouched today is not yet a miss.
            state.miss()

        date += timedelta(days=1)

    return state


def habit_state(habit, today):
    """Replay a habit's history into its current score.

    A habit with no entries at all has never been started, so it reads as a
    fresh habit rather than one that has been missed into a reset.
    """
    if not habit.get('history'):
        return _State(credit_every(habit), credit_amount(habit))
    return _replay_days(habit, today)


def annotate(habit, today):
    """Attach display fields to a habit document in place."""
    history = set(habit.get('history', []))
    today_str = today.strftime('%Y-%m-%d')
    state = habit_state(habit, today)

    habit['completed_today'] = today_str in history
    habit['rested_today'] = today_str in set(habit.get('rest_days', []))
    habit['can_rest'] = (
        not habit['completed_today'] and not habit['rested_today']
    )

    habit['points'] = state.score
    habit['credits'] = state.credits
    habit['streak'] = state.streak
    habit['best_streak'] = state.best_streak
    habit['net_days'] = state.net_days
    habit['tier'] = tier_for(state.net_days)
    habit['hit_points'], habit['miss_points'] = rates_for(state.net_days)
    habit['was_reset'] = state.was_reset
    habit['days_idle'] = days_idle(habit, today)
    habit['should_retire'] = (
        state.was_reset
        and not state.score
        and habit['days_idle'] >= RETIRE_AFTER_DEAD
    )
    habit['credit_every'] = state.credit_every
    habit['credit_amount'] = state.credit_amount
    return habit


def days_idle(habit, today):
    """Days since the habit was last followed or rested."""
    stamps = list(habit.get('history') or []) + list(habit.get('rest_days') or [])
    if not stamps:
        return 0
    try:
        year, month, day = (int(part) for part in max(stamps).split('-'))
        return (today - today.replace(year=year, month=month, day=day)).days
    except (ValueError, TypeError):
        return 0


def _covered(habit, date_str):
    """Followed that day, either by doing it or by spending a rest credit."""
    return (date_str in habit.get('history', [])
            or date_str in habit.get('rest_days', []))


def daily_score(habits, today):
    """How today went: habits covered over habits tracked, as a percentage.

    A rest day counts as covered — the credit was earned, so spending it should
    not read as a miss.
    """
    today_str = today.strftime('%Y-%m-%d')
    done = [h for h in habits if _covered(h, today_str)]

    return {
        'score': round(len(done) / len(habits) * 100) if habits else 0,
        'completed': len(done),
        'total': len(habits),
    }


MAX_SERIES_DAYS = 400


def tracking_since(habits, today):
    """The first day anything was tracked, or today if nothing has been."""
    stamps = []
    for habit in habits:
        history = habit.get('history') or []
        if history:
            stamps.append(min(history))
        elif habit.get('created_at'):
            stamps.append(str(habit['created_at'])[:10])
    if not stamps:
        return today

    try:
        year, month, day = (int(part) for part in min(stamps).split('-'))
        return today.replace(year=year, month=month, day=day)
    except (ValueError, TypeError):
        return today


def series_length(habits, today):
    """Days to plot: the whole practice so far, within a sane maximum."""
    span = (today - tracking_since(habits, today)).days + 1
    return max(1, min(span, MAX_SERIES_DAYS))


def score_series(habits, today, days):
    """Points and completions for each of the last `days` days.

    Each habit is replayed once, forwards, recording its score as every day
    passes. Asking `habit_state` for each habit on each day would replay the
    same history from scratch hundreds of times over.

    Per-habit figures come back as one array each rather than a map per day:
    the ids are then written once instead of once for every day plotted.
    """
    start = today - timedelta(days=days - 1)
    dates = [start + timedelta(days=i) for i in range(days)]
    stamps = [d.strftime('%Y-%m-%d') for d in dates]

    points = [0] * days
    completed = [0] * days
    tracked = [0] * days
    per_habit = {}

    for habit in habits:
        key = str(habit.get('_id') or '')
        if not key:
            continue

        scores = _replay_scores(habit, today, stamps[0])
        born = str(habit.get('created_at', ''))[:10]

        habit_points = [0] * days
        habit_done = [0] * days

        for i, stamp in enumerate(stamps):
            if born and born > stamp:
                continue

            score = scores.get(stamp, 0)
            done = 1 if _covered(habit, stamp) else 0

            habit_points[i] = score
            habit_done[i] = done
            points[i] += score
            completed[i] += done
            tracked[i] += 1

        per_habit[key] = {'points': habit_points, 'done': habit_done}

    return {
        'labels': [d.strftime('%b %d') for d in dates],
        'points': points,
        'completed': completed,
        'total': tracked,
        'per_habit': per_habit,
    }


def _replay_scores(habit, today, from_stamp):
    """Replay a habit once, returning its score on each day from `from_stamp`."""
    if not habit.get('history'):
        return {}

    history = set(habit.get('history', []))
    rest = set(habit.get('rest_days', []))
    state = _State(credit_every(habit), credit_amount(habit))

    scores = {}
    date = _start_date(habit, today)
    while date <= today:
        stamp = date.strftime('%Y-%m-%d')

        if stamp in history:
            state.follow()
        elif stamp in rest:
            if not state.spend_credit():
                state.miss()
        elif date < today:
            state.miss()

        if stamp >= from_stamp:
            scores[stamp] = state.score
        date += timedelta(days=1)

    return scores


def metrics(habits, today, days=None, active=None):
    """Headline totals plus the series behind the progress chart.

    `habits` is every tracked habit, so the chart keeps the history of ones
    that have since been retired. `active` is the subset still on the board,
    which is what today's figures describe.
    """
    if active is None:
        active = habits

    states = [habit_state(h, today) for h in active]
    series = score_series(habits, today, days or series_length(habits, today))

    points = sum(s.score for s in states)
    totals = series['points']
    week_ago = totals[-8] if len(totals) >= 8 else 0

    return {
        'points': points,
        'points_delta': points - week_ago,
        'series': series,
        'chart_habits': [
            {'id': str(h['_id']), 'name': h.get('name', '')}
            for h in habits if h.get('_id')
        ],
        'rules': {
            'hit': HIT,
            'miss': MISS,
            'tier_length': TIER_LENGTH,
                'reset_after': RESET_AFTER_MISSES,
        },
    }
