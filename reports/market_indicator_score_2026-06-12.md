# Market Indicator Score V1

Date: 2026-06-12

本报告为 V1.2 多指标评分的第一版测试输出。

当前只生成指标和评分，不改变任何买入建议。

评分维度包括：趋势、动量、波动风险、回撤位置、布林带位置。

| ticker | role | latest_price | ma50 | ma200 | above_200ma | rsi14 | return_3m | return_6m | vol20_annualized | drawdown_252d | market_score | score_status | reference_signal | suggested_buy_amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VTI | 美国全市场核心 | 365.08 | 356.98 | 337.29 | True | 52.16 | 11.16% | 8.06% | 14.85% | -2.48% | 78.00 | normal | normal_or_positive | 12800.00 |
| VEA | 发达市场 | 71.33 | 69.47 | 64.09 | True | 55.30 | 9.60% | 15.70% | 22.88% | -1.37% | 81.00 | strong | normal_or_positive | 4000.00 |
| VWO | 新兴市场 | 59.28 | 58.74 | 55.38 | True | 51.29 | 7.74% | 11.03% | 21.36% | -3.12% | 76.00 | normal | normal_or_positive | 2000.00 |
| SGOV | 美元现金短债 | 100.52 | 100.18 | 99.09 | True | 100.00 | 0.89% | 1.83% | 0.20% | 0.00% | 71.00 | normal | normal_or_positive | 1200.00 |

说明：

- market_score 是 0 到 100 的辅助评分。
- score_status 包括 strong / normal / neutral / weak / high_risk。
- reference_signal 只是辅助观察信号，暂未接入正式入场规则。
- SGOV 是现金/短债工具，不应按风险资产回撤买点解释。
- 所有输出均为规则化监控信息，不构成投资建议，不自动交易。
