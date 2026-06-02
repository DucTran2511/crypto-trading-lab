from __future__ import annotations

import math

import pytest

from scripts.dca_futures_sim import (
    SimResult,
    compute_liq_price,
    format_summary,
    format_table,
    simulate_dca,
)

# ---------------------------------------------------------------------------
# compute_liq_price
# ---------------------------------------------------------------------------

class TestComputeLiqPrice:
    def test_basic_long(self):
        # wallet=200, 1 unit at entry=100, maint_rate=0
        # liq = (1*100 - 200) / (1*1) = -100 => no liquidation (liq < 0)
        liq = compute_liq_price(wallet=200.0, cum_units=1.0, avg_entry=100.0, maint_rate=0.0)
        assert math.isclose(liq, -100.0)

    def test_5x_leverage_simple(self):
        # 5x on $1000 notional at $100 => 10 units, margin = $200
        # wallet = 200 (just the margin, no extra)
        # liq = 100 - 200 / (10 * (1 - 0)) = 100 - 20 = 80
        liq = compute_liq_price(wallet=200.0, cum_units=10.0, avg_entry=100.0, maint_rate=0.0)
        assert math.isclose(liq, 80.0)

    def test_zero_units_returns_zero(self):
        assert compute_liq_price(wallet=1000.0, cum_units=0.0, avg_entry=50.0, maint_rate=0.0) == 0.0

    def test_maint_rate_raises_liq(self):
        # Higher maint rate => liquidation happens sooner (higher price for long)
        liq_low = compute_liq_price(wallet=200.0, cum_units=10.0, avg_entry=100.0, maint_rate=0.0)
        liq_high = compute_liq_price(wallet=200.0, cum_units=10.0, avg_entry=100.0, maint_rate=0.01)
        assert liq_high > liq_low


# ---------------------------------------------------------------------------
# simulate_dca
# ---------------------------------------------------------------------------

class TestSimulateDca:
    def test_single_level_no_dca(self):
        """order_size == equity * leverage => only one order fits."""
        result = simulate_dca(
            equity=100.0,
            order_size=500.0,  # 5x * 100 = 500, uses all margin
            entry_price=1000.0,
            leverage=5.0,
            dca_drop_pct=10.0,
            maint_rate=0.0,
            taker_fee=0.0,
        )
        assert len(result.levels) == 1
        assert result.margin_exhausted
        lvl = result.levels[0]
        assert math.isclose(lvl.price, 1000.0)
        assert math.isclose(lvl.margin_used, 100.0)

    def test_two_levels(self):
        result = simulate_dca(
            equity=1000.0,
            order_size=200.0,
            entry_price=100.0,
            leverage=5.0,
            dca_drop_pct=10.0,
            maint_rate=0.0,
            taker_fee=0.0,
        )
        assert len(result.levels) >= 2
        first = result.levels[0]
        second = result.levels[1]
        assert math.isclose(first.price, 100.0)
        assert math.isclose(second.price, 90.0)
        assert second.avg_entry < first.avg_entry
        assert second.cum_units > first.cum_units

    def test_avg_entry_decreases(self):
        result = simulate_dca(
            equity=5000.0,
            order_size=200.0,
            entry_price=50000.0,
            leverage=5.0,
            dca_drop_pct=5.0,
            maint_rate=0.004,
            taker_fee=0.0,
        )
        for i in range(1, len(result.levels)):
            assert result.levels[i].avg_entry < result.levels[i - 1].avg_entry

    def test_liq_price_always_below_dca_price_until_end(self):
        result = simulate_dca(
            equity=2000.0,
            order_size=200.0,
            entry_price=100.0,
            leverage=5.0,
            dca_drop_pct=5.0,
            maint_rate=0.004,
            taker_fee=0.0005,
        )
        for lvl in result.levels:
            assert lvl.liq_price < lvl.price, (
                f"DCA #{lvl.level}: liq {lvl.liq_price:.4f} >= price {lvl.price:.4f}"
            )

    def test_terminates_on_liquidation(self):
        # Small equity + big orders => fast liquidation
        result = simulate_dca(
            equity=100.0,
            order_size=90.0,
            entry_price=100.0,
            leverage=10.0,
            dca_drop_pct=20.0,
            maint_rate=0.0,
            taker_fee=0.0,
        )
        assert result.liquidated or result.margin_exhausted

    def test_fees_deducted(self):
        result = simulate_dca(
            equity=1000.0,
            order_size=200.0,
            entry_price=100.0,
            leverage=5.0,
            dca_drop_pct=10.0,
            maint_rate=0.0,
            taker_fee=0.01,  # 1 % fee to make it visible
        )
        first = result.levels[0]
        assert math.isclose(first.cum_fees, 200.0 * 0.01)
        assert first.breakeven_price > first.avg_entry  # must recover fees

    def test_margin_usage_increases(self):
        result = simulate_dca(
            equity=2000.0,
            order_size=200.0,
            entry_price=100.0,
            leverage=5.0,
            dca_drop_pct=5.0,
            maint_rate=0.004,
            taker_fee=0.0,
        )
        for i in range(1, len(result.levels)):
            assert result.levels[i].margin_usage_pct > result.levels[i - 1].margin_usage_pct


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidation:
    def test_zero_equity(self):
        with pytest.raises(ValueError, match="equity"):
            simulate_dca(
                equity=0, order_size=100, entry_price=100, leverage=5,
            )

    def test_negative_order_size(self):
        with pytest.raises(ValueError, match="order_size"):
            simulate_dca(
                equity=1000, order_size=-1, entry_price=100, leverage=5,
            )

    def test_zero_entry_price(self):
        with pytest.raises(ValueError, match="entry_price"):
            simulate_dca(
                equity=1000, order_size=100, entry_price=0, leverage=5,
            )

    def test_leverage_below_one(self):
        with pytest.raises(ValueError, match="leverage"):
            simulate_dca(
                equity=1000, order_size=100, entry_price=100, leverage=0.5,
            )

    def test_dca_drop_pct_out_of_range(self):
        with pytest.raises(ValueError, match="dca_drop_pct"):
            simulate_dca(
                equity=1000, order_size=100, entry_price=100, leverage=5,
                dca_drop_pct=0,
            )
        with pytest.raises(ValueError, match="dca_drop_pct"):
            simulate_dca(
                equity=1000, order_size=100, entry_price=100, leverage=5,
                dca_drop_pct=100,
            )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

class TestFormatting:
    def _sample_result(self) -> SimResult:
        return simulate_dca(
            equity=1000.0,
            order_size=200.0,
            entry_price=100.0,
            leverage=5.0,
            dca_drop_pct=10.0,
            maint_rate=0.004,
            taker_fee=0.0005,
        )

    def test_format_table_contains_header(self):
        table = format_table(self._sample_result())
        assert "DCA Price" in table
        assert "Avg Entry" in table
        assert "Liq Price" in table

    def test_format_summary_contains_key_info(self):
        result = self._sample_result()
        summary = format_summary(result, equity=1000.0, leverage=5.0)
        assert "Equity" in summary
        assert "Leverage" in summary
        assert "5x" in summary

    def test_empty_result(self):
        summary = format_summary(SimResult(), equity=1000.0, leverage=5.0)
        assert "No DCA" in summary
