# 10. Troubleshooting

Errors indexed by message. Search this page (`Ctrl/Cmd-F`) for the first distinctive line of your traceback.

## 10.1 Install failures

### `fatal error: ta-lib/ta_defs.h: No such file or directory`
The `TA-Lib` Python wheel is trying to compile against the **C library**, which is not installed. Install it per [Setup](01-setup.md) §1.2 (Homebrew on macOS, build-from-source on Ubuntu, prebuilt wheel on Windows). Then re-run `pip install -r requirements-dev.txt`.

### `fatal error: Python.h: No such file or directory`
You have Python but not the development headers. On Ubuntu/Debian:
```bash
sudo apt install python3.11-dev   # or python3.12-dev, etc.
```
On Fedora/RHEL: `sudo dnf install python3-devel`. On macOS: install Python from python.org or Homebrew (headers come bundled).

### `error: Microsoft Visual C++ 14.0 or greater is required` (Windows)
Install [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/), choose "Desktop development with C++", and reboot.

### `ERROR: Could not find a version that satisfies the requirement freqtrade==2025.6`
Your Python is too new or too old. Freqtrade 2025.6 supports Python 3.10–3.13. Check with `python --version` and recreate the venv with a supported interpreter.

### Pip resolver hangs forever
The `--use-deprecated=legacy-resolver` flag may help, but the better fix is to upgrade pip:
```bash
pip install --upgrade pip
```
If you previously installed a Freqtrade version other than 2025.6 in the same venv, recreate the venv from scratch.

---

## 10.2 Data download failures

### `HTTP 451: Unavailable For Legal Reasons`
You're trying to reach `api.binance.com` from a region Binance geo-blocks (US, etc.). Either:
- Use the bundled OKX config (default), or
- Use `scripts/download_binance_vision.py` to pull from the public archive (works from any IP, see [Data](04-data.md) §4.3).

### `HTTP 404` from `data.binance.vision`
The pair × timeframe × month combination doesn't exist. Either:
- The month is in the future or too recent (the archive lags by ~1 day).
- The pair didn't exist at that date.
- You misspelled the pair or timeframe.

The script logs the URL it tried — open it in a browser to confirm.

### `freqtrade download-data` finishes but the date range is shorter than I asked for
The exchange has gaps for those candles. Common causes:
- Pair didn't exist yet at that date.
- Exchange outage during that window.
- Rate-limit caused the downloader to stop early (re-run; it resumes from where it left off).

Confirm by running `freqtrade list-data -c user_data/config.json` — it prints the actual covered range per pair.

### Feather file appears empty / `pyarrow` errors on read
Re-download. Most likely the previous run was interrupted mid-write.

---

## 10.3 Strategy / backtest failures

### `Could not find strategy file for EMACrossover`
Strategies are discovered from `user_data/strategies/`. Make sure the class name and the file's class name match, and the file ends in `.py`.

### `Loaded 0 trades` even though the backtest ran
Most likely causes:
- Insufficient `startup_candle_count`. The bundled strategy needs 200 candles. If your `--timerange` is shorter than ~17 hours of 5m bars, the first bar with valid signals is past the end of the range.
- Indicator NaN at every bar. Check the entry conditions in the notebook with a sample dataframe.
- Filter conditions are all `False`. Print intermediate columns to verify.

### Hyperopt "best params" are obviously bad
You probably hit the caching bug — see [Hyperopt](06-hyperopt.md) §6.3 and [Strategy](03-strategy.md) §3.4. Any parameter that affects an indicator's *value* (not just a threshold) must be pre-computed via `.range`.

### `ValueError: cannot reindex from a duplicate axis` during backtest
You have duplicate timestamps in the data. Re-download. If it persists, the exchange returned a corrupt range; try a slightly different `--timerange`.

### Backtest results are wildly different from a previous run with the same config
- Check `fee` and slippage settings in the config — did you change them?
- Did you re-download candles? Recent candles get revised by some exchanges (Binance back-fills).
- Are you on a different timezone? Freqtrade uses UTC internally; if your `--timerange` includes local-time anchors that crossed DST, you'll see drift.

---

## 10.4 Paper / live trading failures

### Web UI shows a blank page
Run `freqtrade install-ui` once. It downloads and unpacks the UI assets into `user_data/`.

### Bot opens trades on paper but never exits
You may have disabled `use_exit_signal` and have no `roi` or `stoploss` defined either. At least one exit mechanism must be active.

### Telegram bot is silent
- `enabled` is `true`?
- Token + chat_id correct?
- Did you `/start` the bot from your account once? Telegram won't let it message you otherwise.
- Check `journalctl -u freqtrade` (or wherever you're piping logs) for Telegram error responses.

### Live orders are rejected by the exchange
Common causes:
- `min_notional` not met (your `stake_amount` is below the exchange minimum). Increase it.
- API key missing trading scope. Re-issue with **spot trading** enabled, **no** withdrawal.
- IP allow-list mismatch — if you set one, your VPS IP must be in it.

---

## 10.5 Lint / test failures

### `pytest` cannot find tests
Run from the repo root, with the venv activated. The `pyproject.toml` config tells pytest to look in `tests/`. If you moved files, update `pyproject.toml`.

### `ruff check .` reports errors you didn't introduce
Pull main and rebase, or ensure your dev deps match `requirements-dev.txt` exactly:
```bash
pip install -r requirements-dev.txt --upgrade
```

### Tests pass locally but fail in CI (when CI exists)
- CI typically uses a clean cache. If you committed a `__pycache__` or stale `.pytest_cache`, that can break test discovery — `git clean -fdx` and re-run locally.
- Time-sensitive tests: be careful of `datetime.now()` in test code. Mock instead.

---

## 10.6 General recovery moves

When in doubt, try in this order:

1. **Re-activate the venv.** `which freqtrade` should print a path inside `.venv/bin/`.
2. **Reinstall deps.** `pip install -r requirements-dev.txt --upgrade`.
3. **Wipe stale state.** `rm -rf user_data/backtest_results user_data/hyperopt_results user_data/tradesv3.dryrun.sqlite`. Candles can stay.
4. **Recreate the venv.** `rm -rf .venv && python -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements-dev.txt`.
5. **Try Docker.** If the native install is fighting you, [Setup](01-setup.md) §1.6 sidesteps the whole TA-Lib + Python toolchain problem.

If a problem isn't on this page, [open an issue](https://github.com/DucTran2511/crypto-trading-lab/issues) with:
- Full traceback or error message.
- `freqtrade --version`, `python --version`, OS + version.
- The exact command you ran.
