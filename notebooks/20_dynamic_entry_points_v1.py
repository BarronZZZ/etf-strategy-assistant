from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]

CONFIG_DIR = PROJECT_DIR / "config"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

UNIVERSE_FILE = CONFIG_DIR / "etf_universe_usd.csv"
TRADE_COSTS_FILE = CONFIG_DIR / "trade_costs.csv"
PRICE_FILE = PROCESSED_DIR / "latest_market_prices.csv"
ORDER_PLAN_FILE = PROCESSED_DIR / "latest_entry_order_plan.csv"

OUTPUT_CSV = PROCESSED_DIR / "dynamic_entry_points_latest.csv"
OUTPUT_MD = REPORT_DIR / "dynamic_entry_points_latest.md"

TODAY = datetime.now().strftime("%Y-%m-%d")


def to_float(x, default=0.0):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def read_trade_costs(path: Path) -> dict:
    df = pd.read_csv(path)
    cfg = dict(zip(df["item"], df["value"]))

    return {
        "commission_per_order": to_float(cfg.get("commission_per_order", 9.90), 9.90),
        "default_slippage_bps": to_float(cfg.get("default_slippage_bps", 5), 5),
        "min_trade_amount": to_float(cfg.get("min_trade_amount", 1000), 1000),
        "max_fee_ratio": to_float(cfg.get("max_fee_ratio", 0.005), 0.005),
        "allow_fractional_shares": str(cfg.get("allow_fractional_shares", "true")).lower() == "true",
    }


def read_prices(path: Path) -> tuple[pd.DataFrame, str]:
    prices = pd.read_csv(path)

    first_col = prices.columns[0]
    if first_col.lower() in ["date", "unnamed: 0"]:
        prices[first_col] = pd.to_datetime(prices[first_col])
        prices = prices.set_index(first_col)

    prices = prices.dropna(how="all")

    try:
        market_date = pd.to_datetime(prices.index[-1]).strftime("%Y-%m-%d")
    except Exception:
        market_date = TODAY

    return prices, market_date


