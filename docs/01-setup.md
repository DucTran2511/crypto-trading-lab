# 1. Setup

This guide takes you from a clean machine to a working `freqtrade --version` in roughly 10 minutes. If anything fails, jump to [Troubleshooting](10-troubleshooting.md) — the most common failure (a TA-Lib build error) is covered there.

## 1.1 Prerequisites

| Tool | Required version | Why |
|---|---|---|
| **Python** | 3.10, 3.11, 3.12, or 3.13 | Freqtrade 2025.6 supports all four. The pinned pyproject targets 3.11 as the lint floor. |
| **git** | any recent | Cloning the repo. |
| **C compiler + TA-Lib system library** | system package | The `TA-Lib` Python wheel links against the native TA-Lib C library. On most systems you need to install it once, separately from `pip install`. |
| **(optional) Docker** | 20+ | Skip all of the above and run the official Freqtrade image instead. See §1.6. |

Pick exactly one path:
- **Path A — native install** (recommended for development; you can edit code and re-run instantly). §1.2 → §1.5.
- **Path B — Docker** (recommended if §1.2 is painful on your OS). §1.6.

---

## 1.2 Install the TA-Lib C library

This is the step that trips up most people. `pip install TA-Lib` will *not* install the C library; it only installs Python bindings to it.

### macOS (Homebrew)
```bash
brew install ta-lib
```

### Ubuntu / Debian
The C library is **not** in the default `apt` repos. Build it from source once:
```bash
sudo apt update
sudo apt install -y build-essential wget
cd /tmp
wget https://github.com/ta-lib/ta-lib/releases/download/v0.4.0/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
```

### Fedora / RHEL
```bash
sudo dnf install -y ta-lib-devel
# or build from source as in the Ubuntu instructions above
```

### Windows
1. Install Python 3.11 or 3.12 from python.org (not the Microsoft Store version).
2. Install [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) → "Desktop development with C++".
3. Either install TA-Lib from the [official Windows installers](https://ta-lib.org/install/#windows) or use a pre-built wheel (e.g. from <https://github.com/cgohlke/talib-build/releases>) and `pip install` the matching `.whl` directly.

Verify TA-Lib is found by the linker:
```bash
# macOS / Linux
echo '#include <ta-lib/ta_defs.h>' | gcc -E - >/dev/null && echo "ta-lib OK"
```

---

## 1.3 Clone and create a virtualenv

```bash
git clone https://github.com/DucTran2511/crypto-trading-lab.git
cd crypto-trading-lab

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

---

## 1.4 Install Python dependencies

```bash
pip install -r requirements-dev.txt
```

This pulls in:
- `freqtrade==2025.6` and its transitive deps (`ccxt`, `SQLAlchemy`, `python-telegram-bot`, `numpy`, `TA-Lib<0.6`, …).
- `pandas==2.2.3`, `pyarrow==16.1.0`, `requests==2.32.3` — pinned because our own scripts import them directly.
- Dev tools: `pytest`, `pytest-cov`, `ruff`, `ipykernel`, `matplotlib`.

`pip install` of `TA-Lib` will compile a tiny C extension at this point. If it fails with `fatal error: ta-lib/ta_defs.h: No such file or directory`, you skipped §1.2 — go back and install the C library.

---

## 1.5 Verify the install

Three quick checks. If all three pass, you are done.

```bash
# 1) Freqtrade CLI is on PATH
freqtrade --version          # → e.g. 2025.6

# 2) Lint is clean and unit tests pass
ruff check .
pytest

# 3) Strategy loads + backtests against the bundled OKX 5m data
freqtrade backtesting -c user_data/config.json \
  --strategy EMACrossover \
  --timerange=20250401-20250501
```

The third command prints a per-pair P/L table at the end and exits 0. Expect the result to be slightly negative — see [Strategy](03-strategy.md) for why that is intentional.

You are now ready to read the [Quickstart](02-quickstart.md) and run your own backtests / hyperopts.

---

## 1.6 Path B — Docker

If §1.2 is too painful, skip the native install entirely:

```bash
# from the repo root
docker run --rm -it \
  -v "$PWD/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  backtesting -c user_data/config.json \
    --strategy EMACrossover \
    --timerange=20250401-20250501
```

The volume mount makes `user_data/` (including your strategy, config, and downloaded candles) visible inside the container. Every Freqtrade subcommand documented later in `docs/` works the same way — just replace `freqtrade <cmd>` with `docker run --rm -it -v "$PWD/user_data:/freqtrade/user_data" freqtradeorg/freqtrade:stable <cmd>`.

Tip: make a shell alias so you don't type the long form:
```bash
alias ft='docker run --rm -it -v "$PWD/user_data:/freqtrade/user_data" freqtradeorg/freqtrade:stable'
# then: ft backtesting -c user_data/config.json --strategy EMACrossover --timerange=20250401-20250501
```

For `freqtrade trade` (paper/live) and the web UI you'll want to also expose port 8080 and run it detached — see [Paper & live trading](07-paper-and-live-trading.md).

---

## 1.7 Editor setup (optional)

VS Code or PyCharm both work out of the box. A couple of suggestions:

- Select `.venv/bin/python` as the project interpreter.
- Enable `ruff` as the linter/formatter — it is already configured in `pyproject.toml`.
- Run `pytest` from the IDE's test panel; the config in `pyproject.toml` discovers the `tests/` folder automatically.

---

Next: [Quickstart](02-quickstart.md).
