from __future__ import annotations

import importlib

import pandas as pd
import pytest
from pandas import DataFrame

from user_data.strategies.ATRAdaptiveMeanReversion import ATRAdaptiveMeanReversion
from user_data.strategies.MultiTimeframeTrend import MultiTimeframeTrend


class FakeDataProvider:
    def __init__(self, informative: DataFrame) -> None:
        self.informative = informative

    def current_whitelist(self) -> list[str]:
        return ["BTC/USDT"]

    def get_pair_dataframe(self, pair: str, timeframe: str) -> DataFrame:
        assert pair == "BTC/USDT"
        assert timeframe == "4h"
        return self.informative.copy()


def _ohlcv_frame(rows: int, freq: str = "1h") -> DataFrame:
    dates = pd.date_range("2025-01-01", periods=rows, freq=freq, tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    close = 100 + trend * 0.1 + (trend % 12) * 0.03
    return DataFrame(
        {
            "date": dates,
            "open": close - 0.1,
            "high": close + 0.4,
            "low": close - 0.4,
            "close": close,
            "volume": 100 + (trend % 20),
        }
    )


@pytest.mark.parametrize(
    ("module_name", "class_name"),
    [
        ("user_data.strategies.MultiTimeframeTrend", "MultiTimeframeTrend"),
        ("user_data.strategies.ATRAdaptiveMeanReversion", "ATRAdaptiveMeanReversion"),
    ],
)
def test_new_strategy_classes_import(module_name: str, class_name: str):
    module = importlib.import_module(module_name)

    assert getattr(module, class_name).__name__ == class_name


def test_multi_timeframe_trend_smoke_populates_expected_columns():
    strategy = MultiTimeframeTrend({})
    strategy.dp = FakeDataProvider(_ohlcv_frame(180, "4h"))
    dataframe = _ohlcv_frame(520)

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert {
        "rsi",
        "ema_local_1h_50",
        "volume_mean",
        "ema_trend_4h_50_4h",
        "ema_trend_slope_4h_50_4h",
        "enter_long",
        "exit_long",
    }.issubset(exited.columns)
    assert len(exited) == len(dataframe)


def test_atr_adaptive_mean_reversion_smoke_populates_expected_columns():
    strategy = ATRAdaptiveMeanReversion({})
    dataframe = _ohlcv_frame(180)

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert {
        "rsi",
        "sma_20",
        "atr_14",
        "atr_median_14_50",
        "enter_long",
        "exit_long",
    }.issubset(exited.columns)
    assert len(exited) == len(dataframe)
