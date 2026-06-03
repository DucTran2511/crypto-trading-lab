# 26. Spot Trend Strategy Results

This report documents Sprint 25: long-only OKX spot trend strategies on the
top-20 USDT universe over the 2020-01-01 through 2025-12-01 research window.

The result is a rejection for the Sprint 25 strategy set. Two strategies passed
the same-window Step 1 screen, but both failed the pre-registered Step 3
walk-forward acceptance gate from [25. Spot Trend Strategies](25-spot-trend-strategies.md)
§25.6. No strategy advanced to regime-filter experiments or paper trading.

## 26.1 Scope

Run dates: 2026-06-03.

Hypothesis: Sprint 23's strongest daily trend result may have failed because
the four-major universe and shorter 2022-01-01 to 2025-05-01 window were too
sparse for day-to-month hold horizons. Sprint 25 widened the universe to the
existing top-20 OKX USDT spot snapshot and extended the window to 2020-01-01
through 2025-12-01.

Strategies tested:

- `WeeklyDonchianBreakoutSpot`
- `TimeSeriesMomentumSpot`
- `DonchianBreakoutDailyTop20`

Universe and data:

- Pairs: `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `PEPE/USDT`, `TON/USDT`,
  `PEOPLE/USDT`, `DOGE/USDT`, `ORDI/USDT`, `TURBO/USDT`, `XRP/USDT`,
  `FIL/USDT`, `SUI/USDT`, `SHIB/USDT`, `FLOKI/USDT`, `WLD/USDT`,
  `NEAR/USDT`, `LTC/USDT`, `ENS/USDT`, `BNB/USDT`, `UNI/USDT`
- Exchange/data directory: OKX spot, `user_data/data/okx/`
- Primary timeframes: `1w` for `WeeklyDonchianBreakoutSpot`; `1d` for
  `TimeSeriesMomentumSpot` and `DonchianBreakoutDailyTop20`
- Requested window: 2020-01-01 through 2025-12-01
- Config: `user_data/config-sprint25-top20.json`

Pre-registered risk and lookback settings:

| Strategy | Timeframe | Stoploss | Minimal ROI | Entry Lookback | Exit Lookback |
|---|---|---:|---|---:|---:|
| `WeeklyDonchianBreakoutSpot` | `1w` | -0.20 | `{"0": 100.0}` | 20 weeks | 10 weeks |
| `TimeSeriesMomentumSpot` | `1d` | -0.25 | `{"0": 100.0}` | EMA 50/200, RSI 14, 100d vol percentile | EMA 50/200 cross |
| `DonchianBreakoutDailyTop20` | `1d` | -0.08 | `{"0": 0.25}` | 20 days | Sprint 23 baseline |

During Step 1 execution, `WeeklyDonchianBreakoutSpot.startup_candle_count` was
corrected from the inherited 5m baseline value of 240 to 100 weekly candles.
This keeps the startup period aligned with the longest weekly indicator
(`ema_trend = 100`) and prevents the 1w screen from discarding most of the
requested window.

## 26.2 Step 1 Same-Window Screen

Commands:

```bash
freqtrade backtesting -c user_data/config-sprint25-top20.json \
    --strategy WeeklyDonchianBreakoutSpot \
    --timerange=20200101-20251201 \
    --timeframe 1w

freqtrade backtesting -c user_data/config-sprint25-top20.json \
    --strategy TimeSeriesMomentumSpot \
    --timerange=20200101-20251201 \
    --timeframe 1d

freqtrade backtesting -c user_data/config-sprint25-top20.json \
    --strategy DonchianBreakoutDailyTop20 \
    --timerange=20200101-20251201 \
    --timeframe 1d
```

Screen criteria from [25. Spot Trend Strategies](25-spot-trend-strategies.md)
§25.6:

- At least 30 trades.
- Max drawdown below 30%.
- Total profit above 0%.

| Strategy | Timeframe | Trades | Total Profit % | Max DD % | Sharpe | Profit Factor | Step 1 Result |
|---|---|---:|---:|---:|---:|---:|---|
| `WeeklyDonchianBreakoutSpot` | `1w` | 29 | 20.84 | 30.62 | 0.04 | 1.44 | Fail: trades and drawdown |
| `TimeSeriesMomentumSpot` | `1d` | 102 | 1223.67 | 1.90 | 0.12 | 13.92 | Pass |
| `DonchianBreakoutDailyTop20` | `1d` | 282 | 80.66 | 28.93 | 0.32 | 1.48 | Pass |

`TimeSeriesMomentumSpot` and `DonchianBreakoutDailyTop20` advanced to Step 3.
`WeeklyDonchianBreakoutSpot` did not advance because it missed the trade floor
by one trade and breached the max-drawdown gate.

Source summary:

- `user_data/backtest_results/sprint25-step1.csv`

## 26.3 Step 3 Walk-Forward

Command template:

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2020-01-01 --end 2025-12-01 \
    --in-sample 730d --out-sample 180d --step 180d \
    --loss SharpeHyperOptLoss --epochs 100 \
    --freqtrade-bin .venv/bin/freqtrade \
    --pairs BTC/USDT ETH/USDT SOL/USDT PEPE/USDT TON/USDT PEOPLE/USDT DOGE/USDT ORDI/USDT TURBO/USDT XRP/USDT FIL/USDT SUI/USDT SHIB/USDT FLOKI/USDT WLD/USDT NEAR/USDT LTC/USDT ENS/USDT BNB/USDT UNI/USDT \
    --timeframe 1d \
    -c user_data/config-sprint25-top20.json \
    -j 1 \
    --output-dir user_data/walk_forward_results/<StrategyName>
```

