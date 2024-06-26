from datetime import date, timedelta
import pandas as pd
import yfinance as yf


market_symbols = {
    "US": "^GSPC",
    "KR": "^KS11",
    "JP": "^N225",
}
market_risk_premiums = {
    "US": 0.0460,
    "KR": 0.0532,
    "JP": 0.0563,
}  # https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html
market_risk_free_rates = {
    "US": 0.05106,
    "KR": 0.03338,
    "JP": 0.00167,
}  # 국채 1년물 수익률: https://www.investing.com/rates-bonds/world-government-bonds
market_returns_by_countries = {}


def capm_expected_return(asset_symbol: str, country: str, start_date: date, end_date: date) -> float:
    if country not in market_returns_by_countries:
        market_prices = download_weekly_prices(market_symbols[country], start_date, end_date)
        market_returns = market_prices.pct_change(fill_method=None).dropna()
        market_returns_by_countries[country] = market_returns
    asset_prices = download_weekly_prices(asset_symbol, start_date, end_date)
    asset_returns = asset_prices.pct_change(fill_method=None).dropna()
    returns = pd.concat([market_returns_by_countries[country], asset_returns], axis=1).dropna()
    covs = returns.cov() * 52
    beta = covs.iloc[0, 1] / covs.iloc[0, 0]
    expected_return = beta * market_risk_premiums[country] + market_risk_free_rates[country]
    return expected_return


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
