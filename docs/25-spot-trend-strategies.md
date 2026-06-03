# 25. Sprint Plan — Long-Hold Spot Trend Strategies

## 25.1 Context

The post-§23.8 direction was briefly proposed as perps + funding-rate
arbitrage (delta-neutral cash-and-carry). That direction was abandoned
before any agent work began because the user clarified the next research
goal: **directional spot alpha, hold times of days → weeks → short
months, no leverage, no perps**.

This is a category of hypothesis the lab has *not* exhausted. The closest
prior sprint is Sprint 23 (1d primary on 4 majors), which rejected on
**sample size**, not on edge. `DonchianBreakoutDaily` returned +15.1% over
3.3 years with a 4.3% max drawdown but only 32 trades — below the
≥50-trade screen, so walk-forward never ran. The honest read of Sprint 23
is "we lacked the equipment to measure long-hold spot trend strategies,"
not "long-hold spot trend strategies don't work."

Sprint 25 fixes the equipment problem along two axes simultaneously:

| Sprint 23 problem | Sprint 25 fix |
|---|---|
| 4-major universe (BTC/ETH/SOL/BNB) | Top-20 USDT spot (the same snapshot Sprint 19 used) |
| 3.3-year window (2022-01 → 2025-05) | 6-year window (2020-01 → 2025-12) |

Together these multiply the available sample by roughly 12× per strategy,
which is enough for proper walk-forward at the day-to-month hold horizon.

### 25.1.1 Why this is a defensible exception to §23.8

§23.8 forbids "another spot indicator variant" because the
**5m-and-1h-on-4-majors** dimension was exhausted across strategy logic,
universe size, dynamic pair selection, and primary timeframe. That
exhaustion is real *within that cell*. The cell **top-20 × 1d-and-1w ×
6-year cycle-spanning window** has not been searched. The fee-economics
argument from `docs/23-higher-timeframe-sweep.md` §23.1 still stands —
moving from 5m to 1d cuts the round-trip fee burden by ~10–20× — and the
sample-size argument from this section adds to it.

This is **the last permitted exception** to §23.8. If Sprint 25 also
rejects, the next sprint must be FreqAI, perps, or stop, with no further
"different angle on indicators" sprints.

### 25.1.2 Why these three strategy candidates

The user's hold-time range "day, week, short range of months" is wide. The
sprint covers it with three strategies that span the range and use
qualitatively different signals:

