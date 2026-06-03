from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from user_data.strategies.DonchianBreakoutDaily import DonchianBreakoutDaily
from user_data.strategies.DonchianBreakoutDailyTop20 import DonchianBreakoutDailyTop20


def _daily_ohlcv_frame(rows: int = 320) -> DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="1D", tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    close = 100 + trend * 0.15 + ((trend % 30) - 15) * 0.4
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


def test_donchian_breakout_daily_top20_smoke_inherits_daily_logic():
    strategy = DonchianBreakoutDailyTop20({})
    dataframe = _daily_ohlcv_frame()

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert isinstance(strategy, DonchianBreakoutDaily)
    assert strategy.timeframe == "1d"
    assert strategy.stoploss == -0.08
    assert strategy.minimal_roi == {"0": 0.25}
    assert {"enter_long", "exit_long"}.issubset(exited.columns)
    assert len(exited) == len(dataframe)
