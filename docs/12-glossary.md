# 12. Glossary

Every term and acronym used elsewhere in the docs, alphabetised.

## A

**ADX** — Average Directional Index. Indicator of trend strength (not direction). > 25 ≈ trending, < 20 ≈ ranging.

**Alt / altcoin** — Any crypto that isn't BTC. By extension, "majors" = BTC + ETH + a handful of liquid large-caps (SOL, BNB, …); "alts" = everything below the top ~20 by market cap, where slippage and manipulation risk go up dramatically.

**API key / secret** — Credentials issued by an exchange that let a bot place orders on your behalf. Should be scoped to **trading only**, **no withdrawal**, and IP-restricted where possible.

**ATR** — Average True Range. The 14-period moving average of "true range" (max of current high–low, |high−prev close|, |low−prev close|). Used for volatility-aware stop placement.

## B

**Backtest** — Replaying historical OHLCV through a strategy as if it had been live, to estimate performance. The output is *not* a prediction; it's a sanity check.

**Bar / candle** — One unit of OHLCV at a given timeframe. "5m candles" = candles whose open is at minute 0/5/10/… UTC.

**Binance.vision** — `https://data.binance.vision`. Binance's public archive of zipped monthly OHLCV CSVs. Geo-unrestricted, immutable, slightly lagged.

**Bollinger bands** — Indicator: SMA(N) ± k × stdev(N). Used for mean-reversion and breakout strategies.

## C

**ccxt** — Open-source unified API for ~100 crypto exchanges. Freqtrade uses ccxt under the hood; switching exchanges is a config change because of ccxt.

**Crossover** — A signal where a fast indicator crosses above (or below) a slow one. The bundled strategy is an EMA crossover.

## D

**DCA (Dollar Cost Average)** — Splitting an entry into multiple sub-entries at different prices. In Freqtrade: `position_adjustment_enable` + `adjust_trade_position()`.

**Drawdown** — Peak-to-trough decline in equity. Always measured in %. Max drawdown is the worst single drawdown over a backtest or live period.

**Dry-run** — Freqtrade mode where the bot connects to live market data but simulates fills instead of placing real orders. The default in this repo's config.

## E

**EMA (Exponential Moving Average)** — Moving average that weights recent prices more heavily than older ones. Reacts faster to changes than SMA, at the cost of more noise.

**Edge** — A repeatable reason why your trades have positive expected value after fees and slippage. Without edge, leverage just accelerates losses.

**Equity** — Current total value of your account (cash + open positions marked to market).

**Exit signal** — A condition that closes an open trade, separately from the stop-loss or ROI ladder. In Freqtrade, set by `populate_exit_trend`.

## F

**Feather** — Apache Arrow's columnar binary format. Freqtrade's default on-disk format for OHLCV; fast to read in pandas (`pd.read_feather`).

**Fee** — Exchange commission per trade. Modelled in the Freqtrade config; in this repo's `config.json` the default is exchange-derived.

**Forward test / paper trade** — Running the strategy in dry-run on **future** market data, to validate that backtest results survive contact with reality.

**FreqAI** — Freqtrade's ML plug-in for using regressors / classifiers (sklearn, lightgbm, pytorch) inside a strategy.

**Freqtrade** — The Python trading bot framework this repo is built on. <https://www.freqtrade.io/>.

## H

**Hyperopt** — Freqtrade's parameter optimiser. Searches `IntParameter` / `DecimalParameter` / `CategoricalParameter` / `BooleanParameter` declarations for the combination that minimises a chosen loss function.

**Hyperopt loss** — The single scalar hyperopt is trying to minimise (e.g. `-Sharpe`). Choice of loss function dramatically changes which parameters "win".

## I

**In-sample / out-of-sample** — Split historical data into a window you tune on (in-sample) and a window you only evaluate on (out-of-sample). Walk-forward formalises this.

**Indicator** — Any value derived from price/volume — e.g. EMA, RSI, ATR, MACD. Computed in `populate_indicators`.

## K

**Kline** — Binance's term for "candle". Used in the `data.binance.vision` URL scheme.

## L

**Leverage** — Borrowed capital multiplying your effective position size. Spot = 1×. Perpetual futures = 1–100×. Multiplies losses linearly; multiplies blow-up probability super-linearly.

**Limit order** — Order to buy/sell at a specified price or better. May not fill.

**Liquidation** — Forced close of a leveraged position when the loss reaches the maintenance margin. *Not* the same as a stop-loss — liquidations are typically priced worse and accompanied by exchange-level fees.

**Look-ahead bias** — Using information from the future in a backtest. Usually accidental (`.shift(-1)`, peek at end-of-day close, etc.). Makes backtests look great and live trading lose money.

