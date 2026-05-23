# 13. Walk-Forward Validation Results

This report captures the first walk-forward validation sweep for the baseline
strategies that survived the same-window backtest screen.

## 13.1 Scope

Two strategies were selected from the baseline validation step:

- `RSITrend`
- `BollingerMeanReversion`

Both were tested with the same walk-forward configuration:

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2025-01-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --spaces buy sell \
    --freqtrade-bin .venv/bin/freqtrade \
    --output-dir user_data/walk_forward_results/<StrategyName>
```

The raw Freqtrade logs, exported backtests, copied parameter files, CSV
summaries, and stability plots were generated under
`user_data/walk_forward_results/`. That directory is intentionally gitignored
because it is local run output.

## 13.2 Results

| Strategy | Fold | In-Sample Window | Out-of-Sample Window | IS Sharpe | IS Profit % | OOS Sharpe | OOS Profit % | Decision |
|---|---:|---|---|---:|---:|---:|---:|---|
| `RSITrend` | 1 | 2025-01-01 to 2025-04-01 | 2025-04-01 to 2025-05-01 | 1.78 | 0.17 | -100.00 | -0.08 | Reject |
| `BollingerMeanReversion` | 1 | 2025-01-01 to 2025-04-01 | 2025-04-01 to 2025-05-01 | 1.11 | 0.14 | -0.47 | -0.02 | Reject |

## 13.3 Interpretation

Both strategies improved in-sample after hyperopt but failed to preserve the
signal out-of-sample. The absolute losses were small, but the direction is the
important part: optimization found parameters that fit the January-April window
without producing a durable April holdout result.

This is not evidence of a tradable edge. Keep both strategies as research
controls, not candidates for paper trading.

## 13.4 Next Step

Build the strategy comparison report listed in `TASKS.md`, using the baseline
backtest table and this walk-forward summary as inputs. The next research
iteration should focus on new filters or exits rather than tuning these same
baseline parameters harder.

[Back to docs index](README.md)
