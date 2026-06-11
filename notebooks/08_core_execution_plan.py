from pathlib import Path
import pandas as pd
from datetime import datetime


# =========================
# 1. 路径设置
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

config_dir = PROJECT_ROOT / "config"
processed_dir = PROJECT_ROOT / "data" / "processed"
reports_dir = PROJECT_ROOT / "reports"

processed_dir.mkdir(exist_ok=True)
reports_dir.mkdir(exist_ok=True)

core_config_path = config_dir / "etf_universe_usd.csv"

print("项目路径：", PROJECT_ROOT)
print("长期核心配置文件：", core_config_path)


# =========================
# 2. 读取长期核心配置
# =========================

core = pd.read_csv(core_config_path)

print("\n===== 长期核心 ETF 配置 =====")
print(core)

print("\n目标权重合计：", core["target_weight"].sum())
print("目标金额合计：", core["target_amount"].sum())


# =========================
# 3. 设置建仓计划
# =========================

total_capital = 50000

initial_buy_pct = 0.40
initial_buy_amount = total_capital * initial_buy_pct

remaining_amount = total_capital - initial_buy_amount
monthly_tranches = 6
monthly_buy_amount = remaining_amount / monthly_tranches

print("\n===== 建仓计划 =====")
print("总金额：", total_capital)
print("首笔比例：", initial_buy_pct)
print("首笔金额：", initial_buy_amount)
print("剩余金额：", remaining_amount)
print("分批月数：", monthly_tranches)
print("每月买入金额：", monthly_buy_amount)


# =========================
# 4. 生成每期买入计划
# =========================

schedule_rows = []

# 第 0 期：首笔 40%
schedule_rows.append({
    "phase": 0,
    "phase_name": "initial_40pct",
    "planned_amount": initial_buy_amount,
    "rule": "首笔建仓，按目标权重买入",
    "status": "planned"
})

# 后续 6 期
for i in range(1, monthly_tranches + 1):
    schedule_rows.append({
        "phase": i,
        "phase_name": f"monthly_dca_{i}",
        "planned_amount": monthly_buy_amount,
        "rule": "每月固定分批买入，按目标权重买入",
        "status": "planned"
    })

schedule = pd.DataFrame(schedule_rows)

schedule_path = processed_dir / "core_execution_schedule.csv"
schedule.to_csv(schedule_path, index=False)

print("\n===== 建仓期数计划 =====")
print(schedule)

print("\n建仓期数计划已保存：", schedule_path)


# =========================
# 5. 生成每期按 ETF 拆分的买入金额
# =========================

detail_rows = []

for _, phase_row in schedule.iterrows():
    for _, etf_row in core.iterrows():
        detail_rows.append({
            "phase": phase_row["phase"],
            "phase_name": phase_row["phase_name"],
            "ticker": etf_row["ticker"],
            "role": etf_row["role"],
            "target_weight": etf_row["target_weight"],
            "phase_total_amount": phase_row["planned_amount"],
            "planned_buy_amount": phase_row["planned_amount"] * etf_row["target_weight"],
            "currency": etf_row["currency"],
            "account": etf_row["account"],
            "status": "planned"
        })

detail = pd.DataFrame(detail_rows)

detail_path = processed_dir / "core_execution_detail.csv"
detail.to_csv(detail_path, index=False)

print("\n===== 每期 ETF 买入金额明细 =====")
print(detail)

print("\n每期 ETF 买入金额明细已保存：", detail_path)


# =========================
# 6. 生成风险提醒规则
# =========================

risk_rules = pd.DataFrame([
    {
        "rule_id": "VTI_DD_10",
        "signal": "VTI_252d_drawdown <= -10%",
        "action": "提醒：可以考虑提前买入下一期，但不自动执行",
        "auto_execute": False
    },
    {
        "rule_id": "VTI_DD_15",
        "signal": "VTI_252d_drawdown <= -15%",
        "action": "提醒：可以考虑提前买入后续两期，但不自动执行",
        "auto_execute": False
    },
    {
        "rule_id": "VTI_DD_25",
        "signal": "VTI_252d_drawdown <= -25%",
        "action": "提醒：可以考虑加快完成剩余建仓，但必须人工确认",
        "auto_execute": False
    },
    {
        "rule_id": "CORE_REBALANCE",
        "signal": "任一ETF实际权重偏离目标权重超过5个百分点",
        "action": "提醒：考虑再平衡，不自动交易",
        "auto_execute": False
    }
])

risk_rules_path = processed_dir / "core_risk_alert_rules.csv"
risk_rules.to_csv(risk_rules_path, index=False)

print("\n===== 长期组合风险提醒规则 =====")
print(risk_rules)

print("\n风险提醒规则已保存：", risk_rules_path)


# =========================
# 7. 生成 Markdown 摘要报告
# =========================

report_path = reports_dir / "core_execution_plan.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write("# 美元长期 ETF 核心组合执行计划\n\n")
    f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    f.write("## 1. 长期核心配置\n\n")
    f.write(core[["ticker", "role", "target_weight", "target_amount"]].to_markdown(index=False))
    f.write("\n\n")

    f.write("## 2. 建仓节奏\n\n")
    f.write(f"- 总金额：${total_capital:,.0f}\n")
    f.write(f"- 首笔买入：${initial_buy_amount:,.0f}，占 {initial_buy_pct:.0%}\n")
    f.write(f"- 剩余金额：${remaining_amount:,.0f}\n")
    f.write(f"- 分 {monthly_tranches} 个月买入，每月 ${monthly_buy_amount:,.0f}\n\n")

    f.write("## 3. 每期买入金额\n\n")
    f.write(schedule.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 4. 风险提醒规则\n\n")
    f.write(risk_rules.to_markdown(index=False))
    f.write("\n\n")

    f.write("## 5. 当前执行结论\n\n")
    f.write("默认执行固定分批建仓：首笔 40%，剩余 6 个月平均买入。\n\n")
    f.write("Smart DCA 只作为提醒，不自动提前买入。\n")

print("\nMarkdown 执行计划已保存：", report_path)


print("\n第 15 步完成：长期核心建仓执行计划生成成功。")
