"""Run walk-forward hyperopt/backtest folds for a Freqtrade strategy.

Example:

    python scripts/walk_forward.py \
        --strategy EMACrossover \
        --start 2025-01-01 --end 2025-05-01 \
        --in-sample 90d --out-sample 30d --step 30d \
        --loss SharpeHyperOptLoss --epochs 100
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DATE_FORMAT = "%Y%m%d"
CSV_COLUMNS = [
    "fold",
    "in_sample_start",
    "in_sample_end",
    "out_sample_start",
    "out_sample_end",
    "in_sample_sharpe",
    "in_sample_max_drawdown_pct",
    "in_sample_total_profit_pct",
    "out_sample_sharpe",
    "out_sample_max_drawdown_pct",
    "out_sample_total_profit_pct",
    "params_file",
]


@dataclass(frozen=True)
class FoldWindow:
    index: int
    in_sample_start: date
    in_sample_end: date
    out_sample_start: date
    out_sample_end: date

    @property
    def in_sample_timerange(self) -> str:
        return make_timerange(self.in_sample_start, self.in_sample_end)

    @property
    def out_sample_timerange(self) -> str:
        return make_timerange(self.out_sample_start, self.out_sample_end)


@dataclass(frozen=True)
class BacktestMetrics:
    sharpe: float | None
    max_drawdown_pct: float | None
    total_profit_pct: float | None


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WalkForwardConfig:
    strategy: str
    start: date
    end: date
    in_sample_days: int
    out_sample_days: int
    step_days: int
    loss: str
    epochs: int
    config_path: Path
    output_dir: Path
    spaces: tuple[str, ...]
    freqtrade_bin: str = "freqtrade"
    strategy_path: Path | None = None
    random_state: int | None = 42
    jobs: int | None = None
    no_plot: bool = False


CommandRunner = Callable[[list[str]], CommandResult]


class WalkForwardError(RuntimeError):
    """Raised when a walk-forward run cannot proceed safely."""


class StrategyParamsBackup:
    """Restore the user's strategy parameter file after the harness finishes."""

    def __init__(self, params_file: Path) -> None:
        self.params_file = params_file
        self._original_bytes: bytes | None = None
        self._existed = False

    def __enter__(self) -> StrategyParamsBackup:
        if self.params_file.exists():
            self._existed = True
            self._original_bytes = self.params_file.read_bytes()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._existed:
            self.params_file.write_bytes(self._original_bytes or b"")
        elif self.params_file.exists():
            self.params_file.unlink()


def parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Expected date as YYYY-MM-DD or YYYYMMDD, got {value!r}")


def parse_duration_days(value: str) -> int:
    match = re.fullmatch(r"(\d+)\s*d?", value.strip().lower())
    if not match:
        raise argparse.ArgumentTypeError(f"Expected duration in days, e.g. 30d, got {value!r}")
    days = int(match.group(1))
    if days <= 0:
        raise argparse.ArgumentTypeError("Duration must be greater than zero")
    return days


def make_timerange(start: date, end: date) -> str:
    return f"{start.strftime(DATE_FORMAT)}-{end.strftime(DATE_FORMAT)}"


def generate_folds(
    start: date,
    end: date,
    in_sample_days: int,
    out_sample_days: int,
    step_days: int,
) -> list[FoldWindow]:
    if start >= end:
        raise ValueError("Start date must be before end date")

    folds: list[FoldWindow] = []
    cursor = start
    index = 1
    while True:
        in_sample_end = cursor + timedelta(days=in_sample_days)
        out_sample_end = in_sample_end + timedelta(days=out_sample_days)
        if out_sample_end > end:
            break
        folds.append(
            FoldWindow(
                index=index,
                in_sample_start=cursor,
                in_sample_end=in_sample_end,
                out_sample_start=in_sample_end,
                out_sample_end=out_sample_end,
            )
        )
        cursor += timedelta(days=step_days)
        index += 1

    if not folds:
        raise ValueError(
            "Date range is too short for the requested in-sample and out-of-sample windows"
        )
    return folds


def subprocess_runner(command: list[str]) -> CommandResult:
    completed = subprocess.run(command, capture_output=True, check=False, text=True)
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def build_hyperopt_command(config: WalkForwardConfig, fold: FoldWindow) -> list[str]:
    command = [
        config.freqtrade_bin,
        "hyperopt",
        "-c",
        str(config.config_path),
        "--strategy",
        config.strategy,
        "--hyperopt-loss",
        config.loss,
        "--spaces",
        *config.spaces,
        "-e",
        str(config.epochs),
        "--timerange",
        fold.in_sample_timerange,
    ]
    append_strategy_path_option(command, config)
    if config.random_state is not None:
        command.extend(["--random-state", str(config.random_state)])
    if config.jobs is not None:
        command.extend(["-j", str(config.jobs)])
    return command


