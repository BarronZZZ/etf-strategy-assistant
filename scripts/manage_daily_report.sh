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

case "$1" in

  status)
    echo "===== 自动任务状态 ====="
    launchctl list | grep "$LABEL" || echo "未找到任务：$LABEL"
    echo ""
    echo "Plist 文件：$PLIST"
    echo "Plist 是否存在："
    [ -f "$PLIST" ] && echo "存在" || echo "不存在"
    echo ""
    echo "今日运行日志：$DAILY_LOG"
    [ -f "$DAILY_LOG" ] && echo "存在" || echo "不存在"
    echo ""
    echo "HTML 最新早报：$HTML_REPORT"
    [ -f "$HTML_REPORT" ] && echo "存在" || echo "不存在"
    ;;

  run)
    echo "手动启动每日早报任务..."
    launchctl start "$LABEL"
    echo "已发送启动命令。请等待 30 秒到几分钟后查看日志："
    echo "bash scripts/manage_daily_report.sh log"
    ;;

  log)
    echo "===== launchd 输出日志 ====="
    tail -120 "$OUT_LOG"
    ;;

  err)
    echo "===== launchd 错误日志 ====="
    if [ -f "$ERR_LOG" ]; then
      tail -120 "$ERR_LOG"
    else
      echo "错误日志不存在。"
    fi
    ;;

  today)
    echo "===== 今日每日早报运行日志 ====="
    if [ -f "$DAILY_LOG" ]; then
      tail -160 "$DAILY_LOG"
    else
      echo "今日运行日志不存在：$DAILY_LOG"
    fi
    ;;

  open)
    echo "打开 HTML 最新早报..."
    open "$HTML_REPORT"
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
    pkill -f "12_daily_market_report_v2_with_validation.py" 2>/dev/null || true
    pkill -f "13_daily_market_report_html.py" 2>/dev/null || true
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
    echo "用法：bash scripts/manage_daily_report.sh {status|run|log|err|today|open|open-md|stop|load|unload|remove}"
    echo ""
    echo "常用命令："
    echo "  status   查看自动任务状态"
    echo "  run      手动启动每日早报"
    echo "  log      查看 launchd 输出日志"
    echo "  err      查看 launchd 错误日志"
    echo "  today    查看今日完整运行日志"
    echo "  open     打开 HTML 最新早报"
    echo "  stop     停止当前正在运行的任务"
    ;;

esac
