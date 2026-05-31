from __future__ import annotations

import importlib

import pandas as pd
import pytest
from pandas import DataFrame


def _daily_ohlcv_frame(rows: int = 320) -> DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="1D", tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    wave = (trend % 30) - 15
    close = 100 + trend * 0.15 + wave * 0.4
    return DataFrame(
        {
            "date": dates,
            "open": close - 0.5,
            "high": close + 1.2,
            "low": close - 1.2,
            "close": close,
            "volume": 1_000 + (trend % 40) * 10,
        }
    )


@pytest.mark.parametrize(
    ("module_name", "class_name", "stoploss", "minimal_roi"),
    [
        ("user_data.strategies.EMACrossoverDaily", "EMACrossoverDaily", -0.10, {"0": 0.20}),
        (
            "user_data.strategies.DonchianBreakoutDaily",
            "DonchianBreakoutDaily",
            -0.08,
            {"0": 0.25},
        ),
        (
            "user_data.strategies.BollingerMeanReversionDaily",
            "BollingerMeanReversionDaily",
            -0.06,
            {"0": 0.08},
        ),
        ("user_data.strategies.RSITrendDaily", "RSITrendDaily", -0.10, {"0": 0.20}),
        ("user_data.strategies.MACDVolumeDaily", "MACDVolumeDaily", -0.10, {"0": 0.20}),
    ],
)
def test_daily_strategy_smoke_runs_inherited_methods(
    module_name: str,
    class_name: str,
    stoploss: float,
    minimal_roi: dict[str, float],
):
    module = importlib.import_module(module_name)
    strategy_cls = getattr(module, class_name)
    strategy = strategy_cls({})
    dataframe = _daily_ohlcv_frame()

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert strategy.timeframe == "1d"
    assert strategy.stoploss == stoploss
    assert strategy.minimal_roi == minimal_roi
    assert len(exited) == len(dataframe)
