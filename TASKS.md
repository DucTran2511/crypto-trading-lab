# TASKS.md — Current Sprint

> Update this file at the end of every coding session.
> Mark: `[ ]` todo, `[/]` in progress, `[x]` done.

---

## Sprint Status

- [/] **Sprint 23: Higher-timeframe sweep (1d primary, MTF combo conditional)**
  Fourteen strategy variants have been rejected across 5m and 1h timeframes.
  Sprint 21 fired its kill criterion, but a single untested cell remains:
  **1d as primary trading timeframe**. The fee-economics argument (§23.1) makes
  this a defensible categorical exception to §21.8, not "another variant" — at
  1d the round-trip fee burden is 10–20× lower than at 5m. This sprint is
  two-tier with a hard gate between tiers: Tier 1 runs all five baselines on 1d
  primary against the 4 majors over a 3-year window; Tier 2 (a single
  `MultiTimeframeConfirmation` strategy combining 1w + 1d + 4h) **only runs if
  Tier 1 produces ≥ 1 Step 3 survivor**. Full plan in
  `docs/23-higher-timeframe-sweep.md`. If both tiers reject, §23.8 applies with
  no further escape hatches — next sprint must be FreqAI, perps+funding, or
  stop.

## Previous Sprints (done)

- [x] **Sprint 21: Daily momentum ranking (top-3 of top-20 universe)** — see
  `docs/21-daily-momentum-ranking.md`. Three ranked variants passed the
  same-window screen; all three failed 7-fold walk-forward acceptance.
  Fourteen strategies tested, fourteen rejected. See
  `docs/22-daily-momentum-results.md`.

- [x] **Sprint 19: Pair universe expansion (top-20 USDT spot)** — see
  `docs/19-pair-universe-expansion.md`. Only `RSITrend` passed the
  same-window screen; it then failed 7-fold walk-forward acceptance with
  avg OOS Sharpe -30.77 and avg OOS profit -0.17%. No strategy advanced.
  See `docs/20-pair-universe-results.md`.

- [x] **Sprint 17: New hypotheses on higher timeframes** — see
  `docs/17-next-sprint-plan.md`. Both 1h candidates passed the same-window
  screen but failed walk-forward acceptance due to negative average
  out-of-sample profit. No strategy advanced. See
  `docs/18-1h-strategy-walk-forward.md`.

## Up Next

If Sprint 23 produces zero survivors, §23.8 applies with no further escape
hatches: next sprint must address a structurally different direction (FreqAI
on engineered features, perps + funding-rate arbitrage, or stop).

### Sprint 23 tasks (per-agent assignments)

> Full spec: `docs/23-higher-timeframe-sweep.md`. Tier rubric: cheap models
> for transcription, mid-tier for code-from-spec, high-tier only for design
> under ambiguity. Do **not** route any of these to Opus Thinking, Codex 5.5
> high+, or Devin without explicit escalation.
>
> **Hard gate between Tier 1 and Tier 2.** Tasks H+I only run if Task F
> produces ≥ 1 Step 3 survivor. If Task F produces zero survivors, jump
> directly to Tasks G + L and skip H–K entirely.