def build_backtest_command(
    config: WalkForwardConfig,
    timerange: str,
    export_file: Path,
) -> list[str]:
    command = [
        config.freqtrade_bin,
        "backtesting",
        "-c",
        str(config.config_path),
        "--strategy",
        config.strategy,
        "--timerange",
        timerange,
        "--export",
        "trades",
        "--export-filename",
        str(export_file),
        "--cache",
        "none",
    ]
    append_strategy_path_option(command, config)
    return command


def append_strategy_path_option(command: list[str], config: WalkForwardConfig) -> None:
    if config.strategy_path is not None:
        command.extend(["--strategy-path", str(config.strategy_path)])


def run_command(command: list[str], log_file: Path, runner: CommandRunner) -> CommandResult:
    result = runner(command)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        "$ " + " ".join(command) + "\n\n"
        "STDOUT\n"
        f"{result.stdout}\n\n"
        "STDERR\n"
        f"{result.stderr}\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        tail = "\n".join((result.stderr or result.stdout).splitlines()[-20:])
        raise WalkForwardError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n{tail}"
        )
    return result


def strategy_params_file(config: WalkForwardConfig) -> Path:
    strategy_dir = config.strategy_path or Path("user_data/strategies")
    return strategy_dir / f"{config.strategy}.json"


def copy_fold_params(params_file: Path, params_dir: Path, fold: FoldWindow, strategy: str) -> Path:
    params_dir.mkdir(parents=True, exist_ok=True)
    destination = params_dir / f"fold_{fold.index:03d}_{strategy}.json"
    if params_file.exists():
        shutil.copy2(params_file, destination)
    else:
        destination.write_text(
            "{}\n",
            encoding="utf-8",
        )
    return destination


def extract_backtest_metrics(
    export_file: Path,
    stdout: str,
    stderr: str,
    strategy: str,
) -> BacktestMetrics:
    payload = None
    if export_file.exists():
        payload = load_json_if_present(export_file)
    else:
        # Check if Freqtrade exported as a ZIP file (standard in newer versions)
        prefix = export_file.name
        # If prefix ends with .json, remove it to match prefix*
        if prefix.endswith(".json"):
            prefix = prefix[:-5]
        zips = sorted(export_file.parent.glob(f"{prefix}*.zip"))
        if zips:
            zip_path = zips[-1]
            try:
                import zipfile
                with zipfile.ZipFile(zip_path) as z:
                    json_file = None
                    for name in z.namelist():
                        if name.endswith(".json") and not name.endswith("_config.json"):
                            json_file = name
                            break
                    if json_file:
                        payload = json.loads(z.read(json_file).decode("utf-8"))
            except Exception as exc:
                print(f"Error parsing zip {zip_path}: {exc}", file=sys.stderr)

    metrics_source = find_strategy_metrics(payload, strategy) if payload is not None else None
    if metrics_source is not None:
        return BacktestMetrics(
            sharpe=find_numeric(metrics_source, ("sharpe", "sharpe_ratio")),
            max_drawdown_pct=find_percent_metric(
                metrics_source,
                percent_keys=(
                    "max_drawdown_pct",
                    "max_drawdown_account_pct",
                    "max_relative_drawdown_pct",
                    "drawdown_pct",
                ),
                ratio_keys=("max_drawdown", "max_drawdown_account", "max_relative_drawdown"),
            ),
            total_profit_pct=find_percent_metric(
                metrics_source,
                percent_keys=("profit_total_pct", "total_profit_pct", "total_profit_%"),
                ratio_keys=("profit_total", "total_profit"),
            ),
        )

    text = "\n".join(part for part in (stdout, stderr) if part)
    sharpe = find_metric_in_text(text, ("Sharpe", "Sharpe Ratio"))
    max_drawdown_pct = find_metric_in_text(
        text,
        ("Max drawdown %", "Max Drawdown", "Absolute Drawdown (Account)", "Max % of account underwater")
    )
    total_profit_pct = find_metric_in_text(text, ("Total profit %", "Total Profit %"))
    return BacktestMetrics(
        sharpe=sharpe,
        max_drawdown_pct=max_drawdown_pct,
        total_profit_pct=total_profit_pct,
    )


