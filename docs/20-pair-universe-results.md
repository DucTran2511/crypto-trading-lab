# 20. Pair Universe Expansion Results

This report documents Sprint 19: expanding the OKX spot universe from four majors
to the top-20 USDT pairs while reusing the existing 5m baseline strategies.

The result is a rejection for the expanded-universe sprint. `RSITrend` was the
only strategy to pass the same-window trade-count/drawdown screen, but it failed
seven-fold walk-forward acceptance because average out-of-sample Sharpe and
average out-of-sample profit were both negative.

## 20.1 Scope

Run dates: 2026-05-27.

Hypothesis: the prior failures may have been caused by the over-served BTC, ETH,
SOL, and BNB universe rather than by the baseline strategy logic. This sprint
therefore changed only the pair universe. Strategy classes and timeframe stayed
unchanged.

Strategies tested:

- `EMACrossover`
- `DonchianBreakout`
- `BollingerMeanReversion`
- `RSITrend`
- `MACDVolume`

Universe source:

- `user_data/universes/top20_okx_2024-07-01.json`
- OKX spot, USDT quote
- Snapshot date: 2024-07-01
- Ranking: historical 30-day quote volume ending 2024-07-01 from local OKX OHLCV
- Exclusions: stablecoins, wrapped tokens, leveraged tokens, synthetic/inverse
  pairs, and pairs without six months of OKX history as of the snapshot date

Committed universe snapshot:

```json
{
  "exchange": "okx",
  "market": "spot",
  "quote": "USDT",
  "snapshot_date": "2024-07-01",
  "selection": "top 20 by historical 30d quote volume ending 2024-07-01",
  "timeframe": "1d",
  "volume_window_days": 30,
  "min_history_months": 6,
  "pairs": [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "PEPE/USDT",
    "TON/USDT",
    "PEOPLE/USDT",
    "DOGE/USDT",
    "ORDI/USDT",
    "TURBO/USDT",
    "XRP/USDT",
    "FIL/USDT",
    "SUI/USDT",
    "SHIB/USDT",
    "FLOKI/USDT",
    "WLD/USDT",
    "NEAR/USDT",
    "LTC/USDT",
    "ENS/USDT",
    "BNB/USDT",
    "UNI/USDT"
  ],
  "candidates": [
    {
      "pair": "BTC/USDT",
      "inst_id": "BTC-USDT",
      "base": "BTC",
      "quote_volume_30d": 12132207300.981245,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "ETH/USDT",
      "inst_id": "ETH-USDT",
      "base": "ETH",
      "quote_volume_30d": 8071585384.796876,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "SOL/USDT",
      "inst_id": "SOL-USDT",
      "base": "SOL",
      "quote_volume_30d": 2789013874.3170524,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "PEPE/USDT",
      "inst_id": "PEPE-USDT",
      "base": "PEPE",
      "quote_volume_30d": 2310964153.7510357,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "TON/USDT",
      "inst_id": "TON-USDT",
      "base": "TON",
      "quote_volume_30d": 2009058652.626474,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "PEOPLE/USDT",
      "inst_id": "PEOPLE-USDT",
      "base": "PEOPLE",
      "quote_volume_30d": 1285681006.1526613,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "DOGE/USDT",
      "inst_id": "DOGE-USDT",
      "base": "DOGE",
      "quote_volume_30d": 1272149900.835706,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "ORDI/USDT",
      "inst_id": "ORDI-USDT",
      "base": "ORDI",
      "quote_volume_30d": 1074648780.232776,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "TURBO/USDT",
      "inst_id": "TURBO-USDT",
      "base": "TURBO",
      "quote_volume_30d": 946007206.081316,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "XRP/USDT",
      "inst_id": "XRP-USDT",
      "base": "XRP",
      "quote_volume_30d": 630430195.2273045,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "FIL/USDT",
      "inst_id": "FIL-USDT",
      "base": "FIL",
      "quote_volume_30d": 599681415.7725252,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "SUI/USDT",
      "inst_id": "SUI-USDT",
      "base": "SUI",
      "quote_volume_30d": 443833656.1431297,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "SHIB/USDT",
      "inst_id": "SHIB-USDT",
      "base": "SHIB",
      "quote_volume_30d": 413730958.80241686,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "FLOKI/USDT",
      "inst_id": "FLOKI-USDT",
      "base": "FLOKI",
      "quote_volume_30d": 382575738.7558658,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "WLD/USDT",
      "inst_id": "WLD-USDT",
      "base": "WLD",
      "quote_volume_30d": 377624074.471086,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "NEAR/USDT",
      "inst_id": "NEAR-USDT",
      "base": "NEAR",
      "quote_volume_30d": 348782317.4711227,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "LTC/USDT",
      "inst_id": "LTC-USDT",
      "base": "LTC",
      "quote_volume_30d": 342145221.06602734,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "ENS/USDT",
      "inst_id": "ENS-USDT",
      "base": "ENS",
      "quote_volume_30d": 340435256.8526412,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "BNB/USDT",
      "inst_id": "BNB-USDT",
      "base": "BNB",
      "quote_volume_30d": 337166800.1620253,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    },
    {
      "pair": "UNI/USDT",
      "inst_id": "UNI-USDT",
      "base": "UNI",
      "quote_volume_30d": 318444298.74658954,
      "candles": 30,
      "history_start": "2023-12-31",
      "history_end": "2024-07-15"
    }
  ]
}
```

