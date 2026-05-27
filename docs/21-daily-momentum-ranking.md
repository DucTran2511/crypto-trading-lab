# 21. Sprint Plan — Daily Momentum Ranking (top-3 of top-20 universe)

## 21.1 Context

Nine strategies have now been rejected by the established validation pipeline:

| Strategy | Timeframe | Universe | Outcome |
|---|---|---|---|
| `EMACrossover` | 5m | 4 majors | Same-window control only (-20.8%) |
| `DonchianBreakout` | 5m | 4 majors | Same-window control only (-28.3%) |
| `MACDVolume` | 5m | 4 majors | Same-window control only (-49.3%) |
| `BollingerMeanReversion` | 5m | 4 majors | Passed screen, failed OOS |
| `RSITrend` | 5m | 4 majors | Passed screen, failed OOS |
| `RSITrendBullOnly` | 5m | 4 majors | Best regime variant, failed 3-fold OOS |
| `MultiTimeframeTrend` | 1h | 4 majors | Passed screen, 7-fold OOS Sharpe +0.20 but avg profit -0.03% |
| `ATRAdaptiveMeanReversion` | 1h | 4 majors | Passed screen, 7-fold OOS Sharpe -16.09 |
| `RSITrend` | 5m | top-20 USDT spot | Passed screen, 7-fold OOS Sharpe -30.77, avg OOS profit -0.17% |

See `docs/14`, `docs/16`, `docs/18`, `docs/20` for the full result history.

**Key observation.** The strategy space (indicator combinations), the
timeframe space (5m and 1h), and the universe-by-volume space (4 majors and
top-20 by quote volume) have all been searched. Every test so far has used
**static pair selection**: pick a universe up front, run the same strategy on
every pair in it, every candle.

The one dimension that has *not* been tested is **dynamic pair selection by
signal**. Crypto markets are highly cross-correlated; on any given day, a few
names lead and most lag. A strategy that trades every pair indiscriminately
pays fees on the laggards to capture a small fraction of the leader move. A
strategy that *picks* the leaders each day before applying its entry logic
might have meaningfully different per-trade economics, even with identical
indicators.

This sprint adds a daily momentum-ranking step in front of the existing
baseline strategies. The universe stays the top-20 from Sprint 19; the
strategies stay the existing 5m baselines unchanged. Only the **entry-eligible
subset** changes — and it changes every UTC day.

This is the registered `docs/19-pair-universe-expansion.md` §19.8 follow-up
*before* declaring the indicator-on-spot research thread dead and escalating
to FreqAI or perps + funding-rate arbitrage. If this sprint also rejects, the
indicator-on-OKX-spot research direction has been exhaustively tested and
should be retired in favour of one of those structurally different
approaches.

## 21.2 Ranking Methodology

### 21.2.1 Signal

For each UTC day `D`, rank the top-20 universe by **trailing 1-day return**
computed from the close of day `D-2` to the close of day `D-1`. The ranking
is then applied to candles in day `D` (00:00 UTC through 23:59 UTC).

Rationale:

- **1-day lookback** is short enough that yesterday's leader is plausibly
  still in motion today (momentum is a real intraday phenomenon in crypto)
  but long enough that a single noisy candle cannot dominate.
- Longer lookbacks (3d, 7d) are explicitly out of scope for this sprint —
  they introduce another tunable parameter and a different hypothesis
  (multi-day continuation vs day-to-day momentum). If 1d fails, the
  registered follow-up is FreqAI, **not** "try 3d and 7d" — that would be
  hyperopting on the hypothesis, which is the same trap as adding more
  indicators.
- **Close-to-close** is used rather than open-to-open to match the candle
  data we already have downloaded.

### 21.2.2 Top-N selection

For each UTC day, the **top-3** ranked pairs are entry-eligible. The other 17
pairs are not entry-eligible that day (open positions from prior days can
still exit normally).

Why 3 and not 5 or 1:

- `max_open_trades = 2` (from `user_data/config.json`, Sprint 17 Option A
  decision). Top-3 gives the strategy one bench pair in case two are already
  open — Freqtrade can then enter the third leader rather than skipping the
  candle.
- Top-1 would be too concentrated; a single laggard ranking would block the
  strategy for the day even when alternates exist.
- Top-5 dilutes the selection effect — at top-5 of 20, 25% of the universe
  is eligible every day, which is approaching the static-universe regime.

### 21.2.3 Date boundaries

