# ETF 数据交叉验证报告 - 2026-06-10

## 1. 验证状态

- 状态：**degraded**
- 摘要：yfinance 主数据源可用，但 Stooq 辅助数据源全部不可用，无法完成独立交叉验证。
- 主数据源：yfinance
- 辅助数据源：Stooq
- 价格差异阈值：1%

## 2. Stooq 下载状态

| ticker   | stooq_available   | used_symbol   | latest_date   | notes                      |
|:---------|:------------------|:--------------|:--------------|:---------------------------|
| SPY      | False             |               |               | Stooq 下载失败或无可用 CSV |
| QQQ      | False             |               |               | Stooq 下载失败或无可用 CSV |
| VTI      | False             |               |               | Stooq 下载失败或无可用 CSV |
| VEA      | False             |               |               | Stooq 下载失败或无可用 CSV |
| VWO      | False             |               |               | Stooq 下载失败或无可用 CSV |
| TLT      | False             |               |               | Stooq 下载失败或无可用 CSV |
| GLD      | False             |               |               | Stooq 下载失败或无可用 CSV |
| IWM      | False             |               |               | Stooq 下载失败或无可用 CSV |
| XLK      | False             |               |               | Stooq 下载失败或无可用 CSV |
| XLF      | False             |               |               | Stooq 下载失败或无可用 CSV |
| XLV      | False             |               |               | Stooq 下载失败或无可用 CSV |
| XLE      | False             |               |               | Stooq 下载失败或无可用 CSV |

## 3. 验证明细

| ticker   | status        | common_date   | yf_latest_date      | stooq_latest_date   |   yf_price |   stooq_price |   abs_diff |   pct_diff | pass_price_check   | notes                                              |
|:---------|:--------------|:--------------|:--------------------|:--------------------|-----------:|--------------:|-----------:|-----------:|:-------------------|:---------------------------------------------------|
| SPY      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     725.43 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| QQQ      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     693.69 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| VTI      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     358.04 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| VEA      | missing_stooq |               | 2026-06-10 00:00:00 |                     |      68.81 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| VWO      | missing_stooq |               | 2026-06-10 00:00:00 |                     |      57.72 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| TLT      | missing_stooq |               | 2026-06-10 00:00:00 |                     |      84.88 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| GLD      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     374.58 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| IWM      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     282.05 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| XLK      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     176.63 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| XLF      | missing_stooq |               | 2026-06-10 00:00:00 |                     |      52.23 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| XLV      | missing_stooq |               | 2026-06-10 00:00:00 |                     |     152.85 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |
| XLE      | missing_stooq |               | 2026-06-10 00:00:00 |                     |      58.25 |           nan |        nan |        nan | False              | Stooq 不可用，无法交叉验证；主数据源 yfinance 可用 |

## 4. 使用说明

- 如果状态为 passed，说明当天价格数据可信度较高。
- 如果状态为 degraded，说明主数据源可用，但辅助数据源不可用，不能视为独立交叉验证通过。
- 如果状态为 need_check，说明部分标的价格差异超过阈值，需要人工检查。
- 无论哪种状态，本系统都不会自动交易。
