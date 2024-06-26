from datetime import date, timedelta
import pandas as pd
import yfinance as yf


def download_weekly_prices(symbol: str, start_date: date, end_date: date):
    prices = yf.download(symbol, start=start_date, end=end_date)["Adj Close"].dropna().resample("W-FRI").last()
    prices = pd.Series(
        prices.values,
        index=[last_date_of_week(pd.to_datetime(ts).date()) for ts in prices.index.values[:-1]] + [end_date],
        name=symbol,
    )
    return prices


def last_date_of_week(base_date: date):
    return base_date + timedelta(days=6 - base_date.weekday())
