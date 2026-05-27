"""Daily-momentum-ranked EMA crossover strategy."""

from __future__ import annotations

from pandas import DataFrame

from user_data.selection.daily_momentum import DailyMomentumRankedMixin
from user_data.strategies.EMACrossover import EMACrossover


class EMACrossoverDailyRanked(DailyMomentumRankedMixin, EMACrossover):
    """EMACrossover with entries restricted to the daily momentum top 3."""

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        return self._apply_daily_momentum_gate(dataframe, metadata)
