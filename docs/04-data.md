# 4. Data

How to get OHLCV candles into the repo, where they live on disk, and how to switch exchanges.

## 4.1 The default — OKX via `freqtrade download-data`

The bundled `user_data/config.json` declares `exchange.name = "okx"`. OKX has deep liquidity on the four pairs we use (BTC, ETH, SOL, BNB) and its public API is reachable from any IP, including geo-blocked regions. That makes it the most reliable default for *backtest data*.

Download:
```bash
freqtrade download-data -c user_data/config.json \
  --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
  --timeframes 5m \
  --timerange=20250101-20250501
```

Output layout (gitignored):
```
user_data/data/okx/
├── BTC_USDT-5m.feather
├── ETH_USDT-5m.feather
├── SOL_USDT-5m.feather
└── BNB_USDT-5m.feather
```

Feather is a fast binary columnar format (Arrow). The schema is `[date, open, high, low, close, volume]`.

## 4.2 Why not Binance?

`api.binance.com` is geo-blocked in the US (and a few other regions) with an HTTP 451. If the project was scaffolded from a US IP, `freqtrade download-data` against Binance would fail. OKX sidesteps that.

If your machine **can** reach `api.binance.com`, you can switch to it freely:
```bash
# 1) point the bot at Binance
# edit user_data/config.json:  "exchange": { "name": "binance", ... }

# 2) re-download
freqtrade download-data -c user_data/config.json \
  --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
  --timeframes 5m \
  --timerange=20250101-20250501
```

Data will land in `user_data/data/binance/`.

## 4.3 The fallback — `data.binance.vision` archives

For Binance candles **without hitting `api.binance.com`** (works from any IP), use the bundled script:

```bash
python scripts/download_binance_vision.py \
  --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
  --timeframe 5m \
  --start 2025-01 --end 2025-04
```

This pulls monthly zipped CSVs from Binance's public archive at `https://data.binance.vision`, concatenates them, and writes Freqtrade-native Feather files to `user_data/data/binance/`. Useful when:

- You're on a US/EU build machine but want to backtest on Binance.com numbers.
- You want a single immutable archive (the API can revise recent candles; the archive doesn't).

After downloading, set `"exchange": { "name": "binance", ... }` in `user_data/config.json` and Freqtrade will pick up the new files.

Caveats:
- The archive lags real-time by ~1 day; intra-month data only becomes available once that month's zip is published.
- Pre-2020 data may be missing for newer pairs.
- The script is in `scripts/`, not packaged — run it from the repo root with the venv activated.

CLI flags worth knowing:
| Flag | Default | Meaning |
|---|---|---|
| `--pairs` | required | Space-separated, e.g. `BTC/USDT ETH/USDT`. |
| `--timeframe` | `5m` | Any Binance kline interval: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`. |
| `--start` / `--end` | required | `YYYY-MM`, inclusive. |
| `--out-dir` | `user_data/data/binance` | Where to write Feather files. |
| `--workers` | `4` | Parallel download workers (one per pair). |

## 4.4 Switching exchanges (cheat-sheet)

The strategy code is exchange-agnostic — it operates purely on OHLCV. To switch, change `exchange.name` in `user_data/config.json` and re-download data:

| You want to… | Steps |
|---|---|
| Backtest on **OKX** (default) | Nothing — `freqtrade download-data` then `backtesting`. |
| Backtest on **real Binance.com** data | Switch `exchange.name` to `binance` and either run `freqtrade download-data` (needs non-blocked IP) or `scripts/download_binance_vision.py` (works from anywhere). |
| Backtest on **Bybit / Kraken / Coinbase / KuCoin / …** | Switch `exchange.name`, re-download. All ccxt-supported exchanges work. |
| Paper- or live-trade on any of the above | Same as backtest, plus add API key + secret under `exchange.key` / `exchange.secret` and set `"dry_run": false` only when you mean it. |

## 4.5 Data hygiene

A few rules to avoid burning research time on bad data:

- **Always re-download after switching exchanges.** Don't use BTC/USDT candles from OKX to backtest a Binance config — fills will diverge.
- **Match the timeframe to the data.** `timeframe = "5m"` in the strategy + 1h candles on disk = silent garbage results.
- **Check the date range you actually got.** `freqtrade download-data` may stop short if the exchange has gaps. The first command Freqtrade runs in `backtesting` prints the actual covered range — if it's shorter than what you asked for, investigate.
- **Don't commit `user_data/data/`.** It is gitignored on purpose: candles are regenerable, often large, and exchange-licensed.

## 4.6 Programmatic access

Both Feather and CSV are easy to load directly from pandas if you want to research outside Freqtrade:

```python
import pandas as pd
df = pd.read_feather("user_data/data/okx/BTC_USDT-5m.feather")
df.set_index("date", inplace=True)
df.head()
```

See [Research notebook](09-research-notebook.md) for a fuller workflow.

---

Next: [Backtesting](05-backtesting.md).
