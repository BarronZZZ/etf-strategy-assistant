from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

config_dir = PROJECT_ROOT / "config"
processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

processed_dir.mkdir(exist_ok=True)
reports_dir.mkdir(exist_ok=True)

universe_path = config_dir / "market_report_universe.csv"
rules_path = config_dir / "daily_report_rules.csv"

print("项目路径：", PROJECT_ROOT)
print("市场观察配置：", universe_path)
print("早报规则配置：", rules_path)


# =========================
# 2. 读取配置
# =========================

universe = pd.read_csv(universe_path)
rules = pd.read_csv(rules_path)

tickers = universe["ticker"].tolist()

print("\n===== 市场观察标的 =====")
print(universe)

print("\n观察标的数量：", len(tickers))

print("\n===== 早报规则 =====")
print(rules)


# =========================
# 3. 下载市场数据
# =========================

print("\n开始下载最近 2 年市场数据...")

data = yf.download(
    tickers,
    period="2y",
    auto_adjust=True,
    progress=False,
    threads=False
)

if isinstance(data.columns, pd.MultiIndex):
    if "Close" in data.columns.get_level_values(0):
        prices = data["Close"].copy()
    else:
        raise ValueError("yfinance 下载结果里没有 Close 列。")
else:
    prices = data[["Close"]].copy()

prices = prices.sort_index()

# 删除全空列
prices = prices.dropna(axis=1, how="all")

# 不同资产交易日历不同，可能导致部分日期缺失。
# 为了计算 MA50 / MA200 / 252日回撤，这里做有限前向填充。
# limit=5 表示最多只填补连续 5 个交易日的缺口，避免过度填充。
prices = prices.ffill(limit=5)

print("\n价格数据维度：", prices.shape)
print("\n价格数据最后 5 行：")
print(prices.tail())


# =========================
# 4. 保存每日市场价格
# =========================

today_str = datetime.now().strftime("%Y-%m-%d")

daily_price_path = processed_dir / f"daily_market_prices_{today_str}.csv"
prices.to_csv(daily_price_path)

latest_prices_path = processed_dir / "latest_market_prices.csv"
prices.to_csv(latest_prices_path)

print("\n每日市场价格已保存：", daily_price_path)
print("最新市场价格已保存：", latest_prices_path)


# =========================
# 5. 计算表现指标
# =========================

def pct_change_n_days(df, n):
    if len(df) <= n:
        return pd.Series(index=df.columns, dtype=float)
    return df.iloc[-1] / df.iloc[-n-1] - 1


latest = prices.iloc[-1]

performance = pd.DataFrame(index=prices.columns)
performance["latest_price"] = latest
performance["return_1d"] = pct_change_n_days(prices, 1)
performance["return_5d"] = pct_change_n_days(prices, 5)
performance["return_1m"] = pct_change_n_days(prices, 21)
performance["return_3m"] = pct_change_n_days(prices, 63)
performance["return_6m"] = pct_change_n_days(prices, 126)
performance["return_12m"] = pct_change_n_days(prices, 252)

ma50 = prices.rolling(50).mean().iloc[-1]
ma200 = prices.rolling(200).mean().iloc[-1]
high_252 = prices.rolling(252).max().iloc[-1]

performance["ma50"] = ma50
performance["ma200"] = ma200
performance["above_50ma"] = performance["latest_price"] > performance["ma50"]
performance["above_200ma"] = performance["latest_price"] > performance["ma200"]
performance["drawdown_252d"] = performance["latest_price"] / high_252 - 1

performance = performance.sort_values("return_3m", ascending=False)

performance_path = processed_dir / f"daily_market_performance_{today_str}.csv"
performance.to_csv(performance_path)

latest_performance_path = processed_dir / "latest_market_performance.csv"
performance.to_csv(latest_performance_path)

print("\n===== 市场表现表，按 3 个月收益排序 =====")
print(performance)

print("\n市场表现表已保存：", performance_path)


# =========================
# 6. 生成风险信号
# =========================

signals = []

