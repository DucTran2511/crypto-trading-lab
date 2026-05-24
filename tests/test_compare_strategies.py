from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.compare_strategies import (
    BaselineResult,
    WalkForwardResult,
    build_comparisons,
    build_markdown_report,
    main,
    read_baseline_results,
    read_walk_forward_results,
)


def test_read_baseline_results_parses_summary_csv(tmp_path: Path):
    csv_file = tmp_path / "baseline_validation_summary.csv"
    csv_file.write_text(
        "\n".join(
            [
                "strategy,trades,win_rate_pct,total_profit_pct,sharpe,max_drawdown_pct,profit_factor",
                "RSITrend,76,21.05,-1.73,-3.58,1.89,0.50",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert read_baseline_results(csv_file) == [
        BaselineResult(
            strategy="RSITrend",
            trades=76,
            win_rate_pct=21.05,
            total_profit_pct=-1.73,
            sharpe=-3.58,
            max_drawdown_pct=1.89,
            profit_factor=0.5,
        )
    ]


def test_read_walk_forward_results_aggregates_oos_metrics(tmp_path: Path):
    strategy_dir = tmp_path / "RSITrend"
    strategy_dir.mkdir()
    summary_file = strategy_dir / "walk_forward_summary.csv"
    with summary_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fold",
                "in_sample_total_profit_pct",
                "out_sample_sharpe",
                "out_sample_max_drawdown_pct",
                "out_sample_total_profit_pct",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "fold": "1",
                "in_sample_total_profit_pct": "2.0",
                "out_sample_sharpe": "1.0",
                "out_sample_max_drawdown_pct": "4.0",
                "out_sample_total_profit_pct": "0.5",
            }
        )
        writer.writerow(
            {
                "fold": "2",
                "in_sample_total_profit_pct": "1.0",
                "out_sample_sharpe": "-1.0",
                "out_sample_max_drawdown_pct": "8.0",
                "out_sample_total_profit_pct": "-0.25",
            }
        )

    results = read_walk_forward_results(tmp_path)

    assert results["RSITrend"] == WalkForwardResult(
        strategy="RSITrend",
        folds=2,
        avg_oos_sharpe=0.0,
        avg_oos_profit_pct=pytest.approx(0.125),
        positive_oos_fold_rate_pct=50.0,
        worst_oos_drawdown_pct=8.0,
        avg_is_oos_profit_gap_pct=pytest.approx(1.375),
    )


def test_build_comparisons_ranks_validated_results_before_controls():
    baselines = [
        BaselineResult(
            strategy="EMACrossover",
            trades=802,
            win_rate_pct=28.4,
            total_profit_pct=-20.8,
            sharpe=-38.7,
            max_drawdown_pct=20.8,
            profit_factor=0.47,
        ),
        BaselineResult(
            strategy="BollingerMeanReversion",
            trades=9,
            win_rate_pct=66.7,
            total_profit_pct=0.09,
            sharpe=0.5,
            max_drawdown_pct=0.03,
            profit_factor=3.4,
        ),
        BaselineResult(
            strategy="RSITrend",
            trades=76,
            win_rate_pct=21.1,
            total_profit_pct=-1.73,
            sharpe=-3.58,
            max_drawdown_pct=1.89,
            profit_factor=0.5,
        ),
    ]
    walk_forward = {
        "BollingerMeanReversion": WalkForwardResult(
            strategy="BollingerMeanReversion",
            folds=1,
            avg_oos_sharpe=-0.47,
            avg_oos_profit_pct=-0.02,
            positive_oos_fold_rate_pct=0.0,
            worst_oos_drawdown_pct=None,
            avg_is_oos_profit_gap_pct=0.16,
        ),
        "RSITrend": WalkForwardResult(
            strategy="RSITrend",
            folds=1,
            avg_oos_sharpe=-100.0,
            avg_oos_profit_pct=-0.08,
            positive_oos_fold_rate_pct=0.0,
            worst_oos_drawdown_pct=None,
            avg_is_oos_profit_gap_pct=0.25,
        ),
    }

    comparisons = build_comparisons(baselines, walk_forward)

    assert [comparison.baseline.strategy for comparison in comparisons] == [
        "BollingerMeanReversion",
        "RSITrend",
        "EMACrossover",
    ]
    assert comparisons[0].status == "Reject"
    assert comparisons[2].status == "Control only"


def test_build_markdown_report_documents_final_research_direction():
    comparisons = build_comparisons(
        [
            BaselineResult(
                strategy="BollingerMeanReversion",
                trades=9,
                win_rate_pct=66.7,
                total_profit_pct=0.09,
                sharpe=0.5,
                max_drawdown_pct=0.03,
                profit_factor=3.4,
            )
        ],
        {
            "BollingerMeanReversion": WalkForwardResult(
                strategy="BollingerMeanReversion",
                folds=1,
                avg_oos_sharpe=-0.47,
                avg_oos_profit_pct=-0.02,
                positive_oos_fold_rate_pct=0.0,
                worst_oos_drawdown_pct=None,
                avg_is_oos_profit_gap_pct=0.16,
            )
        },
    )

    markdown = build_markdown_report(comparisons)

    assert "# 14. Strategy Comparison Report" in markdown
    assert "Worst OOS DD %" in markdown
    assert "Avg IS-OOS Gap %" in markdown
    assert "No baseline is ready for paper trading" in markdown
    assert "Use `BollingerMeanReversion` as the next research control" in markdown


def test_main_includes_regime_walk_forward_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    baseline_csv = tmp_path / "baseline_validation_summary.csv"
    baseline_csv.write_text(
        "\n".join(
            [
                "strategy,trades,win_rate_pct,total_profit_pct,sharpe,max_drawdown_pct,profit_factor",
                "RSITrend,76,21.05,-1.73,-3.58,1.89,0.50",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    regime_root = tmp_path / "regime_walk_forward"
    write_walk_forward_summary(
        regime_root / "RSITrendBullOnly" / "walk_forward_summary.csv",
        [
            {
                "fold": "1",
                "in_sample_total_profit_pct": "0.30",
                "out_sample_sharpe": "0.25",
                "out_sample_max_drawdown_pct": "0.40",
                "out_sample_total_profit_pct": "0.02",
            },
            {
                "fold": "2",
                "in_sample_total_profit_pct": "0.20",
                "out_sample_sharpe": "0.15",
                "out_sample_max_drawdown_pct": "0.20",
                "out_sample_total_profit_pct": "0.01",
            },
        ],
    )
    output = tmp_path / "report.md"

    exit_code = main(
        [
            "--baseline-csv",
            str(baseline_csv),
            "--walk-forward-root",
            str(tmp_path / "missing_baseline_walk_forward"),
            "--regime-walk-forward-root",
            str(regime_root),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    report = output.read_text(encoding="utf-8")
    assert "`RSITrendBullOnly`" in report
    assert "Research candidate" in report
    assert "N/A | N/A | N/A | 2 | 0.01 | 0.20 | 0.40 | 100.00 | 0.23" in report
    assert "`RSITrendBullOnly` ranks first as a research candidate" in report
    captured = capsys.readouterr()
    assert "Wrote strategy comparison report" in captured.err


def write_walk_forward_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fold",
                "in_sample_total_profit_pct",
                "out_sample_sharpe",
                "out_sample_max_drawdown_pct",
                "out_sample_total_profit_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
