# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## In Progress

_Nothing currently in progress._

## Up Next

_Nothing currently queued._

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
