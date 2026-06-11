from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================
# 1. 路径设置
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

    return result


def build_fixed_40_6_dca(price_df, weights, initial_capital=50000):
    """
    固定规则：首笔40%，之后每月5000，6个月买完。
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
        schedule.append({
            "target_date": start_date + pd.DateOffset(months=i),
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
            trade_date = get_next_trading_date(sub_prices.index, schedule[schedule_idx]["target_date"])

            if trade_date is None:
                break

            if current_date >= trade_date:
                buy_amount = min(schedule[schedule_idx]["amount"], cash)
                allocation = buy_amount * w
                new_shares = allocation / sub_prices.loc[current_date]

                shares += new_shares
                cash -= buy_amount

                buy_logs.append({
                    "target_date": schedule[schedule_idx]["target_date"],
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

        records.append({
            "date": current_date,
            "asset_value": asset_value,
            "cash": cash,
            "portfolio_value": total_value,
            "invested_amount": initial_capital - cash
        })

    result = pd.DataFrame(records).set_index("date")
    result["daily_return"] = result["portfolio_value"].pct_change()

    buy_log = pd.DataFrame(buy_logs)

    return result, buy_log


def build_smart_40_6_dca(price_df, weights, initial_capital=50000, signal_ticker="VTI"):
    """
    智能分批规则：
    1. 首笔40%
    2. 默认每月买5000
    3. 如果 VTI 从近252日高点回撤超过10%，提前买下一期5000
    4. 如果回撤超过15%，提前买两期10000
    5. 如果回撤超过25%，投入所有剩余现金
    """
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices = price_df[tickers].dropna().copy()
    signal_price = price_df.loc[sub_prices.index, signal_ticker].dropna()

    common_index = sub_prices.index.intersection(signal_price.index)
    sub_prices = sub_prices.loc[common_index]
    signal_price = signal_price.loc[common_index]

    start_date = sub_prices.index[0]

    monthly_amount = initial_capital * 0.60 / 6

    monthly_dates = []
    for i in range(1, 7):
        target_date = start_date + pd.DateOffset(months=i)
        trade_date = get_next_trading_date(sub_prices.index, target_date)
        if trade_date is not None:
            monthly_dates.append(trade_date)

    shares = pd.Series(0.0, index=tickers)
    cash = initial_capital
    remaining_monthly_tranches = 6

    records = []
    buy_logs = []

    # 首笔 40%
    first_trade_date = start_date
    first_amount = initial_capital * 0.40
    allocation = first_amount * w
    shares += allocation / sub_prices.loc[first_trade_date]
    cash -= first_amount

    buy_logs.append({
        "trade_date": first_trade_date,
        "amount": first_amount,
        "type": "initial_40pct",
        "vti_drawdown_252d": np.nan,
        "remaining_tranches_after_trade": remaining_monthly_tranches,
        "cash_after_trade": cash
    })

    executed_monthly_dates = set()

    rolling_high = signal_price.rolling(252, min_periods=20).max()
    vti_drawdown = signal_price / rolling_high - 1

    for current_date in sub_prices.index:
        if current_date == first_trade_date:
            asset_value = (sub_prices.loc[current_date] * shares).sum()
            records.append({
                "date": current_date,
                "asset_value": asset_value,
                "cash": cash,
                "portfolio_value": asset_value + cash,
                "invested_amount": initial_capital - cash,
                "vti_drawdown_252d": vti_drawdown.loc[current_date]
            })
            continue

        dd = vti_drawdown.loc[current_date]

        buy_amount = 0
        buy_type = None

        # 先判断是否触发大跌加速
        if remaining_monthly_tranches > 0 and cash > 0:
            if dd <= -0.25:
                buy_amount = cash
                buy_type = "smart_all_in_dd_25pct"
            elif dd <= -0.15:
                n = min(2, remaining_monthly_tranches)
                buy_amount = min(monthly_amount * n, cash)
                buy_type = "smart_2_tranches_dd_15pct"
            elif dd <= -0.10:
                n = min(1, remaining_monthly_tranches)
                buy_amount = min(monthly_amount * n, cash)
                buy_type = "smart_1_tranche_dd_10pct"

        # 如果没有触发智能加速，再执行正常月度买入
        if buy_amount == 0 and remaining_monthly_tranches > 0 and cash > 0:
            due_monthly_dates = [d for d in monthly_dates if d <= current_date and d not in executed_monthly_dates]
            if len(due_monthly_dates) > 0:
                buy_amount = min(monthly_amount, cash)
                buy_type = "regular_monthly_dca"
                executed_monthly_dates.add(due_monthly_dates[0])

        # 执行买入
        if buy_amount > 0:
            allocation = buy_amount * w
            shares += allocation / sub_prices.loc[current_date]
            cash -= buy_amount

            used_tranches = int(round(buy_amount / monthly_amount))
            if buy_type == "smart_all_in_dd_25pct":
                used_tranches = remaining_monthly_tranches

            remaining_monthly_tranches = max(0, remaining_monthly_tranches - used_tranches)

            buy_logs.append({
                "trade_date": current_date,
                "amount": buy_amount,
                "type": buy_type,
                "vti_drawdown_252d": dd,
                "remaining_tranches_after_trade": remaining_monthly_tranches,
                "cash_after_trade": cash
            })

        asset_value = (sub_prices.loc[current_date] * shares).sum()
        total_value = asset_value + cash

        records.append({
            "date": current_date,
            "asset_value": asset_value,
            "cash": cash,
            "portfolio_value": total_value,
            "invested_amount": initial_capital - cash,
            "vti_drawdown_252d": dd
        })

    result = pd.DataFrame(records).set_index("date")
    result["daily_return"] = result["portfolio_value"].pct_change()

    buy_log = pd.DataFrame(buy_logs)

    return result, buy_log


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


# =========================
# 5. 回测
# =========================

real_lump = build_lump_sum_portfolio(prices, core_real_weights, initial_capital)
real_fixed_dca, real_fixed_log = build_fixed_40_6_dca(prices, core_real_weights, initial_capital)
real_smart_dca, real_smart_log = build_smart_40_6_dca(prices, core_real_weights, initial_capital, signal_ticker="VTI")

proxy_lump = build_lump_sum_portfolio(prices, core_proxy_weights, initial_capital)
proxy_fixed_dca, proxy_fixed_log = build_fixed_40_6_dca(prices, core_proxy_weights, initial_capital)
proxy_smart_dca, proxy_smart_log = build_smart_40_6_dca(prices, core_proxy_weights, initial_capital, signal_ticker="VTI")


print("\n===== 真实版 Smart DCA 买入日志 =====")
print(real_smart_log)

print("\n===== 长历史代理版 Smart DCA 买入日志 =====")
print(proxy_smart_log)


# =========================
# 6. 计算指标
# =========================

metrics = {
    "REAL_LumpSum_SGOV_2020": calc_metrics(real_lump["portfolio_value"]),
    "REAL_Fixed_40_6_DCA_SGOV_2020": calc_metrics(real_fixed_dca["portfolio_value"]),
    "REAL_Smart_DCA_SGOV_2020": calc_metrics(real_smart_dca["portfolio_value"]),
    "PROXY_LumpSum_BIL_2015": calc_metrics(proxy_lump["portfolio_value"]),
    "PROXY_Fixed_40_6_DCA_BIL_2015": calc_metrics(proxy_fixed_dca["portfolio_value"]),
    "PROXY_Smart_DCA_BIL_2015": calc_metrics(proxy_smart_dca["portfolio_value"])
}

metrics_df = pd.DataFrame(metrics).T

metrics_path = processed_dir / "core_smart_dca_metrics.csv"
metrics_df.to_csv(metrics_path)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 240)
pd.set_option("display.float_format", "{:.6f}".format)

print("\n===== Lump Sum vs Fixed DCA vs Smart DCA =====")
print(metrics_df)

print("\n指标已保存：", metrics_path)


# =========================
# 7. 保存买入日志
# =========================

real_smart_log_path = processed_dir / "real_sgov_smart_dca_buy_log.csv"
proxy_smart_log_path = processed_dir / "proxy_bil_smart_dca_buy_log.csv"

real_smart_log.to_csv(real_smart_log_path, index=False)
proxy_smart_log.to_csv(proxy_smart_log_path, index=False)

print("\n真实版 Smart DCA 买入日志已保存：", real_smart_log_path)
print("代理版 Smart DCA 买入日志已保存：", proxy_smart_log_path)


# =========================
# 8. 保存净值曲线
# =========================

equity_curves = pd.DataFrame({
    "REAL_LumpSum": real_lump["portfolio_value"],
    "REAL_Fixed_DCA": real_fixed_dca["portfolio_value"],
    "REAL_Smart_DCA": real_smart_dca["portfolio_value"],
    "PROXY_LumpSum": proxy_lump["portfolio_value"],
    "PROXY_Fixed_DCA": proxy_fixed_dca["portfolio_value"],
    "PROXY_Smart_DCA": proxy_smart_dca["portfolio_value"]
})

equity_path = processed_dir / "core_smart_dca_equity_curves.csv"
equity_curves.to_csv(equity_path)

plt.figure(figsize=(12, 6))

for col in equity_curves.columns:
    plt.plot(equity_curves.index, equity_curves[col], label=col)

plt.title("Lump Sum vs Fixed DCA vs Smart DCA")
plt.xlabel("Date")
plt.ylabel("Portfolio Value")
plt.legend()
plt.grid(True)
plt.tight_layout()

equity_chart = report_dir / "core_smart_dca_equity_curves.png"
plt.savefig(equity_chart, dpi=150)
plt.show()

print("净值曲线图已保存：", equity_chart)


# =========================
# 9. 保存回撤曲线
# =========================

drawdowns = pd.DataFrame({
    "REAL_LumpSum": calc_drawdown(real_lump["portfolio_value"]),
    "REAL_Fixed_DCA": calc_drawdown(real_fixed_dca["portfolio_value"]),
    "REAL_Smart_DCA": calc_drawdown(real_smart_dca["portfolio_value"]),
    "PROXY_LumpSum": calc_drawdown(proxy_lump["portfolio_value"]),
    "PROXY_Fixed_DCA": calc_drawdown(proxy_fixed_dca["portfolio_value"]),
    "PROXY_Smart_DCA": calc_drawdown(proxy_smart_dca["portfolio_value"])
})

drawdown_path = processed_dir / "core_smart_dca_drawdowns.csv"
drawdowns.to_csv(drawdown_path)

plt.figure(figsize=(12, 6))

for col in drawdowns.columns:
    plt.plot(drawdowns.index, drawdowns[col], label=col)

plt.title("Drawdown: Lump Sum vs Fixed DCA vs Smart DCA")
plt.xlabel("Date")
plt.ylabel("Drawdown")
plt.legend()
plt.grid(True)
plt.tight_layout()

drawdown_chart = report_dir / "core_smart_dca_drawdowns.png"
plt.savefig(drawdown_chart, dpi=150)
plt.show()

print("回撤曲线图已保存：", drawdown_chart)


# =========================
# 10. 说明
# =========================

print("\n===== 说明 =====")
print("1. Fixed DCA = 首笔40%，剩余6个月固定买入。")
print("2. Smart DCA = 如果VTI从近252日高点回撤超过10%/15%/25%，提前使用未来买入额度。")
print("3. Smart DCA 不增加总投入，只改变买入节奏。")
print("4. 本回测不含交易费、税费和滑点。")

print("\n第 12 步完成：智能分批建仓回测运行成功。")
