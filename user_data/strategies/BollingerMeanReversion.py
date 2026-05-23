"""Bollinger Band mean-reversion baseline.

Buy dips below the lower Bollinger Band when RSI confirms oversold conditions,
optionally constrained to long-term uptrends. Exit when price reverts to the
middle band or RSI reaches a neutral-to-strong level.
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


class BollingerMeanReversion(IStrategy):
    """Long-only Bollinger mean-reversion strategy."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.03,
        "30": 0.015,
        "90": 0.005,
        "180": 0.0,
    }
    stoploss = -0.035
    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 240

    bb_window = IntParameter(15, 50, default=20, space="buy", optimize=True)
    bb_stddev = DecimalParameter(1.5, 3.0, default=2.0, decimals=1, space="buy", optimize=True)
    rsi_buy = IntParameter(20, 40, default=30, space="buy", optimize=True)
    rsi_exit = IntParameter(50, 75, default=60, space="sell", optimize=True)
    ema_trend = IntParameter(50, 200, default=100, space="buy", optimize=True)
    use_trend_filter = BooleanParameter(default=True, space="buy", optimize=True)
    min_volume_factor = DecimalParameter(
        0.5, 2.5, default=1.0, decimals=2, space="buy", optimize=True
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        for val in self.bb_window.range:
            rolling_close = dataframe["close"].rolling(window=val)
            dataframe[f"bb_middle_{val}"] = rolling_close.mean()
            dataframe[f"bb_std_{val}"] = rolling_close.std(ddof=0)
        for val in self.ema_trend.range:
            dataframe[f"ema_trend_{val}"] = ta.EMA(dataframe, timeperiod=val)

        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bb_middle = dataframe[f"bb_middle_{self.bb_window.value}"]
        bb_std = dataframe[f"bb_std_{self.bb_window.value}"]
        bb_lower = bb_middle - (bb_std * float(self.bb_stddev.value))

        conditions = [
            dataframe["close"] < bb_lower,
            dataframe["rsi"] < self.rsi_buy.value,
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            dataframe["volume"] > 0,
        ]

        if self.use_trend_filter.value:
            ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]
            conditions.append(dataframe["close"] > ema_trend)

        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bb_middle = dataframe[f"bb_middle_{self.bb_window.value}"]

        dataframe.loc[
            (dataframe["close"] > bb_middle) | (dataframe["rsi"] > self.rsi_exit.value),
            "exit_long",
        ] = 1
        return dataframe
