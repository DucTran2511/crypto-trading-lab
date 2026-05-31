"""Run same-window baseline backtests and collect comparative metrics."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import zipfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_STRATEGIES = (
    "EMACrossover",
    "DonchianBreakout",
    "BollingerMeanReversion",
    "RSITrend",
    "MACDVolume",
)
DEFAULT_PAIRS = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT")
SUMMARY_FIELDS = [
    "strategy",
    "trades",
    "win_rate_pct",
    "total_profit_pct",
    "sharpe",
    "max_drawdown_pct",
    "profit_factor",
]


@dataclass(frozen=True)
class BaselineMetrics:
    """Comparable metrics extracted from one Freqtrade backtest export."""

    strategy: str
    trades: int
    win_rate_pct: float
    total_profit_pct: float
    sharpe: float | None
    max_drawdown_pct: float
    profit_factor: float | None

    def as_row(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "trades": self.trades,
            "win_rate_pct": self.win_rate_pct,
            "total_profit_pct": self.total_profit_pct,
            "sharpe": self.sharpe,
            "max_drawdown_pct": self.max_drawdown_pct,
            "profit_factor": self.profit_factor,
        }


Runner = Callable[..., subprocess.CompletedProcess[str]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run same-window Freqtrade backtests for baseline strategies.",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=list(DEFAULT_STRATEGIES),
        help="Strategy class names to backtest.",
    )
    parser.add_argument(
        "--timerange",
        default="20250101-20250501",
        help="Freqtrade timerange to backtest, e.g. 20250101-20250501.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("user_data/config.json"),
        help="Freqtrade config path.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("user_data/backtest_results"),
        help="Directory for Freqtrade exports and summary files.",
    )
    parser.add_argument(
        "--freqtrade-bin",
        default=".venv/bin/freqtrade",
        help="Freqtrade executable to run.",
    )
    parser.add_argument(
        "--timeframe",
        default=None,
        help="Optional Freqtrade timeframe override, e.g. 1d.",
    )
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=list(DEFAULT_PAIRS),
        help="Pairs described in the Markdown report.",
    )
    return parser


def run_backtest(
    *,
    strategy: str,
    config_path: Path,
    timerange: str,
    results_dir: Path,
    freqtrade_bin: str,
    pairs: Sequence[str],
    timeframe: str | None = None,
    runner: Runner = subprocess.run,
) -> Path | None:
    print(f"Running backtest for {strategy}...", file=sys.stderr)
    export_filename = results_dir / f"baseline_{strategy}.json"
    cmd = [
        freqtrade_bin,
        "backtesting",
        "-c",
        str(config_path),
        "--strategy",
        strategy,
        "--timerange",
        timerange,
        "--export",
        "trades",
        "--export-filename",
        str(export_filename),
        "--cache",
        "none",
        "--pairs",
        *pairs,
    ]
    if timeframe:
        cmd.extend(["--timeframe", timeframe])
    res = runner(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        print(f"Error running backtest for {strategy}:", file=sys.stderr)
        print(res.stderr or res.stdout, file=sys.stderr)
        return None

    last_result_file = results_dir / ".last_result.json"
    if not last_result_file.exists():
        print(f"Error: .last_result.json not found after running {strategy}", file=sys.stderr)
        return None

    try:
        last_result = json.loads(last_result_file.read_text(encoding="utf-8"))
        latest_zip = last_result.get("latest_backtest")
        if not latest_zip:
            print(
                f"Error: latest_backtest key not found in .last_result.json for {strategy}",
                file=sys.stderr,
            )
            return None
        latest_path = Path(latest_zip)
        return latest_path if latest_path.is_absolute() else results_dir / latest_path
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading .last_result.json for {strategy}: {exc}", file=sys.stderr)
        return None


def parse_backtest_zip(zip_path: Path, strategy: str) -> BaselineMetrics | None:
    try:
        with zipfile.ZipFile(zip_path) as z:
            json_file = None
            for name in z.namelist():
                if name.endswith(".json") and not name.endswith("_config.json"):
                    json_file = name
                    break

            if not json_file:
                print(f"Error: JSON file not found in zip {zip_path}", file=sys.stderr)
                return None

            data = json.loads(z.read(json_file).decode("utf-8"))
            strategy_data = data.get("strategy", {}).get(strategy)
            if not strategy_data:
                strategy_keys = list(data.get("strategy", {}).keys())
                if len(strategy_keys) == 1:
                    strategy_data = data["strategy"][strategy_keys[0]]
                else:
                    print(f"Error: no strategy data found in {json_file}", file=sys.stderr)
                    return None

            return BaselineMetrics(
                strategy=strategy,
                trades=int(strategy_data.get("total_trades", 0)),
                win_rate_pct=float(strategy_data.get("winrate", 0.0)) * 100.0,
                total_profit_pct=float(strategy_data.get("profit_total", 0.0)) * 100.0,
                sharpe=strategy_data.get("sharpe"),
                max_drawdown_pct=float(strategy_data.get("max_drawdown_account", 0.0)) * 100.0,
                profit_factor=strategy_data.get("profit_factor"),
            )
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"Error parsing zip {zip_path}: {exc}", file=sys.stderr)
        return None


def write_summary(
    *,
    results: Sequence[BaselineMetrics],
    results_dir: Path,
    timerange: str,
    pairs: Sequence[str],
) -> tuple[Path, Path]:
    csv_file = results_dir / "baseline_validation_summary.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(result.as_row() for result in results)

    md_file = results_dir / "baseline_validation_summary.md"
    md_file.write_text(
        build_markdown_report(results=results, timerange=timerange, pairs=pairs),
        encoding="utf-8",
    )
    return csv_file, md_file


def build_markdown_report(
    *,
    results: Sequence[BaselineMetrics],
    timerange: str,
    pairs: Sequence[str],
) -> str:
    md_content = [
        "# Baseline Strategy Validation Report",
        "",
        f"**Timerange:** `{timerange}`",
        f"**Pairs:** {', '.join(f'`{pair}`' for pair in pairs)} (OKX Spot)",
        "",
        "| Strategy | Trades | Win Rate % | Total Profit % | Sharpe | Max Drawdown % | Profit Factor |",
        "|---|---|---|---|---|---|---|",
    ]

    for result in results:
        row = result.as_row()
        sharpe_str = f"{row['sharpe']:.2f}" if row["sharpe"] is not None else "N/A"
        pf_str = f"{row['profit_factor']:.2f}" if row["profit_factor"] is not None else "N/A"
        md_content.append(
            f"| {row['strategy']} | {row['trades']} | {row['win_rate_pct']:.2f}% | "
            f"{row['total_profit_pct']:.2f}% | {sharpe_str} | "
            f"{row['max_drawdown_pct']:.2f}% | {pf_str} |"
        )

    md_content.extend(["", "## Recommendation", "", "Candidates for walk-forward sweeps:"])
    candidate_lines = candidate_recommendations(results)
    if candidate_lines:
        md_content.extend(candidate_lines)
    else:
        md_content.append("- None. Keep these as controls and research new filters or exits.")

    return "\n".join(md_content) + "\n"


def candidate_recommendations(results: Sequence[BaselineMetrics]) -> list[str]:
    recommendations = []
    for result in results:
        reasons = []
        if result.total_profit_pct > -10.0 and result.trades >= 20:
            reasons.append("positive or low-loss return with reasonable trade count")
        if result.sharpe is not None and result.sharpe > -10.0:
            reasons.append("decent Sharpe relative to crossover baseline")
        if reasons:
            recommendations.append(f"- **{result.strategy}**: {', '.join(reasons)}")
    return recommendations


def run_baselines(
    *,
    strategies: Sequence[str],
    timerange: str,
    config_path: Path,
    results_dir: Path,
    freqtrade_bin: str,
    pairs: Sequence[str],
    timeframe: str | None = None,
    runner: Runner = subprocess.run,
) -> tuple[Path, Path] | None:
    results_dir.mkdir(parents=True, exist_ok=True)
    results: list[BaselineMetrics] = []

    for strategy in strategies:
        zip_path = run_backtest(
            strategy=strategy,
            config_path=config_path,
            timerange=timerange,
            results_dir=results_dir,
            freqtrade_bin=freqtrade_bin,
            pairs=pairs,
            timeframe=timeframe,
            runner=runner,
        )
        if zip_path:
            metrics = parse_backtest_zip(zip_path, strategy)
            if metrics:
                results.append(metrics)
                print(f"Successfully processed {strategy}", file=sys.stderr)
                print(f"  Trades: {metrics.trades}", file=sys.stderr)
                print(f"  Profit: {metrics.total_profit_pct:.2f}%", file=sys.stderr)
                print(f"  Sharpe: {metrics.sharpe}", file=sys.stderr)
            else:
                print(f"Failed to parse metrics for {strategy}", file=sys.stderr)
        else:
            print(f"Failed to run backtest for {strategy}", file=sys.stderr)

    if not results:
        print("No results collected.", file=sys.stderr)
        return None

    return write_summary(results=results, results_dir=results_dir, timerange=timerange, pairs=pairs)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary_files = run_baselines(
        strategies=args.strategies,
        timerange=args.timerange,
        config_path=args.config,
        results_dir=args.results_dir,
        freqtrade_bin=args.freqtrade_bin,
        pairs=args.pairs,
        timeframe=args.timeframe,
    )
    if summary_files is None:
        return 1

    csv_file, md_file = summary_files
    print(f"Wrote CSV: {csv_file}", file=sys.stderr)
    print(f"Wrote Markdown report: {md_file}", file=sys.stderr)
    print(md_file.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
