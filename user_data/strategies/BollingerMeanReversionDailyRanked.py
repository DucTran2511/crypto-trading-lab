"""Daily-momentum-ranked Bollinger mean-reversion strategy."""

from __future__ import annotations

import sys
from pathlib import Path

from pandas import DataFrame

try:
    from user_data.selection.daily_momentum import DailyMomentumRankedMixin
    from user_data.strategies.BollingerMeanReversion import BollingerMeanReversion
except ModuleNotFoundError as exc:
    if exc.name != "user_data":
        raise
    user_data_dir = Path(__file__).resolve().parents[1]
    strategies_dir = Path(__file__).resolve().parent
    sys.path.extend(str(path) for path in (user_data_dir, strategies_dir) if str(path) not in sys.path)
    from BollingerMeanReversion import BollingerMeanReversion
    from selection.daily_momentum import DailyMomentumRankedMixin


class BollingerMeanReversionDailyRanked(DailyMomentumRankedMixin, BollingerMeanReversion):
    """BollingerMeanReversion with entries restricted to the daily momentum top 3."""

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        return self._apply_daily_momentum_gate(dataframe, metadata)
