# Documentation

This folder is the long-form docs for `crypto-trading-lab`. Start here, then drill into the topic you need.

## Read in order if you are new

1. [Setup](01-setup.md) — install Python, TA-Lib, the project deps, and verify everything imports.
2. [Quickstart](02-quickstart.md) — clone → backtest → result table in ~10 minutes.
3. [Strategy walkthrough](03-strategy.md) — how `EMACrossover` is wired, what every parameter does, and how to write your own.
4. [Data](04-data.md) — where OHLCV comes from, how to switch exchanges, and the on-disk layout.
5. [Backtesting](05-backtesting.md) — running, reading, and comparing backtests.
6. [Hyperopt](06-hyperopt.md) — parameter optimisation + walk-forward validation (the part most people get wrong).
7. [Paper & live trading](07-paper-and-live-trading.md) — dry-run, web UI, Telegram, and the safety checklist before any live capital.
8. [Risk & position sizing](08-risk-and-position-sizing.md) — the most important file in the repo.
9. [Research notebook](09-research-notebook.md) — when to drop down to pandas/vectorbt for exploration.
10. [Troubleshooting](10-troubleshooting.md) — common errors and fixes, indexed by error message.
11. [Roadmap](11-roadmap.md) — what to build next, in priority order.
12. [Glossary](12-glossary.md) — every acronym/term used in this repo.
13. [Walk-forward validation results](13-walk-forward-validation-results.md) — first baseline sweep results and rejection rationale.
14. [Strategy comparison report](14-strategy-comparison-report.md) — aggregate baseline and walk-forward ranking.
15. [Regime filter experiments](15-regime-filter-experiments.md) — compare bull-only, bear-excluded, and trending-only filters against controls.
16. [RSITrendBullOnly multi-window](16-rsitrend-bullonly-multiwindow.md) — 3-fold validation result and rejection decision.
17. [Next sprint plan](17-next-sprint-plan.md) — new hypotheses on higher timeframes (MultiTimeframeTrend + ATRAdaptiveMeanReversion).

## Reference

- [Freqtrade official docs](https://www.freqtrade.io/en/stable/) — the upstream framework. When in doubt, theirs is canonical.
- [Freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/) — full strategy API reference.
- [Freqtrade hyperopt](https://www.freqtrade.io/en/stable/hyperopt/) — full hyperopt reference.
- [Freqtrade backtesting](https://www.freqtrade.io/en/stable/backtesting/) — full backtest reference.

## Reality check (read this once)

> No script in this repository is an edge. The default `EMACrossover` is a *deliberately losing* baseline on majors. The point of the repo is to give you a working pipeline so you can spend your time on the only thing that actually makes money: **finding, validating, and risk-managing real edges.** Treat backtests with healthy skepticism (overfitting is the default outcome, not the exception), paper-trade for weeks before risking real capital, and never risk more than ~1% of equity on a single trade.

If something in the docs is wrong, unclear, or out of date, please open an issue or a PR.
