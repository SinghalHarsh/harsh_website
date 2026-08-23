"""Weighted supplement selection and intake stats."""

import random


def weighted_pick(supplements, rng=random):
    """Pick one supplement with probability proportional to its weight.

    Walks the cumulative weight line and takes the first entry whose running
    total passes a uniform draw, so a weight of 50 against 30 and 20 is chosen
    half the time. Returns None when nothing has a usable weight.
    """
    candidates = [s for s in supplements if s.get('weight', 0) > 0]
    if not candidates:
        return None

    total = sum(s['weight'] for s in candidates)
    draw = rng.uniform(0, total)

    running = 0
    for supplement in candidates:
        running += supplement['weight']
        if draw <= running:
            return supplement
    return candidates[-1]


def annotate(supplement, today, total_weight):
    """Attach derived display fields to a supplement document in place."""
    history = supplement.get('history', [])

    supplement['taken_today'] = today.strftime('%Y-%m-%d') in history
    supplement['times_taken'] = len(history)
    supplement['days_this_year'] = sum(
        1 for d in history if d.startswith(today.strftime('%Y'))
    )
    supplement['chance'] = (
        round(supplement.get('weight', 0) / total_weight * 100) if total_weight else 0
    )
    return supplement


def total_weight(supplements):
    return sum(s.get('weight', 0) for s in supplements if s.get('weight', 0) > 0)
