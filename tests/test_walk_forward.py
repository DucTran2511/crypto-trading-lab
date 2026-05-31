from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest

from scripts.walk_forward import (
    BacktestMetrics,
    CommandResult,
    WalkForwardConfig,
    extract_backtest_metrics,
    generate_folds,
    parse_date,
    parse_duration_days,
    run_walk_forward,
)


def test_parse_date_accepts_dash_and_compact_formats():
    assert parse_date("2025-01-31") == date(2025, 1, 31)
    assert parse_date("20250131") == date(2025, 1, 31)


def test_parse_duration_days_accepts_day_suffix_or_plain_integer():
    assert parse_duration_days("30d") == 30
    assert parse_duration_days("30") == 30


def test_generate_folds_slides_until_out_sample_would_exceed_end():
    folds = generate_folds(
        start=date(2025, 1, 1),
        end=date(2025, 5, 1),
        in_sample_days=60,
        out_sample_days=30,
        step_days=30,
    )

    assert [fold.in_sample_timerange for fold in folds] == [
        "20250101-20250302",
        "20250131-20250401",
    ]
    assert [fold.out_sample_timerange for fold in folds] == [
        "20250302-20250401",
        "20250401-20250501",
    ]


def test_generate_folds_rejects_too_short_date_range():
    with pytest.raises(ValueError, match="too short"):
        generate_folds(
            start=date(2025, 1, 1),
            end=date(2025, 2, 1),
            in_sample_days=60,
            out_sample_days=30,
            step_days=30,
        )


def test_extract_backtest_metrics_from_strategy_export(tmp_path: Path):
    export_file = tmp_path / "backtest.json"
    export_file.write_text(
        json.dumps(
            {
                "strategy": {
                    "EMACrossover": {
                        "sharpe": 1.25,
                        "max_drawdown_account": 0.0725,
                        "profit_total": 0.143,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    metrics = extract_backtest_metrics(export_file, "", "", "EMACrossover")

    assert metrics == BacktestMetrics(
        sharpe=1.25,
        max_drawdown_pct=7.249999999999999,
        total_profit_pct=14.299999999999999,
    )


def test_extract_backtest_metrics_from_stdout_when_no_export(tmp_path: Path):
    metrics = extract_backtest_metrics(
        tmp_path / "missing.json",
        "Sharpe: 0.44\nMax drawdown %: 12.5\nTotal profit %: -3.2",
        "",
        "EMACrossover",
    )

    assert metrics == BacktestMetrics(
        sharpe=0.44,
        max_drawdown_pct=12.5,
        total_profit_pct=-3.2,
    )


def test_extract_backtest_metrics_from_stdout_new_drawdown_label(tmp_path: Path):
    metrics = extract_backtest_metrics(
        tmp_path / "missing.json",
        "Sharpe: 0.88\nAbsolute Drawdown (Account): 3.14%\nTotal profit %: 5.5",
        "",
        "EMACrossover",
    )

    assert metrics == BacktestMetrics(
        sharpe=0.88,
        max_drawdown_pct=3.14,
        total_profit_pct=5.5,
    )


def test_extract_backtest_metrics_from_zip(tmp_path: Path):
    import zipfile
    zip_file = tmp_path / "backtest-2026-05-24_17-20-47.zip"
    export_file = tmp_path / "backtest.json"

    with zipfile.ZipFile(zip_file, "w") as z:
        z.writestr(
            "backtest_results.json",
            json.dumps(
                {
                    "strategy": {
                        "EMACrossover": {
                            "sharpe": 1.5,
                            "max_drawdown_account": 0.05,
                            "profit_total": 0.1,
                        }
                    }
                }
            )
        )

    metrics = extract_backtest_metrics(export_file, "", "", "EMACrossover")
    assert metrics == BacktestMetrics(
        sharpe=1.5,
        max_drawdown_pct=5.0,
        total_profit_pct=10.0,
    )


def test_run_walk_forward_orchestrates_hyperopt_and_backtests(tmp_path: Path):
    strategy_path = tmp_path / "strategies"
    strategy_path.mkdir()
    params_file = strategy_path / "EMACrossover.json"
    params_file.write_text('{"existing": true}\n', encoding="utf-8")
    commands: list[list[str]] = []

    def fake_runner(command: list[str]) -> CommandResult:
        commands.append(command)
        subcommand = command[1]
        if subcommand == "hyperopt":
            params_file.write_text('{"fold_param": 1}\n', encoding="utf-8")
            return CommandResult(returncode=0, stdout="hyperopt ok", stderr="")

        export_path = Path(command[command.index("--export-filename") + 1])
        timerange = command[command.index("--timerange") + 1]
        sharpe = 2.0 if timerange == "20250101-20250302" else 0.5
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(
            json.dumps(
                {
                    "strategy": {
                        "EMACrossover": {
                            "sharpe": sharpe,
                            "max_drawdown_pct": 8.0,
                            "profit_total_pct": 4.5,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return CommandResult(returncode=0, stdout="backtest ok", stderr="")

    summary_file = run_walk_forward(
        WalkForwardConfig(
            strategy="EMACrossover",
            start=date(2025, 1, 1),
            end=date(2025, 4, 1),
            in_sample_days=60,
            out_sample_days=30,
            step_days=30,
            loss="SharpeHyperOptLoss",
            epochs=25,
            config_path=tmp_path / "config.json",
            output_dir=tmp_path / "walk_forward",
            spaces=("buy",),
            pairs=("BTC/USDT", "ETH/USDT"),
            timeframe="1d",
            freqtrade_bin="freqtrade",
            strategy_path=strategy_path,
            random_state=7,
            jobs=2,
            no_plot=False,
        ),
        runner=fake_runner,
    )

    assert [command[1] for command in commands] == ["hyperopt", "backtesting", "backtesting"]
    assert "--random-state" in commands[0]
    assert "-j" in commands[0]
    assert "--random-state" not in commands[1]
    assert "-j" not in commands[1]
    assert commands[1][commands[1].index("--cache") + 1] == "none"
    for command in commands:
        pairs_index = command.index("--pairs")
        assert command[pairs_index + 1 : pairs_index + 3] == ["BTC/USDT", "ETH/USDT"]
        assert command[command.index("--timeframe") + 1] == "1d"
    assert params_file.read_text(encoding="utf-8") == '{"existing": true}\n'

    with summary_file.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["in_sample_sharpe"] == "2.0"
    assert rows[0]["out_sample_sharpe"] == "0.5"
    assert Path(rows[0]["params_file"]).read_text(encoding="utf-8") == '{"fold_param": 1}\n'
    assert (tmp_path / "walk_forward" / "walk_forward_stability.png").exists()
