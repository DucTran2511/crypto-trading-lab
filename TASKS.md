# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## In Progress

_Nothing currently in progress._

## Up Next

### Walk-Forward Harness (Priority 1)
- [ ] Create `scripts/walk_forward.py`
  - [ ] Accept strategy name, date range, window sizes, step size, loss function
  - [ ] Implement fold window generation logic
  - [ ] Run hyperopt per in-sample fold
  - [ ] Run backtesting per out-of-sample fold
  - [ ] Collect metrics (Sharpe, drawdown, total %) per fold
  - [ ] Output CSV summary + fold-stability plot
  - [ ] Add tests in `tests/test_walk_forward.py`

### GitHub Actions CI (Priority 2)
- [ ] Create `.github/workflows/ci.yml`
  - [ ] TA-Lib C library install step
  - [ ] `pip install -r requirements-dev.txt`
  - [ ] `ruff check .`
  - [ ] `pytest`

### More Baseline Strategies (Priority 3)
- [ ] Donchian breakout strategy
- [ ] Bollinger mean-reversion strategy
- [ ] RSI(14) + trend filter strategy
- [ ] MACD signal cross + volume strategy

### Regime Classifier (Priority 4)
- [ ] Create `user_data/regime/classifier.py`
  - [ ] EMA slope sign classifier
  - [ ] ADX threshold classifier
  - [ ] Expose single function returning regime label per bar
  - [ ] Importable from any strategy's `populate_indicators`

---

## Done

- [x] Initial scaffold — EMACrossover strategy, config, venv setup
- [x] Position sizing calculator (`risk/position_size.py`)
- [x] Binance Vision download script (`scripts/download_binance_vision.py`)
- [x] Test suite (`tests/test_position_size.py`, `tests/test_download_binance_vision.py`)
- [x] Comprehensive documentation (docs 01-12)
- [x] Multi-agent brain setup (AGENTS.md, TASKS.md, symlinks)

---

## Session Log

| Date | Agent | Summary |
|------|-------|---------|
| 2026-05-21 | Devin | Initial scaffold: EMACrossover, risk calc, data scripts |
| 2026-05-21 | Devin | Comprehensive docs (01-12) |
| 2026-05-22 | Antigravity | Fixed Freqtrade environment setup (Python version) |
| 2026-05-23 | Antigravity | Added multi-agent brain (AGENTS.md, TASKS.md, symlinks) |
