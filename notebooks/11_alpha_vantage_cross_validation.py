from pathlib import Path
from datetime import datetime
from io import StringIO
import time
import os
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

processed_dir = PROJECT_ROOT / "data" / "processed"
raw_dir = PROJECT_ROOT / "data" / "raw"
reports_dir = PROJECT_ROOT / "reports"

processed_dir.mkdir(exist_ok=True)
raw_dir.mkdir(exist_ok=True)
reports_dir.mkdir(exist_ok=True)

today_str = datetime.now().strftime("%Y-%m-%d")

env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

print("项目路径：", PROJECT_ROOT)
print(".env 路径：", env_path)
print("Alpha Vantage API Key 是否存在：", bool(api_key))

if not api_key:
    raise RuntimeError("没有读取到 ALPHA_VANTAGE_API_KEY，请检查 .env 文件。")


# =========================
# 2. 设置交叉验证标的
# =========================
# 注意：Alpha Vantage 免费额度有限，不要频繁重复运行。
# 这 12 个标的一次运行大约需要 12 次 API 请求。

validation_tickers = [
    "SPY", "QQQ", "VTI", "VEA", "VWO",
    "TLT", "GLD", "IWM",
    "XLK", "XLF", "XLV", "XLE"
]

print("\n===== Alpha Vantage 交叉验证标的 =====")
print(validation_tickers)
print("标的数量：", len(validation_tickers))


# =========================
# 3. 下载 yfinance 未复权 Close
# =========================
# 这里不用 auto_adjust=True，因为 Alpha Vantage TIME_SERIES_DAILY 返回的是普通 close。
# 为了口径一致，用 yfinance 的 Close 而不是 Adj Close。

print("\n开始下载 yfinance 数据...")

yf_data = yf.download(
    validation_tickers,
    period="1mo",
    auto_adjust=False,
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
# 4. 下载 Alpha Vantage 数据
# =========================

def download_alpha_vantage_daily_csv(ticker, api_key, today_str):
    """
    下载 Alpha Vantage TIME_SERIES_DAILY CSV。
    如果当天已经下载过，则读取缓存，避免重复消耗 API 请求。
    """

    cache_path = raw_dir / f"alpha_vantage_daily_{ticker}_{today_str}.csv"

    if cache_path.exists():
        try:
            df = pd.read_csv(cache_path)
            if not df.empty and "timestamp" in df.columns and "close" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp").set_index("timestamp")
                return df, "cache", cache_path
        except Exception:
            pass

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "datatype": "csv",
        "apikey": api_key
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"{ticker} Alpha Vantage HTTP错误：{response.status_code}")

    text = response.text.strip()

    # Alpha Vantage 在额度或参数问题时，可能返回 JSON 或提示文本，而不是 CSV。
    if not text.startswith("timestamp,"):
        raise RuntimeError(f"{ticker} Alpha Vantage 返回不是CSV，内容前200字：{text[:200]}")

    cache_path.write_text(text, encoding="utf-8")

    df = pd.read_csv(StringIO(text))

    if df.empty or "timestamp" not in df.columns or "close" not in df.columns:
        raise RuntimeError(f"{ticker} Alpha Vantage CSV字段异常")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").set_index("timestamp")

    return df, "api", cache_path


av_frames = {}
download_logs = []

print("\n开始下载 Alpha Vantage 数据...")

for i, ticker in enumerate(validation_tickers, start=1):
    used_api_request = False

    try:
        df, source_type, cache_path = download_alpha_vantage_daily_csv(ticker, api_key, today_str)
        used_api_request = (source_type == "api")

        av_frames[ticker] = df[["close"]].rename(columns={"close": ticker})

        download_logs.append({
            "ticker": ticker,
            "success": True,
            "source_type": source_type,
            "latest_date": df.index.max(),
            "rows": len(df),
            "cache_path": str(cache_path),
            "notes": "下载成功"
        })

        print(f"{i}/{len(validation_tickers)} {ticker} 成功，来源：{source_type}，最新日期：{df.index.max()}，行数：{len(df)}")

    except Exception as e:
        download_logs.append({
            "ticker": ticker,
            "success": False,
            "source_type": None,
            "latest_date": None,
            "rows": 0,
            "cache_path": None,
            "notes": str(e)
        })

        print(f"{i}/{len(validation_tickers)} {ticker} 失败：{e}")

    # 只有真正调用 Alpha Vantage API 时才等待。
    # 如果是读取当天 cache，不等待。
    if used_api_request and i < len(validation_tickers):
        time.sleep(13)


download_log_df = pd.DataFrame(download_logs)

download_log_path = processed_dir / f"alpha_vantage_download_log_{today_str}.csv"
download_log_df.to_csv(download_log_path, index=False)

latest_download_log_path = processed_dir / "alpha_vantage_download_log_latest.csv"
download_log_df.to_csv(latest_download_log_path, index=False)


if len(av_frames) > 0:
    av_prices = pd.concat(av_frames.values(), axis=1).sort_index().ffill(limit=5)
else:
    av_prices = pd.DataFrame()

print("\n===== Alpha Vantage 下载日志 =====")
print(download_log_df)

if not av_prices.empty:
    print("\nAlpha Vantage 价格数据维度：", av_prices.shape)
    print("Alpha Vantage 最新日期：", av_prices.index.max())
else:
    print("\n没有任何 Alpha Vantage 数据下载成功。")


# =========================
# 5. 交叉验证
# =========================

rows = []

