from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands


PROJECT_DIR = Path(__file__).resolve().parents[1]

CONFIG_CORE = PROJECT_DIR / "config" / "etf_universe_usd.csv"
PRICES_FILE = PROJECT_DIR / "data" / "processed" / "latest_market_prices.csv"
ORDER_PLAN_FILE = PROJECT_DIR / "data" / "processed" / "latest_entry_order_plan.csv"

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")


def read_price_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    date_col = None
    for c in df.columns:
        if c.lower() in ["date", "datetime", "timestamp"]:
            date_col = c
            break

    if date_col is None:
        first_col = df.columns[0]
        parsed = pd.to_datetime(df[first_col], errors="coerce")
        if parsed.notna().mean() > 0.8:
            date_col = first_col
        else:
            raise ValueError("无法识别价格表中的日期列，请检查 latest_market_prices.csv")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()

    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.columns = [str(c).strip() for c in df.columns]
    return df


def get_col(prices: pd.DataFrame, ticker: str):
    ticker_upper = ticker.upper()
    mapping = {str(c).upper(): c for c in prices.columns}
    return mapping.get(ticker_upper)


def safe_latest(series: pd.Series):
    s = series.dropna()
    if len(s) == 0:
        return np.nan
    return float(s.iloc[-1])


def pct_return(close: pd.Series, n: int):
    close = close.dropna()
    if len(close) <= n:
        return np.nan
    return float(close.iloc[-1] / close.iloc[-n - 1] - 1)


def status_from_score(score):
    if pd.isna(score):
        return "unknown"
    if score >= 80:
        return "strong"
    if score >= 65:
        return "normal"
    if score >= 50:
        return "neutral"
    if score >= 35:
        return "weak"
    return "high_risk"


