from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from user_data.strategies.WeeklyDonchianBreakoutSpot import WeeklyDonchianBreakoutSpot


def _weekly_ohlcv_frame(rows: int = 260) -> DataFrame:
    dates = pd.date_range("2020-01-06", periods=rows, freq="1W-MON", tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    close = 100 + trend * 0.8 + (trend % 8) * 0.25
    return DataFrame(
        {
            "date": dates,
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1_000 + (trend % 20) * 20,
        }
    )


def test_weekly_donchian_breakout_spot_smoke_runs_inherited_methods():
    strategy = WeeklyDonchianBreakoutSpot({})
    dataframe = _weekly_ohlcv_frame()

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert strategy.timeframe == "1w"
    assert strategy.stoploss == -0.20
    assert strategy.minimal_roi == {"0": 100.0}
    assert strategy.entry_window.value == 20
    assert strategy.exit_window.value == 10
    assert {"donchian_high_20", "donchian_low_10", "enter_long", "exit_long"}.issubset(
        exited.columns
    )
    assert len(exited) == len(dataframe)
