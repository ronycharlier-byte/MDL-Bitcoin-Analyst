# Telegram ops alerts

The Worker supports native Telegram alerts, client summaries and interactive commands.

## Create the Telegram bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Copy the bot token.
4. Send any message to the new bot from the target chat.
5. Get the chat id:

```powershell
Invoke-RestMethod -Uri "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates" |
  ConvertTo-Json -Depth 10
```

Use the `message.chat.id` value.

## Configure Cloudflare secrets

Set the same secrets on both Worker services.

```powershell
npx wrangler login

"<TELEGRAM_BOT_TOKEN>" | npx wrangler secret put TELEGRAM_BOT_TOKEN
"<TELEGRAM_CHAT_ID>" | npx wrangler secret put TELEGRAM_CHAT_ID

"<TELEGRAM_BOT_TOKEN>" | npx wrangler secret put TELEGRAM_BOT_TOKEN --name quant-btc-model-deep
"<TELEGRAM_CHAT_ID>" | npx wrangler secret put TELEGRAM_CHAT_ID --name quant-btc-model-deep
```

## Deploy

```powershell
npm run deploy
npx wrangler deploy --name quant-btc-model-deep
```

## Test

```powershell
Invoke-RestMethod -Uri "https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev/ops/test-alert"
Invoke-RestMethod -Uri "https://quant-btc-model-deep.mdl-bitcoin-analyst.workers.dev/ops/test-alert"
```

Expected result:

```json
{
  "status": "sent",
  "channels": {
    "telegram": "configured"
  }
}
```

## Runtime behavior

- `/ops/status` reports whether Telegram is configured.
- `/ops/monitor` sends Telegram direct alerts only for `CRITICAL` by default.
- `WARNING` events are grouped in an hourly digest and the daily summary.
- `/alerts` remains the manual command for detailed model warnings.
- Alert cooldown is controlled by `OPS_MONITOR_ALERT_COOLDOWN_SECONDS`.
- Direct alert level is controlled by `TELEGRAM_DIRECT_MIN_LEVEL` (`critical` by default).
- Warning digest cooldown is controlled by `TELEGRAM_WARNING_DIGEST_COOLDOWN_SECONDS`.
- Alert delivery is best-effort; `/ops/status` remains the source of truth.

## Useful commands

- `/summary`: short client view with bias, risk, strategy, reason and prudent action.
- `/status`: operational state.
- `/alerts`: detailed model alerts.
- `/quick`: latest quick run.
- `/deep`: latest deep run.
- `/deep_run`: queue a deep run.
- `/strategy_deep`: strategy score.
- `/paper_strategy`: paper trade only if gates pass.
- `/onboarding`: usage guide.
