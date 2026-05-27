"""Daily momentum ranking helper for strategy entry gating."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from pandas import DataFrame, Series

DEFAULT_RANKING_PATH = Path("user_data/universes/daily_momentum_rank_20240701-20250501.json")
DEFAULT_TOP_N = 3


def is_pair_in_today_top_n(
    pair: str,
    candle_date: object,
    n: int,
    ranking_path: str | Path = DEFAULT_RANKING_PATH,
) -> bool:
    """Convenience wrapper for one-off daily momentum eligibility checks."""

    return DailyMomentumSelection(ranking_path).is_pair_in_today_top_n(pair, candle_date, n)


class DailyMomentumSelection:
    """Load a daily pair ranking JSON and answer top-N eligibility queries."""

    def __init__(self, ranking_path: str | Path = DEFAULT_RANKING_PATH) -> None:
        self.ranking_path = Path(ranking_path)
        self._rankings: dict[str, list[str]] | None = None

    @property
    def rankings(self) -> dict[str, list[str]]:
        if self._rankings is None:
            self._rankings = load_daily_momentum_rankings(self.ranking_path)
        return self._rankings

    def is_pair_in_today_top_n(self, pair: str, candle_date: object, n: int) -> bool:
        """Return whether ``pair`` is in the effective ranking for ``candle_date``."""

        if n <= 0:
            raise ValueError("n must be greater than zero")

        ranking_key = date_key(candle_date)
        return pair in self.rankings.get(ranking_key, [])[:n]

    def eligible_mask(self, dataframe: DataFrame, pair: str, n: int) -> Series:
        """Return a boolean mask for rows whose date ranks ``pair`` in the top N."""

        if "date" not in dataframe.columns:
            raise ValueError("dataframe must include a 'date' column for daily momentum gating")
        if n <= 0:
            raise ValueError("n must be greater than zero")

        eligible_dates = {
            ranking_date
            for ranking_date, ranked_pairs in self.rankings.items()
            if pair in ranked_pairs[:n]
        }
        row_dates = pd.to_datetime(dataframe["date"], utc=True).dt.strftime("%Y-%m-%d")
        return row_dates.isin(eligible_dates)


class DailyMomentumRankedMixin:
    """Mixin for ranked strategy subclasses that gate long entries by daily momentum."""

    daily_momentum_ranking_path: str | Path = DEFAULT_RANKING_PATH
    daily_momentum_top_n: int = DEFAULT_TOP_N

    @property
    def daily_momentum_selection(self) -> DailyMomentumSelection:
        selection = getattr(self, "_daily_momentum_selection", None)
        if selection is None:
            selection = DailyMomentumSelection(self.daily_momentum_ranking_path)
            self._daily_momentum_selection = selection
        return selection

    def _apply_daily_momentum_gate(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair")
        if not isinstance(pair, str) or not pair:
            raise ValueError("metadata must include a non-empty 'pair' value")

        if "enter_long" not in dataframe.columns:
            dataframe["enter_long"] = 0
            return dataframe

        eligible = self.daily_momentum_selection.eligible_mask(
            dataframe=dataframe,
            pair=pair,
            n=self.daily_momentum_top_n,
        )
        dataframe.loc[~eligible, "enter_long"] = 0
        return dataframe


def load_daily_momentum_rankings(ranking_path: Path) -> dict[str, list[str]]:
    payload = json.loads(ranking_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{ranking_path} must contain a JSON object")

    rankings: dict[str, list[str]] = {}
    for ranking_date, ranked_pairs in payload.items():
        if not isinstance(ranking_date, str):
            raise ValueError(f"{ranking_path} contains a non-string date key")
        date_key(ranking_date)
        if not isinstance(ranked_pairs, list) or not all(
            isinstance(pair, str) and pair for pair in ranked_pairs
        ):
            raise ValueError(f"{ranking_path} contains invalid ranked pairs for {ranking_date}")
        rankings[ranking_date] = ranked_pairs

    return rankings


def date_key(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        timestamp = value
    elif isinstance(value, datetime):
        timestamp = pd.Timestamp(value)
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, str):
        timestamp = pd.Timestamp(value)
    else:
        raise TypeError(f"Unsupported date value: {value!r}")

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.date().isoformat()
