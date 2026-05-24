# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## In Progress

- [ ] **Sprint: Multi-window walk-forward validation of `RSITrendBullOnly`**
  Single-fold evidence in `docs/15-regime-filter-experiments.md` is too weak to
  act on (+0.02% OOS profit, 0.25 OOS Sharpe). Need at least 3 OOS folds before
  the variant survives as even a "weak research candidate." See per-agent task
  assignments below.

## Up Next

### Sprint tasks (per-agent assignments)

- [ ] **A. Run the multi-window walk-forward sweep** — _suggested agent: Antigravity Gemini Flash medium_
  - Pre-req: `RSITrendBullOnly` strategy file exists at
    `user_data/regime_filter_results/generated_strategies/RSITrendBullOnly.py`
    (regenerate via `scripts/regime_filter_experiments.py` if needed).
  - Run:
    ```bash
    python scripts/walk_forward.py \
        --strategy RSITrendBullOnly \
        --strategy-path user_data/regime_filter_results/generated_strategies \
        --start 2025-01-01 --end 2025-05-01 \
        --in-sample 90d --out-sample 30d --step 30d \
        --loss SharpeHyperOptLoss --epochs 100 \
        --spaces buy sell \
        --output-dir user_data/walk_forward_results/RSITrendBullOnly \
        --freqtrade-bin .venv/bin/freqtrade
    ```
  - Deliverable: `user_data/walk_forward_results/RSITrendBullOnly/`
    contains `walk_forward_summary.csv`, `walk_forward_stability.png`, and the
    per-fold params/logs/backtest exports. Push the branch but do not commit
    those generated artefacts — they remain gitignored.

- [x] **B. Extend `scripts/compare_strategies.py`** — _suggested agent: Codex 5.4 medium_
  - Add an optional `--regime-walk-forward-root` argument (default
    `user_data/regime_filter_results/walk_forward`) that picks up
    `*/walk_forward_summary.csv` files and includes them in the comparison
    ranking alongside the baseline strategies.
  - Add at least one test in `tests/test_compare_strategies.py` that exercises
    the new flag.
  - Acceptance: `ruff check .` clean, `pytest` green.

- [ ] **C. Write `docs/16-rsitrend-bullonly-multiwindow.md`** — _suggested agent: Antigravity Gemini Flash high (after A finishes)_
  - Structure: 16.1 Scope · 16.2 Per-fold results table · 16.3 Acceptance criteria · 16.4 Decision · 16.5 Next step.
  - Explicit acceptance criteria (commit these to the doc up front, do not move the goalposts after the run):
    1. ≥3 out-of-sample folds completed.
    2. Average OOS Sharpe > 0.
    3. Average OOS total profit > 0.
    4. No single OOS fold drawdown > 5%.
  - All four must hold to mark the variant as "keep researching." Anything weaker → reject.
  - Add the new doc to the `docs/README.md` index and to the AGENTS.md docs table.

- [ ] **D. If A passes acceptance** — _suggested agent: Sonnet 4.6 Thinking or Codex 5.5 high_
  - Design a second validation pass (different timerange, longer in-sample
    window, or a different pair subset). Do NOT advance to paper trading on a
    single-sprint result. Write a short proposal in `docs/16-...md` §16.5 with
    the proposed second-pass parameters and rejection criteria.

- [ ] **E. Update `TASKS.md`** at sprint end — _any agent_

---

## Done

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
