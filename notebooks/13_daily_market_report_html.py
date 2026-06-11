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

performance_path = processed_dir / "latest_market_performance.csv"
signals_path = processed_dir / "latest_market_signals.csv"
validation_path = processed_dir / "cross_validation_alpha_vantage_latest.csv"

print("项目路径：", PROJECT_ROOT)
print("市场表现文件是否存在：", performance_path.exists())
print("市场信号文件是否存在：", signals_path.exists())
print("交叉验证文件是否存在：", validation_path.exists())

if not performance_path.exists():
    raise FileNotFoundError("缺少 latest_market_performance.csv，请先运行每日早报脚本。")

if not signals_path.exists():
    raise FileNotFoundError("缺少 latest_market_signals.csv，请先运行每日早报脚本。")

if not validation_path.exists():
    raise FileNotFoundError("缺少 cross_validation_alpha_vantage_latest.csv，请先运行 Alpha Vantage 交叉验证脚本。")


# =========================
# 2. 读取数据
# =========================

performance = pd.read_csv(performance_path, index_col=0)
signals = pd.read_csv(signals_path)
validation = pd.read_csv(validation_path)

performance.index.name = "ticker"

print("\n===== 市场表现数据 =====")
print(performance.head())

print("\n===== 市场信号 =====")
print(signals.head())

print("\n===== 交叉验证结果 =====")
print(validation.head())


# =========================
# 3. 辅助格式函数
# =========================

def to_bool(x):
    if isinstance(x, bool):
        return x
    if str(x).lower() == "true":
        return True
    if str(x).lower() == "false":
        return False
    return bool(x)


def pct_fmt(x):
    if pd.isna(x):
        return ""
    return f"{x:.2%}"


def num_fmt(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}"


def bool_fmt(x):
    if to_bool(x):
        return "是"
    return "否"


def format_performance_table(df):
    out = df.copy()

    price_cols = ["latest_price", "ma50", "ma200"]
    pct_cols = [
        "return_1d",
        "return_5d",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "drawdown_252d"
    ]
    bool_cols = ["above_50ma", "above_200ma"]

    for col in price_cols:
        if col in out.columns:
            out[col] = out[col].apply(num_fmt)

    for col in pct_cols:
        if col in out.columns:
            out[col] = out[col].apply(pct_fmt)

    for col in bool_cols:
        if col in out.columns:
            out[col] = out[col].apply(bool_fmt)

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
# 4. 判断状态
# =========================

signals["triggered_bool"] = signals["triggered"].apply(to_bool)
triggered = signals[signals["triggered_bool"] == True].copy()

validation["pass_bool"] = validation["pass_price_check"].apply(to_bool)

total_validation = len(validation)
passed_validation = int(validation["pass_bool"].sum())
failed_validation = total_validation - passed_validation

if total_validation == 0:
    data_validation_status = "missing"
    data_validation_summary = "没有可用的交叉验证结果。"
elif failed_validation == 0:
    data_validation_status = "passed"
    data_validation_summary = f"{passed_validation}/{total_validation} 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。"
elif passed_validation > 0:
    data_validation_status = "need_check"
    data_validation_summary = f"{passed_validation}/{total_validation} 个标的通过，{failed_validation} 个标的需要人工检查。"
else:
    data_validation_status = "failed"
    data_validation_summary = f"0/{total_validation} 个标的通过交叉验证，需要检查数据源。"


high_alert_count = (triggered["action_level"] == "high_alert").sum()
alert_count = (triggered["action_level"] == "alert").sum()
warning_count = (triggered["action_level"] == "warning").sum()
watch_count = (triggered["action_level"] == "watch").sum()

if high_alert_count > 0:
    market_status = "高风险"
    market_status_class = "danger"
    action_summary = "暂停自动交易，只做人工确认；长期账户可以观察是否有分批加仓机会。"
elif alert_count > 0:
    market_status = "偏高风险"
    market_status_class = "warning"
    action_summary = "不建议激进加仓；长期账户按计划执行，提前买入需要人工确认。"
elif warning_count > 0:
    market_status = "中等风险"
    market_status_class = "warning"
    action_summary = "长期账户继续按计划执行；短线交易降低仓位。"
elif watch_count > 0:
    market_status = "观察状态"
    market_status_class = "watch"
    action_summary = "长期账户可以继续执行固定分批；如有回撤提醒，可以考虑但不自动提前买入。"
