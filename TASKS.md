# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## Sprint Status

- [/] **Sprint 19: Pair universe expansion (top-20 USDT spot)**
  Eight strategies rejected so far on 4 majors. This sprint changes the pair
  universe (not the strategies, not the timeframe) to test whether the
  bottleneck is the over-served BTC/ETH/SOL/BNB market. Full plan in
  `docs/19-pair-universe-expansion.md`.

## Previous Sprint (done)

- [x] **Sprint 17: New hypotheses on higher timeframes** — see
  `docs/17-next-sprint-plan.md`. Both 1h candidates passed the same-window
  screen but failed walk-forward acceptance due to negative average
  out-of-sample profit. No strategy advanced. See
  `docs/18-1h-strategy-walk-forward.md`.

## Up Next

### Sprint 19 tasks (per-agent assignments)

> Full spec: `docs/19-pair-universe-expansion.md`. Tier rubric: cheap models
> for transcription, mid-tier for code-from-spec, high-tier only for design
> under ambiguity. Do **not** route any of these to Opus Thinking, Codex 5.5
> high+, or Devin without explicit escalation.

- [x] **A. Create feature branch + decide `max_open_trades` posture** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-19-top20` in the agent's worktree.
  - Per `docs/19-pair-universe-expansion.md` §19.4, default to Option A
    (`max_open_trades = 2`, peak ~66% concentration). Only override if there
    is an explicit reason — document the choice in this file's session log.
  - No code edits in this task beyond the config check.
  - Result: created `codex/sprint-19-top20`; kept Option A because
    `user_data/config.json` already has `max_open_trades = 2`.

- [x] **B. Build `scripts/build_universe.py`** — _Codex 5.4 medium_
  - Enumerate OKX USDT spot pairs (`GET /api/v5/market/tickers?instType=SPOT`).
  - Apply exclusions per `docs/19-pair-universe-expansion.md` §19.2.2
    (stablecoins, wrapped tokens, leveraged tokens, < 6 months OKX history).
  - Rank by **historical 30d quote volume ending 2024-07-01** (from local
    OHLCV in `user_data/data/okx/`, not from the live ticker volume field).
  - Write top-20 result to `user_data/universes/top20_okx_2024-07-01.json`.
  - CLI: `argparse`, `--help`, `--snapshot-date YYYY-MM-DD`, `--top N`.
  - Tests in `tests/test_build_universe.py`: mock OKX tickers + synthetic
    OHLCV, verify ranking + every exclusion rule.
  - Acceptance: `ruff check .` clean, `pytest` green.
  - Result: added `scripts/build_universe.py` plus tests covering parser help,
    OKX ticker parsing, stable/wrapped/leveraged/synthetic/history exclusions,
    historical-volume ranking, and JSON output. Verified `ruff check .` and
    `pytest` green.

- [x] **C. Run `build_universe.py`, commit the JSON, update `pair_whitelist`** — _Codex 5.4 low_
  - Run the script and inspect the output. Sanity check: BTC, ETH, SOL,
    BNB should appear; obvious stablecoins should not.
  - Commit `user_data/universes/top20_okx_2024-07-01.json` (this is
    metadata, not candle data — add to git, not gitignore).
  - Update `user_data/config.json` `pair_whitelist` to match.
  - Result: generated `user_data/universes/top20_okx_2024-07-01.json`
    from local 1d OKX OHLCV, confirmed BTC/ETH/SOL/BNB are present and
    obvious stablecoins are absent, and updated `pair_whitelist` to match.

- [x] **D. Download 5m candle data for the 16 new pairs** — _Antigravity Gemini Flash medium_
  ```bash
  freqtrade download-data -c user_data/config.json \
      --timeframes 5m \
      --timerange=20240701-20250501
  ```
  - With the updated `pair_whitelist`, this only fetches what's missing.
  - Data remains gitignored. Push the branch with the JSON + config changes only.
  - Result: ran the download for the top-20 whitelist over
    `20240701-20250501`; verified all 20 5m files cover from 2024-07-01
    through at least 2025-05-01. Candle data remains gitignored.

- [x] **E. Same-window baseline backtests** — _Antigravity Gemini Flash medium (after D)_
  - Run `scripts/run_baselines.py --strategies EMACrossover DonchianBreakout BollingerMeanReversion RSITrend MACDVolume --pairs <top20 from JSON> --timerange=20250101-20250501`.
  - **Screen: ≥ 50 trades and max drawdown < 30%** (raised from 20 per
    §19.6 Step 1).
  - Capture per-pair trade counts in the results doc; this informs follow-up
    sprints.
  - Result: ran the top-20 same-window sweep for `20250101-20250501`.
    `RSITrend` is the only Step 1 survivor (339 trades, 8.97% max drawdown).
    `EMACrossover` failed drawdown (1897 trades, 48.91% DD), `DonchianBreakout`
    failed drawdown (1250 trades, 40.23% DD), `BollingerMeanReversion` failed
    trade count (14 trades, 0.85% DD), and `MACDVolume` failed drawdown
    (3169 trades, 88.02% DD).
  - Per-pair trade counts:
    - `EMACrossover`: BTC 146, ETH 106, SOL 112, PEPE 121, TON 124, PEOPLE 107,
      DOGE 91, ORDI 99, TURBO 88, XRP 113, FIL 78, SUI 88, SHIB 73, FLOKI 67,
      WLD 87, NEAR 64, LTC 87, ENS 74, BNB 86, UNI 86.
    - `DonchianBreakout`: BTC 114, ETH 86, SOL 88, PEPE 55, TON 98, PEOPLE 75,
      DOGE 45, ORDI 73, TURBO 63, XRP 64, FIL 47, SUI 59, SHIB 37, FLOKI 34,
      WLD 46, NEAR 45, LTC 79, ENS 33, BNB 80, UNI 29.
    - `BollingerMeanReversion`: BTC 0, ETH 2, SOL 1, PEPE 1, TON 1, PEOPLE 1,
      DOGE 0, ORDI 0, TURBO 0, XRP 0, FIL 1, SUI 1, SHIB 0, FLOKI 0, WLD 1,
      NEAR 0, LTC 1, ENS 0, BNB 3, UNI 1.
    - `RSITrend`: BTC 18, ETH 18, SOL 20, PEPE 42, TON 20, PEOPLE 11,
      DOGE 23, ORDI 7, TURBO 13, XRP 20, FIL 17, SUI 14, SHIB 28, FLOKI 9,
      WLD 14, NEAR 12, LTC 15, ENS 12, BNB 12, UNI 14.
    - `MACDVolume`: BTC 237, ETH 207, SOL 206, PEPE 187, TON 193, PEOPLE 180,
      DOGE 137, ORDI 162, TURBO 174, XRP 144, FIL 146, SUI 149, SHIB 135,
      FLOKI 120, WLD 119, NEAR 122, LTC 164, ENS 125, BNB 133, UNI 129.

- [ ] **F. Walk-forward validation for screen survivors** — _Antigravity Gemini Flash medium (after E)_
  - For each strategy that passed Task E: run
    `scripts/walk_forward.py` with 90d/30d/30d windows over 2024-07-01 →
    2025-05-01.
  - Acceptance: ≥ 3 OOS folds, avg OOS Sharpe > 0, avg OOS profit > 0,
    no single fold drawdown > 5% (identical to docs/16 §16.3).
  - This is the largest single block of compute in the sprint. Budget
    accordingly; if any strategy passes Task E it can be walk-forwarded in
    parallel with the others.

- [ ] **G. Write results doc `docs/20-pair-universe-results.md`** — _Antigravity Gemini Flash high (after F)_
  - Follow the structure of `docs/18-1h-strategy-walk-forward.md` exactly.
  - Include: the universe selection (paste the JSON), per-strategy +
    per-pair Step 1 results, walk-forward per-fold tables for survivors,
    explicit pass/fail against §19.6 Step 3 acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table.

- [ ] **H. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after F, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` for each survivor.
  - This is the **only** legitimate place to evaluate regime gating.

