"""Official Telegram Bot API notification provider using long polling."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import httpx

from learning_manager.contracts import Reply


class TelegramProvider:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self._offset: int | None = None

    def send(self, *, user_ref: str, message: str, options: list[str] | None = None) -> str:
        if os.getenv("NOTIFY_LIVE", "false").lower() != "true":
            return ""
        payload: dict[str, Any] = {"chat_id": user_ref, "text": message}
        if options:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": option, "callback_data": option}] for option in options
                ]
            }
        response = httpx.post(f"{self.base_url}/sendMessage", json=payload, timeout=30.0)
        response.raise_for_status()
        result = response.json().get("result", {})
        return str(result.get("message_id", ""))

    def poll_replies(self) -> list[Reply]:
        params: dict[str, Any] = {"timeout": 0}
        if self._offset is not None:
            params["offset"] = self._offset
        response = httpx.get(f"{self.base_url}/getUpdates", params=params, timeout=10.0)
        response.raise_for_status()
        updates = response.json().get("result", [])
        replies: list[Reply] = []
        for update in updates:
            self._offset = max(self._offset or 0, int(update["update_id"]) + 1)
            callback = update.get("callback_query")
            message = callback.get("message", {}) if callback else update.get("message", {})
            if str(message.get("chat", {}).get("id")) != self.chat_id:
                continue
            text = callback.get("data") if callback else message.get("text")
            if text is not None:
                replies.append(
                    Reply(
                        user_ref=self.chat_id,
                        text=str(text),
                        received_at=datetime.now(UTC),
                        message_ref=str(update["update_id"]),
                    )
                )
        return replies