## 20.2 Same-Window Screen

Command:

```bash
python scripts/run_baselines.py \
    --strategies EMACrossover DonchianBreakout BollingerMeanReversion RSITrend MACDVolume \
    --pairs BTC/USDT ETH/USDT SOL/USDT PEPE/USDT TON/USDT PEOPLE/USDT DOGE/USDT ORDI/USDT TURBO/USDT XRP/USDT FIL/USDT SUI/USDT SHIB/USDT FLOKI/USDT WLD/USDT NEAR/USDT LTC/USDT ENS/USDT BNB/USDT UNI/USDT \
    --timerange=20250101-20250501
```

Screen criteria:

- At least 50 trades.
- Max drawdown below 30%.

| Strategy | Trades | Win Rate % | Total Profit % | Sharpe | Max DD % | Profit Factor | Screen Result |
|---|---:|---:|---:|---:|---:|---:|---|
| `EMACrossover` | 1897 | 31.05 | -48.63 | -66.98 | 48.91 | 0.57 | Fail: drawdown |
| `DonchianBreakout` | 1250 | 31.76 | -38.72 | -32.53 | 40.23 | 0.66 | Fail: drawdown |
| `BollingerMeanReversion` | 14 | 42.86 | -0.70 | -0.91 | 0.85 | 0.28 | Fail: trades |
| `RSITrend` | 339 | 22.42 | -8.54 | -13.38 | 8.97 | 0.54 | Pass |
| `MACDVolume` | 3169 | 24.77 | -87.89 | -130.51 | 88.02 | 0.50 | Fail: drawdown |

Only `RSITrend` advanced to walk-forward validation.

Per-pair Step 1 results:

### `EMACrossover`

| Pair | Trades | Profit % | Max DD % | Profit Factor |
|---|---:|---:|---:|---:|
| `BTC/USDT` | 146 | -3.12 | 3.33 | 0.47 |
| `ETH/USDT` | 106 | -4.03 | 4.03 | 0.31 |
| `SOL/USDT` | 112 | -1.76 | 2.03 | 0.71 |
| `PEPE/USDT` | 121 | -4.42 | 5.46 | 0.47 |
| `TON/USDT` | 124 | -4.15 | 4.17 | 0.41 |
| `PEOPLE/USDT` | 107 | -2.45 | 3.17 | 0.67 |
| `DOGE/USDT` | 91 | -1.84 | 1.93 | 0.62 |
| `ORDI/USDT` | 99 | -0.53 | 1.63 | 0.91 |
| `TURBO/USDT` | 88 | -3.55 | 4.03 | 0.50 |
| `XRP/USDT` | 113 | -2.23 | 2.42 | 0.64 |
| `FIL/USDT` | 78 | -1.43 | 1.82 | 0.66 |
| `SUI/USDT` | 88 | -3.67 | 3.75 | 0.47 |
| `SHIB/USDT` | 73 | -1.06 | 2.11 | 0.73 |
| `FLOKI/USDT` | 67 | -0.45 | 1.68 | 0.89 |
| `WLD/USDT` | 87 | -3.14 | 3.14 | 0.53 |
| `NEAR/USDT` | 64 | -1.90 | 2.01 | 0.54 |
| `LTC/USDT` | 87 | -1.94 | 2.46 | 0.65 |
| `ENS/USDT` | 74 | -2.63 | 2.66 | 0.48 |
| `BNB/USDT` | 86 | -2.88 | 2.88 | 0.28 |
| `UNI/USDT` | 86 | -1.45 | 1.83 | 0.66 |
| **TOTAL** | 1897 | -48.63 | 48.91 | 0.57 |

