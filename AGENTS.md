# AGENTS.md — crypto-trading-lab

## Project Overview

A Freqtrade-based crypto trading research lab for researching, backtesting, and
(eventually) paper- or live-trading crypto strategies on spot markets.

**Stage:** Early research pipeline. The default `EMACrossover` strategy is an
intentionally *losing* baseline — the point is a working pipeline, not a
profitable bot. Real edge comes from walk-forward validation and regime filtering.

**Repo:** `DucTran2511/crypto-trading-lab`

---

## Tech Stack

- **Python 3.11+** (venv at `.venv/`)
- **Freqtrade 2025.6** (pinned in `requirements.txt`)
- **TA-Lib** C library required at OS level (see `docs/01-setup.md` §1.2)
- **pandas 2.2.3**, **pyarrow 16.1.0**, **requests 2.32.3**
- **ruff** for linting (`pyproject.toml`: line-length 100, target py311)
- **pytest** for testing (`tests/` directory, `-ra -q` default)
- **Jupyter** notebooks for research (`user_data/notebooks/`)
- **Exchange:** OKX spot (dry-run mode) as default data source

---

## Key Commands

```bash
# Activate environment
source .venv/bin/activate

# Lint
ruff check .

# Test
pytest

# Backtest (example: 4 months of 5m candles)
freqtrade backtesting -c user_data/config.json \
    --strategy EMACrossover \
    --timerange=20250101-20250501

# Download data
freqtrade download-data -c user_data/config.json \
    --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
    --timeframes 5m \
    --timerange=20250101-20250501

# Hyperopt (parameter optimization)
freqtrade hyperopt -c user_data/config.json \
    --strategy EMACrossover \
    --hyperopt-loss SharpeHyperOptLoss \
    --spaces buy -e 100 \
    --timerange=20250101-20250501

# Walk-forward validation
python scripts/walk_forward.py \
    --strategy EMACrossover \
    --start 2025-01-01 --end 2025-05-01 \
    --in-sample 90d --out-sample 30d --step 30d \
    --loss SharpeHyperOptLoss --epochs 100

# Position sizing calculator
python -m risk.position_size --equity 500 --entry 65000 --stop 63050 --risk-pct 0.01

# Paper trade
freqtrade trade -c user_data/config.json --strategy EMACrossover
```

---

## Project Structure

```
crypto-trading-lab/
├── user_data/
│   ├── config.json                  # Freqtrade config (OKX spot, dry-run, $500 wallet)
│   ├── strategies/
│   │   ├── AGENTS.md                # Strategy-folder conventions
│   │   ├── EMACrossover.py          # Tunable fast/slow EMA crossover w/ trend filter
│   │   ├── DonchianBreakout.py      # Donchian-channel breakout w/ volume + EMA trend filter
│   │   ├── BollingerMeanReversion.py # BB lower-band dip-buy w/ RSI + optional trend filter
│   │   ├── RSITrend.py              # RSI(14) pullback w/ long-term EMA trend filter
│   │   └── MACDVolume.py            # MACD signal cross w/ volume confirmation
│   ├── regime/
│   │   ├── __init__.py
│   │   └── classifier.py            # ADX + EMA-slope regime labels (bull/bear/range)
│   └── notebooks/
│       └── research_template.ipynb  # Vectorised research starter
├── scripts/
│   ├── AGENTS.md                    # Scripts-folder conventions
│   ├── download_binance_vision.py   # Pull OHLCV from data.binance.vision
│   ├── walk_forward.py              # Hyperopt/backtest walk-forward harness
│   ├── run_baselines.py             # Same-window backtest sweep across baselines
│   ├── compare_strategies.py        # Aggregate baseline + walk-forward results → ranking
│   └── regime_filter_experiments.py # Generate + backtest regime-filtered variants
├── risk/
│   ├── __init__.py
│   └── position_size.py             # CLI position-sizing calculator
├── tests/                           # pytest mirror of source structure (44+ tests)
│   ├── test_position_size.py
│   ├── test_download_binance_vision.py
│   ├── test_walk_forward.py
│   ├── test_run_baselines.py
│   ├── test_compare_strategies.py
│   ├── test_regime_classifier.py
│   └── test_regime_filter_experiments.py
├── docs/                            # Numbered 01-16, long-form documentation
├── .github/workflows/ci.yml         # GitHub Actions: TA-Lib build + ruff + pytest
├── AGENTS.md                        # This file. CLAUDE.md, GEMINI.md symlink here.
├── TASKS.md                         # Current sprint + session log
├── requirements.txt                 # Production deps (pinned)
├── requirements-dev.txt             # + linter, pytest, jupyter, matplotlib
└── pyproject.toml                   # ruff + pytest config
```

