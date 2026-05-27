"""Rank a fixed pair universe by trailing daily momentum."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

DEFAULT_UNIVERSE = Path("user_data/universes/top20_okx_2024-07-01.json")
DEFAULT_DATA_DIR = Path("user_data/data/okx")
DEFAULT_OUTPUT_DIR = Path("user_data/universes")
DEFAULT_TIMEFRAME = "1d"
DEFAULT_LOOKBACK_DAYS = 1
DEFAULT_TOP_N = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank a fixed OKX pair universe by trailing close-to-close momentum.",
    )
    parser.add_argument(
        "--start",
        type=parse_date,
        required=True,
        help="First ranking date, inclusive, as YYYY-MM-DD or YYYYMMDD.",
    )
    parser.add_argument(
        "--end",
        type=parse_date,
        required=True,
        help="End date, exclusive, as YYYY-MM-DD or YYYYMMDD.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=DEFAULT_LOOKBACK_DAYS,
        help="Trailing daily close-to-close lookback. Default: 1.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=(
            "Downstream top-N eligibility count. Rankings are still stored as the full "
            "available universe ordering."
        ),
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=DEFAULT_UNIVERSE,
        help="Universe JSON containing a top-level 'pairs' list.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Freqtrade OKX data directory containing daily feather candle files.",
    )
    parser.add_argument(
        "--timeframe",
        default=DEFAULT_TIMEFRAME,
        help="Local candle timeframe to read. Default: 1d.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output JSON path. Defaults to "
            "user_data/universes/daily_momentum_rank_YYYYMMDD-YYYYMMDD.json."
        ),
    )
    return parser


def parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Expected date as YYYY-MM-DD or YYYYMMDD, got {value!r}")


def pair_to_data_file(pair: str, data_dir: Path, timeframe: str) -> Path:
    return data_dir / f"{pair.replace('/', '_')}-{timeframe}.feather"


def load_universe_pairs(universe_path: Path) -> list[str]:
    payload = json.loads(universe_path.read_text(encoding="utf-8"))
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(f"{universe_path} must contain a non-empty 'pairs' list")
    if not all(isinstance(pair, str) and pair for pair in pairs):
        raise ValueError(f"{universe_path} contains invalid pair values")
    return pairs


def load_daily_closes(pair: str, data_dir: Path, timeframe: str = DEFAULT_TIMEFRAME) -> dict[date, float]:
    data_file = pair_to_data_file(pair, data_dir, timeframe)
    if not data_file.exists():
        raise FileNotFoundError(f"Missing candle file for {pair}: {data_file}")

    dataframe = pd.read_feather(data_file)
    required_columns = {"date", "close"}
    if not required_columns.issubset(dataframe.columns):
        missing = ", ".join(sorted(required_columns - set(dataframe.columns)))
        raise ValueError(f"{data_file} is missing required columns: {missing}")

    dataframe = dataframe[["date", "close"]].copy()
    dataframe["date"] = pd.to_datetime(dataframe["date"], utc=True).dt.date
    dataframe["close"] = pd.to_numeric(dataframe["close"], errors="coerce")
    dataframe = dataframe.dropna(subset=["date", "close"]).sort_values("date")
    dataframe = dataframe.drop_duplicates(subset=["date"], keep="last")
    return dict(zip(dataframe["date"], dataframe["close"], strict=True))


def load_universe_closes(
    *,
    pairs: list[str],
    data_dir: Path,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> dict[str, dict[date, float]]:
    return {pair: load_daily_closes(pair, data_dir, timeframe) for pair in pairs}


def iter_dates(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current < end:
        days.append(current)
        current += timedelta(days=1)
    return days


def trailing_return(
    *,
    closes: dict[date, float],
    ranking_date: date,
    lookback_days: int,
) -> float | None:
    latest_close_date = ranking_date - timedelta(days=1)
    prior_close_date = ranking_date - timedelta(days=lookback_days + 1)
    latest_close = closes.get(latest_close_date)
    prior_close = closes.get(prior_close_date)
    if latest_close is None or prior_close is None or prior_close <= 0:
        return None
    return (latest_close / prior_close) - 1.0


def rank_pairs_for_date(
    *,
    closes_by_pair: dict[str, dict[date, float]],
    ranking_date: date,
    lookback_days: int,
) -> list[str]:
    returns: list[tuple[str, float]] = []
    for pair, closes in closes_by_pair.items():
        pair_return = trailing_return(
            closes=closes,
            ranking_date=ranking_date,
            lookback_days=lookback_days,
        )
        if pair_return is not None:
            returns.append((pair, pair_return))

    returns.sort(key=lambda item: (-item[1], item[0]))
    return [pair for pair, _ in returns]


def build_daily_rankings(
    *,
    closes_by_pair: dict[str, dict[date, float]],
    start: date,
    end: date,
    lookback_days: int,
) -> dict[str, list[str]]:
    return {
        ranking_date.isoformat(): rank_pairs_for_date(
            closes_by_pair=closes_by_pair,
            ranking_date=ranking_date,
            lookback_days=lookback_days,
        )
        for ranking_date in iter_dates(start, end)
    }


def default_output_path(start: date, end: date) -> Path:
    return DEFAULT_OUTPUT_DIR / (
        f"daily_momentum_rank_{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}.json"
    )


def write_rankings(rankings: dict[str, list[str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rankings, indent=2) + "\n", encoding="utf-8")


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.start >= args.end:
        parser.error("--start must be before --end")
    if args.lookback_days <= 0:
        parser.error("--lookback-days must be greater than zero")
    if args.top <= 0:
        parser.error("--top must be greater than zero")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)

    try:
        pairs = load_universe_pairs(args.universe)
        closes_by_pair = load_universe_closes(
            pairs=pairs,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
        rankings = build_daily_rankings(
            closes_by_pair=closes_by_pair,
            start=args.start,
            end=args.end,
            lookback_days=args.lookback_days,
        )
        output_path = args.output or default_output_path(args.start, args.end)
        write_rankings(rankings, output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"rank_pairs_by_momentum: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote daily momentum ranking JSON: {output_path} "
        f"({len(rankings)} days, downstream top {args.top})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
