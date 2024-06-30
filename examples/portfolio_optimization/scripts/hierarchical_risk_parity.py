from datetime import datetime, timedelta
from kstock_account.mirae import MiraeAccount
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage, to_tree
from .common import download_weekly_prices


def cluster_variance(covs, cluster):
    cov_slice = covs.loc[cluster, cluster]
    weights = 1 / np.diag(cov_slice)  # Inverse variance weights
    weights /= weights.sum()
    return weights.T @ cov_slice @ weights


end_date = datetime.now().date() - timedelta(days=1)
start_date = end_date - timedelta(weeks=52)

account = MiraeAccount.login("", "")
equities = sorted(
    account.get_equity_assets(),
    key=lambda equity: equity.market_value * equity.exchange_rate,
    reverse=True,
)

equity_names = {equity.symbol: equity.name for equity in equities}

prices = pd.concat([download_weekly_prices(equity.symbol, start_date, end_date) for equity in equities], axis=1)
returns = prices.pct_change(fill_method=None).dropna()

corrs = returns.corr()
corr_distances = ((1 - corrs) / 2.0) ** 0.5
Z = linkage(corr_distances, "ward")
sort_ix = to_tree(Z).pre_order()  # quasi_diag
ordered_symbols = corrs.index[sort_ix].tolist()

dn = dendrogram(Z, labels=returns.columns)
plt.show()

covs = returns.cov() * 52
weights = pd.Series(1.0, index=ordered_symbols)
clusters = [ordered_symbols]
while len(clusters) > 0:
    clusters = [
        cluster[i:j]
        for cluster in clusters
        for i, j in ((0, len(cluster) // 2), (len(cluster) // 2, len(cluster)))
        if len(cluster) > 1
    ]  # bi-section
    for i in range(0, len(clusters), 2):
        left_cluster = clusters[i]
        right_cluster = clusters[i + 1]
        left_cluster_variance = cluster_variance(covs, left_cluster)
        right_cluster_variance = cluster_variance(covs, right_cluster)
        alpha = 1 - left_cluster_variance / (left_cluster_variance + right_cluster_variance)
        weights.loc[left_cluster] *= alpha  # weight 1
        weights.loc[right_cluster] *= 1 - alpha  # weight 2

print("Optimal Portfolio:")
for symbol, weight in weights.sort_values(ascending=False).items():
    if weight >= 0.00005:
        print(f"{weight*100:5.2f}% {equity_names[symbol]}")
