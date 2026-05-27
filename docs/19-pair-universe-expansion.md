# 19. Sprint Plan — Pair Universe Expansion (top-20 USDT spot)

## 19.1 Context

Eight strategies have now been rejected by the established validation pipeline:

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

See `docs/14`, `docs/16`, `docs/18` for the full result history.

**Key observation.** The strategy space (indicator combinations) and the
timeframe space (5m and 1h) have both been searched. The one variable that has
*not* changed across any of the eight rejections is the **pair universe** —
every test has been on BTC, ETH, SOL, BNB. These four are the most over-served
markets in crypto: every retail TA bot, every market maker, every quant desk
trades them. The signal-to-noise floor is structurally low.

This sprint expands the pair universe to the **top-20 USDT spot pairs on OKX**
and re-runs the existing baseline strategies against that universe. The
strategies themselves do not change — only the data they see.

## 19.2 Universe Definition

### 19.2.1 Selection rule

The universe is the top-20 USDT spot pairs on OKX by 30-day average quote
volume **as of 2024-07-01** (the start of the backtest window). This snapshot
date is fixed up front to prevent survivorship-bias goalpost moving — agents
must not re-rank using 2026 data and then claim 2024 backtest results.

> **Note.** Some look-ahead survivorship bias is inevitable: pairs that
> existed in 2024 but later delisted are excluded. This is acknowledged and
> documented; it is **not** a reason to expand the universe further or to
> re-rank on out-of-sample data.

### 19.2.2 Exclusions

The following are filtered out before ranking:

- **Stablecoin pairs**: `USDC/USDT`, `DAI/USDT`, `TUSD/USDT`, etc.
- **Wrapped tokens** that track another asset 1:1: `WBTC/USDT`, `WETH/USDT`,
  `STETH/USDT`, `WBNB/USDT`, etc.
- **Leveraged tokens** (any with `3L`, `3S`, `5L`, `5S`, `UP`, `DOWN` suffixes).
- **Inverse / synthetic pairs**.
- Any pair with **less than 6 months of OKX history** as of 2024-07-01 (no
  bootstrap effect on 90d in-sample windows).

### 19.2.3 How to discover the universe

OKX exposes 30d quote volume via `GET /api/v5/market/tickers?instType=SPOT`.
A small helper script (Task A) queries it, applies the exclusion rules above,
and writes the resulting whitelist to `user_data/universes/top20_okx_2024-07-01.json`.
Commit the JSON. The committed snapshot is the source of truth for the rest
of the sprint — no agent re-derives it.

> **Warning.** Live OKX ticker volume reflects *current* activity, not
> 2024-07-01 activity. The script must therefore use historical OHLCV
> (already in `user_data/data/okx/`) to compute 30d quote volume ending on
> 2024-07-01 for every USDT spot pair that had data by then. The live
> ticker endpoint is only used to enumerate which pairs **exist** — the
> ranking itself must be done from historical candles.

## 19.3 Strategy Reuse

No new strategy classes are written this sprint. The five committed 5m
baselines are reused as-is:

- `EMACrossover`
- `DonchianBreakout`
- `BollingerMeanReversion`
- `RSITrend`
- `MACDVolume`

The two 1h strategies (`MultiTimeframeTrend`, `ATRAdaptiveMeanReversion`) are
**out of scope** this sprint. Changing both timeframe and universe at once
makes attribution impossible. If the 5m baselines show signal on top-20, a
follow-up sprint can re-run the 1h strategies on the same universe.

## 19.4 Config Changes

Two minimal edits to `user_data/config.json`:

1. Replace `pair_whitelist` with the 20 pairs from the committed snapshot.
2. **Re-evaluate `max_open_trades`.** Current value is `2` (decided in sprint 17
   per docs/17 §17.2.2). With 20 pairs available, the bot will see far more
   simultaneous entry signals — `2` may be too restrictive. The 5m stoploss is
   `-3%`, so 1% equity risk ÷ 3% stop = ~33% per position. Choices:

   - **Option A (recommended):** keep `max_open_trades = 2`. Peak concentration
     stays at ~66% of equity, identical to the conservative posture this repo
     has maintained.
   - **Option B:** increase to `max_open_trades = 3`. Peak concentration ~99%
     of equity. Only do this if Task A explicitly signs off in `TASKS.md`.
   - **Option C:** decrease to `max_open_trades = 1`. Peak concentration ~33%.
     Conservative but trades less; useful if the strategies turn out to be very
     concentrated in time.

   Default to Option A unless there is a reason to deviate.

