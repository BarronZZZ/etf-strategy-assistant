#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

TODAY=$(date +"%Y-%m-%d")
LOG_FILE="logs/daily_report_${TODAY}.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "ETF Strategy Assistant Daily Report" | tee -a "$LOG_FILE"
echo "Run date: $TODAY" | tee -a "$LOG_FILE"
echo "Project dir: $PROJECT_DIR" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 1/4: 生成每日市场数据和市场信号..." | tee -a "$LOG_FILE"
/opt/anaconda3/envs/etf_strategy/bin/python -u notebooks/09_daily_market_report_v1.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 2/4: 运行 Alpha Vantage 价格交叉验证..." | tee -a "$LOG_FILE"
/opt/anaconda3/envs/etf_strategy/bin/python -u notebooks/11_alpha_vantage_cross_validation.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 3/4: 生成 Markdown 每日市场早报 V2..." | tee -a "$LOG_FILE"
/opt/anaconda3/envs/etf_strategy/bin/python -u notebooks/12_daily_market_report_v2_with_validation.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Step 4/4: 生成 HTML 每日市场早报 V2..." | tee -a "$LOG_FILE"
/opt/anaconda3/envs/etf_strategy/bin/python -u notebooks/13_daily_market_report_html.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "每日早报运行完成" | tee -a "$LOG_FILE"
echo "Markdown 最新早报：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/daily_market_report_v2_latest.md" | tee -a "$LOG_FILE"
echo "HTML 最新早报：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/reports/daily_market_report_v2_latest.html" | tee -a "$LOG_FILE"
echo "运行日志：" | tee -a "$LOG_FILE"
echo "$PROJECT_DIR/$LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
