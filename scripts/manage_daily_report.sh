#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

LABEL="com.bz.etfstrategy.dailyreport"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

OUT_LOG="$PROJECT_DIR/logs/launchd_daily_report.out"
ERR_LOG="$PROJECT_DIR/logs/launchd_daily_report.err"
DAILY_LOG="$PROJECT_DIR/logs/daily_report_$(date +"%Y-%m-%d").log"

HTML_REPORT="$PROJECT_DIR/reports/daily_market_report_v2_latest.html"
MD_REPORT="$PROJECT_DIR/reports/daily_market_report_v2_latest.md"
DASHBOARD_REPORT="$PROJECT_DIR/reports/dashboard_latest.html"
ENTRY_DECISION_REPORT="$PROJECT_DIR/reports/daily_entry_decision_latest.md"
MARKET_SCORE_REPORT="$PROJECT_DIR/reports/market_indicator_score_latest.md"
MARKET_SCORE_CSV="$PROJECT_DIR/data/processed/market_indicator_score_latest.csv"

case "$1" in

  status)
    echo "===== 自动任务状态 ====="
    launchctl list | grep "$LABEL" || echo "未找到任务：$LABEL"

    echo ""
    echo "===== 文件检查 ====="
    echo "Plist 文件：$PLIST"
    [ -f "$PLIST" ] && echo "Plist：存在" || echo "Plist：不存在"

    echo ""
    echo "今日运行日志：$DAILY_LOG"
    [ -f "$DAILY_LOG" ] && echo "今日运行日志：存在" || echo "今日运行日志：不存在"

    echo ""
    echo "Markdown 最新早报：$MD_REPORT"
    [ -f "$MD_REPORT" ] && echo "Markdown：存在" || echo "Markdown：不存在"

    echo ""
    echo "HTML 最新早报：$HTML_REPORT"
    [ -f "$HTML_REPORT" ] && echo "HTML：存在" || echo "HTML：不存在"

    echo ""
    echo "Dashboard 最新报告：$DASHBOARD_REPORT"
    [ -f "$DASHBOARD_REPORT" ] && echo "Dashboard：存在" || echo "Dashboard：不存在"

    echo ""
    echo "入场决策报告：$ENTRY_DECISION_REPORT"
    [ -f "$ENTRY_DECISION_REPORT" ] && echo "入场决策：存在" || echo "入场决策：不存在"

    echo ""
    echo "Market Score Markdown 报告：$MARKET_SCORE_REPORT"
    [ -f "$MARKET_SCORE_REPORT" ] && echo "Market Score Markdown：存在" || echo "Market Score Markdown：不存在"

    echo ""
    echo "Market Score CSV 数据：$MARKET_SCORE_CSV"
    [ -f "$MARKET_SCORE_CSV" ] && echo "Market Score CSV：存在" || echo "Market Score CSV：不存在"
    ;;

  run)
    echo "手动启动每日早报任务..."
    launchctl start "$LABEL"
    echo "已发送启动命令。请等待 30 秒到几分钟后查看日志："
    echo "bash scripts/manage_daily_report.sh log"
    ;;

  run-now)
    echo "直接运行每日早报脚本..."
    bash scripts/run_daily_report.sh
    ;;

  log)
    echo "===== launchd 输出日志 ====="
    if [ -f "$OUT_LOG" ]; then
      tail -120 "$OUT_LOG"
    else
      echo "输出日志不存在：$OUT_LOG"
    fi
    ;;

  err)
    echo "===== launchd 错误日志 ====="
    if [ -f "$ERR_LOG" ]; then
      tail -120 "$ERR_LOG"
    else
      echo "错误日志不存在：$ERR_LOG"
    fi
    ;;

  today)
    echo "===== 今日每日早报运行日志 ====="
    if [ -f "$DAILY_LOG" ]; then
      tail -180 "$DAILY_LOG"
    else
      echo "今日运行日志不存在：$DAILY_LOG"
    fi
    ;;

  open)
    echo "打开 HTML 最新早报..."
    open "$HTML_REPORT"
    ;;

  dashboard|open-dashboard)
    echo "打开 Dashboard 最新报告..."
    open "$DASHBOARD_REPORT"
    ;;

  entry)
    echo "打开入场决策 Markdown 报告..."
    open "$ENTRY_DECISION_REPORT"
    ;;

  score|market-score)
    echo "打开 Market Score Markdown 报告..."
    if command -v code >/dev/null 2>&1; then
      code "$MARKET_SCORE_REPORT"
    else
      open -a TextEdit "$MARKET_SCORE_REPORT"
    fi
    ;;

  open-md)
    echo "打开 Markdown 最新早报..."
    open "$MD_REPORT"
    ;;

  stop)
    echo "停止当前每日早报任务..."
    launchctl stop "$LABEL" 2>/dev/null || true
    pkill -f "run_daily_report.sh" 2>/dev/null || true
    pkill -f "09_daily_market_report_v1.py" 2>/dev/null || true
    pkill -f "11_alpha_vantage_cross_validation.py" 2>/dev/null || true
    pkill -f "14_entry_decision_v1.py" 2>/dev/null || true
    pkill -f "12_daily_market_report_v2_with_validation.py" 2>/dev/null || true
    pkill -f "13_daily_market_report_html.py" 2>/dev/null || true
    pkill -f "15_dashboard_report_v1.py" 2>/dev/null || true
    echo "已尝试停止。"
    ;;

  unload)
    echo "卸载每日早报自动任务..."
    launchctl unload "$PLIST" 2>/dev/null || true
    echo "已卸载。"
    ;;

  load)
    echo "加载每日早报自动任务..."
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    echo "已加载。"
    launchctl list | grep "$LABEL" || true
    ;;

  remove)
    echo "卸载并删除每日早报自动任务..."
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "已删除：$PLIST"
    ;;

  *)
    echo "用法：bash scripts/manage_daily_report.sh {status|run|run-now|log|err|today|open|dashboard|entry|score|open-md|stop|load|unload|remove}"
    echo ""
    echo "常用命令："
    echo "  status      查看自动任务状态和报告文件"
    echo "  run         通过 launchd 手动启动每日早报"
    echo "  run-now     直接运行每日早报脚本"
    echo "  log         查看 launchd 输出日志"
    echo "  err         查看 launchd 错误日志"
    echo "  today       查看今日完整运行日志"
    echo "  open        打开普通 HTML 早报"
    echo "  dashboard   打开 Dashboard 报告"
    echo "  entry       打开入场决策报告"\n    echo "  score       打开 Market Score 报告"
    echo "  stop        停止当前正在运行的任务"
    ;;

esac
