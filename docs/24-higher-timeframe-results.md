# 24. Higher-Timeframe Sweep Results

This report documents Sprint 23: testing the final unsearched
indicator-on-OKX-spot cell, `1d` as the primary trading timeframe on the four
major pairs.

The result is a rejection for the higher-timeframe sweep. None of the five
daily baseline variants passed the same-window trade-count screen. No strategy
advanced to walk-forward validation, Tier 2 multi-timeframe confirmation,
regime-filter experiments, or paper trading.

## 24.1 Scope

Run dates: 2026-05-31.

Hypothesis: prior 5m and 1h failures may have been dominated by fee friction.
Moving the same baseline logic to 1d candles should reduce the round-trip fee
burden by roughly 10-20x versus 5m while keeping the strategy, universe, and
validation gates pre-registered.

Strategies tested:

- `EMACrossoverDaily`
- `DonchianBreakoutDaily`
- `BollingerMeanReversionDaily`
- `RSITrendDaily`
- `MACDVolumeDaily`

Universe and data:

- Pairs: `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`
- Exchange/data directory: OKX spot, `user_data/data/okx/`
- Primary timeframe: `1d`
- Window: 2022-01-01 through 2025-05-01
- Additional downloaded timeframes for the conditional Tier 2 path: `1w`, `4h`

Pre-registered daily risk settings:

| Strategy | Stoploss | Minimal ROI |
|---|---:|---|
| `EMACrossoverDaily` | -0.10 | `{"0": 0.20}` |
| `DonchianBreakoutDaily` | -0.08 | `{"0": 0.25}` |
| `BollingerMeanReversionDaily` | -0.06 | `{"0": 0.08}` |
| `RSITrendDaily` | -0.10 | `{"0": 0.20}` |
| `MACDVolumeDaily` | -0.10 | `{"0": 0.20}` |

> **Note.** During execution, the same-window harness was corrected to pass an
> explicit `--timeframe 1d` to Freqtrade. Without that override, config-level
> `timeframe = "5m"` can override the strategy class timeframe. The results
> below are from the corrected `1d` run.

## 24.2 Same-Window Screen

Command:

```bash
python scripts/run_baselines.py \
    --strategies EMACrossoverDaily DonchianBreakoutDaily BollingerMeanReversionDaily RSITrendDaily MACDVolumeDaily \
    --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
    --timerange=20220101-20250501 \
    --timeframe 1d
```

Screen criteria:

- At least 50 trades.
- Max drawdown below 30%.

| Strategy | Trades | Win Rate % | Total Profit % | Sharpe | Max DD % | Profit Factor | Screen Result |
|---|---:|---:|---:|---:|---:|---:|---|
| `EMACrossoverDaily` | 27 | 29.63 | 1.50 | 0.03 | 2.81 | 1.13 | Fail: trades |
| `DonchianBreakoutDaily` | 32 | 37.50 | 15.09 | 0.19 | 4.27 | 2.01 | Fail: trades |
| `BollingerMeanReversionDaily` | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | Fail: trades |
| `RSITrendDaily` | 4 | 25.00 | -0.14 | -0.00 | 2.10 | 0.94 | Fail: trades |
| `MACDVolumeDaily` | 45 | 37.78 | 6.70 | 0.11 | 4.30 | 1.36 | Fail: trades |

No strategy passed the Step 1 screen. The strongest by raw profit,
`DonchianBreakoutDaily`, still produced only 32 trades across 3+ years and four
pairs. `MACDVolumeDaily` came closest to the trade-count threshold with 45
trades, but still failed the pre-registered gate.

Per-pair Step 1 trade counts:

| Pair | EMA | Donchian | Bollinger | RSI | MACD |
|---|---:|---:|---:|---:|---:|
| `BTC/USDT` | 6 | 11 | 0 | 2 | 15 |
| `ETH/USDT` | 10 | 11 | 0 | 0 | 12 |
| `SOL/USDT` | 5 | 8 | 0 | 2 | 10 |
| `BNB/USDT` | 6 | 2 | 0 | 0 | 8 |
| **TOTAL** | 27 | 32 | 0 | 4 | 45 |

Source summary:

- `user_data/backtest_results/baseline_validation_summary.csv`

## 24.3 Walk-Forward Results

Command template, pre-registered for any same-window survivor:

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2022-01-01 --end 2025-05-01 \
    --in-sample 365d --out-sample 90d --step 90d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --freqtrade-bin .venv/bin/freqtrade \
    -j 1 \
    --output-dir user_data/walk_forward_results/<StrategyName>
```

No walk-forward validation was run because Step 1 produced zero survivors.
This follows the hard Tier 1 gate from [23. Higher-Timeframe Sweep](23-higher-timeframe-sweep.md)
§23.6.

The walk-forward harness was also corrected to support explicit `--pairs` and
`--timeframe` arguments for future runs. The attempted `RSITrendDaily`
walk-forward before this correction was discarded because it exposed that the
harness would otherwise inherit the broader config whitelist and config-level
timeframe.

## 24.4 Acceptance Criteria

These criteria were fixed before interpreting the run:

| Stage | Criterion | Required | Observed | Result |
|---|---|---:|---:|---|
| Same-window screen | `EMACrossoverDaily` trades | >= 50 | 27 | Fail |
| Same-window screen | `DonchianBreakoutDaily` trades | >= 50 | 32 | Fail |
| Same-window screen | `BollingerMeanReversionDaily` trades | >= 50 | 0 | Fail |
| Same-window screen | `RSITrendDaily` trades | >= 50 | 4 | Fail |
| Same-window screen | `MACDVolumeDaily` trades | >= 50 | 45 | Fail |
| Same-window screen | Worst max drawdown | < 30.00% | 4.30% | Pass |
| Walk-forward | Completed OOS folds | >= 3 | 0 | Not run |
| Walk-forward | Average OOS Sharpe | > 0 | N/A | Not run |
| Walk-forward | Average OOS total profit % | > 0 | N/A | Not run |
| Walk-forward | No single OOS fold drawdown | <= 5.00% | N/A | Not run |

All five daily variants failed the same-window trade-count gate. The low
drawdowns and positive same-window returns for some variants are not enough to
advance because the sample size is too sparse for walk-forward conclusions.

## 24.5 Decision

Reject the Sprint 23 higher-timeframe sweep.

The 1d timeframe did reduce drawdowns and fee friction, but it also reduced
trade frequency below the minimum sample-size requirement. Across the full
2022-01-01 to 2025-05-01 window, no baseline generated 50 trades across the
four major pairs. The hard Tier 1 gate therefore stops the sprint before
walk-forward validation.

Do not paper-trade any Sprint 23 daily variant. Do not run regime-filter
experiments on these variants because none passed walk-forward acceptance. Do
not implement or run the conditional `MultiTimeframeConfirmation` Tier 2 path
because it was gated on at least one Tier 1 Step 3 survivor.

## 24.6 Next Step

Task H is not applicable because Task F produced zero Step 3 survivors. Tasks I,
J, and K are likewise blocked by the same acceptance gate.

Section 23.8 now applies with no further escape hatches. The indicator-on-OKX
spot direction has been tested across baseline strategies, regime filters,
1h candidates, top-20 universe expansion, daily momentum selection, and now 1d
primary trading on the four majors. The next sprint must choose a structurally
different direction:

- FreqAI or another ML track on engineered features.
- Perpetuals plus funding-rate/arbitrage research.
- Stop the lab here rather than continue adding spot-indicator variants.

[Back to docs index](README.md)
