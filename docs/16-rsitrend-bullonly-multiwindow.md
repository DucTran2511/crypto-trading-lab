# 16. RSITrendBullOnly Multi-Window Walk-Forward

This report documents the multi-window validation pass for `RSITrendBullOnly`, the only
regime-filtered variant that survived the same-window screen and one initial walk-forward
fold in [15. Regime Filter Experiments](15-regime-filter-experiments.md).

The result is a rejection. The variant completed three out-of-sample folds, but average
out-of-sample Sharpe and average out-of-sample profit were both negative.

## 16.1 Scope

Run date: 2026-05-24.

Command:

```bash
python scripts/walk_forward.py \
    --strategy RSITrendBullOnly \
    --strategy-path user_data/regime_filter_results/generated_strategies \
    --start 2025-01-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --spaces buy sell \
    --output-dir user_data/walk_forward_results/RSITrendBullOnly \
    --freqtrade-bin .venv/bin/freqtrade
```

Because additional OKX candles were prepended back to 2024-10-01 before the run, the
90-day in-sample windows could start before 2025-01-01 while still producing 2025
out-of-sample folds.

Source summary:
`user_data/walk_forward_results/RSITrendBullOnly/walk_forward_summary.csv`

## 16.2 Per-Fold Results

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-11-01 to 2025-01-30 | 2025-01-30 to 2025-03-01 | 0.05 | 0.11 | 0.18 | -0.22 | -3.21 | 0.22 | Fail |
| 2 | 2024-12-01 to 2025-03-01 | 2025-03-01 to 2025-03-31 | 0.00 | 0.01 | 0.34 | 0.17 | 2.80 | 0.00 | Pass |
| 3 | 2024-12-31 to 2025-03-31 | 2025-03-31 to 2025-04-30 | 0.32 | 0.92 | 0.14 | -0.12 | -1.03 | 0.18 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 3 |
| Positive OOS folds | 1 of 3 |
| Average IS profit % | 0.12 |
| Average IS Sharpe | 0.34 |
| Worst IS max DD % | 0.34 |
| Average OOS profit % | -0.06 |
| Average OOS Sharpe | -0.48 |
| Worst OOS max DD % | 0.22 |

## 16.3 Acceptance Criteria

These criteria were fixed before interpreting the run:

| Criterion | Required | Observed | Result |
|---|---:|---:|---|
| Completed out-of-sample folds | >= 3 | 3 | Pass |
| Average OOS Sharpe | > 0 | -0.48 | Fail |
| Average OOS total profit % | > 0 | -0.06 | Fail |
| No single OOS fold drawdown | <= 5.00% | 0.22% worst | Pass |

All four criteria had to pass to keep researching `RSITrendBullOnly`. Since two failed,
the variant is rejected.

## 16.4 Decision

Reject `RSITrendBullOnly`.

The first single-fold result looked weakly positive, but the broader run did not preserve
that behavior. Two of three out-of-sample folds lost money, average OOS Sharpe was
negative, and average OOS profit was negative. The low drawdown is not enough to keep the
variant alive because the edge did not survive across windows.

Do not paper-trade this variant and do not tune it further on the same window set.

## 16.5 Next Step

Task D does not apply because the validation did not pass acceptance. Do not design a
second validation pass for `RSITrendBullOnly` from this result.

Keep `RSITrendBullOnly` as a rejected regime-filter experiment and return to research
ideation. The next candidate should start from a new hypothesis, then pass the same
sequence: same-window screen, walk-forward validation, and only then any broader
second-pass validation.

[Back to docs index](README.md)
