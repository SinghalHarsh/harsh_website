"""Sadhana scoring for the weekly spiritual diary.

Answers arrive keyed 'q{question}_d{day}', matching the diary grid, so scoring
works directly off a stored entry's answers dict.
"""

import re

# Question indexes that carry a numeric practice value, with the daily amount
# that counts as a full day's effort. Mirrors QUESTIONS in pages/diary.html.
PRACTICES = (
    (2, 'Japa malas', 4),
    (3, 'Chanting', 15),
    (4, 'Pranayama', 20),
    (5, 'Asanas', 20),
    (6, 'Meditation', 20),
    (7, 'Gita slokas', 2),
    (8, 'Swadhyay', 20),
    (9, 'Mouna', 1),
    (10, 'Selfless service', 15),
    (12, 'Exercise', 20),
    (17, 'Ishta Devata', 15),
    (18, 'Constructive activity', 30),
)

# Time spent here counts against the score rather than for it.
DISTRACTION = (16, 'Gossip / social media / OTT', 2)

ANSWER_KEY = re.compile(r'^q(\d+)_d(\d+)$')

TIERS = (
    (0, 'Not started', 'No practice logged this week yet.'),
    (25, 'Stirring', 'A beginning. Regularity matters more than volume.'),
    (50, 'Steady', 'Practice is taking hold across the week.'),
    (75, 'Deepening', 'Strong, consistent sadhana.'),
    (90, 'Absorbed', 'Near-complete practice across every discipline.'),
)


def _number(value):
    """First number in a free-text answer, or 0. Tolerates '30 min', '2.5'."""
    if value is None:
        return 0.0
    match = re.search(r'\d+(?:\.\d+)?', str(value))
    return float(match.group()) if match else 0.0


def tier_for(score):
    name, blurb, next_at = TIERS[0][1], TIERS[0][2], None
    for threshold, label, text in TIERS:
        if score >= threshold:
            name, blurb = label, text
        else:
            next_at = threshold
            break
    return {'name': name, 'blurb': blurb, 'next_at': next_at}


def week_score(answers):
    """Score one week's answers 0-100, with a per-practice breakdown.

    Each practice scores the share of its daily target met, averaged over the
    days actually filled in, so a partly-logged week is not punished for the
    days it does not yet cover. Distraction time subtracts from the total.
    """
    answers = answers or {}

    days_filled = set()
    for key, value in answers.items():
        match = ANSWER_KEY.match(key)
        if match and str(value).strip():
            days_filled.add(int(match.group(2)))
    day_count = len(days_filled) or 1

    breakdown = []
    for index, label, target in PRACTICES:
        total = sum(_number(answers.get(f'q{index}_d{d}')) for d in days_filled)
        logged = sum(
            1 for d in days_filled if _number(answers.get(f'q{index}_d{d}')) > 0
        )
        ratio = min(total / (target * day_count), 1.0) if target else 0.0
        breakdown.append({
            'label': label,
            'percent': round(ratio * 100),
            'total': round(total, 1),
            'days': logged,
        })

    base = sum(b['percent'] for b in breakdown) / len(breakdown) if breakdown else 0

    index, label, target = DISTRACTION
    distraction_total = sum(_number(answers.get(f'q{index}_d{d}')) for d in days_filled)
    # Up to a 20 point deduction once distraction time runs past the daily allowance.
    penalty = min(
        max(distraction_total - target * day_count, 0) / (target * day_count) * 20, 20
    ) if target else 0

    score = max(0, round(base - penalty))
    breakdown.sort(key=lambda b: b['percent'])

    return {
        'score': score,
        'tier': tier_for(score),
        'days_logged': len(days_filled),
        'penalty': round(penalty),
        'distraction_hours': round(distraction_total, 1),
        'weakest': breakdown[:3],
        'strongest': list(reversed(breakdown[-3:])),
        'breakdown': breakdown,
    }
