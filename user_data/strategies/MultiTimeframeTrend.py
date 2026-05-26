"""Multi-timeframe trend pullback strategy.

Enter long on 1h RSI pullback recoveries only when the 4h trend is aligned up.
The 4h EMA slope acts as the primary filter, while the 1h EMA and volume filters
keep entries in liquid local uptrends.
"""
from __future__ import annotations

from functools import reduce

import talib.abstract as ta
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair
from pandas import DataFrame, concat


class MultiTimeframeTrend(IStrategy):
    """Long-only 1h pullback strategy with 4h trend confirmation."""

    INTERFACE_VERSION = 3
    can_short = False

    minimal_roi = {
        "0": 0.05,
        "240": 0.03,
        "720": 0.01,
        "1440": 0.0,
    }
    stoploss = -0.05
    timeframe = "1h"
    informative_timeframe = "4h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 400

    ema_trend_4h = IntParameter(20, 100, default=50, space="buy", optimize=True)
    rsi_entry_threshold = IntParameter(25, 45, default=40, space="buy", optimize=True)
    rsi_recovery_window = IntParameter(2, 8, default=4, space="buy", optimize=True)
    ema_local_1h = IntParameter(20, 100, default=50, space="buy", optimize=True)
    min_volume_factor = DecimalParameter(
        0.5, 3.0, default=1.0, decimals=2, space="buy", optimize=True
    )
    rsi_exit_threshold = IntParameter(65, 80, default=70, space="sell", optimize=True)

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

    def informative_pairs(self) -> list[tuple[str, str]]:
        dataprovider = getattr(self, "dp", None)
        if dataprovider is None:
            return []
        return [(pair, self.informative_timeframe) for pair in dataprovider.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = ta.RSI(dataframe, timeperiod=14)
        indicator_columns = {"rsi": rsi}
        for val in self.ema_local_1h.range:
            indicator_columns[f"ema_local_1h_{val}"] = ta.EMA(dataframe, timeperiod=val)
        indicator_columns["volume_mean"] = dataframe["volume"].rolling(window=20).mean()
        for threshold in self.rsi_entry_threshold.range:
            for window in self.rsi_recovery_window.range:
                recent_pullback = rsi.shift(1).rolling(window=window, min_periods=1).min() < threshold
                indicator_columns[f"rsi_recovered_{threshold}_{window}"] = (
                    rsi > threshold
                ) & recent_pullback
        dataframe = concat([dataframe, DataFrame(indicator_columns, index=dataframe.index)], axis=1)

        informative = self._get_informative_dataframe(dataframe, metadata)
        informative = self._populate_informative_indicators(informative)

        if not self._can_merge_informative(dataframe, informative):
            return self._populate_informative_fallback(dataframe)

        return merge_informative_pair(
            dataframe,
            informative,
            self.timeframe,
            self.informative_timeframe,
            ffill=True,
        )

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0

        ema_local = dataframe[f"ema_local_1h_{self.ema_local_1h.value}"]
        ema_slope_4h = dataframe[f"ema_trend_slope_4h_{self.ema_trend_4h.value}_4h"]
        rsi_recovered = dataframe[
            f"rsi_recovered_{self.rsi_entry_threshold.value}_{self.rsi_recovery_window.value}"
        ]

        conditions = [
            ema_slope_4h > 0,
            rsi_recovered,
            dataframe["close"] > ema_local,
            dataframe["volume"] > dataframe["volume_mean"] * float(self.min_volume_factor.value),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0

        ema_slope_4h = dataframe[f"ema_trend_slope_4h_{self.ema_trend_4h.value}_4h"]
        rsi_exit = self.rsi_exit_threshold.value
        dataframe.loc[
            (ema_slope_4h < 0)
            | ((dataframe["rsi"] > rsi_exit) & (dataframe["rsi"].shift(1) <= rsi_exit)),
            "exit_long",
        ] = 1
        return dataframe

    def _get_informative_dataframe(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataprovider = getattr(self, "dp", None)
        if dataprovider is None:
            return dataframe.copy()

        informative = dataprovider.get_pair_dataframe(
            pair=metadata["pair"],
            timeframe=self.informative_timeframe,
        )
        if informative.empty:
            return dataframe.copy()
        return informative

    def _populate_informative_indicators(self, informative: DataFrame) -> DataFrame:
        informative_columns = {}
        for val in self.ema_trend_4h.range:
            ema = ta.EMA(informative, timeperiod=val)
            informative_columns[f"ema_trend_4h_{val}"] = ema
            informative_columns[f"ema_trend_slope_4h_{val}"] = ema - ema.shift(5)

        return concat(
            [informative, DataFrame(informative_columns, index=informative.index)],
            axis=1,
        )

    def _populate_informative_fallback(self, dataframe: DataFrame) -> DataFrame:
        informative_columns = {}
        for val in self.ema_trend_4h.range:
            ema = ta.EMA(dataframe, timeperiod=val)
            informative_columns[f"ema_trend_4h_{val}_4h"] = ema
            informative_columns[f"ema_trend_slope_4h_{val}_4h"] = ema - ema.shift(5)

        return concat(
            [dataframe, DataFrame(informative_columns, index=dataframe.index)],
            axis=1,
        )

    @staticmethod
    def _can_merge_informative(dataframe: DataFrame, informative: DataFrame) -> bool:
        return "date" in dataframe.columns and "date" in informative.columns and not informative.empty
