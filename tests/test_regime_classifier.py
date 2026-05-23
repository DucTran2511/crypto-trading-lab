from __future__ import annotations

import pandas as pd
import pytest

from user_data.regime.classifier import classify_regime


def _ohlcv_from_closes(closes: list[float]) -> pd.DataFrame:
    close = pd.Series(closes, dtype="float64")
    return pd.DataFrame(
        {
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 100.0,
        }
    )


def test_classify_regime_labels_uptrend_as_bull():
    dataframe = _ohlcv_from_closes([float(i) for i in range(1, 81)])

    regime = classify_regime(
        dataframe,
        ema_period=5,
        ema_slope_lookback=2,
        adx_period=5,
        adx_threshold=20,
    )

    assert regime.index.equals(dataframe.index)
    assert regime.iloc[-1] == "bull"


def test_classify_regime_labels_downtrend_as_bear():
    dataframe = _ohlcv_from_closes([float(i) for i in range(80, 0, -1)])

    regime = classify_regime(
        dataframe,
        ema_period=5,
        ema_slope_lookback=2,
        adx_period=5,
        adx_threshold=20,
    )

    assert regime.iloc[-1] == "bear"


def test_classify_regime_labels_low_adx_as_range():
    dataframe = _ohlcv_from_closes([100.0 + (0.1 if i % 2 else -0.1) for i in range(80)])

    regime = classify_regime(
        dataframe,
        ema_period=5,
        ema_slope_lookback=2,
        adx_period=5,
        adx_threshold=200,
    )

    assert regime.iloc[-1] == "range"


def test_classify_regime_keeps_warmup_bars_unknown():
    dataframe = _ohlcv_from_closes([float(i) for i in range(1, 30)])

    regime = classify_regime(
        dataframe,
        ema_period=10,
        ema_slope_lookback=3,
        adx_period=10,
    )

    assert regime.iloc[0] == "unknown"


def test_classify_regime_rejects_missing_ohlc_columns():
    with pytest.raises(ValueError, match="missing required OHLC columns"):
        classify_regime(pd.DataFrame({"close": [1.0, 2.0, 3.0]}))
