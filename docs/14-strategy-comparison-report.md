# 14. Strategy Comparison Report

This report aggregates the same-window baseline backtests and the first walk-forward
validation sweep. Generated Freqtrade outputs remain in gitignored
`user_data/backtest_results/` and `user_data/walk_forward_results/`; this document
commits the comparison and decision rationale.

## 14.1 Final Ranking

| Rank | Strategy | Status | Baseline Trades | Baseline Profit % | Baseline Sharpe | Baseline Max DD % | OOS Folds | Avg OOS Profit % | Avg OOS Sharpe | Worst OOS DD % | OOS Positive Fold % | Avg IS-OOS Gap % | Rationale |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `RSITrendBullOnly` | Research candidate | N/A | N/A | N/A | N/A | 1 | 0.02 | 0.25 | N/A | 100.00 | 0.01 | Out-of-sample folds stayed positive after hyperopt; continue with stricter validation. |
| 2 | `BollingerMeanReversion` | Reject | 9 | 0.09 | 0.50 | 0.03 | 1 | -0.02 | -0.47 | N/A | 0.00 | 0.16 | Hyperopt improved the in-sample fold, but the out-of-sample fold did not preserve the edge. |
| 3 | `RSITrendTrendingOnly` | Reject | N/A | N/A | N/A | N/A | 1 | -0.07 | -0.81 | N/A | 0.00 | 0.04 | Regime variant has no same-window baseline row; ranking is based on walk-forward only. |
| 4 | `RSITrend` | Reject | 76 | -1.73 | -3.59 | 1.89 | 1 | -0.08 | -100.00 | N/A | 0.00 | 0.25 | Hyperopt improved the in-sample fold, but the out-of-sample fold did not preserve the edge. |
| 5 | `RSITrendBearExcluded` | Reject | N/A | N/A | N/A | N/A | 1 | N/A | N/A | N/A | N/A | N/A | Regime variant has no same-window baseline row; ranking is based on walk-forward only. |
| 6 | `EMACrossover` | Control only | 802 | -20.82 | -38.72 | 20.84 | 0 | N/A | N/A | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |
| 7 | `DonchianBreakout` | Control only | 968 | -28.32 | -34.76 | 28.74 | 0 | N/A | N/A | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |
| 8 | `MACDVolume` | Control only | 1584 | -49.27 | -110.59 | 49.27 | 0 | N/A | N/A | N/A | N/A | N/A | Rejected before walk-forward validation; keep as a baseline/control, not a candidate. |

## 14.2 Decision

`RSITrendBullOnly` ranks first as a research candidate because its walk-forward holdout metrics stayed positive. It is not ready for paper trading until it passes a broader multi-window or second-pass validation.

Use the highest-ranked research candidate as the next experiment target, while keeping
`BollingerMeanReversion` and `RSITrend` as controls for comparison against the original
baseline and unfiltered strategy behavior.

## 14.3 Next Work

- Run multi-window walk-forward validation for `RSITrendBullOnly` before treating it as
  more than a weak research candidate.
- Keep `BollingerMeanReversion` and unfiltered `RSITrend` as controls.
- Reject the regime variant if the broader validation loses positive OOS Sharpe,
  positive OOS profit, or acceptable drawdown control.

[Back to docs index](README.md)