- [ ] **I. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after G, only if any strategy passes acceptance)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.**

- [ ] **J. Update `TASKS.md`** at sprint end — _Codex 5.4 low_

- [ ] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - Surface any design-level question rather than deciding locally. Examples:
    "the universe-selection script is missing obvious pairs", "should we
    expand to top-50 because top-20 is too sparse?", "zero of five strategies
    passed Step 1 — the kill criterion from §19.8 triggers; should we go to
    FreqAI or perps next?".

---

### Sprint 17 tasks (done — archived for reference)

> Full spec was: `docs/17-next-sprint-plan.md`. Tier rubric: cheap models for
> transcription, mid-tier for code-from-spec, high-tier only for design under
> ambiguity. Do **not** route any of these to Opus Thinking, Codex 5.5 high+,
> or Devin without explicit escalation.

- [x] **A. Create feature branch + decide `max_open_trades` posture** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-1h-strategies` in the agent's worktree.
  - Per `docs/17-next-sprint-plan.md` §17.2.2, decide **Option A** (`max_open_trades = 2`, recommended)
    or **Option B** (keep `3`, document the 60% concentration here).
  - Edit `user_data/config.json` accordingly. Document the chosen option in this file's session log.

- [x] **B. Download 1h candle data** — _Antigravity Gemini Flash medium_
  ```bash
  freqtrade download-data -c user_data/config.json \
      --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
      --timeframes 1h \
      --timerange=20240701-20250501
  ```
  - Data is gitignored. Push the branch with config changes only; do not commit candles.

- [x] **C. Implement `MultiTimeframeTrend.py`** — _Codex 5.4 medium_
  - 1h primary timeframe with 4h informative pairs for trend confirmation.
  - RSI pullback-into-trend entry with volume filter.
  - Hyperopt-safe indicator caching (`for val in self.<param>.range`).
  - `stoploss = -0.05` as a class attribute (do **not** edit `config.json`).
  - See `docs/17-next-sprint-plan.md` §17.3 Strategy A for full spec.
  - New file: `user_data/strategies/MultiTimeframeTrend.py`.

- [x] **D. Implement `ATRAdaptiveMeanReversion.py`** — _Codex 5.4 medium_
  - 1h timeframe, ATR-adaptive entry distance instead of static Bollinger Bands.
  - Volatility contraction filter (ATR < median(ATR, 50)) + RSI < 35.
  - **No regime filter built into the strategy. No `use_regime_filter` hyperopt
    parameter.** Regime gating is evaluated separately in Task I.
  - `stoploss = -0.05` as a class attribute.
  - See `docs/17-next-sprint-plan.md` §17.3 Strategy B for full spec.
  - New file: `user_data/strategies/ATRAdaptiveMeanReversion.py`.

- [x] **E. Add smoke tests for both new strategies** — _Codex 5.4 low_
  - Import test (strategy class loads).
  - `populate_indicators`, `populate_entry_trend`, `populate_exit_trend` return
    DataFrames with expected columns.
  - Acceptance: `ruff check .` clean, `pytest` green.

- [x] **F. Same-window baseline backtests** — _Antigravity Gemini Flash medium (after C, D, E)_
  - Run `scripts/run_baselines.py --strategies MultiTimeframeTrend ATRAdaptiveMeanReversion --timerange=20250101-20250501`.
  - Screen: ≥ 20 trades **and** max drawdown < 30%.
  - Result: both strategies cleared the screen. `MultiTimeframeTrend`: 301 trades,
    -6.14% total profit, -8.08 Sharpe, 6.75% max drawdown. `ATRAdaptiveMeanReversion`:
    797 trades, -26.85% total profit, -48.24 Sharpe, 26.92% max drawdown.
  - If Strategy B fails **only** the trade-count screen, perform the **one**
    relaxation pass per `docs/17-next-sprint-plan.md` §17.4 Step 1 note
    (ATR < median → ATR < 75th percentile). Document the change in the results doc.

- [x] **G. Walk-forward validation for survivors** — _Antigravity Gemini Flash medium (after F)_
  - 3+ OOS folds, 90d in-sample / 30d out-of-sample / 30d step.
  - Range: `2024-07-01` → `2025-05-01`.
  - Acceptance: avg OOS Sharpe > 0, avg OOS profit > 0, max fold DD ≤ 5% (all four criteria from `docs/16` §16.3).
  - Result: both same-window survivors failed full acceptance. `MultiTimeframeTrend`
    completed 7 folds with avg OOS Sharpe 0.20, avg OOS profit -0.03%, and worst
    OOS drawdown 1.06%; it failed only average OOS profit. `ATRAdaptiveMeanReversion`
    completed 7 folds with avg OOS Sharpe -16.09, avg OOS profit -0.76%, and worst
    OOS drawdown 3.46%; it failed average OOS Sharpe and profit. No strategy advances
    to regime-filter experiments or paper trading from Task G.

- [x] **H. Write results doc `docs/18-*.md`** — _Antigravity Gemini Flash high (after G)_
  - Follow the structure of `docs/16-rsitrend-bullonly-multiwindow.md` exactly.
  - Include the trade-count screen result, any relaxation applied per Task F,
    walk-forward per-fold table, and explicit pass/fail against acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table with the new entry.
  - Result: added `docs/18-1h-strategy-walk-forward.md` and linked it from the
    docs index and AGENTS.md. Both 1h sprint candidates are documented as rejected.

- [x] **I. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after G, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` on each survivor.
  - This is the **only** legitimate place to evaluate regime gating.
  - Closed as not applicable: Task G produced no passing Step 3 survivors, so
    there are no legitimate strategies to run through regime-filter experiments.

