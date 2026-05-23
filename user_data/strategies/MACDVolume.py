"""MACD signal cross with volume confirmation baseline.

Enter long when the MACD line crosses above its signal line while volume is
above its recent average. Exit when MACD crosses back below the signal line.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from pandas import DataFrame


class MACDVolume(IStrategy):
    """Long-only MACD crossover strategy with volume confirmation."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.04,
        "45": 0.02,
        "120": 0.005,
        "240": 0.0,
    }
    stoploss = -0.035
    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 240

    macd_fast = IntParameter(8, 16, default=12, space="buy", optimize=True)
    macd_slow = IntParameter(20, 35, default=26, space="buy", optimize=True)
    macd_signal = IntParameter(5, 12, default=9, space="buy", optimize=True)
    min_volume_factor = DecimalParameter(
        0.5, 3.0, default=1.2, decimals=2, space="buy", optimize=True
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
        for val in self.macd_fast.range:
            dataframe[f"ema_fast_{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.macd_slow.range:
            dataframe[f"ema_slow_{val}"] = ta.EMA(dataframe, timeperiod=val)
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd_line, macd_signal = self._macd_series(dataframe)

        conditions = [
            macd_line > macd_signal,
            macd_line.shift(1) <= macd_signal.shift(1),
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd_line, macd_signal = self._macd_series(dataframe)

        dataframe.loc[
            (macd_line < macd_signal) & (macd_line.shift(1) >= macd_signal.shift(1)),
            "exit_long",
        ] = 1
        return dataframe

    def _macd_series(self, dataframe: DataFrame):
        fast_ema = dataframe[f"ema_fast_{self.macd_fast.value}"]
        slow_ema = dataframe[f"ema_slow_{self.macd_slow.value}"]
        macd_line = fast_ema - slow_ema
        macd_signal = macd_line.ewm(
            span=self.macd_signal.value,
            adjust=False,
            min_periods=self.macd_signal.value,
        ).mean()
        return macd_line, macd_signal
