#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import mimetypes
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_DIR / ".env"

REPORTS_DIR = PROJECT_DIR / "reports"
DATA_DIR = PROJECT_DIR / "data" / "processed"

DASHBOARD_HTML = REPORTS_DIR / "dashboard_latest.html"
MARKET_HTML = REPORTS_DIR / "daily_market_report_v2_latest.html"

ENTRY_DECISION_CSV = DATA_DIR / "latest_entry_decision.csv"
MARKET_SCORE_CSV = DATA_DIR / "market_indicator_score_latest.csv"
ACCOUNT_SNAPSHOT_CSV = DATA_DIR / "account_snapshot_latest.csv"
DYNAMIC_ENTRY_CSV = DATA_DIR / "dynamic_entry_points_latest.csv"
CROSS_VALIDATION_CSV = DATA_DIR / "cross_validation_alpha_vantage_latest.csv"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}

    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()

    return env


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv_rows(path)
    return rows[0] if rows else {}


def money(value: str | float | int | None) -> str:
    try:
        if value is None or value == "":
            return "-"
        return f"${float(value):,.2f}"
    except Exception:
        return str(value)


def pct(value: str | float | int | None) -> str:
    try:
        if value is None or value == "":
            return "-"
        v = float(value)
        if abs(v) <= 1:
            return f"{v * 100:.2f}%"
        return f"{v:.2f}%"
    except Exception:
        return str(value)


def short_text(value: str | None, default: str = "-") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def build_summary() -> tuple[str, str]:
    today = date.today().isoformat()

    entry = first_row(ENTRY_DECISION_CSV)
    account = first_row(ACCOUNT_SNAPSHOT_CSV)
    validation_rows = read_csv_rows(CROSS_VALIDATION_CSV)
    score_rows = read_csv_rows(MARKET_SCORE_CSV)
    dynamic_rows = read_csv_rows(DYNAMIC_ENTRY_CSV)

    decision = short_text(entry.get("recommendation"))
    suggested_amount = money(entry.get("suggested_amount"))
    decision_sentence = short_text(entry.get("decision_sentence"))

    validation_status = "unknown"
    if validation_rows:
        ok_count = sum(1 for r in validation_rows if short_text(r.get("status")).lower() in {"ok", "passed"})
        total_count = len(validation_rows)
        pass_count = sum(1 for r in validation_rows if short_text(r.get("pass_price_check")).lower() in {"true", "1", "yes"})
        validation_status = f"{pass_count}/{total_count} 通过"

    cash_balance = money(account.get("cash_balance"))
    total_market_value = money(account.get("total_market_value"))
    total_equity = money(account.get("total_equity"))
    position_status = short_text(account.get("position_status"))
    total_pnl = money(account.get("total_pnl"))
    trade_count = short_text(account.get("trade_count"))

    score_lines = []
    for r in score_rows[:8]:
        score_lines.append(
            f"- {short_text(r.get('ticker'))}: "
            f"Market Score {short_text(r.get('market_score'))}, "
            f"状态 {short_text(r.get('score_status'))}, "
            f"建议金额 {money(r.get('suggested_buy_amount'))}"
        )

    dynamic_current_lines = []
    seen_current = set()
    for r in dynamic_rows:
        ticker = short_text(r.get("ticker"))
        level = short_text(r.get("entry_level"))
        if level != "current" or ticker in seen_current:
            continue
        seen_current.add(ticker)
        dynamic_current_lines.append(
            f"- {ticker}: 当前价 {money(r.get('entry_price'))}, "
            f"当前回撤 {pct(r.get('current_drawdown'))}, "
            f"手续费占比 {pct(r.get('fee_ratio'))}, "
            f"成本状态 {short_text(r.get('cost_status'))}"
        )

    if not score_lines:
        score_lines = ["- Market Score 数据暂未生成"]

    if not dynamic_current_lines:
        dynamic_current_lines = ["- 动态入场点位数据暂未生成"]

    text_body = f"""ETF Daily Report - {today}

今日入场建议：
{decision_sentence}
建议金额：{suggested_amount}
数据验证：{validation_status}

实仓账户：
账户状态：{position_status}
现金余额：{cash_balance}
持仓市值：{total_market_value}
总资产：{total_equity}
总盈亏：{total_pnl}
交易笔数：{trade_count}

Market Score：
{chr(10).join(score_lines)}

动态入场点位 current：
{chr(10).join(dynamic_current_lines)}

附件：
- dashboard_latest.html
- daily_market_report_v2_latest.html

提示：
本邮件仅用于每日监控和提醒，不代表自动交易指令。所有买入、卖出必须人工确认。
"""

    html_score = "".join(f"<li>{line[2:]}</li>" for line in score_lines)
    html_dynamic = "".join(f"<li>{line[2:]}</li>" for line in dynamic_current_lines)

    html_body = f"""
<html>
<body>
  <h2>ETF Daily Report - {today}</h2>

  <h3>今日入场建议</h3>
  <p>{decision_sentence}</p>
  <p><b>建议金额：</b>{suggested_amount}</p>
  <p><b>数据验证：</b>{validation_status}</p>

  <h3>实仓账户</h3>
  <ul>
    <li>账户状态：{position_status}</li>
    <li>现金余额：{cash_balance}</li>
    <li>持仓市值：{total_market_value}</li>
    <li>总资产：{total_equity}</li>
    <li>总盈亏：{total_pnl}</li>
    <li>交易笔数：{trade_count}</li>
  </ul>

  <h3>Market Score</h3>
  <ul>
    {html_score}
  </ul>

  <h3>动态入场点位 current</h3>
  <ul>
    {html_dynamic}
  </ul>

  <p><b>附件：</b>dashboard_latest.html、daily_market_report_v2_latest.html</p>

  <p style="color:#666;">
    本邮件仅用于每日监控和提醒，不代表自动交易指令。所有买入、卖出必须人工确认。
  </p>
</body>
</html>
"""

    return text_body, html_body


