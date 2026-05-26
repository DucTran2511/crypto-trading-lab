# 17. Next Sprint Plan — New Hypotheses on Higher Timeframes

## 17.1 Context

All research candidates from the first round have been rejected through the
established validation pipeline:

| Strategy | Outcome | Key Failure |
|---|---|---|
| `EMACrossover` | Control only | -20.8% baseline profit, never entered walk-forward |
| `DonchianBreakout` | Control only | -28.3% baseline profit, never entered walk-forward |
| `MACDVolume` | Control only | -49.3% baseline profit, never entered walk-forward |
| `BollingerMeanReversion` | Rejected | Passed same-window screen, failed OOS fold |
| `RSITrend` | Rejected | Passed same-window screen, failed OOS fold |
| `RSITrendBullOnly` | Rejected | Best regime variant, failed 3-fold multi-window (avg OOS Sharpe -0.48, avg OOS profit -0.06%) |

See [14. Strategy comparison report](14-strategy-comparison-report.md) for the
full ranking and [16. RSITrendBullOnly multi-window](16-rsitrend-bullonly-multiwindow.md)
for the final rejection.

**Key observation:** Every strategy tested so far has been a single-timeframe, 5m
approach on major pairs (BTC, ETH, SOL, BNB). The 5m timeframe on these pairs is
extremely efficient — thousands of bots already trade the same signals. The
signal-to-noise ratio at 5m on majors is structurally poor for simple
indicator-based entries. This sprint shifts the research to higher timeframes and
structurally different entry logic.

## 17.2 Data Expansion

Before building new strategies, expand the data foundation.

### 17.2.1 Download 1h candles

