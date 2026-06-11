# ETF Strategy Assistant

A local Python-based ETF strategy assistant for long-term USD ETF allocation, daily market monitoring, risk alerts, and data cross-validation.

## Project Purpose

This project helps manage a long-term USD ETF allocation plan and generate a daily market report.

The system currently supports:

- Long-term core ETF allocation planning
- Fixed DCA execution schedule
- Market performance monitoring
- VTI / SPY trend and drawdown alerts
- Tactical ETF watchlist
- yfinance market data download
- Alpha Vantage price cross-validation
- Markdown daily report
- HTML daily report
- macOS launchd daily automation

## Long-Term Core Portfolio

Current long-term USD allocation:

| ETF | Role | Target Weight |
|---|---|---:|
| VTI | US total market core equity | 64% |
| VEA | Developed markets ex-US | 20% |
| VWO | Emerging markets | 10% |
| SGOV | USD Treasury bill / cash buffer | 6% |

Execution plan:

- Total planned capital: USD 50,000
- Initial purchase: 40%
- Remaining capital: 6 monthly DCA tranches
- Smart DCA alerts: manual confirmation only
- No automatic trading

## Daily Market Report

The daily report includes:

- Core ETF performance
- Tactical ETF watchlist performance
- Moving average status
- 252-day drawdown
- VTI risk alerts
- SPY trend alerts
- QQQ vs SPY relative strength
- TLT / GLD defensive signals
- VIX risk state
- yfinance vs Alpha Vantage price cross-validation

Generated reports:

- reports/daily_market_report_v2_latest.md
- reports/daily_market_report_v2_latest.html

## Data Sources

Main data source:

- yfinance

Cross-validation source:

- Alpha Vantage TIME_SERIES_DAILY

Sensitive information is stored locally in .env and is not committed to GitHub.

Create your own .env file based on .env.example.

Example:

ALPHA_VANTAGE_API_KEY=your_api_key_here

## Run Daily Report Manually

Run the full daily report:

bash scripts/run_daily_report.sh

Open the latest HTML report:

bash scripts/manage_daily_report.sh open

Check automation status:

bash scripts/manage_daily_report.sh status

View today's run log:

bash scripts/manage_daily_report.sh today

## macOS Daily Automation

The project uses macOS launchd to run the daily report automatically.

LaunchAgent label:

com.bz.etfstrategy.dailyreport

Default schedule:

Every day at 9:00 local time

Common management commands:

bash scripts/manage_daily_report.sh status
bash scripts/manage_daily_report.sh run
bash scripts/manage_daily_report.sh log
bash scripts/manage_daily_report.sh err
bash scripts/manage_daily_report.sh stop

## Safety Notes

This project does not place trades automatically.

The reports are for monitoring, research, and decision support only.

If data cross-validation fails, the report will mark the data status as not passed and automatic execution remains disabled.

## Project Structure

config/      ETF universe and report rule configurations
data/        Processed market data and generated CSV outputs
notebooks/   Python scripts for data download, backtest, reports, and validation
reports/     Markdown and HTML reports
scripts/     One-click run scripts and automation management scripts

## Disclaimer

This project is for personal research and portfolio monitoring only. It is not financial advice.
