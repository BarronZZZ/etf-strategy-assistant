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


def prepare_prices(price_df, weights, start_date):
    tickers = list(weights.keys())
    sub_prices = price_df[tickers].dropna().copy()
    start_date = pd.Timestamp(start_date)
    actual_start = get_next_trading_date(sub_prices.index, start_date)

    if actual_start is None:
        raise ValueError(f"找不到开始日期之后的交易日：{start_date}")

    sub_prices = sub_prices.loc[actual_start:].copy()
    return sub_prices, actual_start


def build_lump_sum_portfolio(price_df, weights, start_date, initial_capital=50000):
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices, actual_start = prepare_prices(price_df, weights, start_date)

    start_prices = sub_prices.iloc[0]
    allocation = initial_capital * w
    shares = allocation / start_prices

    portfolio_value = sub_prices.mul(shares, axis=1).sum(axis=1)

    result = pd.DataFrame(index=sub_prices.index)
    result["portfolio_value"] = portfolio_value
    result["cash"] = 0.0
    result["invested_amount"] = initial_capital
    result["daily_return"] = result["portfolio_value"].pct_change()

    buy_log = pd.DataFrame([{
        "trade_date": actual_start,
        "amount": initial_capital,
        "type": "lump_sum",
        "cash_after_trade": 0.0
    }])

    return result, buy_log


def build_fixed_40_6_dca(price_df, weights, start_date, initial_capital=50000):
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices, actual_start = prepare_prices(price_df, weights, start_date)

    schedule = []
    schedule.append({
        "target_date": actual_start,
        "amount": initial_capital * 0.40,
        "type": "initial_40pct"
    })

    monthly_amount = initial_capital * 0.60 / 6

    for i in range(1, 7):
        schedule.append({
            "target_date": actual_start + pd.DateOffset(months=i),
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
                shares += allocation / sub_prices.loc[current_date]
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


def build_smart_40_6_dca(price_df, weights, start_date, initial_capital=50000, signal_ticker="VTI"):
    tickers = list(weights.keys())
    w = pd.Series(weights)

    sub_prices, actual_start = prepare_prices(price_df, weights, start_date)

    signal_price = price_df[signal_ticker].dropna()
    signal_price = signal_price.loc[signal_price.index >= actual_start]

    common_index = sub_prices.index.intersection(signal_price.index)
    sub_prices = sub_prices.loc[common_index]
    signal_price = signal_price.loc[common_index]

    monthly_amount = initial_capital * 0.60 / 6

    monthly_dates = []
    for i in range(1, 7):
        target_date = actual_start + pd.DateOffset(months=i)
        trade_date = get_next_trading_date(sub_prices.index, target_date)
        if trade_date is not None:
            monthly_dates.append(trade_date)

    shares = pd.Series(0.0, index=tickers)
    cash = initial_capital
    remaining_monthly_tranches = 6

    records = []
    buy_logs = []

    # 首笔 40%
    first_trade_date = actual_start
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

        if buy_amount == 0 and remaining_monthly_tranches > 0 and cash > 0:
            due_monthly_dates = [d for d in monthly_dates if d <= current_date and d not in executed_monthly_dates]
            if len(due_monthly_dates) > 0:
                buy_amount = min(monthly_amount, cash)
                buy_type = "regular_monthly_dca"
                executed_monthly_dates.add(due_monthly_dates[0])

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
# 4. 设置测试日期和组合
# =========================

initial_capital = 50000

core_real_weights = {
    "VTI": 0.64,
    "VEA": 0.20,
    "VWO": 0.10,
    "SGOV": 0.06
}

stress_start_dates = [
    "2021-09-01",
    "2021-11-01",
    "2022-01-03",
    "2022-03-01",
    "2022-06-01"
]

all_metrics = []
all_buy_logs = []


# =========================
# 5. 循环回测压力期建仓
# =========================

for start_date in stress_start_dates:
    print("\n" + "=" * 80)
    print("测试建仓开始日期：", start_date)
    print("=" * 80)

    lump, lump_log = build_lump_sum_portfolio(
        prices,
        core_real_weights,
        start_date,
        initial_capital
    )

    fixed, fixed_log = build_fixed_40_6_dca(
        prices,
        core_real_weights,
        start_date,
        initial_capital
    )

    smart, smart_log = build_smart_40_6_dca(
        prices,
        core_real_weights,
        start_date,
        initial_capital,
        signal_ticker="VTI"
    )

    metrics = {
        f"{start_date}_LumpSum": calc_metrics(lump["portfolio_value"]),
        f"{start_date}_FixedDCA": calc_metrics(fixed["portfolio_value"]),
        f"{start_date}_SmartDCA": calc_metrics(smart["portfolio_value"])
    }

    metrics_df = pd.DataFrame(metrics).T
    metrics_df["test_start_date"] = start_date

    all_metrics.append(metrics_df)

    print("\nSmart DCA 买入日志：")
    print(smart_log)

    smart_log_copy = smart_log.copy()
    smart_log_copy["test_start_date"] = start_date
    all_buy_logs.append(smart_log_copy)

    equity_curves = pd.DataFrame({
        "LumpSum": lump["portfolio_value"],
        "FixedDCA": fixed["portfolio_value"],
        "SmartDCA": smart["portfolio_value"]
    })

    chart_path = report_dir / f"stress_entry_{start_date}_equity.png"

    plt.figure(figsize=(12, 6))
    for col in equity_curves.columns:
        plt.plot(equity_curves.index, equity_curves[col], label=col)

    plt.title(f"Stress Entry Backtest Starting {start_date}")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()

    print("净值图已保存：", chart_path)


# =========================
# 6. 保存汇总结果
# =========================

final_metrics = pd.concat(all_metrics)
final_metrics_path = processed_dir / "stress_entry_metrics.csv"
final_metrics.to_csv(final_metrics_path)

final_buy_logs = pd.concat(all_buy_logs, ignore_index=True)
final_buy_logs_path = processed_dir / "stress_entry_smart_dca_buy_logs.csv"
final_buy_logs.to_csv(final_buy_logs_path, index=False)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 240)
pd.set_option("display.float_format", "{:.6f}".format)

print("\n" + "=" * 80)
print("===== 压力期建仓测试汇总指标 =====")
print("=" * 80)
print(final_metrics)

print("\n===== Smart DCA 所有买入日志汇总 =====")
print(final_buy_logs)

print("\n汇总指标已保存：", final_metrics_path)
print("Smart DCA 买入日志汇总已保存：", final_buy_logs_path)

print("\n第 13 步完成：压力期建仓测试运行成功。")
