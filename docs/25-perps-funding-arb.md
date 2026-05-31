# 25. Sprint Plan — Perps + Funding-Rate Arbitrage (cash-and-carry, OKX)

## 25.1 Context

After 19 rejected indicator-on-OKX-spot variants across 5m / 1h / 1d
timeframes, two universes (4 majors + top-20 USDT spot), and dynamic
pair selection (Sprint 21 daily momentum), the indicator hypothesis space is
exhausted. `docs/23-higher-timeframe-sweep.md` §23.8 fired definitively after
Sprint 23 with no further escape hatches.

This sprint changes hypothesis category entirely. The edge being tested is
**not** "predict price direction with an indicator." It is **cash flow from
the funding-rate premium** paid by the long side of a perpetual futures
contract when the perp trades above spot. Specifically:

> **Cash-and-carry on perps.** When OKX perp funding > 0, the long side pays
> the short side every 8 hours. A delta-neutral position — long $X of spot,
> short $X notional of perp — earns the funding payment while having near-zero
> directional exposure. The position closes when either (a) funding flips
> negative, (b) the basis blows out, or (c) a circuit breaker fires.

This is **not directional alpha**. It is a structural cash flow from
overconfident long-leverage traders, mediated by the exchange. It is harder to
arbitrage away than indicator alpha for two reasons:

1. The supply of leveraged long demand is approximately permanent in crypto
   bull markets — funding rates have been net positive on BTC/ETH perps for
   the majority of the last 4 years.
2. The capital required is meaningful — every $1 of funding capture requires
   $1 of spot collateral *and* $1 of perp margin. Capital efficiency is much
   lower than for pure indicator strategies, which is why retail bots don't
   compete it down.

### 25.1.1 Why not directional perps trading

This sprint is **not** about trading perps directionally. Going long perps in
isolation is just leverage on top of the same indicator hypothesis already
rejected 19 times. The whole point of the cash-and-carry construction is to
**hedge out the directional exposure** so the funding payment is the only
remaining P&L source.

### 25.1.2 Why OKX (and not Binance / Bybit)

OKX is the existing exchange for the lab. Spot pairs, fee structure, and
historical OHLCV are already on disk. Sprint 25 stays on OKX for continuity.
Binance / Bybit can be a follow-up cross-exchange comparison in a future
sprint *only if* OKX Tier 1 produces a positive result.

## 25.2 Scope and Tiering

Three tiers with hard gates between them. The point of the tiering is to
**buy down risk before deploying capital**: each tier is a self-contained
go/no-go decision.

### 25.2.1 Tier 1 — Historical edge analysis (read-only, no real money)

**Hypothesis:** OKX perp funding rates on BTC/USDT-SWAP and ETH/USDT-SWAP,
over the last 24 months, net of realistic fees and slippage, produced a
positive simulated return on a $500 cash-and-carry position.

**Implementation:**

- Scrape OKX `GET /api/v5/public/funding-rate-history` for BTC-USDT-SWAP and
  ETH-USDT-SWAP, 2024-01-01 → 2025-12-01 (24 months ending recent). Stored to
  `user_data/funding_rates/<inst>-funding-history.json`.
- Scrape OKX `GET /api/v5/market/history-index-candles` (perp mark price) and
  the existing `1d` spot candles for the same window.
- Compute the simulated cash-and-carry P&L day-by-day:
  - Position size: $250 spot long + $250 perp short notional, opened when
    funding > 0 and basis (spot - perp price) is within ±0.5%.
  - Hold while funding > 0 AND basis stays within ±2%.
  - Close when funding ≤ 0 OR basis blows out.
  - Fees: OKX spot taker 0.08% per leg per direction. OKX perp taker 0.05%
    per leg per direction. Round-trip total per position = 0.26%.
  - Slippage: 0.05% per leg per direction added as a conservative buffer
    (cash-and-carry positions are small enough not to move the market on
    BTC/ETH but the worst-case is what matters).
