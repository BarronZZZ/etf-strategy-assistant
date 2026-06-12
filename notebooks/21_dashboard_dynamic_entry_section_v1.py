from pathlib import Path
from html import escape
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

DYNAMIC_ENTRY_FILE = PROCESSED_DIR / "dynamic_entry_points_latest.csv"
DASHBOARD_LATEST = REPORT_DIR / "dashboard_latest.html"

SECTION_START = "<!-- V1.4_DYNAMIC_ENTRY_SECTION_START -->"
SECTION_END = "<!-- V1.4_DYNAMIC_ENTRY_SECTION_END -->"


def fmt_money(x):
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return ""


def fmt_pct(x):
    try:
        return f"{float(x) * 100:,.2f}%"
    except Exception:
        return ""


def fmt_num(x, digits=4):
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return ""


def flag_cn(flag):
    mapping = {
        "cost_ok": "成本可接受",
        "defer_small_amount": "金额太小，建议累积",
        "defer_high_fee_ratio": "手续费占比偏高",
        "no_trade_amount": "无建议买入金额",
    }
    return mapping.get(str(flag), str(flag))


def build_summary_cards(df: pd.DataFrame) -> str:
    current = df[df["entry_level"] == "current"].copy()

    cards = []

    for _, row in current.iterrows():
        ticker = row.get("ticker", "")
        latest_price = fmt_money(row.get("latest_price"))
        dd = fmt_pct(row.get("current_drawdown_252d"))
        fee = fmt_pct(row.get("fee_ratio"))
        flag = flag_cn(row.get("trade_cost_flag"))

        card = f"""
        <div class="v14-card">
          <div class="v14-card-title">{escape(str(ticker))}</div>
          <div class="v14-card-value">{latest_price}</div>
          <div class="v14-card-note">当前回撤 {dd}</div>
          <div class="v14-card-note">手续费占比 {fee} · {escape(flag)}</div>
        </div>
        """
        cards.append(card)

    return "\n".join(cards)


def build_dynamic_table(df: pd.DataFrame) -> str:
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
    ]

    table = df[keep_cols].copy()

    rename = {
        "ticker": "标的",
        "role": "角色",
        "entry_level": "入场层级",
        "latest_price": "当前价",
        "high_252d": "252日高点",
        "current_drawdown_252d": "当前回撤",
        "entry_price": "参考入场价",
        "gap_from_current_to_entry": "距离当前价",
        "return_to_252d_high_from_entry": "回到前高潜在收益",
        "suggested_buy_amount": "建议金额",
        "estimated_execution_price": "含滑点估算成交价",
        "estimated_shares": "估算股数",
        "fee_ratio": "手续费占比",
        "trade_cost_flag": "成本判断",
    }

    money_cols = [
        "latest_price",
        "high_252d",
        "entry_price",
        "suggested_buy_amount",
        "estimated_execution_price",
    ]

    pct_cols = [
        "current_drawdown_252d",
        "gap_from_current_to_entry",
        "return_to_252d_high_from_entry",
        "fee_ratio",
    ]

    for c in money_cols:
        if c in table.columns:
            table[c] = table[c].apply(fmt_money)

    for c in pct_cols:
        if c in table.columns:
            table[c] = table[c].apply(fmt_pct)

    if "estimated_shares" in table.columns:
        table["estimated_shares"] = table["estimated_shares"].apply(lambda x: fmt_num(x, 4))

    if "trade_cost_flag" in table.columns:
        table["trade_cost_flag"] = table["trade_cost_flag"].apply(flag_cn)

    table = table.rename(columns=rename)

    return table.to_html(index=False, escape=False, classes="v14-table")


