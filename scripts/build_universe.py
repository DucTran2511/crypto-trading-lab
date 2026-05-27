"""Build a fixed OKX USDT spot pair universe from historical local candles."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

OKX_TICKERS_URL = "https://www.okx.com/api/v5/market/tickers"
DEFAULT_DATA_DIR = Path("user_data/data/okx")
DEFAULT_OUTPUT_DIR = Path("user_data/universes")
DEFAULT_TIMEFRAME = "5m"
DEFAULT_SNAPSHOT_DATE = "2024-07-01"
DEFAULT_TOP_N = 20
VOLUME_WINDOW_DAYS = 30
MIN_HISTORY_MONTHS = 6
STABLECOIN_BASES = {
    "USDC",
    "DAI",
    "TUSD",
    "FDUSD",
    "USDP",
    "PYUSD",
    "GUSD",
    "LUSD",
    "SUSD",
    "USDD",
    "USDE",
    "USDG",
    "USDJ",
    "USDK",
    "USDL",
    "USDS",
    "USDT",
    "USD1",
    "RLUSD",
    "USAT",
    "AUDF",
    "AUDM",
    "BRL1",
    "EURS",
    "EURT",
}
WRAPPED_BASES = {
    "WBTC",
    "WETH",
    "WBNB",
    "WSOL",
    "WAVAX",
    "WMATIC",
    "WSTETH",
    "STETH",
    "RETH",
    "CBETH",
    "BETH",
    "JITOSOL",
    "OKSOL",
}
LEVERAGED_SUFFIXES = ("3L", "3S", "5L", "5S", "UP", "DOWN", "BULL", "BEAR")
SYNTHETIC_BASES = {
    "BTCST",
    "XAUT",
    "PAXG",
}


@dataclass(frozen=True)
class UniverseCandidate:
    pair: str
    inst_id: str
    base: str
    quote_volume_30d: float
    candles: int
    history_start: date
    history_end: date

    def as_row(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "inst_id": self.inst_id,
            "base": self.base,
            "quote_volume_30d": self.quote_volume_30d,
            "candles": self.candles,
            "history_start": self.history_start.isoformat(),
            "history_end": self.history_end.isoformat(),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a top-N OKX USDT spot universe ranked by historical 30d quote volume."
        ),
    )
    parser.add_argument(
        "--snapshot-date",
        type=parse_snapshot_date,
        default=parse_snapshot_date(DEFAULT_SNAPSHOT_DATE),
        help="Snapshot date as YYYY-MM-DD. The 30d volume window ends at this date.",
    )
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="Number of pairs to keep.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Freqtrade OKX data directory containing feather candle files.",
    )
    parser.add_argument(
        "--timeframe",
        default=DEFAULT_TIMEFRAME,
        help="Local candle timeframe to read, e.g. 5m.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path. Defaults to user_data/universes/top<N>_okx_<date>.json.",
    )
    return parser


def parse_snapshot_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected date as YYYY-MM-DD") from exc


def fetch_okx_usdt_spot_tickers() -> list[dict[str, Any]]:
    response = requests.get(OKX_TICKERS_URL, params={"instType": "SPOT"}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "0":
        raise RuntimeError(f"OKX returned non-zero code: {payload.get('code')} {payload.get('msg')}")
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("OKX ticker response did not include a data list")
    return [ticker for ticker in data if isinstance(ticker, dict)]


def ticker_to_pair(ticker: dict[str, Any]) -> tuple[str, str, str] | None:
    inst_id = str(ticker.get("instId", "")).upper()
    parts = inst_id.split("-")
    if len(parts) != 2:
        return None

    base, quote = parts
    if quote != "USDT":
        return None
    return f"{base}/USDT", inst_id, base


def exclusion_reason(base: str) -> str | None:
    base = base.upper()
    if base in STABLECOIN_BASES:
        return "stablecoin"
    if base in WRAPPED_BASES:
        return "wrapped"
    if base in SYNTHETIC_BASES:
        return "synthetic"
    if any(base.endswith(suffix) for suffix in LEVERAGED_SUFFIXES):
        return "leveraged"
    return None


def pair_to_data_file(pair: str, data_dir: Path, timeframe: str) -> Path:
    return data_dir / f"{pair.replace('/', '_')}-{timeframe}.feather"


def load_pair_candles(pair: str, data_dir: Path, timeframe: str) -> pd.DataFrame | None:
    data_file = pair_to_data_file(pair, data_dir, timeframe)
    if not data_file.exists():
        return None

    dataframe = pd.read_feather(data_file)
    required_columns = {"date", "close", "volume"}
    if not required_columns.issubset(dataframe.columns):
        missing = ", ".join(sorted(required_columns - set(dataframe.columns)))
        raise ValueError(f"{data_file} is missing required columns: {missing}")

    dataframe = dataframe[["date", "close", "volume"]].copy()
    dataframe["date"] = pd.to_datetime(dataframe["date"], utc=True).dt.tz_localize(None)
    dataframe["close"] = pd.to_numeric(dataframe["close"], errors="coerce")
    dataframe["volume"] = pd.to_numeric(dataframe["volume"], errors="coerce")
    return dataframe.dropna(subset=["date", "close", "volume"])


def historical_volume_candidate(
    *,
    pair: str,
    inst_id: str,
    base: str,
    data_dir: Path,
    timeframe: str,
    snapshot_date: date,
) -> UniverseCandidate | None:
    candles = load_pair_candles(pair, data_dir, timeframe)
    if candles is None or candles.empty:
        return None

    snapshot_ts = pd.Timestamp(snapshot_date)
    min_start = snapshot_ts - pd.DateOffset(months=MIN_HISTORY_MONTHS)
    history_start = candles["date"].min()
    history_end = candles["date"].max()
    if history_start > min_start:
        return None
    if history_end < snapshot_ts - pd.Timedelta(days=1):
        return None

    window_start = snapshot_ts - pd.Timedelta(days=VOLUME_WINDOW_DAYS)
    window = candles[(candles["date"] >= window_start) & (candles["date"] < snapshot_ts)]
    if window.empty:
        return None

    quote_volume = (window["close"] * window["volume"]).sum()
    if quote_volume <= 0:
        return None

    return UniverseCandidate(
        pair=pair,
        inst_id=inst_id,
        base=base,
        quote_volume_30d=float(quote_volume),
        candles=len(window),
        history_start=history_start.date(),
        history_end=history_end.date(),
    )


def build_universe(
    *,
    tickers: list[dict[str, Any]],
    data_dir: Path,
    timeframe: str,
    snapshot_date: date,
    top: int,
) -> list[UniverseCandidate]:
    candidates: list[UniverseCandidate] = []
    seen_pairs: set[str] = set()

    for ticker in tickers:
        parsed = ticker_to_pair(ticker)
        if parsed is None:
            continue

        pair, inst_id, base = parsed
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        if exclusion_reason(base) is not None:
            continue

        candidate = historical_volume_candidate(
            pair=pair,
            inst_id=inst_id,
            base=base,
            data_dir=data_dir,
            timeframe=timeframe,
            snapshot_date=snapshot_date,
        )
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(key=lambda candidate: (-candidate.quote_volume_30d, candidate.pair))
    return candidates[:top]


def default_output_path(snapshot_date: date, top: int) -> Path:
    return DEFAULT_OUTPUT_DIR / f"top{top}_okx_{snapshot_date.isoformat()}.json"


def write_universe(
    *,
    candidates: list[UniverseCandidate],
    output_path: Path,
    snapshot_date: date,
    top: int,
    timeframe: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "exchange": "okx",
        "market": "spot",
        "quote": "USDT",
        "snapshot_date": snapshot_date.isoformat(),
        "selection": f"top {top} by historical 30d quote volume ending {snapshot_date.isoformat()}",
        "timeframe": timeframe,
        "volume_window_days": VOLUME_WINDOW_DAYS,
        "min_history_months": MIN_HISTORY_MONTHS,
        "pairs": [candidate.pair for candidate in candidates],
        "candidates": [candidate.as_row() for candidate in candidates],
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top <= 0:
        parser.error("--top must be greater than zero")

    try:
        tickers = fetch_okx_usdt_spot_tickers()
        candidates = build_universe(
            tickers=tickers,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
            snapshot_date=args.snapshot_date,
            top=args.top,
        )
    except (OSError, requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"build_universe: {exc}", file=sys.stderr)
        return 1

    if len(candidates) < args.top:
        print(
            f"build_universe: only {len(candidates)} eligible pairs found for top {args.top}",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or default_output_path(args.snapshot_date, args.top)
    write_universe(
        candidates=candidates,
        output_path=output_path,
        snapshot_date=args.snapshot_date,
        top=args.top,
        timeframe=args.timeframe,
    )
    print(f"Wrote universe JSON: {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