def read_universe(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    lower_map = {c.lower(): c for c in df.columns}

    if "ticker" not in lower_map:
        raise ValueError("etf_universe_usd.csv 缺少 ticker 列")

    df = df.rename(columns={lower_map["ticker"]: "ticker"})

    if "role" not in df.columns:
        df["role"] = ""

    if "target_weight" not in df.columns:
        if "weight" in lower_map:
            df = df.rename(columns={lower_map["weight"]: "target_weight"})
        else:
            df["target_weight"] = 0.0

    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce").fillna(0.0)

    return df


def read_order_plan(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["ticker", "suggested_buy_amount"])

    df = pd.read_csv(path)

    lower_map = {c.lower(): c for c in df.columns}

    if "ticker" not in lower_map:
        return pd.DataFrame(columns=["ticker", "suggested_buy_amount"])

    df = df.rename(columns={lower_map["ticker"]: "ticker"})
    df["ticker"] = df["ticker"].astype(str).str.upper()

    amount_candidates = [
        "suggested_buy_amount",
        "suggested_amount",
        "target_amount",
        "buy_amount",
        "amount",
    ]

    amount_col = None
    for c in amount_candidates:
        if c in lower_map:
            amount_col = lower_map[c]
            break

    if amount_col is None:
        df["suggested_buy_amount"] = 0.0
    else:
        df["suggested_buy_amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0.0)

    return df[["ticker", "suggested_buy_amount"]]


def estimate_trade(entry_price, suggested_amount, costs):
    commission = costs["commission_per_order"]
    slippage_bps = costs["default_slippage_bps"]
    min_trade_amount = costs["min_trade_amount"]
    max_fee_ratio = costs["max_fee_ratio"]
    allow_fractional = costs["allow_fractional_shares"]

    if suggested_amount <= 0 or entry_price <= 0:
        return {
            "estimated_execution_price": np.nan,
            "estimated_shares": 0.0,
            "estimated_gross_cost": 0.0,
            "estimated_total_cost": 0.0,
            "fee_ratio": np.nan,
            "trade_cost_flag": "no_trade_amount",
            "trade_cost_note": "没有建议买入金额",
        }

    execution_price = entry_price * (1 + slippage_bps / 10000)
    available_for_shares = max(suggested_amount - commission, 0)

    if execution_price > 0:
        shares = available_for_shares / execution_price
    else:
        shares = 0.0

    if not allow_fractional:
        shares = np.floor(shares)

    gross_cost = shares * execution_price
    total_cost = gross_cost + commission
    fee_ratio = commission / suggested_amount if suggested_amount > 0 else np.nan

    if suggested_amount < min_trade_amount:
        flag = "defer_small_amount"
        note = f"建议金额低于最低交易金额 ${min_trade_amount:,.0f}"
    elif fee_ratio > max_fee_ratio:
        flag = "defer_high_fee_ratio"
        note = f"手续费占比 {fee_ratio:.2%} 高于上限 {max_fee_ratio:.2%}"
    else:
        flag = "cost_ok"
        note = "交易成本可接受"

    return {
        "estimated_execution_price": execution_price,
        "estimated_shares": shares,
        "estimated_gross_cost": gross_cost,
        "estimated_total_cost": total_cost,
        "fee_ratio": fee_ratio,
        "trade_cost_flag": flag,
        "trade_cost_note": note,
    }


def main():
    print("项目路径：", PROJECT_DIR)
    print("核心配置是否存在：", UNIVERSE_FILE.exists())
    print("交易成本配置是否存在：", TRADE_COSTS_FILE.exists())
    print("价格文件是否存在：", PRICE_FILE.exists())
    print("建议买入明细是否存在：", ORDER_PLAN_FILE.exists())

    universe = read_universe(UNIVERSE_FILE)
    costs = read_trade_costs(TRADE_COSTS_FILE)
    prices, market_date = read_prices(PRICE_FILE)
    order_plan = read_order_plan(ORDER_PLAN_FILE)

    print("")
    print("===== 交易成本配置 =====")
    print(costs)

    print("")
    print("价格数据维度：", prices.shape)
    print("价格日期：", market_date)

    order_map = dict(zip(order_plan["ticker"], order_plan["suggested_buy_amount"]))

    rows = []

    risk_asset_drawdown_levels = [
        ("current", None),
        ("dd_5", 0.05),
        ("dd_10", 0.10),
        ("dd_15", 0.15),
        ("dd_25", 0.25),
    ]

    cash_like_drawdown_levels = [
        ("current", None),
    ]

    cash_like_tickers = {"SGOV", "BIL"}

    for _, u in universe.iterrows():
        ticker = str(u["ticker"]).upper()
        role = str(u.get("role", ""))
        target_weight = to_float(u.get("target_weight", 0.0))

        is_cash_like = (
            ticker in cash_like_tickers
            or "现金" in role
            or "短债" in role
            or "cash" in role.lower()
            or "treasury" in role.lower()
        )

        if is_cash_like:
            drawdown_levels = cash_like_drawdown_levels
        else:
            drawdown_levels = risk_asset_drawdown_levels

        if ticker not in prices.columns:
            print(f"跳过 {ticker}：价格数据中不存在")
            continue

        s = pd.to_numeric(prices[ticker], errors="coerce").dropna()

        if len(s) == 0:
            print(f"跳过 {ticker}：无有效价格")
            continue

        latest_price = float(s.iloc[-1])
        last_252 = s.tail(252)
        high_252d = float(last_252.max())
        low_252d = float(last_252.min())

        current_drawdown = latest_price / high_252d - 1 if high_252d > 0 else 0.0
        return_to_high_from_current = high_252d / latest_price - 1 if latest_price > 0 else 0.0

        suggested_amount = to_float(order_map.get(ticker, 0.0))

        for level_name, dd in drawdown_levels:
            if level_name == "current":
                entry_price = latest_price
            else:
                entry_price = high_252d * (1 - dd)

            gap_from_current = entry_price / latest_price - 1 if latest_price > 0 else 0.0
            return_to_high = high_252d / entry_price - 1 if entry_price > 0 else 0.0

            trade_est = estimate_trade(entry_price, suggested_amount, costs)

            rows.append({
                "date": TODAY,
                "market_date": market_date,
                "ticker": ticker,
                "role": role,
                "target_weight": target_weight,
                "is_cash_like": is_cash_like,
                "entry_level": level_name,
                "latest_price": latest_price,
                "high_252d": high_252d,
                "low_252d": low_252d,
                "current_drawdown_252d": current_drawdown,
                "entry_price": entry_price,
                "gap_from_current_to_entry": gap_from_current,
                "return_to_252d_high_from_entry": return_to_high,
                "return_to_252d_high_from_current": return_to_high_from_current,
                "suggested_buy_amount": suggested_amount,
                **trade_est,
            })

    out = pd.DataFrame(rows)

    out.to_csv(OUTPUT_CSV, index=False)

    print("")
    print("===== 动态入场点位收益率表 =====")
    display_cols = [
        "ticker",
        "entry_level",
        "latest_price",
        "high_252d",
        "current_drawdown_252d",
        "entry_price",
        "gap_from_current_to_entry",
        "return_to_252d_high_from_entry",
        "suggested_buy_amount",
        "estimated_execution_price",
        "estimated_shares",
        "fee_ratio",
        "trade_cost_flag",
    ]
    print(out[display_cols])

    md = []
    md.append("# Dynamic Entry Points V1")
    md.append("")
    md.append(f"Date: {TODAY}")
    md.append(f"Market date: {market_date}")
    md.append("")
    md.append("本报告列出核心 ETF 在不同回撤点位下的参考入场价格，以及从该入场点回到 252 日高点的潜在收益率。")
    md.append("")
    md.append("交易成本假设：")
    md.append(f"- Commission per order: ${costs['commission_per_order']:,.2f}")
    md.append(f"- Default slippage: {costs['default_slippage_bps']:.1f} bps")
    md.append(f"- Minimum trade amount: ${costs['min_trade_amount']:,.2f}")
    md.append(f"- Max fee ratio: {costs['max_fee_ratio']:.2%}")
    md.append("")
    md.append("## Dynamic Entry Table")
    md.append("")

    md_table = out.copy()

    pct_cols = [
        "target_weight",
        "current_drawdown_252d",
        "gap_from_current_to_entry",
        "return_to_252d_high_from_entry",
        "return_to_252d_high_from_current",
        "fee_ratio",
    ]

    money_cols = [
        "latest_price",
        "high_252d",
        "low_252d",
        "entry_price",
        "suggested_buy_amount",
        "estimated_execution_price",
        "estimated_gross_cost",
        "estimated_total_cost",
    ]

    for c in pct_cols:
        if c in md_table.columns:
            md_table[c] = md_table[c].apply(lambda x: "" if pd.isna(x) else f"{float(x):.2%}")

    for c in money_cols:
        if c in md_table.columns:
            md_table[c] = md_table[c].apply(lambda x: "" if pd.isna(x) else f"${float(x):,.2f}")

    if "estimated_shares" in md_table.columns:
        md_table["estimated_shares"] = md_table["estimated_shares"].apply(lambda x: f"{float(x):,.4f}")

    keep_cols = [
        "ticker",
        "role",
        "entry_level",
        "latest_price",
        "high_252d",
        "current_drawdown_252d",
        "entry_price",
        "gap_from_current_to_entry",
        "return_to_252d_high_from_entry",
        "suggested_buy_amount",
        "estimated_execution_price",
        "estimated_shares",
        "fee_ratio",
        "trade_cost_flag",
        "trade_cost_note",
    ]

    md.append(md_table[keep_cols].to_markdown(index=False))
    md.append("")
    md.append("说明：本表只用于观察入场点位和交易成本影响，不构成投资建议，不自动交易。所有交易必须人工确认。SGOV/BIL 等现金或短债类工具只显示 current 当前价和手续费判断，不使用股票型 ETF 的 -5%、-10%、-15%、-25% 回撤点位。")

    OUTPUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("")
    print("动态入场点位 CSV 已保存：", OUTPUT_CSV)
    print("动态入场点位 Markdown 已保存：", OUTPUT_MD)
    print("")
    print("第 67 步完成：动态入场点位收益率脚本运行成功。")


if __name__ == "__main__":
    main()
