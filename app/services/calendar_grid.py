"""Builds the 12-month day grids behind the habit and reminder heatmaps."""

import calendar
from datetime import datetime


def build_year(year, today, day_payload, future_payload=None):
    """Return 12 months of day cells.

    `day_payload(date_str, date_obj)` supplies the per-day fields. Future days
    are flagged and instead take `future_payload` (a dict of neutral defaults),
    so templates can read the same keys for every cell. Leading `None` entries
    pad each month to its first weekday.
    """
    months = []
    for month in range(1, 13):
        first_weekday, num_days = calendar.monthrange(year, month)
        days = [None] * first_weekday

        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day)
            date_str = date_obj.strftime('%Y-%m-%d')
            cell = {
                'date': date_str,
                'display_date': date_obj.strftime('%a, %b %d, %Y'),
                'day': day,
            }
            if date_obj.date() > today.date():
                cell['future'] = True
                cell.update(future_payload or {})
            else:
                cell.update(day_payload(date_str, date_obj))
            days.append(cell)

        months.append({'name': calendar.month_abbr[month], 'days': days})
    return months