- [x] **J. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after H, only if any strategy passes)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.** Live go/no-go is a separate sprint decision.
  - Closed as not applicable: Task G and docs/18 rejected both 1h candidates, so
    no strategy met the prerequisite for a 4-week dry-run. No paper-trade process
    was started.

- [x] **K. Update `TASKS.md`** at sprint end — _Codex 5.4 low_
  - Result: closed the 1h sprint, recorded that no strategy advances, and left
    the next research direction for a future hypothesis sprint.

- [x] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - If any task surfaces a design-level question (e.g., should we change the
    acceptance criteria? extend the sprint? swap pair universe?), stop and
    escalate here. Do **not** decide locally inside the assigned agent.
  - Closed unused: no design-level escalation surfaced during the sprint. The
    pre-registered acceptance criteria were applied without modification.

---

## Done

- [x] RSITrendBullOnly multi-window walk-forward validation
  - [x] Run 3-fold walk-forward sweep with prepended data back to 2024-10-01
  - [x] Document results in `docs/16-rsitrend-bullonly-multiwindow.md`
  - [x] Reject variant (avg OOS Sharpe -0.48, avg OOS profit -0.06%)
  - [x] Close second-pass task as not applicable
- [x] Regime Filter Experiments
  - [x] Apply the regime classifier to the strongest baseline strategy candidates
  - [x] Compare all-regime, bull-only, bear-excluded, and trending-only variants
  - [x] Validate any promising regime-filtered variant with walk-forward validation
  - [x] Keep the original baseline result as the control for every regime experiment
