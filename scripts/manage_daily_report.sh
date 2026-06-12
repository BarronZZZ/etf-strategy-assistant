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

ACCOUNT_REPORT="$PROJECT_DIR/reports/portfolio_accounting_latest.md"
ACCOUNT_SNAPSHOT_CSV="$PROJECT_DIR/data/processed/account_snapshot_latest.csv"
CURRENT_POSITIONS_CSV="$PROJECT_DIR/data/processed/current_positions.csv"
PORTFOLIO_HISTORY_CSV="$PROJECT_DIR/data/processed/portfolio_history.csv"

DYNAMIC_ENTRY_REPORT="$PROJECT_DIR/reports/dynamic_entry_points_latest.md"
DYNAMIC_ENTRY_CSV="$PROJECT_DIR/data/processed/dynamic_entry_points_latest.csv"

open_text_file() {
  FILE_PATH="$1"
  LABEL_NAME="$2"

  if [ ! -f "$FILE_PATH" ]; then
    echo "$LABEL_NAME 不存在：$FILE_PATH"
    echo "可先运行：bash scripts/manage_daily_report.sh run-now"
    exit 1
  fi

  echo "打开 $LABEL_NAME..."
  if command -v code >/dev/null 2>&1; then
    code "$FILE_PATH"
  else
    open -a TextEdit "$FILE_PATH"
  fi
}

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

    echo ""
    echo "===== V1.3 实仓账户模块检查 ====="
    echo "实仓账户 Markdown 报告：$ACCOUNT_REPORT"
    [ -f "$ACCOUNT_REPORT" ] && echo "实仓账户 Markdown：存在" || echo "实仓账户 Markdown：不存在"

    echo "账户快照 CSV：$ACCOUNT_SNAPSHOT_CSV"
    [ -f "$ACCOUNT_SNAPSHOT_CSV" ] && echo "账户快照 CSV：存在" || echo "账户快照 CSV：不存在"

    echo "当前持仓 CSV：$CURRENT_POSITIONS_CSV"
    [ -f "$CURRENT_POSITIONS_CSV" ] && echo "当前持仓 CSV：存在" || echo "当前持仓 CSV：不存在"

    echo "账户历史 CSV：$PORTFOLIO_HISTORY_CSV"
    [ -f "$PORTFOLIO_HISTORY_CSV" ] && echo "账户历史 CSV：存在" || echo "账户历史 CSV：不存在"

    if [ -f "$DASHBOARD_REPORT" ]; then
      grep -q "V1.3 实仓账户跟踪" "$DASHBOARD_REPORT" && echo "Dashboard V1.3 模块：存在" || echo "Dashboard V1.3 模块：不存在"
    fi

    echo ""
    echo "===== V1.4 动态入场点位模块检查 ====="
    echo "动态入场点位 Markdown 报告：$DYNAMIC_ENTRY_REPORT"
    [ -f "$DYNAMIC_ENTRY_REPORT" ] && echo "动态入场点位 Markdown：存在" || echo "动态入场点位 Markdown：不存在"

    echo "动态入场点位 CSV：$DYNAMIC_ENTRY_CSV"
    [ -f "$DYNAMIC_ENTRY_CSV" ] && echo "动态入场点位 CSV：存在" || echo "动态入场点位 CSV：不存在"

    if [ -f "$DASHBOARD_REPORT" ]; then
      grep -q "V1.4 动态入场点位收益率" "$DASHBOARD_REPORT" && echo "Dashboard V1.4 模块：存在" || echo "Dashboard V1.4 模块：不存在"
    fi
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
    open_text_file "$ENTRY_DECISION_REPORT" "入场决策 Markdown 报告"
    ;;

  score|market-score)
    open_text_file "$MARKET_SCORE_REPORT" "Market Score Markdown 报告"
    ;;

  account|portfolio)
    open_text_file "$ACCOUNT_REPORT" "V1.3 实仓账户 Markdown 报告"
    ;;

  dynamic|entry-points)
    open_text_file "$DYNAMIC_ENTRY_REPORT" "V1.4 动态入场点位 Markdown 报告"
    ;;

  open-md)
    open_text_file "$MD_REPORT" "Markdown 最新早报"
    ;;

  stop)
    echo "停止当前每日早报任务..."
    launchctl stop "$LABEL" 2>/dev/null || true
    pkill -f "run_daily_report.sh" 2>/dev/null || true
    pkill -f "09_daily_market_report_v1.py" 2>/dev/null || true
    pkill -f "11_alpha_vantage_cross_validation.py" 2>/dev/null || true
    pkill -f "14_entry_decision_v1.py" 2>/dev/null || true
    pkill -f "16_market_indicator_score_v1.py" 2>/dev/null || true
    pkill -f "17_portfolio_accounting_v1.py" 2>/dev/null || true
    pkill -f "20_dynamic_entry_points_v1.py" 2>/dev/null || true
    pkill -f "12_daily_market_report_v2_with_validation.py" 2>/dev/null || true
    pkill -f "13_daily_market_report_html.py" 2>/dev/null || true
    pkill -f "15_dashboard_report_v1.py" 2>/dev/null || true
    pkill -f "19_dashboard_account_section_v1.py" 2>/dev/null || true
    pkill -f "21_dashboard_dynamic_entry_section_v1.py" 2>/dev/null || true
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
    echo "用法：bash scripts/manage_daily_report.sh {status|run|run-now|log|err|today|open|dashboard|entry|score|account|dynamic|open-md|stop|load|unload|remove}"
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
    echo "  entry       打开入场决策报告"
    echo "  score       打开 Market Score 报告"
    echo "  account     打开 V1.3 实仓账户报告"
    echo "  dynamic     打开 V1.4 动态入场点位报告"
    echo "  open-md     打开 Markdown 最新早报"
    echo "  stop        停止当前正在运行的任务"
    ;;

esac
