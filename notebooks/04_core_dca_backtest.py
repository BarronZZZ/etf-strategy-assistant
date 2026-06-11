from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================
# 1. 设置路径
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

price_path = PROJECT_ROOT / "data" / "processed" / "all_etf_prices.csv"
processed_dir = PROJECT_ROOT / "data" / "processed"
report_dir = PROJECT_ROOT / "reports"

processed_dir.mkdir(exist_ok=True)
report_dir.mkdir(exist_ok=True)

print("项目路径：", PROJECT_ROOT)
print("价格文件：", price_path)


# =========================
# 2. 读取价格数据
# =========================

prices = pd.read_csv(price_path, index_col=0, parse_dates=True)
prices = prices.sort_index()

print("\n价格数据范围：", prices.index.min(), "到", prices.index.max())
print("价格数据维度：", prices.shape)


# =========================
# 3. 工具函数
# =========================

def get_next_trading_date(index, target_date):
    """
    如果目标日期不是交易日，取之后最近的交易日。
    """
    valid_dates = index[index >= target_date]
    if len(valid_dates) == 0:
        return None
    return valid_dates[0]


def calc_metrics(portfolio_value, risk_free_rate=0.0):
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


def build_lump_sum_portfolio(price_df, weights, initial_capital=50000):
    """
    一次性买入。
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
    result["cash"] = 0.0
    result["invested_amount"] = initial_capital
    result["daily_return"] = result["portfolio_value"].pct_change()

    buy_log = pd.DataFrame({
        "date": [start_date],
        "amount": [initial_capital],
        "type": ["lump_sum"]
    })

    return result, shares, buy_log


def build_40_6_dca_portfolio(price_df, weights, initial_capital=50000):
    """
    首笔40%，剩余60%分6个月买入。
    假设：
    1. 支持 fractional shares
    2. 未投入资金作为现金，不计利息
    3. 每次买入都按目标权重分配
    4. 不考虑税费和交易费
    """
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices = price_df[tickers].dropna().copy()

    start_date = sub_prices.index[0]

    schedule = []
    schedule.append({
        "target_date": start_date,
        "amount": initial_capital * 0.40,
        "type": "initial_40pct"
    })

    monthly_amount = initial_capital * 0.60 / 6

    for i in range(1, 7):
        target_date = start_date + pd.DateOffset(months=i)
        schedule.append({
            "target_date": target_date,
            "amount": monthly_amount,
            "type": f"month_{i}_dca"
        })

    shares = pd.Series(0.0, index=tickers)
    cash = initial_capital

    records = []
    buy_logs = []

    schedule_idx = 0

    for current_date in sub_prices.index:
        while schedule_idx < len(schedule):
            target_date = schedule[schedule_idx]["target_date"]
            trade_date = get_next_trading_date(sub_prices.index, target_date)

            if trade_date is None:
                break

            if current_date >= trade_date:
                buy_amount = schedule[schedule_idx]["amount"]
                prices_today = sub_prices.loc[current_date]

                allocation = buy_amount * w
                new_shares = allocation / prices_today

                shares += new_shares
                cash -= buy_amount

                buy_logs.append({
                    "target_date": target_date,
                    "trade_date": current_date,
                    "amount": buy_amount,
                    "type": schedule[schedule_idx]["type"],
                    "cash_after_trade": cash
                })

                schedule_idx += 1
            else:
                break

        asset_value = (sub_prices.loc[current_date] * shares).sum()
        total_value = asset_value + cash
        invested_amount = initial_capital - cash

        records.append({
            "date": current_date,
            "asset_value": asset_value,
            "cash": cash,
            "portfolio_value": total_value,
            "invested_amount": invested_amount
        })

    result = pd.DataFrame(records).set_index("date")
    result["daily_return"] = result["portfolio_value"].pct_change()

    buy_log = pd.DataFrame(buy_logs)

    return result, shares, buy_log


# =========================
# 4. 定义组合
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

real_lump, real_lump_shares, real_lump_log = build_lump_sum_portfolio(
    prices,
    core_real_weights,
    initial_capital
)

real_dca, real_dca_shares, real_dca_log = build_40_6_dca_portfolio(
    prices,
    core_real_weights,
    initial_capital
)

proxy_lump, proxy_lump_shares, proxy_lump_log = build_lump_sum_portfolio(
    prices,
    core_proxy_weights,
    initial_capital
)

proxy_dca, proxy_dca_shares, proxy_dca_log = build_40_6_dca_portfolio(
    prices,
    core_proxy_weights,
    initial_capital
)


print("\n===== 真实版 DCA 买入日志 =====")
print(real_dca_log)

print("\n===== 长历史代理版 DCA 买入日志 =====")
print(proxy_dca_log)


# =========================
# 6. 计算指标
# =========================

metrics = {
    "REAL_LumpSum_SGOV_2020": calc_metrics(real_lump["portfolio_value"]),
    "REAL_40_6_DCA_SGOV_2020": calc_metrics(real_dca["portfolio_value"]),
    "PROXY_LumpSum_BIL_2015": calc_metrics(proxy_lump["portfolio_value"]),
    "PROXY_40_6_DCA_BIL_2015": calc_metrics(proxy_dca["portfolio_value"])
}

metrics_df = pd.DataFrame(metrics).T

metrics_path = processed_dir / "core_dca_metrics.csv"
metrics_df.to_csv(metrics_path)

print("\n===== 一次性买入 vs 40%+6个月分批买入 =====")
print(metrics_df)

print("\n指标已保存：", metrics_path)


# =========================
# 7. 保存买入日志
# =========================

real_dca_log_path = processed_dir / "real_sgov_dca_buy_log.csv"
proxy_dca_log_path = processed_dir / "proxy_bil_dca_buy_log.csv"

real_dca_log.to_csv(real_dca_log_path, index=False)
proxy_dca_log.to_csv(proxy_dca_log_path, index=False)

print("\n真实版买入日志已保存：", real_dca_log_path)
print("代理版买入日志已保存：", proxy_dca_log_path)


# =========================
# 8. 保存净值曲线
# =========================

equity_curves = pd.DataFrame({
    "REAL_LumpSum_SGOV_2020": real_lump["portfolio_value"],
    "REAL_40_6_DCA_SGOV_2020": real_dca["portfolio_value"],
    "PROXY_LumpSum_BIL_2015": proxy_lump["portfolio_value"],
    "PROXY_40_6_DCA_BIL_2015": proxy_dca["portfolio_value"]
})

equity_path = processed_dir / "core_dca_equity_curves.csv"
equity_curves.to_csv(equity_path)

plt.figure(figsize=(12, 6))

for col in equity_curves.columns:
    plt.plot(equity_curves.index, equity_curves[col], label=col)

plt.title("Lump Sum vs 40% Initial + 6-Month DCA")
plt.xlabel("Date")
plt.ylabel("Portfolio Value")
plt.legend()
plt.grid(True)
plt.tight_layout()

equity_chart = report_dir / "core_dca_equity_curves.png"
plt.savefig(equity_chart, dpi=150)
plt.show()

print("净值曲线图已保存：", equity_chart)


# =========================
# 9. 保存回撤曲线
# =========================

drawdowns = pd.DataFrame({
    "REAL_LumpSum_SGOV_2020": calc_drawdown(real_lump["portfolio_value"]),
    "REAL_40_6_DCA_SGOV_2020": calc_drawdown(real_dca["portfolio_value"]),
    "PROXY_LumpSum_BIL_2015": calc_drawdown(proxy_lump["portfolio_value"]),
    "PROXY_40_6_DCA_BIL_2015": calc_drawdown(proxy_dca["portfolio_value"])
})

drawdown_path = processed_dir / "core_dca_drawdowns.csv"
drawdowns.to_csv(drawdown_path)

plt.figure(figsize=(12, 6))

for col in drawdowns.columns:
    plt.plot(drawdowns.index, drawdowns[col], label=col)

plt.title("Drawdown: Lump Sum vs 40% Initial + 6-Month DCA")
plt.xlabel("Date")
plt.ylabel("Drawdown")
plt.legend()
plt.grid(True)
plt.tight_layout()

drawdown_chart = report_dir / "core_dca_drawdowns.png"
plt.savefig(drawdown_chart, dpi=150)
plt.show()

print("回撤曲线图已保存：", drawdown_chart)


# =========================
# 10. 输出最终提示
# =========================

print("\n===== 说明 =====")
print("1. REAL 版本使用 VTI/VEA/VWO/SGOV，从 SGOV 有数据的时间开始。")
print("2. PROXY 版本使用 VTI/VEA/VWO/BIL，可以覆盖更长历史。")
print("3. 40%+6个月分批买入假设未投入现金不计利息。")
print("4. 本回测不含交易费、税费和滑点。")

print("\n第 11 步完成：40%首笔 + 6个月分批建仓回测运行成功。")
