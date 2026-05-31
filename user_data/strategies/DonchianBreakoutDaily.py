"""Daily-timeframe Donchian breakout strategy."""
from __future__ import annotations

try:
    from user_data.strategies.DonchianBreakout import DonchianBreakout
except ModuleNotFoundError:
    from DonchianBreakout import DonchianBreakout


class DonchianBreakoutDaily(DonchianBreakout):
    """DonchianBreakout on 1d candles with pre-registered daily risk settings."""

    timeframe = "1d"
    stoploss = -0.08
    minimal_roi = {"0": 0.25}
