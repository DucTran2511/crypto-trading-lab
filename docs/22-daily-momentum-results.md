# 22. Daily Momentum Ranking Results

This report documents Sprint 21: ranking the Sprint 19 top-20 OKX spot universe
by trailing 1-day momentum and restricting baseline strategy entries to the
current top-3 pairs.

The result is a rejection for the daily-momentum-ranking sprint. Three ranked
variants passed the same-window trade-count/drawdown screen, but all three failed
seven-fold walk-forward acceptance. No strategy advances to regime-filter
experiments or paper trading.

## 22.1 Scope

Run dates: 2026-05-30.

Hypothesis: the prior failures may have been caused by trading all eligible
pairs instead of selecting the strongest movers each day. This sprint therefore
changed only the pair-selection layer. The baseline strategy logic, timeframe,
top-20 universe, `max_open_trades = 2`, and risk posture stayed unchanged.

Strategies tested:

- `EMACrossoverDailyRanked`
- `DonchianBreakoutDailyRanked`
- `BollingerMeanReversionDailyRanked`
- `RSITrendDailyRanked`
- `MACDVolumeDailyRanked`

Ranking methodology:

- Universe: `user_data/universes/top20_okx_2024-07-01.json`
- Ranking file: `user_data/universes/daily_momentum_rank_20240701-20250501.json`
- Signal: trailing 1-day return on closed UTC daily candles
- Gate: allow entries only when the entry candle's prior completed UTC day ranks
  the pair in the top 3
- Stored ranking: full top-20 ordering per day, with downstream strategies using
  `top_n = 3`

Ranking sanity checks from Task E:

- 304 ranked UTC days from 2024-07-01 through 2025-05-01
- Every ranked day has exactly 20 pairs
- Spot checks:
  - 2024-07-15 top-3: `PEOPLE/USDT`, `TURBO/USDT`, `FLOKI/USDT`
  - 2025-01-20 top-3: `ENS/USDT`, `SOL/USDT`, `ETH/USDT`
  - 2025-04-15 top-3: `TON/USDT`, `ENS/USDT`, `ETH/USDT`

## 22.2 Same-Window Screen

Command:

```bash
python scripts/run_baselines.py \
    --strategies EMACrossoverDailyRanked DonchianBreakoutDailyRanked BollingerMeanReversionDailyRanked RSITrendDailyRanked MACDVolumeDailyRanked \
    --pairs BTC/USDT ETH/USDT SOL/USDT PEPE/USDT TON/USDT PEOPLE/USDT DOGE/USDT ORDI/USDT TURBO/USDT XRP/USDT FIL/USDT SUI/USDT SHIB/USDT FLOKI/USDT WLD/USDT NEAR/USDT LTC/USDT ENS/USDT BNB/USDT UNI/USDT \
    --timerange=20250101-20250501
```

Screen criteria:

- At least 50 trades.
- Max drawdown below 30%.

| Strategy | Trades | Win Rate % | Total Profit % | Sharpe | Max DD % | Profit Factor | Screen Result |
|---|---:|---:|---:|---:|---:|---:|---|
| `EMACrossoverDailyRanked` | 627 | 31.26 | -18.93 | -22.65 | 19.33 | 0.58 | Pass |
| `DonchianBreakoutDailyRanked` | 751 | 31.56 | -27.01 | -21.26 | 29.53 | 0.65 | Pass |
| `BollingerMeanReversionDailyRanked` | 4 | 75.00 | 0.15 | 0.26 | 0.10 | 2.47 | Fail: trades |
| `RSITrendDailyRanked` | 67 | 20.90 | -1.96 | -2.98 | 2.90 | 0.52 | Pass |
| `MACDVolumeDailyRanked` | 1131 | 25.55 | -31.58 | -43.21 | 31.97 | 0.54 | Fail: drawdown |

`EMACrossoverDailyRanked`, `DonchianBreakoutDailyRanked`, and
`RSITrendDailyRanked` advanced to walk-forward validation.

Per-pair Step 1 trade counts:

| Pair | EMA | Donchian | Bollinger | RSI | MACD |
|---|---:|---:|---:|---:|---:|
| `BTC/USDT` | 38 | 49 | 0 | 3 | 80 |
| `ETH/USDT` | 12 | 18 | 0 | 0 | 27 |
| `SOL/USDT` | 36 | 45 | 0 | 5 | 52 |
| `PEPE/USDT` | 42 | 41 | 1 | 6 | 68 |
| `TON/USDT` | 44 | 43 | 0 | 4 | 68 |
| `PEOPLE/USDT` | 43 | 45 | 0 | 3 | 57 |
| `DOGE/USDT` | 13 | 20 | 0 | 4 | 27 |
| `ORDI/USDT` | 42 | 62 | 0 | 2 | 69 |
| `TURBO/USDT` | 43 | 62 | 0 | 3 | 90 |
| `XRP/USDT` | 37 | 38 | 0 | 5 | 68 |
| `FIL/USDT` | 14 | 16 | 0 | 1 | 31 |
| `SUI/USDT` | 68 | 74 | 0 | 5 | 113 |
| `SHIB/USDT` | 9 | 12 | 0 | 2 | 22 |
| `FLOKI/USDT` | 15 | 12 | 0 | 2 | 28 |
| `WLD/USDT` | 31 | 41 | 2 | 4 | 54 |
| `NEAR/USDT` | 40 | 43 | 0 | 1 | 54 |
| `LTC/USDT` | 36 | 51 | 0 | 5 | 78 |
| `ENS/USDT` | 8 | 10 | 0 | 3 | 37 |
| `BNB/USDT` | 37 | 47 | 1 | 7 | 71 |
| `UNI/USDT` | 19 | 22 | 0 | 2 | 37 |
| **TOTAL** | 627 | 751 | 4 | 67 | 1131 |

Source summary:

- `user_data/backtest_results/baseline_validation_summary.csv`

## 22.3 Walk-Forward Results

Command template:

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --freqtrade-bin .venv/bin/freqtrade \
    -j 1 \
    --output-dir user_data/walk_forward_results/<StrategyName>