def add_signal(rule_id, triggered, detail):
    rule_row = rules[rules["rule_id"] == rule_id]
    if not rule_row.empty:
        row = rule_row.iloc[0]
        signals.append({
            "rule_id": rule_id,
            "category": row["category"],
            "triggered": triggered,
            "meaning": row["meaning"],
            "action_level": row["action_level"],
            "auto_trade": row["auto_trade"],
            "detail": detail
        })


def safe_value(ticker, column):
    if ticker in performance.index and column in performance.columns:
        return performance.loc[ticker, column]
    return np.nan


vti_price = safe_value("VTI", "latest_price")
vti_ma200 = safe_value("VTI", "ma200")
vti_dd = safe_value("VTI", "drawdown_252d")

spy_price = safe_value("SPY", "latest_price")
spy_ma200 = safe_value("SPY", "ma200")

qqq_3m = safe_value("QQQ", "return_3m")
spy_3m = safe_value("SPY", "return_3m")

tlt_1m = safe_value("TLT", "return_1m")
gld_1m = safe_value("GLD", "return_1m")
spy_1m = safe_value("SPY", "return_1m")

vix_value = safe_value("^VIX", "latest_price")


# VTI 趋势
if not np.isnan(vti_price) and not np.isnan(vti_ma200):
    add_signal(
        "VTI_ABOVE_200MA",
        bool(vti_price > vti_ma200),
        f"VTI 最新价 {vti_price:.2f}，200日均线 {vti_ma200:.2f}"
    )
    add_signal(
        "VTI_BELOW_200MA",
        bool(vti_price < vti_ma200),
        f"VTI 最新价 {vti_price:.2f}，200日均线 {vti_ma200:.2f}"
    )

# VTI 回撤
if not np.isnan(vti_dd):
    add_signal(
        "VTI_DD_10",
        bool(vti_dd <= -0.10),
        f"VTI 252日高点回撤 {vti_dd:.2%}"
    )
    add_signal(
        "VTI_DD_15",
        bool(vti_dd <= -0.15),
        f"VTI 252日高点回撤 {vti_dd:.2%}"
    )
    add_signal(
        "VTI_DD_25",
        bool(vti_dd <= -0.25),
        f"VTI 252日高点回撤 {vti_dd:.2%}"
    )

# SPY 200MA
if not np.isnan(spy_price) and not np.isnan(spy_ma200):
    add_signal(
        "SPY_BELOW_200MA",
        bool(spy_price < spy_ma200),
        f"SPY 最新价 {spy_price:.2f}，200日均线 {spy_ma200:.2f}"
    )

# QQQ 相对 SPY
if not np.isnan(qqq_3m) and not np.isnan(spy_3m):
    add_signal(
        "QQQ_STRONG",
        bool(qqq_3m > spy_3m),
        f"QQQ 3个月收益 {qqq_3m:.2%}，SPY 3个月收益 {spy_3m:.2%}"
    )

# 防守资产
if not np.isnan(tlt_1m) and not np.isnan(spy_1m):
    add_signal(
        "TLT_STRONG_DEFENSE",
        bool(tlt_1m > spy_1m),
        f"TLT 1个月收益 {tlt_1m:.2%}，SPY 1个月收益 {spy_1m:.2%}"
    )

if not np.isnan(gld_1m) and not np.isnan(spy_1m):
    add_signal(
        "GLD_STRONG_DEFENSE",
        bool(gld_1m > spy_1m),
        f"GLD 1个月收益 {gld_1m:.2%}，SPY 1个月收益 {spy_1m:.2%}"
    )

# VIX
if not np.isnan(vix_value):
    add_signal(
        "VIX_HIGH",
        bool(vix_value > 25),
        f"VIX 当前值 {vix_value:.2f}"
    )
    add_signal(
        "VIX_EXTREME",
        bool(vix_value > 35),
        f"VIX 当前值 {vix_value:.2f}"
    )


signals_df = pd.DataFrame(signals)

signals_path = processed_dir / f"daily_market_signals_{today_str}.csv"
signals_df.to_csv(signals_path, index=False)

