"""Official Meta WhatsApp Cloud API notification provider.

This provider never uses the WhatsApp web client or an unofficial library.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from learning_manager.contracts import Reply


class ConfigError(ValueError):
    """Raised when a live notification provider lacks required credentials."""


class WhatsAppProvider:
    def __init__(self, phone_number_id: str | None, access_token: str | None) -> None:
        if not phone_number_id:
            raise ConfigError("WHATSAPP_PHONE_NUMBER_ID is required")
        if not access_token:
            raise ConfigError("WHATSAPP_ACCESS_TOKEN is required")
        version = os.getenv("WHATSAPP_API_VERSION", "v20.0")
        self.url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
        self.access_token = access_token

    def send(self, *, user_ref: str, message: str, options: list[str] | None = None) -> str:
        if os.getenv("NOTIFY_LIVE", "false").lower() != "true":
            return ""
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": user_ref,
        }
        if not options:
            payload.update({"type": "text", "text": {"body": message}})
        else:
            payload.update(
                {"type": "interactive", "interactive": self._interactive(message, options)}
            )
        response = httpx.post(
            self.url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return str(response.json().get("messages", [{}])[0].get("id", ""))

    @staticmethod
    def _interactive(message: str, options: list[str]) -> dict[str, Any]:
        if len(options) <= 3:
            return {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": option, "title": option}}
                        for option in options
                    ]
                },
            }
        return {
            "type": "list",
            "body": {"text": message},
            "action": {
                "button": "Choose",
                "sections": [
                    {
                        "title": "Options",
                        "rows": [{"id": option, "title": option} for option in options],
                    }
                ],
            },
        }

    def poll_replies(self) -> list[Reply]:
        """Inbound messages are handled by the verified webhook in Phase 12.3."""
        return []
