# 18. 1h Strategy Walk-Forward Results

This report documents the multi-window validation pass for the two 1h strategy
hypotheses introduced in [17. Next Sprint Plan](17-next-sprint-plan.md):
`MultiTimeframeTrend` and `ATRAdaptiveMeanReversion`.

The result is a rejection for both strategies. Both completed seven out-of-sample
folds and kept every fold below the 5% drawdown cap, but neither produced positive
average out-of-sample profit.

## 18.1 Scope

Run date: 2026-05-26.

Same-window screen:

| Strategy | Trades | Total Profit % | Sharpe | Max DD % | Screen Result |
|---|---:|---:|---:|---:|---|
| `MultiTimeframeTrend` | 301 | -6.14 | -8.08 | 6.75 | Pass |
| `ATRAdaptiveMeanReversion` | 797 | -26.85 | -48.24 | 26.92 | Pass |

Both strategies passed the pre-registered screen of at least 20 trades and max
drawdown below 30%. `ATRAdaptiveMeanReversion` did not need the one allowed ATR
relaxation pass from §17.4 because it cleared the trade-count screen.

Commands:

```bash
python scripts/walk_forward.py \
    --strategy MultiTimeframeTrend \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    -c user_data/config-1h.local.json \
    --output-dir user_data/walk_forward_results/MultiTimeframeTrend \
    --freqtrade-bin .venv/bin/freqtrade

python scripts/walk_forward.py \
    --strategy ATRAdaptiveMeanReversion \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    -c user_data/config-1h.local.json \
    --output-dir user_data/walk_forward_results/ATRAdaptiveMeanReversion \
    --freqtrade-bin .venv/bin/freqtrade
```

`user_data/config-1h.local.json` matched the committed config except for the
`timeframe = "1h"` override, so Freqtrade did not force the new strategies back to
the repository's default 5m setting.

Before the run, 4h informative candles were downloaded for the same pair universe,
and 1h/4h data were prepended back to 2024-04-01 to provide startup candle warmup for
the first fold.

Source summaries:

- `user_data/backtest_results/baseline_validation_summary.csv`
- `user_data/walk_forward_results/MultiTimeframeTrend/walk_forward_summary.csv`
- `user_data/walk_forward_results/ATRAdaptiveMeanReversion/walk_forward_summary.csv`

## 18.2 Per-Fold Results

### MultiTimeframeTrend

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | 1.61 | 1.80 | 0.46 | -0.71 | -1.70 | 0.88 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | 1.14 | 2.70 | 0.00 | -1.06 | -2.70 | 1.06 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 1.96 | 1.51 | 1.50 | 0.37 | 1.04 | 1.05 | Pass |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | 1.32 | 1.14 | 1.07 | 0.20 | 0.49 | 0.56 | Pass |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 4.25 | 3.44 | 1.01 | -0.59 | -1.38 | 0.88 | Fail |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | 2.11 | 2.28 | 0.52 | 0.33 | 1.55 | 0.15 | Pass |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | 1.10 | 1.27 | 0.62 | 1.26 | 4.12 | 0.52 | Pass |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 4 of 7 |
| Average IS profit % | 1.93 |
| Average IS Sharpe | 2.02 |
| Worst IS max DD % | 1.50 |
| Average OOS profit % | -0.03 |
| Average OOS Sharpe | 0.20 |
| Worst OOS max DD % | 1.06 |

### ATRAdaptiveMeanReversion

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | 0.30 | 0.22 | 0.55 | 0.03 | -100.00 | 0.00 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | 0.66 | 0.91 | 0.02 | -0.23 | -1.57 | 0.23 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 0.44 | 0.46 | 1.02 | 0.46 | 3.35 | 0.00 | Pass |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | 0.80 | 2.45 | 0.08 | -0.48 | -2.00 | 0.54 | Fail |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 1.24 | 2.56 | 0.12 | -3.46 | -7.46 | 3.46 | Fail |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | 0.80 | 1.75 | 0.09 | -0.88 | -1.81 | 1.06 | Fail |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | 0.28 | 0.41 | 0.27 | -0.75 | -3.11 | 0.75 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 2 of 7 |
| Average IS profit % | 0.65 |
| Average IS Sharpe | 1.25 |
| Worst IS max DD % | 1.02 |
| Average OOS profit % | -0.76 |
| Average OOS Sharpe | -16.09 |
| Worst OOS max DD % | 3.46 |

## 18.3 Acceptance Criteria

These criteria were fixed before interpreting the run:

| Strategy | Criterion | Required | Observed | Result |
|---|---|---:|---:|---|
| `MultiTimeframeTrend` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `MultiTimeframeTrend` | Average OOS Sharpe | > 0 | 0.20 | Pass |
| `MultiTimeframeTrend` | Average OOS total profit % | > 0 | -0.03 | Fail |
| `MultiTimeframeTrend` | No single OOS fold drawdown | <= 5.00% | 1.06% worst | Pass |
| `ATRAdaptiveMeanReversion` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `ATRAdaptiveMeanReversion` | Average OOS Sharpe | > 0 | -16.09 | Fail |
| `ATRAdaptiveMeanReversion` | Average OOS total profit % | > 0 | -0.76 | Fail |
| `ATRAdaptiveMeanReversion` | No single OOS fold drawdown | <= 5.00% | 3.46% worst | Pass |

All four criteria had to pass to keep researching a strategy. Since both strategies
failed average OOS profit, both are rejected.

## 18.4 Decision

Reject `MultiTimeframeTrend` and `ATRAdaptiveMeanReversion`.

`MultiTimeframeTrend` came closest: four of seven folds were profitable, drawdown was
well controlled, and average OOS Sharpe was positive. The average OOS profit still
finished slightly negative, so the result does not clear the pre-registered gate.

`ATRAdaptiveMeanReversion` failed more clearly. It lost money in five of seven folds,
had negative average OOS profit, and had strongly negative average OOS Sharpe. Its
drawdown stayed below the cap, but drawdown control without positive expectancy is not
enough to continue.

Do not paper-trade either strategy and do not tune either strategy further on the same
window set.

## 18.5 Next Step

Task I is not applicable because no strategy passed the walk-forward acceptance
criteria. Do not run regime-filter experiments on these rejected baselines.

Task J is also not applicable because no strategy passed the paper-trade gate
prerequisite. Starting a four-week dry run from these results would skip the validation
rules that rejected the prior 5m strategies.

Keep both 1h strategies as rejected research hypotheses. The next candidate should start
from a new hypothesis or a materially different validation plan approved before looking
at results.

[Back to docs index](README.md)
