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

### 17.2.2 Binance.vision as default (stretch)

Per roadmap item 11.3: switch historical data ingestion to
`scripts/download_binance_vision.py` so that backtest results are reproducible
against immutable archives. **This is a stretch goal for this sprint** — only
pursue if the new strategies are complete and validated first.

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

**Entry conditions (all must be true):**

1. **Adaptive dip.** Close is more than `N × ATR(14)` below the 20-period SMA
   (N is tunable; default 1.5). This replaces a fixed Bollinger width with a
   volatility-adaptive distance.
2. **Volatility contraction.** ATR(14) is below its 50-period rolling median.
   Mean reversion is only structurally valid when volatility is low and price is
   ranging.
3. **Oversold confirmation.** RSI(14) < 35.
4. **Regime filter.** `classify_regime()` returns `range` or `bull` (no
   mean-reversion in bear trends — learned from `RSITrendBullOnly`'s failure).

**Exit conditions (any one triggers):**

1. Close returns to the 20-period SMA (mean reverted).
2. ATR(14) expands above `1.5 × median(ATR, 50)` (regime changed — exit early).
3. ROI ladder or stoploss (default -4%).

**Hyperopt-tunable parameters:**

| Parameter | Range | Space |
|---|---|---|
| `atr_entry_multiplier` | 1.0–3.0 | buy |
| `sma_period` | 15–30 | buy |
| `atr_period` | 10–20 | buy |
| `atr_median_lookback` | 30–100 | buy |
| `rsi_oversold` | 25–40 | buy |
| `use_regime_filter` | True/False | buy |
| `atr_exit_multiplier` | 1.0–2.5 | sell |

**Why this might work:** The original `BollingerMeanReversion` failed because it
traded in all volatility regimes. Mean reversion is structurally only valid in
low-volatility, range-bound markets. ATR-gating is the most common fix in
quantitative literature. Combining it with the existing regime classifier
(`user_data/regime/classifier.py`) gives two orthogonal filters against trading
in the wrong conditions.

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

**Screen criteria:** ≥ 20 trades, max drawdown < 30%. Strategies that fail the
screen do not advance.

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
whether regime filtering improves or degrades OOS metrics.

### Step 5: Document

Write results in `docs/18-*.md` (or appropriate number) following the structure
of `docs/16`.

## 17.5 Task Breakdown

| # | Task | Agent | Depends On |
|---|---|---|---|
| 1 | Create feature branch | Any | — |
| 2 | Download 1h candle data (all 4 pairs, 2024-07-01 to 2025-05-01) | Any | 1 |
| 3 | Implement `MultiTimeframeTrend.py` with hyperopt-safe indicators | Antigravity | 2 |
| 4 | Implement `ATRAdaptiveMeanReversion.py` with regime filter | Antigravity | 2 |
| 5 | Add import + smoke tests for both strategies | Any | 3, 4 |
| 6 | `ruff check .` + `pytest` green | Any | 5 |
| 7 | Run same-window baseline backtests | Any | 6 |
| 8 | Run walk-forward validation for survivors | Any | 7 |
| 9 | Write results doc (`docs/18-*.md`) | Any | 8 |
| 10 | Run regime-filter experiments on survivors | Any | 8 |
| 11 | Update `TASKS.md`, `AGENTS.md`, `docs/README.md` | Any | 9, 10 |

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

### Why keep the same 4 pairs?

- Changing too many variables at once makes it impossible to attribute
  improvement. The timeframe and strategy logic change is already a large
  shift. Keep pairs constant.
- Mid-cap alt expansion is a candidate for a future sprint if 1h strategies
  show promise on majors.

---

[Back to docs index](README.md)
