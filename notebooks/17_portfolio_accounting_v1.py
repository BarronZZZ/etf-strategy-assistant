from pathlib import Path
from datetime import datetime
import argparse
import pandas as pd
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]

CONFIG_DIR = PROJECT_DIR / "config"
MANUAL_DIR = PROJECT_DIR / "data" / "manual"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNT_FILE = CONFIG_DIR / "account_status_usd.csv"
UNIVERSE_FILE = CONFIG_DIR / "etf_universe_usd.csv"
TRADE_LOG_FILE = MANUAL_DIR / "trade_log.csv"
PRICE_FILE = PROCESSED_DIR / "latest_market_prices.csv"

CURRENT_POSITIONS_FILE = PROCESSED_DIR / "current_positions.csv"
ACCOUNT_SNAPSHOT_FILE = PROCESSED_DIR / "account_snapshot_latest.csv"
PORTFOLIO_HISTORY_FILE = PROCESSED_DIR / "portfolio_history.csv"

REPORT_FILE = REPORT_DIR / "portfolio_accounting_latest.md"

TODAY = datetime.now().strftime("%Y-%m-%d")


def read_account_status(path: Path) -> dict:
    df = pd.read_csv(path)
    result = {}
    for _, row in df.iterrows():
        result[str(row["item"])] = row["value"]
    return result


def to_float(x, default=0.0):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def read_latest_prices(path: Path) -> tuple[pd.Series, str]:
    prices = pd.read_csv(path)

    first_col = prices.columns[0]
    if first_col.lower() in ["date", "unnamed: 0"]:
        prices[first_col] = pd.to_datetime(prices[first_col])
        prices = prices.set_index(first_col)

    prices = prices.dropna(how="all")
    latest_row = prices.iloc[-1]

    try:
        market_date = pd.to_datetime(prices.index[-1]).strftime("%Y-%m-%d")
    except Exception:
        market_date = TODAY

    return latest_row, market_date