- [x] **A. Create feature branch + confirm 1d backtest window and stoploss table** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-23-higher-timeframes` in the
    agent's worktree.
  - Per `docs/23-higher-timeframe-sweep.md` §23.2.1, the Tier 1 backtest
    window is `2022-01-01` → `2025-05-01`. Per §23.4, per-strategy 1d
    stoploss and `minimal_roi` are pre-registered. Confirm both — do **not**
    treat either as hyperopt parameters. Document any deliberate deviation
    in this file's session log.
  - No code edits in this task beyond the branch creation.
  - Result: created `codex/sprint-23-higher-timeframes`; confirmed Tier 1
    backtest window `2022-01-01` → `2025-05-01`; confirmed pre-registered 1d
    stoploss/ROI table with no deviations and no hyperopt treatment:
    `EMACrossoverDaily` -0.10 / `{"0": 0.20}`,
    `DonchianBreakoutDaily` -0.08 / `{"0": 0.25}`,
    `BollingerMeanReversionDaily` -0.06 / `{"0": 0.08}`,
    `RSITrendDaily` -0.10 / `{"0": 0.20}`,
    `MACDVolumeDaily` -0.10 / `{"0": 0.20}`.

- [x] **B. Download 1d OHLCV for 4 majors over 2022-01-01 → 2025-05-01** — _Codex 5.4 low_
  - Command:
    ```bash
    freqtrade download-data -c user_data/config.json \
      --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
      --timeframes 1d \
      --timerange=20220101-20250501
    ```
  - The candles land in `user_data/data/okx/` and are gitignored. Verify
    file existence and row counts (~1216 daily candles per pair).
  - **Also** download 1w and 4h for the same pairs and window — needed only
    in Tier 2 (Task H), but cheap to download in this task so Tier 2 isn't
    blocked on a data step later.
  - Acceptance: all 3 timeframes × 4 pairs land on disk without errors.
  - Result: downloaded/prepended OKX spot OHLCV for `1d`, `1w`, and `4h`.
    All 12 files exist under `user_data/data/okx/`. Verified rows:
    BTC 1222/229/7367, ETH 1222/229/7367, SOL 1222/229/7367,
    BNB 868/179/5243 for `1d`/`1w`/`4h` respectively. BNB starts
    `2022-12-21` on OKX, so it has fewer candles than the full-window
    BTC/ETH/SOL files; no download errors occurred.

- [x] **C. Implement five `*Daily` strategy subclasses + smoke tests** — _Codex 5.4 medium_
  - Per `docs/23-higher-timeframe-sweep.md` §23.3.1, add:
    - `user_data/strategies/EMACrossoverDaily.py`
    - `user_data/strategies/DonchianBreakoutDaily.py`
    - `user_data/strategies/BollingerMeanReversionDaily.py`
    - `user_data/strategies/RSITrendDaily.py`
    - `user_data/strategies/MACDVolumeDaily.py`
  - Each subclass inherits from the corresponding base, overrides only
    `timeframe`, `stoploss`, and `minimal_roi` per §23.4. Do **not** modify
    `populate_indicators` / `populate_entry_trend` / `populate_exit_trend`.
  - Reuse the `try: from user_data.strategies.X import Y / except
    ModuleNotFoundError` shim from the Sprint 21 `*DailyRanked` files for
    Freqtrade strategy resolver compatibility.
  - Smoke tests in `tests/test_strategy_smoke.py` (or a new
    `tests/test_daily_strategies.py`): import each subclass, instantiate,
    call `populate_indicators` / `populate_entry_trend` /
    `populate_exit_trend` on a small synthetic 1d DataFrame.
  - Acceptance: `ruff check .` clean, `pytest` green (75 + at least 5 new
    tests pass).
  - Result: added the five thin `*Daily` subclasses with only `timeframe`,
    `stoploss`, and `minimal_roi` overrides, plus five smoke tests in
    `tests/test_daily_strategies.py`. Verified `.venv/bin/ruff check .`
    clean and `.venv/bin/pytest` green: 80 passed.

- [x] **D. Tier 1 same-window backtests** — _Codex 5.4 low_
  - Run:
    ```bash
    python scripts/run_baselines.py \
      --strategies EMACrossoverDaily DonchianBreakoutDaily BollingerMeanReversionDaily RSITrendDaily MACDVolumeDaily \
      --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
      --timerange=20220101-20250501
    ```
  - Screen criteria (identical to docs/19 §19.6 Step 1): ≥ 50 trades AND
    max drawdown < 30%.
  - Capture per-strategy + per-pair trade counts in the session log; the
    distribution across pairs is informative even when the screen fails.
  - List Step 1 survivors. Pass them as `--strategy` arguments into Task F.
  - Corrected result: fixed `scripts/run_baselines.py` to pass both `--pairs`
    and explicit `--timeframe` through to `freqtrade backtesting`, then reran
    the Tier 1 sweep constrained to BTC/ETH/SOL/BNB on `1d`. This supersedes
    an earlier invalid run where config-level `timeframe = "5m"` overrode the
    daily strategy class. Screen results:
    `EMACrossoverDaily` 27 trades / 2.81% DD — fail trades;
    `DonchianBreakoutDaily` 32 / 4.27% — fail trades;
    `BollingerMeanReversionDaily` 0 / 0.00% — fail trades;
    `RSITrendDaily` 4 / 2.10% — fail trades;
    `MACDVolumeDaily` 45 / 4.30% — fail trades.
    Per-pair trade counts:
    `EMACrossoverDaily` BTC 6, ETH 10, SOL 5, BNB 6;
    `DonchianBreakoutDaily` BTC 11, ETH 11, SOL 8, BNB 2;
    `BollingerMeanReversionDaily` BTC 0, ETH 0, SOL 0, BNB 0;
    `RSITrendDaily` BTC 2, ETH 0, SOL 2, BNB 0;
    `MACDVolumeDaily` BTC 15, ETH 12, SOL 10, BNB 8.
    Step 1 survivors for Task F: none.

- [x] **E. (Conditional) `MultiTimeframeConfirmation` smoke test stub** — _Codex 5.4 low_
  - **Only if Task D produces ≥ 1 survivor.** Otherwise mark this task as
    not applicable and proceed to G + L.
  - Add a no-op smoke test stub for `MultiTimeframeConfirmation` so Task H
    can drop the implementation into a slot that already has test
    scaffolding. Do **not** implement the strategy here — Task H owns the
    implementation.
  - Result: added `tests/test_multi_timeframe_confirmation.py` with a
    skipped import smoke stub. It remains inactive while Task H's strategy
    module is absent, then instantiates `MultiTimeframeConfirmation` and
    checks the expected class name and `1d` timeframe once implemented.

- [x] **F. Tier 1 walk-forward for screen survivors** — _Antigravity Gemini Flash medium (after D)_
  - For each strategy that passed Task D: run
    ```bash
    python scripts/walk_forward.py \
      --strategy <StrategyName> \
      --start 2022-01-01 --end 2025-05-01 \
      --in-sample 365d --out-sample 90d --step 90d \
      --loss SharpeHyperOptLoss --epochs 100 \
      --freqtrade-bin .venv/bin/freqtrade \
      -j 1 \
      --output-dir user_data/walk_forward_results/<StrategyName>
    ```
  - **Window sizes differ from prior sprints** per §23.6 Step 2 — they are
    the 1d-appropriate analogue of 90d/30d/30d for 5m. The acceptance
    criteria are unchanged.
  - Acceptance (per §23.6 Step 3, unchanged): ≥ 3 OOS folds, avg OOS Sharpe
    > 0, avg OOS profit > 0, no single fold drawdown > 5%.
  - This is the largest compute block of Tier 1.
  - Result: not run for any strategy because the corrected `1d` Task D screen
    produced zero Step 1 survivors. An initial attempted `RSITrendDaily`
    walk-forward exposed missing pair/timeframe forwarding in the harness;
    `scripts/walk_forward.py` now supports explicit `--pairs` and
    `--timeframe` for future runs, but Sprint 23's Tier 1 hard gate stops
    here.

- [ ] **G. Write results doc `docs/24-higher-timeframe-results.md`** — _Antigravity Gemini Flash high (after F)_
  - Follow the structure of `docs/22-daily-momentum-results.md` exactly:
    scope, same-window screen results table, per-pair trade-count table,
    per-fold walk-forward tables for any survivors, explicit pass/fail
    against §23.6 acceptance criteria.
  - If Task F produces ≥ 1 survivor, leave a placeholder section for the
    Tier 2 results and re-edit after Task I. Otherwise document the
    rejection definitively and invoke §23.8.
  - Update `docs/README.md` and AGENTS.md docs table to add entry 24.

- [ ] **H. (Conditional) Implement `MultiTimeframeConfirmation` + smoke test** — _Codex 5.4 medium (only if Task F produces ≥ 1 survivor)_
  - Per `docs/23-higher-timeframe-sweep.md` §23.3.2:
    - `user_data/strategies/MultiTimeframeConfirmation.py`.
    - 1d primary, `informative_pairs()` returns `(pair, "4h")` and
      `(pair, "1w")` per active pair.
    - Indicators: 1w EMA-200 slope (using `merge_informative_pair` with
      `ffill=True`), 4h RSI(14).
    - Entry: `(1w_ema200_slope > 0) & (parent_entry_signal == 1) &
      (4h_rsi < 70)` where `parent_entry_signal` is taken from the best
      Tier 1 survivor (passed via class attribute or explicit subclass).
    - Exit: parent strategy's exit, unchanged.
    - `startup_candle_count >= 1400` (200 weeks × 7 daily candles).
  - Smoke test: verify `merge_informative_pair` uses closed candles only
    (no look-ahead). Specifically, assert that for a 1d candle at date `D`,
    the merged 4h value reflects `4h close <= D - 4h` and the merged 1w
    value reflects `1w close <= D - 1d`.
  - Acceptance: `ruff check .` clean, `pytest` green.

- [ ] **I. (Conditional) Tier 2 same-window + walk-forward for MTF combo** — _Antigravity Gemini Flash medium (after H)_
  - Run `scripts/run_baselines.py` on `MultiTimeframeConfirmation` alone over
    `20220101-20250501`. Then run `scripts/walk_forward.py` if it passes the
    screen.
  - Same 4-criterion acceptance gate.
  - Append results to `docs/24-higher-timeframe-results.md` Tier 2 section.

- [ ] **J. (Conditional) Regime-filter experiments** — _Antigravity Gemini Flash medium (after F or I, only for Step 3 survivors)_
  - Run `scripts/regime_filter_experiments.py` for each survivor.
  - This is the **only** legitimate place to evaluate regime gating on top
    of a strategy that has already passed walk-forward acceptance.

- [ ] **K. (Conditional) Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after G + J, only if any strategy passes acceptance)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.**

- [ ] **L. Update `TASKS.md` at sprint end** — _Codex 5.4 low_
  - Mark Sprint 23 done. If no survivor: invoke §23.8 and write a
    one-paragraph follow-up memo in the session log proposing FreqAI, perps
    + funding, or "stop here" as the next sprint. Surface the decision to
    the ESC lane.

- [ ] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - Surface any design-level question rather than deciding locally.
    Examples: "the 1d walk-forward windows produce only 4 folds — should we
    extend the window?", "Task H's `MultiTimeframeConfirmation` should use
    Tier 1's best survivor as the entry signal — which one if 2 survive?",
    "the `merge_informative_pair` smoke test reveals a 1-candle look-ahead
    — should we accept it or rewrite?".

### Sprint 21 tasks (per-agent assignments)

> Full spec: `docs/21-daily-momentum-ranking.md`. Tier rubric: cheap models
> for transcription, mid-tier for code-from-spec, high-tier only for design
> under ambiguity. Do **not** route any of these to Opus Thinking, Codex 5.5
> high+, or Devin without explicit escalation.

- [x] **A. Create feature branch + decide ranking lookback** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-21-daily-momentum` in the
    agent's worktree.
  - Per `docs/21-daily-momentum-ranking.md` §21.2, default to **1-day**
    trailing return as the ranking signal computed on closed UTC daily
    candles. Only override if there is an explicit reason — document the
    choice in this file's session log.
  - No code edits in this task beyond the branch creation.
  - Result: created `codex/sprint-21-daily-momentum`; kept the pre-registered
    1-day trailing return computed on closed UTC daily candles because no
    explicit override reason surfaced.

