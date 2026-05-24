"""Run regime-filter backtest experiments against selected baseline strategies."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_baselines import BaselineMetrics, parse_backtest_zip

DEFAULT_CANDIDATES = ("BollingerMeanReversion", "RSITrend")
DEFAULT_PAIRS = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT")
VARIANTS: dict[str, tuple[str, ...] | None] = {
    "all-regime": None,
    "bull-only": ("bull",),
    "bear-excluded": ("bull", "range"),
    "trending-only": ("bull", "bear"),
}
SUMMARY_FIELDS = [
    "candidate_strategy",
    "variant",
    "strategy",
    "allowed_regimes",
    "trades",
    "win_rate_pct",
    "total_profit_pct",
    "sharpe",
    "max_drawdown_pct",
    "profit_factor",
    "control_total_profit_pct",
    "delta_total_profit_pct",
    "control_max_drawdown_pct",
    "delta_max_drawdown_pct",
    "walk_forward_candidate",
]


@dataclass(frozen=True)
class RegimeVariant:
    candidate_strategy: str
    variant: str
    strategy_name: str
    allowed_regimes: tuple[str, ...] | None


@dataclass(frozen=True)
class RegimeExperimentResult:
    variant: RegimeVariant
    metrics: BaselineMetrics
    control_metrics: BaselineMetrics
    walk_forward_candidate: bool

    @property
    def delta_total_profit_pct(self) -> float:
        return self.metrics.total_profit_pct - self.control_metrics.total_profit_pct

    @property
    def delta_max_drawdown_pct(self) -> float:
        return self.metrics.max_drawdown_pct - self.control_metrics.max_drawdown_pct

    def as_row(self) -> dict[str, Any]:
        return {
            "candidate_strategy": self.variant.candidate_strategy,
            "variant": self.variant.variant,
            "strategy": self.variant.strategy_name,
            "allowed_regimes": format_allowed_regimes(self.variant.allowed_regimes),
            "trades": self.metrics.trades,
            "win_rate_pct": self.metrics.win_rate_pct,
            "total_profit_pct": self.metrics.total_profit_pct,
            "sharpe": self.metrics.sharpe,
            "max_drawdown_pct": self.metrics.max_drawdown_pct,
            "profit_factor": self.metrics.profit_factor,
            "control_total_profit_pct": self.control_metrics.total_profit_pct,
            "delta_total_profit_pct": self.delta_total_profit_pct,
            "control_max_drawdown_pct": self.control_metrics.max_drawdown_pct,
            "delta_max_drawdown_pct": self.delta_max_drawdown_pct,
            "walk_forward_candidate": self.walk_forward_candidate,
        }


Runner = Callable[..., subprocess.CompletedProcess[str]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare regime-filtered strategy variants against unfiltered controls.",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=list(DEFAULT_CANDIDATES),
        help="Baseline strategy class names to test.",
    )
    parser.add_argument(
        "--timerange",
        default="20250101-20250501",
        help="Freqtrade timerange to backtest, e.g. 20250101-20250501.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("user_data/config.json"),
        help="Freqtrade config path.",
    )
    parser.add_argument(
        "--base-strategy-path",
        type=Path,
        default=Path("user_data/strategies"),
        help="Directory containing the baseline strategy files.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("user_data/regime_filter_results"),
        help="Directory for generated strategies, backtest exports, and summaries.",
    )
    parser.add_argument(
        "--freqtrade-bin",
        default=".venv/bin/freqtrade",
        help="Freqtrade executable to run.",
    )
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=list(DEFAULT_PAIRS),
        help="Pairs described in the Markdown report.",
    )
    parser.add_argument(
        "--min-trades",
        type=int,
        default=20,
        help="Minimum trades required before a filtered variant can be walk-forward candidate.",
    )
    parser.add_argument(
        "--max-drawdown-worsening-pct",
        type=float,
        default=0.0,
        help="Allowed drawdown worsening versus control before rejecting a variant.",
    )
    parser.add_argument(
        "--walk-forward-promising",
        action="store_true",
        help="Run scripts/walk_forward.py for variants marked as promising.",
    )
    parser.add_argument("--wf-start", default="2025-01-01", help="Walk-forward start date.")
    parser.add_argument("--wf-end", default="2025-05-01", help="Walk-forward end date.")
    parser.add_argument("--wf-in-sample", default="90d", help="Walk-forward in-sample window.")
    parser.add_argument("--wf-out-sample", default="30d", help="Walk-forward out-sample window.")
    parser.add_argument("--wf-step", default="30d", help="Walk-forward step size.")
    parser.add_argument("--wf-loss", default="SharpeHyperOptLoss", help="Hyperopt loss function.")
    parser.add_argument("--wf-epochs", type=int, default=100, help="Hyperopt epochs per fold.")
    return parser


def variants_for_strategy(strategy: str) -> list[RegimeVariant]:
    return [
        RegimeVariant(
            candidate_strategy=strategy,
            variant=variant,
            strategy_name=strategy if regimes is None else f"{strategy}{to_pascal_case(variant)}",
            allowed_regimes=regimes,
        )
        for variant, regimes in VARIANTS.items()
    ]


def to_pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", value) if part)


def format_allowed_regimes(regimes: tuple[str, ...] | None) -> str:
    if regimes is None:
        return "all"
    return ",".join(regimes)


def write_variant_strategy(
    *,
    variant: RegimeVariant,
    strategy_dir: Path,
    base_strategy_path: Path,
) -> Path | None:
    if variant.allowed_regimes is None:
        return None

    source_file = base_strategy_path / f"{variant.candidate_strategy}.py"
    if not source_file.exists():
        raise FileNotFoundError(f"Base strategy file not found: {source_file}")

    strategy_dir.mkdir(parents=True, exist_ok=True)
    strategy_file = strategy_dir / f"{variant.strategy_name}.py"
    strategy_file.write_text(build_variant_strategy_source(variant), encoding="utf-8")
    return strategy_file


def build_variant_strategy_source(variant: RegimeVariant) -> str:
    if variant.allowed_regimes is None:
        raise ValueError("Cannot generate a strategy source for the all-regime control")

    regimes = ", ".join(repr(regime) for regime in variant.allowed_regimes)
    return f'''"""Generated regime-filter experiment variant for {variant.candidate_strategy}."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from user_data.regime.classifier import classify_regime
