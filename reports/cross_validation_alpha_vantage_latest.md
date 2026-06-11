# yfinance vs Alpha Vantage 交叉验证报告 - 2026-06-10

## 1. 验证状态

- 状态：**passed**
- 摘要：12/12 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。
- 主数据源：yfinance Close
- 辅助数据源：Alpha Vantage TIME_SERIES_DAILY close
- 差异阈值：1%
- 自动交易：关闭

## 2. Alpha Vantage 下载日志

| ticker   | success   | source_type   | latest_date         |   rows | cache_path                                                                       | notes    |
|:---------|:----------|:--------------|:--------------------|-------:|:---------------------------------------------------------------------------------|:---------|
| SPY      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_SPY_2026-06-10.csv | 下载成功 |
| QQQ      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_QQQ_2026-06-10.csv | 下载成功 |
| VTI      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VTI_2026-06-10.csv | 下载成功 |
| VEA      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VEA_2026-06-10.csv | 下载成功 |
| VWO      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VWO_2026-06-10.csv | 下载成功 |
| TLT      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_TLT_2026-06-10.csv | 下载成功 |
| GLD      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_GLD_2026-06-10.csv | 下载成功 |
| IWM      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_IWM_2026-06-10.csv | 下载成功 |
| XLK      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLK_2026-06-10.csv | 下载成功 |
| XLF      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLF_2026-06-10.csv | 下载成功 |
| XLV      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLV_2026-06-10.csv | 下载成功 |
| XLE      | True      | cache         | 2026-06-10 00:00:00 |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLE_2026-06-10.csv | 下载成功 |

## 3. 交叉验证明细

| ticker   | status   | common_date         | yf_latest_date      | av_latest_date      |   yf_close |   av_close |    abs_diff |    pct_diff | pass_price_check   | notes   |
|:---------|:---------|:--------------------|:--------------------|:--------------------|-----------:|-----------:|------------:|------------:|:-------------------|:--------|
| SPY      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     725.43 |     725.43 | 7.32422e-06 | 1.00964e-08 | True               | 通过    |
| QQQ      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     693.69 |     693.69 | 2.44141e-06 | 3.51945e-09 | True               | 通过    |
| VTI      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     358.04 |     358.04 | 8.54492e-06 | 2.38658e-08 | True               | 通过    |
| VEA      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      68.81 |      68.81 | 2.44141e-06 | 3.54804e-08 | True               | 通过    |
| VWO      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      57.72 |      57.72 | 1.2207e-06  | 2.11487e-08 | True               | 通过    |
| TLT      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      84.88 |      84.88 | 2.74658e-06 | 3.23584e-08 | True               | 通过    |
| GLD      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     374.58 |     374.58 | 1.34277e-05 | 3.58474e-08 | True               | 通过    |
| IWM      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     282.05 |     282.05 | 1.2207e-05  | 4.32797e-08 | True               | 通过    |
| XLK      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     176.63 |     176.63 | 4.88281e-06 | 2.76443e-08 | True               | 通过    |
| XLF      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      52.23 |      52.23 | 4.57764e-07 | 8.76438e-09 | True               | 通过    |
| XLV      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     152.85 |     152.85 | 6.10352e-06 | 3.99314e-08 | True               | 通过    |
| XLE      | ok       | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      58.25 |      58.25 | 0           | 0           | True               | 通过    |

## 4. 使用说明

- 如果状态为 passed，说明两个数据源最新共同交易日价格基本一致。
- 如果状态为 need_check，说明部分价格差异超过阈值，应人工检查。
- 如果状态为 degraded，说明辅助数据源不可用，不应自动交易。
