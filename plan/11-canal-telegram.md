# Fase 11 — Canal Telegram

**Pista:** C · **Depende de:** F0 · **Duración objetivo:** 2 h

**Entrega:** notificación proactiva con pregunta de recuperación y captura de la respuesta.

> **Telegram es el canal reproducible por el juez**: solo hace falta un token de BotFather y
> funciona con *long polling*, sin HTTPS público ni túneles. Por eso es el que lleva la demo.
>
> Regla R4 de las bases: **nada se envía de verdad sin `NOTIFY_LIVE=true` y confirmación humana.**

---

## Tarea 11.1 — ConsoleProvider

**Ficheros:** `providers/notify/console.py`; Test `tests/providers/test_console_notify.py`

- [ ] **Paso 1: test que falla**

```python
def test_send_writes_a_structured_record_and_returns_a_ref(tmp_path) -> None:
    p = ConsoleProvider(out_dir=tmp_path)
    ref = p.send(user_ref="u1", message="¿Qué tipo de Service es solo interno?",
                 options=["ClusterIP", "NodePort", "LoadBalancer"])
    record = json.loads((tmp_path / f"{ref}.json").read_text())
    assert record["user_ref"] == "u1" and len(record["options"]) == 3


def test_poll_replies_reads_scripted_answers_for_simulation(tmp_path) -> None:
    (tmp_path / "replies.jsonl").write_text('{"user_ref":"u1","text":"ClusterIP"}\n')
    assert ConsoleProvider(out_dir=tmp_path).poll_replies()[0].text == "ClusterIP"
```

- [ ] **Paso 2–4:** implementar y verificar. Es el provider por defecto: hace que
      `docker compose up` funcione sin ninguna credencial.
- [ ] **Paso 5: commit** → `feat(notify): add console notification provider`

---

## Tarea 11.2 — TelegramProvider

**Ficheros:** `providers/notify/telegram.py`; Test `tests/providers/test_telegram.py` (`respx`)

**Interfaces producidas:** `TelegramProvider(bot_token, chat_id)` — implementa `NotificationProvider`

- [ ] **Paso 1: test que falla**

```python
def test_send_posts_an_inline_keyboard(respx_mock) -> None:
    route = respx_mock.post(url__regex=r".*/sendMessage").respond(
        json={"ok": True, "result": {"message_id": 42}})
    ref = TelegramProvider("tok", "chat").send(user_ref="chat", message="¿Cuál?",
                                               options=["A", "B"])
    body = json.loads(route.calls[0].request.content)
    assert body["reply_markup"]["inline_keyboard"]
    assert ref == "42"


def test_poll_replies_maps_callback_queries_to_reply_objects(respx_mock) -> None:
    respx_mock.get(url__regex=r".*/getUpdates").respond(json=_updates_with_callback("A"))
    replies = TelegramProvider("tok", "chat").poll_replies()
    assert replies[0].text == "A"


def test_offset_advances_so_updates_are_not_reprocessed(respx_mock) -> None:
    p = TelegramProvider("tok", "chat")
    p.poll_replies(); p.poll_replies()
    assert "offset=" in str(respx_mock.calls[1].request.url)


def test_nothing_is_sent_when_notify_live_is_false(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "false")
    TelegramProvider("tok", "chat").send(user_ref="chat", message="m")
    assert len(respx_mock.calls) == 0        # regla R4
```

- [ ] **Paso 2–4:** implementar con long polling (`getUpdates` con `offset`), teclado inline,
      y el guardarraíl de `NOTIFY_LIVE`. Sin webhook: no requiere HTTPS público.
- [ ] **Paso 5: commit** → `feat(notify): add Telegram provider with long polling`

---

## Tarea 11.3 — Bucle proactivo end-to-end

**Ficheros:** `worker/tick.py` (extender); Test `tests/worker/test_proactive_loop.py`

Loop del §12 de la especificación:
`notificación → micro-pregunta → respuesta → evaluación → learner model → scheduler`

- [ ] **Paso 1: test que falla**

```python
def test_answering_a_retrieval_question_updates_the_learner_model_and_reschedules() -> None:
    before = repo.get("g1").concepts["services"]
    events = tick(today=TODAY, dry_run=False, notifier=scripted(["ClusterIP"]))
    after = repo.get("g1").concepts["services"]
    assert after.mastery > before.mastery
    assert after.next_review > before.next_review
    assert any(e.kind == "retrieval_question" for e in events)


def test_the_question_targets_the_recorded_misconception() -> None:
    events = tick(today=TODAY, dry_run=True)
    q = next(e for e in events if e.kind == "retrieval_question")
    assert "ClusterIP" in q.message      # la misconception concreta, no un recordatorio genérico
```

- [ ] **Paso 2–4:** implementar y verificar
- [ ] **Paso 5: commit** → `feat(worker): close the proactive retrieval loop`

---

## ✅ Criterio de salida

- [ ] `ConsoleProvider` es el defecto y funciona sin credenciales
- [ ] Telegram envía y recibe, verificado a mano una vez con un bot real
- [ ] Nada se envía con `NOTIFY_LIVE=false`
- [ ] Responder una pregunta proactiva mueve el learner model y reprograma el repaso
- [ ] Documenta en `REPRODUCTION.md` los 3 pasos para que un juez lo pruebe con su propio bot