def calc_scores(row):
    ticker = row["ticker"]

    latest_price = row["latest_price"]
    ma50 = row["ma50"]
    ma100 = row["ma100"]
    ma200 = row["ma200"]
    ma200_slope_20d = row["ma200_slope_20d"]
    rsi14 = row["rsi14"]
    macd_hist = row["macd_hist"]
    ret_1m = row["return_1m"]
    ret_3m = row["return_3m"]
    ret_6m = row["return_6m"]
    vol20 = row["vol20_annualized"]
    drawdown = row["drawdown_252d"]
    bb_pband = row["bb_percent_b"]
    bb_width = row["bb_width"]

    above_50 = bool(row["above_50ma"])
    above_100 = bool(row["above_100ma"])
    above_200 = bool(row["above_200ma"])

    # SGOV 是现金/短债工具，评分意义和风险资产不同。
    # 但仍保留价格、均线、波动率指标，帮助检查是否异常。
    is_cash_like = ticker.upper() == "SGOV"

    trend_score = 0
    trend_score += 12 if above_200 else 0
    trend_score += 6 if above_100 else 0
    trend_score += 4 if above_50 else 0
    trend_score += 5 if pd.notna(ma200_slope_20d) and ma200_slope_20d > 0 else 0
    trend_score += 3 if pd.notna(ret_6m) and ret_6m > 0 else 0
    trend_score = min(trend_score, 30)

    momentum_score = 0
    momentum_score += 5 if pd.notna(ret_1m) and ret_1m > 0 else 0
    momentum_score += 7 if pd.notna(ret_3m) and ret_3m > 0 else 0
    momentum_score += 6 if pd.notna(ret_6m) and ret_6m > 0 else 0
    momentum_score += 4 if pd.notna(macd_hist) and macd_hist > 0 else 0

    if pd.notna(rsi14):
        if 45 <= rsi14 <= 70:
            momentum_score += 3
        elif 30 <= rsi14 < 45:
            momentum_score += 1
        elif 70 < rsi14 <= 80:
            momentum_score += 1

    momentum_score = min(momentum_score, 25)

    risk_score = 0
    if pd.notna(vol20):
        if is_cash_like and vol20 <= 0.03:
            risk_score += 8
        elif vol20 <= 0.15:
            risk_score += 8
        elif vol20 <= 0.25:
            risk_score += 6
        elif vol20 <= 0.35:
            risk_score += 3
        else:
            risk_score += 1

    if pd.notna(rsi14):
        if 30 <= rsi14 <= 75:
            risk_score += 7
        elif 20 <= rsi14 < 30 or 75 < rsi14 <= 85:
            risk_score += 3
        else:
            risk_score += 1

    if pd.notna(bb_width):
        if bb_width <= 0.15:
            risk_score += 5
        elif bb_width <= 0.30:
            risk_score += 3
        else:
            risk_score += 1

    risk_score = min(risk_score, 20)

    drawdown_score = 0
    if pd.notna(drawdown):
        if drawdown >= -0.05:
            drawdown_score = 8
        elif drawdown >= -0.15:
            drawdown_score = 15
        elif drawdown >= -0.25:
            drawdown_score = 10
        else:
            drawdown_score = 4

    price_position_score = 0
    if pd.notna(bb_pband):
        if bb_pband < 0.20:
            price_position_score = 10
        elif 0.20 <= bb_pband <= 0.80:
            price_position_score = 8
        elif 0.80 < bb_pband <= 1.00:
            price_position_score = 5
        else:
            price_position_score = 2

    market_score = trend_score + momentum_score + risk_score + drawdown_score + price_position_score
    market_score = min(market_score, 100)

    if not above_200 and not is_cash_like:
        reference_signal = "risk_wait_below_200ma"
    elif pd.notna(drawdown) and drawdown <= -0.25 and not is_cash_like:
        reference_signal = "deep_drawdown_manual_review"
    elif pd.notna(drawdown) and drawdown <= -0.15 and above_200 and not is_cash_like:
        reference_signal = "deep_pullback_opportunity_manual"
    elif pd.notna(drawdown) and drawdown <= -0.10 and above_200 and not is_cash_like:
        reference_signal = "pullback_opportunity"
    elif market_score >= 65:
        reference_signal = "normal_or_positive"
    else:
        reference_signal = "neutral_or_wait"

    if is_cash_like:
        notes = "SGOV 是现金/短债工具，主要用于现金管理，不按风险资产回撤买点解释。"
    else:
        notes = "多指标评分仅用于辅助观察，暂未接入买入决策。"

    return pd.Series({
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "risk_score": risk_score,
        "drawdown_score": drawdown_score,
        "price_position_score": price_position_score,
        "market_score": market_score,
        "score_status": status_from_score(market_score),
        "reference_signal": reference_signal,
        "notes": notes
    })


def fmt_num(x, digits=2):
    if pd.isna(x):
        return ""
    return f"{x:.{digits}f}"


def fmt_pct(x):
    if pd.isna(x):
        return ""
    return f"{x:.2%}"


def markdown_table(df: pd.DataFrame, columns):
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [header, sep]

    for _, r in df.iterrows():
        values = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, float):
                values.append(f"{v:.4f}")
            else:
                values.append(str(v))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


print("项目路径：", PROJECT_DIR)
print("核心配置是否存在：", CONFIG_CORE.exists())
print("价格文件是否存在：", PRICES_FILE.exists())
print("建议买入明细是否存在：", ORDER_PLAN_FILE.exists())

if not CONFIG_CORE.exists():
    raise FileNotFoundError(CONFIG_CORE)

if not PRICES_FILE.exists():
    raise FileNotFoundError(PRICES_FILE)

core = pd.read_csv(CONFIG_CORE)
core.columns = [c.strip() for c in core.columns]

ticker_col = "ticker" if "ticker" in core.columns else "Ticker"
weight_col = "target_weight" if "target_weight" in core.columns else "weight"

core[ticker_col] = core[ticker_col].astype(str).str.upper().str.strip()

prices = read_price_table(PRICES_FILE)
print("价格数据维度：", prices.shape)
print("价格日期范围：", prices.index.min(), "到", prices.index.max())