- No leverage on the spot leg. Perp leg uses 1× margin (notional = collateral).

**Output:** `docs/26-perps-funding-arb-results.md` §26.2 with per-month and
aggregate return tables for both instruments.

**Acceptance (pre-registered, do not move the goalposts):**

| Criterion | Required |
|---|---:|
| Simulated net APY (BTC-USDT-SWAP) | > +5% net of all fees + slippage |
| Simulated net APY (ETH-USDT-SWAP) | > +5% net of all fees + slippage |
| Worst rolling 30d drawdown across both | < 3% |
| Negative-funding episodes per year | ≤ 4 (otherwise position management complexity dominates) |

> **Note.** The 5% threshold is intentional. Sprint 25 needs a margin of
> safety vs. its expected real-world friction (margin calls, exchange
> outages, basis-blow-up handling, withdrawal delays). A historical edge
> of 3% APY is *probably* not enough to survive those frictions.

### 25.2.2 Tier 2 — Paper-trade infrastructure (conditional on Tier 1 acceptance)

**Run only if both BTC and ETH cleared Tier 1.** If either fails, Tier 2 is
skipped and §25.8 fires.

**Implementation:**

- `scripts/funding_arb_paper_trade.py`: dry-run paired-leg position manager.
  Opens both legs simultaneously, monitors basis + funding, closes both legs
  on circuit breakers.
- Circuit breakers (pre-registered, hard rules, no override):
  1. **Funding flip:** funding rate ≤ 0 for any 8h period → close both legs.
  2. **Basis blow-up:** abs(spot - perp) / spot > 1% → close both legs.
  3. **Spot leg failure:** spot order does not fill within 60s of perp fill
     → close perp immediately, alert.
  4. **Perp leg failure:** perp order does not fill within 60s of spot fill
     → close spot immediately, alert.
  5. **Daily P&L drawdown:** -1% on the position day → close both legs.
- **No real money.** All execution is OKX testnet OR paper-trade book with
  `dry_run = true`. The `user_data/config.json` `dry_run_wallet = 500`
  remains.
- 4 weeks of continuous paper-trade execution. Per-day P&L tracked vs Tier 1
  expectation.

**Acceptance:**

| Criterion | Required |
|---|---:|
| Paper-trade weeks completed | ≥ 4 |
| Per-week realized P&L vs Tier 1 simulation | within ± 30% |
| Circuit breaker false-positive count | 0 (any false-positive is a code bug, fix and re-run) |
| Unhandled exception count | 0 |
| Number of legs that closed naked (basis > 1% during exit) | 0 |

### 25.2.3 Tier 3 — Real money (NOT in this sprint)

**Explicitly out of scope for Sprint 25.** Tier 3 is the *next* sprint after
Sprint 25 closes, contingent on Sprint 25 Tier 2 passing all acceptance
criteria. The decision to deploy real money is governed by
`docs/07-paper-and-live-trading.md` §7.6 unchanged.

> **Hard rule.** No live capital touches OKX during Sprint 25 regardless of
> what Tier 1 / Tier 2 results show. Even if Tier 1 shows +20% APY and
> Tier 2 runs flawlessly for 4 weeks, the real-money decision is its own
> sprint with its own pre-registered acceptance.

### 25.2.4 Explicitly skipped

| Cell | Why skipped |
|---|---|
| SOL/USDT-SWAP, BNB/USDT-SWAP, alt perps | Funding rate is more volatile on alts. Start with the two largest, lowest-spread instruments. Future sprint can extend if Tier 1 + Tier 2 succeed. |
| Cross-exchange basis (OKX vs Binance) | Adds counterparty + transfer-latency complexity. Strictly out of scope for Sprint 25. |
| Triangular arb, stat arb, market making | Different hypothesis categories. Not relevant to this sprint. |
| Leverage > 1× on the perp leg | Defeats the delta-neutral construction (margin call on a 5× short leg can occur even with a 20% spot drop). |
| Negative-funding short basis trades (short spot, long perp) | Spot borrow cost on OKX is non-trivial and erodes the funding capture. Only positive-funding trades are in scope. |

