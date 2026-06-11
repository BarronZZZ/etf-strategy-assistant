from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================
# 1. 设置项目路径
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

price_path = PROJECT_ROOT / "data" / "processed" / "all_etf_prices.csv"
report_dir = PROJECT_ROOT / "reports"
processed_dir = PROJECT_ROOT / "data" / "processed"

report_dir.mkdir(exist_ok=True)
processed_dir.mkdir(exist_ok=True)

print("项目路径：", PROJECT_ROOT)
print("价格文件：", price_path)


# =========================
# 2. 读取价格数据
# =========================

prices = pd.read_csv(price_path, index_col=0, parse_dates=True)
prices = prices.sort_index()

print("\n价格数据维度：", prices.shape)
print("\n价格日期范围：", prices.index.min(), "到", prices.index.max())


# =========================
# 3. 定义工具函数
# =========================

def build_lump_sum_portfolio(price_df, weights, initial_capital=50000):
    """
    一次性买入并长期持有。
    假设支持 fractional shares。
    """
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices = price_df[tickers].dropna().copy()

    start_date = sub_prices.index[0]
    start_prices = sub_prices.iloc[0]

    allocation = initial_capital * w
    shares = allocation / start_prices

    portfolio_value = sub_prices.mul(shares, axis=1).sum(axis=1)

    result = pd.DataFrame(index=sub_prices.index)
    result["portfolio_value"] = portfolio_value
    result["daily_return"] = result["portfolio_value"].pct_change()

    return result, shares, start_date


def build_buy_hold(price_df, ticker, initial_capital=50000):
    """
    单一 ETF 买入持有基准。
    """
    s = price_df[ticker].dropna().copy()
    shares = initial_capital / s.iloc[0]

    result = pd.DataFrame(index=s.index)
    result["portfolio_value"] = s * shares
    result["daily_return"] = result["portfolio_value"].pct_change()

    return result


