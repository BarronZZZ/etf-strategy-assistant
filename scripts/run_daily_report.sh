#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

TODAY=$(date +"%Y-%m-%d")
LOG_FILE="logs/daily_report_${TODAY}.log"

mkdir -p logs reports data/processed

PYTHON="/opt/anaconda3/envs/etf_strategy/bin/python -u"

# 是否在每日报告生成完成后自动打开 Dashboard
# true = 自动打开；false = 只生成不打开
AUTO_OPEN_DASHBOARD="${AUTO_OPEN_DASHBOARD:-true}"

echo "========================================" | tee -a "$LOG_FILE"
echo "ETF Strategy Assistant Daily Report" | tee -a "$LOG_FILE"
echo "Run date: $TODAY" | tee -a "$LOG_FILE"
echo "Project dir: $PROJECT_DIR" | tee -a "$LOG_FILE"
echo "Python: $PYTHON" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 1/12: 生成每日市场数据和市场信号..." | tee -a "$LOG_FILE"
$PYTHON notebooks/09_daily_market_report_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 2/12: 运行 Alpha Vantage 价格交叉验证..." | tee -a "$LOG_FILE"
$PYTHON notebooks/11_alpha_vantage_cross_validation.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 3/12: 生成每日入场决策..." | tee -a "$LOG_FILE"
$PYTHON notebooks/14_entry_decision_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 4/12: 生成 Market Indicator Score 多指标评分..." | tee -a "$LOG_FILE"
$PYTHON notebooks/16_market_indicator_score_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 5/12: 生成实仓账户快照..." | tee -a "$LOG_FILE"
$PYTHON notebooks/17_portfolio_accounting_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 6/12: 生成动态入场点位收益率..." | tee -a "$LOG_FILE"
$PYTHON notebooks/20_dynamic_entry_points_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 7/12: 生成 Markdown 每日市场早报 V2..." | tee -a "$LOG_FILE"
$PYTHON notebooks/12_daily_market_report_v2_with_validation.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 8/12: 生成 HTML 每日市场早报 V2..." | tee -a "$LOG_FILE"
$PYTHON notebooks/13_daily_market_report_html.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 9/12: 生成 Dashboard 报告..." | tee -a "$LOG_FILE"
$PYTHON notebooks/15_dashboard_report_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 10/12: 接入 V1.3 实仓账户 Dashboard 模块..." | tee -a "$LOG_FILE"
$PYTHON notebooks/19_dashboard_account_section_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 11/12: 接入 V1.4 动态入场点位 Dashboard 模块..." | tee -a "$LOG_FILE"
$PYTHON notebooks/21_dashboard_dynamic_entry_section_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "每日早报运行完成" | tee -a "$LOG_FILE"
echo "Markdown 最新早报：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/daily_market_report_v2_latest.md" | tee -a "$LOG_FILE"
echo "HTML 最新早报：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/daily_market_report_v2_latest.html" | tee -a "$LOG_FILE"
echo "Dashboard 最新报告：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/dashboard_latest.html" | tee -a "$LOG_FILE"
echo "入场决策报告：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/daily_entry_decision_latest.md" | tee -a "$LOG_FILE"
echo "Market Score 报告：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/market_indicator_score_latest.md" | tee -a "$LOG_FILE"
echo "实仓账户报告：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/portfolio_accounting_latest.md" | tee -a "$LOG_FILE"
echo "动态入场点位报告：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/dynamic_entry_points_latest.md" | tee -a "$LOG_FILE"
echo "运行日志：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/$LOG_FILE" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
if [ "$AUTO_OPEN_DASHBOARD" = "true" ]; then
  
echo ""
echo "Step 12/12: 发送 ETF 每日报告邮件..."
$PYTHON "$PROJECT_DIR/scripts/send_daily_email.py"
\echo "自动打开 Dashboard 网页..." | tee -a "$LOG_FILE"
  /usr/bin/open "$PROJECT_DIR/reports/dashboard_latest.html" || echo "自动打开失败，请手动运行：bash scripts/manage_daily_report.sh dashboard" | tee -a "$LOG_FILE"
else
  echo "AUTO_OPEN_DASHBOARD=false，已生成报告但不自动打开 Dashboard。" | tee -a "$LOG_FILE"
fi

echo "========================================" | tee -a "$LOG_FILE"
