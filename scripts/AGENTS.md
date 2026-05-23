# Scripts Development Rules

## Conventions

- Use `argparse` with clear `--help` descriptions for all CLI scripts
- Include a `if __name__ == "__main__":` guard
- Log progress to stderr, output data to stdout or file
- Handle network errors gracefully with retries where appropriate
- Add corresponding tests in `tests/test_<script_name>.py`

## Existing Scripts

- `download_binance_vision.py` — downloads OHLCV candle data from data.binance.vision
- `walk_forward.py` — runs in-sample hyperopt and out-of-sample backtest folds, then writes a CSV summary and stability plot
