# Fase 12 — Canal WhatsApp (opcional, con tope)

**Pista:** C · **Depende de:** F11 · **Tope duro: 60 min de configuración humana + 60 min de código**

> ⚠️ **Es el primer elemento de la línea de corte.** Si el tope se agota, se abandona y
> Telegram lleva la demo. Está en el plan porque el autor lo pidió expresamente, con el
> riesgo de reproducibilidad documentado.
>
> **Solo API oficial de Meta Cloud.** Prohibido `whatsapp-web.js` y cualquier librería que use
> el cliente web: viola la regla R3 de las bases, exactamente por el mismo motivo por el que la
> especificación §17 rechazó el MCP no oficial de NotebookLM.

---

## Tarea 12.1 — Configuración (TAREA HUMANA, no de agente)

**Tope: 60 minutos. Se ejecuta en paralelo al trabajo de los agentes.**

- [ ] Crear app en Meta for Developers, añadir el producto WhatsApp
- [ ] Obtener número de prueba, `PHONE_NUMBER_ID` y token temporal
- [ ] Registrar el número de destino en la lista de destinatarios permitidos
- [ ] Enviar un mensaje de prueba con `curl` desde la propia consola de Meta
- [ ] Guardar `WHATSAPP_PHONE_NUMBER_ID` y `WHATSAPP_ACCESS_TOKEN` en `.env` (**nunca commitear**)

**Si a los 60 min esto no está funcionando: se aplica el corte de nivel 1 y se pasa a la F13.**

---

## Tarea 12.2 — WhatsAppProvider

**Ficheros:** `providers/notify/whatsapp.py`; Test `tests/providers/test_whatsapp.py` (`respx`)

> **El código se escribe y se testea con transporte simulado independientemente de si la
> Tarea 12.1 tuvo éxito.** Así el provider existe, está probado y documentado aunque no se
> haya podido verificar en vivo.

- [ ] **Paso 1: test que falla**

```python
def test_send_uses_the_official_cloud_api_endpoint(respx_mock) -> None:
    route = respx_mock.post(url__regex=r"https://graph\.facebook\.com/v\d+\.\d+/\d+/messages")\
        .respond(json={"messages": [{"id": "wamid.X"}]})
    ref = WhatsAppProvider("pid", "tok").send(user_ref="+34600000000", message="m")
    assert ref == "wamid.X"
    assert route.called


def test_options_are_sent_as_interactive_buttons(respx_mock) -> None:
    route = respx_mock.post(url__regex=r".*/messages").respond(json={"messages": [{"id": "x"}]})
    WhatsAppProvider("pid", "tok").send(user_ref="+34600000000", message="¿Cuál?",
                                        options=["ClusterIP", "NodePort"])
    body = json.loads(route.calls[0].request.content)
    assert body["type"] == "interactive"
    assert len(body["interactive"]["action"]["buttons"]) == 2


def test_more_than_three_options_falls_back_to_a_list_message(respx_mock) -> None:
    # La Cloud API limita a 3 botones. Con más, hay que usar list message.
    respx_mock.post(url__regex=r".*/messages").respond(json={"messages": [{"id": "x"}]})
    WhatsAppProvider("pid", "tok").send(user_ref="+34600000000", message="m",
                                        options=["A", "B", "C", "D"])
    body = json.loads(respx_mock.calls[0].request.content)
    assert body["interactive"]["type"] == "list"


def test_nothing_is_sent_when_notify_live_is_false(monkeypatch, respx_mock) -> None:
    monkeypatch.setenv("NOTIFY_LIVE", "false")
    WhatsAppProvider("pid", "tok").send(user_ref="+34600000000", message="m")
    assert len(respx_mock.calls) == 0


def test_missing_credentials_fail_fast_with_a_clear_message() -> None:
    with pytest.raises(ConfigError, match="WHATSAPP_PHONE_NUMBER_ID"):
        WhatsAppProvider(None, None)
```

- [x] **Paso 2–4:** implementar y verificar
- [x] **Paso 5: commit** → `feat(notify): add WhatsApp Cloud API provider`

---

## Tarea 12.3 — Recepción de respuestas

- [ ] Endpoint `POST /webhooks/whatsapp` con verificación de firma `X-Hub-Signature-256`
- [ ] `GET /webhooks/whatsapp` para el desafío de verificación de Meta
- [ ] Test: una firma inválida devuelve 403 y **no** procesa el mensaje
- [x] Documentar en `REPRODUCTION.md` que este canal requiere HTTPS público y por tanto **no es
      el camino reproducible**; el camino reproducible es Telegram o consola
- [ ] Commit → `feat(api): add verified WhatsApp webhook endpoint`

---

## ✅ Criterio de salida

- [ ] El provider existe, está testeado con transporte simulado y respeta `NOTIFY_LIVE`
- [ ] Si la Tarea 12.1 tuvo éxito: un envío real verificado y grabado para el vídeo
- [ ] Si no: `WHATSAPP_ENABLED=false` documentado, sin bloquear nada más
- [ ] `REPRODUCTION.md` deja claro qué canal debe usar un juez
