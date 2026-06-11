from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

today_str = datetime.now().strftime("%Y-%m-%d")

print("项目路径：", PROJECT_ROOT)


# =========================
# 2. 文件路径
# =========================

performance_path = processed_dir / "latest_market_performance.csv"
signals_path = processed_dir / "latest_market_signals.csv"
validation_path = processed_dir / "cross_validation_alpha_vantage_latest.csv"
entry_decision_path = processed_dir / "latest_entry_decision.csv"
entry_order_path = processed_dir / "latest_entry_order_plan.csv"

required_files = [
    performance_path,
    signals_path,
    validation_path,
    entry_decision_path,
    entry_order_path
]

for path in required_files:
    print(f"{path.name} 是否存在：", path.exists())

missing_files = [p for p in required_files if not p.exists()]

if missing_files:
    raise FileNotFoundError(
        "以下文件不存在，请先运行前面的每日早报、交叉验证和入场决策脚本：\n"
        + "\n".join(str(p) for p in missing_files)
    )


# =========================
# 3. 读取数据
# =========================

performance = pd.read_csv(performance_path, index_col=0)
signals = pd.read_csv(signals_path)
validation = pd.read_csv(validation_path)
entry_decision = pd.read_csv(entry_decision_path)
entry_order = pd.read_csv(entry_order_path)

performance.index.name = "ticker"

decision = entry_decision.iloc[0]

print("\n===== 入场决策 =====")
print(entry_decision)

print("\n===== 建议买入明细 =====")
print(entry_order)


# =========================
# 4. 格式函数
# =========================

def to_bool(x):
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in ["true", "1", "yes", "y"]:
        return True
    if s in ["false", "0", "no", "n"]:
        return False
    return False


def num_fmt(x):
    if pd.isna(x):
        return ""
    return f"{float(x):,.2f}"


def dollar_fmt(x):
    if pd.isna(x):
        return ""
    return f"${float(x):,.0f}"


def pct_fmt(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.2%}"


def bool_fmt(x):
    return "是" if to_bool(x) else "否"


def get_class_for_action(action_type):
    if action_type in ["WAIT", "MANUAL_REVIEW"]:
        return "danger"
    if action_type in ["BUY_INITIAL_SMALL", "BUY_INITIAL_PLUS_ONE_DCA"]:
        return "warning"
    if action_type in ["BUY_INITIAL_STANDARD", "MONTHLY_DCA"]:
        return "normal"
    return "watch"


def get_class_for_status(status):
    status = str(status)
    if status in ["passed", "normal", "正常"]:
        return "normal"
    if status in ["need_check", "watch", "观察状态", "medium_risk", "elevated_risk"]:
        return "warning"
    return "danger"


def format_performance_table(df):
    out = df.copy()

    for col in ["latest_price", "ma50", "ma200"]:
        if col in out.columns:
            out[col] = out[col].apply(num_fmt)

    for col in [
        "return_1d",
        "return_5d",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "drawdown_252d"
    ]:
        if col in out.columns:
            out[col] = out[col].apply(pct_fmt)

    for col in ["above_50ma", "above_200ma"]:
        if col in out.columns:
            out[col] = out[col].apply(bool_fmt)

    return out


def format_order_table(df):
    out = df.copy()

    if "target_weight" in out.columns:
        out["target_weight"] = out["target_weight"].apply(pct_fmt)

    if "suggested_buy_amount" in out.columns:
        out["suggested_buy_amount"] = out["suggested_buy_amount"].apply(dollar_fmt)

    return out


def format_validation_table(df):
    out = df.copy()

    for col in ["yf_close", "av_close", "abs_diff"]:
        if col in out.columns:
            out[col] = out[col].apply(num_fmt)

    if "pct_diff" in out.columns:
        out["pct_diff"] = out["pct_diff"].apply(pct_fmt)

    if "pass_price_check" in out.columns:
        out["pass_price_check"] = out["pass_price_check"].apply(bool_fmt)

    return out


# =========================
# 5. 提取核心变量
# =========================

recommendation = decision["recommendation"]
action_type = decision["action_type"]
suggested_amount = float(decision["suggested_amount_usd"])
decision_sentence = decision["decision_sentence"]

