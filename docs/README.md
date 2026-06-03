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
18. [1h strategy walk-forward results](18-1h-strategy-walk-forward.md) — 7-fold validation result and rejection decision for the 1h sprint candidates.
19. [Pair universe expansion sprint plan](19-pair-universe-expansion.md) — top-20 USDT spot universe on OKX; reuse 5m baselines to test whether the universe was the bottleneck.
20. [Pair universe expansion results](20-pair-universe-results.md) — top-20 OKX universe screen, RSITrend walk-forward result, and rejection decision.
21. [Daily momentum ranking sprint plan](21-daily-momentum-ranking.md) — rank top-20 by trailing 1d return each UTC day and restrict entries to today's top-3; final pre-FreqAI/perps test of the indicator-on-spot thread.
22. [Daily momentum ranking results](22-daily-momentum-results.md) — same-window screen, three walk-forward rejections, and Sprint 21 kill-criterion decision.
23. [Higher-timeframe sweep sprint plan](23-higher-timeframe-sweep.md) — Sprint 23 two-tier plan: 1d primary on 4 majors (Tier 1) + conditional 1w/1d/4h `MultiTimeframeConfirmation` (Tier 2); defensible categorical exception to §21.8 on fee-economics grounds; last untested cell before escalating beyond indicator-on-spot.
24. [Higher-timeframe sweep results](24-higher-timeframe-results.md) — corrected 1d same-window screen, zero Step 1 survivors, Tier 2 skipped, and §23.8 escalation decision.
25. [Long-hold spot trend strategies sprint plan](25-spot-trend-strategies.md) — Sprint 25 plan: three long-only spot strategies (`WeeklyDonchianBreakoutSpot`, `TimeSeriesMomentumSpot`, `DonchianBreakoutDailyTop20`) on top-20 USDT spot over 2020-01-01 → 2025-12-01; addresses Sprint 23's sample-size critique by widening the universe and extending the window; §25.1.1 documents this as the last permitted exception to §23.8.
26. [Spot trend strategy results](26-spot-trend-results.md) — Sprint 25 Step 1 same-window screen and Step 3 walk-forward rejection; two strategies passed Step 1, both failed Step 3, and §25.8 now points to FreqAI/ML or stopping the lab.
27. [Spot DCA-with-take-profit sprint plan](27-spot-dca-with-tp.md) — Sprint 27 plan: three DCA-with-TP entry-signal variants (`DCASpotRSIEntry`, `DCASpotBBEntry`, `DCASpotPullbackEntry`) on BTC/ETH/SOL spot only, 2020-04-01 → 2025-12-01; pre-registered +8% TP, -25% hard stop, 90-day time stop, max 5 legs at -5% spacing; structurally different trade shape (scale-in on adverse moves) from the 22 prior indicator variants; §27.1.1 documents this as the last permitted exception to §25.8 before escalating to FreqAI or stopping.

## Reference

- [Freqtrade official docs](https://www.freqtrade.io/en/stable/) — the upstream framework. When in doubt, theirs is canonical.
- [Freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/) — full strategy API reference.
- [Freqtrade hyperopt](https://www.freqtrade.io/en/stable/hyperopt/) — full hyperopt reference.
- [Freqtrade backtesting](https://www.freqtrade.io/en/stable/backtesting/) — full backtest reference.

## Reality check (read this once)

> No script in this repository is an edge. The default `EMACrossover` is a *deliberately losing* baseline on majors. The point of the repo is to give you a working pipeline so you can spend your time on the only thing that actually makes money: **finding, validating, and risk-managing real edges.** Treat backtests with healthy skepticism (overfitting is the default outcome, not the exception), paper-trade for weeks before risking real capital, and never risk more than ~1% of equity on a single trade.

If something in the docs is wrong, unclear, or out of date, please open an issue or a PR.
