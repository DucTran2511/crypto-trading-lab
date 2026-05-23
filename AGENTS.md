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
│   │   └── EMACrossover.py          # Tunable fast/slow EMA crossover w/ trend filter
│   └── notebooks/
│       └── research_template.ipynb  # Vectorised research starter
├── scripts/
│   └── download_binance_vision.py   # Pull OHLCV from data.binance.vision
├── risk/
│   ├── __init__.py
│   └── position_size.py             # CLI position-sizing calculator
├── tests/
│   ├── test_position_size.py
│   └── test_download_binance_vision.py
├── docs/                            # Numbered 01-12, long-form documentation
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

**Last milestone:** Initial scaffold complete (EMACrossover, config, docs, risk calc, data download).

**See `TASKS.md` for current sprint and detailed progress.**

Roadmap priority (from `docs/11-roadmap.md`):
1. Walk-forward harness (`scripts/walk_forward.py`)
2. GitHub Actions CI
3. More baseline strategies (Donchian, Bollinger, RSI+trend, MACD)
4. Regime classifier utility (`user_data/regime/classifier.py`)
5. Switch live data to Binance.vision as default
6. Live monitoring stack (logs, Telegram, heartbeat)
7. Paper-trade validation (4+ weeks)
8. Live micro-size deployment

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

---

## Git Workflow

- **Main branch:** `main`
- **Feature branches:** `<agent-or-author>/<feature-name>`
  - e.g. `antigravity/walk-forward-harness`, `codex/github-actions-ci`
- **Merge via PR** when feature is complete
- Update `TASKS.md` at end of every session