market_status_cn = decision["market_status_cn"]
data_validation_status = decision["data_validation_status"]
position_status = decision["position_status"]
current_cash = float(decision["current_cash"])
invested_amount = float(decision["invested_amount"])

vti_price = float(decision["vti_price"])
vti_ma200 = float(decision["vti_ma200"])
vti_drawdown = float(decision["vti_drawdown_252d"])
vti_dd_10_price = float(decision["vti_dd_10_price"])
vti_dd_15_price = float(decision["vti_dd_15_price"])
vti_dd_25_price = float(decision["vti_dd_25_price"])
vix_value = float(decision["vix_value"])

action_class = get_class_for_action(action_type)
market_class = get_class_for_status(market_status_cn)
validation_class = get_class_for_status(data_validation_status)

remaining_cash_after_buy = current_cash - suggested_amount


# =========================
# 6. 准备表格
# =========================

core_tickers = ["VTI", "VEA", "VWO", "SGOV"]
core_perf = performance.loc[[t for t in core_tickers if t in performance.index]].copy()

top_3m = performance.sort_values("return_3m", ascending=False).head(6)
bottom_3m = performance.sort_values("return_3m", ascending=True).head(6)

signals["triggered_bool"] = signals["triggered"].apply(to_bool)
triggered = signals[signals["triggered_bool"] == True].copy()

core_cols = [
    "latest_price",
    "return_1d",
    "return_1m",
    "return_3m",
    "return_6m",
    "return_12m",
    "above_200ma",
    "drawdown_252d"
]

rank_cols = [
    "latest_price",
    "return_1m",
    "return_3m",
    "return_6m",
    "return_12m",
    "above_200ma",
    "drawdown_252d"
]

order_cols = [
    "ticker",
    "role",
    "target_weight",
    "suggested_buy_amount",
    "currency",
    "account",
    "action_type",
    "auto_trade",
    "notes"
]

validation_cols = [
    "ticker",
    "status",
    "common_date",
    "yf_close",
    "av_close",
    "pct_diff",
    "pass_price_check",
    "notes"
]

core_html = format_performance_table(core_perf[core_cols]).to_html(classes="data-table", border=0)
top_html = format_performance_table(top_3m[rank_cols]).to_html(classes="data-table", border=0)
bottom_html = format_performance_table(bottom_3m[rank_cols]).to_html(classes="data-table", border=0)
order_html = format_order_table(entry_order[order_cols]).to_html(index=False, classes="data-table", border=0)
validation_html = format_validation_table(validation[validation_cols]).to_html(index=False, classes="data-table", border=0)

if triggered.empty:
    triggered_html = "<p>今日没有触发高优先级风险信号。</p>"
else:
    triggered_cols = ["rule_id", "category", "action_level", "meaning", "detail", "auto_trade"]
    triggered_html = triggered[triggered_cols].to_html(index=False, classes="data-table", border=0)


# =========================
# 7. 生成 HTML Dashboard
# =========================

html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>ETF Strategy Dashboard - {today_str}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f4f6f8;
    color: #222;
    margin: 0;
    padding: 0;
}}

.container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 28px;
}}

h1 {{
    margin-bottom: 6px;
    font-size: 32px;
}}

h2 {{
    margin-top: 34px;
    padding-bottom: 8px;
    border-bottom: 2px solid #ddd;
}}

.subtitle {{
    color: #666;
    margin-bottom: 20px;
}}

.card-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 20px;
}}

.card {{
    background: white;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}

.card-title {{
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
}}

.card-value {{
    font-size: 24px;
    font-weight: 700;
}}

.normal {{
    color: #137333;
}}

.warning {{
    color: #b06000;
}}

.watch {{
    color: #7a5c00;
}}

.danger {{
    color: #b00020;
}}

.summary {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    line-height: 1.8;
}}

.decision-box {{
    background: #fff;
    border-left: 8px solid #137333;
    border-radius: 14px;
    padding: 22px;
    margin-top: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}

.decision-box.warning {{
    border-left-color: #b06000;
}}

.decision-box.danger {{
    border-left-color: #b00020;
}}

.decision-title {{
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 12px;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    margin-top: 12px;
    font-size: 14px;
}}

.data-table th {{
    background: #eef1f5;
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #ddd;
}}

.data-table td {{
    padding: 9px 10px;
    border-bottom: 1px solid #eee;
}}

.data-table tr:hover {{
    background: #f9fbff;
}}

.level-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 12px;
}}

