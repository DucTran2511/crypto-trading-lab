"""Daily-timeframe Bollinger mean-reversion strategy."""
from __future__ import annotations

try:
    from user_data.strategies.BollingerMeanReversion import BollingerMeanReversion
except ModuleNotFoundError:
    from BollingerMeanReversion import BollingerMeanReversion


class BollingerMeanReversionDaily(BollingerMeanReversion):
    """BollingerMeanReversion on 1d candles with pre-registered daily risk settings."""

    timeframe = "1d"
    stoploss = -0.06
    minimal_roi = {"0": 0.08}
