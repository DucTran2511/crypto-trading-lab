# 14. Strategy Comparison Report

This report aggregates the same-window baseline backtests and the first walk-forward
validation sweep. Generated Freqtrade outputs remain in gitignored
`user_data/backtest_results/` and `user_data/walk_forward_results/`; this document
commits the comparison and decision rationale.

## 14.1 Final Ranking

| Rank | Strategy | Status | Baseline Trades | Baseline Profit % | Baseline Sharpe | Baseline Max DD % | OOS Folds | Avg OOS Profit % | Avg OOS Sharpe | OOS Positive Fold % | Rationale |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `BollingerMeanReversion` | Reject | 9 | 0.09 | 0.50 | 0.03 | 1 | -0.02 | -0.47 | 0.00 | Hyperopt improved the in-sample fold, but the out-of-sample fold did not preserve the edge. |
| 2 | `RSITrend` | Reject | 76 | -1.73 | -3.59 | 1.89 | 1 | -0.08 | -100.00 | 0.00 | Hyperopt improved the in-sample fold, but the out-of-sample fold did not preserve the edge. |
| 3 | `EMACrossover` | Control only | 802 | -20.82 | -38.72 | 20.84 | 0 | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |
| 4 | `DonchianBreakout` | Control only | 968 | -28.32 | -34.76 | 28.74 | 0 | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |
| 5 | `MACDVolume` | Control only | 1584 | -49.27 | -110.59 | 49.27 | 0 | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |

## 14.2 Decision

`BollingerMeanReversion` ranks first because it had the least-bad validated holdout result, but it is still rejected as a tradable strategy. No baseline is ready for paper trading.

Use `BollingerMeanReversion` as the next research control because it had the smallest
baseline drawdown and the best out-of-sample result among the strategies that reached
walk-forward validation. The next iteration should focus on regime filters, entry
quality, and trade-frequency improvements instead of simply increasing hyperopt epochs.

## 14.3 Next Work

- Keep `EMACrossover`, `DonchianBreakout`, and `MACDVolume` as losing controls.
- Treat `RSITrend` as a secondary control: it had enough trades, but failed the holdout badly.
- Run regime-filter experiments against `BollingerMeanReversion` first, always comparing
  against the unfiltered baseline result.

[Back to docs index](README.md)
