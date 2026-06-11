from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from io import StringIO


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

processed_dir.mkdir(exist_ok=True)
reports_dir.mkdir(exist_ok=True)

today_str = datetime.now().strftime("%Y-%m-%d")

print("项目路径：", PROJECT_ROOT)


# =========================
# 2. 设置需要交叉验证的 ETF
# =========================

validation_tickers = [
    "SPY", "QQQ", "VTI", "VEA", "VWO",
    "TLT", "GLD", "IWM",
    "XLK", "XLF", "XLV", "XLE"
]

print("\n===== 交叉验证标的 =====")
print(validation_tickers)


# =========================
# 3. 下载 yfinance 数据
# =========================

print("\n开始下载 yfinance 数据...")

yf_data = yf.download(
    validation_tickers,
    period="1mo",
    auto_adjust=True,
    progress=False,
    threads=False
)

if isinstance(yf_data.columns, pd.MultiIndex):
    yf_prices = yf_data["Close"].copy()
else:
    yf_prices = yf_data[["Close"]].copy()

yf_prices = yf_prices.sort_index().ffill(limit=5)

print("yfinance 数据维度：", yf_prices.shape)
print("yfinance 最新日期：", yf_prices.index.max())


# =========================
# 4. 尝试下载 Stooq 数据
# =========================

def download_stooq_daily_for_ticker(ticker):
    """
    尝试从 Stooq 下载日线数据。
    为了提高兼容性，会尝试多种 symbol 写法。
    如果全部失败，返回 None。
    """

    symbol_candidates = [
        ticker.lower() + ".us",
        ticker.upper() + ".US",
        ticker.lower(),
        ticker.upper()
    ]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=45)

    d1 = start_date.strftime("%Y%m%d")
    d2 = end_date.strftime("%Y%m%d")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for symbol in symbol_candidates:
        urls = [
            f"https://stooq.com/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d",
            f"https://stooq.com/q/d/l/?s={symbol}&i=d"
        ]

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code != 200:
                    continue

                text = response.text.strip()

                if not text or "No data" in text or "Date,Open,High,Low,Close,Volume" not in text:
                    continue

                df = pd.read_csv(StringIO(text))

                if df.empty or "Date" not in df.columns or "Close" not in df.columns:
                    continue

                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date").set_index("Date")

                out = df[["Close"]].rename(columns={"Close": ticker})

                return out, symbol, url

            except Exception:
                continue

    return None, None, None


print("\n开始尝试下载 Stooq 数据...")

stooq_frames = {}
stooq_download_status = []

for ticker in validation_tickers:
    df, used_symbol, used_url = download_stooq_daily_for_ticker(ticker)

    if df is not None:
        stooq_frames[ticker] = df
        stooq_download_status.append({
            "ticker": ticker,
            "stooq_available": True,
            "used_symbol": used_symbol,
            "latest_date": df.index.max(),
            "notes": "Stooq 下载成功"
        })
        print(f"{ticker} 下载成功，Stooq symbol: {used_symbol}，最新日期：{df.index.max()}")
    else:
        stooq_download_status.append({
            "ticker": ticker,
            "stooq_available": False,
            "used_symbol": None,
            "latest_date": None,
            "notes": "Stooq 下载失败或无可用 CSV"
        })
        print(f"{ticker} Stooq 下载失败或无可用 CSV")


if len(stooq_frames) > 0:
    stooq_prices = pd.concat(stooq_frames.values(), axis=1).sort_index().ffill(limit=5)
    print("\nStooq 数据维度：", stooq_prices.shape)
    print("Stooq 最新日期：", stooq_prices.index.max())
else:
    stooq_prices = pd.DataFrame()
    print("\nStooq 没有任何标的下载成功。本次交叉验证将标记为 degraded。")


# =========================
# 5. 对齐日期并比较
# =========================

rows = []