## 25.3 Implementation Files

### 25.3.1 New files (Task B + Task H)

- `scripts/scrape_okx_funding_rates.py` (Task B): scraper for
  `/api/v5/public/funding-rate-history`. CLI with `--inst`, `--start`,
  `--end`, `--out`. Idempotent (re-running over an existing JSON file
  appends new rows only). Tests with mocked HTTP.
- `scripts/simulate_funding_arb.py` (Task C): Tier 1 historical simulator.
  Reads funding history + spot candles + perp candles. Outputs a P&L
  time-series CSV + summary statistics matching the §25.2.1 acceptance
  table. Tests with synthetic funding + price data.
- `scripts/funding_arb_paper_trade.py` (Task H, conditional): Tier 2
  paired-leg paper-trade execution. Uses Freqtrade's exchange wrapper for
  authenticated OKX testnet calls. Implements the §25.2.2 circuit breakers
  exactly.

### 25.3.2 Files NOT being created

- **No new Freqtrade strategy.** Cash-and-carry is not a single-leg, single
  -timeframe strategy. Freqtrade's `IStrategy` interface assumes one entry
  → one exit per pair; cash-and-carry needs paired-leg coordination.
- **No new `user_data/strategies/*.py`.** The infrastructure lives in
  `scripts/` because it is paired-leg execution logic, not strategy logic.
- **No FreqAI configuration.** Tier 1 is a deterministic simulation; Tier 2
  is rule-based execution. Neither needs ML.

## 25.4 Configuration

`user_data/config.json` changes required for **Tier 2 only** (Tier 1 is
read-only HTTP scraping):

- Add OKX testnet API credentials via `user_data/config-testnet.json`
  (separate file, never committed). Tier 2 reads from this file via the
  `--config` flag.
- `dry_run` remains `true` even on testnet — the paired-leg manager treats
  testnet as a dry-run-equivalent.
- `dry_run_wallet` stays at $500. Per-position size = $250 + $250 = $500
  paired notional. **Only one position open at a time** for the full
  duration of Sprint 25.

The committed `user_data/config.json` is NOT modified by this sprint.

## 25.5 Risk Doctrine for Cash-and-Carry

The 1% equity-per-trade rule from `docs/08-risk-and-position-sizing.md` is
re-interpreted for paired-leg positions:

- A "trade" is one cash-and-carry *position* (both legs together).
- Equity-per-trade risk = the maximum P&L drawdown the position can absorb
  before circuit breakers force-close it, divided by total equity.
- At $500 equity with $250 + $250 paired notional and the §25.2.2 -1%
  per-day daily drawdown breaker, max single-trade risk = $5 = 1% of equity.

> **Note.** This is mathematically equivalent to the existing 1% rule. The
> circuit breaker is the position-sizing mechanism.

## 25.6 Validation Pipeline

Identical structure to prior sprints, but the per-tier acceptance criteria
are pre-registered in §25.2 because the question being asked is different
(cash flow vs walk-forward signal).

### Step 1 — Tier 1 historical simulation
- Pre-registered acceptance: §25.2.1 table.
- If any criterion fails: §25.8 kill criterion fires.

### Step 2 — Tier 2 paper-trade infrastructure
- Conditional on Step 1 passing.
- Pre-registered acceptance: §25.2.2 table.
- If any criterion fails: §25.8 kill criterion fires.

### Step 3 — Live deployment (NEXT sprint, not this one)
- Out of scope for Sprint 25. Gated on a separate sprint plan to be written
  only if Steps 1 + 2 pass.

## 25.7 Task Breakdown

> Canonical task IDs are the letters in `TASKS.md` (A–L + ESC).
> Cross-references in this document use those letters.
>
> **Hard gates:** Tasks D + E + F + G run only if Task C produces ≥ 5% APY
> on both BTC + ETH. Tasks H + I + J + K run only if all four of Tier 1
> §25.2.1 criteria pass.

