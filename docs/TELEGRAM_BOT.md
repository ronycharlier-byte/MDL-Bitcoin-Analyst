# Telegram bot

Telegram is a notification and research-control interface, not an execution channel.

## Setup

Configure `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` and a high-entropy `TELEGRAM_WEBHOOK_SECRET` in the Worker secret store. An administrator calls `POST /telegram/setup-webhook` with `WORKER_ADMIN_TOKEN`; the Worker registers the secret token with Telegram. D1 migration `0008_telegram_webhook_security.sql` is required before receiving updates.

Incoming `POST /telegram/webhook` must have the correct `X-Telegram-Bot-Api-Secret-Token`, integer `update_id`, recent timestamp and allowed chat ID. `update_id` is inserted once; duplicates are acknowledged without repeating side effects.

## Commands

Read commands include `/help`, `/status`, `/summary`, `/quick`, `/deep`, `/alerts`, `/last`, strategy diagnostics and paper reports. `/quick_fresh`, `/deep_run`, `/rule`, `/mute` and mock-paper commands mutate queues or D1 and remain owner-only. Historical `/trade_approve` cannot approve live execution; the underlying route is blocked and paper journal semantics are explicit.

Message delivery splits long text below Telegram limits, includes part numbers, uses bounded timeouts, retries a single 429 according to `retry_after`, and falls back to plain text when rich formatting is rejected.

## Operational policy

- Critical alerts may be immediate; lower severity should be grouped to prevent noise.
- Deduplicate by event/update ID and use cooldowns for repeated threshold alerts.
- Never include API tokens, webhook URLs, client keys or raw personal identifiers in messages/logs.
- A Telegram button is never human approval for a financial transaction.
- Degraded Telegram delivery must not block archive creation or model validation.

## Test matrix

Validate correct/wrong/missing secret, foreign chat ID, duplicate/stale/malformed update, long messages, Markdown-like text, Telegram 429, network timeout, D1 unavailable and live-approval attempts. Tests must use fake tokens and mocked HTTP.
