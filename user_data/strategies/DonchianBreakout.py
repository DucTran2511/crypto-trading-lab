"""Donchian channel breakout baseline.

Go long when price breaks above the prior Donchian high with volume
confirmation and a long-term EMA trend filter. Exit when price falls below the
prior Donchian low. This is a classic trend-following baseline for comparing
against more complex breakout systems.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from pandas import DataFrame


class DonchianBreakout(IStrategy):
    """Long-only Donchian breakout strategy with volume and trend filters."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.05,
        "60": 0.03,
        "180": 0.01,
        "360": 0.0,
    }
    stoploss = -0.04
    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 240

    entry_window = IntParameter(20, 80, default=55, space="buy", optimize=True)
    exit_window = IntParameter(10, 40, default=20, space="sell", optimize=True)
    ema_trend = IntParameter(50, 200, default=100, space="buy", optimize=True)
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
        for val in self.entry_window.range:
            dataframe[f"donchian_high_{val}"] = dataframe["high"].rolling(val).max().shift(1)
        for val in self.exit_window.range:
            dataframe[f"donchian_low_{val}"] = dataframe["low"].rolling(val).min().shift(1)
        for val in self.ema_trend.range:
            dataframe[f"ema_trend_{val}"] = ta.EMA(dataframe, timeperiod=val)

        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        donchian_high = dataframe[f"donchian_high_{self.entry_window.value}"]
        ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]

        conditions = [
            dataframe["close"] > donchian_high,
            dataframe["close"] > ema_trend,
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        donchian_low = dataframe[f"donchian_low_{self.exit_window.value}"]

        dataframe.loc[
            dataframe["close"] < donchian_low,
            "exit_long",
        ] = 1
        return dataframe
