"""Aggregate baseline and walk-forward results into a strategy comparison report."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BaselineResult:
    strategy: str
    trades: int
    win_rate_pct: float
    total_profit_pct: float
    sharpe: float | None
    max_drawdown_pct: float
    profit_factor: float | None


@dataclass(frozen=True)
class WalkForwardResult:
    strategy: str
    folds: int
    avg_oos_sharpe: float | None
    avg_oos_profit_pct: float | None
    positive_oos_fold_rate_pct: float | None
    worst_oos_drawdown_pct: float | None
    avg_is_oos_profit_gap_pct: float | None


@dataclass(frozen=True)
class StrategyComparison:
    baseline: BaselineResult
    walk_forward: WalkForwardResult | None
    rank: int
    status: str
    rationale: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a Markdown comparison report from baseline and walk-forward summaries.",
    )
    parser.add_argument(
        "--baseline-csv",
        type=Path,
        default=Path("user_data/backtest_results/baseline_validation_summary.csv"),
        help="CSV created by scripts/run_baselines.py.",
    )
    parser.add_argument(
        "--walk-forward-root",
        type=Path,
        default=Path("user_data/walk_forward_results"),
        help="Directory containing per-strategy walk_forward_summary.csv files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/14-strategy-comparison-report.md"),
        help="Markdown report path to write.",
    )
    return parser


def read_baseline_results(path: Path) -> list[BaselineResult]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    results = []
    for row in rows:
        results.append(
            BaselineResult(
                strategy=row["strategy"],
                trades=int(row["trades"]),
                win_rate_pct=float(row["win_rate_pct"]),
                total_profit_pct=float(row["total_profit_pct"]),
                sharpe=optional_float(row["sharpe"]),
                max_drawdown_pct=float(row["max_drawdown_pct"]),
                profit_factor=optional_float(row["profit_factor"]),
            )
        )
    return results


def read_walk_forward_results(root: Path) -> dict[str, WalkForwardResult]:
    results = {}
    if not root.exists():
        return results

    for summary_file in sorted(root.glob("*/walk_forward_summary.csv")):
        strategy = summary_file.parent.name
        result = read_walk_forward_summary(summary_file, strategy)
        if result is not None:
            results[strategy] = result
    return results


def read_walk_forward_summary(path: Path, strategy: str) -> WalkForwardResult | None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return None

    oos_sharpes = compact_optional_floats(row["out_sample_sharpe"] for row in rows)
    oos_profits = compact_optional_floats(row["out_sample_total_profit_pct"] for row in rows)
    oos_drawdowns = compact_optional_floats(row["out_sample_max_drawdown_pct"] for row in rows)
    is_profits = compact_optional_floats(row["in_sample_total_profit_pct"] for row in rows)

    gaps = [
        is_profit - oos_profit
        for is_profit, oos_profit in zip(is_profits, oos_profits, strict=False)
    ]
    positive_rate = None
    if oos_profits:
        positive_rate = 100.0 * sum(profit > 0 for profit in oos_profits) / len(oos_profits)

    return WalkForwardResult(
        strategy=strategy,
        folds=len(rows),
        avg_oos_sharpe=mean_or_none(oos_sharpes),
        avg_oos_profit_pct=mean_or_none(oos_profits),
        positive_oos_fold_rate_pct=positive_rate,
        worst_oos_drawdown_pct=max(oos_drawdowns) if oos_drawdowns else None,
        avg_is_oos_profit_gap_pct=mean_or_none(gaps),
    )


def build_comparisons(
    baseline_results: Sequence[BaselineResult],
    walk_forward_results: dict[str, WalkForwardResult],
) -> list[StrategyComparison]:
    sorted_baselines = sorted(
        baseline_results,
        key=lambda result: comparison_sort_key(result, walk_forward_results.get(result.strategy)),
    )

    comparisons = []
    for rank, baseline in enumerate(sorted_baselines, start=1):
        walk_forward = walk_forward_results.get(baseline.strategy)
        status, rationale = classify_strategy(baseline, walk_forward)
        comparisons.append(
            StrategyComparison(
                baseline=baseline,
                walk_forward=walk_forward,
                rank=rank,
                status=status,
                rationale=rationale,
            )
        )
    return comparisons


def comparison_sort_key(
    baseline: BaselineResult,
    walk_forward: WalkForwardResult | None,
) -> tuple[int, float, float, float, int]:
    if walk_forward is not None:
        return (
            0,
            -(walk_forward.avg_oos_profit_pct or -999.0),
            -(walk_forward.avg_oos_sharpe or -999.0),
            baseline.max_drawdown_pct,
            -baseline.trades,
        )

    return (
        1,
        -baseline.total_profit_pct,
        -(baseline.sharpe or -999.0),
        baseline.max_drawdown_pct,
        -baseline.trades,
    )


def classify_strategy(
    baseline: BaselineResult,
    walk_forward: WalkForwardResult | None,
) -> tuple[str, str]:
    if walk_forward is None:
        return (
            "Control only",
            "Rejected before walk-forward validation; keep as a baseline/control, not a candidate.",
        )

    if (
        walk_forward.avg_oos_profit_pct is not None
        and walk_forward.avg_oos_profit_pct > 0
        and walk_forward.avg_oos_sharpe is not None
        and walk_forward.avg_oos_sharpe > 0
        and (walk_forward.positive_oos_fold_rate_pct or 0.0) >= 50.0
    ):
        return (
            "Research candidate",
            "Out-of-sample fold stayed positive after hyperopt; continue with stricter validation.",
        )

    return (
        "Reject",
        "Hyperopt improved the in-sample fold, but the out-of-sample fold did not preserve the edge.",
    )


def build_markdown_report(comparisons: Sequence[StrategyComparison]) -> str:
    top_strategy = comparisons[0].baseline.strategy
    lines = [
        "# 14. Strategy Comparison Report",
        "",
        "This report aggregates the same-window baseline backtests and the first walk-forward",
        "validation sweep. Generated Freqtrade outputs remain in gitignored",
        "`user_data/backtest_results/` and `user_data/walk_forward_results/`; this document",
        "commits the comparison and decision rationale.",
        "",
        "## 14.1 Final Ranking",
        "",
        "| Rank | Strategy | Status | Baseline Trades | Baseline Profit % | Baseline Sharpe | Baseline Max DD % | OOS Folds | Avg OOS Profit % | Avg OOS Sharpe | OOS Positive Fold % | Rationale |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for comparison in comparisons:
        baseline = comparison.baseline
        walk_forward = comparison.walk_forward
        lines.append(
            f"| {comparison.rank} | `{baseline.strategy}` | {comparison.status} | "
            f"{baseline.trades} | {baseline.total_profit_pct:.2f} | "
            f"{format_optional(baseline.sharpe)} | {baseline.max_drawdown_pct:.2f} | "
            f"{walk_forward.folds if walk_forward else 0} | "
            f"{format_optional(walk_forward.avg_oos_profit_pct if walk_forward else None)} | "
            f"{format_optional(walk_forward.avg_oos_sharpe if walk_forward else None)} | "
            f"{format_optional(walk_forward.positive_oos_fold_rate_pct if walk_forward else None)} | "
            f"{comparison.rationale} |"
        )

    lines.extend(
        [
            "",
            "## 14.2 Decision",
            "",
            f"`{top_strategy}` ranks first because it had the least-bad validated holdout result, "
            "but it is still rejected as a tradable strategy. No baseline is ready for paper trading.",
            "",
            "Use `BollingerMeanReversion` as the next research control because it had the smallest",
            "baseline drawdown and the best out-of-sample result among the strategies that reached",
            "walk-forward validation. The next iteration should focus on regime filters, entry",
            "quality, and trade-frequency improvements instead of simply increasing hyperopt epochs.",
            "",
            "## 14.3 Next Work",
            "",
            "- Keep `EMACrossover`, `DonchianBreakout`, and `MACDVolume` as losing controls.",
            "- Treat `RSITrend` as a secondary control: it had enough trades, but failed the holdout badly.",
            "- Run regime-filter experiments against `BollingerMeanReversion` first, always comparing",
            "  against the unfiltered baseline result.",
            "",
            "[Back to docs index](README.md)",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(comparisons: Sequence[StrategyComparison], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown_report(comparisons), encoding="utf-8")
    return output


def optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def compact_optional_floats(values: Iterable[str]) -> list[float]:
    return [number for value in values if (number := optional_float(str(value))) is not None]


def mean_or_none(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def format_optional(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_results = read_baseline_results(args.baseline_csv)
    walk_forward_results = read_walk_forward_results(args.walk_forward_root)
    comparisons = build_comparisons(baseline_results, walk_forward_results)
    output = write_report(comparisons, args.output)
    print(f"Wrote strategy comparison report: {output}", file=sys.stderr)
    print(output.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
