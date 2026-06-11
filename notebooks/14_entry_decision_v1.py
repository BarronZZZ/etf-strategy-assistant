from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

config_dir = PROJECT_ROOT / "config"
processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

today_str = datetime.now().strftime("%Y-%m-%d")

print("项目路径：", PROJECT_ROOT)


# =========================
# 2. 文件路径
# =========================

account_path = config_dir / "account_status_usd.csv"
rules_path = config_dir / "entry_decision_rules.csv"
core_config_path = config_dir / "etf_universe_usd.csv"

performance_path = processed_dir / "latest_market_performance.csv"
signals_path = processed_dir / "latest_market_signals.csv"
validation_path = processed_dir / "cross_validation_alpha_vantage_latest.csv"

required_files = [
    account_path,
    rules_path,
    core_config_path,
    performance_path,
    signals_path,
    validation_path
]

for path in required_files:
    print(f"{path.name} 是否存在：", path.exists())

missing_files = [path for path in required_files if not path.exists()]

if missing_files:
    raise FileNotFoundError(
        "以下文件不存在：\n" + "\n".join(str(p) for p in missing_files)
    )


# =========================
# 3. 读取数据
# =========================

account_df = pd.read_csv(account_path)
rules = pd.read_csv(rules_path)
core_config = pd.read_csv(core_config_path)
performance = pd.read_csv(performance_path, index_col=0)
signals = pd.read_csv(signals_path)
validation = pd.read_csv(validation_path)

performance.index.name = "ticker"

print("\n===== 当前账户状态 =====")
print(account_df)

print("\n===== 入场规则 =====")
print(rules)

print("\n===== 市场表现数据前几行 =====")
print(performance.head())


# =========================
# 4. 工具函数
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