All existing data is 5m only. Higher-timeframe strategies need 1h (and optionally
4h via Freqtrade's `informative_pairs()`) candles.

```bash
freqtrade download-data -c user_data/config.json \
  --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
  --timeframes 1h \
  --timerange=20240701-20250501
```

This gives 10 months of 1h data — enough for 3+ walk-forward folds with 90-day
in-sample and 30-day out-of-sample windows.

> **Note.** Binance.vision as the default ingestion source (roadmap item 11.3) is
> intentionally **out of scope** for this sprint. It is unrelated to the 1h
> hypothesis and changing the data source mid-sprint would conflate the
> evaluation. Leave it for a dedicated infra sprint after the 1h strategies are
> resolved either way.

### 17.2.2 Position-sizing posture (review before any backtest)

The stoploss change in §17.6 (from -3% on 5m to -5% on 1h) interacts with
`max_open_trades`:

- Risk-per-trade rule: 1% of equity per trade.
- 1% equity risk ÷ 5% stop distance = **20% of equity** per position max.
- `user_data/config.json` currently has `max_open_trades = 3` (carry-over from the
  5m era). 3 × 20% = **60% of equity deployed at peak**, which is materially
  more concentrated than the previous 5m posture (3 × 12% ≈ 36% at peak).

**Decision before running any 1h backtest:**

- **Option A (recommended):** Tighten `max_open_trades` to `2` in
  `user_data/config.json` for this sprint. 2 × 20% = 40% peak concentration,
  which is closer to the conservative posture so far.
- **Option B:** Keep `max_open_trades = 3` and document that this sprint runs at
  60% peak concentration. Acceptable only if the sprint owner explicitly signs
  off in `TASKS.md`.

Do not introduce per-strategy stoploss changes by editing `config.json` globally
— set `stoploss = -0.05` as a class attribute on each new 1h strategy so the
5m baselines are unaffected. See `EMACrossover.py` for the pattern.

## 17.3 Strategy Hypotheses

Two structurally different approaches, both on the 1h timeframe:

---

### Strategy A: `MultiTimeframeTrend`

**File:** `user_data/strategies/MultiTimeframeTrend.py`

**Hypothesis:** Enter on 1h pullbacks within a 4h uptrend. The higher timeframe
acts as the primary signal, reducing the noise that killed all 5m strategies.

**Entry conditions (all must be true):**

1. **4h trend alignment.** The 4h EMA(50) slope (computed over the last 5 bars)
   is positive — the higher-timeframe trend is up.
2. **1h pullback-and-recover.** RSI(14) on the 1h chart pulled back below a
   tunable threshold (default 40) then recovered above it within the last
   N candles. This is a dip-buy into a confirmed trend.
3. **1h local trend.** Close is above the 1h EMA(50).
4. **Volume confirmation.** 1h volume is above its 20-period rolling mean.

**Exit conditions (any one triggers):**

1. 4h EMA(50) slope turns negative (trend broken on HTF).
2. 1h RSI(14) crosses above 70 (overbought).
3. ROI ladder or stoploss (configurable; default -5% for 1h candle range).

**Hyperopt-tunable parameters:**

| Parameter | Range | Space |
|---|---|---|
| `ema_trend_4h` | 20–100 | buy |
| `rsi_entry_threshold` | 25–45 | buy |
| `rsi_recovery_window` | 2–8 candles | buy |
| `ema_local_1h` | 20–100 | buy |
| `min_volume_factor` | 0.5–3.0 | buy |
| `rsi_exit_threshold` | 65–80 | sell |

**Freqtrade implementation notes:**
- Uses `informative_pairs()` to request 4h candles as an informative timeframe.
- The primary `timeframe` is `"1h"`.
- `startup_candle_count` must be at least `max(ema_trend_4h.range) * 4` (to
  allow the 4h EMA to warm up on 1h bars).
- Use the `for val in self.<param>.range` pattern from `EMACrossover` §3.4 for
  hyperopt-safe indicator caching.

**Why this might work:** Multi-timeframe alignment is one of the few
retail-accessible structural edges in crypto. The 4h filter eliminates the
majority of chop that killed 5m strategies. RSI pullback-into-trend is a
well-documented setup with weak-positive expectancy on momentum assets in
academic literature.

---

### Strategy B: `ATRAdaptiveMeanReversion`

**File:** `user_data/strategies/ATRAdaptiveMeanReversion.py`

**Hypothesis:** Mean reversion only works in low-volatility regimes. Instead of a
static Bollinger Band (like `BollingerMeanReversion`), use ATR(14) to dynamically
size entry distance and only take trades when volatility is contracted.

This strategy is the **unfiltered baseline**. Regime gating is **not** built into
the strategy itself and is **not** a hyperopt parameter — it would let hyperopt
pick whichever branch happened to win in-sample, defeating the validation. Regime
filters are evaluated separately by `scripts/regime_filter_experiments.py` after
the baseline survives walk-forward, exactly as was done for `RSITrend` →
`RSITrendBullOnly` (see `docs/15-regime-filter-experiments.md`).

**Entry conditions (all must be true):**

1. **Adaptive dip.** Close is more than `N × ATR(14)` below the `sma_period`-bar
   SMA (N is tunable; default 1.5). This replaces a fixed Bollinger width with a
   volatility-adaptive distance.
2. **Volatility contraction.** ATR(14) is below its `atr_median_lookback`-period
   rolling median. Mean reversion is structurally only valid when volatility is
   low and price is ranging.
3. **Oversold confirmation.** RSI(14) < `rsi_oversold` (default 35).

**Exit conditions (any one triggers):**

1. Close returns to the `sma_period`-bar SMA (mean reverted).
2. ATR(14) expands above `atr_exit_multiplier × median(ATR, atr_median_lookback)`
   (regime changed — exit early).
3. ROI ladder or stoploss (default -5%; see §17.6).

**Hyperopt-tunable parameters:**

| Parameter | Range | Space |
|---|---|---|
| `atr_entry_multiplier` | 1.0–3.0 | buy |
| `sma_period` | 15–30 | buy |
| `atr_period` | 10–20 | buy |
| `atr_median_lookback` | 30–100 | buy |
| `rsi_oversold` | 25–40 | buy |
| `atr_exit_multiplier` | 1.0–2.5 | sell |

> **Warning.** Do **not** add `use_regime_filter: True/False` to the hyperopt
> space. Run regime gating as a separate generated subclass via
> `scripts/regime_filter_experiments.py` (the established pattern). Tuning a
> filter on/off in hyperopt amounts to letting the optimizer pick the version
> with more degrees of freedom and produces results that do not generalise.

**Why this might work:** The original `BollingerMeanReversion` failed because it
traded in all volatility regimes. Mean reversion is structurally only valid in
low-volatility, range-bound markets. ATR-gating is the most common fix in
quantitative literature. If the unfiltered baseline survives walk-forward,
`regime_filter_experiments.py` then tests whether layering a `range`-only or
`bull-or-range` regime filter on top further improves OOS metrics.

---

## 17.4 Validation Pipeline

Apply the exact same pipeline that correctly rejected the previous candidates.
**Do not change the acceptance criteria after seeing results.**

### Step 1: Same-window baseline backtest

```bash
python scripts/run_baselines.py \
  --strategies MultiTimeframeTrend ATRAdaptiveMeanReversion \
  --timerange=20250101-20250501
```

**Screen criteria:** ≥ 20 trades **and** max drawdown < 30%. Strategies that fail
the screen do not advance.

> **Note — trade-count fallback for Strategy B.** The ATR-contraction + RSI <
> 35 filter on Strategy B is intentionally tight and may produce < 20 trades
> over 4 months on 1h × 4 pairs. If Strategy B fails **only** the trade-count
> screen (not the drawdown screen), perform **one** relaxation pass before
> abandoning the hypothesis: change the ATR-contraction filter from
> `ATR < median(ATR, 50)` to `ATR < 75th-percentile(ATR, 50)`. Document the
> change in the results doc and re-run Step 1 once. Do **not** keep relaxing
> filters in pursuit of trade count — that is post-hoc tuning. If the relaxed
> version still fails, reject the hypothesis.
>
> This fallback applies **only** to the trade-count screen, not to walk-forward
> acceptance criteria in Step 3.

### Step 2: Walk-forward validation (3+ OOS folds)

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100
```

### Step 3: Acceptance criteria

All four must pass (identical to `docs/16` §16.3):

| Criterion | Required |
|---|---|
| Completed out-of-sample folds | ≥ 3 |
| Average OOS Sharpe | > 0 |
| Average OOS total profit % | > 0 |
| No single OOS fold drawdown | ≤ 5% |

### Step 4: Regime-filter experiments (if Step 3 passes)

Run `scripts/regime_filter_experiments.py` for any passing strategy to check
whether regime filtering improves or degrades OOS metrics. This is the **only**
legitimate place to evaluate regime gating — not inside the strategy class and
not inside the hyperopt space.

### Step 5: Document

Write results in `docs/18-*.md` (or appropriate number) following the structure
of `docs/16`. Include the trade-count screen result, walk-forward per-fold table,
and explicit pass/fail against §17.4 step 3 acceptance criteria.

### Step 6: Paper-trade gate (only if Step 3 passes)

Any strategy that passes acceptance must run as a Freqtrade dry-run for **at
least 4 weeks of live wall-clock time** before any further escalation:

```bash
freqtrade trade -c user_data/config.json --strategy <StrategyName>
```

> **Warning.** Do not skip the paper-trade gate. Walk-forward acceptance is
> necessary but not sufficient — it doesn't catch exchange-side execution issues
> (partial fills, fee changes, API stalls), regime shifts between historical
> windows and live, or operational bugs (timezone, candle alignment, restart
> handling). Until 4 weeks of dry-run logs match the backtest's expected
> per-week trade count and win rate within tolerance, no live deployment.

This sprint does **not** include any live-money deployment. That decision is
deferred to a future sprint and requires a separate go/no-go in `TASKS.md`.

## 17.5 Task Breakdown

Agent assignments follow the cost/capability rubric established in PR #10:
cheap models for transcription, mid-tier for code from spec, high-tier for
design-under-ambiguity, Devin only for end-to-end PRs. Do **not** route any task
here to Opus Thinking, Codex 5.5 high+, or Devin unless explicitly escalated.

| # | Task | Suggested agent | Depends On |
|---|---|---|---|
| 1 | Create feature branch | Codex 5.4 low (or any) | — |
| 2 | Adjust `max_open_trades` per §17.2.2 decision; document choice in `TASKS.md` | Codex 5.4 low | 1 |
| 3 | Download 1h candle data (4 pairs, 2024-07-01 → 2025-05-01) | Antigravity Gemini Flash medium | 1 |
| 4 | Implement `MultiTimeframeTrend.py` per §17.3 Strategy A | Codex 5.4 medium | 3 |
| 5 | Implement `ATRAdaptiveMeanReversion.py` per §17.3 Strategy B (no regime filter, no `use_regime_filter` param) | Codex 5.4 medium | 3 |
| 6 | Add import + smoke tests for both strategies in `tests/` | Codex 5.4 low | 4, 5 |
| 7 | `ruff check .` + `pytest` green | Codex 5.4 low | 6 |
| 8 | Run same-window baseline backtests (`scripts/run_baselines.py`) | Antigravity Gemini Flash medium | 7 |
| 9 | If Strategy B fails only the trade-count screen, apply the **one** relaxation per §17.4 Step 1 note | Antigravity Gemini Flash medium | 8 |
| 10 | Run walk-forward validation for survivors (`scripts/walk_forward.py`) | Antigravity Gemini Flash medium | 8 (or 9) |
| 11 | Write results doc `docs/18-*.md` following `docs/16` structure | Antigravity Gemini Flash high | 10 |
| 12 | Run regime-filter experiments on Step 3 survivors only (`scripts/regime_filter_experiments.py`) | Antigravity Gemini Flash medium | 10 |
| 13 | If any strategy passes acceptance, start 4-week paper-trade dry-run per §17.4 Step 6 | Antigravity Gemini Flash medium | 11 |
| 14 | Update `TASKS.md`, `AGENTS.md`, `docs/README.md` to reflect sprint outcome | Codex 5.4 low | 11, 12 |
| ESC | Anything ambiguous or design-level that arises (e.g., should we change the acceptance criteria? extend the sprint? swap pair universe?) | Sonnet 4.6 Thinking — escalate, do **not** decide locally | any |

**Cost ceiling:** ~1 Antigravity Gemini Flash medium-day + ~1 Codex 5.4
medium-half-day. Do not pre-emptively escalate to higher tiers; if a task
actually requires escalation, the assigned agent should stop and surface it.

## 17.6 Design Decisions and Rationale

### Why 1h instead of 5m?

- 5m on BTC/ETH/SOL/BNB produced ~800 trades in 4 months but every strategy
  had negative expectancy. The noise at 5m on majors overwhelms simple
  indicator signals.
- 1h will produce fewer trades (30–100 range) but each trade is based on a
  more meaningful price structure.
- Multi-timeframe confirmation (1h + 4h) is only practical at 1h resolution
  or higher.

### Why -5% stoploss for 1h (up from -3%)?

- A single 1h candle on BTC can easily move 2–3%. A -3% stop on 1h would
  trigger on normal volatility noise, not on the trade thesis being wrong.
- -5% accommodates the larger candle range while still capping single-trade
  risk (with position sizing: 1% equity risk ÷ 5% stop distance = 20% of
  equity per position max).
- Implementation: set `stoploss = -0.05` as a class attribute on each 1h
  strategy. Do **not** edit `user_data/config.json` — the 5m baselines still
  use -3% and the config is the wrong place to put strategy-specific risk.
- See §17.2.2 for the `max_open_trades` interaction this introduces.

### Why split regime filtering out of the strategy class?

- Tuning a regime filter as a hyperopt Boolean lets the optimiser pick the
  branch that happened to fit the in-sample window — there is no out-of-sample
  test of whether the filter itself adds signal.
- The existing pipeline (`scripts/regime_filter_experiments.py`) generates a
  family of regime-filtered subclasses from a baseline strategy and backtests
  each as a separate strategy. This is how `RSITrendBullOnly` was identified
  as the strongest variant of `RSITrend` (see `docs/15`).
- Replicating that pattern here means: build Strategy B unfiltered, validate
  it via walk-forward, **then** evaluate regime gating as separate experiments.

### Why keep the same 4 pairs?

- Changing too many variables at once makes it impossible to attribute
  improvement. The timeframe and strategy logic change is already a large
  shift. Keep pairs constant.
- Mid-cap alt expansion is a candidate for a future sprint if 1h strategies
  show promise on majors.

---

[Back to docs index](README.md)
