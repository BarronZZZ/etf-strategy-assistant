from pathlib import Path
from datetime import datetime
import html
import pandas as pd
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")


FILES = {
    "market_performance": DATA_DIR / "latest_market_performance.csv",
    "market_signals": DATA_DIR / "latest_market_signals.csv",
    "cross_validation": DATA_DIR / "cross_validation_alpha_vantage_latest.csv",
    "entry_decision": DATA_DIR / "latest_entry_decision.csv",
    "entry_order_plan": DATA_DIR / "latest_entry_order_plan.csv",
    "market_indicator_score": DATA_DIR / "market_indicator_score_latest.csv",
}


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # 处理 index 被保存成第一列的情况
    if len(df.columns) > 0:
        first_col = df.columns[0]
        if first_col.lower() in ["unnamed: 0", "index"]:
            df = df.rename(columns={first_col: "ticker"})

    # 统一 ticker 列
    for c in df.columns:
        if c.lower() == "ticker":
            df = df.rename(columns={c: "ticker"})
            break

    if "Ticker" in df.columns and "ticker" not in df.columns:
        df = df.rename(columns={"Ticker": "ticker"})

    return df


def esc(x):
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def fmt_num(x, digits=2):
    try:
        if pd.isna(x):
            return ""
        return f"{float(x):,.{digits}f}"
    except Exception:
        return esc(x)


def fmt_money(x):
    try:
        if pd.isna(x):
            return ""
        return f"${float(x):,.0f}"
    except Exception:
        return esc(x)


def fmt_pct(x):
    try:
        if pd.isna(x):
            return ""
        return f"{float(x):.2%}"
    except Exception:
        return esc(x)


def fmt_bool(x):
    if pd.isna(x):
        return ""
    if str(x).lower() in ["true", "1", "yes"]:
        return "True"
    if str(x).lower() in ["false", "0", "no"]:
        return "False"
    return esc(x)


def value_from_row(row, key, default=""):
    if row is None:
        return default
    if key not in row.index:
        return default
    val = row[key]
    if pd.isna(val):
        return default
    return val


def df_to_html_table(df: pd.DataFrame, columns, rename_map=None, format_map=None, max_rows=None):
    if df is None or df.empty:
        return "<p class='muted'>暂无数据</p>"

    rename_map = rename_map or {}
    format_map = format_map or {}

    available_cols = [c for c in columns if c in df.columns]
    if not available_cols:
        return "<p class='muted'>暂无可展示字段</p>"

    show_df = df[available_cols].copy()
    if max_rows is not None:
        show_df = show_df.head(max_rows)

    ths = "".join(f"<th>{esc(rename_map.get(c, c))}</th>" for c in available_cols)
    rows = []

    for _, r in show_df.iterrows():
        tds = []
        for c in available_cols:
            v = r[c]
            if c in format_map:
                v2 = format_map[c](v)
            else:
                v2 = esc(v)
            tds.append(f"<td>{v2}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")

    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{ths}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def badge_class(value):
    s = str(value).lower()

    if s in ["passed", "normal", "strong", "ok", "true", "允许首笔建仓"]:
        return "badge good"

    if s in ["need_check", "manual_review", "neutral", "wait", "等待", "weak"]:
        return "badge warn"

    if s in ["failed", "high_risk", "false", "price_mismatch"]:
        return "badge bad"

    return "badge"


print("项目路径：", PROJECT_DIR)
for name, path in FILES.items():
    print(f"{path.name} 是否存在：", path.exists())


market_perf = read_csv_safe(FILES["market_performance"])
market_signals = read_csv_safe(FILES["market_signals"])
cross_validation = read_csv_safe(FILES["cross_validation"])
entry_decision = read_csv_safe(FILES["entry_decision"])
entry_order_plan = read_csv_safe(FILES["entry_order_plan"])
indicator_score = read_csv_safe(FILES["market_indicator_score"])


print("")
print("===== 入场决策 =====")
print(entry_decision)

print("")
print("===== 建议买入明细 =====")
print(entry_order_plan)

print("")
print("===== Market Indicator Score =====")
if indicator_score.empty:
    print("market_indicator_score_latest.csv 不存在或为空。Dashboard 将跳过 V1.2 指标表。")
else:
    show_cols = [
        "ticker", "role", "latest_price", "ma50", "ma200", "above_200ma",
        "rsi14", "return_3m", "return_6m", "vol20_annualized",
        "drawdown_252d", "market_score", "score_status",
        "suggested_buy_amount"
    ]
    print(indicator_score[[c for c in show_cols if c in indicator_score.columns]])


