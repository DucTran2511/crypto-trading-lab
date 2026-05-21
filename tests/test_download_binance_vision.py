from __future__ import annotations

import pandas as pd
import pytest

from scripts.download_binance_vision import (
    COLUMNS,
    Month,
    iter_months,
    pair_to_filename,
    pair_to_symbol,
    parse_month,
    to_freqtrade_frame,
)


def test_parse_month_valid():
    assert parse_month("2025-01") == Month(2025, 1)
    assert parse_month("2024-12") == Month(2024, 12)


def test_parse_month_invalid():
    with pytest.raises(ValueError):
        parse_month("2025")
    with pytest.raises(ValueError):
        parse_month("2025-01-01")


def test_iter_months_inclusive():
    months = list(iter_months(Month(2024, 11), Month(2025, 2)))
    assert months == [
        Month(2024, 11), Month(2024, 12), Month(2025, 1), Month(2025, 2)
    ]


def test_iter_months_single_month():
    assert list(iter_months(Month(2025, 3), Month(2025, 3))) == [Month(2025, 3)]


def test_pair_helpers():
    assert pair_to_symbol("BTC/USDT") == "BTCUSDT"
    assert pair_to_filename("btc/usdt") == "BTC_USDT"


def test_to_freqtrade_frame_handles_ms_timestamps():
    raw = pd.DataFrame(
        [[1735689600000, 100, 110, 90, 105, 1.5, 0, 0, 0, 0, 0, 0]],
        columns=COLUMNS,
    )
    out = to_freqtrade_frame(raw)
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert out["date"].iloc[0] == pd.Timestamp("2025-01-01 00:00:00")


def test_to_freqtrade_frame_handles_us_timestamps():
    # Some Binance archives use microseconds for newer pairs.
    raw = pd.DataFrame(
        [[1735689600000000, 100, 110, 90, 105, 1.5, 0, 0, 0, 0, 0, 0]],
        columns=COLUMNS,
    )
    out = to_freqtrade_frame(raw)
    assert out["date"].iloc[0] == pd.Timestamp("2025-01-01 00:00:00")


def test_to_freqtrade_frame_empty_input():
    out = to_freqtrade_frame(pd.DataFrame(columns=COLUMNS))
    assert out.empty
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume"]
