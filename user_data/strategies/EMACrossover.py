"""EMA crossover strategy.

A classic momentum baseline: go long when a fast EMA crosses above a slow EMA,
exit when it crosses back. This is intentionally simple — it is a starting point
for research, not a production-ready edge.

Risk controls applied on top of the raw crossover:
- Hard stoploss (configurable, default -3%).
- ROI ladder so winners are taken systematically.
- Volume filter to avoid illiquid candles.
- Optional trend filter using a longer EMA on the same timeframe.

All numeric parameters are exposed as ``IntParameter`` / ``DecimalParameter`` so
they can be tuned with ``freqtrade hyperopt``.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import (
    BooleanParameter,
    DecimalParameter,
    IntParameter,
    IStrategy,
)
from pandas import DataFrame


class EMACrossover(IStrategy):
    """Fast/slow EMA crossover with a trend filter and basic risk controls."""

    INTERFACE_VERSION = 3

    # Spot, long-only.
    can_short = False

    # ROI ladder: take 4% immediately, 2% after 30m, 1% after 60m, exit flat after 2h.
    minimal_roi = {
        "0": 0.04,
        "30": 0.02,
        "60": 0.01,
        "120": 0.0,
    }

    stoploss = -0.03
    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    timeframe = "5m"
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 200

    # Tunable parameters (hyperopt-able).
    ema_fast = IntParameter(5, 25, default=9, space="buy", optimize=True)
    ema_slow = IntParameter(15, 60, default=21, space="buy", optimize=True)
    ema_trend = IntParameter(50, 200, default=100, space="buy", optimize=True)
    use_trend_filter = BooleanParameter(default=True, space="buy", optimize=True)

    min_volume_factor = DecimalParameter(
        0.5, 3.0, default=1.0, decimals=2, space="buy", optimize=True
    )

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {
        "entry": "GTC",
        "exit": "GTC",
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Pre-compute every candidate EMA period across the hyperopt search space.
        # Freqtrade caches the output of populate_indicators() once per pair, so
        # consuming ``self.ema_fast.value`` here would lock the EMA periods to
        # their defaults for every hyperopt trial. By materialising one column
        # per candidate period we let populate_entry_trend / populate_exit_trend
        # select the right one per trial from the cached frame.
        for val in self.ema_fast.range:
            dataframe[f"ema_fast_{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.ema_slow.range:
            dataframe[f"ema_slow_{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.ema_trend.range:
            dataframe[f"ema_trend_{val}"] = ta.EMA(dataframe, timeperiod=val)
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast = dataframe[f"ema_fast_{self.ema_fast.value}"]
        ema_slow = dataframe[f"ema_slow_{self.ema_slow.value}"]

        conditions = [
            # Fast EMA crossed above slow EMA on this candle.
            (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1)),
            # Volume confirmation.
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            # Non-zero volume sanity.
            dataframe["volume"] > 0,
        ]

        if self.use_trend_filter.value:
            ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]
            conditions.append(dataframe["close"] > ema_trend)

        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_fast = dataframe[f"ema_fast_{self.ema_fast.value}"]
        ema_slow = dataframe[f"ema_slow_{self.ema_slow.value}"]

        # Exit when fast EMA crosses back below slow EMA.
        dataframe.loc[
            (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1)),
            "exit_long",
        ] = 1
        return dataframe