The ranking for day `D` is computed from candles closed by `D-1 23:59 UTC` and
becomes effective at `D 00:00 UTC`. **There is no look-ahead.** Any candle
inside day `D` (e.g. `D 13:35 UTC`) uses the ranking computed at `D 00:00`,
not a ranking that includes any of `D`'s own data.

The ranking helper exposed in Task C must enforce this: when asked
"is pair `P` in today's top-3 for date `D`?", it looks up the entry indexed by
date `D` in the ranking JSON, which was computed from data ending at
`D-1 23:59 UTC`.

## 21.3 Implementation

The implementation is intentionally **thin**. The existing baseline strategies
are not modified. Instead:

1. `scripts/rank_pairs_by_momentum.py` (Task B): produces a per-day ranking
   JSON for a date range, using local OKX 1d OHLCV.
2. `user_data/selection/daily_momentum.py` (Task C): a small helper that loads
   the ranking JSON once per strategy instance and exposes
   `is_pair_in_today_top_n(pair, date, n)`.
3. `user_data/strategies/<Name>DailyRanked.py` (Task C): one thin subclass per
   existing baseline. Each subclass overrides `populate_entry_trend` to
   AND-gate the original entry signal with `is_pair_in_today_top_n`. No
   indicator logic, no stoploss, no ROI, no `informative_pairs` changes.

This factoring ensures:

- Backtests of `EMACrossover` and `EMACrossoverDailyRanked` on the same data
  and time range produce comparable results — any difference is *only* due to
  the ranking gate.
- If the gate hurts performance, the unranked baseline is the obvious
  control to fall back on.
- No baseline strategy is mutated, so Sprint 19's results remain reproducible
  bit-for-bit.

> **Note.** Freqtrade's pairlist plugin system is an alternative way to
> implement dynamic pair selection. It is **not** used here because (a) it
> requires either a custom plugin or a config-level filter that re-evaluates
> every candle, both of which are heavier than the strategy-level gate, and
> (b) the strategy-level gate is the most direct mapping to the hypothesis
> "an existing baseline strategy plus a daily filter."

## 21.4 Configuration

No `user_data/config.json` changes are required for this sprint. The
`pair_whitelist` already contains the top-20 from Sprint 19, which is the
exact universe being ranked.

`max_open_trades` stays at 2 (Sprint 17 Option A). Stake amount stays at $50.

## 21.5 Backtest Window

`2024-07-01` → `2025-05-01`, same as Sprint 19. Same per-pair 5m data already
on disk (top-20 was downloaded in Sprint 19 Task D). One additional dataset
is required: **1-day OKX candles for the same 20 pairs and date range**, used
only by `scripts/rank_pairs_by_momentum.py`. This is downloaded as part of
Task B (the script can either call `freqtrade download-data` itself or fail
with a clear error if the data is missing).

## 21.6 Validation Pipeline

The same four-criterion gate from `docs/16` §16.3 applies, unchanged. No
goalpost moving:

### Step 1 — Same-window screen

Run `scripts/run_baselines.py` on the five `*DailyRanked` strategies over
`--timerange=20250101-20250501`. A strategy advances iff:

- **≥ 50 trades** in the window (same bar raised in Sprint 19), AND
- **Max drawdown < 30%**.

The trade-count screen is meaningful here because the daily-rank gate is
expected to *reduce* trade count by roughly `3/20 = 15%` of baseline — but no
more than that. A strategy whose baseline produced 339 trades (e.g.
`RSITrend`) should produce ~50 ranked trades. A strategy whose baseline
produced 14 trades (e.g. `BollingerMeanReversion`) will not pass this screen
under the daily rank, and that result is informative — it means the
combination of low-frequency entry + dynamic selection has insufficient
exposure to be evaluated.

### Step 2 — Walk-forward validation

For each Step 1 survivor, run `scripts/walk_forward.py` with the same
90d/30d/30d windows over 2024-07-01 → 2025-05-01.

### Step 3 — Acceptance (all four must pass)

1. **≥ 3 completed OOS folds** (a strategy that hyperopt cannot fit on
   in-sample data is rejected).
2. **Average OOS Sharpe > 0** (positive risk-adjusted return out of sample).
3. **Average OOS total profit % > 0** (positive expectancy net of fees).
4. **No single OOS fold drawdown > 5%** (tail-risk bounded).

These are pre-registered. They do not change between sprints. A strategy that
fails any one criterion is rejected and may not be paper-traded.

### Step 4 — Regime filter experiments (Task I)

Only for Step 3 survivors. Run `scripts/regime_filter_experiments.py` to test
whether bull-only or trending-only sub-variants improve OOS results.

