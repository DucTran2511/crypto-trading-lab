# 23. Sprint Plan — Higher-Timeframe Sweep (1d primary, MTF combo conditional)

## 23.1 Context

Fourteen strategy variants have now been rejected:

| Strategy | Primary TF | Informative TF | Universe | Outcome |
|---|---|---|---|---|
| `EMACrossover` | 5m | — | 4 majors | Same-window control only |
| `DonchianBreakout` | 5m | — | 4 majors | Same-window control only |
| `MACDVolume` | 5m | — | 4 majors | Same-window control only |
| `BollingerMeanReversion` | 5m | — | 4 majors | Passed screen, failed OOS |
| `RSITrend` | 5m | — | 4 majors | Passed screen, failed OOS |
| `RSITrendBullOnly` | 5m | — | 4 majors | Failed 3-fold OOS |
| `MultiTimeframeTrend` | **1h** | **4h** | 4 majors | OOS Sharpe +0.20, profit -0.03% |
| `ATRAdaptiveMeanReversion` | **1h** | — | 4 majors | OOS Sharpe -16.09 |
| `RSITrend` | 5m | — | top-20 USDT spot | OOS Sharpe -30.77 |
| 5× `*DailyRanked` baselines | 5m | 1d (as ranking signal only) | top-20 | 3 passed screen, all 3 failed OOS |

See `docs/14`, `docs/16`, `docs/18`, `docs/20`, `docs/22` for the full result
history.

**Why this sprint is not a §21.8 kill-criterion violation.** The Sprint 21
kill criterion explicitly disallows adding "another spot indicator, timeframe,
or ranking lookback" as the next step. The intent was to block more
hyperopting on the same exhausted hypothesis. This sprint is a defensible
exception because the variable being changed — **trading timeframe** — is
categorically different from the variables searched so far, for a specific
quantitative reason:

| Primary TF | Typical trades / yr (4 pairs) | Round-trip fee burden (0.16%) | Strategy needs gross > |
|---|---:|---:|---:|
| 5m | 300 – 1,200 | 48% – 192% of capital | impossible-to-feasible |
| 1h | 100 – 300 | 16% – 48% | hard |
| 4h | 30 – 100 | 4.8% – 16% | plausible |
| **1d** | **10 – 50** | **1.6% – 8%** | **well within reach** |
| 1w | 3 – 15 | 0.5% – 2.4% | trivial, but sample size dies |

Every rejection so far has been on a timeframe where fees alone require a
double-digit gross win rate just to break even. Moving from 5m to 1d cuts
that burden by ~10–20×. **Same indicators, same logic, structurally different
friction.** This is a categorical change, not "another variant," and is the
last untested cell in the (strategy, timeframe, universe, selection) grid
before the indicator-on-OKX-spot direction is fully exhausted.

If this sprint also produces zero survivors, §23.8 reaffirms the kill
criterion with one fewer escape hatch.

## 23.2 Scope and Tiering

This sprint is intentionally **two-tier with a hard gate between tiers** to
avoid sunk-cost compounding. Tier 2 only runs if Tier 1 produces ≥1 Step 3
survivor.

### 23.2.1 Tier 1 — 1d primary on 4 majors

The highest-EV untested cell in the grid.

- **Universe:** BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT — the original 4
  majors, **not** the top-20. Reasoning: 1d candles produce ~30 trades/yr/pair
  even with permissive filters; widening to 20 pairs is unnecessary at this
  sample size and reintroduces the universe-by-volume variable Sprint 19
  already ruled out as the bottleneck.
- **Strategies:** all 5 existing baselines (`EMACrossover`,
  `DonchianBreakout`, `BollingerMeanReversion`, `RSITrend`, `MACDVolume`),
  unchanged except for `timeframe = "1d"` and a re-derived stoploss
  appropriate for 1d candles (see §23.4).
- **Backtest window:** `2022-01-01` → `2025-05-01` (3 years, 4 months). The
  window is extended back to 2022 specifically to produce enough samples for
  the ≥ 50-trade screen on a 1d timeframe.
- **Validation:** the same 4-criterion gate from `docs/16` §16.3, unchanged.

### 23.2.2 Tier 2 — MTF combination (conditional)

**Run only if Tier 1 produces ≥1 Step 3 survivor.** If Tier 1 produces zero
survivors, Tier 2 is skipped and §23.8 fires.