def build_level_matrix(df: pd.DataFrame) -> str:
    matrix_df = df.copy()

    # SGOV / BIL 等现金或短债类工具不放入回撤点位矩阵，
    # 因为它们不应按股票型 ETF 的 -5%、-10%、-15%、-25% 回撤点位解释。
    if "is_cash_like" in matrix_df.columns:
        matrix_df = matrix_df[~matrix_df["is_cash_like"].astype(bool)].copy()

    if matrix_df.empty:
        return "<p>当前没有适合展示回撤点位矩阵的风险资产。</p>"

    pivot_price = matrix_df.pivot(index="ticker", columns="entry_level", values="entry_price")
    pivot_return = matrix_df.pivot(index="ticker", columns="entry_level", values="return_to_252d_high_from_entry")

    order = ["current", "dd_5", "dd_10", "dd_15", "dd_25"]

    rows = []

    for ticker in pivot_price.index:
        row = {"标的": ticker}
        for level in order:
            if level in pivot_price.columns:
                price = pivot_price.loc[ticker, level]
                ret = pivot_return.loc[ticker, level]
                row[f"{level} 价格"] = "" if pd.isna(price) else fmt_money(price)
                row[f"{level} 回前高收益"] = "" if pd.isna(ret) else fmt_pct(ret)
        rows.append(row)

    out = pd.DataFrame(rows)
    return out.to_html(index=False, escape=False, classes="v14-table")


def build_section(df: pd.DataFrame) -> tuple[str, str]:
    report_date = str(df["date"].iloc[0]) if "date" in df.columns and len(df) else ""
    market_date = str(df["market_date"].iloc[0]) if "market_date" in df.columns and len(df) else ""

    cards = build_summary_cards(df)
    matrix = build_level_matrix(df)
    table = build_dynamic_table(df)

    section = f"""
{SECTION_START}
<style>
.v14-dynamic-section {{
  margin-top: 32px;
  padding: 24px;
  border-radius: 18px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.v14-dynamic-section h2 {{
  margin-top: 0;
  font-size: 24px;
}}
.v14-subtitle {{
  color: #9a3412;
  margin-bottom: 18px;
}}
.v14-card-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}}
.v14-card {{
  background: white;
  border: 1px solid #fed7aa;
  border-radius: 14px;
  padding: 16px;
}}
.v14-card-title {{
  font-size: 13px;
  color: #9a3412;
  margin-bottom: 8px;
}}
.v14-card-value {{
  font-size: 22px;
  font-weight: 700;
  color: #7c2d12;
}}
.v14-card-note {{
  font-size: 12px;
  color: #9a3412;
  margin-top: 6px;
}}
.v14-table {{
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  font-size: 12px;
  margin-bottom: 20px;
}}
.v14-table th {{
  background: #ffedd5;
  color: #7c2d12;
  padding: 9px;
  text-align: left;
}}
.v14-table td {{
  padding: 8px 9px;
  border-bottom: 1px solid #fed7aa;
}}
.v14-note {{
  font-size: 12px;
  color: #9a3412;
  margin-top: 14px;
}}
</style>

<section class="v14-dynamic-section">
  <h2>V1.4 动态入场点位收益率</h2>
  <div class="v14-subtitle">
    报告日期 {escape(report_date)}，市场价格日期 {escape(market_date)}。
    本模块根据 252 日高点、当前价、回撤点位、手续费和滑点，计算不同入场点的参考收益率。
  </div>

  <div class="v14-card-grid">
    {cards}
  </div>

  <h3>点位矩阵：不同入场价与回到前高潜在收益</h3>
  {matrix}

  <h3>动态入场点位明细</h3>
  {table}

  <div class="v14-note">
    说明：本模块只用于观察点位、潜在收益率和交易成本影响，不构成投资建议，不自动交易。SGOV / BIL 等现金或短债类工具不进入回撤点位矩阵，只保留 current 当前价和手续费判断。
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
    print("动态入场点位文件是否存在：", DYNAMIC_ENTRY_FILE.exists())
    print("Dashboard latest 是否存在：", DASHBOARD_LATEST.exists())

    if not DYNAMIC_ENTRY_FILE.exists():
        raise FileNotFoundError("缺少 dynamic_entry_points_latest.csv，请先运行 notebooks/20_dynamic_entry_points_v1.py")

    df = pd.read_csv(DYNAMIC_ENTRY_FILE)

    section, report_date = build_section(df)

    dashboard_date = REPORT_DIR / f"dashboard_{report_date}.html"

    update_dashboard(DASHBOARD_LATEST, section)
    update_dashboard(dashboard_date, section)

    print("")
    print("第 68 步完成：Dashboard 已接入 V1.4 动态入场点位模块。")


if __name__ == "__main__":
    main()
