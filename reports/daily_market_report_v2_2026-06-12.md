# 每日市场早报 V2 - 2026-06-12

## 1. 综合结论

- 市场状态：**正常**
- 数据交叉验证：**passed**
- 验证摘要：12/12 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。
- 交易权限：**自动交易关闭；允许生成交易提醒**
- 操作摘要：长期账户按固定计划执行；短线账户只做观察，不自动交易。

## 2. 长期核心账户观察

| Ticker   |   latest_price |   return_1d |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| VTI      |        365.08  | 0.00214084  | -0.00631491 |  0.111588   |   0.0805969 |    0.258287  | True          |      -0.0247892 |
| VEA      |         71.33  | 0.000280525 |  0.0109128  |  0.0960482  |   0.157011  |    0.310111  | True          |      -0.0136891 |
| VWO      |         59.28  | 0.00304569  | -0.0113409  |  0.0774264  |   0.110312  |    0.259503  | True          |      -0.0312142 |
| SGOV     |        100.517 | 0.000266714 |  0.00294704 |  0.00886133 |   0.0182836 |    0.0391261 | True          |       0         |

## 3. 今日触发信号

| rule_id            | category   | action_level   | meaning              | detail                                     | auto_trade   |
|:-------------------|:-----------|:---------------|:---------------------|:-------------------------------------------|:-------------|
| VTI_ABOVE_200MA    | trend      | normal         | 长期趋势健康         | VTI 最新价 365.08，200日均线 337.29        | False        |
| QQQ_STRONG         | rotation   | info           | 科技成长强于大盘     | QQQ 3个月收益 19.35%，SPY 3个月收益 10.68% | False        |
| TLT_STRONG_DEFENSE | defense    | info           | 债券防守资产相对走强 | TLT 1个月收益 1.32%，SPY 1个月收益 -1.30%  | False        |

## 4. 数据交叉验证明细

| ticker   | status   | common_date   |   yf_close |   av_close |    pct_diff | pass_price_check   | notes                                              |
|:---------|:---------|:--------------|-----------:|-----------:|------------:|:-------------------|:---------------------------------------------------|
| SPY      | ok       | 2026-06-10    |     725.43 |     725.43 | 1.00964e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| QQQ      | ok       | 2026-06-10    |     693.69 |     693.69 | 3.51945e-09 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VTI      | ok       | 2026-06-10    |     358.04 |     358.04 | 2.38658e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VEA      | ok       | 2026-06-10    |      68.81 |      68.81 | 3.54804e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VWO      | ok       | 2026-06-10    |      57.72 |      57.72 | 2.11487e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| TLT      | ok       | 2026-06-10    |      84.88 |      84.88 | 3.23584e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| GLD      | ok       | 2026-06-10    |     374.58 |     374.58 | 3.58474e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| IWM      | ok       | 2026-06-10    |     282.05 |     282.05 | 4.32797e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLK      | ok       | 2026-06-10    |     176.63 |     176.63 | 2.76443e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLF      | ok       | 2026-06-10    |      52.23 |      52.23 | 8.76438e-09 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLV      | ok       | 2026-06-10    |     152.85 |     152.85 | 3.99314e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLE      | ok       | 2026-06-10    |      58.25 |      58.25 | 0           | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |

## 5. 数据验证异常标的

所有交叉验证标的均通过。

## 6. 3个月表现靠前标的

| Ticker   |   latest_price |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| XLK      |        183.25  |  0.0208914  |    0.322077 |   0.241847  |     0.54114  | True          |      -0.0754755 |
| QQQ      |        715.623 | -0.00578943 |    0.193453 |   0.146853  |     0.364594 | True          |      -0.0409258 |
| IWM      |        292.57  |  0.0285463  |    0.177448 |   0.140703  |     0.415687 | True          |       0         |
| VTI      |        365.08  | -0.00631491 |    0.111588 |   0.0805969 |     0.258287 | True          |      -0.0247892 |
| SPY      |        738.47  | -0.012965   |    0.106806 |   0.0776366 |     0.251148 | True          |      -0.0277789 |

## 7. 3个月表现靠后标的

| Ticker   |   latest_price |   return_1m |    return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|-------------:|------------:|-------------:|:--------------|----------------:|
| ^VIX     |        19.2    |  0.112399   | -0.183326    |  0.292929   |   -0.0778097 | True          |     -0.381642   |
| GLD      |       386.54   | -0.095199   | -0.16048     | -0.0170379  |    0.222106  | False         |     -0.220528   |
| CL=F     |        84.46   | -0.165168   | -0.0966845   |  0.466319   |    0.157303  | True          |     -0.252235   |
| TLT      |        85.7018 |  0.0131759  | -0.00582903  | -0.00598105 |    0.0380006 | False         |     -0.0421718  |
| DX-Y.NYB |        99.73   |  0.00859634 |  0.000200625 |  0.0140316  |    0.0157874 | True          |     -0.00776041 |

## 8. Alpha Vantage 下载日志

| ticker   | success   | source_type   | latest_date   |   rows | cache_path                                                                       | notes    |
|:---------|:----------|:--------------|:--------------|-------:|:---------------------------------------------------------------------------------|:---------|
| SPY      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_SPY_2026-06-12.csv | 下载成功 |
| QQQ      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_QQQ_2026-06-12.csv | 下载成功 |
| VTI      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VTI_2026-06-12.csv | 下载成功 |
| VEA      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VEA_2026-06-12.csv | 下载成功 |
| VWO      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VWO_2026-06-12.csv | 下载成功 |
| TLT      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_TLT_2026-06-12.csv | 下载成功 |
| GLD      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_GLD_2026-06-12.csv | 下载成功 |
| IWM      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_IWM_2026-06-12.csv | 下载成功 |
| XLK      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLK_2026-06-12.csv | 下载成功 |
| XLF      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLF_2026-06-12.csv | 下载成功 |
| XLV      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLV_2026-06-12.csv | 下载成功 |
| XLE      | True      | cache         | 2026-06-11    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLE_2026-06-12.csv | 下载成功 |

## 9. 数据说明

- 市场表现数据来自 yfinance。
- 价格交叉验证来自 Alpha Vantage TIME_SERIES_DAILY。
- 如果数据交叉验证不是 passed，本系统不允许自动交易。
- 当前版本只生成提醒，不自动下单。
