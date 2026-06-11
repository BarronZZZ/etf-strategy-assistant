from pathlib import Path
from datetime import datetime
import pandas as pd


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

today_str = datetime.now().strftime("%Y-%m-%d")

print("项目路径：", PROJECT_ROOT)


# =========================
# 2. 读取已有每日市场数据
# =========================

performance_path = processed_dir / "latest_market_performance.csv"
signals_path = processed_dir / "latest_market_signals.csv"
validation_path = processed_dir / "cross_validation_alpha_vantage_latest.csv"
av_log_path = processed_dir / "alpha_vantage_download_log_latest.csv"

required_files = [
    performance_path,
    signals_path,
    validation_path,
    av_log_path
]

for path in required_files:
    print(f"{path.name} 是否存在：", path.exists())

missing_files = [path for path in required_files if not path.exists()]

if missing_files:
    raise FileNotFoundError(
        "以下文件不存在，请先运行第17步和第20步：\n"
        + "\n".join(str(p) for p in missing_files)
    )


performance = pd.read_csv(performance_path, index_col=0)
signals = pd.read_csv(signals_path)
validation = pd.read_csv(validation_path)
av_log = pd.read_csv(av_log_path)

print("\n===== 市场表现数据 =====")
print(performance.head())

print("\n===== 市场信号 =====")
print(signals)

print("\n===== Alpha Vantage 交叉验证结果 =====")
print(validation)


# =========================
# 3. 判断交叉验证状态
# =========================

total_validation = len(validation)
passed_validation = int(validation["pass_price_check"].sum())
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

print("\n===== 数据交叉验证状态 =====")
print("状态：", data_validation_status)
print("摘要：", data_validation_summary)


# =========================
# 4. 判断市场风险状态
# =========================

triggered = signals[signals["triggered"] == True].copy()

high_alert_count = (triggered["action_level"] == "high_alert").sum()
alert_count = (triggered["action_level"] == "alert").sum()
warning_count = (triggered["action_level"] == "warning").sum()
watch_count = (triggered["action_level"] == "watch").sum()

if high_alert_count > 0:
    market_status = "高风险"
    action_summary = "暂停自动交易，只做人工确认；长期账户可以观察是否有分批加仓机会。"
elif alert_count > 0:
    market_status = "偏高风险"
    action_summary = "不建议激进加仓；长期账户按计划执行，提前买入需要人工确认。"
elif warning_count > 0:
    market_status = "中等风险"
    action_summary = "长期账户继续按计划执行；短线交易降低仓位。"
elif watch_count > 0:
    market_status = "观察状态"
    action_summary = "长期账户可以继续执行固定分批；如有回撤提醒，可以考虑但不自动提前买入。"
else:
    market_status = "正常"
    action_summary = "长期账户按固定计划执行；短线账户只做观察，不自动交易。"


# 如果交叉验证没有 passed，强制降低交易自动化级别
if data_validation_status != "passed":
    final_trade_permission = "禁止自动交易，只允许人工查看"
    final_action_summary = (
        action_summary
        + " 但由于数据交叉验证未完全通过，本日报告只作为观察，不作为交易执行依据。"
    )
else:
    final_trade_permission = "自动交易关闭；允许生成交易提醒"
    final_action_summary = action_summary

print("\n===== 综合状态 =====")
print("市场状态：", market_status)
print("数据验证：", data_validation_status)
print("交易权限：", final_trade_permission)
print("操作摘要：", final_action_summary)


# =========================
# 5. 整理报告表格
# =========================

core_tickers = ["VTI", "VEA", "VWO", "SGOV"]
core_perf = performance.loc[[t for t in core_tickers if t in performance.index]].copy()

top_3m = performance.sort_values("return_3m", ascending=False).head(5)
bottom_3m = performance.sort_values("return_3m", ascending=True).head(5)

failed_validation_table = validation[validation["pass_price_check"] == False].copy()


# =========================
# 6. 生成 Markdown V2 早报
# =========================

report_path = reports_dir / f"daily_market_report_v2_{today_str}.md"
latest_report_path = reports_dir / "daily_market_report_v2_latest.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# 每日市场早报 V2 - {today_str}\n\n")

    f.write("## 1. 综合结论\n\n")
    f.write(f"- 市场状态：**{market_status}**\n")
    f.write(f"- 数据交叉验证：**{data_validation_status}**\n")
    f.write(f"- 验证摘要：{data_validation_summary}\n")
    f.write(f"- 交易权限：**{final_trade_permission}**\n")
    f.write(f"- 操作摘要：{final_action_summary}\n\n")

    f.write("## 2. 长期核心账户观察\n\n")
    f.write(core_perf[[
        "latest_price",
        "return_1d",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "above_200ma",
        "drawdown_252d"
    ]].to_markdown())
    f.write("\n\n")

    f.write("## 3. 今日触发信号\n\n")
    if triggered.empty:
        f.write("今日没有触发高优先级风险信号。\n\n")
    else:
        f.write(triggered[[
            "rule_id",
            "category",
            "action_level",
            "meaning",
            "detail",
            "auto_trade"
        ]].to_markdown(index=False))
        f.write("\n\n")

    f.write("## 4. 数据交叉验证明细\n\n")
    f.write(validation[[
        "ticker",
        "status",
        "common_date",
        "yf_close",
        "av_close",
        "pct_diff",
        "pass_price_check",
        "notes"
    ]].to_markdown(index=False))
    f.write("\n\n")

    f.write("## 5. 数据验证异常标的\n\n")
    if failed_validation_table.empty:
        f.write("所有交叉验证标的均通过。\n\n")
    else:
        f.write(failed_validation_table.to_markdown(index=False))
        f.write("\n\n")

    f.write("## 6. 3个月表现靠前标的\n\n")
    f.write(top_3m[[
        "latest_price",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "above_200ma",
        "drawdown_252d"
    ]].to_markdown())
    f.write("\n\n")

    f.write("## 7. 3个月表现靠后标的\n\n")
    f.write(bottom_3m[[
        "latest_price",
        "return_1m",
        "return_3m",
        "return_6m",
        "return_12m",
        "above_200ma",
        "drawdown_252d"
    ]].to_markdown())
    f.write("\n\n")

    f.write("## 8. Alpha Vantage 下载日志\n\n")
    f.write(av_log.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 9. 数据说明\n\n")
    f.write("- 市场表现数据来自 yfinance。\n")
    f.write("- 价格交叉验证来自 Alpha Vantage TIME_SERIES_DAILY。\n")
    f.write("- 如果数据交叉验证不是 passed，本系统不允许自动交易。\n")
    f.write("- 当前版本只生成提醒，不自动下单。\n")

with open(report_path, "r", encoding="utf-8") as src:
    content = src.read()

with open(latest_report_path, "w", encoding="utf-8") as dst:
    dst.write(content)

print("\n每日市场早报 V2 已保存：", report_path)
print("最新每日市场早报 V2 已保存：", latest_report_path)

print("\n第 21 步完成：交叉验证已整合进每日市场早报 V2。")
