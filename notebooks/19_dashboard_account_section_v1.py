from pathlib import Path
from datetime import datetime
from html import escape
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

ACCOUNT_SNAPSHOT_FILE = PROCESSED_DIR / "account_snapshot_latest.csv"
CURRENT_POSITIONS_FILE = PROCESSED_DIR / "current_positions.csv"

DASHBOARD_LATEST = REPORT_DIR / "dashboard_latest.html"

SECTION_START = "<!-- V1.3_ACCOUNT_SECTION_START -->"
SECTION_END = "<!-- V1.3_ACCOUNT_SECTION_END -->"


def fmt_money(x):
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return "$0.00"


def fmt_pct(x):
    try:
        return f"{float(x) * 100:,.2f}%"
    except Exception:
        return "0.00%"


def fmt_num(x, digits=4):
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return "0.0000"


def build_card(title, value, note=""):
    return f"""
    <div class="v13-card">
      <div class="v13-card-title">{escape(str(title))}</div>
      <div class="v13-card-value">{escape(str(value))}</div>
      <div class="v13-card-note">{escape(str(note))}</div>
    </div>
    """


def build_positions_table(positions: pd.DataFrame) -> str:
    if positions.empty:
        return "<p>当前没有持仓记录。</p>"

    cols = [
        "ticker",
        "role",
        "target_weight",
        "shares",
        "avg_cost",
        "last_price",
        "market_value",
        "cost_basis",
        "unrealized_pnl",
        "unrealized_return",
        "actual_weight_total_equity",
        "weight_gap_vs_target",
    ]

    available_cols = [c for c in cols if c in positions.columns]
    df = positions[available_cols].copy()

    rename_map = {
        "ticker": "标的",
        "role": "角色",
        "target_weight": "目标权重",
        "shares": "持仓股数",
        "avg_cost": "平均成本",
        "last_price": "最新价格",
        "market_value": "当前市值",
        "cost_basis": "持仓成本",
        "unrealized_pnl": "浮盈亏",
        "unrealized_return": "浮盈亏率",
        "actual_weight_total_equity": "总资产权重",
        "weight_gap_vs_target": "相对目标差异",
    }

    money_cols = ["avg_cost", "last_price", "market_value", "cost_basis", "unrealized_pnl"]
    pct_cols = ["target_weight", "unrealized_return", "actual_weight_total_equity", "weight_gap_vs_target"]

    for c in money_cols:
        if c in df.columns:
            df[c] = df[c].apply(fmt_money)

    for c in pct_cols:
        if c in df.columns:
            df[c] = df[c].apply(fmt_pct)

    if "shares" in df.columns:
        df["shares"] = df["shares"].apply(lambda x: fmt_num(x, 4))

    df = df.rename(columns=rename_map)

    return df.to_html(index=False, escape=False, classes="v13-table")