decision_row = entry_decision.iloc[0] if not entry_decision.empty else None

recommendation = value_from_row(decision_row, "recommendation", "暂无")
decision_sentence = value_from_row(decision_row, "decision_sentence", "暂无入场决策")
suggested_amount = value_from_row(decision_row, "suggested_amount_usd", 0)
market_status_cn = value_from_row(decision_row, "market_status_cn", "暂无")
data_validation_status = value_from_row(decision_row, "data_validation_status", "暂无")
data_validation_summary = value_from_row(decision_row, "data_validation_summary", "")
position_status = value_from_row(decision_row, "position_status", "")
current_cash = value_from_row(decision_row, "current_cash", np.nan)
invested_amount = value_from_row(decision_row, "invested_amount", np.nan)
action_type = value_from_row(decision_row, "action_type", "")
matched_rule_id = value_from_row(decision_row, "matched_rule_id", "")
auto_trade = value_from_row(decision_row, "auto_trade", False)
decision_mode = value_from_row(decision_row, "decision_mode", "")

vti_price = value_from_row(decision_row, "vti_price", np.nan)
vti_ma200 = value_from_row(decision_row, "vti_ma200", np.nan)
vti_drawdown = value_from_row(decision_row, "vti_drawdown_252d", np.nan)
vix_value = value_from_row(decision_row, "vix_value", np.nan)
vti_dd_10_price = value_from_row(decision_row, "vti_dd_10_price", np.nan)
vti_dd_15_price = value_from_row(decision_row, "vti_dd_15_price", np.nan)
vti_dd_25_price = value_from_row(decision_row, "vti_dd_25_price", np.nan)

buy_after_cash = np.nan
try:
    buy_after_cash = float(current_cash) - float(suggested_amount)
except Exception:
    pass


core_indicator_cols = [
    "ticker", "role", "latest_price", "ma50", "ma200", "above_200ma",
    "rsi14", "return_3m", "return_6m", "vol20_annualized",
    "drawdown_252d", "dd_10_price", "dd_15_price", "dd_25_price",
    "market_score", "score_status", "suggested_buy_amount"
]

core_indicator_rename = {
    "ticker": "ETF",
    "role": "角色",
    "latest_price": "当前价",
    "ma50": "50日均线",
    "ma200": "200日均线",
    "above_200ma": "高于200MA",
    "rsi14": "RSI14",
    "return_3m": "3M收益",
    "return_6m": "6M收益",
    "vol20_annualized": "20日年化波动",
    "drawdown_252d": "252日回撤",
    "dd_10_price": "-10%参考价",
    "dd_15_price": "-15%参考价",
    "dd_25_price": "-25%参考价",
    "market_score": "Market Score",
    "score_status": "评分状态",
    "suggested_buy_amount": "建议金额",
}

core_indicator_format = {
    "latest_price": fmt_num,
    "ma50": fmt_num,
    "ma200": fmt_num,
    "above_200ma": fmt_bool,
    "rsi14": fmt_num,
    "return_3m": fmt_pct,
    "return_6m": fmt_pct,
    "vol20_annualized": fmt_pct,
    "drawdown_252d": fmt_pct,
    "dd_10_price": fmt_num,
    "dd_15_price": fmt_num,
    "dd_25_price": fmt_num,
    "market_score": fmt_num,
    "suggested_buy_amount": fmt_money,
}

score_breakdown_cols = [
    "ticker", "trend_score", "momentum_score", "risk_score",
    "drawdown_score", "price_position_score", "market_score",
    "reference_signal", "notes"
]

score_breakdown_rename = {
    "ticker": "ETF",
    "trend_score": "趋势分",
    "momentum_score": "动量分",
    "risk_score": "风险分",
    "drawdown_score": "回撤分",
    "price_position_score": "价格位置分",
    "market_score": "总分",
    "reference_signal": "辅助信号",
    "notes": "说明",
}

score_breakdown_format = {
    "trend_score": fmt_num,
    "momentum_score": fmt_num,
    "risk_score": fmt_num,
    "drawdown_score": fmt_num,
    "price_position_score": fmt_num,
    "market_score": fmt_num,
}

order_cols = [
    "ticker", "role", "target_weight", "suggested_buy_amount",
    "currency", "account", "action_type", "auto_trade", "notes"
]

