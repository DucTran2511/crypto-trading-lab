# 3. Strategy walkthrough — `EMACrossover`

This page is a line-by-line tour of `user_data/strategies/EMACrossover.py` and a template for writing your own.

## 3.1 What the strategy does (in English)

> Go long when a **fast EMA** crosses above a **slow EMA**, in a context where price is **above a longer trend EMA**, and the candle's **volume** is above its recent rolling mean. Exit on the reverse cross, on a fixed **ROI ladder**, or on a hard **-3% stop**. Trade only spot, long-only, on the 5-minute timeframe.

That single sentence is the entire alpha hypothesis. Everything in the file is plumbing for it.

## 3.2 Class-level attributes

| Attribute | Default | Meaning |
|---|---|---|
| `INTERFACE_VERSION = 3` | 3 | Required by Freqtrade's strategy API. |
| `can_short = False` | `False` | Spot, long-only. Set to `True` only on a futures-enabled config. |
| `minimal_roi` | 0.04 → 0.02 → 0.01 → 0.0 at 0 / 30 / 60 / 120 minutes | "Take profit" ladder: if the trade is at +4% any time, exit immediately; at +2% after 30 min; +1% after 1h; +0% (break even) after 2h. Keeps winners from giving back gains. |
| `stoploss = -0.03` | -3% | Hard stop. Tightens or loosens with risk appetite, but never disable it. |
| `trailing_stop = False` | off | The simpler model is easier to reason about; the trailing settings below are kept so you can flip a single boolean to enable. |
| `timeframe = "5m"` | 5-minute candles | Match this to the data you download. |
| `process_only_new_candles = True` | True | Recompute indicators only when a new candle closes — much cheaper. |
| `use_exit_signal = True` | True | Honour `populate_exit_trend` (the reverse-cross exit). |
| `startup_candle_count = 200` | 200 | Burn 200 candles at the start so the longest EMA (up to 200-period trend) has enough history. |

## 3.3 Hyperopt-tunable parameters

```python
ema_fast = IntParameter(5, 25, default=9, space="buy", optimize=True)
ema_slow = IntParameter(15, 60, default=21, space="buy", optimize=True)
ema_trend = IntParameter(50, 200, default=100, space="buy", optimize=True)
use_trend_filter = BooleanParameter(default=True, space="buy", optimize=True)
min_volume_factor = DecimalParameter(0.5, 3.0, default=1.0, decimals=2, space="buy", optimize=True)
```

Five knobs that hyperopt can search:
- `ema_fast` ∈ [5, 25] — fast EMA period.
- `ema_slow` ∈ [15, 60] — slow EMA period (a crossover is only meaningful with fast < slow, which the search will discover).
- `ema_trend` ∈ [50, 200] — trend-filter EMA period.
- `use_trend_filter` — toggle the trend filter on/off.
- `min_volume_factor` ∈ [0.5, 3.0] — how many × the 20-period rolling volume mean is required for entry.

All of them live in the `"buy"` parameter space so a single `freqtrade hyperopt --spaces buy` tunes them all together.

## 3.4 `populate_indicators` — and the hyperopt caching gotcha

```python
def populate_indicators(self, dataframe, metadata):
    for val in self.ema_fast.range:
        dataframe[f"ema_fast_{val}"] = ta.EMA(dataframe, timeperiod=val)
    for val in self.ema_slow.range:
        dataframe[f"ema_slow_{val}"] = ta.EMA(dataframe, timeperiod=val)
    for val in self.ema_trend.range:
        dataframe[f"ema_trend_{val}"] = ta.EMA(dataframe, timeperiod=val)
    dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
    return dataframe
```

**Why the `for val in self.ema_fast.range` loop?**

Freqtrade calls `populate_indicators()` *once per pair* during a hyperopt run and **caches the result**. `populate_entry_trend()` and `populate_exit_trend()` are then re-run for every trial with new parameter values, against that cached frame.

If you wrote the naive version (`ta.EMA(dataframe, timeperiod=int(self.ema_fast.value))`), the EMA periods would be locked to whatever `.value` was when the cache was filled — usually the defaults. Hyperopt would happily report "optimal" EMA periods that were never actually tested. This is a real, easy-to-miss bug.

The fix is the canonical Freqtrade pattern: compute one column per *candidate* period (`self.ema_fast.range` enumerates the whole search space), then pick the right one inside `populate_entry_trend` / `populate_exit_trend` (which *do* get re-run per trial).

`dataframe["volume_mean"]` doesn't change with any tunable parameter, so it stays a single column.

## 3.5 `populate_entry_trend` — long-only entry conditions

```python
def populate_entry_trend(self, dataframe, metadata):
    ema_fast = dataframe[f"ema_fast_{self.ema_fast.value}"]
    ema_slow = dataframe[f"ema_slow_{self.ema_slow.value}"]
    conditions = [
        (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1)),  # cross-up
        dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
        dataframe["volume"] > 0,
    ]
    if self.use_trend_filter.value:
        ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]
        conditions.append(dataframe["close"] > ema_trend)
    dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
    return dataframe
```

