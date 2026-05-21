<!--
Updated: 2026-05-03 (sessie 21)
Gebruik: plak dit als opening prompt bij een nieuwe CLI agent sessie op SPI
-->

# SPI Live-Session Prompt

Kopieer en plak dit aan het begin van een nieuwe agent CLI sessie op SPI.

---

## Prompt tekst

```
Je bent een agent op SPI (192.168.42.21). Bootstrap via:

  curl http://localhost:65000/info/v2

Dit geeft je de volledige capability map: tools, endpoints, auth, resources.

Samenvatting actuele endpoints (sessie 21, 2026-05-03):
- POST /v2/chat/completions       — LLM chat (OpenAI-compat), model "auto" of GET /v2/models
- POST /v2/voice/synthesize       — TTS Nederlands (Parkiet)
- POST /v2/voice/transcribe       — STT Whisper large-v3 NL+EN
- POST /v2/image/generate         — ComfyUI image gen
- POST /v2/vision/analyze         — Lokaal vision (MiniCPM-o Q4, ~22s, geen cloud nodig)
  Body: {"image": "<base64>", "prompt": "...", "agent_id": "jouw-id"}
  Of:   {"image_url": "http://...", "prompt": "...", "agent_id": "jouw-id"}
- GET/PUT/DELETE /v2/files/{root}/{path} — File API (roots: sophie, susan, shared)
- POST /v2/jobs                   — Async job queue (llm|tts|stt|image)
- GET /registry/pages             — Alle services met web UI
- POST /registry/register         — Registreer service + optioneel web_url

Auth: loopback (127.x, 192.168.42.x) = geen auth nodig.
Extern = Authorization: Bearer <token>.

Altijd agent_id meesturen in requests.
Meer context: /opt/bootstrap/TOOLS.md, /opt/bootstrap/START.md
```

---

## Notes voor de gebruiker

- Plak dit vóór je eigenlijke taakbeschrijving
- De agent doet daarna een `curl /info/v2` voor de volledige up-to-date kaart
- Dit bestand bijwerken na elke sessie met nieuwe endpoints
