from __future__ import annotations

import importlib
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas import DataFrame

from user_data.selection.daily_momentum import DailyMomentumSelection

RANKED_STRATEGIES = [
    ("user_data.strategies.EMACrossoverDailyRanked", "EMACrossoverDailyRanked"),
    ("user_data.strategies.DonchianBreakoutDailyRanked", "DonchianBreakoutDailyRanked"),
    (
        "user_data.strategies.BollingerMeanReversionDailyRanked",
        "BollingerMeanReversionDailyRanked",
    ),
    ("user_data.strategies.RSITrendDailyRanked", "RSITrendDailyRanked"),
    ("user_data.strategies.MACDVolumeDailyRanked", "MACDVolumeDailyRanked"),
]


def _write_rankings(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "2025-01-01": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                "2025-01-02": ["ETH/USDT", "SOL/USDT", "BTC/USDT"],
                "2025-01-03": ["SOL/USDT", "ETH/USDT", "BTC/USDT"],
            }
        ),
        encoding="utf-8",
    )
    return path


def _ohlcv_frame(rows: int = 320) -> DataFrame:
    dates = pd.date_range("2025-01-01", periods=rows, freq="5min", tz="UTC")
    trend = pd.Series(range(rows), dtype="float64")
    close = 100 + trend * 0.05 + (trend % 18) * 0.02
    return DataFrame(
        {
            "date": dates,
            "open": close - 0.1,
            "high": close + 0.4,
            "low": close - 0.4,
            "close": close,
            "volume": 100 + (trend % 25),
        }
    )


def test_daily_momentum_selection_returns_false_for_missing_dates(tmp_path: Path):
    selection = DailyMomentumSelection(_write_rankings(tmp_path / "rankings.json"))

    assert not selection.is_pair_in_today_top_n("BTC/USDT", "2025-01-04 12:00:00+00:00", 3)


def test_daily_momentum_selection_returns_false_for_out_of_universe_pairs(tmp_path: Path):
    selection = DailyMomentumSelection(_write_rankings(tmp_path / "rankings.json"))

    assert not selection.is_pair_in_today_top_n("DOGE/USDT", "2025-01-01 12:00:00+00:00", 3)


def test_daily_momentum_selection_uses_entry_candle_utc_date_boundary(tmp_path: Path):
    selection = DailyMomentumSelection(_write_rankings(tmp_path / "rankings.json"))

    assert selection.is_pair_in_today_top_n("BTC/USDT", "2025-01-01 23:59:59+00:00", 1)
    assert selection.is_pair_in_today_top_n("ETH/USDT", "2025-01-02 00:00:00+00:00", 1)
    assert selection.is_pair_in_today_top_n("BTC/USDT", "2025-01-02 06:30:00+07:00", 1)
    assert selection.is_pair_in_today_top_n("SOL/USDT", "2025-01-03 00:00:00+00:00", 1)
    assert not selection.is_pair_in_today_top_n("ETH/USDT", "2025-01-03 00:00:00+00:00", 1)


@pytest.mark.parametrize(("module_name", "class_name"), RANKED_STRATEGIES)
def test_daily_ranked_strategy_classes_import(module_name: str, class_name: str):
    module = importlib.import_module(module_name)

    assert getattr(module, class_name).__name__ == class_name


@pytest.mark.parametrize(("module_name", "class_name"), RANKED_STRATEGIES)
def test_daily_ranked_strategies_smoke_populate_entry_and_exit(
    tmp_path: Path,
    module_name: str,
    class_name: str,
):
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    strategy = strategy_class({})
    strategy.daily_momentum_ranking_path = _write_rankings(tmp_path / "rankings.json")
    dataframe = _ohlcv_frame()

    populated = strategy.populate_indicators(dataframe.copy(), {"pair": "BTC/USDT"})
    entered = strategy.populate_entry_trend(populated.copy(), {"pair": "BTC/USDT"})
    exited = strategy.populate_exit_trend(entered.copy(), {"pair": "BTC/USDT"})

    assert "enter_long" in exited.columns
    assert "exit_long" in exited.columns
    assert len(exited) == len(dataframe)
