"""Daily time-series momentum strategy for Sprint 25 spot trend testing.

Enter long only when price and EMA trend filters are aligned, RSI has recently
crossed back above 50, and short-term realized volatility sits in the middle of
its trailing distribution. Exit on a daily EMA death cross or loss of the
long-term EMA trend.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class TimeSeriesMomentumSpot(IStrategy):
    """Long-only daily momentum strategy with a realized-volatility filter."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.25
    timeframe = "1d"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 220

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
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        rsi_cross_up_50 = (dataframe["rsi"] > 50) & (dataframe["rsi"].shift(1) <= 50)
        dataframe["rsi_crossed_up_50_recent"] = (
            rsi_cross_up_50.astype(int).rolling(window=5, min_periods=1).max().astype(bool)
        )

        dataframe["realized_vol_5d"] = dataframe["close"].pct_change().rolling(window=5).std()
        realized_vol_window = dataframe["realized_vol_5d"].rolling(window=100, min_periods=100)
        dataframe["realized_vol_25"] = realized_vol_window.quantile(0.25)
        dataframe["realized_vol_75"] = realized_vol_window.quantile(0.75)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0

        conditions = [
            dataframe["close"] > dataframe["ema_200"],
            dataframe["ema_50"] > dataframe["ema_200"],
            dataframe["rsi_crossed_up_50_recent"],
            dataframe["realized_vol_5d"] >= dataframe["realized_vol_25"],
            dataframe["realized_vol_5d"] <= dataframe["realized_vol_75"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda left, right: left & right, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0

        ema_death_cross = (dataframe["ema_50"] < dataframe["ema_200"]) & (
            dataframe["ema_50"].shift(1) >= dataframe["ema_200"].shift(1)
        )
        dataframe.loc[
            ema_death_cross | (dataframe["close"] < dataframe["ema_200"]),
            "exit_long",
        ] = 1
        return dataframe