### Step 5 — 4-week paper-trade dry-run (Task J)

Only for Step 3 survivors (with or without a regime filter). Mandatory
prerequisite before any live capital is considered. Tracked per-week, trade
count and win rate must remain within 30% of backtest expectation.

### Step 6 — Live deployment

**Out of scope for this sprint.** Even if Step 5 passes, going live is a
separate sprint-level decision and is gated on `docs/07-paper-and-live-trading.md`
§7.6.

## 21.7 Task Breakdown

> Canonical task IDs are the letters in `TASKS.md` (A–K + ESC). Cross-references
> in this document use those letters. The table below is a summary; consult
> `TASKS.md` for full per-task acceptance criteria.

| Task | Owner tier | Depends on | Brief |
|---|---|---|---|
| A | Codex 5.4 low | — | Branch + confirm 1d ranking lookback |
| B | Codex 5.4 medium | A | `scripts/rank_pairs_by_momentum.py` + tests |
| C | Codex 5.4 medium | A | `daily_momentum.py` helper + 5 `*DailyRanked` strategy subclasses |
| D | Codex 5.4 low | B, C | Smoke tests for helper and ranked strategies |
| E | Codex 5.4 low | B | Generate and commit the ranking JSON for the backtest window |
| F | Antigravity Flash medium | C, D, E | Same-window baseline backtests for ranked variants |
| G | Antigravity Flash medium | F | Walk-forward validation for Step 1 survivors |
| H | Antigravity Flash high | G | Write `docs/22-daily-momentum-results.md` |
| I | Antigravity Flash medium | G | Regime-filter experiments (only for Step 3 survivors) |
| J | Antigravity Flash medium | H | 4-week paper-trade dry-run (only for Step 3 survivors) |
| K | Codex 5.4 low | all | Update `TASKS.md` at sprint end |
| ESC | Sonnet 4.6 Thinking | — | Escalation lane — design-level questions only |

**Cost ceiling.** ≈1 Codex 5.4 medium-day for B+C, ≈0.5 Codex 5.4 low-day for
A+D+E+K, ≈2 Antigravity Flash medium-days for F+G+I+J, ≈0.5 Antigravity Flash
high-day for H. No Opus, no Codex 5.5 high+, no Devin in the default path.

## 21.8 Kill Criterion

If **zero strategies pass Step 3 walk-forward acceptance**, the
indicator-on-OKX-spot research direction has been exhaustively tested across:

- 5 baseline indicator strategies + 1 regime-filtered variant
- 2 timeframes (5m, 1h)
- 2 static universes (4 majors, top-20)
- 1 dynamic universe (top-3 of top-20, by daily momentum)

At that point, do **not** add another indicator, another timeframe, or another
lookback period for the ranking signal. Those are all variants of the same
hypothesis. The next sprint must instead address a structurally different
direction:

- **Option A — FreqAI.** Use Freqtrade's built-in ML module. Feed 30+
  engineered features (BTC dominance, volatility regime, RSI/EMA stack,
  volume profile, candle patterns, time-of-day) and train an LGBM
  classifier on per-bar return targets. Walk-forward retraining. Higher
  over-fit risk; higher information density per sprint.
- **Option B — Perps + funding-rate arbitrage.** Cash-and-carry: long spot
  + short perp when funding is positive. Structural cash flow, not
  directional alpha. Requires opening a perps account on OKX or Binance
  and adding a paired-leg position manager. Lowest sprint cost; highest
  probability of finding *some* survivable edge (because the edge is a
  paid cash flow, not a discovered pattern).

The branching decision between A and B is reserved for the ESC lane after
this sprint closes. Both are roughly the same effort; the deciding factor is
whether you have (or can quickly create) a perps account.

## 21.9 Out of Scope

These are deferred to future sprints:

- **Hyperopt over the lookback period or top-N.** The 1d lookback and top-3
  are fixed up front by design. Tuning them is the same hypothesis-erosion
  trap that "try another indicator" is.
- **Volatility-adjusted ranking.** A simple `return / std` ranking would be a
  cleaner signal but adds an indicator-engineering subproblem to a sprint
  that's already testing one hypothesis.
- **Multi-day ranking (3d, 7d).** Different hypothesis — multi-day
  continuation vs day-to-day leadership. Reserve for a future sprint *only
  if* this one produces a survivor and the question becomes "can we tune the
  lookback to improve OOS?"
- **Cross-exchange ranking.** OKX spot only.

[Back to docs index](README.md)
