# CLAUDE.md

This file provides instructions for Claude Code when working on this repository.

## Project Overview

This project is ETF Strategy Assistant, a local Python-based system for long-term USD ETF allocation, daily market monitoring, price cross-validation, entry decision support, and dashboard reporting.

The project is designed for personal research, portfolio monitoring, and decision support only.

It must not place trades automatically.

## Current Version

Current stable version: V1.1

Main features:

- Long-term USD ETF core allocation
- Fixed DCA execution plan
- Smart DCA alerts only
- Daily market data update
- yfinance market data source
- Alpha Vantage price cross-validation
- Entry decision rules for empty position
- Buy / wait / manual review recommendation
- Markdown report
- HTML report
- Dashboard report
- macOS launchd daily automation
- GitHub version control
- API key safety protection

## Important Safety Rules

Never modify or commit the following files or directories:

- .env
- data/raw/
- logs/
- any file containing real API keys, passwords, tokens, or account credentials

Never expose or print the real Alpha Vantage API key.

Never add .env to Git.

Never change .gitignore in a way that allows .env, logs, or data/raw to be committed.

Never implement automatic trading without explicit human approval.

Never connect this project to a brokerage live trading API without explicit human approval.

Never change portfolio allocation, planned capital, or buy amount rules without explaining the impact first.

All trading-related outputs must remain recommendations only.

Every buy, sell, rebalance, or allocation action must require manual confirmation.

## Investment Safety Rules

This system does not provide financial advice.

Any output such as buy, wait, add, reduce, or rebalance is a rule-based monitoring signal only.

The system must always include:

- auto_trade = false
- manual confirmation required
- no automatic order placement

If data cross-validation status is not passed, the system must block buy recommendations and return WAIT or manual review.

If VTI or SPY is below the 200-day moving average, empty-position entry should be conservative or blocked according to rules.

If VIX is elevated, entry size should be reduced or require manual review.

## Core Portfolio

Long-term target allocation:

- VTI: 64%
- VEA: 20%
- VWO: 10%
- SGOV: 6%

Planned capital:

- Total planned capital: USD 50,000
- Initial entry amount: USD 20,000
- Monthly DCA amount: USD 5,000
- Monthly DCA period: 6 months

Current account status is stored in:

- config/account_status_usd.csv

Entry decision rules are stored in:

- config/entry_decision_rules.csv

Core ETF allocation is stored in:

- config/etf_universe_usd.csv

Market report universe is stored in:

- config/market_report_universe.csv

Daily report rules are stored in:

- config/daily_report_rules.csv

## Main Scripts

Daily market data and signal generation:

- notebooks/09_daily_market_report_v1.py

Alpha Vantage cross-validation:

- notebooks/11_alpha_vantage_cross_validation.py

Entry decision:

- notebooks/14_entry_decision_v1.py

Markdown report V2:

- notebooks/12_daily_market_report_v2_with_validation.py

HTML report:

- notebooks/13_daily_market_report_html.py

Dashboard report:

- notebooks/15_dashboard_report_v1.py

One-click daily workflow:

- scripts/run_daily_report.sh

Automation management:

- scripts/manage_daily_report.sh

## How To Run

Use this command to run the full daily workflow:

bash scripts/run_daily_report.sh

Use this command to open the Dashboard:

bash scripts/manage_daily_report.sh dashboard

Use this command to check automation status:

bash scripts/manage_daily_report.sh status

Use this command to view today's run log:

bash scripts/manage_daily_report.sh today

## Python Environment

The local conda environment is:

etf_strategy

The expected Python path is:

/opt/anaconda3/envs/etf_strategy/bin/python

The one-click script should use this Python path explicitly.

## Data Validation Logic

Main market data source:

- yfinance

Cross-validation source:

- Alpha Vantage TIME_SERIES_DAILY

Important rule:

During intraday runs, Alpha Vantage and yfinance may update at different times.

The cross-validation script should use the previous common trading day when the latest common date is today, to avoid intraday mismatch false alarms.

If cross-validation is not passed:

- entry recommendation must be WAIT
- buy amount must be 0
- dashboard must show data validation warning
- automatic trading must remain disabled

## Dashboard Requirements

The dashboard should show:

- today's recommendation
- suggested amount
- market status
- data validation status
- VTI current price
- VTI 200-day moving average
- VTI drawdown
- VTI -10%, -15%, -25% reference levels
- VIX value
- suggested buy breakdown by ETF
- triggered signals
- cross-validation details

Dashboard output files:

- reports/dashboard_latest.html
- reports/dashboard_YYYY-MM-DD.html

## Git Rules

Before every commit, run:

git status --short

git ls-files .env

grep -R "ALPHA_VANTAGE_API_KEY=" . --exclude=".env" --exclude-dir=".git" --exclude-dir="logs" --exclude-dir="data/raw"

find . -type f -size +50M -not -path "./.git/*" -not -path "./data/raw/*" -not -path "./logs/*"

Expected safety results:

- git ls-files .env should return nothing
- grep should only show placeholders or environment variable names, not the real key
- large file check should return nothing

## Recommended Development Style

Make small, reviewable changes.

Explain what each change does.

Do not combine unrelated changes.

Prefer simple Python scripts over complex frameworks unless requested.

Keep all strategy rules transparent and easy to audit.

Do not add hidden logic.

Do not change financial rules silently.

## Future Upgrade Ideas

Possible future upgrades:

- Streamlit dashboard
- email daily report
- real position tracking
- rebalance calculator
- TradingView webhook signal ingestion
- QuantConnect or IBKR paper trading integration
- improved charting
- scenario analysis
- risk budget dashboard

Any upgrade involving real trading or brokerage integration must remain paper trading or alert-only unless explicitly approved.