Three always-on conditions plus one optional trend filter, all `AND`'d together:

1. **Crossover.** Fast EMA is above slow EMA *now*, and was below or equal *one candle ago*. This is a real cross, not just "fast > slow forever".
2. **Volume confirmation.** Current candle's volume is at least `min_volume_factor` × the 20-period rolling volume mean (e.g. 1.0× = average, 2.0× = double the average).
3. **Sanity.** Volume must be > 0 (guards against gappy/halted candles).
4. **(optional) Trend filter.** Price is above the trend EMA — keeps you from buying every micro-bounce in a downtrend.

When all conditions are true, `enter_long` is set to `1` on that candle, and Freqtrade will queue a buy order on the next bar.

## 3.6 `populate_exit_trend` — symmetric exit

```python
def populate_exit_trend(self, dataframe, metadata):
    ema_fast = dataframe[f"ema_fast_{self.ema_fast.value}"]
    ema_slow = dataframe[f"ema_slow_{self.ema_slow.value}"]
    dataframe.loc[
        (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1)),
        "exit_long",
    ] = 1
    return dataframe
```

Exit on the reverse crossover. Combined with the ROI ladder and the hard -3% stop, you have three orthogonal exit reasons:

| Trigger | When it fires | Typical bucket in backtest "exit reason" |
|---|---|---|
| ROI ladder | Profit hits a level on the ROI table at the right elapsed time | `roi` |
| Hard stop | -3% from entry | `stop_loss` |
| Exit signal | Fast EMA crosses back below slow EMA | `exit_signal` |

## 3.7 Sample backtest result (default params)

OKX 5m, 2025-01-01 → 2025-05-01:

| Pair | Trades | Win % | Total P/L | Total P/L % |
|---|---:|---:|---:|---:|
| SOL/USDT | 202 | 41.6 | -13.83 | -2.77 |
| BNB/USDT | 180 | 29.4 | -26.45 | -5.29 |
| BTC/USDT | 221 | 31.2 | -28.25 | -5.65 |
| ETH/USDT | 199 | 27.1 | -35.44 | -7.09 |
| **TOTAL** | **802** | **32.4** | **-103.97** | **-20.79** |

Sharpe -12.19, max drawdown 20.81% on a $500 wallet.

**Why such poor results?**

- A naive crossover on majors has ~zero edge; fees + slippage make it negative.
- The 5m timeframe is high-frequency relative to the signal, so noise dominates.
- The hard ROI ladder cuts winners aggressively (4% in the first 30 min) while the stop is symmetric at 3%, so per-trade expectancy is structurally not great.

This is what an *un-edged* strategy looks like, and that is **on purpose**: the repo gives you a working pipeline so you can spend your time finding real edges, not building infrastructure.

## 3.8 Writing your own strategy

Copy `EMACrossover.py` to a new file in `user_data/strategies/`, rename the class, change the entry/exit rules. The rough recipe:

1. **Declare tunable parameters** at the class level (`IntParameter`, `DecimalParameter`, `CategoricalParameter`, `BooleanParameter`).
2. **Compute indicators in `populate_indicators`** — and if any tunable parameter affects an indicator value, use the `for val in self.<param>.range` pattern from §3.4. If you forget this, hyperopt will lie to you.
3. **Express entries in `populate_entry_trend`** as a list of boolean series, `AND`'d together, written to `enter_long` (and `enter_short` for shorts on futures configs).
4. **Express exits in `populate_exit_trend`** the same way, but to `exit_long` / `exit_short`.
5. **Always** define `stoploss`, `minimal_roi`, `timeframe`, and `startup_candle_count` — they are the bare minimum risk plumbing.

Test it the same way:
```bash
freqtrade backtesting -c user_data/config.json --strategy MyStrategy --timerange=20250101-20250501
```

## 3.9 Common pitfalls

- **Using `.value` inside `populate_indicators` for hyperopt-tunable parameters.** See §3.4. Always use `.range` for indicator periods, and `.value` only inside entry/exit functions (or for params that don't affect indicator values — `min_volume_factor` and `use_trend_filter` here are fine because they only show up downstream).
- **Look-ahead bias.** Never use future information. Freqtrade backtests bar-by-bar, so as long as you only reference columns from the past (or the current bar's open, which is what you actually trade), you are safe. Be especially careful with `.rolling()` and `.ewm()` — they are fine. `.shift(-N)` is **not** — that's a future leak.
- **No startup candles.** If your longest indicator needs 100 bars, set `startup_candle_count` to at least that. Otherwise the first 100 bars produce `NaN`s and you get silently zero trades.
- **Different timeframes between config and strategy.** Match `timeframe = "5m"` to the candles you downloaded; mismatched timeframes either error or silently use the wrong data.

---

Next: [Data](04-data.md).
