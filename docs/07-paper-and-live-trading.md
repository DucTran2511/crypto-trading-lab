# 7. Paper & live trading

Freqtrade has a single command for both: `freqtrade trade`. The only difference between paper (dry-run) and live (real money) is one boolean in the config.

## 7.1 Dry-run (paper) — start here

```bash
freqtrade trade -c user_data/config.json --strategy EMACrossover
```

With `"dry_run": true` (the default in this repo's config), Freqtrade:
- Connects to OKX's public market-data feed.
- Tracks live candles and runs your strategy in real time.
- Simulates fills against the `dry_run_wallet` (default $500) at the next bar's open, applying the same fee + slippage model as the backtest.
- Persists trade state to `user_data/tradesv3.dryrun.sqlite` so the bot can be restarted without losing position.

Stop with `Ctrl+C`. Inspect what happened:
```bash
freqtrade show-trades --db-url sqlite:///user_data/tradesv3.dryrun.sqlite
```

Or summarise profit:
```bash
freqtrade profit --db-url sqlite:///user_data/tradesv3.dryrun.sqlite
```

## 7.2 Reset the dry-run wallet

To start fresh:
```bash
rm user_data/tradesv3.dryrun.sqlite
```
That wipes simulated trade history; the next `freqtrade trade` invocation starts again from `dry_run_wallet`.

## 7.3 Web UI (optional but useful)

The web UI gives you live equity curves, per-trade detail, manual force-buy/sell buttons, and a chart with strategy signals.

1. Edit `user_data/config.json`:
   ```json
   "api_server": {
     "enabled": true,
     "listen_ip_address": "127.0.0.1",
     "listen_port": 8080,
     "verbosity": "error",
     "enable_openapi": false,
     "jwt_secret_key": "<paste a long random string>",
     "ws_token": "<paste another long random string>",
     "CORS_origins": [],
     "username": "freqtrader",
     "password": "<pick a password>"
   }
   ```
2. Install the UI assets (once):
   ```bash
   freqtrade install-ui
   ```
3. Start the bot:
   ```bash
   freqtrade trade -c user_data/config.json --strategy EMACrossover
   ```
4. Open <http://127.0.0.1:8080> and log in with the username/password from step 1.

**Security:** never expose `127.0.0.1` to the public internet. If you must access it remotely, SSH-tunnel: `ssh -L 8080:127.0.0.1:8080 user@your-vm`.

## 7.4 Telegram alerts (optional)

Useful so you know when trades happen without watching the screen.

1. Talk to [@BotFather](https://t.me/BotFather), `/newbot`, follow prompts, copy the token.
2. Send your new bot any message, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`.
3. In `user_data/config.json`:
   ```json
   "telegram": {
     "enabled": true,
     "token": "<bot token>",
     "chat_id": "<your chat id>"
   }
   ```
4. Restart `freqtrade trade`. Send `/start` and then `/help` to the bot to see all commands (e.g. `/status`, `/profit`, `/forcesell`).

## 7.5 Going live — what changes

To trade real money on real candles with real orders:

1. Open an account on the exchange you want to trade (Binance, OKX, Bybit, Kraken, …). Enable 2FA.
2. Generate an **API key** with **spot trading** scope. **Do not** enable withdrawal scope. If the exchange supports IP allow-listing, use it.
3. Paste the credentials into `user_data/config.json`:
   ```json
   "exchange": {
     "name": "binance",          // or okx, bybit, etc.
     "key": "<api key>",
     "secret": "<api secret>",
     ...
   }
   ```
4. Flip `"dry_run": false`.
5. (Strongly recommended) reduce `dry_run_wallet` mentally — it becomes irrelevant — and make sure `stake_amount`, `max_open_trades`, and `stoploss` are values you can actually tolerate losing on every trade.
6. Run with a **separate** database file so paper history doesn't mix in:
   ```json
   "db_url": "sqlite:///user_data/tradesv3.live.sqlite"
   ```
7. `freqtrade trade -c user_data/config.json --strategy EMACrossover`.

## 7.6 Pre-live checklist (do not skip)

Read every line and tick mentally before flipping `dry_run` to `false`.

1. [ ] Strategy has been backtested on **at least 6 months** of recent data.
2. [ ] Strategy has survived a walk-forward test on **at least 2 non-overlapping** holdouts (see [Hyperopt](06-hyperopt.md) §6.4).
3. [ ] Strategy has been paper-traded with `freqtrade trade --dry-run` for **at least 4 weeks**.
4. [ ] Paper-trading stats (profit, win %, drawdown) match the backtest within ~30%. Big divergence = your fee/slippage model is wrong; do not go live.
5. [ ] You can articulate, in one sentence, *why* you think this strategy has edge. ("It backtested well" is not an answer.)
6. [ ] `stake_amount` × `max_open_trades` ≤ 10% of the equity you can afford to lose in this account.
7. [ ] `stoploss` is set. `stoploss_on_exchange` is `false` for spot (Freqtrade closes positions; relying on exchange stops introduces race conditions on most CEXs).
8. [ ] You have a kill switch: a way to stop the bot and flatten all positions in < 60 seconds (`/forcesell all` via Telegram, or `freqtrade stop` then manual close on the exchange).
9. [ ] API key has **only** spot trading scope, **no** withdrawal scope.
10. [ ] You're starting with the smallest position size the exchange allows — typically $10–$50 per trade. Size up only after weeks of live data.

If any box is unticked, you are gambling, not trading.

## 7.7 What to expect when you go live

- **Slippage and fills will be worse than backtest.** Your orders move the market on smaller pairs; you'll occasionally miss fills entirely.
- **Latency matters.** A 5-minute timeframe is tolerant; 1-minute or below is not. On 5m, you have ~30s of margin.
- **Your edge will shrink.** Other people backtested the same idea. The 32% baseline winrate from `EMACrossover` is honest precisely because it shows the kind of "edge" naive approaches have on majors.
- **You will second-guess the bot.** Don't. Manual overrides destroy more accounts than bad strategies. Either trust the system or improve it on paper.

## 7.8 Run as a long-lived service (Linux)

For a serious paper or live run, run Freqtrade under `systemd` or `tmux`/`screen`, not from a terminal that closes when you log out.

A minimal systemd unit (`/etc/systemd/system/freqtrade.service`):

```ini
[Unit]
Description=Freqtrade bot
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repos/crypto-trading-lab
ExecStart=/home/ubuntu/repos/crypto-trading-lab/.venv/bin/freqtrade trade -c user_data/config.json --strategy EMACrossover
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now freqtrade
sudo journalctl -u freqtrade -f
```

Or Docker (replace the `backtesting` subcommand with `trade`):
```bash
docker run -d --restart=unless-stopped --name freqtrade \
  -v "$PWD/user_data:/freqtrade/user_data" \
  -p 127.0.0.1:8080:8080 \
  freqtradeorg/freqtrade:stable \
  trade -c user_data/config.json --strategy EMACrossover
```

---

Next: [Risk & position sizing](08-risk-and-position-sizing.md).
