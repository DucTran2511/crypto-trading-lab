# 8. Risk & position sizing

The single biggest difference between traders who survive and traders who blow up is **not** strategy selection — it is position sizing. If you only ever read one page in this repo, make it this one.

## 8.1 The one rule

> Never risk more than ~1% of account equity on a single trade.

Everything below is just the arithmetic that enforces it.

## 8.2 Fixed-risk sizing

Risk a fixed dollar amount on every trade, regardless of how big or small the stop distance is.

```
units = dollar_risk / |entry_price - stop_price|
```

Example: $5 of risk on a $500 account (1%), buying BTC at $65,000 with a stop at $63,050:

```
stop distance = |65000 - 63050| = $1,950 per BTC
units         = $5 / $1,950     = 0.002564 BTC
notional      = 0.002564 × 65000 = $166.67
```

If BTC hits the stop, you lose ~$5. If BTC rallies to $68,000, you make $7.69 (0.002564 × $3,000). The position size automatically scales to whatever the stop distance happens to be — tight stops let you size up, wide stops force you to size down.

Run it from the CLI:
```bash
python -m risk.position_size \
  --equity 500 --entry 65000 --stop 63050 --risk-pct 0.01
```

Or by dollar amount instead of percentage:
```bash
python -m risk.position_size \
  --equity 500 --entry 65000 --stop 63050 --dollar-risk 5
```

Output:
```
Units:                  0.002564
Notional value:         $166.67
Dollar risk at stop:    $5.00
Risk as % of equity:    1.000%
Stop distance from entry: 3.000%
```

## 8.3 Fixed-fraction sizing

Same as fixed-risk, but `dollar_risk` is computed from `equity × risk_fraction` *on each trade*, so the position scales as the account grows or shrinks.

```python
from risk.position_size import size_for_fixed_fraction

plan = size_for_fixed_fraction(
    entry_price=65_000,
    stop_price=63_050,
    equity=500,
    risk_fraction=0.01,
)
print(plan.pretty())
```

This is what most retail systems should default to. After a 10% gain, you're risking 10% more in dollars; after a 10% loss, you're risking 10% less. The account compounds and decompresses gracefully.

## 8.4 What the API gives you

`risk/position_size.py` exposes:

| Function | Args | Returns |
|---|---|---|
| `size_for_fixed_risk(entry_price, stop_price, dollar_risk, equity)` | absolute risk in $ | `PositionPlan` |
| `size_for_fixed_fraction(entry_price, stop_price, equity, risk_fraction)` | risk as fraction of equity (0 < f < 1) | `PositionPlan` |

`PositionPlan` is a frozen dataclass with:
- `units` — quantity to buy (in base currency, e.g. BTC).
- `notional` — `units × entry_price` (in quote currency, USDT).
- `dollar_risk` — what you'll lose if the stop fills exactly.
- `risk_pct_of_equity` — sanity-check against the 1% rule.
- `stop_distance_pct` — how far the stop is in %.

Both helpers raise `ValueError` for nonsense inputs (zero stop distance, non-positive risk, equity ≤ 0). The tests in `tests/test_position_size.py` enumerate the validation cases.

## 8.5 CLI reference

```
python -m risk.position_size [options]

required:
  --equity FLOAT        Total account equity in quote currency.
  --entry FLOAT         Entry price.
  --stop FLOAT          Stop-loss price.

exactly one of:
  --risk-pct FLOAT      Fraction of equity to risk per trade, e.g. 0.01 = 1%.
  --dollar-risk FLOAT   Absolute amount to risk, in quote currency.

options:
  -h, --help            Show this help message and exit.
```

## 8.6 Risk-of-ruin (the scary table)

A "1% per trade" rule is not arbitrary. Below is the rough probability of an N% drawdown given a winning strategy with win rate `p` and 1:1 R:R, sized at 1% per trade. Use it to calibrate your tolerance.

| Win rate | P(20% drawdown) | P(50% drawdown) | P(ruin: 100% drawdown) |
|---:|---:|---:|---:|
| 45% | ~95% | ~80% | very high — don't trade |
| 50% | ~50% | ~10% | low (with discipline) |
| 55% | ~10% | < 1% | negligible |
| 60% | < 1% | ~0 | negligible |

You'll notice the numbers improve *dramatically* with even small edge improvements. The way to survive is: small edge × small risk × many trades.

## 8.7 How this connects to Freqtrade

Freqtrade does **not** use `risk/position_size.py` automatically — the bot sizes positions via `stake_amount` (fixed) or `unlimited` (split available balance across `max_open_trades`). The CLI in this repo is for two things:

1. **Manual sanity check** before discretionary trades.
2. **A reference implementation** if you write a custom `custom_stake_amount()` in your strategy (Freqtrade calls it before placing each order; you can return whatever stake makes sense given current equity and the strategy's signal).

Example custom stake (sketched, not in repo):
```python
from risk.position_size import size_for_fixed_fraction

def custom_stake_amount(self, pair, current_time, current_rate, proposed_stake,
                        min_stake, max_stake, leverage, entry_tag, side, **kwargs):
    equity = self.wallets.get_total(self.config["stake_currency"])
    stop_price = current_rate * (1 + float(self.stoploss))
    plan = size_for_fixed_fraction(
        entry_price=current_rate,
        stop_price=stop_price,
        equity=equity,
        risk_fraction=0.01,
    )
    return min(max(plan.notional, min_stake or 0), max_stake)
```

Drop that into a strategy if you want true 1%-of-equity sizing on every entry.

## 8.8 Stop placement, briefly

A 1% rule is meaningless without a stop. Three sensible places:

- **Volatility-based** (ATR multiple): stop = entry − k × ATR(14). `k` between 1.5 and 3 for crypto majors.
- **Structure-based**: stop = below the most recent swing low (long) / above the most recent swing high (short).
- **Time-based**: exit after N candles regardless. Cheap and surprisingly effective when combined with one of the above.

The bundled `EMACrossover` uses a flat -3% stop, which is a *price-percentage* stop. It's the worst of the three on principle (ignores volatility and structure) but the simplest to backtest. A real strategy should usually do better.

---

Next: [Research notebook](09-research-notebook.md).