def attach_file(msg: EmailMessage, path: Path) -> None:
    if not path.exists():
        print(f"附件不存在，跳过：{path}")
        return

    ctype, encoding = mimetypes.guess_type(str(path))
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)
    data = path.read_bytes()

    msg.add_attachment(
        data,
        maintype=maintype,
        subtype=subtype,
        filename=path.name,
    )


def send_email(force: bool = False, dry_run: bool = False) -> None:
    env = load_env(ENV_PATH)

    email_enabled = env.get("EMAIL_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

    if not email_enabled and not force:
        print("EMAIL_ENABLED=false，跳过发送。测试发送请使用 --force。")
        return

    required_keys = [
        "EMAIL_FROM",
        "EMAIL_TO",
        "EMAIL_SMTP_HOST",
        "EMAIL_SMTP_PORT",
        "EMAIL_APP_PASSWORD",
    ]

    missing = [key for key in required_keys if not env.get(key)]
    if missing:
        raise SystemExit(f"缺少邮件配置：{', '.join(missing)}")

    today = date.today().isoformat()

    text_body, html_body = build_summary()

    msg = EmailMessage()
    msg["From"] = env["EMAIL_FROM"]
    msg["To"] = env["EMAIL_TO"]
    msg["Subject"] = f"ETF Daily Report - {today}"

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    attach_file(msg, DASHBOARD_HTML)
    attach_file(msg, MARKET_HTML)

    print("准备发送邮件：")
    print(f"From: {env['EMAIL_FROM']}")
    print(f"To: {env['EMAIL_TO']}")
    print(f"Subject: {msg['Subject']}")
    print(f"Attachment dashboard_latest.html: {DASHBOARD_HTML.exists()}")
    print(f"Attachment daily_market_report_v2_latest.html: {MARKET_HTML.exists()}")

    if dry_run:
        print("dry-run 模式：不实际发送。")
        return

    smtp_host = env["EMAIL_SMTP_HOST"]
    smtp_port = int(env["EMAIL_SMTP_PORT"])

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(env["EMAIL_FROM"], env["EMAIL_APP_PASSWORD"])
        server.send_message(msg)

    print("邮件发送完成。")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="忽略 EMAIL_ENABLED=false，强制发送一次")
    parser.add_argument("--dry-run", action="store_true", help="只检查和预览，不实际发送")
    args = parser.parse_args()

    send_email(force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
