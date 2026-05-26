# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## In Progress

- [/] **Sprint: New hypotheses on higher timeframes**
  All 5m single-timeframe strategies rejected. Shifting to 1h primary timeframe
  with two structurally different approaches. Full plan in
  `docs/17-next-sprint-plan.md`.

## Up Next

### Sprint tasks (per-agent assignments)

> Full spec: `docs/17-next-sprint-plan.md`. Tier rubric: cheap models for
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

- [ ] **F. Same-window baseline backtests** — _Antigravity Gemini Flash medium (after C, D, E)_
  - Run `scripts/run_baselines.py --strategies MultiTimeframeTrend ATRAdaptiveMeanReversion --timerange=20250101-20250501`.
  - Screen: ≥ 20 trades **and** max drawdown < 30%.
  - If Strategy B fails **only** the trade-count screen, perform the **one**
    relaxation pass per `docs/17-next-sprint-plan.md` §17.4 Step 1 note
    (ATR < median → ATR < 75th percentile). Document the change in the results doc.

- [ ] **G. Walk-forward validation for survivors** — _Antigravity Gemini Flash medium (after F)_
  - 3+ OOS folds, 90d in-sample / 30d out-of-sample / 30d step.
  - Range: `2024-07-01` → `2025-05-01`.
  - Acceptance: avg OOS Sharpe > 0, avg OOS profit > 0, max fold DD ≤ 5% (all four criteria from `docs/16` §16.3).

- [ ] **H. Write results doc `docs/18-*.md`** — _Antigravity Gemini Flash high (after G)_
  - Follow the structure of `docs/16-rsitrend-bullonly-multiwindow.md` exactly.
  - Include the trade-count screen result, any relaxation applied per Task F,
    walk-forward per-fold table, and explicit pass/fail against acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table with the new entry.

- [ ] **I. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after G, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` on each survivor.
  - This is the **only** legitimate place to evaluate regime gating.

- [ ] **J. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after H, only if any strategy passes)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.** Live go/no-go is a separate sprint decision.

- [ ] **K. Update `TASKS.md`** at sprint end — _Codex 5.4 low_

- [ ] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - If any task surfaces a design-level question (e.g., should we change the
    acceptance criteria? extend the sprint? swap pair universe?), stop and
    escalate here. Do **not** decide locally inside the assigned agent.

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
