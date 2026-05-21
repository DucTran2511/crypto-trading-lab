"""Download Binance historical OHLCV data from data.binance.vision.

Binance publishes monthly and daily kline archives as zipped CSVs at
``https://data.binance.vision``. The archives are unauthenticated and not
geo-restricted, which makes them the most reliable source of historical data
for backtests when the live ``api.binance.com`` endpoint is unreachable.

This script downloads the requested pairs/timeframes/months, concatenates them
into a single DataFrame per pair, and stores them in Freqtrade's Feather
format (``user_data/data/binance/<PAIR>-<TIMEFRAME>.feather``) so that
``freqtrade backtesting`` can use them directly.

Example:

    python scripts/download_binance_vision.py \
        --pairs BTC/USDT ETH/USDT SOL/USDT BNB/USDT \
        --timeframe 5m \
        --start 2025-01 --end 2025-04
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore",
]
OUTPUT_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


@dataclass(frozen=True)
class Month:
    year: int
    month: int

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


def parse_month(s: str) -> Month:
    parts = s.split("-")
    if len(parts) != 2:
        raise ValueError(f"Expected YYYY-MM, got {s!r}")
    return Month(int(parts[0]), int(parts[1]))


def iter_months(start: Month, end: Month):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield Month(y, m)
        m += 1
        if m == 13:
            m, y = 1, y + 1


def pair_to_symbol(pair: str) -> str:
    """`BTC/USDT` -> `BTCUSDT` (Binance symbol convention)."""
    return pair.replace("/", "").upper()


def pair_to_filename(pair: str) -> str:
    """`BTC/USDT` -> `BTC_USDT` (Freqtrade convention)."""
    return pair.replace("/", "_").upper()


def download_month(pair: str, timeframe: str, month: Month, timeout: int = 60) -> pd.DataFrame:
    symbol = pair_to_symbol(pair)
    url = f"{BASE_URL}/{symbol}/{timeframe}/{symbol}-{timeframe}-{month}.zip"
    resp = requests.get(url, timeout=timeout)
    if resp.status_code == 404:
        # Future or missing month — skip silently.
        return pd.DataFrame(columns=COLUMNS)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            # Binance kline CSVs sometimes ship with a header row, sometimes not.
            # We sniff the first byte: if it's a digit (timestamp) there's no header.
            first = f.read(1)
            f.seek(0)
            header = 0 if not first.isdigit() else None
            df = pd.read_csv(f, header=header, names=COLUMNS)
    return df


def to_freqtrade_frame(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    df = raw.copy()
    # Binance returns timestamps in microseconds for some symbols/months and
    # milliseconds for others; detect by magnitude.
    unit = "us" if df["open_time"].iloc[0] > 10**14 else "ms"
    df["date"] = pd.to_datetime(df["open_time"], unit=unit, utc=True)
    df["date"] = df["date"].dt.tz_localize(None).astype("datetime64[ms]")
    out = df[["date", "open", "high", "low", "close", "volume"]].astype(
        {"open": "float", "high": "float", "low": "float", "close": "float", "volume": "float"}
    )
    return out


def store_pair(out_dir: Path, pair: str, timeframe: str, df: pd.DataFrame) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"{pair_to_filename(pair)}-{timeframe}.feather"
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    df.to_feather(filename, compression="lz4", compression_level=9)
    return filename


def fetch_pair(
    pair: str, timeframe: str, months: list[Month], out_dir: Path
) -> tuple[str, Path, int]:
    frames: list[pd.DataFrame] = []
    for month in months:
        raw = download_month(pair, timeframe, month)
        if raw.empty:
            continue
        frames.append(to_freqtrade_frame(raw))
    if not frames:
        raise RuntimeError(f"No data found for {pair} {timeframe} in given range")
    combined = pd.concat(frames, ignore_index=True)
    path = store_pair(out_dir, pair, timeframe, combined)
    return pair, path, len(combined)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", nargs="+", required=True, help="e.g. BTC/USDT ETH/USDT")
    parser.add_argument("--timeframe", default="5m", help="e.g. 1m, 5m, 15m, 1h, 4h, 1d")
    parser.add_argument("--start", type=parse_month, required=True, help="YYYY-MM")
    parser.add_argument("--end", type=parse_month, required=True, help="YYYY-MM (inclusive)")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("user_data/data/binance"),
        help="Where to write Freqtrade-compatible Feather files",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)

    months = list(iter_months(args.start, args.end))
    print(
        f"Downloading {len(args.pairs)} pair(s) × {len(months)} month(s) "
        f"of {args.timeframe} klines → {args.out_dir}",
        file=sys.stderr,
    )

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(fetch_pair, p, args.timeframe, months, args.out_dir): p
            for p in args.pairs
        }
        for fut in as_completed(futures):
            pair = futures[fut]
            try:
                pair, path, n_rows = fut.result()
            except Exception as exc:
                print(f"  {pair}: FAILED ({exc})", file=sys.stderr)
                continue
            print(f"  {pair}: {n_rows:>7,} rows → {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
