import calendar
from datetime import date, timedelta
import re
import requests


def convert_to_yfinance_symbol(symbol: str) -> str:
    if re.match(r"^A\d{6}$", symbol):
        symbol = symbol[1:]
    r = requests.get(
        f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"},
    )
    yfinance_symbol = sorted(filter(lambda x: x["symbol"].startswith(symbol), r.json()["quotes"]), key=lambda x: len(x["symbol"]))[0]["symbol"]
    return yfinance_symbol


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
