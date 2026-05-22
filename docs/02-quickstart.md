# 2. Quickstart

Get from a freshly cloned repo to your first end-to-end backtest result in ~10 minutes. Assumes [Setup](01-setup.md) is done and `freqtrade --version` works.

## 2.1 Anatomy of the project

```
crypto-trading-lab/
├── user_data/                         # everything Freqtrade reads/writes
│   ├── config.json                    # bot config: exchange, wallet, pairs, timeframe, ...
│   ├── strategies/EMACrossover.py     # the strategy class
│   ├── notebooks/research_template.ipynb
│   ├── data/<exchange>/<PAIR>-<tf>.feather   # candles (gitignored)
│   ├── backtest_results/              # auto-generated (gitignored)
│   └── hyperopt_results/              # auto-generated (gitignored)
├── scripts/download_binance_vision.py # alt data source for Binance candles
├── risk/position_size.py              # position-sizing CLI
├── tests/                             # pytest suite for the utility code
├── requirements.txt / -dev.txt        # pinned deps
└── pyproject.toml                     # ruff + pytest config
```

## 2.2 Download some candles

The default config uses **OKX** (it's reachable from any IP and has deep liquidity; see [Data](04-data.md) for why and how to switch).

```bash
freqtrade download-data -c user_data/config.json \
  --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
  --timeframes 5m \
  --timerange=20250101-20250501
```

Output lands in `user_data/data/okx/BTC_USDT-5m.feather` (and friends). The whole 4-pair × 4-month download takes <2 minutes on a normal connection.

## 2.3 Run a backtest

```bash
freqtrade backtesting -c user_data/config.json \
  --strategy EMACrossover \
  --timerange=20250101-20250501
```

You will get a series of tables. The two most important are:

- **Backtested period & per-pair results** (per-pair trade count, win rate, profit).
- **STRATEGY SUMMARY** (aggregate trades, average profit, max drawdown).

Expected ballpark on the bundled defaults: ~800 trades, ~32% win rate, slightly negative aggregate P/L. **This is intentional** — see [Strategy](03-strategy.md). The point right now is that the pipeline works end-to-end.

## 2.4 Run the tests + lint

```bash
ruff check .
pytest
```

Both should be green. `pytest` covers the position-sizing CLI and the `data.binance.vision` ingest helpers.

## 2.5 Position sizing from the CLI

You should not skip this — *every* trade you ever place should pass through the same math.

```bash
python -m risk.position_size --equity 500 --entry 65000 --stop 63050 --risk-pct 0.01
```

Prints how many BTC units to buy if you have a $500 account and you want to risk exactly 1% ($5) on a long entry at $65,000 with a stop at $63,050. See [Risk & position sizing](08-risk-and-position-sizing.md) for the math + arguments.

## 2.6 Where to go next

- I want to understand what the strategy actually does → [Strategy](03-strategy.md)
- I want to tune parameters → [Hyperopt](06-hyperopt.md)
- I want to paper trade live → [Paper & live trading](07-paper-and-live-trading.md)
- I want to use real Binance data → [Data](04-data.md)
- I want to research a new strategy idea outside Freqtrade → [Research notebook](09-research-notebook.md)
- Something broke → [Troubleshooting](10-troubleshooting.md)