```

The `-j 1` option only constrained Freqtrade worker count. It did not change the
fold windows, strategy, hyperopt loss, hyperopt spaces, epoch count, pair
universe, ranking gate, or acceptance criteria.

### `EMACrossoverDailyRanked`

Source summary:

- `user_data/walk_forward_results/EMACrossoverDailyRanked/walk_forward_summary.csv`

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | 0.10 | 0.19 | 0.49 | -0.74 | -3.23 | 0.75 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | 0.33 | 0.47 | 1.96 | -0.37 | -1.34 | 0.78 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 1.03 | 1.46 | 1.46 | -2.30 | -9.26 | 2.62 | Fail |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | 0.66 | 0.83 | 1.18 | 1.19 | 3.00 | 0.60 | Pass |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 2.23 | 1.16 | 2.47 | -0.90 | -3.71 | 1.62 | Fail |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | 0.09 | 0.32 | 0.01 | 0.06 | 0.79 | 0.03 | Pass |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | 0.50 | 0.78 | 0.00 | 0.00 | 0.00 | 0.00 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 2 of 7 |
| Average IS profit % | 0.70 |
| Average IS Sharpe | 0.74 |
| Worst IS max DD % | 2.47 |
| Average OOS profit % | -0.44 |
| Average OOS Sharpe | -1.96 |
| Worst OOS max DD % | 2.62 |

### `DonchianBreakoutDailyRanked`

Source summary:

- `user_data/walk_forward_results/DonchianBreakoutDailyRanked/walk_forward_summary.csv`

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | -9.97 | -9.05 | 12.49 | -1.76 | -5.03 | 3.62 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | -6.37 | -6.17 | 9.97 | 0.94 | 1.45 | 5.35 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 1.13 | 0.77 | 5.73 | -4.60 | -10.76 | 4.98 | Fail |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | -0.27 | -0.19 | 7.56 | -0.59 | -1.70 | 2.05 | Fail |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 2.36 | 1.55 | 7.87 | -6.05 | -21.35 | 6.43 | Fail |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | -9.10 | -8.51 | 9.92 | -5.22 | -16.84 | 5.66 | Fail |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | -10.45 | -10.86 | 11.70 | -3.09 | -8.08 | 4.94 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 1 of 7 |
| Average IS profit % | -4.67 |
| Average IS Sharpe | -4.64 |
| Worst IS max DD % | 12.49 |
| Average OOS profit % | -2.91 |
| Average OOS Sharpe | -8.90 |
| Worst OOS max DD % | 6.43 |

### `RSITrendDailyRanked`

Source summary:

- `user_data/walk_forward_results/RSITrendDailyRanked/walk_forward_summary.csv`

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | 1.06 | 1.49 | 0.49 | -0.73 | -9.16 | 0.86 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | 0.47 | 0.62 | 0.27 | 0.00 | 0.00 | 0.00 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 0.80 | 1.38 | 0.27 | -0.48 | -2.23 | 0.48 | Fail |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | 0.46 | 0.70 | 0.14 | -0.34 | -2.13 | 0.39 | Fail |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 0.64 | 0.64 | 1.35 | -1.08 | -8.62 | 1.08 | Fail |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | 0.25 | 0.71 | 0.00 | -0.13 | -100.00 | 0.13 | Fail |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | -0.08 | -0.17 | 0.13 | -0.26 | -7.89 | 0.26 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 0 of 7 |
| Average IS profit % | 0.51 |
| Average IS Sharpe | 0.77 |
| Worst IS max DD % | 1.35 |
| Average OOS profit % | -0.43 |
| Average OOS Sharpe | -18.57 |
| Worst OOS max DD % | 1.08 |

## 22.4 Acceptance Criteria

These criteria were fixed before interpreting the run:

| Strategy | Criterion | Required | Observed | Result |
|---|---|---:|---:|---|
| `EMACrossoverDailyRanked` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `EMACrossoverDailyRanked` | Average OOS Sharpe | > 0 | -1.96 | Fail |
| `EMACrossoverDailyRanked` | Average OOS total profit % | > 0 | -0.44 | Fail |
| `EMACrossoverDailyRanked` | No single OOS fold drawdown | <= 5.00% | 2.62% worst | Pass |
| `DonchianBreakoutDailyRanked` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `DonchianBreakoutDailyRanked` | Average OOS Sharpe | > 0 | -8.90 | Fail |
| `DonchianBreakoutDailyRanked` | Average OOS total profit % | > 0 | -2.91 | Fail |
| `DonchianBreakoutDailyRanked` | No single OOS fold drawdown | <= 5.00% | 6.43% worst | Fail |
| `RSITrendDailyRanked` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `RSITrendDailyRanked` | Average OOS Sharpe | > 0 | -18.57 | Fail |
| `RSITrendDailyRanked` | Average OOS total profit % | > 0 | -0.43 | Fail |
| `RSITrendDailyRanked` | No single OOS fold drawdown | <= 5.00% | 1.08% worst | Pass |

All four criteria had to pass to keep researching a strategy. None did.

## 22.5 Decision

Reject the Sprint 21 daily-momentum-ranking result.

Daily momentum selection reduced the trading universe to the strongest three
pairs each UTC day, but it did not create a validated edge. The same-window
screen let three variants through, which was enough to justify walk-forward
validation. Out of sample, all three had negative average Sharpe and negative
average profit. `DonchianBreakoutDailyRanked` also breached the 5% single-fold
drawdown cap.

Do not paper-trade any Sprint 21 ranked variant. Do not run regime-filter
experiments on these variants as survivors because none passed walk-forward
acceptance.

## 22.6 Next Step

Task I is not applicable because Task G produced no passing Step 3 survivor.
Regime gating is reserved for strategies that first pass walk-forward validation.

Task J is not applicable because no strategy passed the paper-trade gate
prerequisite. Starting a four-week dry run from these results would skip the
validation rules that rejected the candidates.

The kill criterion from [21. Daily Momentum Ranking](21-daily-momentum-ranking.md)
§21.8 now applies. The indicator-on-OKX-spot direction has now been tested
across baseline strategy, regime filter, timeframe, static universe expansion,
and dynamic daily-momentum pair selection. The next sprint should address a
structurally different direction: FreqAI on engineered features, or a separate
perps/funding-rate research track.

[Back to docs index](README.md)