latest_signals_path = processed_dir / "latest_market_signals.csv"
signals_df.to_csv(latest_signals_path, index=False)

print("\n===== 今日市场信号 =====")
print(signals_df)

print("\n市场信号已保存：", signals_path)


# =========================
# 7. 生成整体风险状态
# =========================

triggered = signals_df[signals_df["triggered"] == True].copy()

high_alert_count = (triggered["action_level"] == "high_alert").sum()
alert_count = (triggered["action_level"] == "alert").sum()
warning_count = (triggered["action_level"] == "warning").sum()
watch_count = (triggered["action_level"] == "watch").sum()

if high_alert_count > 0:
    market_status = "高风险"
    action_summary = "暂停自动交易，只做人工确认；长期账户可以观察是否有分批加仓机会。"
elif alert_count > 0:
    market_status = "偏高风险"
    action_summary = "不建议激进加仓；长期账户按计划执行，提前买入需要人工确认。"
elif warning_count > 0:
    market_status = "中等风险"
    action_summary = "长期账户继续按计划执行；短线交易降低仓位。"
elif watch_count > 0:
    market_status = "观察状态"
    action_summary = "长期账户可以继续执行固定分批；如有回撤提醒，可以考虑但不自动提前买入。"
else:
    market_status = "正常"
    action_summary = "长期账户按固定计划执行；短线账户只做观察，不自动交易。"

print("\n===== 市场风险状态 =====")
print("市场状态：", market_status)
print("操作摘要：", action_summary)


# =========================
# 8. 生成 Markdown 每日早报
# =========================

report_path = reports_dir / f"daily_market_report_{today_str}.md"
latest_report_path = reports_dir / "daily_market_report_latest.md"

top_3m = performance.sort_values("return_3m", ascending=False).head(5)
bottom_3m = performance.sort_values("return_3m", ascending=True).head(5)

core_tickers = ["VTI", "VEA", "VWO", "SGOV"]
core_perf = performance.loc[[t for t in core_tickers if t in performance.index]].copy()

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# 每日市场早报 - {today_str}\n\n")

    f.write("## 1. 市场风险状态\n\n")
    f.write(f"- 当前状态：**{market_status}**\n")
    f.write(f"- 操作摘要：{action_summary}\n")
    f.write("- 自动交易：关闭。本报告只提供提醒，不自动下单。\n\n")

    f.write("## 2. 长期核心账户观察\n\n")
    f.write(core_perf[[
        "latest_price",
        "return_1d",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "above_200ma",
        "drawdown_252d"
    ]].to_markdown())
    f.write("\n\n")

    f.write("## 3. 今日触发信号\n\n")
    if triggered.empty:
        f.write("今日没有触发高优先级风险信号。\n\n")
    else:
        f.write(triggered[[
            "rule_id",
            "category",
            "action_level",
            "meaning",
            "detail",
            "auto_trade"
        ]].to_markdown(index=False))
        f.write("\n\n")

    f.write("## 4. 3个月表现靠前标的\n\n")
    f.write(top_3m[["latest_price", "return_1m", "return_3m", "return_6m", "return_12m"]].to_markdown())
    f.write("\n\n")

    f.write("## 5. 3个月表现靠后标的\n\n")
    f.write(bottom_3m[["latest_price", "return_1m", "return_3m", "return_6m", "return_12m"]].to_markdown())
    f.write("\n\n")

    f.write("## 6. 数据说明\n\n")
    f.write("- 本版早报使用 yfinance 下载市场价格数据。\n")
    f.write("- 后续版本会加入 Alpha Vantage / FRED / 新闻数据交叉验证。\n")
    f.write("- 本报告不构成投资建议，也不会自动交易。\n")

# 同步保存 latest 版本
with open(report_path, "r", encoding="utf-8") as src:
    content = src.read()

with open(latest_report_path, "w", encoding="utf-8") as dst:
    dst.write(content)

print("\n每日市场早报已保存：", report_path)
print("最新早报副本已保存：", latest_report_path)

print("\n第 17 步完成：每日市场早报 V1 生成成功。")
