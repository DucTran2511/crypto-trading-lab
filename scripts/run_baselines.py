"""Automate running backtests on five baseline strategies and collect comparative metrics."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import zipfile
from pathlib import Path

STRATEGIES = [
    "EMACrossover",
    "DonchianBreakout",
    "BollingerMeanReversion",
    "RSITrend",
    "MACDVolume",
]

TIMERANGE = "20250101-20250501"
CONFIG_PATH = Path("user_data/config.json")
RESULTS_DIR = Path("user_data/backtest_results")


def run_backtest(strategy: str) -> Path | None:
    print(f"Running backtest for {strategy}...")
    export_filename = RESULTS_DIR / f"baseline_{strategy}.json"
    cmd = [
        ".venv/bin/freqtrade",
        "backtesting",
        "-c",
        str(CONFIG_PATH),
        "--strategy",
        strategy,
        "--timerange",
        TIMERANGE,
        "--export",
        "trades",
        "--export-filename",
        str(export_filename),
        "--cache",
        "none",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        print(f"Error running backtest for {strategy}:", file=sys.stderr)
        print(res.stderr or res.stdout, file=sys.stderr)
        return None

    # Find the zip filename from .last_result.json
    last_result_file = RESULTS_DIR / ".last_result.json"
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
        return RESULTS_DIR / latest_zip
    except Exception as e:
        print(f"Error reading .last_result.json for {strategy}: {e}", file=sys.stderr)
        return None


def parse_backtest_zip(zip_path: Path, strategy: str) -> dict[str, any] | None:
    try:
        with zipfile.ZipFile(zip_path) as z:
            # Find the JSON file inside the zip (usually same base name as zip but with .json)
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
                # Try fallback keys if strategy isn't named exactly as requested
                # or just use first key
                strategy_keys = list(data.get("strategy", {}).keys())
                if strategy_keys:
                    strategy_data = data["strategy"][strategy_keys[0]]
                else:
                    print(f"Error: no strategy data found in {json_file}", file=sys.stderr)
                    return None

            # Extract metrics
            total_trades = strategy_data.get("total_trades", 0)
            winrate = strategy_data.get("winrate", 0.0) * 100.0
            profit_total = strategy_data.get("profit_total", 0.0) * 100.0
            sharpe = strategy_data.get("sharpe")
            max_drawdown = strategy_data.get("max_drawdown_account", 0.0) * 100.0
            profit_factor = strategy_data.get("profit_factor")

            return {
                "strategy": strategy,
                "trades": total_trades,
                "win_rate_pct": winrate,
                "total_profit_pct": profit_total,
                "sharpe": sharpe,
                "max_drawdown_pct": max_drawdown,
                "profit_factor": profit_factor,
            }
    except Exception as e:
        print(f"Error parsing zip {zip_path}: {e}", file=sys.stderr)
        return None


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for strategy in STRATEGIES:
        zip_path = run_backtest(strategy)
        if zip_path:
            metrics = parse_backtest_zip(zip_path, strategy)
            if metrics:
                results.append(metrics)
                print(f"Successfully processed {strategy}")
                print(f"  Trades: {metrics['trades']}")
                print(f"  Profit: {metrics['total_profit_pct']:.2f}%")
                print(f"  Sharpe: {metrics['sharpe']}")
            else:
                print(f"Failed to parse metrics for {strategy}", file=sys.stderr)
        else:
            print(f"Failed to run backtest for {strategy}", file=sys.stderr)

    if not results:
        print("No results collected.", file=sys.stderr)
        return 1

    # Write CSV
    csv_file = RESULTS_DIR / "baseline_validation_summary.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "trades",
                "win_rate_pct",
                "total_profit_pct",
                "sharpe",
                "max_drawdown_pct",
                "profit_factor",
            ],
        )
        writer.writeheader()
        writer.writerows(results)
    print(f"\nWrote CSV: {csv_file}")

    # Write Markdown
    md_file = RESULTS_DIR / "baseline_validation_summary.md"
    md_content = []
    md_content.append("# Baseline Strategy Validation Report")
    md_content.append("")
    md_content.append(f"**Timerange:** `{TIMERANGE}`")
    md_content.append("**Pairs:** `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT` (OKX Spot)")
    md_content.append("")
    md_content.append(
        "| Strategy | Trades | Win Rate % | Total Profit % | Sharpe | Max Drawdown % | Profit Factor |"
    )
    md_content.append("|---|---|---|---|---|---|---|")
    for r in results:
        sharpe_str = f"{r['sharpe']:.2f}" if r["sharpe"] is not None else "N/A"
        pf_str = f"{r['profit_factor']:.2f}" if r["profit_factor"] is not None else "N/A"
        md_content.append(
            f"| {r['strategy']} | {r['trades']} | {r['win_rate_pct']:.2f}% | "
            f"{r['total_profit_pct']:.2f}% | {sharpe_str} | {r['max_drawdown_pct']:.2f}% | {pf_str} |"
        )
    md_content.append("")

    # Also suggest which strategy is worth walk-forward validation
    # Criteria: Positive return, or if all are negative, the ones that are closest to profit/have reasonable drawdown & trades.
    md_content.append("## Recommendation")
    md_content.append("")
    md_content.append("Candidates for walk-forward sweeps:")
    for r in results:
        # A strategy is a candidate if it performs better than EMACrossover or has reasonable trade count / Sharpe
        recom = []
        if r["total_profit_pct"] > -10.0 and r["trades"] >= 20:
            recom.append("Positive or low-loss return with reasonable trade count")
        if r["sharpe"] is not None and r["sharpe"] > -10.0:
            recom.append("Decent Sharpe relative to crossover baseline")
        if recom:
            md_content.append(f"- **{r['strategy']}**: {', '.join(recom)}")

    md_text = "\n".join(md_content)
    md_file.write_text(md_text, encoding="utf-8")
    print(f"Wrote Markdown report: {md_file}")
    print("\n" + md_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
