# 每日市场早报 V2 - 2026-06-11

## 1. 综合结论

- 市场状态：**正常**
- 数据交叉验证：**passed**
- 验证摘要：12/12 个标的通过 yfinance 与 Alpha Vantage 价格交叉验证。
- 交易权限：**自动交易关闭；允许生成交易提醒**
- 操作摘要：长期账户按固定计划执行；短线账户只做观察，不自动交易。

## 2. 长期核心账户观察

| Ticker   |   latest_price |   return_1d |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| VTI      |         363.67 |           0 | -0.00285152 |  0.118601   |   0.0800466 |    0.238619  | True          |      -0.0285553 |
| VEA      |          69.84 |           0 | -0.0111851  |  0.09619    |   0.137551  |    0.267178  | True          |      -0.0342921 |
| VWO      |          58.45 |           0 | -0.0248582  |  0.0820067  |   0.0923579 |    0.223159  | True          |      -0.0447785 |
| SGOV     |         100.47 |           0 |  0.00257976 |  0.00839162 |   0.0180123 |    0.0390558 | True          |       0         |

## 3. 今日触发信号

| rule_id            | category   | action_level   | meaning              | detail                                     | auto_trade   |
|:-------------------|:-----------|:---------------|:---------------------|:-------------------------------------------|:-------------|
| VTI_ABOVE_200MA    | trend      | normal         | 长期趋势健康         | VTI 最新价 363.67，200日均线 337.07        | False        |
| QQQ_STRONG         | rotation   | info           | 科技成长强于大盘     | QQQ 3个月收益 19.37%，SPY 3个月收益 11.59% | False        |
| TLT_STRONG_DEFENSE | defense    | info           | 债券防守资产相对走强 | TLT 1个月收益 0.77%，SPY 1个月收益 -0.71%  | False        |

## 4. 数据交叉验证明细

| ticker   | status   | common_date   |   yf_close |   av_close |    pct_diff | pass_price_check   | notes                                              |
|:---------|:---------|:--------------|-----------:|-----------:|------------:|:-------------------|:---------------------------------------------------|
| SPY      | ok       | 2026-06-09    |     737.05 |     737.05 | 1.6562e-08  | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| QQQ      | ok       | 2026-06-09    |     707.83 |     707.83 | 2.4144e-08  | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VTI      | ok       | 2026-06-09    |     363.67 |     363.67 | 3.69229e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VEA      | ok       | 2026-06-09    |      69.84 |      69.84 | 5.24357e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| VWO      | ok       | 2026-06-09    |      58.45 |      58.45 | 1.30529e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| TLT      | ok       | 2026-06-09    |      85.12 |      85.12 | 3.22672e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| GLD      | ok       | 2026-06-09    |     390.78 |     390.78 | 3.12376e-09 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| IWM      | ok       | 2026-06-09    |     285.02 |     285.02 | 3.85458e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLK      | ok       | 2026-06-09    |     180.77 |     180.77 | 2.36348e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLF      | ok       | 2026-06-09    |      52.46 |      52.46 | 1.74519e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLV      | ok       | 2026-06-09    |     154.57 |     154.57 | 4.73845e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |
| XLE      | ok       | 2026-06-09    |      57.39 |      57.39 | 1.06352e-08 | True               | 通过；使用前一个共同交易日，避免最新交易日数据误判 |

## 5. 数据验证异常标的

所有交叉验证标的均通过。

## 6. 3个月表现靠前标的

| Ticker   |   latest_price |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| XLK      |         180.77 |  0.0221657  |    0.323061 |   0.218781  |     0.498974 | True          |      -0.0879875 |
| QQQ      |         707.83 | -0.00962629 |    0.193698 |   0.130695  |     0.332789 | True          |      -0.0513696 |
| IWM      |         285.02 |  0.00831349 |    0.157902 |   0.124306  |     0.353941 | True          |      -0.0240044 |
| VTI      |         363.67 | -0.00285152 |    0.118601 |   0.0800466 |     0.238619 | True          |      -0.0285553 |
| SPY      |         737.05 | -0.007086   |    0.11592  |   0.0780673 |     0.234781 | True          |      -0.0296484 |

## 7. 3个月表现靠后标的

| Ticker   |   latest_price |   return_1m |   return_3m |   return_6m |   return_12m | above_200ma   |   drawdown_252d |
|:---------|---------------:|------------:|------------:|------------:|-------------:|:--------------|----------------:|
| ^VIX     |          20.72 |  0.159485   | -0.237955   |  0.313887   |    0.149833  | True          |     -0.332689   |
| GLD      |         390.78 | -0.0922648  | -0.152027   |  0.00444676 |    0.251698  | False         |     -0.211978   |
| CL=F     |          89.44 | -0.114631   | -0.0939114  |  0.529935   |    0.314521  | True          |     -0.208145   |
| TLT      |          85.12 |  0.00772173 | -0.00493348 | -0.0140706  |    0.0210195 | False         |     -0.0486741  |
| DX-Y.NYB |         100    |  0.0154346  | -0.00358709 |  0.0122482  |    0.0212418 | True          |     -0.00507414 |

## 8. Alpha Vantage 下载日志

| ticker   | success   | source_type   | latest_date   |   rows | cache_path                                                                       | notes    |
|:---------|:----------|:--------------|:--------------|-------:|:---------------------------------------------------------------------------------|:---------|
| SPY      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_SPY_2026-06-11.csv | 下载成功 |
| QQQ      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_QQQ_2026-06-11.csv | 下载成功 |
| VTI      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VTI_2026-06-11.csv | 下载成功 |
| VEA      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VEA_2026-06-11.csv | 下载成功 |
| VWO      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_VWO_2026-06-11.csv | 下载成功 |
| TLT      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_TLT_2026-06-11.csv | 下载成功 |
| GLD      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_GLD_2026-06-11.csv | 下载成功 |
| IWM      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_IWM_2026-06-11.csv | 下载成功 |
| XLK      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLK_2026-06-11.csv | 下载成功 |
| XLF      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLF_2026-06-11.csv | 下载成功 |
| XLV      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLV_2026-06-11.csv | 下载成功 |
| XLE      | True      | cache         | 2026-06-10    |    100 | /Users/bz/etf-strategy-assistant/data/raw/alpha_vantage_daily_XLE_2026-06-11.csv | 下载成功 |

## 9. 数据说明

- 市场表现数据来自 yfinance。
- 价格交叉验证来自 Alpha Vantage TIME_SERIES_DAILY。
- 如果数据交叉验证不是 passed，本系统不允许自动交易。
- 当前版本只生成提醒，不自动下单。
