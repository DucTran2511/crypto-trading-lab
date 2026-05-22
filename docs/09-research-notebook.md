# 9. Research notebook

Sometimes the Freqtrade strategy API is the wrong shape for what you want to ask. The notebook in `user_data/notebooks/research_template.ipynb` is the escape hatch: a plain Jupyter environment with pandas + matplotlib pointed at the same Feather files Freqtrade uses.

## 9.1 When to use the notebook vs a strategy class

Use the notebook for:
- **Exploring** an idea before committing to a strategy class (e.g. "does the SMA gradient predict next-bar returns at all?").
- **Visualising** trades, equity curves, signal density, drawdowns.
- **One-off** analyses that don't need to be re-run every backtest.
- **Vectorised** experiments where you need the whole dataframe at once (Freqtrade's bar-by-bar simulator is the wrong fit).

Use a Freqtrade strategy class for:
- **Production** backtests with realistic fee/slippage/order-book modelling.
- **Hyperopt** parameter searches.
- **Paper or live trading**.

The natural workflow: prototype in the notebook → if it shows signal, port to a strategy class → backtest → hyperopt → walk-forward → paper-trade → live.

## 9.2 Launching it

```bash
source .venv/bin/activate   # or your equivalent
jupyter lab                 # or: jupyter notebook
```

Open `user_data/notebooks/research_template.ipynb`. The first cell loads the OKX 5m data for `BTC/USDT` so you can immediately start experimenting.

## 9.3 Loading candles directly

```python
import pandas as pd

df = pd.read_feather("user_data/data/okx/BTC_USDT-5m.feather")
df = df.set_index("date").sort_index()
df.head()
```

Columns are `[open, high, low, close, volume]` after `set_index`. Date is timezone-aware UTC.

## 9.4 A minimal vectorised backtest

The full Freqtrade simulator is unnecessary for triage work. A pandas vectorised version is ~5 lines:

```python
fast = df["close"].ewm(span=9, adjust=False).mean()
slow = df["close"].ewm(span=21, adjust=False).mean()
signal = ((fast > slow) & (fast.shift(1) <= slow.shift(1))).astype(int)
returns = df["close"].pct_change().fillna(0)
strategy_returns = (signal.shift(1) * returns)  # enter next bar
equity = (1 + strategy_returns).cumprod()
equity.plot(title="Naive EMA crossover, no fees/slippage")
```

This won't model stops, ROI ladders, or fees. It's good for "is there any signal here at all?", not for production claims.

## 9.5 Loading an exported Freqtrade backtest

After running `freqtrade backtesting --export trades`, the JSON file contains per-trade detail:

```python
import json
with open("user_data/backtest_results/run.json") as f:
    payload = json.load(f)
trades = pd.json_normalize(payload["trades"])
trades.head()
```

Useful follow-ups:
- `trades.groupby("exit_reason")["profit_abs"].agg(["count", "sum"])` — exit reason attribution.
- `trades.groupby(pd.Grouper(key="open_date", freq="W"))["profit_abs"].sum()` — weekly P/L.
- `trades.profit_abs.cumsum().plot()` — equity curve.

## 9.6 Suggested research cells

Things worth measuring before you trust any backtest:

1. **Signal density by hour of day / day of week.** If your strategy fires 10× more in one session, the result is dominated by one regime.
2. **Auto-correlation of trade returns.** High positive autocorr → you have one trend you keep riding; one regime change kills it.
3. **Drawdown duration histogram.** "Max drawdown 20%" is a number; "drawdown lasted 9 months" is psychology.
4. **Per-pair P/L scatter.** If 80% of your profit comes from one pair, your strategy is a one-pair strategy.
5. **Slippage sensitivity.** Re-run with fees doubled. If the strategy goes from +5% to -2%, your "edge" is fee arbitrage and won't survive live.

## 9.7 Don't commit candle data

`user_data/data/` is gitignored on purpose. The notebook itself is committed; the data is not. If you produce a notebook that depends on a specific downloaded range, note the `freqtrade download-data` invocation at the top so anyone can reproduce.

---

Next: [Troubleshooting](10-troubleshooting.md).
