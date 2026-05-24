# 15. Regime Filter Experiments

Use this workflow after the baseline comparison report has identified a strategy worth
researching further. The current control is `BollingerMeanReversion`; `RSITrend` is a
secondary control because it had enough trades but failed walk-forward validation.

The experiment harness compares four variants for each selected strategy:

| Variant | Allowed regimes | Purpose |
|---|---|---|
| `all-regime` | all | Original baseline control. |
| `bull-only` | `bull` | Only trade directional uptrends. |
| `bear-excluded` | `bull`, `range` | Avoid classified downtrends. |
| `trending-only` | `bull`, `bear` | Trade only when ADX says the market is trending. |

## 15.1 Run the experiment

```bash
python scripts/regime_filter_experiments.py \
    --strategies BollingerMeanReversion RSITrend \
    --timerange=20250101-20250501
```

Outputs are written under `user_data/regime_filter_results/`:

- `generated_strategies/` contains temporary Freqtrade strategy classes for the filtered
  variants.
- `regime_filter_summary.csv` contains machine-readable metrics and deltas versus the
  unfiltered control.
- `regime_filter_summary.md` contains the human-readable decision table.

The generated strategy classes call each baseline strategy first, then clear `enter_long`
where `user_data.regime.classifier.classify_regime()` does not match the variant's allowed
regimes. That keeps the baseline entry/exit logic unchanged and isolates the regime filter.

## 15.2 Promotion rule

A filtered variant is only marked as a walk-forward candidate when it:

1. Keeps at least `--min-trades` trades, default `20`.
2. Improves total profit percentage versus its `all-regime` control.
3. Does not worsen max drawdown versus the control, unless explicitly allowed with
   `--max-drawdown-worsening-pct`.

This is a screen, not proof. A promoted variant still needs walk-forward validation before
any claim that the filter works.

## 15.3 Walk-forward promoted variants

To run walk-forward automatically for promoted variants:

```bash
python scripts/regime_filter_experiments.py \
    --strategies BollingerMeanReversion RSITrend \
    --timerange=20250101-20250501 \
    --walk-forward-promising \
    --wf-start 2025-01-01 --wf-end 2025-05-01 \
    --wf-in-sample 90d --wf-out-sample 30d --wf-step 30d \
    --wf-loss SharpeHyperOptLoss --wf-epochs 100
```

Walk-forward outputs are written to
`user_data/regime_filter_results/walk_forward/<GeneratedStrategyName>/`.

## 15.4 Interpretation

Keep the original `all-regime` row as the control in every discussion. If a filtered row
improves profit by reducing trades to a tiny sample, reject it as under-sampled. If it
passes the screen but fails walk-forward, reject it as overfit. Only variants with positive
out-of-sample fold behavior deserve another research iteration.

## 15.5 Current Run

Run date: 2026-05-24.

Same-window screen, `20250101-20250501`:

| Strategy | Variant | Trades | Profit % | Delta Profit % | Max DD % | Walk-forward candidate |
|---|---|---:|---:|---:|---:|---|
| `BollingerMeanReversion` | `all-regime` | 9 | 0.09 | 0.00 | 0.03 | no |
| `BollingerMeanReversion` | `bull-only` | 5 | 0.09 | 0.00 | 0.03 | no |
| `BollingerMeanReversion` | `bear-excluded` | 9 | 0.09 | 0.00 | 0.03 | no |
| `BollingerMeanReversion` | `trending-only` | 5 | 0.09 | 0.00 | 0.03 | no |
| `RSITrend` | `all-regime` | 76 | -1.73 | 0.00 | 1.89 | no |
| `RSITrend` | `bull-only` | 51 | -0.75 | 0.98 | 1.01 | yes |
| `RSITrend` | `bear-excluded` | 64 | -0.88 | 0.85 | 1.10 | yes |
| `RSITrend` | `trending-only` | 63 | -1.60 | 0.13 | 1.80 | yes |

Promoted walk-forward validation, `2025-01-01` to `2025-05-01`, 90d in-sample and
30d out-of-sample:

| Strategy variant | IS Profit % | IS Sharpe | OOS Profit % | OOS Sharpe | Decision |
|---|---:|---:|---:|---:|---|
| `RSITrendBullOnly` | 0.03 | 0.09 | 0.02 | 0.25 | Keep as a weak research candidate only. |
| `RSITrendBearExcluded` | 0.17 | 1.78 | N/A | N/A | Reject for no out-of-sample trades/metrics. |
| `RSITrendTrendingOnly` | -0.03 | -0.11 | -0.07 | -0.81 | Reject. |

`RSITrendBullOnly` is not tradable from this evidence; the result is small and only one
fold. It is the only regime-filtered variant worth a further multi-window research pass.

[Back to docs index](README.md)
