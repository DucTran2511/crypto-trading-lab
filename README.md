# crypto-trading-lab

A starter repository for researching, backtesting, and (eventually) paper- or
live-trading crypto strategies with [Freqtrade](https://www.freqtrade.io/).

> **Reality check up front.** No script in this repository is an edge. The
> default `EMACrossover` strategy is a *losing* baseline on majors — that is
> intentional. The point of this repo is to give you a working pipeline so you
> can spend your time on the only thing that actually makes money: finding,
> validating, and risk-managing real edges.

## What's in here

```
crypto-trading-lab/
├── user_data/
│   ├── config.json                  # Freqtrade config (OKX spot, dry-run, $500 wallet)
│   ├── strategies/
│   │   └── EMACrossover.py          # tunable fast/slow EMA crossover w/ trend filter
│   └── notebooks/
│       └── research_template.ipynb  # vectorised research starter
├── scripts/
│   └── download_binance_vision.py   # pull Binance.com OHLCV from data.binance.vision
├── risk/
│   └── position_size.py             # CLI position-sizing calculator
├── tests/                           # pytest suite for the utility code
├── requirements.txt                 # production deps (pinned)
├── requirements-dev.txt             # + linter, pytest, jupyter, matplotlib
└── pyproject.toml                   # ruff + pytest config
```

## Quick start

```bash
# 1) Set up a clean environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 2) Download some historical data (3 months of 5m candles for 4 majors)
freqtrade download-data -c user_data/config.json \
    --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
    --timeframes 5m \
    --timerange=20250101-20250501

# 3) Run a backtest
freqtrade backtesting -c user_data/config.json \
    --strategy EMACrossover \
    --timerange=20250101-20250501

# 4) Optimise parameters (slow! ~minutes)
freqtrade hyperopt -c user_data/config.json \
    --strategy EMACrossover \
    --hyperopt-loss SharpeHyperOptLoss \
    --spaces buy \
    -e 100 \
    --timerange=20250101-20250501

# 5) Paper-trade live
freqtrade trade -c user_data/config.json --strategy EMACrossover
```

## Sample backtest result (baseline EMA crossover, default params)

| Pair      | Trades | Win % | Total P/L | Total P/L % |
|-----------|-------:|------:|----------:|------------:|
| SOL/USDT  |    202 | 41.6  |   -13.83  |       -2.77 |
| BNB/USDT  |    180 | 29.4  |   -26.45  |       -5.29 |
| BTC/USDT  |    221 | 31.2  |   -28.25  |       -5.65 |
| ETH/USDT  |    199 | 27.1  |   -35.44  |       -7.09 |
| **TOTAL** |  **802** | **32.4** | **-103.97** | **-20.79** |

- Period: 2025-01-01 → 2025-05-01 (4 months)
- Timeframe: 5m
- Starting wallet: 500 USDT, max 3 concurrent trades, 50 USDT stake
- Stoploss: -3%, ROI ladder 4% / 2% / 1% / 0% over 0 / 30 / 60 / 120 min
- Sharpe: -12.19 / Sortino: -15.18 / Max drawdown: 20.81%

**This is what an *un-edged* strategy looks like.** Fees + slippage + a 32 %
win rate eat the small upside. Your job is to find filters/regimes/exits that
flip this into a positive expectancy, then survive walk-forward.

## Why OKX as the default data source?

This repo was scaffolded on a US-located build environment from which
`api.binance.com` is geo-blocked (HTTP 451). OKX serves the same major pairs
with deep liquidity and a working public API from any IP, so it is the most
reliable default for *backtest data*.

The strategy code does **not** depend on which exchange you use — it operates
purely on OHLCV. To switch:

| If you want to…                                  | Do this                                                                         |
|--------------------------------------------------|---------------------------------------------------------------------------------|
| Backtest on **OKX** data (default)               | Nothing — just run `freqtrade download-data` then `backtesting`.                |
| Backtest on **real Binance.com** data            | `python scripts/download_binance_vision.py --pairs BTC/USDT ETH/USDT --timeframe 5m --start 2025-01 --end 2025-04` and change `exchange.name` in `user_data/config.json` to `binance`. |
| Paper- or live-trade on **Binance**              | Change `exchange.name` to `binance`, add API key + secret, run `freqtrade trade`. (You need a non-blocked IP for Binance.com.) |
| Paper- or live-trade on **Bybit / Kraken / etc.**| Change `exchange.name` accordingly and re-download data.                        |

## Strategy: `EMACrossover`

A classic fast-EMA / slow-EMA crossover, with three small additions:

1. **Trend filter** — only take longs when price is above a longer EMA
   (default 100-period). Helps avoid counter-trend entries.
2. **Volume confirmation** — entry candle's volume must exceed a rolling mean
   factor. Filters out dead/illiquid candles.
3. **ROI ladder + hard stop** — take profit at fixed levels, exit at -3% hard
   stop. Removes the "let it run forever" failure mode.

Every numeric parameter is exposed via Freqtrade's `IntParameter` /
`DecimalParameter`, so `freqtrade hyperopt --spaces buy` will tune them for you
on in-sample data.

> **Hyperopt is *not* magic.** It will happily over-fit. Always use
> `--timerange` to hold out a forward window, then re-run `backtesting` on the
> held-out slice to check whether the optimised parameters survive.

## Position sizing

```bash
python -m risk.position_size --equity 500 --entry 65000 --stop 63050 --risk-pct 0.01
```

Outputs:

```
Units:                  0.002564
Notional value:         $166.67
Dollar risk at stop:    $5.00
Risk as % of equity:    1.000%
Stop distance from entry: 3.000%
```

Rule of thumb: **never** risk more than 1 % of equity on a single crypto
trade. On a $500 account that is $5 per trade. Yes, it sounds small. Yes, it
is what keeps you alive long enough to develop an edge.

## Running the tests

```bash
ruff check .
pytest
```

## Roadmap / next things to build (in order)

1. **Walk-forward harness** — automate "optimise on N months, validate on next
   M, slide the window" so you stop fooling yourself with single-fit hyperopt.
2. **More strategies to use as research baselines** — Donchian breakout,
   Bollinger mean-reversion, RSI+trend, market-regime filter.
3. **Live data layer** — switch from OKX backtest data to `data.binance.vision`
   downloads so you backtest on the same data you will trade against.
4. **Telegram + Web UI alerts** — Freqtrade has both built in; just wire up
   credentials in `config.json`.
5. **Paper trade for ≥ 4 weeks** before any live capital. Match backtest stats
   against dry-run stats — if they diverge, something is wrong with your fill
   or fee model.
6. **Live with micro size** only after (5) passes.

## What *not* to do

- Don't increase leverage to "make $500 worth trading". On 100× leverage a 1 %
  move against you wipes the account.
- Don't trade alts before you can show edge on majors. Alts blow up faster.
- Don't follow Telegram signal sellers, YouTube "5-minute strategy" videos, or
  anything that claims a > 90 % win rate.
- Don't martingale / average down into a loser. It is not a strategy, it is a
  slow account death.

## License

MIT — do what you want, but no warranty. Trading is risky; you can lose all of
your capital.
