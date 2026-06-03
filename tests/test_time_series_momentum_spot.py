from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from user_data.strategies.TimeSeriesMomentumSpot import TimeSeriesMomentumSpot


def _daily_momentum_frame(rows: int = 260) -> DataFrame:
    dates = pd.date_range("2023-01-01", periods=rows, freq="1D", tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    cycle = ((trend % 16) - 8).abs()
    close = 100 + trend * 0.35 + cycle * 0.25
    return DataFrame(
        {
            "date": dates,
            "open": close - 0.4,
            "high": close + 0.8,
            "low": close - 0.8,
            "close": close,
            "volume": 1_000 + (trend % 15) * 25,
        }
    )


def test_time_series_momentum_spot_smoke_populates_expected_columns():
    strategy = TimeSeriesMomentumSpot({})
    dataframe = _daily_momentum_frame()

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert strategy.timeframe == "1d"
    assert strategy.stoploss == -0.25
    assert strategy.minimal_roi == {"0": 100.0}
    assert {
        "ema_50",
        "ema_200",
        "rsi",
        "rsi_crossed_up_50_recent",
        "realized_vol_5d",
        "realized_vol_25",
        "realized_vol_75",
        "enter_long",
        "exit_long",
    }.issubset(exited.columns)
    assert len(exited) == len(dataframe)


def test_time_series_momentum_spot_entry_signal_has_no_lookahead():
    strategy = TimeSeriesMomentumSpot({})
    dataframe = _daily_momentum_frame(320)
    mutated_future = dataframe.copy()
    cutoff = 240
    mutated_future.loc[cutoff + 1 :, ["open", "high", "low", "close", "volume"]] = 1.0

    original = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    original = strategy.populate_entry_trend(original, {"pair": "BTC/USDT"})
    mutated = strategy.populate_indicators(mutated_future.copy(), {"pair": "BTC/USDT"})
    mutated = strategy.populate_entry_trend(mutated, {"pair": "BTC/USDT"})

    pd.testing.assert_series_equal(
        original.loc[:cutoff, "enter_long"],
        mutated.loc[:cutoff, "enter_long"],
        check_names=False,
    )