| Task | Owner tier | Depends on | Brief |
|---|---|---|---|
| A | Codex 5.4 low | — | Branch + confirm Tier 1 instrument list (BTC-USDT-SWAP, ETH-USDT-SWAP) and 24m window |
| B | Codex 5.4 medium | A | `scripts/scrape_okx_funding_rates.py` + tests |
| C | Codex 5.4 medium | A | `scripts/simulate_funding_arb.py` + tests |
| D | Antigravity Flash medium | B | Run scraper, commit `user_data/funding_rates/*.json` |
| E | Antigravity Flash medium | C, D | Run Tier 1 simulation for BTC + ETH; produce summary tables |
| F | Antigravity Flash high | E | Write `docs/26-perps-funding-arb-results.md` Tier 1 section |
| G | Codex 5.4 low | F | If Tier 1 fails: invoke §25.8 and skip H–K |
| H | Codex 5.4 high | F (conditional on Tier 1 acceptance) | `scripts/funding_arb_paper_trade.py` + tests |
| I | Antigravity Flash medium | H | 4-week paper-trade execution on OKX testnet |
| J | Antigravity Flash high | I | Write `docs/26-perps-funding-arb-results.md` Tier 2 section |
| K | Codex 5.4 low | J | Sprint closeout in `TASKS.md` + decide on Tier 3 next-sprint trigger |
| L | Codex 5.4 low | all | Update `TASKS.md` at sprint end |
| ESC | Sonnet 4.6 Thinking | — | Escalation lane — design-level questions only |

**Cost ceiling.** ≈ 1 Codex 5.4 medium-day for B+C, ≈ 1 Codex 5.4 high-day
for H (the only high-tier slot, justified by paired-leg exchange execution
risk), ≈ 0.5 Codex 5.4 low-day for A+G+K+L, ≈ 2.5 Antigravity Flash medium-
days for D+E+I, ≈ 1 Antigravity Flash high-day for F+J.

> **Why Task H is Codex 5.4 high, not medium.** Paired-leg exchange
> execution against a real API (even testnet) is the highest-blast-radius
> code in any sprint to date. A bug in the circuit breakers means a leg
> closes naked; a bug in the order sequencing means the perp fills before
> the spot and the position is briefly directional. This is the one place
> in the sprint where saving model cost is not worth the risk.

## 25.8 Kill Criterion

If **Tier 1 historical simulation fails any §25.2.1 acceptance criterion**
OR **Tier 2 paper-trade execution fails any §25.2.2 acceptance criterion**,
the cash-and-carry hypothesis is rejected.

At that point, the §23.8 escape hatches have been narrowed by one more
option. The remaining choices are:

- **Option A — FreqAI / ML on engineered features.** Still available; not
  attempted yet.
- **Option C — Stop the lab.** Honest answer if the research muscle and the
  pipeline are the deliverable.

There is no "try a different perps direction" follow-up. The cash-and-carry
construction is the most-conservative perps strategy that exists; if it
fails on BTC + ETH with the most-liquid funding history, every other perps
direction is strictly harder.

## 25.9 Out of Scope

- **Real money in Sprint 25.** Tier 3 is the next sprint after this one
  closes, gated on Tier 1 + Tier 2 acceptance.
- **Alt perps (SOL, BNB, mid-caps).** Future-sprint extension only.
- **Cross-exchange basis.** Future-sprint extension only.
- **Negative-funding short basis.** Spot borrow cost makes this
  economically marginal on OKX; out of scope per §25.2.4.
- **Higher leverage on the perp leg.** Defeats the delta-neutral
  construction per §25.2.4.
- **Triangular arb, stat arb, market making.** Different categories of
  hypothesis. Not in scope.
- **Live deployment decision.** Governed by
  `docs/07-paper-and-live-trading.md` §7.6 unchanged.

[Back to docs index](README.md)
