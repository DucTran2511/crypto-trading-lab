# 27. Sprint Plan — Spot DCA-with-Take-Profit Strategies

## 27.1 Context

Sprint 25 rejected. All three long-hold spot trend candidates failed the
§25.6 walk-forward gate (`docs/26-spot-trend-results.md`). §25.8 normally
restricts the remaining choices to **FreqAI** or **stop the lab** — no
further "different angle on indicators" sprints.

This sprint is a **structurally different** hypothesis class, not another
indicator variant. The 22 strategies tested across Sprints 13–25 all share
one mechanic: open a position when a signal fires, close it when the
opposite signal fires. **DCA-with-take-profit reverses both ends:**
*scale in* on adverse moves, *scale out* at a fixed profit target. This
is not a re-parameterisation of trend or momentum — it's a different
trade-shape primitive.

The user's `DucTran2511/dca-testing` repo contains a margin/liquidation
calculator (`scripts/dca_futures_sim.py`, merged in PR #52) implementing
the *math* of DCA on a leveraged futures long. Sprint 27 ports the
spot-equivalent of that math into the lab as a real Freqtrade strategy,
adds three entry-signal candidates, and validates the result through
the existing same-window-then-walk-forward harness.

### 27.1.1 Why this is a defensible exception to §25.8

§25.8 forbids "another spot-indicator variant" because the
**entry-signal-then-exit-signal** trade shape has been exhausted across
strategy logic, universe, hold horizon, and timeframe on long-only spot.
That exhaustion is real *within that trade shape*. The
**scale-in-on-adverse-move, scale-out-at-fixed-target** trade shape has
not been tested at all.

Concretely, prior sprints rejected on three failure modes (§22 §24 §26):
sample-size starvation, regime-dependent unfiltered edge, and
fee-and-noise dominance. DCA-with-TP is the only one of these modes that
**structurally addresses sample-size starvation** — every entry produces
multiple legs and a deterministic exit, so trade counts are bounded above
(by max legs) rather than driven by signal scarcity. It also turns
regime-dependence into an explicitly modeled drawdown profile (the
ladder), not a hidden assumption.

This is **the last permitted exception** to §25.8 in this direction. If
Sprint 27 also rejects, the next sprint must be FreqAI or stop, with no
further "different DCA variant" or "different entry signal" sprint
permitted.

### 27.1.2 Why these three entry-signal candidates

The user's stated goals are "good entry" and "good take profit." TP is
pre-registered identically across all three strategies (§27.4) so the
sprint isolates one variable: the **entry signal**. The three candidates
cover qualitatively different "is now a good time to start a DCA ladder?"
hypotheses:

| Strategy | Entry signal | Hypothesis |
|---|---|---|
| `DCASpotRSIEntry` | RSI(14) on 1d crosses up through 30 | Oversold mean reversion |
| `DCASpotBBEntry` | Close on 1d closes below Bollinger lower(20, 2.0) | Volatility-band mean reversion |
| `DCASpotPullbackEntry` | Close on 1d below EMA(50) AND above EMA(200) | Bull-market dip-buy |

All three are **long-only on spot, no leverage**. The DCA-and-TP
mechanics (§27.3) are identical across the three.

## 27.2 Scope

### 27.2.1 Shared DCA-with-TP mechanics

These rules apply to all three strategies. They are **pre-registered
class attributes**, not hyperopt parameters (§27.4).

- **Initial leg.** Entry signal opens one position at $50 notional.
- **DCA legs.** While a position is open, monitor price vs the
  **initial entry price**. Open an additional $50 leg each time price
  closes at or below:
  - `-5%` from initial entry → DCA leg 1
  - `-10%` → DCA leg 2
  - `-15%` → DCA leg 3
  - `-20%` → DCA leg 4
- **Max legs.** 5 total (initial + 4 DCAs). No further adds even if
  price keeps dropping.
- **Take profit.** Exit the entire position (all legs) when
  `current_rate ≥ avg_entry × 1.08` (running weighted-average entry
  including fees, +8%).
- **Hard stoploss.** Class attribute `stoploss = -0.25` on the position
  as a whole — Freqtrade fires the stop when `current_rate ≤ avg_entry
  × (1 + stoploss)`, i.e. **25% below the running avg entry**. With
  all 5 equal-USD legs filled, avg entry sits at ≈11% below initial
  (`5 / (1/1.0 + 1/0.95 + 1/0.90 + 1/0.85 + 1/0.80) = 0.8944`), so the
  stop fires near **-32.9% from initial entry** — about 16% below the
  deepest DCA leg at -20%. Catastrophe stop only: it does not trip on
  partial ladders unless price has fallen far past the bottom of the
  intended ladder. Dollar loss when the stop fires on a full ladder is
  `$250 × 0.25 = $62.50` (matches §27.5).
- **Time stop.** If `current_time - trade.open_date_utc > 90 days`,
  exit the position at market regardless of P&L. Prevents indefinite
  ladder-holding through extended bear markets.

### 27.2.2 Strategy 1 — `DCASpotRSIEntry`

Long-only oversold-reversion entry.

- **Initial entry:** `RSI(14, 1d)` was below `30` on the prior bar AND
  `RSI(14, 1d) ≥ 30` on the current bar (i.e. RSI crossed up through 30,
  no look-ahead).
- **DCA + TP + stops:** identical to §27.2.1.
- **Timeframe:** `1d`.

### 27.2.3 Strategy 2 — `DCASpotBBEntry`

Long-only Bollinger-lower-band entry.

- **Initial entry:** `close < BollingerLower(20, 2.0)` on the current
  1d bar (close at or below the 20-day lower band with 2.0 std dev).
- **DCA + TP + stops:** identical to §27.2.1.
- **Timeframe:** `1d`.

### 27.2.4 Strategy 3 — `DCASpotPullbackEntry`

Long-only bull-market pullback entry.

- **Initial entry:** all conditions:
  1. `close > EMA(200, 1d)` (long-term trend up)
  2. `close < EMA(50, 1d)` (short-term pullback into the trend)
  3. `EMA(50, 1d) > EMA(200, 1d)` (golden-cross regime confirmed)
- **DCA + TP + stops:** identical to §27.2.1.
- **Timeframe:** `1d`.

### 27.2.5 Universe

`BTC/USDT`, `ETH/USDT`, `SOL/USDT` on OKX spot. Three pairs. No
memecoins, no top-20 expansion.

Why narrow:
- DCA-with-TP **requires mean reversion within the time stop window**.
  Assets that can permanently lose >90% of their value (LUNA, FTT,
  most memecoins) break the implicit assumption of the strategy. A
  90-day time stop on a "rugged" asset locks in a -50% to -80% loss
  per ladder.
- All three pairs have **multi-year on-chain history** with documented
  bounce-back from drawdowns ≥50% (BTC 2018-19, BTC/ETH 2022, SOL 2022).
- Wider universes (top-10 or top-20) would inflate trade count but
  introduce assets without comparable bounce history. The sample-size
  cost is acceptable because DCA generates more legs per entry than
  signal-and-exit strategies.

### 27.2.6 Window

`2020-04-01` → `2025-12-01` (~5 years 8 months).

Rationale:
- Start at 2020-04-01 because SOL/USDT did not trade on OKX before
  ~2020-04. A uniform start date avoids ragged per-pair data windows.
- Covers 1 full bear → bull → bear → bull cycle (2020 COVID, 2021 bull,
  2022 bear, 2023-24 bull, 2025 consolidation).
- 5.7 years × 1d candles = ~2080 candles per pair × 3 pairs = 6240
  total candles. Enough for walk-forward at the trade-counts DCA
  produces (see §27.6).

### 27.2.7 Explicitly skipped

| Cell | Why skipped |
|---|---|
| Leverage / futures variants | Sprint 27 is spot-only. `scripts/dca_futures_sim.py` from PR #52 is reference math only; not invoked by any Sprint 27 task. The leverage version of DCA has a well-known martingale-with-cliff failure mode (catastrophic single-event drawdowns despite many winning cycles). |
| Wider universe (top-20) | §27.2.5. Survivorship risk on memecoins breaks the mean-reversion assumption. |
| Variable TP (ATR-scaled, trailing) | One TP rule per sprint. +8% fixed is the simplest pre-registerable variant. ATR-scaled and trailing TPs are explicit follow-up candidates only if Sprint 27 passes. |
| Variable DCA spacing (geometric, ATR-scaled) | Same reason. -5% fixed spacing is the baseline. |
| Hyperopt over DCA spacing / max legs / TP / time-stop | Strictly forbidden. These are pre-registered (§27.4) so the sprint isolates *entry-signal quality* as the only moving variable. |
| Adding short-side DCA | Spot-only excludes shorts. Separate research direction. |
| FreqAI / ML on engineered features | Reserved for the post-Sprint-27 escalation if §27.8 fires. |

## 27.3 Implementation Files

### 27.3.1 New strategy files

- `user_data/strategies/DCASpotBase.py` — abstract base class containing
  the shared DCA + TP + stop mechanics from §27.2.1. Inherits from
  `IStrategy`. **Not itself loadable as a Freqtrade strategy** (class
  name does not match a strategy intended for direct backtesting; the
  three concrete subclasses are the strategies the harness loads).
- `user_data/strategies/DCASpotRSIEntry.py` — concrete subclass
  overriding `populate_indicators` to compute RSI(14) and
  `populate_entry_trend` to gate entries on the §27.2.2 cross-up rule.
- `user_data/strategies/DCASpotBBEntry.py` — concrete subclass
  overriding `populate_indicators` to compute BollingerBands(20, 2.0)
  and `populate_entry_trend` to gate entries on the §27.2.3 close-below
  rule.
- `user_data/strategies/DCASpotPullbackEntry.py` — concrete subclass
  overriding `populate_indicators` to compute EMA(50) and EMA(200) and
  `populate_entry_trend` to gate entries on the §27.2.4 three-condition
  rule.

The base class owns `adjust_trade_position`, `custom_exit`, `stoploss`,
`minimal_roi`, `position_adjustment_enable = True`,
`max_entry_position_adjustment` (4, for the 4 DCA legs after initial),
and `process_only_new_candles = True`.

The subclasses own `populate_indicators`, `populate_entry_trend`,
`populate_exit_trend` (the last returns all zeros — exits are owned by
`custom_exit` in the base).

### 27.3.2 New config

- `user_data/config-sprint27-dca.json` — copy of `user_data/config.json`
  with:
  - `pair_whitelist`: `["BTC/USDT", "ETH/USDT", "SOL/USDT"]`
  - `dry_run = true`, `dry_run_wallet = 500`, `trading_mode = spot`
  - `stake_amount = 50`
  - `max_open_trades = 3` (one ladder per pair, no double-ladders
    within a pair)
  - `position_adjustment_enable = true` (mirror the base class
    attribute at config level so the backtest engine picks it up)
  - `timeframe = "1d"`

The committed `user_data/config.json` is **not modified**.

### 27.3.3 New tests

- `tests/test_dca_spot_base.py` — unit tests for the base class:
  - DCA leg fires at -5% from initial entry, not -5% from avg entry.
  - Max 5 legs total (4 calls to `adjust_trade_position` return a
    positive number, the 5th call returns `None`).
  - `custom_exit` returns a TP exit when `current_rate ≥ avg_entry * 1.08`.
  - `custom_exit` returns a time-stop exit when `current_time -
    trade.open_date_utc > 90 days` and no TP/stop hit.
- `tests/test_dca_spot_rsi_entry.py` — smoke test +
  no-look-ahead assertion on the RSI-cross signal.
- `tests/test_dca_spot_bb_entry.py` — smoke test +
  no-look-ahead assertion on the BB lower-band signal.
- `tests/test_dca_spot_pullback_entry.py` — smoke test +
  no-look-ahead assertion on the EMA stack signal.

## 27.4 Pre-Registered DCA / TP / Stop Parameters

These are **not hyperopt parameters** — they are class attributes locked
at sprint plan time, identical-treatment to Sprint 25 §25.4.
Goalpost-move attempts during execution are blocked.

| Parameter | Value | Notes |
|---|---:|---|
| Initial leg stake (`stake_amount`) | `$50` | Config-side. |
| DCA spacing | `-5%` from initial entry | Per-leg trigger price. |
| Max legs (initial + DCAs) | `5` | `max_entry_position_adjustment = 4`. |
| Take profit | `+8%` from running avg entry | Owned by `custom_exit`. |
| Hard stoploss (`stoploss`) | `-0.25` | Catastrophe stop, computed against running avg entry. |
| Time stop | `90 days` from initial open | Owned by `custom_exit`. |
| `minimal_roi` | `{"0": 100.0}` | TP handled by `custom_exit`; `minimal_roi` is effectively disabled to prevent it from competing with the +8% rule. |
| `max_open_trades` | `3` | Config-side; one ladder per pair. |

Rationale:
- **+8% TP, -25% stop = ~1:3.1 reward-to-risk** at the wallet level once
  all 5 legs are filled (8 / 25 = 0.32). Standard, deliberately
  unfavourable per-trade R:R for mean-reversion DCA: the strategy wins
  small and often on the TP path and loses big and rarely on the
  catastrophe-stop path. Tighter TPs produce more wins but bleed on the
  rare full-ladder loss; wider TPs reduce win rate without lifting
  expected value.
- **5 legs, -5% spacing** caps the price-range covered by a single
  ladder at -20% (initial entry → deepest leg). On BTC/ETH the realised
  20-day drawdown exceeded -20% only 3 times in the 2020-2025 window
  (2020-03 COVID, 2021-05 China ban, 2022-06 Luna/3AC). The 90-day
  time stop catches those.
- **90-day time stop** balances "give the ladder time to bounce" against
  "do not turn a -20% open position into a 6-month bag." 90 days is one
  realised business quarter; longer than typical crypto mean-reversion
  cycles and shorter than secular bear durations.
- **No hyperopt** because Sprint 27's research question is "does any
  entry signal produce profitable DCA-with-TP cycles at these
  pre-registered settings?" Tuning the DCA / TP / stop alongside the
  entry signal inflates the multiple-comparison problem and makes the
  walk-forward gate untestable.

## 27.5 Risk Doctrine for DCA-with-TP on Spot

The 1% equity-per-trade rule from
`docs/08-risk-and-position-sizing.md` is preserved with the same
re-interpretation as Sprint 25 §25.5: the 1% rule applies to
intraday-stop strategies where stops fire on noise. DCA ladders use the
stop as a *catastrophe* limit, not a trade-management tool.

Per-ladder risk envelope:

- Initial leg stake: $50.
- Max legs: 5.
- Max notional per ladder (all legs filled): `5 × $50 = $250`.
- Max wallet at risk at hard stop (-0.25 from avg entry on a fully
  filled ladder): approximately `$250 × 0.25 = $62.50 = 12.5% of $500`.
- Time-stop loss (worst realistic case before stop fires): if the
  ladder fills all 5 legs at avg entry of `-10%` and exits at
  `-15%` from initial entry at the 90-day mark: realised loss
  approximately `$250 × 0.067 = $16.75 = 3.4% of $500`.
- Max open ladders: 3 (one per pair). Max total wallet at risk:
  `3 × $62.50 = $187.50 = 37.5% of $500`. Conservative for a long-only
  spot lab.

Total stake at full deployment: `3 ladders × 5 legs × $50 = $750`. This
exceeds the `$500` wallet — meaning Freqtrade will only fill legs while
the wallet has free margin. In practice ladders cannot all be fully
loaded simultaneously; the realistic peak deployment is approximately
`10 legs × $50 = $500 = 100% of wallet` across all open ladders.

## 27.6 Validation Pipeline

Five steps. The acceptance gates at Step 1 and Step 3 are pre-registered
and **not negotiable** during execution. Same structure as Sprint 25
§25.6 with thresholds adjusted for the DCA trade shape.

### Step 1 — Same-window screen

For each strategy, run a single backtest over the full 2020-04-01 →
2025-12-01 window on the BTC/ETH/SOL universe.

**Acceptance:**

| Criterion | Required |
|---|---:|
| Total trades (closed ladders) across universe | ≥ 30 |
| Max drawdown (full-window) | < 30% |
| Total profit % (full-window) | > 0% (any positive return advances) |

> **Note.** "Trade" = one closed ladder, not one leg. A 5-leg ladder
> exiting at TP counts as a single trade. Per-pair entry rate for the
> three candidate signals is estimated 4–8 ladders per pair per year
> (RSI cross-ups: ~4, BB lower-band closes: ~6, EMA pullbacks: ~8).
> Over 5.7 years × 3 pairs = 17 pair-years, that puts the expected
> trade count in the 70–140 range — well above the ≥ 30 floor.

### Step 2 — Hyperopt sanity check (optional)

Skipped for Sprint 27. The pre-registered class attributes are not
hyperopt parameters by design (§27.4).

### Step 3 — Walk-forward validation

For each Step 1 survivor, run walk-forward with these windows:

- In-sample: 730 days (2 years)
- Out-of-sample: 180 days (6 months)
- Step: 180 days (6 months)
- Total OOS folds: approximately 7 complete folds across 5.7 years
  (the fold generator drops trailing incomplete OOS windows, same
  behaviour as Sprint 25 produced).

**Acceptance (4-criterion gate, identical thresholds to §25.6):**

| Criterion | Required |
|---|---:|
| Number of OOS folds with profit > 0 | ≥ 4 of `folds` (50% rounded up) |
| Average OOS Sharpe across all folds | > 0 |
| Average OOS total profit % across all folds | > 0% |
| Worst single OOS fold drawdown | ≤ 10% |

Strategies passing all four criteria advance to Step 4. Strategies
failing **any** criterion are rejected — no goalpost moving.

### Step 4 — Regime-filter experiments (conditional on Step 3 survivor)

Run only if any strategy clears Step 3. Apply
bull-only / bear-excluded / trending-only regime filters from
`user_data/regime/classifier.py` to the *entry signal* (not the DCA
mechanics) and re-run walk-forward. Compare filtered vs unfiltered to
see whether the regime filter lifts OOS Sharpe by ≥ 0.2.

### Step 5 — Paper-trade dry-run (conditional on Step 4 acceptance)

Run only if any regime-filtered survivor improves on the unfiltered
control by ≥ 0.2 OOS Sharpe. 4 weeks of `dry_run = true` paper trade on
`config-sprint27-dca.json`. Acceptance: realised P&L within ±50% of the
walk-forward simulation (long-hold DCA variance is wider than 5m).

## 27.7 Task Breakdown

> Canonical task IDs are the letters in `TASKS.md` (A–L + ESC).
> Cross-references in this document use those letters.
>
> **Hard gate at Step 1.** Tasks F–K run only on Step 1 survivors.
> If Step 1 rejects all three strategies, jump directly to Tasks G + L.
>
> **Hard gate at Step 3.** Tasks H–K run only on Step 3 survivors.

| Task | Owner tier | Depends on | Brief |
|---|---|---|---|
| A | Codex 5.4 low | — | Branch + confirm universe + window + pre-registered parameter table |
| B | Codex 5.4 low | A | Download 1d OHLCV for BTC/ETH/SOL over 2020-04-01 → 2025-12-01 |
| C | Codex 5.4 medium | A | Implement `DCASpotBase` + three concrete entry-signal subclasses + tests |
| D | Codex 5.4 medium | A | Build `config-sprint27-dca.json`; verify pair_whitelist and `position_adjustment_enable` |
| E | Antigravity Flash medium | C, D | Step 1 same-window backtest sweep across all three strategies |
| F | Antigravity Flash medium | E | Step 3 walk-forward for Step 1 survivors |
| G | Antigravity Flash high | E, F | Write `docs/28-spot-dca-results.md` |
| H | Antigravity Flash medium | F | (Conditional) Step 4 regime-filter experiments on Step 3 survivors |
| I | Antigravity Flash medium | H | (Conditional) Step 5 4-week paper-trade dry-run |
| J | Antigravity Flash medium | I | (Conditional) Extend `docs/28-spot-dca-results.md` with Step 4 + Step 5 results |
| K | Codex 5.4 low | F, J | (Conditional) Live deployment readiness checklist if any strategy clears Step 5 |
| L | Codex 5.4 low | all | Update `TASKS.md` at sprint end |
| ESC | Sonnet 4.6 Thinking | — | Escalation lane — design-level questions only |

**Cost ceiling.** ≈ 1 Codex 5.4 medium-day for C+D, ≈ 0.5 Codex 5.4
low-day for A+B+K+L, ≈ 2 Antigravity Flash medium-days for E+F+H+I, ≈ 1
Antigravity Flash high-day for G+J. No high-tier execution code is
required because this is dry-run-only spot trading on existing
infrastructure (Freqtrade backtest + walk-forward harness, both reused
unchanged from Sprint 25).

## 27.8 Kill Criterion

If **any of the following fires**, Sprint 27 is rejected and §27.8
applies:

1. All three strategies fail Step 1 (same-window screen).
2. All Step 1 survivors fail Step 3 (walk-forward acceptance).
3. The Step 4 regime filter does not lift any survivor's OOS Sharpe by
   ≥ 0.2.

§27.8 narrows the §25.8 escape hatches by one more option. Remaining
choices after Sprint 27 rejection:

- **Option A — FreqAI / ML on engineered features.** Still untested.
- **Option C — Stop the lab.** Honest answer if neither cash flow nor
  ML on engineered features is worth the added complexity.

There is no "try a different DCA variant" follow-up. Sprint 27 covers
the realistic entry-signal-for-DCA space (oversold mean reversion,
volatility-band mean reversion, bull-market dip-buy). If all three
reject, the DCA-with-TP-on-spot direction is exhausted and the broader
spot-strategy-search thread is closed.

## 27.9 Out of Scope

Explicit non-goals for Sprint 27:

- **Perps, futures, leverage.** Sprint 27 is spot-only. The
  `scripts/dca_futures_sim.py` tool merged in PR #52 is a reference
  utility; it is not invoked by any Sprint 27 task.
- **Variable DCA spacing / TP / stops.** Out of scope —
  pre-registered to isolate entry-signal quality (§27.4).
- **Hyperopt over any DCA parameter.** Strictly forbidden.
- **Wider universe.** Out of scope — survivorship risk on lower-cap
  assets breaks the mean-reversion assumption (§27.2.5).
- **More than 3 entry signals.** Three is enough to span the realistic
  "good entry" hypothesis space. Adding more inflates the
  multiple-comparison problem.
- **Real-money deployment.** Governed by `docs/07` §7.6 unchanged. Not
  invoked by any Sprint 27 task.
- **Window extension to pre-2020.** SOL listing date governs the
  earliest start; see §27.2.6.

---

Back to [docs/README.md](README.md).
