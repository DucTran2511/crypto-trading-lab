"""Position-sizing helpers.

The single biggest difference between traders who survive and traders who blow
up is **not** strategy selection — it is position sizing. The math here is
trivial; what matters is using it on *every* trade.

Two flavours are provided:

1. ``size_for_fixed_risk`` — risk a fixed dollar amount per trade given a
   stoploss distance. This is the default for almost every retail setup.
2. ``size_for_fixed_fraction`` — risk a fixed fraction of *account equity* per
   trade. Equivalent to (1) at the start, but the position scales up/down as
   the account grows/shrinks.

A CLI is exposed so you can sanity-check sizes from the command line before
placing a trade.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionPlan:
    units: float
    notional: float
    dollar_risk: float
    risk_pct_of_equity: float
    stop_distance_pct: float

    def pretty(self) -> str:
        return (
            f"Units:                  {self.units:.6f}\n"
            f"Notional value:         ${self.notional:,.2f}\n"
            f"Dollar risk at stop:    ${self.dollar_risk:,.2f}\n"
            f"Risk as % of equity:    {self.risk_pct_of_equity * 100:.3f}%\n"
            f"Stop distance from entry: {self.stop_distance_pct * 100:.3f}%"
        )


def size_for_fixed_risk(
    *,
    entry_price: float,
    stop_price: float,
    dollar_risk: float,
    equity: float,
) -> PositionPlan:
    """Return a position plan given a fixed dollar amount to risk."""
    if entry_price <= 0 or stop_price <= 0:
        raise ValueError("Prices must be positive")
    if equity <= 0:
        raise ValueError("Equity must be positive")
    if dollar_risk <= 0:
        raise ValueError("dollar_risk must be positive")

    stop_distance = abs(entry_price - stop_price)
    if stop_distance == 0:
        raise ValueError("Stop must differ from entry")

    units = dollar_risk / stop_distance
    notional = units * entry_price
    return PositionPlan(
        units=units,
        notional=notional,
        dollar_risk=dollar_risk,
        risk_pct_of_equity=dollar_risk / equity,
        stop_distance_pct=stop_distance / entry_price,
    )


def size_for_fixed_fraction(
    *,
    entry_price: float,
    stop_price: float,
    equity: float,
    risk_fraction: float = 0.01,
) -> PositionPlan:
    """Risk a fixed fraction of equity (e.g. 1%) per trade."""
    if not 0 < risk_fraction < 1:
        raise ValueError("risk_fraction must be in (0, 1) — e.g. 0.01 for 1%")
    return size_for_fixed_risk(
        entry_price=entry_price,
        stop_price=stop_price,
        dollar_risk=equity * risk_fraction,
        equity=equity,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equity", type=float, required=True, help="Account equity in USD/USDT")
    parser.add_argument("--entry", type=float, required=True, help="Planned entry price")
    parser.add_argument("--stop", type=float, required=True, help="Stop-loss price")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--risk-pct",
        type=float,
        help="Risk this fraction of equity (e.g. 0.01 for 1%%)",
    )
    mode.add_argument(
        "--risk-usd",
        type=float,
        help="Risk this many USD on the trade",
    )

    args = parser.parse_args(argv)

    if args.risk_pct is not None:
        plan = size_for_fixed_fraction(
            entry_price=args.entry,
            stop_price=args.stop,
            equity=args.equity,
            risk_fraction=args.risk_pct,
        )
    else:
        plan = size_for_fixed_risk(
            entry_price=args.entry,
            stop_price=args.stop,
            dollar_risk=args.risk_usd,
            equity=args.equity,
        )

    print(plan.pretty())
    return 0


if __name__ == "__main__":
    sys.exit(main())