for ticker in validation_tickers:
    if ticker not in yf_prices.columns:
        rows.append({
            "ticker": ticker,
            "status": "missing_yfinance",
            "common_date": None,
            "yf_latest_date": None,
            "av_latest_date": None,
            "yf_close": np.nan,
            "av_close": np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "yfinance 无数据"
        })
        continue

    yf_s = yf_prices[ticker].dropna()

    if av_prices.empty or ticker not in av_prices.columns:
        rows.append({
            "ticker": ticker,
            "status": "missing_alpha_vantage",
            "common_date": None,
            "yf_latest_date": yf_s.index.max() if not yf_s.empty else None,
            "av_latest_date": None,
            "yf_close": yf_s.iloc[-1] if not yf_s.empty else np.nan,
            "av_close": np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "Alpha Vantage 无可用数据"
        })
        continue

    av_s = av_prices[ticker].dropna()

    common_dates = yf_s.index.intersection(av_s.index)

    if len(common_dates) == 0:
        rows.append({
            "ticker": ticker,
            "status": "no_common_date",
            "common_date": None,
            "yf_latest_date": yf_s.index.max(),
            "av_latest_date": av_s.index.max() if not av_s.empty else None,
            "yf_close": yf_s.iloc[-1],
            "av_close": av_s.iloc[-1] if not av_s.empty else np.nan,
            "abs_diff": np.nan,
            "pct_diff": np.nan,
            "pass_price_check": False,
            "notes": "yfinance 和 Alpha Vantage 没有共同日期"
        })
        continue

    # 为避免盘中数据误判：
    # 如果最新共同日期是今天，默认使用前一个共同交易日进行交叉验证。
    # 原因：yfinance 在盘中可能更新当日价格，而 Alpha Vantage/cache 可能仍是旧收盘或延迟数据。
    common_dates_sorted = common_dates.sort_values()
    latest_common_date = common_dates_sorted.max()
    today_date = pd.Timestamp(datetime.now().date())

    if latest_common_date.normalize() == today_date and len(common_dates_sorted) >= 2:
        common_date = common_dates_sorted[-2]
        date_selection_note = "使用前一个共同交易日，避免盘中数据误判"
    else:
        common_date = latest_common_date
        date_selection_note = "使用最新共同交易日"

    yf_close = float(yf_s.loc[common_date])
    av_close = float(av_s.loc[common_date])

    abs_diff = abs(yf_close - av_close)
    pct_diff = abs_diff / yf_close if yf_close != 0 else np.nan

    pass_check = bool(pct_diff <= 0.01)

    rows.append({
        "ticker": ticker,
        "status": "ok" if pass_check else "price_mismatch",
        "common_date": common_date,
        "yf_latest_date": yf_s.index.max(),
        "av_latest_date": av_s.index.max(),
        "yf_close": yf_close,
        "av_close": av_close,
        "abs_diff": abs_diff,
        "pct_diff": pct_diff,
        "pass_price_check": pass_check,
        "notes": ("通过；" + date_selection_note) if pass_check else ("价格差异超过1%，需要人工检查；" + date_selection_note)
    })


validation = pd.DataFrame(rows)

validation_path = processed_dir / f"cross_validation_alpha_vantage_{today_str}.csv"
validation.to_csv(validation_path, index=False)

latest_validation_path = processed_dir / "cross_validation_alpha_vantage_latest.csv"
validation.to_csv(latest_validation_path, index=False)

print("\n===== yfinance vs Alpha Vantage 交叉验证结果 =====")
print(validation)

print("\n交叉验证结果已保存：", validation_path)
print("最新交叉验证结果已保存：", latest_validation_path)


# =========================
# 6. 生成状态摘要
# =========================

passed = int(validation["pass_price_check"].sum())
total = len(validation)
failed = total - passed

av_success_count = int(download_log_df["success"].sum())

if av_success_count == 0:
    validation_status = "degraded"
    validation_summary = "Alpha Vantage 全部下载失败，无法完成交叉验证。"
elif failed == 0:
    validation_status = "passed"
    validation_summary = f"{passed}/{total} 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。"
else:
    validation_status = "need_check"
    validation_summary = f"{passed}/{total} 个标的通过，{failed} 个标的需要人工检查。"

print("\n===== 交叉验证摘要 =====")
print("状态：", validation_status)
print("摘要：", validation_summary)


# =========================
# 7. 生成 Markdown 报告
# =========================

md_path = reports_dir / f"cross_validation_alpha_vantage_{today_str}.md"
latest_md_path = reports_dir / "cross_validation_alpha_vantage_latest.md"

with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# yfinance vs Alpha Vantage 交叉验证报告 - {today_str}\n\n")

    f.write("## 1. 验证状态\n\n")
    f.write(f"- 状态：**{validation_status}**\n")
    f.write(f"- 摘要：{validation_summary}\n")
    f.write("- 主数据源：yfinance Close\n")
    f.write("- 辅助数据源：Alpha Vantage TIME_SERIES_DAILY close\n")
    f.write("- 差异阈值：1%\n")
    f.write("- 自动交易：关闭\n\n")

    f.write("## 2. Alpha Vantage 下载日志\n\n")
    f.write(download_log_df.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 3. 交叉验证明细\n\n")
    f.write(validation.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 4. 使用说明\n\n")
    f.write("- 如果状态为 passed，说明两个数据源最新共同交易日价格基本一致。\n")
    f.write("- 如果状态为 need_check，说明部分价格差异超过阈值，应人工检查。\n")
    f.write("- 如果状态为 degraded，说明辅助数据源不可用，不应自动交易。\n")

with open(md_path, "r", encoding="utf-8") as src:
    content = src.read()

with open(latest_md_path, "w", encoding="utf-8") as dst:
    dst.write(content)

print("\nMarkdown 报告已保存：", md_path)
print("最新 Markdown 报告已保存：", latest_md_path)

print("\n第 20 步完成：Alpha Vantage 交叉验证运行成功。")
