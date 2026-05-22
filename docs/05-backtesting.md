# 5. Backtesting

How to run backtests, what the output means, and how to compare runs.

## 5.1 The one command you'll run most

```bash
freqtrade backtesting -c user_data/config.json \
  --strategy EMACrossover \
  --timerange=20250101-20250501
```

That's it. Freqtrade loads the strategy, replays every 5m candle in the time range, simulates orders at the next-candle open, applies fees + slippage from the config, and produces a series of summary tables.

## 5.2 Reading the output

The most important tables, in order of usefulness:

1. **BACKTESTING REPORT (per pair)** — for each pair, total trades, win %, total P/L in USDT and %, average duration. Tells you which pairs your strategy works on.
2. **EXIT REASON STATS** — how trades exited (`roi` / `stop_loss` / `exit_signal` / `force_exit`). If 80% of your exits are `stop_loss` you have an entry-quality problem; if 80% are `roi` your stop is probably too wide.
3. **MIXED TAG STATS / BUY TAG STATS** — only useful if you tagged entries (see [Strategy](03-strategy.md) §3.8).
4. **STRATEGY SUMMARY** — single-line aggregate: trades, average % profit, total profit, win/draw/loss breakdown, max drawdown.
5. **Bottom block** — Sharpe (daily wallet balance), Sortino, Calmar, drawdown duration, market change (so you can compare your strategy to "just buy and hold").

A few rules of thumb when reading these:
- **Sharpe** below ~0.5 over a meaningful period (months) means there's no edge worth pursuing.
- **Max drawdown** > 20% on a paper account → almost certainly account-wiping on live with leverage. A good baseline target for retail crypto is ≤ 15% in-sample, ≤ 25% out-of-sample.
- **Win rate** is the *least* informative number on the page. A 20% win-rate strategy can be very profitable with the right R:R; a 70% win-rate strategy can lose money with the wrong one.
- **Market change** vs your **total %**: if the market did +50% and you made +10%, that's not a strategy, that's underperforming long-only.

## 5.3 Useful flags

| Flag | What it does |
|---|---|
| `--timerange=20250101-20250501` | Inclusive start, exclusive end. Use to chop in-sample vs out-of-sample windows. |
| `--timeframe=5m` | Override the strategy's `timeframe`. Rarely needed. |
| `--pairs BTC/USDT ETH/USDT` | Only backtest these pairs (otherwise uses `pair_whitelist`). |
| `--max-open-trades 1` | Override `max_open_trades` from the config. |
| `--stake-amount 50` | Override stake size per trade. |
| `--enable-protections` | Apply `protections` rules from the config (cooldown, max drawdown, low-profit pair). |
| `--export trades` | Dump every individual trade to `user_data/backtest_results/<timestamp>.json` for downstream analysis. |
| `--export trades --export-filename my-run.json` | Like above but with a chosen filename. |
| `--breakdown month` | Add a per-month P/L breakdown to the report. |
| `-i 5m` | Alias for `--timeframe`. |

The full list is `freqtrade backtesting --help`.

## 5.4 Comparing two runs

After `--export trades`, the JSON files in `user_data/backtest_results/` carry the full trade-level detail. You can analyse them with pandas in the [research notebook](09-research-notebook.md):

```python
import pandas as pd
a = pd.read_json("user_data/backtest_results/run-a.json")["trades"]
b = pd.read_json("user_data/backtest_results/run-b.json")["trades"]
# ... compare totals, exit reasons, drawdowns
```

You can also use `freqtrade backtesting-show` to render a saved result table without re-running the backtest:
```bash
freqtrade backtesting-show -c user_data/config.json --export-filename user_data/backtest_results/run-a.json
```

## 5.5 Avoiding self-deception

These are the failure modes most people land in:

- **Single-period overfit.** A strategy that looks great on Jan–May 2025 may be terrible on Jun–Aug. Always split your data into in-sample (for tuning) and out-of-sample (for honest evaluation). See [Hyperopt](06-hyperopt.md) §6.4 for walk-forward.
- **Implicit look-ahead.** If your indicator references "tomorrow's close" anywhere — even via a careless `.shift(-1)` — your backtest is fictional. Most strategy classes avoid this naturally, but custom ones get it wrong all the time.
- **Survivorship bias in pair selection.** Picking "the 5 best-performing alts of 2024" and backtesting on them in 2024 is a guaranteed win that means nothing about the future.
- **Optimisation against the holdout.** The moment you re-run hyperopt because the out-of-sample number looked bad, the holdout is contaminated. Be honest with yourself.
- **No fees / wrong fees.** The config bakes in a reasonable fee + slippage. Don't disable it. Real fills on small accounts are often *worse* than the model; never *better*.

## 5.6 What to do with a "good" backtest

Define good first: *positive Sharpe out-of-sample, drawdown below your tolerance, behaves sanely across a regime change.* If that's true:

1. **Walk-forward** on at least 3 non-overlapping holdouts. If any of them is materially worse than the in-sample, distrust the result.
2. **Paper-trade for ≥ 4 weeks.** Match the live-paper stats to the backtest stats. If they diverge, your fee/slippage model is wrong.
3. **Only then** size up to live, with micro position size and a kill switch.

See [Paper & live trading](07-paper-and-live-trading.md) §7.6 for the full pre-live checklist.

---

Next: [Hyperopt](06-hyperopt.md).