---

## Coding Conventions

- **Strategies** inherit from `IStrategy` (Freqtrade base class)
- Use `IntParameter` / `DecimalParameter` for all hyperopt-tunable values
- Ruff lint rules: `E, F, I, B, UP, W` (ignore `E501`)
- Line length: 100 characters
- One strategy per file in `user_data/strategies/`
- Scripts use `argparse` and include `--help` with clear descriptions
- Tests mirror source structure: `risk/` → `tests/test_position_size.py`
- Keep strategies self-contained (no cross-strategy imports)
- Use type hints where practical

---

## Current Status & Roadmap

**Last milestone:** Multi-window validation of `RSITrendBullOnly` complete. The
variant failed the 3-fold acceptance criteria with negative average OOS Sharpe
and profit, so it is rejected. See `docs/16-rsitrend-bullonly-multiwindow.md`.

**Current sprint:** Close out the `RSITrendBullOnly` validation sprint and return
to new research hypotheses.
**See `TASKS.md` for active tasks and per-agent assignments.**

Roadmap priority (from `docs/11-roadmap.md`):
1. Form a new strategy or filter hypothesis; `RSITrendBullOnly` is rejected.
2. Validate any new candidate with same-window screening and walk-forward tests.
3. Switch live data to Binance.vision as default.
4. Live monitoring stack (logs, Telegram, heartbeat).
5. Paper-trade validation (4+ weeks).
6. Live micro-size deployment.

---

## Critical Rules — Do NOT

- **Never** modify exchange credentials in `user_data/config.json`
- **Never** commit candle data (`user_data/data/` is gitignored)
- **Never** use leverage — spot only
- **Never** skip walk-forward validation when claiming a strategy "works"
- **Never** risk more than 1% of equity per trade
- **Never** commit `.env` or private config files
- **Never** hardcode API keys or secrets anywhere

---

## Documentation

Full docs in `docs/` (read in order):

| # | File | Topic |
|---|------|-------|
| 01 | `docs/01-setup.md` | Python, TA-Lib, Docker setup |
| 02 | `docs/02-quickstart.md` | Clone → backtest in 10 min |
| 03 | `docs/03-strategy.md` | EMACrossover line-by-line |
| 04 | `docs/04-data.md` | Data sources and download |
| 05 | `docs/05-backtesting.md` | Running and interpreting backtests |
| 06 | `docs/06-hyperopt.md` | Hyperopt + walk-forward |
| 07 | `docs/07-paper-and-live-trading.md` | Dry-run, web UI, Telegram |
| 08 | `docs/08-risk-and-position-sizing.md` | Position sizing (most important) |
| 09 | `docs/09-research-notebook.md` | Jupyter research workflow |
| 10 | `docs/10-troubleshooting.md` | Indexed by error message |
| 11 | `docs/11-roadmap.md` | What to build next |
| 12 | `docs/12-glossary.md` | Trading/Freqtrade terms |
| 13 | `docs/13-walk-forward-validation-results.md` | First baseline walk-forward sweep + rejections |
| 14 | `docs/14-strategy-comparison-report.md` | Aggregate baseline + WF ranking |
| 15 | `docs/15-regime-filter-experiments.md` | Regime-filter variants vs unfiltered controls |
| 16 | `docs/16-rsitrend-bullonly-multiwindow.md` | RSITrendBullOnly 3-fold validation + rejection |

---

## Git Workflow

**MANDATORY: Always create a feature branch before starting any task. Never commit directly to `main`.**

1. **Before writing any code**, create and switch to a feature branch:
   ```bash
   git checkout -b <agent-name>/<feature-name>
   ```
   - Branch naming: `<agent-or-author>/<short-description>`
   - Examples: `antigravity/donchian-strategy`, `codex/regime-classifier`, `copilot/fix-tests`

2. **Commit your work** on the feature branch with clear commit messages.

3. **Push the branch** when work is complete:
   ```bash
   git push -u origin <agent-name>/<feature-name>
   ```

4. **Merge via PR** — do not merge directly into `main`.

5. **Update `TASKS.md`** at the end of every session (on the feature branch).
