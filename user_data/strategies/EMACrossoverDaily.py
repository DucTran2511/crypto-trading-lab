"""Daily-timeframe EMA crossover strategy."""
from __future__ import annotations

try:
    from user_data.strategies.EMACrossover import EMACrossover
except ModuleNotFoundError:
    from EMACrossover import EMACrossover


class EMACrossoverDaily(EMACrossover):
    """EMACrossover on 1d candles with pre-registered daily risk settings."""

    timeframe = "1d"
    stoploss = -0.10
    minimal_roi = {"0": 0.20}