suggested_amount_map = {}
if ORDER_PLAN_FILE.exists():
    order_plan = pd.read_csv(ORDER_PLAN_FILE)
    order_plan.columns = [c.strip() for c in order_plan.columns]
    if "ticker" in order_plan.columns and "suggested_buy_amount" in order_plan.columns:
        suggested_amount_map = dict(zip(
            order_plan["ticker"].astype(str).str.upper(),
            pd.to_numeric(order_plan["suggested_buy_amount"], errors="coerce")
        ))

rows = []

for _, cfg in core.iterrows():
    ticker = str(cfg[ticker_col]).upper().strip()
    col = get_col(prices, ticker)

    if col is None:
        rows.append({
            "date": TODAY,
            "ticker": ticker,
            "role": cfg.get("role", ""),
            "target_weight": cfg.get(weight_col, np.nan),
            "data_available": False,
            "notes": "价格文件中没有找到该 ETF"
        })
        continue

    close = prices[col].dropna().astype(float)

    if len(close) < 60:
        rows.append({
            "date": TODAY,
            "ticker": ticker,
            "role": cfg.get("role", ""),
            "target_weight": cfg.get(weight_col, np.nan),
            "data_available": False,
            "notes": "历史数据不足，暂不计算指标"
        })
        continue

    ma50 = close.rolling(50).mean()
    ma100 = close.rolling(100).mean()
    ma200 = close.rolling(200).mean()

    returns = close.pct_change()
    vol20 = returns.rolling(20).std() * np.sqrt(252)

    high_252 = close.tail(252).max()
    drawdown_252d = close.iloc[-1] / high_252 - 1 if high_252 and high_252 > 0 else np.nan

    try:
        rsi14 = RSIIndicator(close=close, window=14).rsi()
    except Exception:
        rsi14 = pd.Series(index=close.index, dtype=float)

    try:
        macd = MACD(close=close)
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()
        macd_hist = macd.macd_diff()
    except Exception:
        macd_line = pd.Series(index=close.index, dtype=float)
        macd_signal = pd.Series(index=close.index, dtype=float)
        macd_hist = pd.Series(index=close.index, dtype=float)

    try:
        bb = BollingerBands(close=close, window=20, window_dev=2)
        bb_high = bb.bollinger_hband()
        bb_mid = bb.bollinger_mavg()
        bb_low = bb.bollinger_lband()
        bb_width = bb.bollinger_wband()
        bb_percent_b = bb.bollinger_pband()
    except Exception:
        bb_high = pd.Series(index=close.index, dtype=float)
        bb_mid = pd.Series(index=close.index, dtype=float)
        bb_low = pd.Series(index=close.index, dtype=float)
        bb_width = pd.Series(index=close.index, dtype=float)
        bb_percent_b = pd.Series(index=close.index, dtype=float)

    latest_price = float(close.iloc[-1])
    latest_ma50 = safe_latest(ma50)
    latest_ma100 = safe_latest(ma100)
    latest_ma200 = safe_latest(ma200)

    row = {
        "date": close.index[-1].strftime("%Y-%m-%d"),
        "ticker": ticker,
        "role": cfg.get("role", ""),
        "target_weight": cfg.get(weight_col, np.nan),
        "data_available": True,
        "latest_price": latest_price,
        "ma50": latest_ma50,
        "ma100": latest_ma100,
        "ma200": latest_ma200,
        "above_50ma": bool(pd.notna(latest_ma50) and latest_price > latest_ma50),
        "above_100ma": bool(pd.notna(latest_ma100) and latest_price > latest_ma100),
        "above_200ma": bool(pd.notna(latest_ma200) and latest_price > latest_ma200),
        "ma200_slope_20d": pct_return(ma200.dropna(), 20),
        "return_1m": pct_return(close, 21),
        "return_3m": pct_return(close, 63),
        "return_6m": pct_return(close, 126),
        "return_12m": pct_return(close, 252),
        "vol20_annualized": safe_latest(vol20),
        "rsi14": safe_latest(rsi14),
        "macd": safe_latest(macd_line),
        "macd_signal": safe_latest(macd_signal),
        "macd_hist": safe_latest(macd_hist),
        "bb_high": safe_latest(bb_high),
        "bb_mid": safe_latest(bb_mid),
        "bb_low": safe_latest(bb_low),
        "bb_width": safe_latest(bb_width),
        "bb_percent_b": safe_latest(bb_percent_b),
        "high_252d": float(high_252),
        "drawdown_252d": float(drawdown_252d),
        "dd_10_price": float(high_252 * 0.90),
        "dd_15_price": float(high_252 * 0.85),
        "dd_25_price": float(high_252 * 0.75),
        "suggested_buy_amount": float(suggested_amount_map.get(ticker, 0.0)),
    }

    rows.append(row)