def build_section(snapshot: pd.DataFrame, positions: pd.DataFrame) -> tuple[str, str]:
    row = snapshot.iloc[0].to_dict()

    report_date = str(row.get("date", datetime.now().strftime("%Y-%m-%d")))
    market_date = str(row.get("market_date", report_date))

    position_status = str(row.get("position_status", "unknown"))
    cash_balance = row.get("cash_balance", 0)
    total_market_value = row.get("total_market_value", 0)
    total_equity = row.get("total_equity", 0)
    unrealized_pnl = row.get("unrealized_pnl", 0)
    realized_pnl = row.get("realized_pnl", 0)
    total_pnl = row.get("total_pnl", 0)
    cash_weight = row.get("cash_weight", 0)
    invested_weight = row.get("invested_weight", 0)
    trade_count = row.get("trade_count", 0)
    total_commission = row.get("total_commission", 0)

    cards = "\n".join([
        build_card("账户状态", position_status, f"报告日期 {report_date}"),
        build_card("现金余额", fmt_money(cash_balance), fmt_pct(cash_weight)),
        build_card("持仓市值", fmt_money(total_market_value), fmt_pct(invested_weight)),
        build_card("总资产", fmt_money(total_equity), f"市场日期 {market_date}"),
        build_card("浮盈亏", fmt_money(unrealized_pnl), "未实现盈亏"),
        build_card("已实现盈亏", fmt_money(realized_pnl), "卖出后确认"),
        build_card("总盈亏", fmt_money(total_pnl), "浮盈亏 + 已实现盈亏"),
        build_card("累计手续费", fmt_money(total_commission), f"交易笔数 {int(float(trade_count))}"),
    ])

    positions_table = build_positions_table(positions)

    section = f"""
{SECTION_START}
<style>
.v13-account-section {{
  margin-top: 32px;
  padding: 24px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.v13-account-section h2 {{
  margin-top: 0;
  font-size: 24px;
}}
.v13-subtitle {{
  color: #64748b;
  margin-bottom: 18px;
}}
.v13-card-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}}
.v13-card {{
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
}}
.v13-card-title {{
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}}
.v13-card-value {{
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}}
.v13-card-note {{
  font-size: 12px;
  color: #94a3b8;
  margin-top: 6px;
}}
.v13-table {{
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  font-size: 13px;
}}
.v13-table th {{
  background: #e2e8f0;
  color: #0f172a;
  padding: 10px;
  text-align: left;
}}
.v13-table td {{
  padding: 9px 10px;
  border-bottom: 1px solid #e5e7eb;
}}
.v13-note {{
  font-size: 12px;
  color: #64748b;
  margin-top: 14px;
}}
</style>

<section class="v13-account-section">
  <h2>V1.3 实仓账户跟踪</h2>
  <div class="v13-subtitle">
    根据 <code>data/manual/trade_log.csv</code> 自动计算现金、持仓、市值、浮盈亏和手续费。
  </div>

  <div class="v13-card-grid">
    {cards}
  </div>

  <h3>当前持仓明细</h3>
  {positions_table}

  <div class="v13-note">
    说明：本模块只用于账户记录和风险监控，不构成投资建议，不自动交易。所有买入和卖出必须人工确认。
  </div>
</section>
{SECTION_END}
"""

    return section, report_date


def inject_section(html: str, section: str) -> str:
    if SECTION_START in html and SECTION_END in html:
        before = html.split(SECTION_START)[0]
        after = html.split(SECTION_END)[1]
        return before + section + after

    if "</body>" in html:
        return html.replace("</body>", section + "\n</body>")

    return html + "\n" + section


def update_dashboard(path: Path, section: str):
    if not path.exists():
        print("跳过，Dashboard 不存在：", path)
        return

    html = path.read_text(encoding="utf-8")
    updated = inject_section(html, section)
    path.write_text(updated, encoding="utf-8")
    print("已更新 Dashboard：", path)


def main():
    print("账户快照文件是否存在：", ACCOUNT_SNAPSHOT_FILE.exists())
    print("当前持仓文件是否存在：", CURRENT_POSITIONS_FILE.exists())
    print("Dashboard latest 是否存在：", DASHBOARD_LATEST.exists())

    if not ACCOUNT_SNAPSHOT_FILE.exists():
        raise FileNotFoundError("缺少 account_snapshot_latest.csv，请先运行 notebooks/17_portfolio_accounting_v1.py")

    if not CURRENT_POSITIONS_FILE.exists():
        raise FileNotFoundError("缺少 current_positions.csv，请先运行 notebooks/17_portfolio_accounting_v1.py")

    snapshot = pd.read_csv(ACCOUNT_SNAPSHOT_FILE)
    positions = pd.read_csv(CURRENT_POSITIONS_FILE)

    section, report_date = build_section(snapshot, positions)

    dashboard_date = REPORT_DIR / f"dashboard_{report_date}.html"

    update_dashboard(DASHBOARD_LATEST, section)
    update_dashboard(dashboard_date, section)

    print("")
    print("第 64 步完成：Dashboard 已接入 V1.3 实仓账户跟踪模块。")


if __name__ == "__main__":
    main()