.level-card {{
    background: white;
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

.level-title {{
    color: #666;
    font-size: 13px;
    margin-bottom: 6px;
}}

.level-value {{
    font-size: 22px;
    font-weight: 700;
}}

.footer {{
    color: #666;
    font-size: 13px;
    margin-top: 36px;
    line-height: 1.6;
}}

.badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: #eef1f5;
    font-size: 13px;
}}
</style>
</head>

<body>
<div class="container">

<h1>ETF Strategy Dashboard</h1>
<div class="subtitle">生成日期：{today_str} ｜ 账户状态：{position_status} ｜ 自动交易：关闭</div>

<div class="card-row">
    <div class="card">
        <div class="card-title">今日建议</div>
        <div class="card-value {action_class}">{recommendation}</div>
    </div>
    <div class="card">
        <div class="card-title">建议金额</div>
        <div class="card-value">{dollar_fmt(suggested_amount)}</div>
    </div>
    <div class="card">
        <div class="card-title">市场状态</div>
        <div class="card-value {market_class}">{market_status_cn}</div>
    </div>
    <div class="card">
        <div class="card-title">数据验证</div>
        <div class="card-value {validation_class}">{data_validation_status}</div>
    </div>
</div>

<div class="decision-box {action_class}">
    <div class="decision-title">{decision_sentence}</div>
    <div>
        当前现金：{dollar_fmt(current_cash)} ｜ 已投入：{dollar_fmt(invested_amount)} ｜ 
        建议买入后剩余现金：{dollar_fmt(remaining_cash_after_buy)}
    </div>
    <div>
        执行动作：{action_type} ｜ 执行方式：人工确认 ｜ 自动交易：关闭
    </div>
</div>

<h2>1. 入场点位参考</h2>

<div class="level-grid">
    <div class="level-card">
        <div class="level-title">VTI 当前价</div>
        <div class="level-value">{num_fmt(vti_price)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">VTI 200日均线</div>
        <div class="level-value">{num_fmt(vti_ma200)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">VTI 当前回撤</div>
        <div class="level-value">{pct_fmt(vti_drawdown)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">VIX</div>
        <div class="level-value">{num_fmt(vix_value)}</div>
    </div>
</div>

<div class="level-grid">
    <div class="level-card">
        <div class="level-title">VTI -10% 回撤参考价</div>
        <div class="level-value">{num_fmt(vti_dd_10_price)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">VTI -15% 回撤参考价</div>
        <div class="level-value">{num_fmt(vti_dd_15_price)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">VTI -25% 回撤参考价</div>
        <div class="level-value">{num_fmt(vti_dd_25_price)}</div>
    </div>
    <div class="level-card">
        <div class="level-title">当前规则</div>
        <div class="level-value">{decision["matched_rule_id"]}</div>
    </div>
</div>

<h2>2. 建议买入明细</h2>
{order_html}

<h2>3. 长期核心账户观察</h2>
{core_html}

<h2>4. 今日触发信号</h2>
{triggered_html}

<h2>5. 数据交叉验证</h2>
{validation_html}

<h2>6. 3个月表现靠前标的</h2>
{top_html}

<h2>7. 3个月表现靠后标的</h2>
{bottom_html}

<div class="footer">
    <strong>说明：</strong><br>
    本 Dashboard 使用 yfinance 生成市场表现数据，并使用 Alpha Vantage 做价格交叉验证。<br>
    今日建议来自本地规则系统，不是自动交易指令。所有买入动作都需要人工确认。<br>
    本报告用于个人研究、组合监控和决策辅助，不构成投资建议。
</div>

</div>
</body>
</html>
"""

dashboard_path = reports_dir / f"dashboard_{today_str}.html"
latest_dashboard_path = reports_dir / "dashboard_latest.html"

dashboard_path.write_text(html, encoding="utf-8")
latest_dashboard_path.write_text(html, encoding="utf-8")

print("\nDashboard 已保存：", dashboard_path)
print("最新 Dashboard 已保存：", latest_dashboard_path)

print("\n第 34 步完成：Dashboard V1 生成成功。")
