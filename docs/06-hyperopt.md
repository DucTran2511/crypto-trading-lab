# 6. Hyperopt

`freqtrade hyperopt` is a parameter optimiser: it tries many combinations of your strategy's tunable parameters and reports the best ones for a given loss function. It is *also* the easiest way in the entire pipeline to fool yourself. Read §6.3 and §6.4 carefully.

## 6.1 Run it

```bash
freqtrade hyperopt -c user_data/config.json \
  --strategy EMACrossover \
  --hyperopt-loss SharpeHyperOptLoss \
  --spaces buy \
  -e 100 \
  --timerange=20250101-20250401
```

What each flag does:

| Flag | Meaning |
|---|---|
| `--strategy EMACrossover` | The strategy class whose `IntParameter` / `DecimalParameter` / `BooleanParameter` declarations define the search space. |
| `--hyperopt-loss SharpeHyperOptLoss` | The "score" hyperopt is minimising. Other useful losses below. |
| `--spaces buy` | Which parameter spaces to optimise. The bundled strategy uses `buy` for everything. You can also tune `sell`, `roi`, `stoploss`, `trailing`, `protection`, or `all`. |
| `-e 100` | Number of trials. 100 is enough to *explore* a small search space; 500–1000 for a serious tune. |
| `--timerange=20250101-20250401` | The **in-sample** window. Keep at least 1 month out-of-sample for honest evaluation. |
| `--print-all` | Print every trial, not just improvements. |
| `--random-state 42` | Reproducible runs. Worth setting once you're publishing numbers. |
| `-j 4` | Parallelism — number of worker processes. |

Output lands in `user_data/hyperopt_results/`. Print the best result:
```bash
freqtrade hyperopt-show --best
# or to inspect a specific run:
freqtrade hyperopt-show -n 1
```

## 6.2 Loss functions worth knowing

| Loss | What it rewards | When to use |
|---|---|---|
| `ShortTradeDurHyperOptLoss` (default if you don't specify) | Average per-trade % profit, scaled by trade count + duration. Generic. | When you don't have an opinion yet. |
| `SharpeHyperOptLoss` | Daily Sharpe ratio. | When you care about risk-adjusted returns (almost always). |
| `SortinoHyperOptLoss` | Daily Sortino (downside-only stdev). | When you want to penalise losers but not winners. |
| `CalmarHyperOptLoss` | Annual return / max drawdown. | When drawdown is your dominant constraint. |
| `MaxDrawDownHyperOptLoss` | Minimises drawdown. | Pre-flight check; rarely the final objective. |
| `OnlyProfitHyperOptLoss` | Maximises raw profit. | Trap. Will pick risky, low-trade-count winners. Use Sharpe/Sortino instead. |

You can also write your own — see the [Freqtrade hyperopt-loss docs](https://www.freqtrade.io/en/stable/hyperopt/#configure-an-own-hyperopt-loss-function).

## 6.3 The caching gotcha (don't skip this)

Freqtrade calls `populate_indicators()` *once per pair* during a hyperopt run and **caches** the resulting frame. `populate_entry_trend()` and `populate_exit_trend()` are then re-evaluated for every trial against that cached frame.

If your strategy reads `self.<param>.value` *inside* `populate_indicators`, the cached frame will be locked to whatever `.value` was when the cache was filled — usually the defaults. Hyperopt will then report "optimal" parameters that were **never actually tested**, because every trial reused the same default indicator values.

Symptoms:
- Hyperopt finishes suspiciously fast.
- The "best" parameter set has weird values right at the edge of the search range.
- Re-running the backtest with the "best" parameters gives a totally different result than what hyperopt reported.

Fix: pre-compute one column per candidate value using `.range`, and select inside the trend functions. The bundled `EMACrossover` does this — see [Strategy](03-strategy.md) §3.4.

If you write your own strategy: **any** parameter that affects an indicator value must use this pattern. Parameters that only affect threshold comparisons (like `min_volume_factor` here) are fine to consume directly via `.value` inside the entry/exit functions.

## 6.4 Walk-forward — the only test that matters

A single in-sample hyperopt result is *worthless*. It tells you the best parameters for the past, which is exactly the regime that will never repeat. The honest workflow is **walk-forward**:

```
in-sample          out-of-sample
[--- tune ---]    [--- validate ---]
2025-01-01        2025-04-01      2025-05-01
```

1. Hyperopt on Jan–March (in-sample).
2. Take the best parameters from step 1 — **without changing them** — and backtest on April–May (out-of-sample).
3. If out-of-sample is materially worse (Sharpe drops > 50%, drawdown doubles), the in-sample was overfit. Discard the params.
4. If out-of-sample is comparable, you have weak evidence of an edge. Repeat on a different window before you trust it.
5. **Never** re-run hyperopt because the out-of-sample looked bad. That contaminates the holdout. If you do, start fresh on a new period that hyperopt has never seen.

For a more robust check, run several non-overlapping in/out splits ("walk-forward folds") and look at the *distribution* of out-of-sample Sharpes. If half the folds are negative, you don't have an edge — you got lucky on one window.

A walk-forward harness is on the roadmap (see [Roadmap](11-roadmap.md) §11.1) so you don't have to do this by hand every time.

## 6.5 Practical recipe (paste-friendly)

```bash
# 1) In-sample: tune the buy space.
freqtrade hyperopt -c user_data/config.json \
  --strategy EMACrossover \
  --hyperopt-loss SharpeHyperOptLoss \
  --spaces buy \
  -e 200 \
  --timerange=20250101-20250401 \
  --random-state 42

# 2) Inspect the best.
freqtrade hyperopt-show --best

# 3) Apply the best parameters to your strategy (Freqtrade writes them to
#    a .json file alongside the strategy, picked up automatically).

# 4) Out-of-sample: backtest on April (untouched).
freqtrade backtesting -c user_data/config.json \
  --strategy EMACrossover \
  --timerange=20250401-20250501

# 5) Compare in-sample vs out-of-sample. If OOS is fine, repeat on a
#    different period (e.g. May–July) before trusting anything.
```

## 6.6 Common pitfalls

- **Too few trials.** With 5 parameters and only 30 trials, you've barely scratched the search space; the "best" is essentially random. 100 minimum, 500 for confidence.
- **Tuning everything at once.** `--spaces all` lets hyperopt change ROI, stop, trailing, AND entry params simultaneously. The combinatorics explode and you get an unstable optimum. Tune `buy` first, then `roi`/`stoploss` separately.
- **Optimising on too short a window.** A few weeks of data won't span a regime change; the tuned params will fall apart the moment volatility shifts.
- **Picking the wrong loss function.** `OnlyProfitHyperOptLoss` selects high-variance lottery tickets. Use `SharpeHyperOptLoss` or `SortinoHyperOptLoss` for almost all cases.
- **Re-running on the holdout.** The single fastest way to overfit. Promise yourself you won't, then actually don't.

---

Next: [Paper & live trading](07-paper-and-live-trading.md).