from user_data.strategies.{variant.candidate_strategy} import {variant.candidate_strategy}


class {variant.strategy_name}({variant.candidate_strategy}):
    """{variant.candidate_strategy} constrained to {format_allowed_regimes(variant.allowed_regimes)} regimes."""

    startup_candle_count = max({variant.candidate_strategy}.startup_candle_count, 240)
    allowed_regimes = ({regimes},)

    def populate_indicators(self, dataframe, metadata):
        dataframe = super().populate_indicators(dataframe, metadata)
        dataframe["regime"] = classify_regime(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe = super().populate_entry_trend(dataframe, metadata)
        dataframe.loc[~dataframe["regime"].isin(self.allowed_regimes), "enter_long"] = 0
        return dataframe
'''


def run_backtest(
    *,
    variant: RegimeVariant,
    config_path: Path,
    timerange: str,
    results_dir: Path,
    freqtrade_bin: str,
    strategy_path: Path | None,
    runner: Runner = subprocess.run,
) -> Path | None:
    print(
        f"Running {variant.candidate_strategy} {variant.variant} backtest...",
        file=sys.stderr,
    )
    export_filename = results_dir / f"{variant.strategy_name}_{variant.variant}.json"
    command = [
        freqtrade_bin,
        "backtesting",
        "-c",
        str(config_path),
        "--strategy",
        variant.strategy_name,
        "--timerange",
        timerange,
        "--export",
        "trades",
        "--export-filename",
        str(export_filename),
        "--cache",
        "none",
    ]
    if strategy_path is not None:
        command.extend(["--strategy-path", str(strategy_path)])

    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"Error running backtest for {variant.strategy_name}:", file=sys.stderr)
        print(result.stderr or result.stdout, file=sys.stderr)
        return None

    return latest_backtest_path(results_dir)


def latest_backtest_path(results_dir: Path) -> Path | None:
    last_result_file = results_dir / ".last_result.json"
    if not last_result_file.exists():
        print("Error: .last_result.json not found after backtest", file=sys.stderr)
        return None

    try:
        latest_zip = json.loads(last_result_file.read_text(encoding="utf-8")).get(
            "latest_backtest"
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading .last_result.json: {exc}", file=sys.stderr)
        return None

    if not latest_zip:
        print("Error: latest_backtest key not found in .last_result.json", file=sys.stderr)
        return None
    latest_path = Path(latest_zip)
    return latest_path if latest_path.is_absolute() else results_dir / latest_path


def is_walk_forward_candidate(
    *,
    metrics: BaselineMetrics,
    control_metrics: BaselineMetrics,
    min_trades: int,
    max_drawdown_worsening_pct: float,
) -> bool:
    return (
        metrics.trades >= min_trades
        and metrics.total_profit_pct > control_metrics.total_profit_pct
        and metrics.max_drawdown_pct
        <= control_metrics.max_drawdown_pct + max_drawdown_worsening_pct
    )


def write_summary(
    *,
    results: Sequence[RegimeExperimentResult],
    results_dir: Path,
    timerange: str,
    pairs: Sequence[str],
) -> tuple[Path, Path]:
    csv_file = results_dir / "regime_filter_summary.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(result.as_row() for result in results)

    md_file = results_dir / "regime_filter_summary.md"
    md_file.write_text(
        build_markdown_report(results=results, timerange=timerange, pairs=pairs),
        encoding="utf-8",
    )
    return csv_file, md_file


def build_markdown_report(
    *,
    results: Sequence[RegimeExperimentResult],
    timerange: str,
    pairs: Sequence[str],
) -> str:
    lines = [
        "# Regime Filter Experiment Report",
        "",
        f"**Timerange:** `{timerange}`",
        f"**Pairs:** {', '.join(f'`{pair}`' for pair in pairs)}",
        "",
        "The `all-regime` row is the unfiltered baseline control for each strategy.",
        "",
        "| Candidate | Variant | Allowed Regimes | Trades | Profit % | Delta Profit % | "
        "Max DD % | Delta Max DD % | Sharpe | Profit Factor | Walk-Forward Candidate |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        row = result.as_row()
        lines.append(
            f"| `{row['candidate_strategy']}` | {row['variant']} | "
            f"`{row['allowed_regimes']}` | {row['trades']} | "
            f"{row['total_profit_pct']:.2f} | {row['delta_total_profit_pct']:.2f} | "
            f"{row['max_drawdown_pct']:.2f} | {row['delta_max_drawdown_pct']:.2f} | "
            f"{format_optional(row['sharpe'])} | {format_optional(row['profit_factor'])} | "
            f"{'yes' if row['walk_forward_candidate'] else 'no'} |"
        )

    candidates = [result for result in results if result.walk_forward_candidate]
    lines.extend(["", "## Decision", ""])
    if candidates:
        lines.append(
            "Run walk-forward validation for the variants marked `yes`; they improved on the "
            "control without exceeding the drawdown filter."
        )
    else:
        lines.append(
            "No filtered variant cleared the promotion rule. Keep the baseline result as the "
            "control and do not claim the regime filter works."
        )
    return "\n".join(lines) + "\n"


def format_optional(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return f"{float(value):.2f}"


def run_walk_forward_for_candidates(
    *,
    results: Sequence[RegimeExperimentResult],
    args: argparse.Namespace,
    generated_strategy_dir: Path,
    runner: Runner = subprocess.run,
) -> None:
    for result in results:
        if not result.walk_forward_candidate:
            continue
        output_dir = args.results_dir / "walk_forward" / result.variant.strategy_name
        command = [
            sys.executable,
            "scripts/walk_forward.py",
            "--strategy",
            result.variant.strategy_name,
            "--start",
            args.wf_start,
            "--end",
            args.wf_end,
            "--in-sample",
            args.wf_in_sample,
            "--out-sample",
            args.wf_out_sample,
            "--step",
            args.wf_step,
            "--loss",
            args.wf_loss,
            "--epochs",
            str(args.wf_epochs),
            "-c",
            str(args.config),
            "--strategy-path",
            str(generated_strategy_dir),
            "--output-dir",
            str(output_dir),
            "--freqtrade-bin",
            args.freqtrade_bin,
        ]
        completed = runner(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            print(
                f"Walk-forward failed for {result.variant.strategy_name}:",
                file=sys.stderr,
            )
            print(completed.stderr or completed.stdout, file=sys.stderr)


def run_experiments(
    *,
    args: argparse.Namespace,
    runner: Runner = subprocess.run,
) -> tuple[Path, Path] | None:
    args.results_dir.mkdir(parents=True, exist_ok=True)
    generated_strategy_dir = args.results_dir / "generated_strategies"
    results: list[RegimeExperimentResult] = []

    for strategy in args.strategies:
        variants = variants_for_strategy(strategy)
        metrics_by_variant: dict[str, BaselineMetrics] = {}

        for variant in variants:
            strategy_path = None
            if variant.allowed_regimes is not None:
                write_variant_strategy(
                    variant=variant,
                    strategy_dir=generated_strategy_dir,
                    base_strategy_path=args.base_strategy_path,
                )
                strategy_path = generated_strategy_dir

            zip_path = run_backtest(
                variant=variant,
                config_path=args.config,
                timerange=args.timerange,
                results_dir=args.results_dir,
                freqtrade_bin=args.freqtrade_bin,
                strategy_path=strategy_path,
                runner=runner,
            )
            if zip_path is None:
                continue
            metrics = parse_backtest_zip(zip_path, variant.strategy_name)
            if metrics is not None:
                metrics_by_variant[variant.variant] = metrics

        control_metrics = metrics_by_variant.get("all-regime")
        if control_metrics is None:
            print(f"Skipping {strategy}: all-regime control did not complete.", file=sys.stderr)
            continue

        for variant in variants:
            metrics = metrics_by_variant.get(variant.variant)
            if metrics is None:
                continue
            promising = False
            if variant.allowed_regimes is not None:
                promising = is_walk_forward_candidate(
                    metrics=metrics,
                    control_metrics=control_metrics,
                    min_trades=args.min_trades,
                    max_drawdown_worsening_pct=args.max_drawdown_worsening_pct,
                )
            results.append(
                RegimeExperimentResult(
                    variant=variant,
                    metrics=metrics,
                    control_metrics=control_metrics,
                    walk_forward_candidate=promising,
                )
            )

    if not results:
        print("No regime experiment results collected.", file=sys.stderr)
        return None

    summary_files = write_summary(
        results=results,
        results_dir=args.results_dir,
        timerange=args.timerange,
        pairs=args.pairs,
    )
    if args.walk_forward_promising:
        run_walk_forward_for_candidates(
            results=results,
            args=args,
            generated_strategy_dir=generated_strategy_dir,
            runner=runner,
        )
    return summary_files


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.min_trades < 0:
        print("--min-trades must be non-negative", file=sys.stderr)
        return 2
    if args.wf_epochs <= 0:
        print("--wf-epochs must be greater than zero", file=sys.stderr)
        return 2

    summary_files = run_experiments(args=args)
    if summary_files is None:
        return 1

    csv_file, md_file = summary_files
    print(f"Wrote CSV: {csv_file}", file=sys.stderr)
    print(f"Wrote Markdown report: {md_file}", file=sys.stderr)
    print(md_file.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