## M

**MACD** — Moving Average Convergence/Divergence. Indicator: (12-EMA − 26-EMA) plotted with a 9-period EMA of itself as a signal line.

**Market order** — Order to buy/sell immediately at the best available price. Always fills, but at a worse effective price than the displayed top of book on small accounts.

**Maker fee / taker fee** — Maker = order rests on the book and is filled later (a limit order at the spread or better). Taker = order executes immediately against an existing order (a market order, or a limit order that crosses the spread). Taker fees are higher on most exchanges.

**Max drawdown** — See "drawdown".

**Mean reversion** — Family of strategies that bet prices return to a moving average / range. Works in low-volatility regimes; gets crushed in trends.

## O

**OHLCV** — Open, High, Low, Close, Volume — the five numbers per candle. The primitive input to almost every strategy.

**OKX** — Crypto exchange. Default in this repo because its public market data is reachable from any IP.

**Optimisation** — See "hyperopt". Note: the spelling is "optimi**s**ation" in the docs (en-GB) — a holdover from Freqtrade's own docs.

**Overfit** — A strategy whose backtest looks great because the parameters were tuned to noise in the specific window. Walks-forward apart at the first regime change.

## P

**Paper trade** — See "dry-run" / "forward test".

**Pair** — Two assets traded against each other. `BTC/USDT` means BTC quoted in USDT.

**ROI** — Return on Investment. In Freqtrade, the `minimal_roi` table is the "take-profit ladder" — exit at +X% after Y minutes.

**Position size** — How much of an asset you hold. Determined per trade by the position-sizing rule (this repo defaults to 1% of equity at risk per trade).

**Protection** — Freqtrade construct that disables trading on a pair under certain conditions (max drawdown, low-profit pair, cooldown). See `protections` in the config.

## R

**Range** (Freqtrade) — `IntParameter(...).range` gives every candidate value in the search space. Used in `populate_indicators` to pre-compute one column per candidate so hyperopt actually varies indicator periods.

**Regime** — Market state: trending up, trending down, ranging, high-volatility, low-volatility, etc. A strategy that profits in one regime almost always loses in others.

**RSI** — Relative Strength Index. Bounded oscillator (0–100) measuring up-day vs down-day momentum over N periods. < 30 = oversold, > 70 = overbought.

## S

**Sharpe ratio** — (mean daily return − risk-free rate) / stdev of daily return × √252. Risk-adjusted return. Above 1 is decent for retail, above 2 is rare and probably overfit.

**Slippage** — Difference between the price you expected to fill at and the price you actually got. Real on small accounts and dominates on illiquid pairs.

**Spread** — Difference between best bid and best ask. The minimum cost of trading.

**Stake amount** — Notional value per trade in quote currency (USDT). Set in `config.json` (`stake_amount`).

**Stop-loss** — Exit at a specified price to cap loss. Usually placed below entry (long) or above (short). In Freqtrade: `stoploss = -0.03` = 3% from entry.

**Stoploss-on-exchange** — Whether the stop is held by the exchange (a real working order) or by Freqtrade (a virtual stop that the bot closes when triggered). Almost always `False` on spot; the bot's stop is more reliable than the exchange's on most CEXs.

## T

**TA-Lib** — Open-source technical-analysis C library. The `talib` Python wrapper depends on the C library being installed. Source of the most common setup pain in this repo.

**Telegram bot** — Freqtrade's notification + remote-control interface. Configure under `telegram` in `config.json`.

**Timeframe** — Granularity of candles: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`. Lower = more trades, more noise, more fees. Higher = fewer trades, harder to backtest meaningfully.

**Trade** — One round trip: open + close. Tracked in the bot's SQLite DB.

**Trend filter** — A condition that suppresses entries when the larger trend is the wrong direction. In `EMACrossover`: long only when `close > EMA(200)`.

## U

**USDT / USDC** — Stablecoins pegged to USD. The default quote currency for crypto majors on most exchanges.

## V

**Vectorised backtest** — Replaying a strategy with pandas array operations rather than a bar-by-bar event loop. Much faster, but skips fees/slippage/order-book modelling. Use for triage, not for production claims. `vectorbt` is a popular library for this.

**Volume** — Amount traded in a candle, in base units (BTC) or quote units (USDT) depending on exchange convention.

## W

**Walk-forward** — Repeatedly tune on a window then evaluate on the next window, sliding through history. The minimum honest test of a strategy. See [Hyperopt](06-hyperopt.md) §6.4.

**Whitelist / blacklist** — `pair_whitelist` is the universe the bot trades; `pair_blacklist` overrides it. Both live under `exchange` in the config.

---

Back to the [docs index](README.md).