for ticker in validation_tickers:
    if ticker not in yf_prices.columns:
        rows.append({
            "ticker": ticker,
            "status": "missing_yfinance",
            "common_date": None,
            "yf_latest_date": None,
            "stooq_latest_date": None,
            "yf_price": np.nan,
            "stooq_price": np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "yfinance 无数据"
        })
        continue

    yf_s = yf_prices[ticker].dropna()

    if stooq_prices.empty or ticker not in stooq_prices.columns:
        rows.append({
            "ticker": ticker,
            "status": "missing_stooq",
            "common_date": None,
            "yf_latest_date": yf_s.index.max() if not yf_s.empty else None,
            "stooq_latest_date": None,
            "yf_price": yf_s.iloc[-1] if not yf_s.empty else np.nan,
            "stooq_price": np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "Stooq 不可用，无法交叉验证；主数据源 yfinance 可用"
        })
        continue

    stooq_s = stooq_prices[ticker].dropna()

    if yf_s.empty or stooq_s.empty:
        rows.append({
            "ticker": ticker,
            "status": "empty_data",
            "common_date": None,
            "yf_latest_date": yf_s.index.max() if not yf_s.empty else None,
            "stooq_latest_date": stooq_s.index.max() if not stooq_s.empty else None,
            "yf_price": yf_s.iloc[-1] if not yf_s.empty else np.nan,
            "stooq_price": stooq_s.iloc[-1] if not stooq_s.empty else np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "至少一个数据源为空"
        })
        continue

    common_dates = yf_s.index.intersection(stooq_s.index)

    if len(common_dates) == 0:
        rows.append({
            "ticker": ticker,
            "status": "no_common_date",
            "common_date": None,
            "yf_latest_date": yf_s.index.max(),
            "stooq_latest_date": stooq_s.index.max(),
            "yf_price": yf_s.iloc[-1],
            "stooq_price": stooq_s.iloc[-1],
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "没有共同交易日期"
        })
        continue

    common_date = common_dates.max()

    yf_price = yf_s.loc[common_date]
    stooq_price = stooq_s.loc[common_date]

    abs_diff = abs(yf_price - stooq_price)
    pct_diff = abs_diff / yf_price if yf_price != 0 else np.nan

    pass_check = bool(pct_diff <= 0.01)

    rows.append({
        "ticker": ticker,
        "status": "ok" if pass_check else "price_mismatch",
        "common_date": common_date,
        "yf_latest_date": yf_s.index.max(),
        "stooq_latest_date": stooq_s.index.max(),
        "yf_price": yf_price,
        "stooq_price": stooq_price,
        "abs_diff": abs_diff,
        "pct_diff": pct_diff,
        "pass_price_check": pass_check,
        "notes": "通过" if pass_check else "价格差异超过1%，需要人工检查"
    })


validation = pd.DataFrame(rows)
stooq_status = pd.DataFrame(stooq_download_status)

validation_path = processed_dir / f"cross_validation_report_{today_str}.csv"
validation.to_csv(validation_path, index=False)

latest_validation_path = processed_dir / "cross_validation_report_latest.csv"
validation.to_csv(latest_validation_path, index=False)

stooq_status_path = processed_dir / f"stooq_download_status_{today_str}.csv"
stooq_status.to_csv(stooq_status_path, index=False)

latest_stooq_status_path = processed_dir / "stooq_download_status_latest.csv"
stooq_status.to_csv(latest_stooq_status_path, index=False)

print("\n===== Stooq 下载状态 =====")
print(stooq_status)

print("\n===== 数据交叉验证结果 =====")
print(validation)

print("\n交叉验证报告已保存：", validation_path)
print("最新交叉验证报告已保存：", latest_validation_path)
print("Stooq 下载状态已保存：", stooq_status_path)


# =========================
# 6. 生成验证状态
# =========================

passed = validation["pass_price_check"].sum()
total = len(validation)
failed = total - passed

stooq_available_count = stooq_status["stooq_available"].sum()

if stooq_available_count == 0:
    validation_status = "degraded"
    validation_summary = "yfinance 主数据源可用，但 Stooq 辅助数据源全部不可用，无法完成独立交叉验证。"
elif failed == 0:
    validation_status = "passed"
    validation_summary = f"{passed}/{total} 个标的通过价格交叉验证。"
else:
    validation_status = "need_check"
    validation_summary = f"{passed}/{total} 个标的通过，{failed} 个标的需要检查。"


# =========================
# 7. 生成 Markdown 报告
# =========================

md_path = reports_dir / f"cross_validation_report_{today_str}.md"
latest_md_path = reports_dir / "cross_validation_report_latest.md"

with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# ETF 数据交叉验证报告 - {today_str}\n\n")

    f.write("## 1. 验证状态\n\n")
    f.write(f"- 状态：**{validation_status}**\n")
    f.write(f"- 摘要：{validation_summary}\n")
    f.write("- 主数据源：yfinance\n")
    f.write("- 辅助数据源：Stooq\n")
    f.write("- 价格差异阈值：1%\n\n")

    f.write("## 2. Stooq 下载状态\n\n")
    f.write(stooq_status.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 3. 验证明细\n\n")
    f.write(validation.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 4. 使用说明\n\n")
    f.write("- 如果状态为 passed，说明当天价格数据可信度较高。\n")
    f.write("- 如果状态为 degraded，说明主数据源可用，但辅助数据源不可用，不能视为独立交叉验证通过。\n")
    f.write("- 如果状态为 need_check，说明部分标的价格差异超过阈值，需要人工检查。\n")
    f.write("- 无论哪种状态，本系统都不会自动交易。\n")

with open(md_path, "r", encoding="utf-8") as src:
    content = src.read()

with open(latest_md_path, "w", encoding="utf-8") as dst:
    dst.write(content)

print("\nMarkdown 交叉验证报告已保存：", md_path)
print("最新 Markdown 交叉验证报告已保存：", latest_md_path)

print("\n===== 交叉验证摘要 =====")
print("状态：", validation_status)
print("摘要：", validation_summary)

print("\n第 18 步完成：数据交叉验证模块 V1 修复版运行成功。")