- [x] Strategy Comparison Report
  - [x] Create a strategy comparison report that aggregates baseline backtest and walk-forward results
  - [x] Rank strategies by out-of-sample performance, drawdown control, trade count, and fold stability
  - [x] Add a small parser/aggregation test if report generation becomes scripted
  - [x] Document the final baseline ranking and which strategy should receive the next research iteration
- [x] Walk-Forward Validation Sweep
  - [x] Run `scripts/walk_forward.py` for each baseline strategy that survives the initial backtest screen
  - [x] Compare in-sample vs out-of-sample Sharpe, drawdown, and total profit by fold
  - [x] Reject strategies with unstable out-of-sample results or drawdowns above the research risk tolerance
  - [x] Save CSV summaries and stability plots for later comparison
- [x] Baseline Strategy Validation
  - [x] Confirm/download 5m OHLCV data for BTC/USDT, ETH/USDT, SOL/USDT, and BNB/USDT for `20250101-20250501`
  - [x] Run same-window backtests for `EMACrossover`, `DonchianBreakout`, `BollingerMeanReversion`, `RSITrend`, and `MACDVolume`
  - [x] Record comparable metrics: trades, win rate, total profit %, Sharpe, max drawdown, and profit factor
  - [x] Identify which strategies are worth walk-forward validation