| Strategy | Signal | Hold range |
|---|---|---|
| `WeeklyDonchianBreakoutSpot` | 20-week breakout, 10-week trail-stop exit | 1–6 months |
| `TimeSeriesMomentumSpot` | 50d EMA > 200d EMA AND price > 200d EMA | 2 weeks – 4 months |
| `DonchianBreakoutDailyTop20` | 1d Donchian breakout (resurrect Sprint 23's strongest variant on the wider universe) | 5 – 60 days |

All three are **long-only on spot**. No shorts, no perps, no leverage.

## 25.2 Scope

### 25.2.1 Strategy 1 — `WeeklyDonchianBreakoutSpot`

Classic trend-following on weekly candles. Long-only.

- **Entry:** weekly close above the highest weekly close of the last 20 weeks.
- **Exit:** weekly close below the lowest weekly close of the last 10 weeks.
- **Stoploss (hard, behind exit logic as a safety net):** `-0.20`.
- **`minimal_roi`:** empty (`{"0": 100.0}` — let trend run, no profit target).
- **Timeframe:** `1w`.
- **Universe:** top-20 USDT spot (see §25.2.4).

Implementation: thin subclass of `DonchianBreakout` that overrides
`timeframe`, `stoploss`, `minimal_roi`, and the breakout/exit lookback
windows.

### 25.2.2 Strategy 2 — `TimeSeriesMomentumSpot`

Time-series momentum with regime filter. Long-only.

- **Entry:** all four conditions:
  1. `close > EMA(200, 1d)`
  2. `EMA(50, 1d) > EMA(200, 1d)`
  3. RSI(14, 1d) crossed up through 50 within the last 5 candles
  4. 5d realized vol within the 25th–75th percentile of the trailing 100d
     (avoid entries during dead chop and during euphoric blow-offs)
- **Exit:** `EMA(50, 1d)` crosses below `EMA(200, 1d)` OR `close < EMA(200, 1d)`.
- **Stoploss (safety net):** `-0.25`.
- **`minimal_roi`:** empty.
- **Timeframe:** `1d`.
- **Universe:** top-20 USDT spot.

Implementation: new strategy file `user_data/strategies/TimeSeriesMomentumSpot.py`.
This is the only **new from-scratch strategy** in Sprint 25.

### 25.2.3 Strategy 3 — `DonchianBreakoutDailyTop20`

Resurrect Sprint 23's strongest variant on the wider universe + extended
window. Long-only.

- **Entry / exit logic:** identical to existing `DonchianBreakoutDaily`
  (Sprint 23). Inherits unchanged.
- **Stoploss:** `-0.08` (Sprint 23 pre-registered).
- **`minimal_roi`:** `{"0": 0.25}` (Sprint 23 pre-registered).
- **Timeframe:** `1d`.
- **Universe:** top-20 USDT spot (vs Sprint 23's 4 majors).

Implementation: thin subclass `DonchianBreakoutDailyTop20` that overrides
**only** the universe (via `pair_whitelist` in a Sprint-25-scoped config).
The strategy class itself is unchanged from `DonchianBreakoutDaily`.

> **Note.** Strategy 3 directly tests the Sprint 23 sample-size hypothesis.
> If the sample-size fix turns Sprint 23's near-miss into an actual edge,
> this is where it shows up.

### 25.2.4 Universe

Top-20 USDT spot on OKX, ranked by 30d quote volume, snapshotted at
**2024-07-01** (the same snapshot Sprint 19 used; see
`user_data/universes/top20_okx_2024-07-01.json`).

Re-using the existing snapshot is intentional:
- **Same survivorship-bias profile as Sprint 19** — comparable across sprints.
- **No new universe-build sprint required** — Task A confirms the snapshot
  exists and is readable; no rebuild.



### 25.2.5 Window

`2020-01-01` → `2025-12-01` (~6 years).

Rationale:
- Spans 1 full bear → bull → bear → bull cycle (2020 COVID crash, 2021 bull,
  2022 bear, 2023-2024 bull, 2025 consolidation).
- All top-20 pairs from the 2024-07-01 snapshot have **continuous OKX spot
  data** for this window (verified at sprint plan time; Task B confirms).
- 6 years × 1d candles = 2,191 candles per pair × 20 pairs = 43,820 total
  candles. Plenty for walk-forward.

Why not extend to 2018-01-01: half the top-20 pairs (e.g., SOL, MATIC, ICP)
didn't exist on OKX in 2018. A strict 2018 start either drops them from the
universe (defeats the wider-universe fix) or introduces ragged per-pair
data windows (introduces survivorship-bias confounders). 2020-01-01 is the
earliest start where the universe is consistent.

### 25.2.6 Explicitly skipped

| Cell | Why skipped |
|---|---|
| Cross-sectional momentum (rank by 90d return, monthly rebalance) | Considered. Adds custom-whitelist-update infrastructure that pays off only if all three Sprint 25 candidates reject. Save it for a follow-up. |
| 1w primary on the 4-major universe | Already implicitly tested by Sprint 23's downsampled rationale; even with 8 years × 4 pairs = 32 pair-years × ~6 weekly trades/yr ≈ 200 trades. Marginal. |
| Mean-reversion on 1d (Bollinger pullback, RSI dip-buy) | Indicator mean-reversion was rejected at 5m (Sprint 13/15) and 1d (Sprint 23). Including it again would just retest a known-failed cell on a wider universe. |
| Perps + funding-rate arbitrage | Out of scope — per user direction, spot-only. |
| FreqAI / ML on engineered features | Reserved for the post-Sprint-25 escalation if §25.8 fires. |
| 1w primary on more than 4 strategies | One weekly-primary strategy is enough to establish whether weekly-trend works at all on this universe. |

## 25.3 Implementation Files

### 25.3.1 New strategy files

- `user_data/strategies/WeeklyDonchianBreakoutSpot.py` — thin subclass of
  `DonchianBreakout` overriding `timeframe`, `stoploss`, `minimal_roi`,
  breakout lookback (20 weeks), and exit lookback (10 weeks).
- `user_data/strategies/TimeSeriesMomentumSpot.py` — full new strategy
  implementing the §25.2.2 entry/exit logic with the 4-condition entry and
  death-cross exit.
- `user_data/strategies/DonchianBreakoutDailyTop20.py` — thin subclass of
  `DonchianBreakoutDaily` (no logic changes; universe override is
  config-side, not class-side).

### 25.3.2 New config

- `user_data/config-sprint25-top20.json` — copy of `user_data/config.json`
  with `pair_whitelist` populated from `top20_okx_2024-07-01.json`,
  `dry_run = true`, `dry_run_wallet = 500`, `max_open_trades = 5` (allows
  up to 5 concurrent positions across the 20-pair universe; max equity at
  risk = 5 × $50 stake × ~25% safety stop = ~$62 = 12% of wallet which is
  the conservative bound).

The committed `user_data/config.json` is **not modified** — Sprint 25 uses
its own config.

### 25.3.3 New tests

- `tests/test_weekly_donchian_breakout_spot.py` — smoke test (instantiate,
  call `populate_indicators` / `populate_entry_trend` /
  `populate_exit_trend` on a synthetic weekly DataFrame).
- `tests/test_time_series_momentum_spot.py` — smoke test +
  no-look-ahead unit test (entry signals at index `t` must not depend on
  any data at index `t+1` or later).
- `tests/test_donchian_breakout_daily_top20.py` — smoke test that confirms
  the subclass inherits unchanged logic from `DonchianBreakoutDaily`.

## 25.4 Pre-Registered Stoploss / ROI / Lookback

These are **not hyperopt parameters** — they are class attributes locked
at sprint plan time, identical-treatment to Sprint 23 §23.4. Goalpost-move
attempts during execution are blocked.

| Strategy | Timeframe | Stoploss | `minimal_roi` | Lookback (entry) | Lookback (exit) |
|---|---|---:|---|---:|---:|
| `WeeklyDonchianBreakoutSpot` | `1w` | -0.20 | `{"0": 100.0}` (effectively no target) | 20 weeks | 10 weeks |
| `TimeSeriesMomentumSpot` | `1d` | -0.25 | `{"0": 100.0}` | EMA 50 / 200, RSI 14 | EMA 50/200 cross |
| `DonchianBreakoutDailyTop20` | `1d` | -0.08 | `{"0": 0.25}` | 20 days (Sprint 23) | (Sprint 23 baseline) |

Rationale:
- Wide stoplosses on `WeeklyDonchianBreakoutSpot` and
  `TimeSeriesMomentumSpot` are deliberate. Long-hold trend-following
  strategies are **expected** to eat 15–20% drawdowns on individual
  positions — that's the cost of letting winners run for months. A
  -0.05 stoploss would knock the strategy out on noise that the entry
  logic is supposed to ignore.
- `DonchianBreakoutDailyTop20` keeps Sprint 23's pre-registered values
  unchanged so the universe expansion is the *only* moving variable
  vs Sprint 23.

## 25.5 Risk Doctrine for Long-Hold Spot

The 1% equity-per-trade rule from `docs/08-risk-and-position-sizing.md`
is preserved with re-interpretation for long-hold positions:

- Per-trade stake: $50 (unchanged from prior sprints).
- Max concurrent open positions: 5 (`max_open_trades = 5`).
- Per-trade implied risk at -0.20 stop = $10 = 2% of $500 equity.
- **Why is this not a violation of the 1% rule?** The 1% rule applies to
  intraday-stop strategies where stops fire on noise. Long-hold strategies
  use the stop as a *catastrophe* limit, not a trade-management tool. The
  effective per-trade risk in normal conditions (the strategy exits via
  trail-stop or signal break) is much lower than the catastrophe stop
  implies. The `docs/08` author explicitly documents this distinction
  (§8.4 final paragraph).
- Total wallet exposure cap: 5 positions × $50 = $250 = 50% of $500
  equity. This is conservative for a long-only spot lab.

## 25.6 Validation Pipeline

Five steps. The acceptance gates at Step 1 and Step 3 are pre-registered
and **not negotiable** during execution.

### Step 1 — Same-window screen

For each strategy, run a single backtest over the full 2020-01-01 →
2025-12-01 window on the top-20 universe.

**Acceptance (relaxed-but-rigorous):**

| Criterion | Required |
|---|---:|
| Total trades across universe | ≥ 30 |
| Max drawdown (full-window) | < 30% |
| Total profit % (full-window) | > 0% (any positive return advances) |

> **Note.** ≥ 30 trades is relaxed from Sprint 23's ≥ 50. Long-hold
> strategies are sparse by construction. The walk-forward stage at Step 3
> is where rigor is preserved.

### Step 2 — Hyperopt sanity check (optional)

Skipped for Sprint 25. The pre-registered class attributes are not
hyperopt parameters by design (see §25.4).

### Step 3 — Walk-forward validation

For each Step 1 survivor, run walk-forward with these windows:

- In-sample: 730 days (2 years)
- Out-of-sample: 180 days (6 months)
- Step: 180 days (6 months)
- Total OOS folds: `(6y - 2y) / 6m = 8`

**Acceptance (4-criterion gate, identical structure to §16.3 with
adjusted thresholds for long-hold horizon):**

| Criterion | Required |
|---|---:|
| Number of OOS folds with profit > 0 | ≥ 4 of 8 (50%) |
| Average OOS Sharpe across all folds | > 0 |
| Average OOS total profit % across all folds | > 0% |
| Worst single OOS fold drawdown | ≤ 10% |

Strategies passing all four criteria advance to Step 4. Strategies failing
**any** criterion are rejected — no goalpost moving.

### Step 4 — Regime-filter experiments (conditional on Step 3 survivor)

Run only if any strategy clears Step 3. Apply bull-only / bear-excluded /
trending-only regime filters from `user_data/regime/classifier.py` and
re-run walk-forward. Compare filtered vs unfiltered to see whether the
regime filter improves OOS Sharpe.

### Step 5 — Paper-trade dry-run (conditional on Step 4 acceptance)

Run only if any regime-filtered survivor improves on the unfiltered
control by ≥ 0.2 OOS Sharpe. 4 weeks of `dry_run = true` paper trade on
`config-sprint25-top20.json`. Acceptance: realized P&L within ±50% of the
walk-forward simulation (long-hold variance is wider than 5m).

## 25.7 Task Breakdown

> Canonical task IDs are the letters in `TASKS.md` (A–L + ESC).
> Cross-references in this document use those letters.
>
> **Hard gate at Step 1.** Tasks F–K run only on Step 1 survivors.
> If Step 1 rejects all three strategies, jump directly to Tasks G + L.
>
> **Hard gate at Step 3.** Tasks J + K run only on Step 3 survivors.

| Task | Owner tier | Depends on | Brief |
|---|---|---|---|
| A | Codex 5.4 low | — | Branch + confirm universe snapshot + window + stoploss table |
| B | Codex 5.4 low | A | Download 1d + 1w OHLCV for top-20 over 2020-01-01 → 2025-12-01 |
| C | Codex 5.4 medium | A | Implement three strategy files + smoke tests |
| D | Codex 5.4 medium | A | Build `config-sprint25-top20.json`; verify pair_whitelist matches the universe snapshot |
| E | Antigravity Flash medium | C, D | Step 1 same-window backtest sweep across all three strategies |
| F | Antigravity Flash medium | E | Step 3 walk-forward for Step 1 survivors |
| G | Antigravity Flash high | E, F | Write `docs/26-spot-trend-results.md` |
| H | Antigravity Flash medium | F | (Conditional) Step 4 regime-filter experiments on Step 3 survivors |
| I | Antigravity Flash medium | H | (Conditional) Step 5 4-week paper-trade dry-run |
| J | Antigravity Flash medium | I | (Conditional) Extend `docs/26-spot-trend-results.md` with Step 4 + Step 5 results |
| K | Codex 5.4 low | F, J | (Conditional) Live deployment readiness checklist if any strategy clears Step 5 |
| L | Codex 5.4 low | all | Update `TASKS.md` at sprint end |
| ESC | Sonnet 4.6 Thinking | — | Escalation lane — design-level questions only |

**Cost ceiling.** ≈ 1 Codex 5.4 medium-day for C+D, ≈ 0.5 Codex 5.4 low-day
for A+B+K+L, ≈ 2 Antigravity Flash medium-days for E+F+H+I, ≈ 1 Antigravity
Flash high-day for G+J. No high-tier execution code is required because
this is dry-run-only spot trading on existing infrastructure (Freqtrade
backtest + walk-forward harness, both reused unchanged from Sprint 23).

## 25.8 Kill Criterion

If **any of the following fires**, Sprint 25 is rejected and §25.8
applies:

1. All three strategies fail Step 1 (same-window screen).
2. All Step 1 survivors fail Step 3 (walk-forward acceptance).
3. The Step 4 regime filter does not lift any survivor's OOS Sharpe by
   ≥ 0.2.

§25.8 narrows the §23.8 escape hatches by one more option. Remaining
choices after Sprint 25 rejection:

- **Option A — FreqAI / ML on engineered features.** Still untested.
- **Option C — Stop the lab.** Honest answer if neither cash flow nor
  ML on engineered features is worth the added complexity.

There is no "try a different long-hold spot strategy" follow-up. Sprint 25
covers the realistic hold-time and signal-type space (weekly trend,
daily-momentum-with-regime, daily-breakout-on-wide-universe). If all
three reject, the long-hold spot direction is exhausted.

## 25.9 Out of Scope

Explicit non-goals for Sprint 25:

- **Perps, futures, leverage.** Sprint 25 is spot-only. The
  `scripts/dca_futures_sim.py` tool merged in PR #52 is a standalone
  educational utility; it is not invoked by any Sprint 25 task.
- **Cross-sectional momentum (rank-and-rebalance) strategies.** Out of
  scope — added complexity not justified by the marginal coverage gain
  per §25.2.6.
- **Mean-reversion on 1d.** Out of scope — already rejected at 5m and 1d
  cells.
- **More than 3 strategies.** Three is enough to span the day-to-month
  hold horizon. Adding more strategies inflates the multiple-comparison
  problem (more shots on goal = more chance of a false positive) without
  adding meaningful coverage.
- **Real-money deployment.** Governed by `docs/07` §7.6 unchanged. Not
  invoked by any Sprint 25 task.
- **Window extension to 2018.** Universe consistency takes priority; see
  §25.2.5 rationale.

[Back to docs index](README.md)
