from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from scripts.rank_pairs_by_momentum import (
    build_daily_rankings,
    build_parser,
    load_daily_closes,
    load_universe_pairs,
    pair_to_data_file,
    write_rankings,
)


def _write_daily_candles(data_dir: Path, pair: str, closes: dict[str, float]) -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(list(closes.keys()), utc=True),
            "open": list(closes.values()),
            "high": list(closes.values()),
            "low": list(closes.values()),
            "close": list(closes.values()),
            "volume": [1.0] * len(closes),
        }
    )
    output = pair_to_data_file(pair, data_dir, "1d")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_feather(output)


def test_parser_help_exits_without_reading_data(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0
    assert "Rank a fixed OKX pair universe" in capsys.readouterr().out


def test_load_universe_pairs_reads_top_level_pairs(tmp_path: Path):
    universe = tmp_path / "universe.json"
    universe.write_text(json.dumps({"pairs": ["BTC/USDT", "ETH/USDT"]}), encoding="utf-8")

    assert load_universe_pairs(universe) == ["BTC/USDT", "ETH/USDT"]


def test_build_daily_rankings_orders_pairs_by_trailing_one_day_return(tmp_path: Path):
    _write_daily_candles(
        tmp_path,
        "AAA/USDT",
        {"2024-01-01": 100.0, "2024-01-02": 110.0, "2024-01-03": 99.0},
    )
    _write_daily_candles(
        tmp_path,
        "BBB/USDT",
        {"2024-01-01": 100.0, "2024-01-02": 105.0, "2024-01-03": 126.0},
    )
    _write_daily_candles(
        tmp_path,
        "CCC/USDT",
        {"2024-01-01": 100.0, "2024-01-02": 90.0, "2024-01-03": 99.0},
    )
    closes_by_pair = {
        pair: load_daily_closes(pair, tmp_path) for pair in ("AAA/USDT", "BBB/USDT", "CCC/USDT")
    }

    rankings = build_daily_rankings(
        closes_by_pair=closes_by_pair,
        start=date(2024, 1, 3),
        end=date(2024, 1, 5),
        lookback_days=1,
    )

    assert rankings == {
        "2024-01-03": ["AAA/USDT", "BBB/USDT", "CCC/USDT"],
        "2024-01-04": ["BBB/USDT", "CCC/USDT", "AAA/USDT"],
    }


def test_build_daily_rankings_omits_pair_with_insufficient_history(tmp_path: Path):
    _write_daily_candles(
        tmp_path,
        "AAA/USDT",
        {"2024-01-01": 100.0, "2024-01-02": 110.0, "2024-01-03": 121.0},
    )
    _write_daily_candles(
        tmp_path,
        "NEW/USDT",
        {"2024-01-02": 50.0, "2024-01-03": 75.0},
    )
    closes_by_pair = {pair: load_daily_closes(pair, tmp_path) for pair in ("AAA/USDT", "NEW/USDT")}

    rankings = build_daily_rankings(
        closes_by_pair=closes_by_pair,
        start=date(2024, 1, 3),
        end=date(2024, 1, 5),
        lookback_days=1,
    )

    assert rankings["2024-01-03"] == ["AAA/USDT"]
    assert rankings["2024-01-04"] == ["NEW/USDT", "AAA/USDT"]


def test_write_rankings_uses_plain_date_to_pair_list_schema(tmp_path: Path):
    output = tmp_path / "rankings.json"
    rankings = {"2024-01-03": ["AAA/USDT", "BBB/USDT"]}

    write_rankings(rankings, output)

    assert json.loads(output.read_text(encoding="utf-8")) == rankings
