"""Simple market regime classifier.

The classifier combines two intentionally conservative signals:
- EMA slope sign determines bullish vs bearish trend direction.
- ADX threshold separates trending bars from range-bound bars.

It returns one label per input bar and is designed to be imported from a
strategy's ``populate_indicators`` method or used directly in notebooks.
"""
from __future__ import annotations

from typing import Literal

import pandas as pd
from pandas import DataFrame, Series

RegimeLabel = Literal["bull", "bear", "range", "unknown"]


def classify_regime(
    dataframe: DataFrame,
    *,
    ema_period: int = 100,
    ema_slope_lookback: int = 5,
    adx_period: int = 14,
    adx_threshold: float = 20.0,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> Series:
    """Return a regime label for each bar in ``dataframe``.

    Labels:
    - ``bull``: ADX is above threshold and EMA slope is positive.
    - ``bear``: ADX is above threshold and EMA slope is negative.
    - ``range``: ADX is below threshold or EMA slope is flat.
    - ``unknown``: insufficient lookback data to classify the bar.
    """
    _validate_inputs(
        dataframe=dataframe,
        columns=(high_col, low_col, close_col),
        ema_period=ema_period,
        ema_slope_lookback=ema_slope_lookback,
        adx_period=adx_period,
        adx_threshold=adx_threshold,
    )

    close = dataframe[close_col]
    ema = close.ewm(span=ema_period, adjust=False, min_periods=ema_period).mean()
    ema_slope = ema - ema.shift(ema_slope_lookback)
    adx = _adx(
        high=dataframe[high_col],
        low=dataframe[low_col],
        close=close,
        period=adx_period,
    )

    regime = pd.Series("unknown", index=dataframe.index, dtype="object")
    enough_data = ema_slope.notna() & adx.notna()
    trending = enough_data & (adx >= adx_threshold)

    regime.loc[enough_data & ~trending] = "range"
    regime.loc[trending & (ema_slope > 0)] = "bull"
    regime.loc[trending & (ema_slope < 0)] = "bear"
    regime.loc[trending & (ema_slope == 0)] = "range"
    return regime


def _adx(*, high: Series, low: Series, close: Series, period: int) -> Series:
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(0.0, index=high.index)
    minus_dm = pd.Series(0.0, index=high.index)
    plus_dm.loc[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm.loc[(down_move > up_move) & (down_move > 0)] = down_move

    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    alpha = 1 / period
    average_true_range = true_range.ewm(
        alpha=alpha,
        adjust=False,
        min_periods=period,
    ).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    plus_di = plus_di / average_true_range
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    minus_di = minus_di / average_true_range

    di_sum = plus_di + minus_di
    dx = 100 * (plus_di - minus_di).abs() / di_sum.where(di_sum != 0)
    return dx.ewm(alpha=alpha, adjust=False, min_periods=period).mean()


def _validate_inputs(
    *,
    dataframe: DataFrame,
    columns: tuple[str, str, str],
    ema_period: int,
    ema_slope_lookback: int,
    adx_period: int,
    adx_threshold: float,
) -> None:
    missing = sorted(set(columns) - set(dataframe.columns))
    if missing:
        raise ValueError(f"dataframe is missing required OHLC columns: {', '.join(missing)}")
    if ema_period < 2:
        raise ValueError("ema_period must be at least 2")
    if ema_slope_lookback < 1:
        raise ValueError("ema_slope_lookback must be at least 1")
    if adx_period < 2:
        raise ValueError("adx_period must be at least 2")
    if adx_threshold < 0:
        raise ValueError("adx_threshold must be non-negative")
