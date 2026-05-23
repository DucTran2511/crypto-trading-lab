# Strategy Development Rules

## Creating a New Strategy

1. Inherit from `freqtrade.strategy.IStrategy`
2. One strategy per file: `user_data/strategies/<StrategyName>.py`
3. Class name must match filename (e.g., `EMACrossover` in `EMACrossover.py`)

## Required Methods

- `populate_indicators(self, dataframe, metadata)` — compute all indicators
- `populate_entry_trend(self, dataframe, metadata)` — set `enter_long` column
- `populate_exit_trend(self, dataframe, metadata)` — set `exit_long` column

## Required Properties

- `minimal_roi` — ROI ladder (dict)
- `stoploss` — hard stop as negative float (e.g., `-0.03`)
- `timeframe` — candle size string (e.g., `"5m"`)

## Hyperopt-Tunable Parameters

- Use `IntParameter` for integers (EMA periods, lookback windows)
- Use `DecimalParameter` for floats (volume factors, multipliers)
- Always set `default`, `space`, and `optimize` arguments
- Reference via `.value` inside `populate_*` methods

## Testing a Strategy

```bash
freqtrade backtesting -c user_data/config.json \
    --strategy <StrategyName> \
    --timerange=20250101-20250501
```

## Style

- Use descriptive variable names for indicators (not `df['a']`)
- Add a module-level docstring explaining the strategy logic
- Keep helper functions inside the class as private methods