order_rename = {
    "ticker": "ETF",
    "role": "角色",
    "target_weight": "目标权重",
    "suggested_buy_amount": "建议金额",
    "currency": "币种",
    "account": "账户",
    "action_type": "动作",
    "auto_trade": "自动交易",
    "notes": "说明",
}

order_format = {
    "target_weight": fmt_pct,
    "suggested_buy_amount": fmt_money,
    "auto_trade": fmt_bool,
}

signal_cols = ["rule_id", "category", "triggered", "severity", "auto_trade", "detail"]
signal_rename = {
    "rule_id": "规则",
    "category": "类别",
    "triggered": "是否触发",
    "severity": "级别",
    "auto_trade": "自动交易",
    "detail": "说明",
}
signal_format = {
    "triggered": fmt_bool,
    "auto_trade": fmt_bool,
}

cross_cols = ["ticker", "status", "common_date", "yf_close", "av_close", "pct_diff", "pass_price_check", "notes"]
cross_rename = {
    "ticker": "ETF",
    "status": "状态",
    "common_date": "验证日期",
    "yf_close": "yfinance价格",
    "av_close": "Alpha Vantage价格",
    "pct_diff": "差异",
    "pass_price_check": "是否通过",
    "notes": "说明",
}
cross_format = {
    "yf_close": fmt_num,
    "av_close": fmt_num,
    "pct_diff": fmt_pct,
    "pass_price_check": fmt_bool,
}

perf_cols = ["ticker", "latest_price", "return_1d", "return_1m", "return_3m", "return_6m", "return_12m", "above_200ma", "drawdown_252d"]
perf_rename = {
    "ticker": "ETF",
    "latest_price": "当前价",
    "return_1d": "1日",
    "return_1m": "1M",
    "return_3m": "3M",
    "return_6m": "6M",
    "return_12m": "12M",
    "above_200ma": "高于200MA",
    "drawdown_252d": "252日回撤",
}
perf_format = {
    "latest_price": fmt_num,
    "return_1d": fmt_pct,
    "return_1m": fmt_pct,
    "return_3m": fmt_pct,
    "return_6m": fmt_pct,
    "return_12m": fmt_pct,
    "above_200ma": fmt_bool,
    "drawdown_252d": fmt_pct,
}


css = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  background: #f6f7f9;
  color: #1f2937;
}
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 28px;
}
h1 {
  margin: 0 0 8px 0;
  font-size: 30px;
}
h2 {
  margin-top: 32px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}