indicator_df = pd.DataFrame(rows)

available_mask = indicator_df.get("data_available", False) == True
if available_mask.any():
    scores = indicator_df.loc[available_mask].apply(calc_scores, axis=1)
    indicator_df = indicator_df.join(scores)

# 输出排序保持核心配置顺序
output_file = OUTPUT_DIR / f"market_indicator_score_{TODAY}.csv"
latest_output_file = OUTPUT_DIR / "market_indicator_score_latest.csv"

indicator_df.to_csv(output_file, index=False)
indicator_df.to_csv(latest_output_file, index=False)

print("")
print("===== Market Indicator Score =====")

display_cols = [
    "ticker", "role", "latest_price", "ma50", "ma200", "above_200ma",
    "rsi14", "return_3m", "return_6m", "vol20_annualized",
    "drawdown_252d", "market_score", "score_status",
    "reference_signal", "suggested_buy_amount"
]

print(indicator_df[display_cols])

report_file = REPORT_DIR / f"market_indicator_score_{TODAY}.md"
latest_report_file = REPORT_DIR / "market_indicator_score_latest.md"

report_df = indicator_df.copy()

for c in ["latest_price", "ma50", "ma100", "ma200", "rsi14", "market_score", "suggested_buy_amount"]:
    if c in report_df.columns:
        report_df[c] = report_df[c].apply(lambda x: fmt_num(x, 2) if pd.notna(x) else "")

for c in ["return_1m", "return_3m", "return_6m", "return_12m", "vol20_annualized", "drawdown_252d", "ma200_slope_20d"]:
    if c in report_df.columns:
        report_df[c] = report_df[c].apply(fmt_pct)

md_cols = [
    "ticker", "role", "latest_price", "ma50", "ma200", "above_200ma",
    "rsi14", "return_3m", "return_6m", "vol20_annualized",
    "drawdown_252d", "market_score", "score_status",
    "reference_signal", "suggested_buy_amount"
]

md = []
md.append(f"# Market Indicator Score V1")
md.append("")
md.append(f"Date: {TODAY}")
md.append("")
md.append("本报告为 V1.2 多指标评分的第一版测试输出。")
md.append("")
md.append("当前只生成指标和评分，不改变任何买入建议。")
md.append("")
md.append("评分维度包括：趋势、动量、波动风险、回撤位置、布林带位置。")
md.append("")
md.append(markdown_table(report_df, md_cols))
md.append("")
md.append("说明：")
md.append("")
md.append("- market_score 是 0 到 100 的辅助评分。")
md.append("- score_status 包括 strong / normal / neutral / weak / high_risk。")
md.append("- reference_signal 只是辅助观察信号，暂未接入正式入场规则。")
md.append("- SGOV 是现金/短债工具，不应按风险资产回撤买点解释。")
md.append("- 所有输出均为规则化监控信息，不构成投资建议，不自动交易。")
md.append("")

report_file.write_text("\n".join(md), encoding="utf-8")
latest_report_file.write_text("\n".join(md), encoding="utf-8")

print("")
print("指标评分已保存：", output_file)
print("最新指标评分已保存：", latest_output_file)
print("Markdown 报告已保存：", report_file)
print("最新 Markdown 报告已保存：", latest_report_file)
print("")
print("第 46 步完成：Market Indicator Score V1 生成成功。")