- **Single new strategy:** `MultiTimeframeConfirmation`.
- **Logic:** `1w EMA-200 slope > 0` (trend regime) AND the best Tier 1
  survivor's 1d entry signal AND `4h RSI(14) < 70` (overbought filter).
- **Universe:** same 4 majors.
- **Backtest window:** same 2022-01-01 → 2025-05-01.
- **Validation:** same 4-criterion gate.

### 23.2.3 Explicitly skipped

| Cell | Why skipped |
|---|---|
| 4h primary as a standalone sweep | Sits between rejected 1h and proposed 1d. Fee economics improve but not categorically. If 1d rejects, 4h almost certainly does too; if 1d survives, 4h is a noisier subset. |
| 1w primary as a standalone sweep | 3.3 years × 4 pairs ≈ 700 weekly candles total. Realistic trade count per strategy < 30, fails the ≥ 50 screen mechanically. Better used as a *trend filter* in Tier 2. |
| Top-20 universe on 1d/4h | Sprint 19 already showed the universe is not the bottleneck. Reintroducing it confounds the timeframe variable. |
| 1d ranking + 1d primary together | The Sprint 21 ranking machinery is designed around 5m candles inside a daily window. Combining it with 1d primary trading would mean ranking → choose 3 pairs → trade them at 1d, which collapses to "trade fewer pairs," not a meaningfully different gate. |

## 23.3 Implementation

The implementation is intentionally **thin**, like Sprint 21. No new
infrastructure is required; the existing harness handles everything.

### 23.3.1 Strategy subclasses (Task C)

Five thin subclasses, one per baseline:

- `user_data/strategies/EMACrossoverDaily.py`
- `user_data/strategies/DonchianBreakoutDaily.py`
- `user_data/strategies/BollingerMeanReversionDaily.py`
- `user_data/strategies/RSITrendDaily.py`
- `user_data/strategies/MACDVolumeDaily.py`

Each subclass:

1. Inherits from the corresponding base strategy.
2. Overrides `timeframe = "1d"`.
3. Overrides `stoploss = -0.10` (or per-strategy as in §23.4).
4. Overrides `minimal_roi` to `{"0": 0.20}` — 20% TP, scaled to daily
   volatility.
5. Does **not** touch `populate_indicators`, `populate_entry_trend`, or
   `populate_exit_trend`. Same entry/exit logic as the parent. **The only
   variable changing is the candle size.**

Same hyperopt-safe `.range` indicator caching pattern; no new parameter
ranges introduced. If the parent class hyperopts an `ema_fast` from 5 to 50
candles, that range is reused unchanged — but those 5–50 candles are now days
instead of 5-minute bars.

### 23.3.2 MTF combination strategy (Task H, conditional)

`user_data/strategies/MultiTimeframeConfirmation.py`:

- `timeframe = "1d"` (primary)
- `informative_pairs()` returns `[(pair, "4h"), (pair, "1w")]` per active pair
- Indicator: 1w EMA-200 slope (forward-fill into 1d using
  `merge_informative_pair`)
- Indicator: 4h RSI(14) (forward-fill into 1d using `merge_informative_pair`)
- Entry: `(1w_ema200_slope > 0) & (parent_entry_signal == 1) & (4h_rsi < 70)`
- Exit: parent strategy's exit, unchanged
- `startup_candle_count` ≥ `200 * 7 = 1400` daily candles (≈ 4 years) — this
  is why the 2022-01-01 backtest window matters; otherwise the 1w EMA-200
  hasn't warmed up by the backtest start.

> **Note.** Freqtrade's `informative_pairs` semantics: the 4h and 1w candles
> are looked up by their **closed** timestamp, then forward-filled to the 1d
> primary candle's timestamp. No look-ahead is possible if `merge_informative_pair`
> is used per the Freqtrade docs (which sets `ffill=True`). The smoke test in
> Task H must verify the merge is using closed candles only.

## 23.4 Per-Strategy Stoploss and ROI (1d)

The 5m baselines use `stoploss = -0.03` because 5m intra-candle range is
small. On 1d candles, a -3% stop is inside one day's normal price range and
will be triggered by intraday noise even when the daily trend is intact.
Per-strategy stops on 1d:

| Strategy | 1d Stoploss | 1d minimal_roi | Rationale |
|---|---:|---|---|
| `EMACrossoverDaily` | -0.10 | `{"0": 0.20}` | Trend-following; gives ~3% room below entry on average daily range |
| `DonchianBreakoutDaily` | -0.08 | `{"0": 0.25}` | Breakout; tighter stop OK because breakout typically continues or fails fast |
| `BollingerMeanReversionDaily` | -0.06 | `{"0": 0.08}` | Mean-reversion; tight stop, modest TP, expects fast reversion |
| `RSITrendDaily` | -0.10 | `{"0": 0.20}` | Trend-following pullback |
| `MACDVolumeDaily` | -0.10 | `{"0": 0.20}` | Trend-following |

These numbers are pre-registered. They are **not** hyperopt parameters; they
are class attributes. Hyperopting the stop would re-introduce the same
goalpost-moving trap §21.8 rejected.

## 23.5 Configuration

No `user_data/config.json` changes are required for this sprint. The
`pair_whitelist` already contains the 4 majors and 16 top-20 pairs; the
Tier 1 backtests use `--pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT` directly.

`max_open_trades` stays at 2. Stake stays at $50. Risk doctrine unchanged:
2 × $50 × 10% strategy stop = $10 peak open risk on $500 wallet ≈ 2% of
equity — a one-step relaxation from the 5m-era 1% target because 1d stops
must be wider.

## 23.6 Validation Pipeline

Identical to `docs/16` §16.3. No goalpost moving.

### Step 1 — Same-window screen

Run `scripts/run_baselines.py` on the five `*Daily` strategies over
`--timerange=20220101-20250501`.

- **≥ 50 trades** in the window across the 4 majors, AND
- **Max drawdown < 30%**.

> **Note.** The trade-count screen is meaningful here precisely because 1d
> candles produce few trades. A strategy that fails the ≥ 50 screen on a
> 3+ year window is producing < 1 trade/month per pair, which is too sparse
> for any walk-forward conclusion. This is *not* a relaxation of the gate —
> it's the same gate the 5m strategies had to clear.

### Step 2 — Walk-forward validation

For each Step 1 survivor: `scripts/walk_forward.py` with **365d in-sample,
90d out-of-sample, 90d step** over 2022-01-01 → 2025-05-01.

> **Window-size rationale.** The 90d/30d/30d windows used in 5m and 1h
> sprints assume hundreds of trades per fold. On 1d candles those windows
> are too short (a 30d out-of-sample fold has ~30 daily candles, ~3 trades
> per strategy per pair). 365d/90d/90d is the 1d-appropriate analogue,
> producing ~11 folds with ~90 daily candles per OOS fold — comparable
> *sample size* per fold to the 5m sprints. The acceptance criteria are
> unchanged.

### Step 3 — Acceptance (all four must pass)

1. **≥ 3 completed OOS folds.**
2. **Average OOS Sharpe > 0.**
3. **Average OOS total profit % > 0.**
4. **No single OOS fold drawdown > 5%.**

Pre-registered. A strategy that fails any one criterion is rejected and may
not be paper-traded.

### Step 4 — Tier 2 MTF combination (Task I, conditional)

Only runs if Step 3 produces ≥ 1 survivor. Same 4-criterion gate applied to
`MultiTimeframeConfirmation` over the same windows.

### Step 5 — Regime filter experiments (Task J, conditional)

Only for Step 3 / Step 4 survivors. Same `scripts/regime_filter_experiments.py`
as prior sprints.

### Step 6 — 4-week paper-trade dry-run (Task K, conditional)

Only for Step 3 / Step 4 / Step 5 survivors. Mandatory prerequisite before any
live consideration. Tracked per-week, trade count and win rate must remain
within 30% of backtest expectation.

### Step 7 — Live deployment

**Out of scope.** Even if Step 6 passes, going live is a separate sprint-level
decision gated on `docs/07-paper-and-live-trading.md` §7.6.

## 23.7 Task Breakdown

> Canonical task IDs are the letters in `TASKS.md` (A–L + ESC).
> Cross-references in this document use those letters.