.subtitle {
  color: #6b7280;
  margin-bottom: 24px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.card {
  background: white;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.card-title {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 8px;
}
.card-value {
  font-size: 24px;
  font-weight: 700;
}
.card-small {
  color: #6b7280;
  font-size: 13px;
  margin-top: 6px;
}
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e5e7eb;
  color: #374151;
  font-weight: 600;
}
.badge.good {
  background: #dcfce7;
  color: #166534;
}
.badge.warn {
  background: #fef3c7;
  color: #92400e;
}
.badge.bad {
  background: #fee2e2;
  color: #991b1b;
}
.alert {
  background: #fff7ed;
  border-left: 5px solid #f97316;
  padding: 14px 16px;
  border-radius: 8px;
  margin: 20px 0;
}
.note {
  background: #eef2ff;
  border-left: 5px solid #6366f1;
  padding: 14px 16px;
  border-radius: 8px;
  margin: 20px 0;
}
.table-wrap {
  overflow-x: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  background: #f3f4f6;
  text-align: left;
  padding: 10px;
  white-space: nowrap;
}
td {
  border-top: 1px solid #e5e7eb;
  padding: 9px 10px;
  white-space: nowrap;
}
.muted {
  color: #6b7280;
}
.footer {
  margin-top: 36px;
  color: #6b7280;
  font-size: 12px;
}
@media (max-width: 900px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
"""


html_doc = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>ETF Strategy Dashboard V1.2</title>
<style>{css}</style>
</head>
<body>
<div class="container">

  <h1>ETF Strategy Dashboard V1.2</h1>
  <div class="subtitle">生成日期：{TODAY} ｜ 规则化监控报告，不自动交易，不构成投资建议</div>

  <div class="grid">
    <div class="card">
      <div class="card-title">今日建议</div>
      <div class="card-value"><span class="{badge_class(recommendation)}">{esc(recommendation)}</span></div>
      <div class="card-small">{esc(action_type)}</div>
    </div>

    <div class="card">
      <div class="card-title">建议金额</div>
      <div class="card-value">{fmt_money(suggested_amount)}</div>
      <div class="card-small">买入后现金：{fmt_money(buy_after_cash)}</div>
    </div>

    <div class="card">
      <div class="card-title">市场状态</div>
      <div class="card-value"><span class="{badge_class(market_status_cn)}">{esc(market_status_cn)}</span></div>
      <div class="card-small">规则：{esc(matched_rule_id)}</div>
    </div>

    <div class="card">
      <div class="card-title">数据验证</div>
      <div class="card-value"><span class="{badge_class(data_validation_status)}">{esc(data_validation_status)}</span></div>
      <div class="card-small">{esc(data_validation_summary)}</div>
    </div>
  </div>

  <div class="alert">
    <b>今日决策句：</b>{esc(decision_sentence)}<br>
    <b>自动交易：</b>{fmt_bool(auto_trade)} ｜ <b>决策模式：</b>{esc(decision_mode)} ｜ <b>当前状态：</b>{esc(position_status)}
  </div>

  <h2>账户概览</h2>
  <div class="grid">
    <div class="card">
      <div class="card-title">当前现金</div>
      <div class="card-value">{fmt_money(current_cash)}</div>
    </div>
    <div class="card">
      <div class="card-title">已投入金额</div>
      <div class="card-value">{fmt_money(invested_amount)}</div>
    </div>
    <div class="card">
      <div class="card-title">VTI 当前价</div>
      <div class="card-value">{fmt_num(vti_price)}</div>
      <div class="card-small">200MA：{fmt_num(vti_ma200)}</div>
    </div>
    <div class="card">
      <div class="card-title">VIX</div>
      <div class="card-value">{fmt_num(vix_value)}</div>
      <div class="card-small">VTI 回撤：{fmt_pct(vti_drawdown)}</div>
    </div>
  </div>

  <h2>VTI 原始入场参考点位</h2>
  <div class="grid">
    <div class="card">
      <div class="card-title">VTI -10% 回撤参考价</div>
      <div class="card-value">{fmt_num(vti_dd_10_price)}</div>
    </div>
    <div class="card">
      <div class="card-title">VTI -15% 回撤参考价</div>
      <div class="card-value">{fmt_num(vti_dd_15_price)}</div>
    </div>
    <div class="card">
      <div class="card-title">VTI -25% 回撤参考价</div>
      <div class="card-value">{fmt_num(vti_dd_25_price)}</div>
    </div>
    <div class="card">
      <div class="card-title">当前匹配规则</div>
      <div class="card-value">{esc(matched_rule_id)}</div>
    </div>
  </div>

  <h2>V1.2 核心 ETF 多指标入场参考表</h2>
  <div class="note">
    这一部分新增 VTI / VEA / VWO / SGOV 的多指标观察表，包括价格、均线、RSI、3M/6M收益、波动率、回撤、-10%/-15%/-25%参考价和 Market Score。
    当前仅用于辅助观察，暂未改变正式买入建议。
  </div>
  {df_to_html_table(indicator_score, core_indicator_cols, core_indicator_rename, core_indicator_format)}

  <h2>V1.2 Market Score 评分拆解</h2>
  {df_to_html_table(indicator_score, score_breakdown_cols, score_breakdown_rename, score_breakdown_format)}

  <h2>建议买入明细</h2>
  {df_to_html_table(entry_order_plan, order_cols, order_rename, order_format)}

  <h2>市场信号</h2>
  {df_to_html_table(market_signals, signal_cols, signal_rename, signal_format)}

  <h2>Alpha Vantage 交叉验证</h2>
  {df_to_html_table(cross_validation, cross_cols, cross_rename, cross_format)}

  <h2>市场表现摘要</h2>
  {df_to_html_table(market_perf, perf_cols, perf_rename, perf_format, max_rows=18)}

  <div class="footer">
    本报告由 ETF Strategy Assistant 自动生成。所有交易相关信息均为规则化监控输出，不构成投资建议，不自动交易，必须人工确认。
    SGOV 为现金/短债工具，其 RSI、回撤和布林带指标不应按风险资产买点解释。
  </div>

</div>
</body>
</html>
"""


dated_report = REPORT_DIR / f"dashboard_{TODAY}.html"
latest_report = REPORT_DIR / "dashboard_latest.html"

dated_report.write_text(html_doc, encoding="utf-8")
latest_report.write_text(html_doc, encoding="utf-8")

print("")
print("Dashboard 已保存：", dated_report)
print("最新 Dashboard 已保存：", latest_report)
print("")
print("第 49 步完成：Dashboard V1.2 已接入 Market Indicator Score。")