def read_universe(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # 兼容不同列名
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

    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce").fillna(0.0)

    return df


def read_trade_log(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"交易记录文件不存在：{path}")

    df = pd.read_csv(path)

    required_cols = [
        "trade_id", "trade_date", "ticker", "side", "shares",
        "order_price", "executed_price", "gross_amount",
        "commission", "slippage_bps", "net_cash_flow",
        "account", "currency", "notes"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"trade_log.csv 缺少字段：{missing}")

    if len(df) == 0:
        return df

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["side"] = df["side"].astype(str).str.upper()

    numeric_cols = [
        "shares", "order_price", "executed_price",
        "gross_amount", "commission", "slippage_bps", "net_cash_flow"
    ]

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values(["trade_date", "trade_id"]).reset_index(drop=True)

    return df


def build_positions(universe: pd.DataFrame, trade_log: pd.DataFrame, latest_prices: pd.Series) -> tuple[pd.DataFrame, float, float, float]:
    rows = []
    realized_pnl_total = 0.0
    total_commission = 0.0
    total_trade_gross = 0.0

    for _, u in universe.iterrows():
        ticker = str(u["ticker"]).upper()
        role = u.get("role", "")
        target_weight = to_float(u.get("target_weight", 0.0))

        ticker_trades = trade_log[trade_log["ticker"] == ticker].copy() if len(trade_log) > 0 else pd.DataFrame()

        shares = 0.0
        cost_basis = 0.0
        realized_pnl = 0.0
        commission_sum = 0.0
        gross_sum = 0.0

        if len(ticker_trades) > 0:
            for _, tr in ticker_trades.iterrows():
                side = str(tr["side"]).upper()
                tr_shares = to_float(tr["shares"])
                executed_price = to_float(tr["executed_price"])
                gross_amount = to_float(tr["gross_amount"], tr_shares * executed_price)
                commission = to_float(tr["commission"])

                if gross_amount == 0 and tr_shares > 0 and executed_price > 0:
                    gross_amount = tr_shares * executed_price

                commission_sum += commission
                gross_sum += gross_amount

                if side == "BUY":
                    shares += tr_shares
                    cost_basis += gross_amount + commission

                elif side == "SELL":
                    sell_shares = min(tr_shares, shares)
                    avg_cost_before = cost_basis / shares if shares > 0 else 0.0
                    cost_reduced = avg_cost_before * sell_shares
                    sale_proceeds = gross_amount - commission
                    realized_pnl += sale_proceeds - cost_reduced

                    shares -= sell_shares
                    cost_basis -= cost_reduced

                else:
                    raise ValueError(f"{ticker} 存在未知 side：{side}")

        last_price = to_float(latest_prices.get(ticker, np.nan), np.nan)
        market_value = shares * last_price if not pd.isna(last_price) else 0.0
        avg_cost = cost_basis / shares if shares > 0 else 0.0
        unrealized_pnl = market_value - cost_basis
        unrealized_return = unrealized_pnl / cost_basis if cost_basis > 0 else 0.0

        total_commission += commission_sum
        total_trade_gross += gross_sum
        realized_pnl_total += realized_pnl

        rows.append({
            "date": TODAY,
            "ticker": ticker,
            "role": role,
            "target_weight": target_weight,
            "shares": shares,
            "avg_cost": avg_cost,
            "last_price": last_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_return": unrealized_return,
            "realized_pnl": realized_pnl,
            "commission_paid": commission_sum,
        })

    positions = pd.DataFrame(rows)

    total_market_value = positions["market_value"].sum()

    if total_market_value > 0:
        positions["actual_weight_in_positions"] = positions["market_value"] / total_market_value
    else:
        positions["actual_weight_in_positions"] = 0.0

    return positions, realized_pnl_total, total_commission, total_trade_gross


def append_history(snapshot: pd.DataFrame, path: Path):
    if path.exists():
        hist = pd.read_csv(path)
        hist = hist[hist["date"] != snapshot.iloc[0]["date"]]
        hist = pd.concat([hist, snapshot], ignore_index=True)
    else:
        hist = snapshot.copy()

    hist = hist.sort_values("date").reset_index(drop=True)
    hist.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Portfolio accounting for ETF Strategy Assistant")
    parser.add_argument(
        "--trade-log",
        default=str(TRADE_LOG_FILE),
        help="交易记录文件路径。默认读取 data/manual/trade_log.csv"
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="测试输出后缀。例如 test_initial_buy。为空时写入正式 latest 文件。"
    )
    args = parser.parse_args()

    trade_log_file = Path(args.trade_log)
    output_suffix = str(args.output_suffix).strip()

    if output_suffix:
        current_positions_file = PROCESSED_DIR / f"current_positions_{output_suffix}.csv"
        account_snapshot_file = PROCESSED_DIR / f"account_snapshot_{output_suffix}.csv"
        portfolio_history_file = PROCESSED_DIR / f"portfolio_history_{output_suffix}.csv"
        report_file = REPORT_DIR / f"portfolio_accounting_{output_suffix}.md"
        run_mode = "test"
    else:
        current_positions_file = CURRENT_POSITIONS_FILE
        account_snapshot_file = ACCOUNT_SNAPSHOT_FILE
        portfolio_history_file = PORTFOLIO_HISTORY_FILE
        report_file = REPORT_FILE
        run_mode = "live"

    print("项目路径：", PROJECT_DIR)
    print("运行模式：", run_mode)
    print("账户配置是否存在：", ACCOUNT_FILE.exists())
    print("核心配置是否存在：", UNIVERSE_FILE.exists())
    print("交易记录文件：", trade_log_file)
    print("交易记录是否存在：", trade_log_file.exists())
    print("价格文件是否存在：", PRICE_FILE.exists())

    account = read_account_status(ACCOUNT_FILE)
    universe = read_universe(UNIVERSE_FILE)
    trade_log = read_trade_log(trade_log_file)
    latest_prices, market_date = read_latest_prices(PRICE_FILE)

    starting_cash = to_float(account.get("total_planned_capital", account.get("current_cash", 0.0)))
    account_currency = account.get("account_currency", "USD")

    print("")
    print("===== 基础账户信息 =====")
    print("账户货币：", account_currency)
    print("计划总资金：", starting_cash)
    print("价格日期：", market_date)
    print("交易记录行数：", len(trade_log))

    positions, realized_pnl_total, total_commission, total_trade_gross = build_positions(
        universe=universe,
        trade_log=trade_log,
        latest_prices=latest_prices,
    )

    if len(trade_log) > 0:
        cash_change = 0.0

        for _, tr in trade_log.iterrows():
            side = str(tr["side"]).upper()
            shares = to_float(tr["shares"])
            executed_price = to_float(tr["executed_price"])
            gross_amount = to_float(tr["gross_amount"], shares * executed_price)
            commission = to_float(tr["commission"])
            net_cash_flow = to_float(tr["net_cash_flow"], np.nan)

            if pd.isna(net_cash_flow):
                if side == "BUY":
                    net_cash_flow = -(gross_amount + commission)
                elif side == "SELL":
                    net_cash_flow = gross_amount - commission
                else:
                    net_cash_flow = 0.0

            cash_change += net_cash_flow
    else:
        cash_change = 0.0

    cash_balance = starting_cash + cash_change
    total_market_value = positions["market_value"].sum()
    total_cost_basis = positions["cost_basis"].sum()
    unrealized_pnl = positions["unrealized_pnl"].sum()
    total_equity = cash_balance + total_market_value

    if total_equity > 0:
        cash_weight = cash_balance / total_equity
        invested_weight = total_market_value / total_equity
    else:
        cash_weight = 0.0
        invested_weight = 0.0

    if total_market_value > 0:
        position_status = "invested"
    elif len(trade_log) == 0:
        position_status = "empty"
    else:
        position_status = "no_current_position"

    positions["actual_weight_total_equity"] = positions["market_value"] / total_equity if total_equity > 0 else 0.0
    positions["weight_gap_vs_target"] = positions["actual_weight_total_equity"] - positions["target_weight"]

    snapshot = pd.DataFrame([{
        "date": TODAY,
        "market_date": market_date,
        "account_currency": account_currency,
        "position_status": position_status,
        "starting_cash": starting_cash,
        "cash_balance": cash_balance,
        "cash_change_from_trades": cash_change,
        "total_market_value": total_market_value,
        "total_cost_basis": total_cost_basis,
        "total_equity": total_equity,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl_total,
        "total_pnl": unrealized_pnl + realized_pnl_total,
        "cash_weight": cash_weight,
        "invested_weight": invested_weight,
        "trade_count": len(trade_log),
        "total_commission": total_commission,
        "total_trade_gross": total_trade_gross,
    }])

    positions.to_csv(current_positions_file, index=False)
    snapshot.to_csv(account_snapshot_file, index=False)
    append_history(snapshot, portfolio_history_file)

    print("")
    print("===== 当前持仓 =====")
    print(positions[[
        "ticker", "shares", "avg_cost", "last_price",
        "market_value", "cost_basis", "unrealized_pnl",
        "unrealized_return", "actual_weight_total_equity",
        "weight_gap_vs_target"
    ]])

    print("")
    print("===== 账户快照 =====")
    print(snapshot)

    md = []
    md.append("# Portfolio Accounting V1")
    md.append("")
    md.append(f"Date: {TODAY}")
    md.append(f"Market date: {market_date}")
    md.append("")
    md.append("本报告根据实仓交易记录 trade_log.csv 自动计算现金、持仓、市值和浮盈亏。")
    md.append("")
    md.append("## Account Snapshot")
    md.append("")
    md.append(f"- Position status: {position_status}")
    md.append(f"- Starting cash: ${starting_cash:,.2f}")
    md.append(f"- Cash balance: ${cash_balance:,.2f}")
    md.append(f"- Total market value: ${total_market_value:,.2f}")
    md.append(f"- Total equity: ${total_equity:,.2f}")
    md.append(f"- Total cost basis: ${total_cost_basis:,.2f}")
    md.append(f"- Unrealized PnL: ${unrealized_pnl:,.2f}")
    md.append(f"- Realized PnL: ${realized_pnl_total:,.2f}")
    md.append(f"- Total commission: ${total_commission:,.2f}")
    md.append(f"- Trade count: {len(trade_log)}")
    md.append("")
    md.append("## Current Positions")
    md.append("")
    md.append(positions.to_markdown(index=False))
    md.append("")
    md.append("说明：本报告只用于记录和监控，不构成投资建议，不自动交易。")

    report_file.write_text("\n".join(md), encoding="utf-8")

    print("")
    print("当前持仓已保存：", current_positions_file)
    print("账户快照已保存：", account_snapshot_file)
    print("账户历史已保存：", portfolio_history_file)
    print("Markdown 报告已保存：", report_file)
    print("")
    print("第 61 步完成：实仓持仓与现金余额计算脚本运行成功。")


if __name__ == "__main__":
    main()
