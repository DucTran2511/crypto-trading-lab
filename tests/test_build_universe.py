from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_universe import (
    build_parser,
    build_universe,
    exclusion_reason,
    pair_to_data_file,
    ticker_to_pair,
    write_universe,
)


def _ticker(inst_id: str) -> dict[str, str]:
    return {"instId": inst_id}


def _write_candles(
    data_dir: Path,
    pair: str,
    *,
    start: str = "2023-12-01",
    end: str = "2024-07-02",
    close: float = 10.0,
    volume: float = 1.0,
) -> None:
    dates = pd.date_range(start=start, end=end, freq="1D", inclusive="left")
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": volume,
        }
    )
    output = pair_to_data_file(pair, data_dir, "5m")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_feather(output)


def test_parser_help_exits_without_fetching_tickers(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0
    assert "Build a top-N OKX USDT spot universe" in capsys.readouterr().out


def test_ticker_to_pair_only_keeps_simple_usdt_spot_pairs():
    assert ticker_to_pair(_ticker("BTC-USDT")) == ("BTC/USDT", "BTC-USDT", "BTC")
    assert ticker_to_pair(_ticker("ETH-USDC")) is None
    assert ticker_to_pair(_ticker("BTC-USDT-SWAP")) is None


def test_exclusion_reason_covers_stable_wrapped_leveraged_and_synthetic_assets():
    assert exclusion_reason("USDC") == "stablecoin"
    assert exclusion_reason("WBTC") == "wrapped"
    assert exclusion_reason("ETH3L") == "leveraged"
    assert exclusion_reason("BTCDOWN") == "leveraged"
    assert exclusion_reason("BTCST") == "synthetic"
    assert exclusion_reason("BTC") is None


def test_build_universe_ranks_by_historical_30d_quote_volume(tmp_path: Path):
    tickers = [_ticker("AAA-USDT"), _ticker("BBB-USDT"), _ticker("CCC-USDT")]
    _write_candles(tmp_path, "AAA/USDT", close=2.0, volume=10.0)
    _write_candles(tmp_path, "BBB/USDT", close=10.0, volume=10.0)
    _write_candles(tmp_path, "CCC/USDT", close=5.0, volume=10.0)

    universe = build_universe(
        tickers=tickers,
        data_dir=tmp_path,
        timeframe="5m",
        snapshot_date=date(2024, 7, 1),
        top=2,
    )

    assert [candidate.pair for candidate in universe] == ["BBB/USDT", "CCC/USDT"]
    assert universe[0].quote_volume_30d == pytest.approx(3000.0)
    assert universe[1].quote_volume_30d == pytest.approx(1500.0)


def test_build_universe_applies_all_exclusion_rules(tmp_path: Path):
    tickers = [
        _ticker("BTC-USDT"),
        _ticker("USDC-USDT"),
        _ticker("WBTC-USDT"),
        _ticker("ETH3L-USDT"),
        _ticker("BTCST-USDT"),
        _ticker("NEW-USDT"),
        _ticker("MISSING-USDT"),
    ]
    for pair in ("BTC/USDT", "USDC/USDT", "WBTC/USDT", "ETH3L/USDT", "BTCST/USDT"):
        _write_candles(tmp_path, pair, close=10.0, volume=10.0)
    _write_candles(tmp_path, "NEW/USDT", start="2024-03-01", close=1000.0, volume=1000.0)

    universe = build_universe(
        tickers=tickers,
        data_dir=tmp_path,
        timeframe="5m",
        snapshot_date=date(2024, 7, 1),
        top=10,
    )

    assert [candidate.pair for candidate in universe] == ["BTC/USDT"]


def test_write_universe_creates_expected_json(tmp_path: Path):
    tickers = [_ticker("BTC-USDT")]
    _write_candles(tmp_path / "data", "BTC/USDT", close=10.0, volume=10.0)
    candidates = build_universe(
        tickers=tickers,
        data_dir=tmp_path / "data",
        timeframe="5m",
        snapshot_date=date(2024, 7, 1),
        top=1,
    )
    output = tmp_path / "top1_okx_2024-07-01.json"

    write_universe(
        candidates=candidates,
        output_path=output,
        snapshot_date=date(2024, 7, 1),
        top=1,
        timeframe="5m",
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["exchange"] == "okx"
    assert payload["snapshot_date"] == "2024-07-01"
    assert payload["pairs"] == ["BTC/USDT"]
    assert payload["candidates"][0]["quote_volume_30d"] == pytest.approx(3000.0)
