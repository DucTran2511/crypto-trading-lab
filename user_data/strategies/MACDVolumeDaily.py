"""Daily-timeframe MACD volume-confirmation strategy."""
from __future__ import annotations

try:
    from user_data.strategies.MACDVolume import MACDVolume
except ModuleNotFoundError:
    from MACDVolume import MACDVolume


class MACDVolumeDaily(MACDVolume):
    """MACDVolume on 1d candles with pre-registered daily risk settings."""

    timeframe = "1d"
    stoploss = -0.10
    minimal_roi = {"0": 0.20}