- [x] **B. Build `scripts/rank_pairs_by_momentum.py`** — _Codex 5.4 medium_
  - Read the top-20 universe JSON
    (`user_data/universes/top20_okx_2024-07-01.json`) and local OKX 1d
    OHLCV from `user_data/data/okx/`.
  - Compute trailing 1d return per pair for every UTC day in a given range.
  - Write a per-day ranking JSON to
    `user_data/universes/daily_momentum_rank_YYYYMMDD-YYYYMMDD.json` with
    schema `{date: [pairs sorted best→worst]}`.
  - CLI: `argparse`, `--help`, `--start YYYY-MM-DD`, `--end YYYY-MM-DD`,
    `--lookback-days 1` (default 1), `--top N` (default 3 in downstream
    consumers, but stored ranking is the full top-20 ordering).
  - Tests in `tests/test_rank_pairs_by_momentum.py`: synthetic OHLCV with
    known returns, verify daily ordering, verify edge case where a pair has
    insufficient history.
  - Acceptance: `ruff check .` clean, `pytest` green.
  - Result: added `scripts/rank_pairs_by_momentum.py` and focused tests for
    parser help, universe loading, known-return ordering, insufficient
    per-pair history, and the plain `{date: [pairs...]}` output schema.
    Verified `.venv/bin/ruff check .`, `.venv/bin/pytest`, and a real-data
    CLI smoke run for `2024-07-01` through `2024-07-04`.

- [x] **C. Wire the rank into entry gating** — _Codex 5.4 medium_
  - Per `docs/21-daily-momentum-ranking.md` §21.3, add a strategy-level
    helper (new module `user_data/selection/daily_momentum.py`) that loads
    the ranking JSON and exposes `is_pair_in_today_top_n(pair, date, n)`.
  - Add a thin subclass per baseline strategy:
    `EMACrossoverDailyRanked`, `DonchianBreakoutDailyRanked`,
    `BollingerMeanReversionDailyRanked`, `RSITrendDailyRanked`,
    `MACDVolumeDailyRanked`. Each subclass overrides
    `populate_entry_trend` to AND-gate the original entry signal with the
    helper. **No other strategy logic changes.**
  - Files: `user_data/selection/__init__.py`,
    `user_data/selection/daily_momentum.py`,
    `user_data/strategies/*DailyRanked.py`.
  - Acceptance: `ruff check .` clean, `pytest` green (smoke tests in
    Task D).
  - Result: added the lazy-loading daily momentum selection helper and thin
    daily-ranked subclasses for `EMACrossover`, `DonchianBreakout`,
    `BollingerMeanReversion`, `RSITrend`, and `MACDVolume`. Each subclass
    calls the baseline `populate_entry_trend` unchanged, then clears
    `enter_long` outside the configured top-3 daily ranking gate. Verified
    `.venv/bin/ruff check .`, imports for all five ranked strategy classes,
    and `.venv/bin/pytest`.

