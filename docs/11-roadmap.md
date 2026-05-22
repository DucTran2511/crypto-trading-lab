# 11. Roadmap

What to build next, in rough priority order. None of this is required to use the repo as-is; it's the path from "I have a working pipeline" to "I have something I might run with real money".

## 11.1 Walk-forward harness (high priority)

**Problem.** Walk-forward (in-sample tune → out-of-sample validate, then slide the window) is the only honest way to evaluate a strategy. Doing it by hand is tedious and error-prone.

**Proposal.** A `scripts/walk_forward.py` that takes:
- A strategy name.
- A total date range.
- Window sizes (e.g. 90d in-sample / 30d out-of-sample).
- A step size (e.g. 30d).
- A hyperopt loss function.

…and produces a single CSV + plot with each fold's in-sample and out-of-sample Sharpe / drawdown / total %. Fold-stability is the most important number on the output: if half your folds are negative OOS, you have no edge.

**Sketch:**
```
for fold in fold_windows:
    freqtrade hyperopt --timerange <fold.in_sample>
    apply best params
    freqtrade backtesting --timerange <fold.out_of_sample>
    collect metrics
emit CSV + plot
```

## 11.2 GitHub Actions CI

Currently the repo has no CI. A minimal workflow:

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: sudo apt-get install -y build-essential wget
      - run: |
          cd /tmp && wget https://github.com/ta-lib/ta-lib/releases/download/v0.4.0/ta-lib-0.4.0-src.tar.gz
          tar -xzf ta-lib-0.4.0-src.tar.gz && cd ta-lib
          ./configure --prefix=/usr && make && sudo make install && sudo ldconfig
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: pytest
```

That gives PR-blocking lint + tests for everything except the actual backtest (which needs candles you don't want to commit).

## 11.3 More baseline strategies

Each of these is a known, simple structure that's worth having to compare against:

- **Donchian breakout** — long when close > rolling-N-high, exit on rolling-N-low. The classic turtle trend-follower. Works best on 1h–4h timeframes.
- **Bollinger mean-reversion** — long below lower band when ATR is below its median (regime filter). Easy to overfit; good teacher.
- **RSI(14) + trend filter** — long when RSI < 30 and price > 200EMA. The "classic" buy-the-dip-in-an-uptrend setup.
- **MACD signal cross + volume** — variant of `EMACrossover` with momentum from MACD instead of pure crossover.

Each lives in `user_data/strategies/<name>.py`, with the same parameter+hyperopt structure as `EMACrossover`. The point is to have multiple un-edged baselines so you can tell whether an *idea* improves on naive momentum, naive mean-reversion, etc.

## 11.4 A regime classifier as a shared utility

A surprising amount of "edge" comes from *only trading when the market is in the right regime*. A simple classifier (e.g. 200-period EMA slope sign, or ADX > 25 vs < 20) used by multiple strategies as a filter is much higher leverage than building yet another strategy.

Proposal: `user_data/regime/classifier.py` that exposes a single function returning a regime label per bar, importable from any strategy's `populate_indicators`.

## 11.5 Switch live data to Binance.vision

Once `scripts/download_binance_vision.py` is robust enough, it's worth making it the *default* path for historical data and using `freqtrade download-data` only for the recent tail (last ~7 days). Reasons:

- Binance archive is immutable; the API back-fills recent candles, which silently changes backtest results.
- Archive works from any IP — no geo-block headaches.
- It's faster for big ranges (parallel zip download is much faster than rate-limited REST pagination).

Implementation: add a `--source` flag to `freqtrade download-data` wrapper, or a `scripts/update_data.sh` that does Vision-for-historical + REST-for-recent and dumps both into `user_data/data/binance/`.

## 11.6 Live monitoring stack

Once you're paper-trading 24/7, you want:

- **Logs to a file** (`--logfile user_data/logs/freqtrade.log`), not just stdout.
- **Telegram alerts** (already documented — see [Paper & live trading](07-paper-and-live-trading.md) §7.4).
- **Heartbeat** — a cron job that pings `/api/v1/ping` on the bot's API server every minute and alerts you if it stops responding. (Without this, a frozen bot in the middle of a position is silently catastrophic.)
- **A boring dashboard** — `freqtrade-ui` is fine; adding Grafana on top of the bot's `/api/v1/stats` is overkill but fun.

## 11.7 Paper-trade validation period (4+ weeks)

Before any live capital:

1. Run `freqtrade trade -c user_data/config.json --strategy <yours>` continuously for at least 4 weeks (longer is better).
2. After the period, run the **same** strategy on the **same** date range via `freqtrade backtesting`.
3. The two should agree within ~30% on profit, win rate, and drawdown. If they don't, the bug is almost always in your fee/slippage assumptions; do not go live until it's resolved.

## 11.8 Live micro-size deployment

Only after 11.7 passes:

1. New exchange account dedicated to the bot (don't mix with discretionary trading).
2. API key with **spot only**, **no withdrawal**, **IP-restricted** if supported.
3. Stake the smallest size the exchange allows for the first month (typically $10–$50 per trade).
4. Daily review: compare live vs backtest stats. Any divergence > 50% on any metric is a stop-and-investigate.
5. Only after another month of live = backtest do you increase position size, and only in small increments.

The honest expected outcome at this stage is: the strategy underperforms its backtest because the backtest doesn't model your actual order book impact. That's why you stay small.

## 11.9 Stretch — explore FreqAI

Freqtrade ships [FreqAI](https://www.freqtrade.io/en/stable/freqai/), a plug-in for using ML models (sklearn, lightgbm, pytorch) inside a strategy. **Don't** start here — most retail traders who bolt on ML before establishing a non-ML baseline waste months building a model whose features have no predictive power. But once you have a working baseline + a regime classifier, FreqAI is a sensible next step for trying to predict next-bar return or regime.

---

This is the end of the docs. Back to the [docs index](README.md).
