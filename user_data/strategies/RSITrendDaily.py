"""Daily-timeframe RSI trend-pullback strategy."""
from __future__ import annotations

try:
    from user_data.strategies.RSITrend import RSITrend
except ModuleNotFoundError:
    from RSITrend import RSITrend


class RSITrendDaily(RSITrend):
    """RSITrend on 1d candles with pre-registered daily risk settings."""

    timeframe = "1d"
    stoploss = -0.10
    minimal_roi = {"0": 0.20}