- [x] **D. Smoke tests for ranked strategies and selection helper** — _Codex 5.4 low_
  - `tests/test_daily_momentum_selection.py`: helper handles missing dates,
    out-of-universe pairs, and the date-boundary case (entry candle's date
    looks up the *previous* completed UTC day's ranking).
  - For each ranked strategy: import test + populate_indicators /
    populate_entry_trend / populate_exit_trend smoke test.
  - Acceptance: `ruff check .` clean, `pytest` green.
  - Result: added `tests/test_daily_momentum_selection.py` covering missing
    dates, out-of-universe pairs, UTC date-boundary behavior, imports for all
    five daily-ranked strategies, and populate_indicators /
    populate_entry_trend / populate_exit_trend smoke runs against a temporary
    ranking JSON. Verified `.venv/bin/ruff check .` and `.venv/bin/pytest`
    with 75 passing tests.

- [x] **E. Generate daily-rank JSON for the backtest window** — _Codex 5.4 low_
  - Run the script for `2024-07-01` → `2025-05-01` and commit the resulting
    JSON (it's metadata, not candle data — add to git, not gitignore).
  - Sanity check: spot-check 3 random days; confirm the top-3 are large-cap
    or known-mover names; confirm no day has fewer than 20 ranked pairs
    (otherwise data gap).
  - Result: downloaded missing local OKX `1d` candles for the top-20 universe
    through `2025-05-01`, generated
    `user_data/universes/daily_momentum_rank_20240701-20250501.json`, and
    confirmed 304 ranked days with exactly 20 pairs per day. Spot checks:
    `2024-07-15` top-3 `PEOPLE/USDT`, `TURBO/USDT`, `FLOKI/USDT`;
    `2025-01-20` top-3 `ENS/USDT`, `SOL/USDT`, `ETH/USDT`;
    `2025-04-15` top-3 `TON/USDT`, `ENS/USDT`, `ETH/USDT`. Verified
    `.venv/bin/ruff check .` and `.venv/bin/pytest`.

- [x] **F. Same-window baseline backtests for ranked variants** — _Antigravity Gemini Flash medium (after C, D, E)_
  - Run `scripts/run_baselines.py` against the five `*DailyRanked` strategies
    on `--timerange=20250101-20250501`.
  - Screen: ≥ 50 trades **and** max drawdown < 30% (identical to docs/19
    §19.6 Step 1).
  - Capture per-pair trade counts in the results doc; this is informative
    even if the screen fails.
  - Result: fixed ranked-strategy imports so Freqtrade's strategy resolver can
    load them, then ran the same-window sweep over `20250101-20250501`.
    Step 1 survivors for Task G: `EMACrossoverDailyRanked`,
    `DonchianBreakoutDailyRanked`, and `RSITrendDailyRanked`.
    `BollingerMeanReversionDailyRanked` failed trade count; `MACDVolumeDailyRanked`
    failed drawdown.
  - Summary:
    - `EMACrossoverDailyRanked`: 627 trades, -18.93% profit, Sharpe -22.65,
      19.33% max drawdown — pass Step 1.
    - `DonchianBreakoutDailyRanked`: 751 trades, -27.01% profit, Sharpe
      -21.26, 29.53% max drawdown — pass Step 1.
    - `BollingerMeanReversionDailyRanked`: 4 trades, +0.15% profit, Sharpe
      +0.26, 0.10% max drawdown — fail trade count.
    - `RSITrendDailyRanked`: 67 trades, -1.96% profit, Sharpe -2.98,
      2.90% max drawdown — pass Step 1.
    - `MACDVolumeDailyRanked`: 1131 trades, -31.58% profit, Sharpe -43.21,
      31.97% max drawdown — fail drawdown.
  - Per-pair trade counts:
    - `EMACrossoverDailyRanked`: BTC 38, ETH 12, SOL 36, PEPE 42, TON 44,
      PEOPLE 43, DOGE 13, ORDI 42, TURBO 43, XRP 37, FIL 14, SUI 68,
      SHIB 9, FLOKI 15, WLD 31, NEAR 40, LTC 36, ENS 8, BNB 37, UNI 19.
    - `DonchianBreakoutDailyRanked`: BTC 49, ETH 18, SOL 45, PEPE 41,
      TON 43, PEOPLE 45, DOGE 20, ORDI 62, TURBO 62, XRP 38, FIL 16,
      SUI 74, SHIB 12, FLOKI 12, WLD 41, NEAR 43, LTC 51, ENS 10,
      BNB 47, UNI 22.
    - `BollingerMeanReversionDailyRanked`: BTC 0, ETH 0, SOL 0, PEPE 1,
      TON 0, PEOPLE 0, DOGE 0, ORDI 0, TURBO 0, XRP 0, FIL 0, SUI 0,
      SHIB 0, FLOKI 0, WLD 2, NEAR 0, LTC 0, ENS 0, BNB 1, UNI 0.
    - `RSITrendDailyRanked`: BTC 3, ETH 0, SOL 5, PEPE 6, TON 4, PEOPLE 3,
      DOGE 4, ORDI 2, TURBO 3, XRP 5, FIL 1, SUI 5, SHIB 2, FLOKI 2,
      WLD 4, NEAR 1, LTC 5, ENS 3, BNB 7, UNI 2.
    - `MACDVolumeDailyRanked`: BTC 80, ETH 27, SOL 52, PEPE 68, TON 68,
      PEOPLE 57, DOGE 27, ORDI 69, TURBO 90, XRP 68, FIL 31, SUI 113,
      SHIB 22, FLOKI 28, WLD 54, NEAR 54, LTC 78, ENS 37, BNB 71, UNI 37.

- [x] **G. Walk-forward validation for screen survivors** — _Antigravity Gemini Flash medium (after F)_
  - For each strategy that passed Task F: run `scripts/walk_forward.py`
    with 90d/30d/30d windows over 2024-07-01 → 2025-05-01.
  - Acceptance: ≥ 3 OOS folds, avg OOS Sharpe > 0, avg OOS profit > 0, no
    single fold drawdown > 5% (identical to docs/16 §16.3).
  - This is the largest compute block of the sprint.
  - Result: ran 7-fold walk-forward validation for all Task F survivors:
    `EMACrossoverDailyRanked`, `DonchianBreakoutDailyRanked`, and
    `RSITrendDailyRanked`. All three failed Step 3 acceptance.
    `EMACrossoverDailyRanked`: avg OOS Sharpe -1.96, avg OOS profit -0.44%,
    worst OOS drawdown 2.62%. `DonchianBreakoutDailyRanked`: avg OOS Sharpe
    -8.90, avg OOS profit -2.91%, worst OOS drawdown 6.43%.
    `RSITrendDailyRanked`: avg OOS Sharpe -18.57, avg OOS profit -0.43%,
    worst OOS drawdown 1.08%.

- [x] **H. Write results doc `docs/22-daily-momentum-results.md`** — _Antigravity Gemini Flash high (after G)_
  - Follow the structure of `docs/20-pair-universe-results.md` exactly.
  - Include: ranking methodology recap, per-strategy + per-pair Step 1
    results, walk-forward per-fold tables for survivors, explicit pass/fail
    against §21.6 acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table.
  - Result: wrote `docs/22-daily-momentum-results.md` with ranking recap,
    Step 1 screen results, per-pair trade-count table, per-fold
    walk-forward tables for the three screen survivors, acceptance criteria,
    rejection decision, and kill-criterion next step. Updated `docs/README.md`
    and `AGENTS.md`.

- [x] **I. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after G, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` for each survivor.
  - This is the **only** legitimate place to evaluate regime gating.
  - Closed as not applicable: Task G produced no passing Step 3 survivors, so
    there is no valid ranked strategy to send into regime-filter experiments.

- [x] **J. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after H, only if any strategy passes acceptance)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.**
  - Closed as not applicable: no Sprint 21 strategy passed walk-forward
    acceptance, so starting a 4-week dry-run would skip the paper-trade gate.

- [x] **K. Update `TASKS.md`** at sprint end — _Codex 5.4 low_
  - Mark Sprint 21 done. If no survivor: invoke the kill criterion in
    `docs/21-daily-momentum-ranking.md` §21.8 and write a one-paragraph
    follow-up memo in the session log proposing FreqAI or perps+funding
    as the next sprint.
  - Result: marked Sprint 21 done and invoked the §21.8 kill criterion. The
    next sprint should move to a structurally different direction: FreqAI on
    engineered features, or perps plus funding-rate arbitrage.

- [x] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - Surface any design-level question rather than deciding locally.
    Examples: "should ranking use 3d or 7d return instead of 1d?",
    "should we trade top-5 instead of top-3?", "the ranking JSON has gaps
    on holidays — should we forward-fill?".
  - Closed unused: no design-level ambiguity surfaced during Tasks G-H-J.

---

### Sprint 19 tasks (done — archived for reference)

> Full spec was: `docs/19-pair-universe-expansion.md`. Tier rubric: cheap
> models for transcription, mid-tier for code-from-spec, high-tier only for
> design under ambiguity. Do **not** route any of these to Opus Thinking,
> Codex 5.5 high+, or Devin without explicit escalation.

- [x] **A. Create feature branch + decide `max_open_trades` posture** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-19-top20` in the agent's worktree.
  - Per `docs/19-pair-universe-expansion.md` §19.4, default to Option A
    (`max_open_trades = 2`, peak ~66% concentration). Only override if there
    is an explicit reason — document the choice in this file's session log.
  - No code edits in this task beyond the config check.
  - Result: created `codex/sprint-19-top20`; kept Option A because
    `user_data/config.json` already has `max_open_trades = 2`.

- [x] **B. Build `scripts/build_universe.py`** — _Codex 5.4 medium_
  - Enumerate OKX USDT spot pairs (`GET /api/v5/market/tickers?instType=SPOT`).
  - Apply exclusions per `docs/19-pair-universe-expansion.md` §19.2.2
    (stablecoins, wrapped tokens, leveraged tokens, < 6 months OKX history).
  - Rank by **historical 30d quote volume ending 2024-07-01** (from local
    OHLCV in `user_data/data/okx/`, not from the live ticker volume field).
  - Write top-20 result to `user_data/universes/top20_okx_2024-07-01.json`.
  - CLI: `argparse`, `--help`, `--snapshot-date YYYY-MM-DD`, `--top N`.
  - Tests in `tests/test_build_universe.py`: mock OKX tickers + synthetic
    OHLCV, verify ranking + every exclusion rule.
  - Acceptance: `ruff check .` clean, `pytest` green.
  - Result: added `scripts/build_universe.py` plus tests covering parser help,
    OKX ticker parsing, stable/wrapped/leveraged/synthetic/history exclusions,
    historical-volume ranking, and JSON output. Verified `ruff check .` and
    `pytest` green.

- [x] **C. Run `build_universe.py`, commit the JSON, update `pair_whitelist`** — _Codex 5.4 low_
  - Run the script and inspect the output. Sanity check: BTC, ETH, SOL,
    BNB should appear; obvious stablecoins should not.
  - Commit `user_data/universes/top20_okx_2024-07-01.json` (this is
    metadata, not candle data — add to git, not gitignore).
  - Update `user_data/config.json` `pair_whitelist` to match.
  - Result: generated `user_data/universes/top20_okx_2024-07-01.json`
    from local 1d OKX OHLCV, confirmed BTC/ETH/SOL/BNB are present and
    obvious stablecoins are absent, and updated `pair_whitelist` to match.

- [x] **D. Download 5m candle data for the 16 new pairs** — _Antigravity Gemini Flash medium_
  ```bash
  freqtrade download-data -c user_data/config.json \
      --timeframes 5m \
      --timerange=20240701-20250501
  ```
  - With the updated `pair_whitelist`, this only fetches what's missing.
  - Data remains gitignored. Push the branch with the JSON + config changes only.
  - Result: ran the download for the top-20 whitelist over
    `20240701-20250501`; verified all 20 5m files cover from 2024-07-01
    through at least 2025-05-01. Candle data remains gitignored.

- [x] **E. Same-window baseline backtests** — _Antigravity Gemini Flash medium (after D)_
  - Run `scripts/run_baselines.py --strategies EMACrossover DonchianBreakout BollingerMeanReversion RSITrend MACDVolume --pairs <top20 from JSON> --timerange=20250101-20250501`.
  - **Screen: ≥ 50 trades and max drawdown < 30%** (raised from 20 per
    §19.6 Step 1).
  - Capture per-pair trade counts in the results doc; this informs follow-up
    sprints.
  - Result: ran the top-20 same-window sweep for `20250101-20250501`.
    `RSITrend` is the only Step 1 survivor (339 trades, 8.97% max drawdown).
    `EMACrossover` failed drawdown (1897 trades, 48.91% DD), `DonchianBreakout`
    failed drawdown (1250 trades, 40.23% DD), `BollingerMeanReversion` failed
    trade count (14 trades, 0.85% DD), and `MACDVolume` failed drawdown
    (3169 trades, 88.02% DD).
  - Per-pair trade counts:
    - `EMACrossover`: BTC 146, ETH 106, SOL 112, PEPE 121, TON 124, PEOPLE 107,
      DOGE 91, ORDI 99, TURBO 88, XRP 113, FIL 78, SUI 88, SHIB 73, FLOKI 67,
      WLD 87, NEAR 64, LTC 87, ENS 74, BNB 86, UNI 86.
    - `DonchianBreakout`: BTC 114, ETH 86, SOL 88, PEPE 55, TON 98, PEOPLE 75,
      DOGE 45, ORDI 73, TURBO 63, XRP 64, FIL 47, SUI 59, SHIB 37, FLOKI 34,
      WLD 46, NEAR 45, LTC 79, ENS 33, BNB 80, UNI 29.
    - `BollingerMeanReversion`: BTC 0, ETH 2, SOL 1, PEPE 1, TON 1, PEOPLE 1,
      DOGE 0, ORDI 0, TURBO 0, XRP 0, FIL 1, SUI 1, SHIB 0, FLOKI 0, WLD 1,
      NEAR 0, LTC 1, ENS 0, BNB 3, UNI 1.
    - `RSITrend`: BTC 18, ETH 18, SOL 20, PEPE 42, TON 20, PEOPLE 11,
      DOGE 23, ORDI 7, TURBO 13, XRP 20, FIL 17, SUI 14, SHIB 28, FLOKI 9,
      WLD 14, NEAR 12, LTC 15, ENS 12, BNB 12, UNI 14.
    - `MACDVolume`: BTC 237, ETH 207, SOL 206, PEPE 187, TON 193, PEOPLE 180,
      DOGE 137, ORDI 162, TURBO 174, XRP 144, FIL 146, SUI 149, SHIB 135,
      FLOKI 120, WLD 119, NEAR 122, LTC 164, ENS 125, BNB 133, UNI 129.

- [x] **F. Walk-forward validation for screen survivors** — _Antigravity Gemini Flash medium (after E)_
  - For each strategy that passed Task E: run
    `scripts/walk_forward.py` with 90d/30d/30d windows over 2024-07-01 →
    2025-05-01.
  - Acceptance: ≥ 3 OOS folds, avg OOS Sharpe > 0, avg OOS profit > 0,
    no single fold drawdown > 5% (identical to docs/16 §16.3).
  - This is the largest single block of compute in the sprint. Budget
    accordingly; if any strategy passes Task E it can be walk-forwarded in
    parallel with the others.
  - Result: ran 7-fold walk-forward validation for the only Task E survivor,
    `RSITrend`, with 90d/30d/30d windows over 2024-07-01 → 2025-05-01.
    Acceptance failed: avg OOS Sharpe -30.77, avg OOS profit -0.17%, worst
    fold drawdown 0.84%. It passed fold count and drawdown criteria, but failed
    average OOS Sharpe and average OOS profit. No strategy advances from
    Task F to regime-filter experiments or paper trading.

- [x] **G. Write results doc `docs/20-pair-universe-results.md`** — _Antigravity Gemini Flash high (after F)_
  - Follow the structure of `docs/18-1h-strategy-walk-forward.md` exactly.
  - Include: the universe selection (paste the JSON), per-strategy +
    per-pair Step 1 results, walk-forward per-fold tables for survivors,
    explicit pass/fail against §19.6 Step 3 acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table.
  - Result: added `docs/20-pair-universe-results.md`, linked it from
    `docs/README.md`, and added it to the AGENTS.md documentation table.
    The doc rejects Sprint 19 because `RSITrend` failed walk-forward acceptance.

- [x] **H. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after F, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` for each survivor.
  - This is the **only** legitimate place to evaluate regime gating.
  - Closed as not applicable: Task F/G produced no passing Step 3 survivors.
    `RSITrend` was the only same-window screen survivor, and it failed
    walk-forward acceptance on average OOS Sharpe and average OOS profit, so
    there is no legitimate candidate for regime-filter experiments.

- [x] **I. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after G, only if any strategy passes acceptance)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.**
  - Closed as not applicable: no Sprint 19 strategy passed walk-forward
    acceptance. Starting a dry-run from the rejected `RSITrend` result would
    bypass the pre-registered paper-trade gate.

- [x] **J. Update `TASKS.md`** at sprint end — _Codex 5.4 low_
  - Result: closed Sprint 19 with no strategy advancing to regime-filter
    experiments or paper trading. `RSITrend` was the only Step 1 survivor and
    failed Step 3 walk-forward acceptance. The registered next research path is
    the daily-momentum-ranking follow-up from `docs/19-pair-universe-expansion.md`
    §19.8, not another same-universe retune.

- [x] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - Surface any design-level question rather than deciding locally. Examples:
    "the universe-selection script is missing obvious pairs", "should we
    expand to top-50 because top-20 is too sparse?", "zero of five strategies
    passed Step 1 — the kill criterion from §19.8 triggers; should we go to
    FreqAI or perps next?".
  - Closed unused for Sprint 19: no unplanned design-level decision was made.
    Because one strategy passed the same-window screen but none passed
    walk-forward validation, the pre-registered §19.8 branch points to a
    daily-momentum-ranking follow-up sprint before FreqAI/perps escalation.

---

### Sprint 17 tasks (done — archived for reference)

> Full spec was: `docs/17-next-sprint-plan.md`. Tier rubric: cheap models for
> transcription, mid-tier for code-from-spec, high-tier only for design under
> ambiguity. Do **not** route any of these to Opus Thinking, Codex 5.5 high+,
> or Devin without explicit escalation.

- [x] **A. Create feature branch + decide `max_open_trades` posture** — _Codex 5.4 low_
  - Branch: `git checkout -b <agent>/sprint-1h-strategies` in the agent's worktree.
  - Per `docs/17-next-sprint-plan.md` §17.2.2, decide **Option A** (`max_open_trades = 2`, recommended)
    or **Option B** (keep `3`, document the 60% concentration here).
  - Edit `user_data/config.json` accordingly. Document the chosen option in this file's session log.

- [x] **B. Download 1h candle data** — _Antigravity Gemini Flash medium_
  ```bash
  freqtrade download-data -c user_data/config.json \
      --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
      --timeframes 1h \
      --timerange=20240701-20250501
  ```
  - Data is gitignored. Push the branch with config changes only; do not commit candles.

- [x] **C. Implement `MultiTimeframeTrend.py`** — _Codex 5.4 medium_
  - 1h primary timeframe with 4h informative pairs for trend confirmation.
  - RSI pullback-into-trend entry with volume filter.
  - Hyperopt-safe indicator caching (`for val in self.<param>.range`).
  - `stoploss = -0.05` as a class attribute (do **not** edit `config.json`).
  - See `docs/17-next-sprint-plan.md` §17.3 Strategy A for full spec.
  - New file: `user_data/strategies/MultiTimeframeTrend.py`.

- [x] **D. Implement `ATRAdaptiveMeanReversion.py`** — _Codex 5.4 medium_
  - 1h timeframe, ATR-adaptive entry distance instead of static Bollinger Bands.
  - Volatility contraction filter (ATR < median(ATR, 50)) + RSI < 35.
  - **No regime filter built into the strategy. No `use_regime_filter` hyperopt
    parameter.** Regime gating is evaluated separately in Task I.
  - `stoploss = -0.05` as a class attribute.
  - See `docs/17-next-sprint-plan.md` §17.3 Strategy B for full spec.
  - New file: `user_data/strategies/ATRAdaptiveMeanReversion.py`.

- [x] **E. Add smoke tests for both new strategies** — _Codex 5.4 low_
  - Import test (strategy class loads).
  - `populate_indicators`, `populate_entry_trend`, `populate_exit_trend` return
    DataFrames with expected columns.
  - Acceptance: `ruff check .` clean, `pytest` green.

- [x] **F. Same-window baseline backtests** — _Antigravity Gemini Flash medium (after C, D, E)_
  - Run `scripts/run_baselines.py --strategies MultiTimeframeTrend ATRAdaptiveMeanReversion --timerange=20250101-20250501`.
  - Screen: ≥ 20 trades **and** max drawdown < 30%.
  - Result: both strategies cleared the screen. `MultiTimeframeTrend`: 301 trades,
    -6.14% total profit, -8.08 Sharpe, 6.75% max drawdown. `ATRAdaptiveMeanReversion`:
    797 trades, -26.85% total profit, -48.24 Sharpe, 26.92% max drawdown.
  - If Strategy B fails **only** the trade-count screen, perform the **one**
    relaxation pass per `docs/17-next-sprint-plan.md` §17.4 Step 1 note
    (ATR < median → ATR < 75th percentile). Document the change in the results doc.

- [x] **G. Walk-forward validation for survivors** — _Antigravity Gemini Flash medium (after F)_
  - 3+ OOS folds, 90d in-sample / 30d out-of-sample / 30d step.
  - Range: `2024-07-01` → `2025-05-01`.
  - Acceptance: avg OOS Sharpe > 0, avg OOS profit > 0, max fold DD ≤ 5% (all four criteria from `docs/16` §16.3).
  - Result: both same-window survivors failed full acceptance. `MultiTimeframeTrend`
    completed 7 folds with avg OOS Sharpe 0.20, avg OOS profit -0.03%, and worst
    OOS drawdown 1.06%; it failed only average OOS profit. `ATRAdaptiveMeanReversion`
    completed 7 folds with avg OOS Sharpe -16.09, avg OOS profit -0.76%, and worst
    OOS drawdown 3.46%; it failed average OOS Sharpe and profit. No strategy advances
    to regime-filter experiments or paper trading from Task G.

- [x] **H. Write results doc `docs/18-*.md`** — _Antigravity Gemini Flash high (after G)_
  - Follow the structure of `docs/16-rsitrend-bullonly-multiwindow.md` exactly.
  - Include the trade-count screen result, any relaxation applied per Task F,
    walk-forward per-fold table, and explicit pass/fail against acceptance criteria.
  - Update `docs/README.md` and AGENTS.md docs table with the new entry.
  - Result: added `docs/18-1h-strategy-walk-forward.md` and linked it from the
    docs index and AGENTS.md. Both 1h sprint candidates are documented as rejected.

- [x] **I. Regime-filter experiments on Step 3 survivors** — _Antigravity Gemini Flash medium (after G, only for passing strategies)_
  - Run `scripts/regime_filter_experiments.py` on each survivor.
  - This is the **only** legitimate place to evaluate regime gating.
  - Closed as not applicable: Task G produced no passing Step 3 survivors, so
    there are no legitimate strategies to run through regime-filter experiments.

- [x] **J. Start 4-week paper-trade dry-run** — _Antigravity Gemini Flash medium (after H, only if any strategy passes)_
  - `freqtrade trade -c user_data/config.json --strategy <StrategyName>`.
  - Track per-week trade count and win rate vs backtest expectation.
  - **No live-money deployment in this sprint.** Live go/no-go is a separate sprint decision.
  - Closed as not applicable: Task G and docs/18 rejected both 1h candidates, so
    no strategy met the prerequisite for a 4-week dry-run. No paper-trade process
    was started.

- [x] **K. Update `TASKS.md`** at sprint end — _Codex 5.4 low_
  - Result: closed the 1h sprint, recorded that no strategy advances, and left
    the next research direction for a future hypothesis sprint.

- [x] **ESC. Escalation lane** — _Sonnet 4.6 Thinking_
  - If any task surfaces a design-level question (e.g., should we change the
    acceptance criteria? extend the sprint? swap pair universe?), stop and
    escalate here. Do **not** decide locally inside the assigned agent.
  - Closed unused: no design-level escalation surfaced during the sprint. The
    pre-registered acceptance criteria were applied without modification.

---

## Done

- [x] RSITrendBullOnly multi-window walk-forward validation
  - [x] Run 3-fold walk-forward sweep with prepended data back to 2024-10-01
  - [x] Document results in `docs/16-rsitrend-bullonly-multiwindow.md`
  - [x] Reject variant (avg OOS Sharpe -0.48, avg OOS profit -0.06%)
  - [x] Close second-pass task as not applicable
- [x] Regime Filter Experiments
  - [x] Apply the regime classifier to the strongest baseline strategy candidates
  - [x] Compare all-regime, bull-only, bear-excluded, and trending-only variants
  - [x] Validate any promising regime-filtered variant with walk-forward validation
  - [x] Keep the original baseline result as the control for every regime experiment
- [x] Strategy Comparison Report
  - [x] Create a strategy comparison report that aggregates baseline backtest and walk-forward results
  - [x] Rank strategies by out-of-sample performance, drawdown control, trade count, and fold stability
  - [x] Add a small parser/aggregation test if report generation becomes scripted
  - [x] Document the final baseline ranking and which strategy should receive the next research iteration
- [x] Walk-Forward Validation Sweep
  - [x] Run `scripts/walk_forward.py` for each baseline strategy that survives the initial backtest screen
  - [x] Compare in-sample vs out-of-sample Sharpe, drawdown, and total profit by fold
  - [x] Reject strategies with unstable out-of-sample results or drawdowns above the research risk tolerance
  - [x] Save CSV summaries and stability plots for later comparison
- [x] Baseline Strategy Validation
  - [x] Confirm/download 5m OHLCV data for BTC/USDT, ETH/USDT, SOL/USDT, and BNB/USDT for `20250101-20250501`
  - [x] Run same-window backtests for `EMACrossover`, `DonchianBreakout`, `BollingerMeanReversion`, `RSITrend`, and `MACDVolume`
  - [x] Record comparable metrics: trades, win rate, total profit %, Sharpe, max drawdown, and profit factor
  - [x] Identify which strategies are worth walk-forward validation
- [x] More baseline strategies
  - [x] Donchian breakout strategy
  - [x] Bollinger mean-reversion strategy
  - [x] RSI(14) + trend filter strategy
  - [x] MACD signal cross + volume strategy
- [x] Regime classifier (`user_data/regime/classifier.py`)
  - [x] EMA slope sign classifier
  - [x] ADX threshold classifier
  - [x] Expose single function returning regime label per bar
  - [x] Importable from any strategy's `populate_indicators`
- [x] Walk-forward harness (`scripts/walk_forward.py`)
  - [x] Accept strategy name, date range, window sizes, step size, loss function
  - [x] Implement fold window generation logic
  - [x] Run hyperopt per in-sample fold
  - [x] Run backtesting per out-of-sample fold
  - [x] Collect metrics (Sharpe, drawdown, total %) per fold
  - [x] Output CSV summary + fold-stability plot
  - [x] Add tests in `tests/test_walk_forward.py`
- [x] Initial scaffold — EMACrossover strategy, config, venv setup
- [x] Position sizing calculator (`risk/position_size.py`)
- [x] Binance Vision download script (`scripts/download_binance_vision.py`)
- [x] Test suite (`tests/test_position_size.py`, `tests/test_download_binance_vision.py`)
- [x] Comprehensive documentation (docs 01-12)
- [x] Multi-agent brain setup (AGENTS.md, TASKS.md, symlinks)
- [x] GitHub Actions CI workflow (.github/workflows/ci.yml)
  - [x] TA-Lib C library install step
  - [x] `pip install -r requirements-dev.txt`
  - [x] `ruff check .`
  - [x] `pytest`

---

## Session Log

| Date | Agent | Summary |
|------|-------|---------|
| 2026-05-21 | Devin | Initial scaffold: EMACrossover, risk calc, data scripts |
| 2026-05-21 | Devin | Comprehensive docs (01-12) |
| 2026-05-22 | Antigravity | Fixed Freqtrade environment setup (Python version) |
| 2026-05-23 | Antigravity | Added multi-agent brain (AGENTS.md, TASKS.md, symlinks) |
| 2026-05-23 | Antigravity | Reinstalled Codex CLI globally to resolve missing platform dependency |
| 2026-05-23 | Antigravity | Implemented GitHub Actions CI workflow with TA-Lib build and pytest/ruff checks |
| 2026-05-23 | Codex | Built walk-forward harness and updated docs/metadata for usage and generated outputs |
| 2026-05-23 | Codex | Reviewed and tightened CI triggers/cache before merge |
| 2026-05-23 | Codex | Implemented baseline strategies and regime classifier utility |
| 2026-05-23 | Codex | Queued validation, reporting, and regime-filter experiment tasks |
| 2026-05-23 | Antigravity | Automated and ran same-window baseline backtests, generated report, selected RSITrend/BollingerMeanReversion for walk-forward sweeps |
| 2026-05-23 | Codex | Fixed baseline validation CLI help behavior and added parser/report tests |
| 2026-05-23 | Antigravity | Ran walk-forward validation sweeps for RSITrend and BollingerMeanReversion, analyzed results and rejected both due to overfitting |
| 2026-05-24 | Codex | Extended strategy comparison report to include regime walk-forward result roots |
| 2026-05-23 | Codex | Reviewed walk-forward sweep branch and added committed results report |
| 2026-05-24 | Codex | Added scripted strategy comparison report and ranked baselines for next research iteration |
| 2026-05-24 | Codex | Implemented and ran regime-filter experiments; `RSITrendBullOnly` survived as weak research-only candidate |
| 2026-05-24 | Antigravity | Prepended OKX data starting from 2024-10-01, ran 3-fold walk-forward validation sweep for RSITrendBullOnly, and rejected it |
| 2026-05-24 | Codex | Documented RSITrendBullOnly multi-window validation in docs/16 and linked it from docs indexes |
| 2026-05-24 | Codex | Closed task D as not applicable because RSITrendBullOnly failed acceptance |
| 2026-05-26 | Antigravity | Closed RSITrendBullOnly sprint, wrote next sprint plan (docs/17), opened new sprint for 1h strategies |
| 2026-05-26 | Codex | Started `codex/sprint-1h-strategies`; chose Option A and set `max_open_trades = 2` for 40% peak concentration on 1h candidates |
| 2026-05-26 | Antigravity | Downloaded 1h candle data for BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT (2024-07-01 to 2025-05-01) |
| 2026-05-26 | Codex | Implemented `ATRAdaptiveMeanReversion` 1h ATR-gated mean-reversion baseline with no built-in regime filter |
| 2026-05-26 | Codex | Implemented `MultiTimeframeTrend` with 1h entries, 4h informative EMA-slope confirmation, RSI recovery logic, and volume filtering |
| 2026-05-26 | Codex | Added smoke tests for both 1h strategy classes and verified `ruff check .` plus `pytest` |
| 2026-05-26 | Codex | Ran same-window 1h baseline backtests for Task F; both strategies passed the trade-count/drawdown screen, and Strategy B needed no ATR relaxation |
| 2026-05-26 | Codex | Ran 7-fold walk-forward validation for `MultiTimeframeTrend` and `ATRAdaptiveMeanReversion`; both failed acceptance due to negative average OOS profit |
| 2026-05-26 | Codex | Documented the 1h strategy walk-forward rejection in docs/18 and linked it from docs/README.md and AGENTS.md |
| 2026-05-26 | Codex | Closed Task I as not applicable because Task G produced no passing Step 3 survivors for regime-filter experiments |
| 2026-05-26 | Codex | Closed Task J as not applicable because no strategy passed walk-forward acceptance for paper trading |
| 2026-05-26 | Codex | Closed the 1h sprint bookkeeping: Task K complete, escalation lane unused, no candidate advances |
| 2026-05-27 | Codex | Started `codex/sprint-19-top20`; chose Sprint 19 Option A and kept `max_open_trades = 2` for ~66% peak concentration |
| 2026-05-27 | Codex | Implemented Task B for Sprint 19: top-N OKX USDT universe builder with exclusion/ranking tests; verified ruff and pytest |
| 2026-05-27 | Codex | Completed Sprint 19 Task C: generated top-20 OKX universe JSON from local historical OHLCV and updated `pair_whitelist` |
| 2026-05-27 | Codex | Completed Sprint 19 Task D: downloaded and verified top-20 OKX 5m candles for 2024-07-01 through 2025-05-01 |
| 2026-05-27 | Codex | Completed Sprint 19 Task E same-window top-20 baseline sweep; only `RSITrend` passed the trade-count/drawdown screen |
| 2026-05-27 | Codex | Completed Sprint 19 Task F: `RSITrend` failed 7-fold top-20 walk-forward acceptance on avg OOS Sharpe and profit |
| 2026-05-27 | Codex | Completed Sprint 19 Task G: documented top-20 universe rejection in docs/20 and updated docs indexes |
| 2026-05-27 | Codex | Closed Sprint 19 Task H as not applicable because there are no Step 3 survivors for regime-filter experiments |
| 2026-05-27 | Codex | Closed Sprint 19 Task I as not applicable because no strategy passed the paper-trade acceptance gate |
| 2026-05-27 | Codex | Closed Sprint 19 Task J and ESC lane: no candidate advances; next registered follow-up is daily momentum ranking |
| 2026-05-27 | Devin | Bookkeeping closeout: marked Sprint 19 done, archived its task list, updated AGENTS.md milestone/tally (9 strategies, 9 rejected) |
| 2026-05-27 | Devin | Queued Sprint 21: wrote `docs/21-daily-momentum-ranking.md` and populated `TASKS.md` A–K + ESC with per-agent tier assignments |
| 2026-05-27 | Codex | Completed Sprint 21 Task A: created `codex/sprint-21-daily-momentum` and kept the default 1-day closed-UTC daily momentum lookback |
| 2026-05-27 | Codex | Completed Sprint 21 Task B: added daily momentum ranking CLI plus tests; verified ruff, pytest, and a real-data smoke run |
| 2026-05-27 | Codex | Completed Sprint 21 Task C: wired daily momentum ranking into five thin ranked strategy subclasses with the shared selection helper |
| 2026-05-27 | Codex | Completed Sprint 21 Task D: added selection-helper and ranked-strategy smoke coverage; verified ruff and pytest |
| 2026-05-27 | Codex | Completed Sprint 21 Task E: generated and sanity-checked the full-window daily momentum ranking JSON with 20 pairs on all 304 days |
| 2026-05-27 | Codex | Completed Sprint 21 Task F: ran same-window ranked baseline sweep; EMACrossoverDailyRanked, DonchianBreakoutDailyRanked, and RSITrendDailyRanked passed the Step 1 screen |
| 2026-05-30 | Codex | Completed Sprint 21 Task G: ran 7-fold walk-forward validation for EMACrossoverDailyRanked, DonchianBreakoutDailyRanked, and RSITrendDailyRanked; all failed Step 3 acceptance |
| 2026-05-30 | Codex | Completed Sprint 21 Task H: documented daily momentum ranking rejection in docs/22 and updated docs indexes |
| 2026-05-30 | Codex | Closed Sprint 21 Task I as not applicable because Task G produced no passing Step 3 survivors for regime-filter experiments |
| 2026-05-30 | Codex | Closed Sprint 21 Task J as not applicable because no ranked strategy passed the paper-trade acceptance gate |
| 2026-05-30 | Codex | Closed Sprint 21 Task K and invoked the kill criterion: next sprint should leave spot-indicator variants and evaluate either FreqAI engineered-feature models or a perps plus funding-rate arbitrage track |
| 2026-05-31 | Codex | Completed Sprint 23 Task A: created `codex/sprint-23-higher-timeframes` and confirmed the 2022-01-01 to 2025-05-01 1d window plus pre-registered stoploss/ROI table with no deviations |
| 2026-05-31 | Codex | Completed Sprint 23 Task B: downloaded/prepended OKX 1d, 1w, and 4h candles for BTC/ETH/SOL/BNB; all files landed, with BNB limited to OKX data starting 2022-12-21 |
| 2026-05-31 | Codex | Completed Sprint 23 Task C: added five `*Daily` strategy subclasses plus smoke tests; verified ruff and pytest (80 passed) |
| 2026-05-31 | Codex | Completed Sprint 23 Task D: fixed baseline runner pair/timeframe forwarding, reran the valid Tier 1 four-major 1d screen, and found zero Step 1 survivors |
| 2026-05-31 | Codex | Completed Sprint 23 Task E: added the conditional `MultiTimeframeConfirmation` smoke test stub without implementing the strategy |
| 2026-05-31 | Codex | Completed Sprint 23 Task F as not applicable: no corrected 1d same-window screen survivors advanced to walk-forward; added pair/timeframe forwarding to the walk-forward harness |
