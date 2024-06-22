import calendar
from datetime import date, timedelta


def daterange(start_date: date, end_date: date):
    while start_date < end_date:
        yield start_date
        start_date += timedelta(days=1)
    yield end_date


def weekrange(start_date: date, end_date: date):
    s = start_date
    e = start_date + timedelta(days=6 - start_date.weekday())
    while e <= end_date:
        yield (s, e)
        s = e + timedelta(days=1)
        e = s + timedelta(days=6)
    yield (s, end_date)


def monthrange(start_date: date, end_date: date):
    start_date = _last_date_of_month(start_date.year, start_date.month)
    while start_date < end_date:
        yield start_date
        year = start_date.year
        month = start_date.month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        start_date = _last_date_of_month(year, month)
    yield end_date


def _last_date_of_month(year: int, month: int):
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, last_day)
