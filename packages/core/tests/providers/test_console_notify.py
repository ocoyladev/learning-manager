import json

from learning_manager.providers.notify.console import ConsoleProvider


def test_send_writes_structured_record_and_returns_ref(tmp_path) -> None:
    ref = ConsoleProvider(tmp_path).send(user_ref="u1", message="Which?", options=["A", "B"])
    record = json.loads((tmp_path / f"{ref}.json").read_text())
    assert record["user_ref"] == "u1" and len(record["options"]) == 2


def test_poll_replies_reads_scripted_answers(tmp_path) -> None:
    (tmp_path / "replies.jsonl").write_text('{"user_ref":"u1","text":"A"}\n')
    provider = ConsoleProvider(tmp_path)
    assert provider.poll_replies()[0].text == "A"
    assert provider.poll_replies() == []
