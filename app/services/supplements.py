"""Supplement slots and intake stats."""

from datetime import timedelta


ALL_SLOTS = ('morning', 'afternoon', 'evening', 'night')
DEFAULT_SLOTS = ('morning', 'evening')
SLOT_ICONS = {
    'morning': 'sun',
    'afternoon': 'cloud-sun',
    'evening': 'moon',
    'night': 'bed',
}
EITHER = 'either'


def normalise_slots(raw):
    """Enabled slots, kept in ALL_SLOTS order and never empty.

    An unknown or duplicated name is dropped rather than trusted, so a stale
    stored value cannot put a slot on the board that nothing can be marked for.
    Falling back to the defaults keeps the page usable if every slot is cleared.
    """
    chosen = {s for s in (raw or ()) if s in ALL_SLOTS}
    ordered = tuple(s for s in ALL_SLOTS if s in chosen)
    return ordered or DEFAULT_SLOTS


def slots_for(supplement, slots):
    """The enabled slots a supplement can be marked in."""
    own = supplement.get('slot', EITHER)
    return [s for s in slots if own in (s, EITHER)]


def entry(date_str, slot):
    """History key for one dose. Slot-qualified so a day can hold several."""
    return f'{date_str}:{slot}'


def entry_date(item):
    """Date half of a history entry.

    Entries logged before slots existed are bare dates, so anything without a
    slot suffix is read as-is and still counts toward the day.
    """
    return item.split(':', 1)[0]


def taken_days(history):
    """Distinct calendar days in a history, ignoring which slot."""
    return {entry_date(item) for item in history}


def annotate(supplement, today, slots=ALL_SLOTS):
    """Attach derived display fields to a supplement document in place.

    Every known slot is filled in, not just the enabled ones, so a dose logged
    under a slot that was later switched off still reads back as taken.
    """
    history = supplement.get('history', [])
    today_iso = today.strftime('%Y-%m-%d')
    days = taken_days(history)

    supplement['taken_today'] = today_iso in days
    supplement['slot'] = supplement.get('slot', EITHER)
    supplement['taken_slots'] = {
        slot: entry(today_iso, slot) in history for slot in set(slots) | set(ALL_SLOTS)
    }
    supplement['times_taken'] = len(history)
    supplement['days_this_year'] = sum(
        1 for d in days if d.startswith(today.strftime('%Y'))
    )
    supplement['streak'] = streak(history, today)
    return supplement


def streak(history, today):
    """Consecutive days taken, counting back from today.

    A gap ends the run. Today not yet taken is not a break — the count simply
    starts at yesterday, so a streak survives until the day is actually missed.
    """
    taken = taken_days(history)
    if not taken:
        return 0

    day = today.date()
    if day.strftime('%Y-%m-%d') not in taken:
        day -= timedelta(days=1)

    count = 0
    while day.strftime('%Y-%m-%d') in taken:
        count += 1
        day -= timedelta(days=1)
    return count
