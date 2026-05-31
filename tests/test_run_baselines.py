from __future__ import annotations

import csv
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.run_baselines import (
    BaselineMetrics,
    build_markdown_report,
    build_parser,
    parse_backtest_zip,
    run_backtest,
    write_summary,
)


def _write_backtest_zip(path: Path, strategy: str = "RSITrend") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "backtest.json",
            json.dumps(
                {
                    "strategy": {
                        strategy: {
                            "total_trades": 76,
                            "winrate": 0.2105,
                            "profit_total": -0.0173,
                            "sharpe": -3.58,
                            "max_drawdown_account": 0.0189,
                            "profit_factor": 0.5,
                        }
                    }
                }
            ),
        )
        archive.writestr("backtest_config.json", "{}")


def test_parser_help_exits_without_running_backtests(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0
    assert "Run same-window Freqtrade backtests" in capsys.readouterr().out


def test_run_backtest_builds_command_and_reads_last_result(tmp_path: Path):
    commands: list[list[str]] = []

    def fake_runner(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        (tmp_path / ".last_result.json").write_text(
            json.dumps({"latest_backtest": "baseline_RSITrend.zip"}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "ok", "")

    zip_path = run_backtest(
        strategy="RSITrend",
        config_path=tmp_path / "config.json",
        timerange="20250101-20250501",
        results_dir=tmp_path,
        freqtrade_bin="freqtrade",
        pairs=["BTC/USDT", "ETH/USDT"],
        runner=fake_runner,
    )

    assert zip_path == tmp_path / "baseline_RSITrend.zip"
    command = commands[0]
    assert command[:2] == ["freqtrade", "backtesting"]
    assert command[command.index("--strategy") + 1] == "RSITrend"
    assert command[command.index("--timerange") + 1] == "20250101-20250501"
    assert command[command.index("--cache") + 1] == "none"
    assert command[command.index("--pairs") + 1 :] == ["BTC/USDT", "ETH/USDT"]


def test_parse_backtest_zip_extracts_comparable_metrics(tmp_path: Path):
    zip_path = tmp_path / "backtest.zip"
    _write_backtest_zip(zip_path)

    metrics = parse_backtest_zip(zip_path, "RSITrend")

    assert metrics is not None
    assert metrics.strategy == "RSITrend"
    assert metrics.trades == 76
    assert metrics.win_rate_pct == pytest.approx(21.05)
    assert metrics.total_profit_pct == pytest.approx(-1.73)
    assert metrics.sharpe == -3.58
    assert metrics.max_drawdown_pct == pytest.approx(1.89)
    assert metrics.profit_factor == 0.5


def test_parse_backtest_zip_returns_none_when_strategy_is_missing(tmp_path: Path):
    zip_path = tmp_path / "backtest.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "backtest.json",
            json.dumps(
                {
                    "strategy": {
                        "FirstStrategy": {},
                        "SecondStrategy": {},
                    }
                }
            ),
        )

    assert parse_backtest_zip(zip_path, "RSITrend") is None


def test_write_summary_creates_csv_and_markdown(tmp_path: Path):
    results = [
        BaselineMetrics(
            strategy="BollingerMeanReversion",
            trades=9,
            win_rate_pct=66.67,
            total_profit_pct=0.09,
            sharpe=0.5,
            max_drawdown_pct=0.03,
            profit_factor=3.4,
        ),
        BaselineMetrics(
            strategy="RSITrend",
            trades=76,
            win_rate_pct=21.05,
            total_profit_pct=-1.73,
            sharpe=-3.58,
            max_drawdown_pct=1.89,
            profit_factor=0.5,
        ),
    ]

    csv_file, md_file = write_summary(
        results=results,
        results_dir=tmp_path,
        timerange="20250101-20250501",
        pairs=["BTC/USDT", "ETH/USDT"],
    )

    with csv_file.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["strategy"] == "BollingerMeanReversion"
    assert rows[1]["trades"] == "76"
    markdown = md_file.read_text(encoding="utf-8")
    assert "**Timerange:** `20250101-20250501`" in markdown
    assert "`BTC/USDT`, `ETH/USDT`" in markdown
    assert "**RSITrend**" in markdown


def test_build_markdown_report_handles_no_candidates():
    markdown = build_markdown_report(
        results=[
            BaselineMetrics(
                strategy="MACDVolume",
                trades=10,
                win_rate_pct=10.0,
                total_profit_pct=-50.0,
                sharpe=-100.0,
                max_drawdown_pct=50.0,
                profit_factor=0.3,
            )
        ],
        timerange="20250101-20250501",
        pairs=["BTC/USDT"],
    )

    assert "None. Keep these as controls" in markdown
