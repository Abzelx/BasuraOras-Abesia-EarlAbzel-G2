from datetime import timedelta

from django.utils import timezone


def now_local():
    """Current time in the project time zone (Asia/Manila). Tests replace this to 'freeze' time."""
    return timezone.localtime()


def next_collection(schedules, today):
    """Return (date, schedule) for the soonest upcoming collection, or None."""
    best = None
    for schedule in schedules:
        days_ahead = (schedule.day_of_week - today.isoweekday()) % 7
        when = today + timedelta(days=days_ahead)
        if best is None or when < best[0]:
            best = (when, schedule)
    return best
