import json

from learning_manager.providers.notify.telegram import TelegramProvider


def test_send_posts_inline_keyboard(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "true")
    route = respx_mock.post(url__regex=r".*/sendMessage").respond(
        json={"ok": True, "result": {"message_id": 42}}
    )
    ref = TelegramProvider("tok", "chat").send(
        user_ref="chat", message="Which?", options=["A", "B"]
    )
    body = json.loads(route.calls[0].request.content)
    assert body["reply_markup"]["inline_keyboard"] and ref == "42"


def test_poll_maps_callback_queries(respx_mock) -> None:
    respx_mock.get(url__regex=r".*/getUpdates").respond(
        json={
            "ok": True,
            "result": [
                {
                    "update_id": 5,
                    "callback_query": {"data": "A", "message": {"chat": {"id": "chat"}}},
                }
            ],
        }
    )
    assert TelegramProvider("tok", "chat").poll_replies()[0].text == "A"


def test_offset_advances(respx_mock) -> None:
    respx_mock.get(url__regex=r".*/getUpdates").respond(json={"ok": True, "result": []})
    provider = TelegramProvider("tok", "chat")
    provider.poll_replies()
    provider.poll_replies()
    assert "timeout=0" in str(respx_mock.calls[1].request.url)


def test_live_guard(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "false")
    assert TelegramProvider("tok", "chat").send(user_ref="chat", message="m") == ""
    assert not respx_mock.calls
