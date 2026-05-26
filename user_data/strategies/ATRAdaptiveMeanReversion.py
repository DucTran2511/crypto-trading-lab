"""ATR-adaptive mean-reversion strategy.

Buy unusually deep 1h dips below a moving average only when volatility is
contracted and RSI confirms oversold pressure. Exit when price returns to the
mean or ATR expansion suggests the ranging regime has broken.
"""
from __future__ import annotations

from functools import reduce

import pandas as pd
import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from pandas import DataFrame


class ATRAdaptiveMeanReversion(IStrategy):
    """Long-only ATR-gated mean-reversion strategy."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.04,
        "240": 0.02,
        "720": 0.005,
        "1440": 0.0,
    }
    stoploss = -0.05
    timeframe = "1h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 160

    atr_entry_multiplier = DecimalParameter(
        1.0, 3.0, default=1.5, decimals=1, space="buy", optimize=True
    )
    sma_period = IntParameter(15, 30, default=20, space="buy", optimize=True)
    atr_period = IntParameter(10, 20, default=14, space="buy", optimize=True)
    atr_median_lookback = IntParameter(30, 100, default=50, space="buy", optimize=True)
    rsi_oversold = IntParameter(25, 40, default=35, space="buy", optimize=True)
    atr_exit_multiplier = DecimalParameter(
        1.0, 2.5, default=1.5, decimals=1, space="sell", optimize=True
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

        indicator_columns = {}
        for val in self.sma_period.range:
            indicator_columns[f"sma_{val}"] = dataframe["close"].rolling(window=val).mean()

        for atr_period in self.atr_period.range:
            atr = ta.ATR(dataframe, timeperiod=atr_period)
            indicator_columns[f"atr_{atr_period}"] = atr
            for lookback in self.atr_median_lookback.range:
                indicator_columns[f"atr_median_{atr_period}_{lookback}"] = atr.rolling(
                    window=lookback
                ).median()

        if indicator_columns:
            dataframe = pd.concat([dataframe, pd.DataFrame(indicator_columns)], axis=1)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sma = dataframe[f"sma_{self.sma_period.value}"]
        atr = dataframe[f"atr_{self.atr_period.value}"]
        atr_median = dataframe[
            f"atr_median_{self.atr_period.value}_{self.atr_median_lookback.value}"
        ]
        adaptive_lower = sma - (atr * float(self.atr_entry_multiplier.value))

        conditions = [
            dataframe["close"] < adaptive_lower,
            atr < atr_median,
            dataframe["rsi"] < self.rsi_oversold.value,
            dataframe["volume"] > 0,
        ]

        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sma = dataframe[f"sma_{self.sma_period.value}"]
        atr = dataframe[f"atr_{self.atr_period.value}"]
        atr_median = dataframe[
            f"atr_median_{self.atr_period.value}_{self.atr_median_lookback.value}"
        ]

        dataframe.loc[
            (dataframe["close"] >= sma)
            | (atr > atr_median * float(self.atr_exit_multiplier.value)),
            "exit_long",
        ] = 1
        return dataframe
