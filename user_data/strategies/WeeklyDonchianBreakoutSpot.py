"""Weekly Donchian breakout strategy for Sprint 25 spot trend testing."""
from __future__ import annotations

try:
    from user_data.strategies.DonchianBreakout import DonchianBreakout
except ModuleNotFoundError:
    from DonchianBreakout import DonchianBreakout


class _FixedParameter:
    """Small value/range shim for inherited strategy code without hyperopt exposure."""

    def __init__(self, value: int | float) -> None:
        self.value = value
        self.range = (value,)


class WeeklyDonchianBreakoutSpot(DonchianBreakout):
    """DonchianBreakout on 1w candles with pre-registered weekly settings."""

    timeframe = "1w"
    stoploss = -0.20
    minimal_roi = {"0": 100.0}
    startup_candle_count: int = 240

    entry_window = _FixedParameter(20)
    exit_window = _FixedParameter(10)
    ema_trend = _FixedParameter(100)
    min_volume_factor = _FixedParameter(1.0)