- [x] More baseline strategies
  - [x] Donchian breakout strategy
  - [x] Bollinger mean-reversion strategy
  - [x] RSI(14) + trend filter strategy
  - [x] MACD signal cross + volume strategy
- [x] Regime classifier (`user_data/regime/classifier.py`)
  - [x] EMA slope sign classifier
  - [x] ADX threshold classifier
  - [x] Expose single function returning regime label per bar
  - [x] Importable from any strategy's `populate_indicators`
- [x] Walk-forward harness (`scripts/walk_forward.py`)
  - [x] Accept strategy name, date range, window sizes, step size, loss function
  - [x] Implement fold window generation logic
  - [x] Run hyperopt per in-sample fold
  - [x] Run backtesting per out-of-sample fold
  - [x] Collect metrics (Sharpe, drawdown, total %) per fold
  - [x] Output CSV summary + fold-stability plot
  - [x] Add tests in `tests/test_walk_forward.py`
- [x] Initial scaffold — EMACrossover strategy, config, venv setup
- [x] Position sizing calculator (`risk/position_size.py`)
- [x] Binance Vision download script (`scripts/download_binance_vision.py`)
- [x] Test suite (`tests/test_position_size.py`, `tests/test_download_binance_vision.py`)
- [x] Comprehensive documentation (docs 01-12)
- [x] Multi-agent brain setup (AGENTS.md, TASKS.md, symlinks)
- [x] GitHub Actions CI workflow (.github/workflows/ci.yml)
  - [x] TA-Lib C library install step
  - [x] `pip install -r requirements-dev.txt`
  - [x] `ruff check .`
  - [x] `pytest`

---

## Session Log