| Task | Owner tier | Depends on | Brief |
|---|---|---|---|
| A | Codex 5.4 low | — | Branch + confirm 1d backtest window and stoploss table |
| B | Codex 5.4 low | A | Download 1d OHLCV for 4 majors, 2022-01-01 → 2025-05-01 |
| C | Codex 5.4 medium | A | Five `*Daily` strategy subclasses + smoke tests |
| D | Codex 5.4 low | B, C | Tier 1 same-window backtests (`run_baselines.py`) |
| E | Codex 5.4 low | C | Smoke test for `MultiTimeframeConfirmation` if needed in Tier 2 |
| F | Antigravity Flash medium | D | Tier 1 walk-forward for Step 1 survivors |
| G | Antigravity Flash high | F | Write `docs/24-higher-timeframe-results.md` |
| H | Codex 5.4 medium | F (conditional on ≥ 1 Step 3 survivor) | `MultiTimeframeConfirmation` strategy + smoke test |
| I | Antigravity Flash medium | H | Tier 2 same-window + walk-forward for MTF combo |
| J | Antigravity Flash medium | F or I (conditional) | Regime-filter experiments for survivors |
| K | Antigravity Flash medium | G + J (conditional) | 4-week paper-trade dry-run for survivors |
| L | Codex 5.4 low | all | Update `TASKS.md` at sprint end + invoke §23.8 if no survivors |
| ESC | Sonnet 4.6 Thinking | — | Escalation lane — design-level questions only |

**Cost ceiling.** ≈ 1 Codex 5.4 medium-day for C+H, ≈ 0.5 Codex 5.4 low-day
for A+B+D+E+L, ≈ 2 Antigravity Flash medium-days for F+I+J+K, ≈ 0.5
Antigravity Flash high-day for G. No Opus, no Codex 5.5 high+, no Devin in
the default path.

## 23.8 Kill Criterion

If **Tier 1 produces zero Step 3 survivors AND Tier 2 is skipped** — or if
Tier 1 has survivors but Tier 2's `MultiTimeframeConfirmation` also fails —
the indicator-on-OKX-spot research direction has now been tested across:

- 5 baseline indicator strategies + 1 regime-filtered variant
- 4 primary timeframes (5m, 1h, **and now 1d** — plus 4h as an informative
  layer inside MTT and MTF combo)
- 2 static universes (4 majors, top-20)
- 1 dynamic universe (top-3 of top-20, by daily momentum)
- 1 multi-timeframe-confirmation variant spanning 1w + 1d + 4h

At that point the answer is **conclusive**: indicators on OKX spot do not
produce a validated edge with the current acceptance criteria. The next
sprint **must** address a structurally different direction:

- **Option A — FreqAI.** Freqtrade's built-in ML module. Feed 30+ engineered
  features (BTC dominance, volatility regime, RSI/EMA stack, volume profile,
  candle patterns, time-of-day) and train an LGBM classifier on per-bar
  return targets. Walk-forward retraining. Higher over-fit risk; higher
  information density per sprint.
- **Option B — Perps + funding-rate arbitrage.** Cash-and-carry: long spot,
  short perp when funding is positive. Structural cash flow, not directional
  alpha. Requires opening a perps account on OKX or Binance and adding a
  paired-leg position manager. Lowest sprint cost; highest probability of
  finding *some* survivable edge because the edge is a paid cash flow, not
  a discovered pattern.
- **Option C — Stop here.** The pipeline + 24 docs + multi-agent muscle are
  the deliverable. Park the repo. Right answer if the goal was learning
  research discipline more than income, or if neither Option A nor Option B
  is worth the time at the current capital base ($500 dry-run).

The decision between A, B, and C is reserved for the ESC lane after this
sprint closes. **No more indicator/timeframe/lookback sprints.** §23.8 has no
escape hatch — the categorical-fee-economics argument that justified this
sprint as an exception to §21.8 has been used. There are no remaining
categorical changes within the indicator-on-spot hypothesis space.

## 23.9 Out of Scope

These are deferred to future sprints or explicitly skipped:

- **Hyperopt over the stoploss or ROI parameters.** Both are class
  attributes, not hyperopt parameters. Tuning them is the same trap §21.8
  rejected.
- **4h primary as a standalone test.** Skipped per §23.2.3 — sits between
  rejected 1h and proposed 1d without categorical economic difference.
- **1w primary as a standalone test.** Skipped per §23.2.3 — sample size too
  small for the ≥ 50-trade screen.
- **Top-20 universe on 1d/4h.** Skipped per §23.2.3 — Sprint 19 ruled out
  the universe as the bottleneck.
- **3d, 7d, or other lookback periods for the Sprint 21 momentum ranking.**
  Out of scope per §21.8.
- **Cross-exchange testing.** OKX spot only.
- **Live deployment.** Out of scope per §23.6 Step 7 regardless of result.

[Back to docs index](README.md)