Execution note: §25.6 estimated 8 OOS folds from the 2020-01-01 through
2025-12-01 window. The actual `scripts/walk_forward.py` fold generator admits
only complete OOS windows ending on or before 2025-12-01, which produced 7
complete folds. The absolute profitable-fold gate was still applied as written:
at least 4 profitable OOS folds.

`TimeSeriesMomentumSpot` has no hyperopt parameters by design. The
walk-forward harness therefore used static strategy defaults for each fold
after Freqtrade reported that no requested hyperopt space existed. The harness
was also hardened to retry transient OKX market-metadata reload failures during
child Freqtrade commands.

| Strategy | Folds | Profitable OOS Folds | Avg OOS Sharpe | Avg OOS Profit % | Worst OOS DD % | Step 3 Result |
|---|---:|---:|---:|---:|---:|---|
| `TimeSeriesMomentumSpot` | 7 | 3 | -0.62 | 6.99 | 35.57 | Fail |
| `DonchianBreakoutDailyTop20` | 7 | 3 | 0.28 | 13.63 | 19.20 | Fail |

`TimeSeriesMomentumSpot` failed three criteria: fewer than 4 profitable OOS
folds, negative average OOS Sharpe, and worst OOS drawdown above 10%.
`DonchianBreakoutDailyTop20` failed two criteria: fewer than 4 profitable OOS
folds and worst OOS drawdown above 10%.

Source summaries:

- `user_data/walk_forward_results/sprint25-step3.csv`
- `user_data/walk_forward_results/TimeSeriesMomentumSpot/walk_forward_summary.csv`
- `user_data/walk_forward_results/DonchianBreakoutDailyTop20/walk_forward_summary.csv`

## 26.4 Acceptance Criteria

These criteria were fixed before interpreting the run in
[25. Spot Trend Strategies](25-spot-trend-strategies.md) §25.6.

| Stage | Criterion | Required | Observed | Result |
|---|---|---:|---:|---|
| Step 1 | `WeeklyDonchianBreakoutSpot` trades | >= 30 | 29 | Fail |
| Step 1 | `WeeklyDonchianBreakoutSpot` max DD | < 30.00% | 30.62% | Fail |
| Step 1 | `WeeklyDonchianBreakoutSpot` total profit | > 0.00% | 20.84% | Pass |
| Step 1 | `TimeSeriesMomentumSpot` trades | >= 30 | 102 | Pass |
| Step 1 | `TimeSeriesMomentumSpot` max DD | < 30.00% | 1.90% | Pass |
| Step 1 | `TimeSeriesMomentumSpot` total profit | > 0.00% | 1223.67% | Pass |
| Step 1 | `DonchianBreakoutDailyTop20` trades | >= 30 | 282 | Pass |
| Step 1 | `DonchianBreakoutDailyTop20` max DD | < 30.00% | 28.93% | Pass |
| Step 1 | `DonchianBreakoutDailyTop20` total profit | > 0.00% | 80.66% | Pass |
| Step 3 | `TimeSeriesMomentumSpot` profitable OOS folds | >= 4 | 3 | Fail |
| Step 3 | `TimeSeriesMomentumSpot` avg OOS Sharpe | > 0 | -0.62 | Fail |
| Step 3 | `TimeSeriesMomentumSpot` avg OOS profit | > 0.00% | 6.99% | Pass |
| Step 3 | `TimeSeriesMomentumSpot` worst OOS DD | <= 10.00% | 35.57% | Fail |
| Step 3 | `DonchianBreakoutDailyTop20` profitable OOS folds | >= 4 | 3 | Fail |
| Step 3 | `DonchianBreakoutDailyTop20` avg OOS Sharpe | > 0 | 0.28 | Pass |
| Step 3 | `DonchianBreakoutDailyTop20` avg OOS profit | > 0.00% | 13.63% | Pass |
| Step 3 | `DonchianBreakoutDailyTop20` worst OOS DD | <= 10.00% | 19.20% | Fail |

Both Step 1 survivors failed the Step 3 walk-forward gate. Positive average
OOS profit was not enough to advance because fold consistency and drawdown
control failed.

## 26.5 Decision

Reject Sprint 25.

Do not paper-trade any Sprint 25 strategy. Do not run regime-filter experiments
for Sprint 25 because no strategy passed the Step 3 walk-forward gate. Tasks H,
I, J, and K are therefore not applicable unless the sprint is explicitly
reopened with new acceptance criteria.

This rejection is not a same-window rejection. `TimeSeriesMomentumSpot` and
`DonchianBreakoutDailyTop20` both looked attractive in the full-window screen,
but the walk-forward splits exposed unstable out-of-sample behavior. That is
exactly the failure mode the Sprint 25 gate was meant to catch.

## 26.6 Next Decision

Section 25.8 now applies. Sprint 25 was the last permitted exception to the
post-Sprint-23 rule against more spot-indicator variants. The remaining
registered options are:

- Option A: start a FreqAI or other ML sprint on engineered features.
- Option C: stop the lab here and do not continue searching spot-indicator
  variants.

No further "different angle on indicators" spot sprint should be queued without
explicit escalation.

[Back to docs index](README.md)
