"""RSI(14) pullback with trend filter baseline.

Enter long when RSI(14) crosses back above an oversold threshold while price is
above a long-term EMA trend filter. Exit when RSI reaches a high threshold or
price loses the trend filter.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from pandas import DataFrame


class RSITrend(IStrategy):
    """Long-only RSI(14) trend-pullback strategy."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.035,
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

    rsi_buy = IntParameter(25, 45, default=35, space="buy", optimize=True)
    rsi_exit = IntParameter(60, 85, default=70, space="sell", optimize=True)
    ema_trend = IntParameter(50, 200, default=100, space="buy", optimize=True)
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
        for val in self.ema_trend.range:
            dataframe[f"ema_trend_{val}"] = ta.EMA(dataframe, timeperiod=val)
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]

        conditions = [
            dataframe["close"] > ema_trend,
            dataframe["rsi"] > self.rsi_buy.value,
            dataframe["rsi"].shift(1) <= self.rsi_buy.value,
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_trend = dataframe[f"ema_trend_{self.ema_trend.value}"]

        dataframe.loc[
            (dataframe["rsi"] > self.rsi_exit.value) | (dataframe["close"] < ema_trend),
            "exit_long",
        ] = 1
        return dataframe