### `DonchianBreakout`

| Pair | Trades | Profit % | Max DD % | Profit Factor |
|---|---:|---:|---:|---:|
| `BTC/USDT` | 114 | -2.91 | 3.15 | 0.59 |
| `ETH/USDT` | 86 | -2.68 | 3.05 | 0.60 |
| `SOL/USDT` | 88 | 0.12 | 2.13 | 1.02 |
| `PEPE/USDT` | 55 | -0.51 | 1.42 | 0.91 |
| `TON/USDT` | 98 | -5.05 | 5.32 | 0.37 |
| `PEOPLE/USDT` | 75 | -3.27 | 5.66 | 0.67 |
| `DOGE/USDT` | 45 | -1.69 | 2.18 | 0.56 |
| `ORDI/USDT` | 73 | -5.22 | 5.23 | 0.41 |
| `TURBO/USDT` | 63 | -2.23 | 3.13 | 0.72 |
| `XRP/USDT` | 64 | -0.42 | 1.75 | 0.92 |
| `FIL/USDT` | 47 | -1.66 | 2.23 | 0.52 |
| `SUI/USDT` | 59 | -0.74 | 1.52 | 0.85 |
| `SHIB/USDT` | 37 | 0.33 | 0.83 | 1.14 |
| `FLOKI/USDT` | 34 | -0.94 | 2.09 | 0.77 |
| `WLD/USDT` | 46 | -1.56 | 3.07 | 0.71 |
| `NEAR/USDT` | 45 | -2.22 | 2.43 | 0.51 |
| `LTC/USDT` | 79 | -3.56 | 3.70 | 0.52 |
| `ENS/USDT` | 33 | -0.38 | 1.06 | 0.89 |
| `BNB/USDT` | 80 | -2.90 | 2.90 | 0.37 |
| `UNI/USDT` | 29 | -1.23 | 1.69 | 0.53 |
| **TOTAL** | 1250 | -38.72 | 40.23 | 0.66 |

### `BollingerMeanReversion`

| Pair | Trades | Profit % | Max DD % | Profit Factor |
|---|---:|---:|---:|---:|
| `BTC/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `ETH/USDT` | 2 | 0.01 | 0.00 | 4.91 |
| `SOL/USDT` | 1 | 0.00 | 0.00 | 0.00 |
| `PEPE/USDT` | 1 | 0.01 | 0.00 | 0.00 |
| `TON/USDT` | 1 | -0.38 | 0.38 | 0.00 |
| `PEOPLE/USDT` | 1 | -0.09 | 0.09 | 0.00 |
| `DOGE/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `ORDI/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `TURBO/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `XRP/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `FIL/USDT` | 1 | -0.12 | 0.12 | 0.00 |
| `SUI/USDT` | 1 | -0.17 | 0.17 | 0.00 |
| `SHIB/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `FLOKI/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `WLD/USDT` | 1 | 0.15 | 0.00 | 0.00 |
| `NEAR/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `LTC/USDT` | 1 | -0.07 | 0.07 | 0.00 |
| `ENS/USDT` | 0 | 0.00 | 0.00 | 0.00 |
| `BNB/USDT` | 3 | 0.07 | 0.03 | 3.49 |
| `UNI/USDT` | 1 | -0.11 | 0.11 | 0.00 |
| **TOTAL** | 14 | -0.70 | 0.85 | 0.28 |

### `RSITrend`

