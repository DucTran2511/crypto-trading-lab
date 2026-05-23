# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## In Progress

_Nothing currently in progress._

## Up Next

### Baseline Strategy Validation (Priority 1)
- [ ] Confirm/download 5m OHLCV data for BTC/USDT, ETH/USDT, SOL/USDT, and BNB/USDT for `20250101-20250501`
- [ ] Run same-window backtests for `EMACrossover`, `DonchianBreakout`, `BollingerMeanReversion`, `RSITrend`, and `MACDVolume`
- [ ] Record comparable metrics: trades, win rate, total profit %, Sharpe, max drawdown, and profit factor
- [ ] Identify which strategies are worth walk-forward validation

### Walk-Forward Validation Sweep (Priority 1)
- [ ] Run `scripts/walk_forward.py` for each baseline strategy that survives the initial backtest screen
- [ ] Compare in-sample vs out-of-sample Sharpe, drawdown, and total profit by fold
- [ ] Reject strategies with unstable out-of-sample results or drawdowns above the research risk tolerance
- [ ] Save CSV summaries and stability plots for later comparison

### Strategy Comparison Report (Priority 2)
- [ ] Create a strategy comparison report that aggregates baseline backtest and walk-forward results
- [ ] Rank strategies by out-of-sample performance, drawdown control, trade count, and fold stability
- [ ] Add a small parser/aggregation test if report generation becomes scripted
- [ ] Document the final baseline ranking and which strategy should receive the next research iteration

### Regime Filter Experiments (Priority 3)
- [ ] Apply the regime classifier to the strongest baseline strategy candidates
- [ ] Compare all-regime, bull-only, bear-excluded, and trending-only variants
- [ ] Validate any promising regime-filtered variant with walk-forward validation
- [ ] Keep the original baseline result as the control for every regime experiment

---

## Done

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