def load_json_if_present(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WalkForwardError(f"Could not parse backtest export JSON at {path}") from exc


def find_strategy_metrics(payload: Any, strategy: str) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        strategy_block = payload.get("strategy")
        if isinstance(strategy_block, dict):
            nested = strategy_block.get(strategy)
            if isinstance(nested, dict):
                return nested

        direct = payload.get(strategy)
        if isinstance(direct, dict):
            return direct

        if has_metric_keys(payload):
            return payload

        for value in payload.values():
            found = find_strategy_metrics(value, strategy)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = find_strategy_metrics(item, strategy)
            if found is not None:
                return found
    return None


def has_metric_keys(payload: dict[str, Any]) -> bool:
    metric_keys = {
        "sharpe",
        "profit_total_pct",
        "total_profit_pct",
        "max_drawdown_pct",
        "max_drawdown_account_pct",
    }
    return bool(metric_keys.intersection(payload))


def find_numeric(payload: dict[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip().rstrip("%"))
            except ValueError:
                continue
    return None


def find_percent_metric(
    payload: dict[str, Any],
    percent_keys: Iterable[str],
    ratio_keys: Iterable[str],
) -> float | None:
    percent_value = find_numeric(payload, percent_keys)
    if percent_value is not None:
        return percent_value

    ratio_value = find_numeric(payload, ratio_keys)
    if ratio_value is None:
        return None
    if -1.0 <= ratio_value <= 1.0:
        return ratio_value * 100
    return ratio_value


def find_metric_in_text(text: str, labels: Iterable[str]) -> float | None:
    for label in labels:
        pattern = re.compile(
            rf"{re.escape(label)}\s*(?:\||│|:)?\s*(-?\d+(?:\.\d+)?)\s*%?",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return float(match.group(1))
    return None


def write_summary_csv(rows: list[dict[str, object]], summary_file: Path) -> None:
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with summary_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def plot_fold_stability(rows: list[dict[str, object]], plot_file: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    folds = [int(row["fold"]) for row in rows]
    oos_profit = [float_or_zero(row["out_sample_total_profit_pct"]) for row in rows]
    oos_sharpe = [float_or_zero(row["out_sample_sharpe"]) for row in rows]

    fig, profit_axis = plt.subplots(figsize=(10, 5))
    profit_axis.bar(folds, oos_profit, color="#3b82f6", alpha=0.78, label="OOS total profit %")
    profit_axis.axhline(0, color="#111827", linewidth=1)
    profit_axis.set_xlabel("Fold")
    profit_axis.set_ylabel("Out-of-sample total profit %")
    profit_axis.set_xticks(folds)

    sharpe_axis = profit_axis.twinx()
    sharpe_axis.plot(folds, oos_sharpe, color="#f97316", marker="o", label="OOS Sharpe")
    sharpe_axis.axhline(0, color="#f97316", linestyle="--", linewidth=1, alpha=0.5)
    sharpe_axis.set_ylabel("Out-of-sample Sharpe")

    handles, labels = profit_axis.get_legend_handles_labels()
    handles_2, labels_2 = sharpe_axis.get_legend_handles_labels()
    profit_axis.legend(handles + handles_2, labels + labels_2, loc="best")
    fig.tight_layout()
    plot_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(plot_file, dpi=150)
    plt.close(fig)


def float_or_zero(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        return float(value)
    return 0.0


def run_walk_forward(
    config: WalkForwardConfig,
    runner: CommandRunner = subprocess_runner,
) -> Path:
    folds = generate_folds(
        config.start,
        config.end,
        config.in_sample_days,
        config.out_sample_days,
        config.step_days,
    )
    logs_dir = config.output_dir / "logs"
    exports_dir = config.output_dir / "backtests"
    params_dir = config.output_dir / "params"
    logs_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)
    params_dir.mkdir(parents=True, exist_ok=True)
    summary_file = config.output_dir / "walk_forward_summary.csv"
    plot_file = config.output_dir / "walk_forward_stability.png"
    params_file = strategy_params_file(config)
    rows: list[dict[str, object]] = []

    with StrategyParamsBackup(params_file):
        for fold in folds:
            print(
                f"Fold {fold.index}: hyperopt {fold.in_sample_timerange}, "
                f"backtest {fold.out_sample_timerange}",
                file=sys.stderr,
            )
            run_command(
                build_hyperopt_command(config, fold),
                logs_dir / f"fold_{fold.index:03d}_hyperopt.log",
                runner,
            )
            fold_params_file = copy_fold_params(params_file, params_dir, fold, config.strategy)

            in_export = exports_dir / f"fold_{fold.index:03d}_in_sample.json"
            in_result = run_command(
                build_backtest_command(config, fold.in_sample_timerange, in_export),
                logs_dir / f"fold_{fold.index:03d}_in_sample_backtest.log",
                runner,
            )
            in_metrics = extract_backtest_metrics(
                in_export,
                in_result.stdout,
                in_result.stderr,
                config.strategy,
            )

            out_export = exports_dir / f"fold_{fold.index:03d}_out_sample.json"
            out_result = run_command(
                build_backtest_command(config, fold.out_sample_timerange, out_export),
                logs_dir / f"fold_{fold.index:03d}_out_sample_backtest.log",
                runner,
            )
            out_metrics = extract_backtest_metrics(
                out_export,
                out_result.stdout,
                out_result.stderr,
                config.strategy,
            )

            rows.append(
                {
                    "fold": fold.index,
                    "in_sample_start": fold.in_sample_start.isoformat(),
                    "in_sample_end": fold.in_sample_end.isoformat(),
                    "out_sample_start": fold.out_sample_start.isoformat(),
                    "out_sample_end": fold.out_sample_end.isoformat(),
                    "in_sample_sharpe": in_metrics.sharpe,
                    "in_sample_max_drawdown_pct": in_metrics.max_drawdown_pct,
                    "in_sample_total_profit_pct": in_metrics.total_profit_pct,
                    "out_sample_sharpe": out_metrics.sharpe,
                    "out_sample_max_drawdown_pct": out_metrics.max_drawdown_pct,
                    "out_sample_total_profit_pct": out_metrics.total_profit_pct,
                    "params_file": str(fold_params_file),
                }
            )

    write_summary_csv(rows, summary_file)
    if not config.no_plot:
        plot_fold_stability(rows, plot_file)
    return summary_file


def parse_args(argv: list[str] | None = None) -> WalkForwardConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", required=True, help="Freqtrade strategy class name")
    parser.add_argument("--start", type=parse_date, required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", type=parse_date, required=True, help="End date, YYYY-MM-DD")
    parser.add_argument(
        "--in-sample",
        type=parse_duration_days,
        required=True,
        help="In-sample tuning window in days, e.g. 90d",
    )
    parser.add_argument(
        "--out-sample",
        type=parse_duration_days,
        required=True,
        help="Out-of-sample validation window in days, e.g. 30d",
    )
    parser.add_argument(
        "--step",
        type=parse_duration_days,
        required=True,
        help="Days to slide between folds, e.g. 30d",
    )
    parser.add_argument("--loss", default="SharpeHyperOptLoss", help="Hyperopt loss function")
    parser.add_argument("--epochs", type=int, default=100, help="Hyperopt epochs per fold")
    parser.add_argument("--spaces", nargs="+", default=["buy"], help="Hyperopt spaces to tune")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("user_data/config.json"),
        help="Freqtrade config path",
    )
    parser.add_argument(
        "--strategy-path",
        type=Path,
        default=None,
        help="Optional Freqtrade strategy directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("user_data/walk_forward_results"),
        help="Directory for CSV, plot, logs, backtest exports, and fold parameter files",
    )
    parser.add_argument("--freqtrade-bin", default="freqtrade", help="Freqtrade executable")
    parser.add_argument("--random-state", type=int, default=42, help="Hyperopt random seed")
    parser.add_argument("-j", "--jobs", type=int, default=None, help="Freqtrade worker count")
    parser.add_argument("--no-plot", action="store_true", help="Skip PNG stability plot")
    args = parser.parse_args(argv)

    if args.epochs <= 0:
        parser.error("--epochs must be greater than zero")
    if args.jobs is not None and args.jobs <= 0:
        parser.error("--jobs must be greater than zero")

    return WalkForwardConfig(
        strategy=args.strategy,
        start=args.start,
        end=args.end,
        in_sample_days=args.in_sample,
        out_sample_days=args.out_sample,
        step_days=args.step,
        loss=args.loss,
        epochs=args.epochs,
        config_path=args.config,
        output_dir=args.output_dir,
        spaces=tuple(args.spaces),
        freqtrade_bin=args.freqtrade_bin,
        strategy_path=args.strategy_path,
        random_state=args.random_state,
        jobs=args.jobs,
        no_plot=args.no_plot,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        summary_file = run_walk_forward(parse_args(argv))
    except (ValueError, WalkForwardError) as exc:
        print(f"walk_forward: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote summary CSV: {summary_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
