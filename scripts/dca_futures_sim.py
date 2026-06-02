"""Simulate DCA (Dollar-Cost Averaging) on a leveraged crypto futures long.

Given a total wallet, order size, first entry price, and leverage, the
simulator adds a new long at each DCA level (price drops by a fixed %) and
prints a table showing how average entry, liquidation price, margin usage,
and required bounce evolve at every step.

The simulation stops when:
  1. The next DCA price is at or below the liquidation price (liquidated), or
  2. There is not enough remaining margin to open the next order.

Cross-margin mode is assumed: the entire wallet balance backs all positions.

Example
-------
::

    python scripts/dca_futures_sim.py \
        --equity 1000 --order-size 200 --entry 100000 \
        --leverage 5 --dca-drop-pct 5

"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

DEFAULT_MAINT_RATE = 0.004  # 0.4 % — typical for small positions on Binance / OKX
DEFAULT_DCA_DROP_PCT = 5.0
DEFAULT_TAKER_FEE = 0.0005  # 0.05 %


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DCALevel:
    """Snapshot of the position after a single DCA order executes."""

    level: int
    price: float
    units_added: float
    cum_units: float
    avg_entry: float
    margin_used: float
    margin_remaining: float
    margin_usage_pct: float
    liq_price: float
    breakeven_price: float
    bounce_to_breakeven_pct: float
    cum_fees: float


@dataclass
class SimResult:
    """Full result of a DCA simulation run."""

    levels: list[DCALevel] = field(default_factory=list)
    liquidated: bool = False
    margin_exhausted: bool = False
    reason: str = ""


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def compute_liq_price(
    wallet: float,
    cum_units: float,
    avg_entry: float,
    maint_rate: float,
) -> float:
    """Cross-margin liquidation price for a long position.

    Liquidation triggers when equity equals maintenance margin:
        wallet + cum_units * (liq - avg_entry) = cum_units * liq * maint_rate
    Solving for ``liq``:
        liq = (cum_units * avg_entry - wallet) / (cum_units * (1 - maint_rate))
    """
    if cum_units <= 0:
        return 0.0
    return (cum_units * avg_entry - wallet) / (cum_units * (1.0 - maint_rate))


def simulate_dca(
    *,
    equity: float,
    order_size: float,
    entry_price: float,
    leverage: float,
    dca_drop_pct: float = DEFAULT_DCA_DROP_PCT,
    maint_rate: float = DEFAULT_MAINT_RATE,
    taker_fee: float = DEFAULT_TAKER_FEE,
    max_levels: int = 100,
) -> SimResult:
    """Run a DCA simulation and return the result.

    Parameters
    ----------
    equity : float
        Total wallet balance in quote currency (USDT).
    order_size : float
        Notional value of each DCA order in quote currency.
    entry_price : float
        Price of the first long entry.
    leverage : float
        Leverage multiplier (e.g. 5 for 5x).
    dca_drop_pct : float
        Percentage price drop between consecutive DCA orders.
    maint_rate : float
        Exchange maintenance-margin rate (fraction, e.g. 0.004 = 0.4 %).
    taker_fee : float
        Taker fee per order (fraction, e.g. 0.0005 = 0.05 %).
    max_levels : int
        Safety cap on the number of DCA levels.
    """
    if equity <= 0:
        raise ValueError("equity must be positive")
    if order_size <= 0:
        raise ValueError("order_size must be positive")
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")
    if leverage < 1:
        raise ValueError("leverage must be >= 1")
    if not 0 < dca_drop_pct < 100:
        raise ValueError("dca_drop_pct must be in (0, 100)")

    result = SimResult()

    cum_units = 0.0
    cum_notional = 0.0  # sum of (units_i * price_i)
    cum_margin = 0.0
    cum_fees = 0.0
    wallet = equity

    for i in range(max_levels):
        drop_factor = (1.0 - dca_drop_pct / 100.0) ** i
        price = entry_price * drop_factor

        # Check: would we be liquidated before this DCA fires?
        if i > 0:
            liq_prev = compute_liq_price(wallet, cum_units, cum_notional / cum_units, maint_rate)
            if price <= liq_prev:
                result.liquidated = True
                result.reason = (
                    f"Liquidated before DCA #{i + 1}: price ${price:,.2f} "
                    f"<= liq ${liq_prev:,.2f}"
                )
                break

        # Margin required for this order
        margin_needed = order_size / leverage
        fee = order_size * taker_fee
        total_cost = margin_needed + fee

        if total_cost > (wallet - cum_margin):
            result.margin_exhausted = True
            remaining = wallet - cum_margin
            result.reason = (
                f"Insufficient margin for DCA #{i + 1}: need ${total_cost:,.2f}, "
                f"have ${remaining:,.2f}"
            )
            break

        # Execute the DCA order
        units = order_size / price
        cum_units += units
        cum_notional += units * price
        cum_margin += margin_needed
        cum_fees += fee
        wallet -= fee  # fees are deducted from wallet

        avg_entry = cum_notional / cum_units
        margin_remaining = wallet - cum_margin
        liq = compute_liq_price(wallet, cum_units, avg_entry, maint_rate)
        breakeven = avg_entry + cum_fees / cum_units  # need to recover fees too
        bounce_pct = ((breakeven / price) - 1.0) * 100.0 if price > 0 else 0.0

        level = DCALevel(
            level=i + 1,
            price=price,
            units_added=units,
            cum_units=cum_units,
            avg_entry=avg_entry,
            margin_used=cum_margin,
            margin_remaining=margin_remaining,
            margin_usage_pct=(cum_margin / wallet) * 100.0,
            liq_price=max(liq, 0.0),
            breakeven_price=breakeven,
            bounce_to_breakeven_pct=bounce_pct,
            cum_fees=cum_fees,
        )
        result.levels.append(level)

    if not result.liquidated and not result.margin_exhausted and result.levels:
        result.reason = f"Completed {len(result.levels)} DCA levels without liquidation."

    return result


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def format_table(result: SimResult) -> str:
    """Return a human-readable table of the simulation."""
    header = (
        f"{'#':>3}  {'DCA Price':>12}  {'Units +':>10}  {'Cum Units':>10}  "
        f"{'Avg Entry':>12}  {'Liq Price':>12}  {'Margin Used':>12}  "
        f"{'Margin Left':>12}  {'Usage %':>8}  {'Breakeven':>12}  {'Bounce %':>9}"
    )
    sep = "-" * len(header)
    lines = [header, sep]

    for lvl in result.levels:
        lines.append(
            f"{lvl.level:>3}  "
            f"${lvl.price:>11,.2f}  "
            f"{lvl.units_added:>10.6f}  "
            f"{lvl.cum_units:>10.6f}  "
            f"${lvl.avg_entry:>11,.2f}  "
            f"${lvl.liq_price:>11,.2f}  "
            f"${lvl.margin_used:>11,.2f}  "
            f"${lvl.margin_remaining:>11,.2f}  "
            f"{lvl.margin_usage_pct:>7.1f}%  "
            f"${lvl.breakeven_price:>11,.2f}  "
            f"{lvl.bounce_to_breakeven_pct:>8.2f}%"
        )

    lines.append(sep)
    lines.append(result.reason)
    return "\n".join(lines)


def format_summary(result: SimResult, equity: float, leverage: float) -> str:
    """Return a short summary paragraph."""
    if not result.levels:
        return "No DCA levels executed."

    last = result.levels[-1]
    parts = [
        f"Equity: ${equity:,.2f}  |  Leverage: {leverage:.0f}x  |  "
        f"DCA levels executed: {len(result.levels)}",
        f"Final avg entry:   ${last.avg_entry:,.2f}",
        f"Final liq price:   ${last.liq_price:,.2f}",
        f"Margin used:       ${last.margin_used:,.2f} / ${equity:,.2f} "
        f"({last.margin_usage_pct:.1f}%)",
        f"Total fees paid:   ${last.cum_fees:,.2f}",
        f"Bounce needed:     {last.bounce_to_breakeven_pct:.2f}% "
        f"from last DCA price to breakeven",
    ]
    if result.liquidated:
        parts.append("*** LIQUIDATION: price reached liq level before next DCA ***")
    if result.margin_exhausted:
        parts.append("*** MARGIN EXHAUSTED: cannot fund next DCA order ***")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate DCA on a leveraged crypto futures long. "
            "Shows average entry, liquidation price, margin usage, and "
            "required bounce at each DCA level."
        ),
    )
    parser.add_argument(
        "--equity",
        type=float,
        required=True,
        help="Total wallet balance in USDT.",
    )
    parser.add_argument(
        "--order-size",
        type=float,
        required=True,
        help="Notional USDT value per DCA order.",
    )
    parser.add_argument(
        "--entry",
        type=float,
        required=True,
        help="First long entry price.",
    )
    parser.add_argument(
        "--leverage",
        type=float,
        required=True,
        help="Leverage multiplier (e.g. 5 for 5x).",
    )
    parser.add_argument(
        "--dca-drop-pct",
        type=float,
        default=DEFAULT_DCA_DROP_PCT,
        help="Price drop %% between DCA levels (default: %(default)s).",
    )
    parser.add_argument(
        "--maint-rate",
        type=float,
        default=DEFAULT_MAINT_RATE,
        help="Maintenance margin rate as a decimal (default: %(default)s = 0.4%%).",
    )
    parser.add_argument(
        "--taker-fee",
        type=float,
        default=DEFAULT_TAKER_FEE,
        help="Taker fee per order as a decimal (default: %(default)s = 0.05%%).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = simulate_dca(
        equity=args.equity,
        order_size=args.order_size,
        entry_price=args.entry,
        leverage=args.leverage,
        dca_drop_pct=args.dca_drop_pct,
        maint_rate=args.maint_rate,
        taker_fee=args.taker_fee,
    )

    print(format_summary(result, equity=args.equity, leverage=args.leverage))
    print()
    print(format_table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
