# Reproduction Guide

## Test the Telegram notification channel

1. Create a bot with [BotFather](https://t.me/BotFather), copy its token, and start a chat
   with the bot. Set `TELEGRAM_BOT_TOKEN` to the token and set `TELEGRAM_CHAT_ID` to the
   numeric chat ID used for the demo.
2. Select Telegram and explicitly enable live notifications in the environment:

   ```bash
   NOTIFY_PROVIDER=telegram \
   TELEGRAM_BOT_TOKEN=your-token \
   TELEGRAM_CHAT_ID=your-chat-id \
   NOTIFY_LIVE=true \
   SCHEDULER_MODE=simulation \
   docker compose up -d
   ```

3. Send a message to the bot, then run the worker or the relevant simulation command. The
   worker uses Telegram long polling (`getUpdates`) and advances its update offset, so each
   reply is consumed once. Inline keyboard selections are returned as retrieval answers.

For a credential-free run, keep `NOTIFY_PROVIDER=console` and `NOTIFY_LIVE=false`. Outbound
messages are written as JSON files and scripted replies can be placed in
`notifications/replies.jsonl`.

Live sending is disabled unless `NOTIFY_LIVE=true`; enable it only after confirming the target
chat and the simulation mode.
