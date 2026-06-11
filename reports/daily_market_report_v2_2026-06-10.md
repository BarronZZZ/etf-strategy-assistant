# 每日市场早报 V2 - 2026-06-10

## 1. 综合结论

- 市场状态：**正常**
- 数据交叉验证：**passed**
- 验证摘要：12/12 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。
- 交易权限：**自动交易关闭；允许生成交易提醒**
- 操作摘要：长期账户按固定计划执行；短线账户只做观察，不自动交易。

## 2. 长期核心账户观察

| Ticker   |   latest_price |    return_1d |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|-------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| VTI      |         358.04 | -0.0154811   | -0.013093   |  0.0952723  |   0.0712325 |    0.223355  | True          |      -0.0435943 |
| VEA      |          68.81 | -0.014748    | -0.0165786  |  0.0674786  |   0.133461  |    0.258226  | True          |      -0.0485343 |
| VWO      |          57.72 | -0.0124893   | -0.0281192  |  0.0627877  |   0.0876861 |    0.208129  | True          |      -0.0567086 |
| SGOV     |         100.48 |  9.95535e-05 |  0.00277936 |  0.00879304 |   0.0181135 |    0.0392627 | True          |       0         |

## 3. 今日触发信号

| rule_id            | category   | action_level   | meaning              | detail                                    | auto_trade   |
|:-------------------|:-----------|:---------------|:---------------------|:------------------------------------------|:-------------|
| VTI_ABOVE_200MA    | trend      | normal         | 长期趋势健康         | VTI 最新价 358.04，200日均线 336.80       | False        |
| QQQ_STRONG         | rotation   | info           | 科技成长强于大盘     | QQQ 3个月收益 16.29%，SPY 3个月收益 9.21% | False        |
| TLT_STRONG_DEFENSE | defense    | info           | 债券防守资产相对走强 | TLT 1个月收益 0.26%，SPY 1个月收益 -1.73% | False        |

## 4. 数据交叉验证明细

| ticker   | status   | common_date   |   yf_close |   av_close |    pct_diff | pass_price_check   | notes   |
|:---------|:---------|:--------------|-----------:|-----------:|------------:|:-------------------|:--------|
| SPY      | ok       | 2026-06-10    |     725.43 |     725.43 | 1.00964e-08 | True               | 通过    |
| QQQ      | ok       | 2026-06-10    |     693.69 |     693.69 | 3.51945e-09 | True               | 通过    |
| VTI      | ok       | 2026-06-10    |     358.04 |     358.04 | 2.38658e-08 | True               | 通过    |
| VEA      | ok       | 2026-06-10    |      68.81 |      68.81 | 3.54804e-08 | True               | 通过    |
| VWO      | ok       | 2026-06-10    |      57.72 |      57.72 | 2.11487e-08 | True               | 通过    |
| TLT      | ok       | 2026-06-10    |      84.88 |      84.88 | 3.23584e-08 | True               | 通过    |
| GLD      | ok       | 2026-06-10    |     374.58 |     374.58 | 3.58474e-08 | True               | 通过    |
| IWM      | ok       | 2026-06-10    |     282.05 |     282.05 | 4.32797e-08 | True               | 通过    |
| XLK      | ok       | 2026-06-10    |     176.63 |     176.63 | 2.76443e-08 | True               | 通过    |
| XLF      | ok       | 2026-06-10    |      52.23 |      52.23 | 8.76438e-09 | True               | 通过    |
| XLV      | ok       | 2026-06-10    |     152.85 |     152.85 | 3.99314e-08 | True               | 通过    |
| XLE      | ok       | 2026-06-10    |      58.25 |      58.25 | 0           | True               | 通过    |

## 5. 数据验证异常标的

所有交叉验证标的均通过。

## 6. 3个月表现靠前标的

| Ticker   |   latest_price |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| XLK      |         176.63 |  0.00816215 |   0.283007  |   0.19658   |     0.478234 | True          |      -0.108874  |
| QQQ      |         693.69 | -0.019159   |   0.162918  |   0.112646  |     0.309231 | True          |      -0.07032   |
| IWM      |         282.05 | -0.00184032 |   0.142038  |   0.127727  |     0.334501 | True          |      -0.0341746 |
| VTI      |         358.04 | -0.013093   |   0.0952723 |   0.0712325 |     0.223355 | True          |      -0.0435943 |
| SPY      |         725.43 | -0.0172722  |   0.0921106 |   0.0681081 |     0.220144 | True          |      -0.0449465 |

## 7. 3个月表现靠后标的

| Ticker   |   latest_price |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| GLD      |        374.58  | -0.134779   | -0.197695   |  -0.0330924 |    0.21471   | False         |     -0.244646   |
| ^VIX     |         22.22  |  0.235131   | -0.185782   |   0.312463  |    0.28737   | True          |     -0.28438    |
| CL=F     |         92.01  | -0.0995302  | -0.0388593  |   0.579571  |    0.35011   | True          |     -0.185392   |
| TLT      |         84.88  |  0.00263397 | -0.0126451  |  -0.0130507 |    0.0303149 | False         |     -0.0513565  |
| DX-Y.NYB |         99.962 |  0.0170109  |  0.00222579 |   0.0074783 |    0.013505  | True          |     -0.00545223 |

## 8. Alpha Vantage 下载日志

| ticker   | success   | source_type   | latest_date   |   rows | cache_path                                                                       | notes    |
|:---------|:----------|:--------------|:--------------|-------:|:---------------------------------------------------------------------------------|:---------|
| SPY      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_SPY_2026-06-10.csv | 下载成功 |
| QQQ      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_QQQ_2026-06-10.csv | 下载成功 |
| VTI      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VTI_2026-06-10.csv | 下载成功 |
| VEA      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VEA_2026-06-10.csv | 下载成功 |
| VWO      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VWO_2026-06-10.csv | 下载成功 |
| TLT      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_TLT_2026-06-10.csv | 下载成功 |
| GLD      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_GLD_2026-06-10.csv | 下载成功 |
| IWM      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_IWM_2026-06-10.csv | 下载成功 |
| XLK      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLK_2026-06-10.csv | 下载成功 |
| XLF      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLF_2026-06-10.csv | 下载成功 |
| XLV      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLV_2026-06-10.csv | 下载成功 |
| XLE      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLE_2026-06-10.csv | 下载成功 |

## 9. 数据说明

- 市场表现数据来自 yfinance。
- 价格交叉验证来自 Alpha Vantage TIME_SERIES_DAILY。
- 如果数据交叉验证不是 passed，本系统不允许自动交易。
- 当前版本只生成提醒，不自动下单。