else:
    market_status = "正常"
    market_status_class = "normal"
    action_summary = "长期账户按固定计划执行；短线账户只做观察，不自动交易。"


if data_validation_status == "passed":
    validation_class = "normal"
    final_trade_permission = "自动交易关闭；允许生成交易提醒"
else:
    validation_class = "danger"
    final_trade_permission = "禁止自动交易，只允许人工查看"


# =========================
# 5. 准备表格
# =========================

core_tickers = ["VTI", "VEA", "VWO", "SGOV"]
core_perf = performance.loc[[t for t in core_tickers if t in performance.index]].copy()

top_3m = performance.sort_values("return_3m", ascending=False).head(6)
bottom_3m = performance.sort_values("return_3m", ascending=True).head(6)

failed_validation = validation[validation["pass_bool"] == False].copy()

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
validation_html = format_validation_table(validation[validation_cols]).to_html(index=False, classes="data-table", border=0)

if triggered.empty:
    triggered_html = "<p>今日没有触发高优先级风险信号。</p>"
else:
    triggered_cols = ["rule_id", "category", "action_level", "meaning", "detail", "auto_trade"]
    triggered_html = triggered[triggered_cols].to_html(index=False, classes="data-table", border=0)

if failed_validation.empty:
    failed_validation_html = "<p>所有交叉验证标的均通过。</p>"
else:
    failed_validation_html = format_validation_table(failed_validation[validation_cols]).to_html(
        index=False,
        classes="data-table",
        border=0
    )


# =========================
# 6. 生成 HTML
# =========================

html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>每日市场早报 V2 - {today_str}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f5f6f8;
    color: #222;
    margin: 0;
    padding: 0;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 28px;
}}

h1 {{
    font-size: 30px;
    margin-bottom: 8px;
}}

h2 {{
    margin-top: 32px;
    padding-bottom: 8px;
    border-bottom: 2px solid #ddd;
}}

.card-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 20px;
}}

.card {{
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
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
    color: #147a3e;
}}

.warning {{
    color: #b36b00;
}}

.watch {{
    color: #7a5c00;
}}

.danger {{
    color: #b00020;
}}

.summary {{
    background: white;
    border-radius: 14px;
    padding: 18px;
    margin-top: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    line-height: 1.7;
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

<h1>每日市场早报 V2</h1>
<div class="badge">生成日期：{today_str}</div>

<div class="card-row">
    <div class="card">
        <div class="card-title">市场状态</div>
        <div class="card-value {market_status_class}">{market_status}</div>
    </div>
    <div class="card">
        <div class="card-title">数据交叉验证</div>
        <div class="card-value {validation_class}">{data_validation_status}</div>
    </div>
    <div class="card">
        <div class="card-title">交易权限</div>
        <div class="card-value">提醒模式</div>
    </div>
</div>

<div class="summary">
    <strong>综合结论：</strong><br>
    数据验证：{data_validation_summary}<br>
    交易权限：{final_trade_permission}<br>
    操作摘要：{action_summary}
</div>

<h2>1. 长期核心账户观察</h2>
{core_html}

<h2>2. 今日触发信号</h2>
{triggered_html}

<h2>3. 数据交叉验证明细</h2>
{validation_html}

<h2>4. 数据验证异常标的</h2>
{failed_validation_html}

<h2>5. 3个月表现靠前标的</h2>
{top_html}

<h2>6. 3个月表现靠后标的</h2>
{bottom_html}

<div class="footer">
    <strong>说明：</strong><br>
    本报告使用 yfinance 生成市场表现数据，并使用 Alpha Vantage 做价格交叉验证。<br>
    如果交叉验证状态不是 passed，本系统不允许自动交易。<br>
    当前版本只生成提醒，不自动下单，也不构成投资建议。
</div>

</div>
</body>
</html>
"""

html_path = reports_dir / f"daily_market_report_v2_{today_str}.html"
latest_html_path = reports_dir / "daily_market_report_v2_latest.html"

html_path.write_text(html, encoding="utf-8")
latest_html_path.write_text(html, encoding="utf-8")

print("\nHTML 每日市场早报已保存：", html_path)
print("最新 HTML 每日市场早报已保存：", latest_html_path)

print("\n第 23 步完成：HTML 每日市场早报生成成功。")