Do **not** change `stake_amount`, `dry_run_wallet`, or the exchange config.

## 19.5 Data Expansion

```bash
freqtrade download-data -c user_data/config.json \
    --timeframes 5m \
    --timerange=20240701-20250501
```

With `pair_whitelist` already pointing at the new top-20, this fetches 5m
candles for all 20 pairs over the 10-month window. Expected size: ~16 new
pairs × 5m × 10 months ≈ 1.4M new bars total. Still well within disk and
memory budgets.

Data remains gitignored. The whitelist JSON in `user_data/universes/` **is**
committed (it's metadata, not candle data).

## 19.6 Validation Pipeline

Same pipeline as sprints 17/18, with one screen-criterion adjustment for the
larger universe.

### Step 1: Same-window baseline backtest

```bash
python scripts/run_baselines.py \
    --strategies EMACrossover DonchianBreakout BollingerMeanReversion RSITrend MACDVolume \
    --pairs $(jq -r '.pairs | join(" ")' user_data/universes/top20_okx_2024-07-01.json) \
    --timerange=20250101-20250501
```

**Screen criteria** (per strategy, aggregate across all 20 pairs):

- ≥ 50 trades (raised from 20 because 5× more pairs means more opportunities;
  a strategy generating < 50 trades on 20 pairs over 4 months is too rare to
  be statistically meaningful)
- Max drawdown < 30%

Strategies that fail the screen do not advance to walk-forward.

### Step 2: Per-strategy walk-forward (3+ OOS folds)

For each strategy that passes Step 1:

```bash
python scripts/walk_forward.py \
    --strategy <StrategyName> \
    --start 2024-07-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100
```

> **Note.** `walk_forward.py` uses the `pair_whitelist` from `config.json`
> at hyperopt/backtest time, so the top-20 universe applies automatically once
> Task B is complete.

### Step 3: Acceptance criteria

Identical to docs/16 §16.3 and docs/17 §17.4 — **do not change after seeing
results**:

| Criterion | Required |
|---|---:|
| Completed out-of-sample folds | ≥ 3 |
| Average OOS Sharpe | > 0 |
| Average OOS total profit % | > 0 |
| No single OOS fold drawdown | ≤ 5% |

### Step 4: Regime-filter experiments (only if Step 3 passes)

For any survivor, run `scripts/regime_filter_experiments.py` to test whether
bull-only / range-only / trending-only variants improve OOS metrics. As with
sprints 15/17, this is the **only** legitimate place to evaluate regime
gating — not inside the strategy class, not in the hyperopt space.

### Step 5: Document

Write results in `docs/20-*.md` following the structure of `docs/18`. Include
the universe selection methodology, per-pair trade counts in same-window step,
walk-forward per-fold table, and explicit pass/fail against §19.6 Step 3.

### Step 6: Paper-trade gate (only if any strategy passes Step 3)

4+ weeks of `freqtrade trade --dry-run` before any live consideration.
Identical to docs/17 §17.4 Step 6.

This sprint does **not** include any live-money deployment.

## 19.7 Task Breakdown

Agent assignments follow the cost/capability rubric established in PR #10.
Do **not** route any task here to Opus Thinking, Codex 5.5 high+, or Devin
without explicit escalation.

| # | Task | Suggested agent | Depends On |
|---|---|---|---|
| 1 | Create feature branch + decide `max_open_trades` posture per §19.4 | Codex 5.4 low | — |
| 2 | Write `scripts/build_universe.py`: enumerate OKX USDT spot, exclude per §19.2.2, rank by historical 30d quote volume ending 2024-07-01, output `user_data/universes/top20_okx_2024-07-01.json` | Codex 5.4 medium | 1 |
| 3 | Add a test for `build_universe.py` (mock OKX tickers + synthetic OHLCV, verify ranking + exclusion logic) | Codex 5.4 low | 2 |
| 4 | Run `build_universe.py`, commit the JSON, update `pair_whitelist` in `user_data/config.json` | Codex 5.4 low | 2, 3 |
| 5 | Download 5m candle data for the new 16 pairs (BTC/ETH/SOL/BNB already present) | Antigravity Gemini Flash medium | 4 |
| 6 | Run same-window baseline backtests per §19.6 Step 1 | Antigravity Gemini Flash medium | 5 |
| 7 | For each strategy that passes Step 1, run walk-forward sweep per §19.6 Step 2 | Antigravity Gemini Flash medium | 6 |
| 8 | Write `docs/20-pair-universe-results.md` following docs/18 structure | Antigravity Gemini Flash high | 7 |
| 9 | Regime-filter experiments on Step 3 survivors only | Antigravity Gemini Flash medium | 7 |
| 10 | If any strategy passes acceptance, start 4-week paper-trade dry-run per §19.6 Step 6 | Antigravity Gemini Flash medium | 8 |
| 11 | Update `TASKS.md`, `AGENTS.md`, `docs/README.md` to reflect sprint outcome | Codex 5.4 low | 8, 9 |
| ESC | Anything ambiguous or design-level (e.g., did the universe-selection script miss obvious pairs? should we expand to top-50? should we re-introduce 1h strategies?) | Sonnet 4.6 Thinking — escalate, do **not** decide locally | any |

**Cost ceiling:** ~1 Codex 5.4 medium-day + ~2 Antigravity Gemini Flash
medium-days. The walk-forward step (Task 7) is the largest single block —
each strategy × top-20 sweep is ~5× the compute of sprint 17's
single-strategy walk-forward. Plan accordingly.

## 19.8 Design Decisions and Rationale

### Why top-20 and not top-50 or top-100?

- Compute scales linearly with pair count; top-50 would be ~2.5× compute
  for what is probably diminishing returns.
- Top-20 is roughly where OKX volume per pair drops below $50M/day — below
  that, slippage and fill quality on $50 dry-run orders is questionable.
- If top-20 shows clear signal in any strategy, a follow-up sprint can
  expand to top-50.

### Why fix the snapshot date at 2024-07-01?

- The backtest window is 2025-01-01 → 2025-05-01. Selecting the universe
  at 2024-07-01 (6 months before the window start) gives meaningful
  volume history without using future information.
- Any agent that re-ranks the universe using 2026 ticker data and then
  applies it to 2024 backtests is doing implicit look-ahead. The
  committed JSON prevents this.

### Why same screen criteria (>0 OOS Sharpe, >0 OOS profit) and not stricter?

- Stricter criteria after 8 rejections would feel like moving the
  goalposts inward, which is just as bad as moving them outward.
- The current criteria are deliberately *weak* — a strategy that survives
  them is a "weak research candidate" only, not something to deploy.
  Paper-trade gating (Step 6) is the secondary filter.

### Why no daily momentum ranking?

- Daily ranking ("trade only the top-3 pairs by 1d momentum each day") is
  a meaningfully different strategy from "trade all 20 pairs all the time."
- This sprint tests the simpler hypothesis first. If any strategy survives,
  a follow-up sprint can add the momentum ranking as a meta-layer.

### Why not re-run the 1h strategies on top-20 in the same sprint?

- Changing two variables at once (universe and timeframe) makes attribution
  impossible. If a 1h strategy works on top-20, we won't know whether it's
  the universe or the timeframe doing the work.
- The 5m baselines are already implemented, tested, and CI-green. Reusing
  them is the lowest-effort highest-info first pass.

### What is the kill criterion for this entire research thread?

- If **zero of five strategies pass the same-window screen** on top-20:
  the strategy space is the bottleneck, not the universe. Escalate via
  the ESC lane — next sprint should be FreqAI (Option 2 from the
  branching memo) or perps + funding rate (Option 3), not yet another
  universe tweak.
- If **at least one strategy passes the screen but none pass walk-forward**:
  proceed to the daily-momentum-ranking follow-up sprint described in
  §19.8 "Why no daily momentum ranking" before declaring the thread dead.
- If **any strategy passes walk-forward**: the sprint succeeded. Move to
  paper-trade gate (Step 6).

---

[Back to docs index](README.md)