| Pair | Trades | Profit % | Max DD % | Profit Factor |
|---|---:|---:|---:|---:|
| `BTC/USDT` | 18 | -0.32 | 0.40 | 0.48 |
| `ETH/USDT` | 18 | -0.09 | 0.30 | 0.85 |
| `SOL/USDT` | 20 | -0.61 | 0.61 | 0.48 |
| `PEPE/USDT` | 42 | -1.65 | 1.86 | 0.41 |
| `TON/USDT` | 20 | -0.97 | 0.97 | 0.19 |
| `PEOPLE/USDT` | 11 | -1.19 | 1.24 | 0.04 |
| `DOGE/USDT` | 23 | -0.50 | 0.61 | 0.58 |
| `ORDI/USDT` | 7 | 0.10 | 0.23 | 1.36 |
| `TURBO/USDT` | 13 | 0.36 | 0.29 | 1.55 |
| `XRP/USDT` | 20 | -0.45 | 0.53 | 0.57 |
| `FIL/USDT` | 17 | -0.97 | 0.97 | 0.05 |
| `SUI/USDT` | 14 | -0.40 | 0.49 | 0.53 |
| `SHIB/USDT` | 28 | -0.88 | 0.88 | 0.26 |
| `FLOKI/USDT` | 9 | -0.16 | 0.61 | 0.74 |
| `WLD/USDT` | 14 | -0.29 | 0.83 | 0.67 |
| `NEAR/USDT` | 12 | -0.11 | 0.46 | 0.83 |
| `LTC/USDT` | 15 | 0.29 | 0.32 | 1.41 |
| `ENS/USDT` | 12 | -0.41 | 0.61 | 0.38 |
| `BNB/USDT` | 12 | -0.14 | 0.34 | 0.67 |
| `UNI/USDT` | 14 | -0.15 | 0.42 | 0.76 |
| **TOTAL** | 339 | -8.54 | 8.97 | 0.54 |

### `MACDVolume`

| Pair | Trades | Profit % | Max DD % | Profit Factor |
|---|---:|---:|---:|---:|
| `BTC/USDT` | 237 | -6.92 | 6.92 | 0.30 |
| `ETH/USDT` | 207 | -5.83 | 5.83 | 0.40 |
| `SOL/USDT` | 206 | -4.64 | 4.74 | 0.55 |
| `PEPE/USDT` | 187 | -8.53 | 9.06 | 0.39 |
| `TON/USDT` | 193 | -5.28 | 5.35 | 0.40 |
| `PEOPLE/USDT` | 180 | -6.39 | 6.39 | 0.50 |
| `DOGE/USDT` | 137 | -1.79 | 2.36 | 0.70 |
| `ORDI/USDT` | 162 | -2.49 | 2.91 | 0.75 |
| `TURBO/USDT` | 174 | -6.51 | 6.85 | 0.52 |
| `XRP/USDT` | 144 | -1.94 | 2.52 | 0.72 |
| `FIL/USDT` | 146 | -2.91 | 3.24 | 0.57 |
| `SUI/USDT` | 149 | -2.77 | 3.12 | 0.70 |
| `SHIB/USDT` | 135 | -3.71 | 3.79 | 0.44 |
| `FLOKI/USDT` | 120 | -2.73 | 2.88 | 0.63 |
| `WLD/USDT` | 119 | -6.83 | 6.93 | 0.25 |
| `NEAR/USDT` | 122 | -2.37 | 2.37 | 0.64 |
| `LTC/USDT` | 164 | -3.47 | 3.69 | 0.61 |
| `ENS/USDT` | 125 | -4.00 | 4.00 | 0.45 |
| `BNB/USDT` | 133 | -3.78 | 3.78 | 0.30 |
| `UNI/USDT` | 129 | -5.02 | 5.11 | 0.39 |
| **TOTAL** | 3169 | -87.89 | 88.02 | 0.50 |

Source summary:

- `user_data/backtest_results/baseline_validation_summary.csv`

## 20.3 Walk-Forward Results

Command:

```bash
PYTHONWARNINGS=ignore python scripts/walk_forward.py \
    --strategy RSITrend \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --freqtrade-bin .venv/bin/freqtrade \
    -j 1
```

The `-j 1` option only constrained Freqtrade worker count. It did not change the
fold windows, strategy, hyperopt loss, hyperopt spaces, epoch count, pair universe,
or acceptance criteria. `PYTHONWARNINGS=ignore` was used to keep pandas
fragmentation warnings from overwhelming the run log.