def to_float(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default


def get_account_value(item, default=None):
    row = account_df[account_df["item"] == item]
    if row.empty:
        return default
    return row.iloc[0]["value"]


def get_rule(rule_id):
    row = rules[rules["rule_id"] == rule_id]
    if row.empty:
        raise ValueError(f"找不到规则：{rule_id}")
    return row.iloc[0]


def safe_perf(ticker, column):
    if ticker in performance.index and column in performance.columns:
        return performance.loc[ticker, column]
    return np.nan


# =========================
# 5. 账户状态
# =========================

position_status = str(get_account_value("position_status", "unknown"))
current_cash = to_float(get_account_value("current_cash", 0), 0)
invested_amount = to_float(get_account_value("invested_amount", 0), 0)
initial_entry_done = to_bool(get_account_value("initial_entry_done", "false"))
auto_trade_enabled = to_bool(get_account_value("auto_trade_enabled", "false"))
decision_mode = str(get_account_value("decision_mode", "manual_confirm"))

print("\n===== 解析后的账户状态 =====")
print("position_status:", position_status)
print("current_cash:", current_cash)
print("invested_amount:", invested_amount)
print("initial_entry_done:", initial_entry_done)
print("auto_trade_enabled:", auto_trade_enabled)
print("decision_mode:", decision_mode)


# =========================
# 6. 数据交叉验证状态
# =========================

validation["pass_bool"] = validation["pass_price_check"].apply(to_bool)

total_validation = len(validation)
passed_validation = int(validation["pass_bool"].sum())
failed_validation = total_validation - passed_validation

if total_validation == 0:
    data_validation_status = "missing"
elif failed_validation == 0:
    data_validation_status = "passed"
elif passed_validation > 0:
    data_validation_status = "need_check"
else:
    data_validation_status = "failed"

data_validation_summary = f"{passed_validation}/{total_validation} 个标的通过 yfinance 与 Alpha Vantage 交叉验证。"

print("\n===== 数据交叉验证状态 =====")
print("状态：", data_validation_status)
print("摘要：", data_validation_summary)


# =========================
# 7. 市场状态
# =========================

signals["triggered_bool"] = signals["triggered"].apply(to_bool)
triggered = signals[signals["triggered_bool"] == True].copy()

high_alert_count = (triggered["action_level"] == "high_alert").sum()
alert_count = (triggered["action_level"] == "alert").sum()
warning_count = (triggered["action_level"] == "warning").sum()
watch_count = (triggered["action_level"] == "watch").sum()

if high_alert_count > 0:
    market_status = "high_risk"
    market_status_cn = "高风险"
elif alert_count > 0:
    market_status = "elevated_risk"
    market_status_cn = "偏高风险"
elif warning_count > 0:
    market_status = "medium_risk"
    market_status_cn = "中等风险"
elif watch_count > 0:
    market_status = "watch"
    market_status_cn = "观察状态"
else:
    market_status = "normal"
    market_status_cn = "正常"

print("\n===== 市场状态 =====")
print("market_status:", market_status)
print("market_status_cn:", market_status_cn)


# =========================
# 8. 关键市场变量
# =========================

vti_price = to_float(safe_perf("VTI", "latest_price"))
vti_ma200 = to_float(safe_perf("VTI", "ma200"))
vti_dd = to_float(safe_perf("VTI", "drawdown_252d"))

spy_price = to_float(safe_perf("SPY", "latest_price"))
spy_ma200 = to_float(safe_perf("SPY", "ma200"))

vix_value = to_float(safe_perf("^VIX", "latest_price"))

vti_above_200ma = bool(vti_price > vti_ma200) if not np.isnan(vti_price) and not np.isnan(vti_ma200) else False
spy_above_200ma = bool(spy_price > spy_ma200) if not np.isnan(spy_price) and not np.isnan(spy_ma200) else False

# 计算 VTI 252日高点和回撤触发参考价
if not np.isnan(vti_price) and not np.isnan(vti_dd) and vti_dd > -1:
    vti_252_high = vti_price / (1 + vti_dd)
else:
    vti_252_high = np.nan

vti_dd_10_price = vti_252_high * 0.90 if not np.isnan(vti_252_high) else np.nan
vti_dd_15_price = vti_252_high * 0.85 if not np.isnan(vti_252_high) else np.nan
vti_dd_25_price = vti_252_high * 0.75 if not np.isnan(vti_252_high) else np.nan

print("\n===== 关键市场变量 =====")
print("VTI 最新价:", vti_price)
print("VTI 200日均线:", vti_ma200)
print("VTI 是否高于200日均线:", vti_above_200ma)
print("VTI 252日回撤:", vti_dd)
print("SPY 最新价:", spy_price)
print("SPY 200日均线:", spy_ma200)
print("SPY 是否高于200日均线:", spy_above_200ma)
print("VIX:", vix_value)


# =========================
# 9. 入场决策逻辑
# =========================

matched_rule_id = None

if data_validation_status != "passed":
    matched_rule_id = "DATA_VALIDATION_BLOCK"

elif position_status == "empty":
    # 空仓状态下，先判断是否出现极端或趋势破位
    if (not np.isnan(vix_value) and vix_value > 35) or (not vti_above_200ma) or (not spy_above_200ma):
        matched_rule_id = "EMPTY_HIGH_RISK_WAIT"

    elif (not np.isnan(vti_dd)) and vti_dd <= -0.25:
        matched_rule_id = "EMPTY_DEEP_PULLBACK_MANUAL"

    elif (not np.isnan(vti_dd)) and vti_dd <= -0.15 and vti_dd > -0.25:
        matched_rule_id = "EMPTY_PULLBACK_ENTRY_15"

    elif (not np.isnan(vti_dd)) and vti_dd <= -0.10 and vti_dd > -0.15 and vti_above_200ma:
        matched_rule_id = "EMPTY_PULLBACK_ENTRY_10"

    elif (
        (not np.isnan(vix_value))
        and vix_value >= 25
        and vix_value <= 35
        and vti_above_200ma
        and spy_above_200ma
    ):
        matched_rule_id = "EMPTY_ELEVATED_RISK_SMALL_ENTRY"

    elif (
        (not np.isnan(vix_value))
        and vix_value < 25
        and vti_above_200ma
        and spy_above_200ma
        and (not np.isnan(vti_dd))
        and vti_dd > -0.10
    ):
        matched_rule_id = "EMPTY_NORMAL_INITIAL_ENTRY"

    else:
        matched_rule_id = "EMPTY_HIGH_RISK_WAIT"

else:
    if initial_entry_done and market_status == "normal":
        matched_rule_id = "AFTER_ENTRY_NORMAL_DCA"
    elif initial_entry_done and market_status in ["high_risk", "elevated_risk"]:
        matched_rule_id = "AFTER_ENTRY_RISK_WAIT"
    else:
        matched_rule_id = "AFTER_ENTRY_RISK_WAIT"


matched_rule = get_rule(matched_rule_id)

recommendation = matched_rule["recommendation"]
action_type = matched_rule["action_type"]
suggested_amount = to_float(matched_rule["suggested_amount_usd"], 0)

# 金额不能超过当前现金
final_suggested_amount = min(suggested_amount, current_cash)

# 再次强制确保不会自动交易
final_auto_trade = False

if final_suggested_amount > 0:
    decision_sentence = f"今日规则建议：{recommendation}，建议金额 ${final_suggested_amount:,.0f}，但必须人工确认。"
else:
    decision_sentence = f"今日规则建议：{recommendation}，暂不执行买入。"

print("\n===== 今日入场决策 =====")
print("matched_rule_id:", matched_rule_id)
print("recommendation:", recommendation)
print("action_type:", action_type)
print("suggested_amount:", final_suggested_amount)
print("decision_sentence:", decision_sentence)


# =========================
# 10. 生成买入金额明细
# =========================

order_rows = []

for _, row in core_config.iterrows():
    ticker = row["ticker"]
    target_weight = to_float(row["target_weight"], 0)

    planned_buy_amount = final_suggested_amount * target_weight

    order_rows.append({
        "date": today_str,
        "ticker": ticker,
        "role": row["role"],
        "target_weight": target_weight,
        "suggested_buy_amount": planned_buy_amount,
        "currency": row["currency"],
        "account": row["account"],
        "action_type": action_type,
        "auto_trade": final_auto_trade,
        "notes": "仅为规则建议，必须人工确认"
    })

order_plan = pd.DataFrame(order_rows)

print("\n===== 建议买入明细 =====")
print(order_plan)


# =========================
# 11. 生成决策结果表
# =========================

decision = pd.DataFrame([{
    "date": today_str,
    "position_status": position_status,
    "current_cash": current_cash,
    "invested_amount": invested_amount,
    "data_validation_status": data_validation_status,
    "data_validation_summary": data_validation_summary,
    "market_status": market_status,
    "market_status_cn": market_status_cn,
    "vti_price": vti_price,
    "vti_ma200": vti_ma200,
    "vti_above_200ma": vti_above_200ma,
    "vti_drawdown_252d": vti_dd,
    "vti_252_high_est": vti_252_high,
    "vti_dd_10_price": vti_dd_10_price,
    "vti_dd_15_price": vti_dd_15_price,
    "vti_dd_25_price": vti_dd_25_price,
    "spy_price": spy_price,
    "spy_ma200": spy_ma200,
    "spy_above_200ma": spy_above_200ma,
    "vix_value": vix_value,
    "matched_rule_id": matched_rule_id,
    "recommendation": recommendation,
    "action_type": action_type,
    "suggested_amount_usd": final_suggested_amount,
    "auto_trade": final_auto_trade,
    "decision_mode": decision_mode,
    "decision_sentence": decision_sentence
}])


decision_path = processed_dir / f"daily_entry_decision_{today_str}.csv"
latest_decision_path = processed_dir / "latest_entry_decision.csv"

order_path = processed_dir / f"daily_entry_order_plan_{today_str}.csv"
latest_order_path = processed_dir / "latest_entry_order_plan.csv"

decision.to_csv(decision_path, index=False)
decision.to_csv(latest_decision_path, index=False)

order_plan.to_csv(order_path, index=False)
order_plan.to_csv(latest_order_path, index=False)

print("\n入场决策已保存：", decision_path)
print("最新入场决策已保存：", latest_decision_path)
print("建议买入明细已保存：", order_path)
print("最新建议买入明细已保存：", latest_order_path)


# =========================
# 12. 生成 Markdown 报告
# =========================

report_path = reports_dir / f"daily_entry_decision_{today_str}.md"
latest_report_path = reports_dir / "daily_entry_decision_latest.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# 每日入场决策报告 - {today_str}\n\n")

    f.write("## 1. 今日结论\n\n")
    f.write(f"- {decision_sentence}\n")
    f.write(f"- 匹配规则：{matched_rule_id}\n")
    f.write(f"- 数据验证：{data_validation_status}，{data_validation_summary}\n")
    f.write(f"- 市场状态：{market_status_cn}\n")
    f.write(f"- 自动交易：关闭\n")
    f.write(f"- 执行方式：人工确认\n\n")

    f.write("## 2. 关键点位参考\n\n")
    f.write(f"- VTI 最新价：{vti_price:.2f}\n")
    f.write(f"- VTI 200日均线：{vti_ma200:.2f}\n")
    f.write(f"- VTI 252日高点估算：{vti_252_high:.2f}\n")
    f.write(f"- VTI -10% 回撤参考价：{vti_dd_10_price:.2f}\n")
    f.write(f"- VTI -15% 回撤参考价：{vti_dd_15_price:.2f}\n")
    f.write(f"- VTI -25% 回撤参考价：{vti_dd_25_price:.2f}\n")
    f.write(f"- 当前 VTI 252日回撤：{vti_dd:.2%}\n")
    f.write(f"- 当前 VIX：{vix_value:.2f}\n\n")

    f.write("## 3. 建议买入金额明细\n\n")
    f.write(order_plan.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 4. 说明\n\n")
    f.write("- 本报告只根据既定规则生成买入或等待建议。\n")
    f.write("- 本系统不会自动交易。\n")
    f.write("- 所有买入建议都需要人工确认。\n")
    f.write("- 本报告不构成投资建议。\n")

with open(report_path, "r", encoding="utf-8") as src:
    content = src.read()

with open(latest_report_path, "w", encoding="utf-8") as dst:
    dst.write(content)

print("\n每日入场决策 Markdown 已保存：", report_path)
print("最新每日入场决策 Markdown 已保存：", latest_report_path)

print("\n第 33 步完成：每日入场决策 V1 生成成功。")