| Date | Agent | Summary |
|------|-------|---------|
| 2026-05-21 | Devin | Initial scaffold: EMACrossover, risk calc, data scripts |
| 2026-05-21 | Devin | Comprehensive docs (01-12) |
| 2026-05-22 | Antigravity | Fixed Freqtrade environment setup (Python version) |
| 2026-05-23 | Antigravity | Added multi-agent brain (AGENTS.md, TASKS.md, symlinks) |
| 2026-05-23 | Antigravity | Reinstalled Codex CLI globally to resolve missing platform dependency |
| 2026-05-23 | Antigravity | Implemented GitHub Actions CI workflow with TA-Lib build and pytest/ruff checks |
| 2026-05-23 | Codex | Built walk-forward harness and updated docs/metadata for usage and generated outputs |
| 2026-05-23 | Codex | Reviewed and tightened CI triggers/cache before merge |
| 2026-05-23 | Codex | Implemented baseline strategies and regime classifier utility |
| 2026-05-23 | Codex | Queued validation, reporting, and regime-filter experiment tasks |
| 2026-05-23 | Antigravity | Automated and ran same-window baseline backtests, generated report, selected RSITrend/BollingerMeanReversion for walk-forward sweeps |
| 2026-05-23 | Codex | Fixed baseline validation CLI help behavior and added parser/report tests |
| 2026-05-23 | Antigravity | Ran walk-forward validation sweeps for RSITrend and BollingerMeanReversion, analyzed results and rejected both due to overfitting |
| 2026-05-24 | Codex | Extended strategy comparison report to include regime walk-forward result roots |
| 2026-05-23 | Codex | Reviewed walk-forward sweep branch and added committed results report |
| 2026-05-24 | Codex | Added scripted strategy comparison report and ranked baselines for next research iteration |
| 2026-05-24 | Codex | Implemented and ran regime-filter experiments; `RSITrendBullOnly` survived as weak research-only candidate |
| 2026-05-24 | Antigravity | Prepended OKX data starting from 2024-10-01, ran 3-fold walk-forward validation sweep for RSITrendBullOnly, and rejected it |
| 2026-05-24 | Codex | Documented RSITrendBullOnly multi-window validation in docs/16 and linked it from docs indexes |
| 2026-05-24 | Codex | Closed task D as not applicable because RSITrendBullOnly failed acceptance |
| 2026-05-26 | Antigravity | Closed RSITrendBullOnly sprint, wrote next sprint plan (docs/17), opened new sprint for 1h strategies |
| 2026-05-26 | Codex | Started `codex/sprint-1h-strategies`; chose Option A and set `max_open_trades = 2` for 40% peak concentration on 1h candidates |
| 2026-05-26 | Antigravity | Downloaded 1h candle data for BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT (2024-07-01 to 2025-05-01) |
| 2026-05-26 | Codex | Implemented `ATRAdaptiveMeanReversion` 1h ATR-gated mean-reversion baseline with no built-in regime filter |
| 2026-05-26 | Codex | Implemented `MultiTimeframeTrend` with 1h entries, 4h informative EMA-slope confirmation, RSI recovery logic, and volume filtering |
| 2026-05-26 | Codex | Added smoke tests for both 1h strategy classes and verified `ruff check .` plus `pytest` |
| 2026-05-26 | Codex | Ran same-window 1h baseline backtests for Task F; both strategies passed the trade-count/drawdown screen, and Strategy B needed no ATR relaxation |
| 2026-05-26 | Codex | Ran 7-fold walk-forward validation for `MultiTimeframeTrend` and `ATRAdaptiveMeanReversion`; both failed acceptance due to negative average OOS profit |
| 2026-05-26 | Codex | Documented the 1h strategy walk-forward rejection in docs/18 and linked it from docs/README.md and AGENTS.md |
| 2026-05-26 | Codex | Closed Task I as not applicable because Task G produced no passing Step 3 survivors for regime-filter experiments |
| 2026-05-26 | Codex | Closed Task J as not applicable because no strategy passed walk-forward acceptance for paper trading |
| 2026-05-26 | Codex | Closed the 1h sprint bookkeeping: Task K complete, escalation lane unused, no candidate advances |
| 2026-05-27 | Codex | Started `codex/sprint-19-top20`; chose Sprint 19 Option A and kept `max_open_trades = 2` for ~66% peak concentration |
| 2026-05-27 | Codex | Implemented Task B for Sprint 19: top-N OKX USDT universe builder with exclusion/ranking tests; verified ruff and pytest |
| 2026-05-27 | Codex | Completed Sprint 19 Task C: generated top-20 OKX universe JSON from local historical OHLCV and updated `pair_whitelist` |
| 2026-05-27 | Codex | Completed Sprint 19 Task D: downloaded and verified top-20 OKX 5m candles for 2024-07-01 through 2025-05-01 |
| 2026-05-27 | Codex | Completed Sprint 19 Task E same-window top-20 baseline sweep; only `RSITrend` passed the trade-count/drawdown screen |