def calc_metrics(portfolio_value, risk_free_rate=0.0):
    """
    计算常见回测指标。
    """
    pv = portfolio_value.dropna()
    returns = pv.pct_change().dropna()

    total_return = pv.iloc[-1] / pv.iloc[0] - 1

    days = (pv.index[-1] - pv.index[0]).days
    years = days / 365.25

    cagr = (pv.iloc[-1] / pv.iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan

    running_max = pv.cummax()
    drawdown = pv / running_max - 1
    max_drawdown = drawdown.min()

    annualized_vol = returns.std() * np.sqrt(252)

    sharpe = np.nan
    if annualized_vol != 0:
        sharpe = (cagr - risk_free_rate) / annualized_vol

    return {
        "start_date": pv.index[0],
        "end_date": pv.index[-1],
        "start_value": pv.iloc[0],
        "end_value": pv.iloc[-1],
        "total_return": total_return,
        "CAGR": cagr,
        "max_drawdown": max_drawdown,
        "annualized_vol": annualized_vol,
        "sharpe_simple": sharpe,
        "years": years
    }


def calc_drawdown(portfolio_value):
    pv = portfolio_value.dropna()
    return pv / pv.cummax() - 1


# =========================
# 4. 定义你的长期核心组合
# =========================

initial_capital = 50000

core_real_weights = {
    "VTI": 0.64,
    "VEA": 0.20,
    "VWO": 0.10,
    "SGOV": 0.06
}

core_proxy_weights = {
    "VTI": 0.64,
    "VEA": 0.20,
    "VWO": 0.10,
    "BIL": 0.06
}

print("\n真实版组合：", core_real_weights)
print("长历史代理版组合：", core_proxy_weights)


# =========================
# 5. 运行回测
# =========================

real_portfolio, real_shares, real_start = build_lump_sum_portfolio(
    prices,
    core_real_weights,
    initial_capital
)

proxy_portfolio, proxy_shares, proxy_start = build_lump_sum_portfolio(
    prices,
    core_proxy_weights,
    initial_capital
)

spy_bh = build_buy_hold(prices, "SPY", initial_capital)
vti_bh = build_buy_hold(prices, "VTI", initial_capital)

print("\n真实版组合开始日期：", real_start)
print("真实版买入股数：")
print(real_shares)

print("\n长历史代理版组合开始日期：", proxy_start)
print("长历史代理版买入股数：")
print(proxy_shares)


# =========================
# 6. 计算指标
# =========================

metrics = {}

metrics["Core_REAL_SGOV_2020"] = calc_metrics(real_portfolio["portfolio_value"])
metrics["Core_PROXY_BIL_2015"] = calc_metrics(proxy_portfolio["portfolio_value"])
metrics["SPY_BuyHold_2015"] = calc_metrics(spy_bh["portfolio_value"])
metrics["VTI_BuyHold_2015"] = calc_metrics(vti_bh["portfolio_value"])

metrics_df = pd.DataFrame(metrics).T

metrics_path = processed_dir / "core_lump_sum_metrics.csv"
metrics_df.to_csv(metrics_path)

print("\n===== 一次性买入回测指标 =====")
print(metrics_df)

print("\n指标已保存：", metrics_path)


# =========================
# 7. 对齐并画净值曲线
# =========================

equity_curves = pd.DataFrame({
    "Core_REAL_SGOV_2020": real_portfolio["portfolio_value"],
    "Core_PROXY_BIL_2015": proxy_portfolio["portfolio_value"],
    "SPY_BuyHold_2015": spy_bh["portfolio_value"],
    "VTI_BuyHold_2015": vti_bh["portfolio_value"]
})

equity_path = processed_dir / "core_lump_sum_equity_curves.csv"
equity_curves.to_csv(equity_path)

plt.figure(figsize=(12, 6))

for col in equity_curves.columns:
    plt.plot(equity_curves.index, equity_curves[col], label=col)

plt.title("Core Portfolio Lump Sum Backtest")
plt.xlabel("Date")
plt.ylabel("Portfolio Value")
plt.legend()
plt.grid(True)
plt.tight_layout()

equity_chart = report_dir / "core_lump_sum_equity_curves.png"
plt.savefig(equity_chart, dpi=150)
plt.show()

print("净值曲线图已保存：", equity_chart)


# =========================
# 8. 画最大回撤曲线
# =========================

drawdowns = pd.DataFrame({
    "Core_REAL_SGOV_2020": calc_drawdown(real_portfolio["portfolio_value"]),
    "Core_PROXY_BIL_2015": calc_drawdown(proxy_portfolio["portfolio_value"]),
    "SPY_BuyHold_2015": calc_drawdown(spy_bh["portfolio_value"]),
    "VTI_BuyHold_2015": calc_drawdown(vti_bh["portfolio_value"])
})

drawdown_path = processed_dir / "core_lump_sum_drawdowns.csv"
drawdowns.to_csv(drawdown_path)

plt.figure(figsize=(12, 6))

for col in drawdowns.columns:
    plt.plot(drawdowns.index, drawdowns[col], label=col)

plt.title("Core Portfolio Drawdown")
plt.xlabel("Date")
plt.ylabel("Drawdown")
plt.legend()
plt.grid(True)
plt.tight_layout()

drawdown_chart = report_dir / "core_lump_sum_drawdowns.png"
plt.savefig(drawdown_chart, dpi=150)
plt.show()

print("回撤曲线图已保存：", drawdown_chart)


# =========================
# 9. 输出最终结果摘要
# =========================

print("\n===== 重点解释 =====")
print("1. Core_REAL_SGOV_2020 是真实版长期配置，但只能从 SGOV 有数据的日期开始。")
print("2. Core_PROXY_BIL_2015 用 BIL 替代 SGOV，可以观察更长历史。")
print("3. SPY_BuyHold_2015 和 VTI_BuyHold_2015 是基准。")
print("4. 这一版是假设一次性投入 50000 美元，并长期持有，不再平衡。")

print("\n第 10 步完成：长期核心组合一次性买入回测运行成功。")
