from pathlib import Path
import pandas as pd
import yfinance as yf


# =========================
# 1. 设置项目路径
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

core_path = PROJECT_ROOT / "config" / "etf_universe_usd.csv"
tactical_path = PROJECT_ROOT / "config" / "tactical_universe_usd.csv"

print("项目路径：", PROJECT_ROOT)


# =========================
# 2. 读取 ETF 配置
# =========================

core_etfs = pd.read_csv(core_path)
tactical_etfs = pd.read_csv(tactical_path)

print("\n===== 长期核心 ETF 配置 =====")
print(core_etfs)

print("\n长期核心目标权重合计：", core_etfs["target_weight"].sum())
print("长期核心目标金额合计：", core_etfs["target_amount"].sum())

print("\n===== 短线观察 ETF 配置 =====")
print(tactical_etfs)


# =========================
# 3. 合并 ticker
# =========================

core_tickers = core_etfs["ticker"].tolist()
tactical_tickers = tactical_etfs["ticker"].tolist()

all_tickers = sorted(list(set(core_tickers + tactical_tickers)))

print("\n全部需要下载的 ETF：")
print(all_tickers)
print("ETF 数量：", len(all_tickers))


# =========================
# 4. 下载历史价格
# =========================

print("\n开始下载价格数据...")

data = yf.download(
    all_tickers,
    start="2015-01-01",
    auto_adjust=True,
    progress=False
)

# yfinance 多 ticker 下载后一般是 MultiIndex columns
if isinstance(data.columns, pd.MultiIndex):
    if "Close" in data.columns.get_level_values(0):
        prices = data["Close"].copy()
    else:
        raise ValueError("下载结果中没有 Close 价格列，请检查 yfinance 输出结构。")
else:
    prices = data[["Close"]].copy()

prices = prices.sort_index()

print("\n价格数据维度：", prices.shape)
print("\n价格数据前 5 行：")
print(prices.head())

print("\n价格数据后 5 行：")
print(prices.tail())


# =========================
# 5. 缺失值检查
# =========================

missing = pd.DataFrame({
    "missing_days": prices.isna().sum(),
    "missing_pct": prices.isna().mean()
}).sort_values("missing_days", ascending=False)

print("\n===== 缺失值检查 =====")
print(missing)


# =========================
# 6. 保存结果
# =========================

output_path = PROJECT_ROOT / "data" / "processed" / "all_etf_prices.csv"
prices.to_csv(output_path)

missing_path = PROJECT_ROOT / "data" / "processed" / "missing_check.csv"
missing.to_csv(missing_path)

print("\n价格数据已保存到：", output_path)
print("缺失值检查已保存到：", missing_path)


# =========================
# 7. 简单收益和波动检查
# =========================

returns = prices.pct_change(fill_method=None).dropna(how="all")

summary = pd.DataFrame({
    "start_date": prices.apply(lambda x: x.first_valid_index()),
    "end_date": prices.apply(lambda x: x.last_valid_index()),
    "start_price": prices.apply(lambda x: x.dropna().iloc[0] if x.dropna().shape[0] > 0 else None),
    "latest_price": prices.apply(lambda x: x.dropna().iloc[-1] if x.dropna().shape[0] > 0 else None),
    "total_return": prices.apply(lambda x: x.dropna().iloc[-1] / x.dropna().iloc[0] - 1 if x.dropna().shape[0] > 1 else None),
    "annualized_vol": returns.std() * (252 ** 0.5)
})

summary_path = PROJECT_ROOT / "data" / "processed" / "etf_summary.csv"
summary.to_csv(summary_path)

print("\n===== ETF 简单统计 =====")
print(summary)

print("\nETF 简单统计已保存到：", summary_path)

print("\n第 8 步完成：数据检查脚本运行成功。")
