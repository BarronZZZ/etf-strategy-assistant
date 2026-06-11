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

| ticker   | status   | common_date         | yf_latest_date      | av_latest_date      |   yf_close |   av_close |    abs_diff |    pct_diff | pass_price_check   | notes                                        |
|:---------|:---------|:--------------------|:--------------------|:--------------------|-----------:|-----------:|------------:|------------:|:-------------------|:---------------------------------------------|
| SPY      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     737.05 |     737.05 | 1.2207e-05  | 1.6562e-08  | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| QQQ      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     707.83 |     707.83 | 1.70898e-05 | 2.4144e-08  | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| VTI      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     363.67 |     363.67 | 1.34277e-05 | 3.69229e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| VEA      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      69.84 |      69.84 | 3.66211e-06 | 5.24357e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| VWO      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      58.45 |      58.45 | 7.62939e-07 | 1.30529e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| TLT      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      85.12 |      85.12 | 2.74658e-06 | 3.22672e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| GLD      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     390.78 |     390.78 | 1.2207e-06  | 3.12376e-09 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| IWM      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     285.02 |     285.02 | 1.09863e-05 | 3.85458e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| XLK      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     180.77 |     180.77 | 4.27246e-06 | 2.36348e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| XLF      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      52.46 |      52.46 | 9.15527e-07 | 1.74519e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| XLV      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |     154.57 |     154.57 | 7.32422e-06 | 4.73845e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |
| XLE      | ok       | 2026-06-09 00:00:00 | 2026-06-10 00:00:00 | 2026-06-10 00:00:00 |      57.39 |      57.39 | 6.10352e-07 | 1.06352e-08 | True               | 通过；使用前一个共同交易日，避免盘中数据误判 |

## 4. 使用说明

- 如果状态为 passed，说明两个数据源最新共同交易日价格基本一致。
- 如果状态为 need_check，说明部分价格差异超过阈值，应人工检查。
- 如果状态为 degraded，说明辅助数据源不可用，不应自动交易。
