import json

import pytest

from learning_manager.providers.notify.whatsapp import ConfigError, WhatsAppProvider


def test_send_uses_the_official_cloud_api_endpoint(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "true")
    route = respx_mock.post(
        url__regex=r"https://graph\.facebook\.com/v\d+\.\d+/\d+/messages"
    ).respond(json={"messages": [{"id": "wamid.X"}]})
    ref = WhatsAppProvider("123", "tok").send(user_ref="+34600000000", message="m")
    assert ref == "wamid.X"
    assert route.called


def test_options_are_sent_as_interactive_buttons(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "true")
    route = respx_mock.post(url__regex=r".*/messages").respond(json={"messages": [{"id": "x"}]})
    WhatsAppProvider("pid", "tok").send(
        user_ref="+34600000000", message="¿Cuál?", options=["ClusterIP", "NodePort"]
    )
    body = json.loads(route.calls[0].request.content)
    assert body["type"] == "interactive"
    assert len(body["interactive"]["action"]["buttons"]) == 2


def test_more_than_three_options_falls_back_to_a_list_message(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "true")
    respx_mock.post(url__regex=r".*/messages").respond(json={"messages": [{"id": "x"}]})
    WhatsAppProvider("pid", "tok").send(
        user_ref="+34600000000", message="m", options=["A", "B", "C", "D"]
    )
    body = json.loads(respx_mock.calls[0].request.content)
    assert body["interactive"]["type"] == "list"


def test_nothing_is_sent_when_notify_live_is_false(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "false")
    assert WhatsAppProvider("pid", "tok").send(user_ref="+34600000000", message="m") == ""
    assert not respx_mock.calls


def test_missing_credentials_fail_fast_with_a_clear_message() -> None:
    with pytest.raises(ConfigError, match="WHATSAPP_PHONE_NUMBER_ID"):
        WhatsAppProvider(None, None)
