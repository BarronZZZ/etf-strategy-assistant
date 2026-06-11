from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# 1. 设置项目路径
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

price_path = PROJECT_ROOT / "data" / "processed" / "all_etf_prices.csv"
report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)

print("项目路径：", PROJECT_ROOT)
print("价格文件：", price_path)


# =========================
# 2. 读取价格数据
# =========================

prices = pd.read_csv(price_path, index_col=0, parse_dates=True)

print("\n价格数据维度：", prices.shape)
print("\n价格数据前 5 行：")
print(prices.head())

print("\n价格数据后 5 行：")
print(prices.tail())


# =========================
# 3. 设置 ETF 分组
# =========================

core_etfs = ["VTI", "VEA", "VWO", "SGOV"]
tactical_etfs = ["SPY", "QQQ", "TLT", "GLD", "IWM", "XLK", "XLF", "XLV", "XLE", "BIL"]

print("\n长期核心 ETF：", core_etfs)
print("短线观察 ETF：", tactical_etfs)


# =========================
# 4. 画长期核心 ETF 原始价格走势
# =========================

plt.figure(figsize=(12, 6))

for ticker in core_etfs:
    plt.plot(prices.index, prices[ticker], label=ticker)

plt.title("Core ETF Price Trend")
plt.xlabel("Date")
plt.ylabel("Adjusted Close Price")
plt.legend()
plt.grid(True)
plt.tight_layout()

core_price_chart = report_dir / "core_etf_price_trend.png"
plt.savefig(core_price_chart, dpi=150)
plt.show()

print("\n长期核心 ETF 原始价格图已保存：", core_price_chart)


# =========================
# 5. 画长期核心 ETF 归一化走势
#    归一化 = 从各自第一天有效价格开始，统一设为 100
# =========================

core_prices = prices[core_etfs].copy()

core_normalized = pd.DataFrame(index=core_prices.index)

for ticker in core_etfs:
    s = core_prices[ticker].dropna()
    core_normalized.loc[s.index, ticker] = s / s.iloc[0] * 100

plt.figure(figsize=(12, 6))

for ticker in core_etfs:
    plt.plot(core_normalized.index, core_normalized[ticker], label=ticker)

plt.title("Core ETF Normalized Trend, Start = 100")
plt.xlabel("Date")
plt.ylabel("Normalized Price")
plt.legend()
plt.grid(True)
plt.tight_layout()

core_norm_chart = report_dir / "core_etf_normalized_trend.png"
plt.savefig(core_norm_chart, dpi=150)
plt.show()

print("长期核心 ETF 归一化走势图已保存：", core_norm_chart)


# =========================
# 6. 画短线观察池归一化走势
# =========================

tactical_prices = prices[tactical_etfs].copy()

tactical_normalized = pd.DataFrame(index=tactical_prices.index)

for ticker in tactical_etfs:
    s = tactical_prices[ticker].dropna()
    tactical_normalized.loc[s.index, ticker] = s / s.iloc[0] * 100

plt.figure(figsize=(12, 6))

for ticker in tactical_etfs:
    plt.plot(tactical_normalized.index, tactical_normalized[ticker], label=ticker)

plt.title("Tactical ETF Normalized Trend, Start = 100")
plt.xlabel("Date")
plt.ylabel("Normalized Price")
plt.legend()
plt.grid(True)
plt.tight_layout()

tactical_norm_chart = report_dir / "tactical_etf_normalized_trend.png"
plt.savefig(tactical_norm_chart, dpi=150)
plt.show()

print("短线观察池 ETF 归一化走势图已保存：", tactical_norm_chart)


# =========================
# 7. 计算最近表现
# =========================

latest = prices.iloc[-1]

perf = pd.DataFrame(index=prices.columns)

perf["latest_price"] = latest
perf["return_1m"] = prices.pct_change(21).iloc[-1]
perf["return_3m"] = prices.pct_change(63).iloc[-1]
perf["return_6m"] = prices.pct_change(126).iloc[-1]
perf["return_12m"] = prices.pct_change(252).iloc[-1]

perf = perf.sort_values("return_3m", ascending=False)

perf_path = PROJECT_ROOT / "data" / "processed" / "recent_performance.csv"
perf.to_csv(perf_path)

print("\n===== 最近表现，按 3 个月收益排序 =====")
print(perf)

print("\n最近表现表已保存：", perf_path)

print("\n第 9 步完成：ETF 可视化检查运行成功。")
