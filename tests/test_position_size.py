from __future__ import annotations

import math

import pytest

from risk.position_size import (
    PositionPlan,
    size_for_fixed_fraction,
    size_for_fixed_risk,
)


def test_fixed_risk_long_trade():
    plan = size_for_fixed_risk(
        entry_price=100.0,
        stop_price=95.0,
        dollar_risk=10.0,
        equity=1000.0,
    )
    assert isinstance(plan, PositionPlan)
    # $10 risk / $5 stop distance = 2 units.
    assert math.isclose(plan.units, 2.0)
    assert math.isclose(plan.notional, 200.0)
    assert math.isclose(plan.dollar_risk, 10.0)
    assert math.isclose(plan.risk_pct_of_equity, 0.01)
    assert math.isclose(plan.stop_distance_pct, 0.05)


def test_fixed_risk_short_or_stop_above_entry():
    # We don't care which side: stop distance is what matters.
    plan = size_for_fixed_risk(
        entry_price=100.0,
        stop_price=105.0,
        dollar_risk=20.0,
        equity=1000.0,
    )
    assert math.isclose(plan.units, 4.0)
    assert math.isclose(plan.dollar_risk, 20.0)


def test_fixed_fraction_matches_fixed_risk():
    plan_frac = size_for_fixed_fraction(
        entry_price=50.0,
        stop_price=48.0,
        equity=2000.0,
        risk_fraction=0.01,
    )
    plan_fixed = size_for_fixed_risk(
        entry_price=50.0,
        stop_price=48.0,
        dollar_risk=20.0,  # 1% of 2000
        equity=2000.0,
    )
    assert math.isclose(plan_frac.units, plan_fixed.units)
    assert math.isclose(plan_frac.dollar_risk, plan_fixed.dollar_risk)


def test_fixed_fraction_rejects_invalid_fraction():
    with pytest.raises(ValueError):
        size_for_fixed_fraction(
            entry_price=100, stop_price=95, equity=1000, risk_fraction=0
        )
    with pytest.raises(ValueError):
        size_for_fixed_fraction(
            entry_price=100, stop_price=95, equity=1000, risk_fraction=1
        )
    with pytest.raises(ValueError):
        size_for_fixed_fraction(
            entry_price=100, stop_price=95, equity=1000, risk_fraction=1.5
        )


def test_fixed_risk_rejects_zero_stop_distance():
    with pytest.raises(ValueError):
        size_for_fixed_risk(
            entry_price=100, stop_price=100, dollar_risk=10, equity=1000
        )


def test_fixed_risk_rejects_negative_inputs():
    with pytest.raises(ValueError):
        size_for_fixed_risk(entry_price=-1, stop_price=95, dollar_risk=10, equity=1000)
    with pytest.raises(ValueError):
        size_for_fixed_risk(entry_price=100, stop_price=-95, dollar_risk=10, equity=1000)
    with pytest.raises(ValueError):
        size_for_fixed_risk(entry_price=100, stop_price=95, dollar_risk=0, equity=1000)
    with pytest.raises(ValueError):
        size_for_fixed_risk(entry_price=100, stop_price=95, dollar_risk=10, equity=0)
