import cvxpy as cp
from examples.common import capm_expected_return, download_weekly_prices
from datetime import datetime, timedelta
from kstock_account.mirae import MiraeAccount
import numpy as np
import pandas as pd

end_date = datetime.now().date() - timedelta(days=1)
start_date = end_date - timedelta(weeks=52)

account = MiraeAccount.login("", "")
equities = account.get_equity_assets()
equities = sorted(equities, key=lambda x: x.market_value * x.exchange_rate, reverse=True)
equity_prices = pd.concat([download_weekly_prices(equity.symbol, start_date, end_date) for equity in equities], axis=1)
equity_returns = equity_prices.pct_change(fill_method=None).dropna()
equity_covs = equity_returns.cov() * 52

equity_expected_returns = pd.Series(
    [capm_expected_return(equity.symbol, equity.currency[0:2], start_date, end_date) for equity in equities],
    index=[equity.name for equity in equities],
)
print("Expected Return:")
for name, expected_return in equity_expected_returns.items():
    print(f"{expected_return*100:5.2f}% {name}")
print()

portfolio_weights = cp.Variable(len(equities))
portfolio_return = np.array(equity_expected_returns) @ portfolio_weights
portfolio_risk = cp.quad_form(portfolio_weights, equity_covs)
portfolio_constraints = [cp.sum(portfolio_weights) == 1, portfolio_weights >= 0]
if len(equities) >= 5:  # 개별 종목 비중 제한 20%
    portfolio_constraints.append(portfolio_weights <= 0.2)
prob = cp.Problem(cp.Maximize(portfolio_return - portfolio_risk), portfolio_constraints)
prob.solve()

portfolio_weights = pd.Series(portfolio_weights.value, index=[equity.name for equity in equities])
print("Optimal Portfolio:")
for name, weight in portfolio_weights.sort_values(ascending=False).items():
    if weight >= 0.00005:
        print(f"{weight*100:5.2f}% {name}")