Source summary:

- `user_data/walk_forward_results/walk_forward_summary.csv`

| Fold | In-sample window | Out-of-sample window | IS Profit % | IS Sharpe | IS Max DD % | OOS Profit % | OOS Sharpe | OOS Max DD % | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2024-07-01 to 2024-09-29 | 2024-09-29 to 2024-10-29 | -0.09 | -0.29 | 0.31 | 0.35 | -100.00 | 0.00 | Fail |
| 2 | 2024-07-31 to 2024-10-29 | 2024-10-29 to 2024-11-28 | 0.07 | 0.17 | 0.47 | -0.04 | -100.00 | 0.04 | Fail |
| 3 | 2024-08-30 to 2024-11-28 | 2024-11-28 to 2024-12-28 | 0.40 | 0.75 | 0.53 | -0.48 | -1.77 | 0.65 | Fail |
| 4 | 2024-09-29 to 2024-12-28 | 2024-12-28 to 2025-01-27 | 0.37 | 0.59 | 0.40 | -0.31 | -3.40 | 0.45 | Fail |
| 5 | 2024-10-29 to 2025-01-27 | 2025-01-27 to 2025-02-26 | 0.31 | 0.50 | 0.24 | 0.48 | 1.98 | 0.08 | Pass |
| 6 | 2024-11-28 to 2025-02-26 | 2025-02-26 to 2025-03-28 | 1.11 | 1.66 | 0.12 | -0.49 | -4.75 | 0.69 | Fail |
| 7 | 2024-12-28 to 2025-03-28 | 2025-03-28 to 2025-04-27 | 0.57 | 1.05 | 0.29 | -0.68 | -7.44 | 0.84 | Fail |

Aggregate:

| Metric | Value |
|---|---:|
| Completed OOS folds | 7 |
| Positive OOS folds | 2 of 7 |
| Average IS profit % | 0.39 |
| Average IS Sharpe | 0.63 |
| Worst IS max DD % | 0.53 |
| Average OOS profit % | -0.17 |
| Average OOS Sharpe | -30.77 |
| Worst OOS max DD % | 0.84 |

## 20.4 Acceptance Criteria

These criteria were fixed before interpreting the run:

| Strategy | Criterion | Required | Observed | Result |
|---|---|---:|---:|---|
| `RSITrend` | Completed out-of-sample folds | >= 3 | 7 | Pass |
| `RSITrend` | Average OOS Sharpe | > 0 | -30.77 | Fail |
| `RSITrend` | Average OOS total profit % | > 0 | -0.17 | Fail |
| `RSITrend` | No single OOS fold drawdown | <= 5.00% | 0.84% worst | Pass |

All four criteria had to pass to keep researching a strategy. `RSITrend` failed
average OOS Sharpe and average OOS profit, so it is rejected.

## 20.5 Decision

Reject the Sprint 19 pair-universe expansion result.

The expanded top-20 universe did increase trade counts for several strategies,
but it did not produce a validated edge. The three highest-activity strategies
failed the same-window screen because drawdown exceeded 30%. `BollingerMeanReversion`
had controlled drawdown but only 14 trades, far below the 50-trade screen.
`RSITrend` passed the same-window screen, then lost money out of sample in five
of seven folds and had strongly negative average OOS Sharpe.

Do not paper-trade `RSITrend` from this sprint. Do not run regime-filter
experiments on it as a survivor because it did not pass walk-forward acceptance.

## 20.6 Next Step

Task H is not applicable because Task F produced no passing Step 3 survivor.
Regime gating is reserved for strategies that first pass walk-forward validation.

Task I is not applicable because no strategy passed the paper-trade gate
prerequisite. Starting a four-week dry run from these results would skip the
validation rules that rejected the candidate.

The branching rule from [19. Pair Universe Expansion](19-pair-universe-expansion.md)
now applies. This was not the "zero of five strategies pass the same-window screen"
case, because `RSITrend` did pass Step 1. It was the "at least one strategy passes
the screen but none pass walk-forward" case, so the registered follow-up is the
daily-momentum-ranking sprint described in §19.8 before declaring the research
thread dead or escalating to FreqAI/perps.

[Back to docs index](README.md)
