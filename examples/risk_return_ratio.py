from datetime import date, datetime
import math
import numpy as np
import pandas as pd
from kstock_account.mirae import MiraeAccount
from examples.common import download_weekly_prices

start_date = date(2024, 1, 1)
end_date = datetime.now().date()

account = MiraeAccount.login("", "")
account_history = account.get_history(start_date, end_date)
portfolio_returns = pd.Series(
    [record.pnl_percent for record in account_history],
    index=[record.end_date for record in account_history],
)

market_prices = download_weekly_prices("VT", start_date, end_date)
market_returns = market_prices.pct_change(fill_method=None).dropna()

portfolio_period_return = np.cumprod([1 + n for n in portfolio_returns.values])[-1] - 1
portfolio_annualized_return = (1 + portfolio_period_return) ** (52 / len(portfolio_returns)) - 1

market_period_return = np.cumprod([1 + n for n in market_returns.values])[-1] - 1
market_annualized_return = (1 + market_period_return) ** (52 / len(market_returns)) - 1
risk_free_rate = 0.053
print(f"portfolio annualized return: {portfolio_annualized_return*100:.2f}%, market annualized return: {market_annualized_return*100:.2f}%")

returns = pd.concat([market_returns, portfolio_returns], axis=1).dropna()
covs = returns.cov() * 52
portfolio_beta = covs.iloc[0, 1] / covs.iloc[0, 0]
print(f"portfolio beta: {portfolio_beta:.2f}")
portfolio_jensens_alpha = portfolio_annualized_return - (portfolio_beta * (market_annualized_return - risk_free_rate) + risk_free_rate)
print(f"portfolio jensen's alpha: {portfolio_jensens_alpha:.2f}")

portfolio_sharpe_ratio = (portfolio_annualized_return - risk_free_rate) / math.sqrt(covs.iloc[1, 1])
market_sharpe_ratio = (market_annualized_return - risk_free_rate) / math.sqrt(covs.iloc[0, 0])
print(f"portfolio sharpe ratio: {portfolio_sharpe_ratio:.2f}, market sharpe ratio: {market_sharpe_ratio:.2f}")

portfolio_treynor_ratio = (portfolio_annualized_return - risk_free_rate) / portfolio_beta
market_treynor_ratio = market_annualized_return - risk_free_rate
print(f"portfolio treynor ratio: {portfolio_treynor_ratio:.2f}, market treynor ratio: {market_treynor_ratio:.2f}")
