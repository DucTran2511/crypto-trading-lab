from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.regime_filter_experiments import (
    RegimeExperimentResult,
    RegimeVariant,
    build_markdown_report,
    build_variant_strategy_source,
    is_walk_forward_candidate,
    run_backtest,
    variants_for_strategy,
    write_summary,
    write_variant_strategy,
)
from scripts.run_baselines import BaselineMetrics


def _metrics(strategy: str, *, trades: int = 40, profit: float = 1.0, drawdown: float = 2.0):
    return BaselineMetrics(
        strategy=strategy,
        trades=trades,
        win_rate_pct=45.0,
        total_profit_pct=profit,
        sharpe=0.2,
        max_drawdown_pct=drawdown,
        profit_factor=1.1,
    )


def test_variants_keep_all_regime_as_control_strategy_name():
    variants = variants_for_strategy("BollingerMeanReversion")

    assert [variant.variant for variant in variants] == [
        "all-regime",
        "bull-only",
        "bear-excluded",
        "trending-only",
    ]
    assert variants[0].strategy_name == "BollingerMeanReversion"
    assert variants[1].strategy_name == "BollingerMeanReversionBullOnly"
    assert variants[2].allowed_regimes == ("bull", "range")


def test_build_variant_strategy_source_applies_classifier_after_parent_entry_logic():
    variant = RegimeVariant(
        candidate_strategy="BollingerMeanReversion",
        variant="bull-only",
        strategy_name="BollingerMeanReversionBullOnly",
        allowed_regimes=("bull",),
    )

    source = build_variant_strategy_source(variant)

    assert "class BollingerMeanReversionBullOnly(BollingerMeanReversion):" in source
    assert "Path(__file__).resolve().parents[3]" in source
    assert "classify_regime(dataframe)" in source
    assert "dataframe = super().populate_entry_trend(dataframe, metadata)" in source
    assert '~dataframe["regime"].isin(self.allowed_regimes)' in source
    assert "allowed_regimes = ('bull',)" in source


def test_write_variant_strategy_requires_existing_base_strategy_file(tmp_path: Path):
    variant = variants_for_strategy("MissingStrategy")[1]

    with pytest.raises(FileNotFoundError):
        write_variant_strategy(
            variant=variant,
            strategy_dir=tmp_path / "generated",
            base_strategy_path=tmp_path / "strategies",
        )


def test_run_backtest_builds_strategy_path_command_and_reads_last_result(tmp_path: Path):
    commands: list[list[str]] = []
    variant = RegimeVariant(
        candidate_strategy="BollingerMeanReversion",
        variant="bull-only",
        strategy_name="BollingerMeanReversionBullOnly",
        allowed_regimes=("bull",),
    )

    def fake_runner(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        (tmp_path / ".last_result.json").write_text(
            json.dumps({"latest_backtest": "regime_filter.zip"}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "ok", "")

    zip_path = run_backtest(
        variant=variant,
        config_path=tmp_path / "config.json",
        timerange="20250101-20250501",
        results_dir=tmp_path,
        freqtrade_bin="freqtrade",
        strategy_path=tmp_path / "generated",
        runner=fake_runner,
    )

    assert zip_path == tmp_path / "regime_filter.zip"
    command = commands[0]
    assert command[:2] == ["freqtrade", "backtesting"]
    assert command[command.index("--strategy") + 1] == "BollingerMeanReversionBullOnly"
    assert command[command.index("--strategy-path") + 1] == str(tmp_path / "generated")


def test_walk_forward_candidate_requires_improvement_trade_count_and_drawdown_control():
    control = _metrics("BollingerMeanReversion", trades=30, profit=-1.0, drawdown=5.0)

    assert is_walk_forward_candidate(
        metrics=_metrics("Filtered", trades=30, profit=0.0, drawdown=5.0),
        control_metrics=control,
        min_trades=20,
        max_drawdown_worsening_pct=0.0,
    )
    assert not is_walk_forward_candidate(
        metrics=_metrics("Filtered", trades=10, profit=0.0, drawdown=5.0),
        control_metrics=control,
        min_trades=20,
        max_drawdown_worsening_pct=0.0,
    )
    assert not is_walk_forward_candidate(
        metrics=_metrics("Filtered", trades=30, profit=0.0, drawdown=5.1),
        control_metrics=control,
        min_trades=20,
        max_drawdown_worsening_pct=0.0,
    )


def test_write_summary_creates_csv_and_markdown(tmp_path: Path):
    control_variant = variants_for_strategy("BollingerMeanReversion")[0]
    filtered_variant = variants_for_strategy("BollingerMeanReversion")[1]
    control = _metrics("BollingerMeanReversion", profit=-1.0, drawdown=5.0)
    filtered = _metrics("BollingerMeanReversionBullOnly", profit=0.5, drawdown=4.0)
    results = [
        RegimeExperimentResult(control_variant, control, control, False),
        RegimeExperimentResult(filtered_variant, filtered, control, True),
    ]

    csv_file, md_file = write_summary(
        results=results,
        results_dir=tmp_path,
        timerange="20250101-20250501",
        pairs=["BTC/USDT", "ETH/USDT"],
    )

    assert csv_file.read_text(encoding="utf-8").splitlines()[1].startswith(
        "BollingerMeanReversion,all-regime"
    )
    markdown = md_file.read_text(encoding="utf-8")
    assert "The `all-regime` row is the unfiltered baseline control" in markdown
    assert "| `BollingerMeanReversion` | bull-only | `bull` |" in markdown
    assert "Run walk-forward validation" in markdown


def test_build_markdown_report_documents_no_promising_variants():
    variant = variants_for_strategy("BollingerMeanReversion")[1]
    control = _metrics("BollingerMeanReversion", profit=1.0, drawdown=2.0)
    filtered = _metrics("BollingerMeanReversionBullOnly", profit=0.0, drawdown=1.0)

    markdown = build_markdown_report(
        results=[RegimeExperimentResult(variant, filtered, control, False)],
        timerange="20250101-20250501",
        pairs=["BTC/USDT"],
    )

    assert "No filtered variant cleared the promotion rule" in markdown


def test_generated_backtest_zip_can_be_parsed_by_strategy_name(tmp_path: Path):
    zip_path = tmp_path / "backtest.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "backtest.json",
            json.dumps(
                {
                    "strategy": {
                        "BollingerMeanReversionBullOnly": {
                            "total_trades": 12,
                            "winrate": 0.5,
                            "profit_total": 0.01,
                            "sharpe": 1.0,
                            "max_drawdown_account": 0.02,
                            "profit_factor": 1.5,
                        }
                    }
                }
            ),
        )

    from scripts.run_baselines import parse_backtest_zip

    metrics = parse_backtest_zip(zip_path, "BollingerMeanReversionBullOnly")

    assert metrics is not None
    assert metrics.total_profit_pct == pytest.approx(1.0)
