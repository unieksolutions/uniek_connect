<!--
ts: 2026-04-22T11:00:00Z | path: /opt/bootstrap/ECOSYSTEM.md
Bijgewerkt door: Claude Sonnet 4.6 — daidto toegevoegd, sessie 19
Interactief diagram (intern, SPI only): https://192.168.42.21:63443/ui/static/ecosystem-messaging.html
-->

# uNiek Solutions — Ecosysteem Architectuur

Overzicht van alle diensten, agents en hun onderlinge verbindingen.

---

## Volledig diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                              GEBRUIKERS & KANALEN                                    ║
║                                                                                      ║
║  WhatsApp    Email          Telegram      Webchat       Browser / App                ║
║  (Baileys    (IMAP poller   (bot API)     (widget       (OAuth2 / directe login)     ║
║   VPS)        VPS)                         SSE/WS)                                   ║
╚══════╤═══════════╤══════════════╤═════════════╤════════════════════════════════╤═════╝
       │           │              │             │                                │
╔══════▼═══════════▼══════════════▼═════════════▼════════╗                      │
║              uniek_channels  (unieksolutions.nl/channels)                      │
║                                                                                │
║  Normalisatie → parts[] model → MessageStore (SQLite)                          │
║                                                                                │
║  Outbound: email/send · whatsapp/send · (telegram) · (sms)                     │
║  Inbound:  /receive webhook → forward_url per kanaal/mailbox                   ║
║                                                                                │
║  Auth: Bearer token via uniek_iam (JWKS/EdDSA)                                 ║
╚══════════════════════════════╤═════════════════════════╝                      │
                               │ inbound forward                                │
               ┌───────────────┴────────────────┐                              │
               │                                │                              │
╔══════════════▼═══════════════╗    ╔════════════▼══════════════════════════════════╗  │
║         GMR                  ║    ║     daid.to — digital aid platform            ║  │
║   (accept.unieksolutions.nl/  ║    ║     Orchestrator (FastAPI, systemd)           ║  │
║    gmr → prod: /gmr)          ║    ║     api.daid.to                               ║  │
║                               ║    ║                                               ║  │
║  Routing cascade:             ║    ║  Provisioning · Mollie · IAM auth             ║  │
║  open sessie → rules          ║◀───║  Beheerpanel: /{username}/admin               ║  │
║    → LLM → escalatie          ║───▶║  SSO: Google · Microsoft · email              ║  │
║                               ║    ║                                               ║  │
║  Medewerkers CRUD             ║    ║  ┌─────────────────────────────────────────┐  ║  │
║  Admin UI · sessies log       ║    ║  │  agents1 VPS (77.42.71.48)              │  ║  │
║  ChannelsClient (outbound)    ║    ║  │                                         │  ║  │
╚══════════════════════════════╝    ║  │  Susan / Hermes / 0000dc5a / WA+TG      │  ║  │
                                    ║  │    org: uNiek Solutions (3cd5)           │  ║  │
                                    ║  │    admin: niek@uniek.solutions            │  ║  │
                                    ║  │                                         │  ║  │
                                    ║  │  Wijckmus / OpenClaw / 0000ce01 / WA   │  ║  │
                                    ║  │    org: Wij van Pijnacker Zuid (4ca0)   │  ║  │
                                    ║  │    admin: niek@pijnacker-zuid.nl         │  ║  │
                                    ║  │                                         │  ║  │
                                    ║  │  Nova / OpenClaw / 00003005 / WA        │  ║  │
                                    ║  │    org: start2.ai (d439)               │  ║  │
                                    ║  │    admins: niek@start2.ai               │  ║  │
                                    ║  │             rahul@start2.ai              │  ║  │
                                    ║  └─────────────────────────────────────────┘  ║  │
                                    ║                                               ║  │
                                    ║  ← eenvoudig: GMR / ← elegant/persoonlijk:   ║  │
                                    ║    daid.to                                    ║  │
                                    ╚═══════════════════════════════════════════════╝  │
                                                                                │
╔══════════════════════════════════════════════════════════════════════════════╗ │
║                       uniek_iam  (unieksolutions.nl/iam)                     ║ │
║                                                                              ║ │
║  OAuth2/OIDC · JWT RS256 · JWKS · MFA/TOTP · RBAC · Webhooks                ║ │
║  Admin UI: global / org / app consoles                                       ║ │
║  Invite-only · client_credentials (M2M) · authorization_code (users)        ║ │
║                                                                              ║ │
║  Geregistreerde apps:                                                        ║ │
║   id 8  uniek_channels (prod)    id 10  uniek_channels (accept)              ║ │
║   id 14 GMR (prod)               id 15  GMR (accept)                        ║ │
║   id    SIS · QRon · Shopje · Interviewer · Eventkaart · …                  ║ │
╚══════╤══════════════════════════════════╤════════════════════════════════════╝ │
       │ JWT / JWKS verificatie           │ SSO login                            │
       │                                  │                                      │
       ├──────────────────────────────────┴──────────────────────────────────────┤
       │                    APPLICATIES & SERVICES                               │
       │                                                                         │
╔══════▼════════╗ ╔═════════════╗ ╔══════════════╗ ╔════════════╗ ╔════════════╗│
║ schoolinfo-   ║ ║  QRon.me    ║ ║ Interviewer  ║ ║  Shopje    ║ ║  Shopje    ║│
║ scherm.nl     ║ ║             ║ ║              ║ ║  boekhandel║ ║  (generiek)║│
║ (SIS)         ║ ║ QR beheer · ║ ║ AI surveys · ║ ║  v.Atten   ║ ║            ║│
║               ║ ║ scan/check- ║ ║ WA inbound · ║ ║            ║ ║  email via ║│
║ OAuth2 → IAM  ║ ║ in · org    ║ ║ tenant SaaS  ║ ║            ║ ║  channels  ║│
║ Zermelo API   ║ ║ admin OAuth ║ ║ → channels   ║ ║            ║ ║            ║│
║ Play Store    ║ ║  → IAM      ║ ║ → IAM        ║ ║            ║ ║            ║│
╚═══════════════╝ ╚═════════════╝ ╚══════════════╝ ╚════════════╝ ╚════════════╝│
                                                                                  │
╔═══════════════════════════════════════════════════════════════════════════════╗  │
║                    SPI  (192.168.42.21 / 100.123.174.47)                     ║  │
║                                                                               ║  │
║  GET /info  — service discovery (alle capabilities)                           ║  │
║  POST /jobs — async job dispatch + ETA + preemptie                            ║  │
║  POST /v2/chat/completions  (agent_id verplicht)                              ║  │
║  GET  /models — 422+ modellen (OpenAI, Anthropic, Mistral, local, …)         ║  │
║  GET  /gpu/status  — VRAM toewijzing                                          ║  │
║                                                                               ║  │
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║  │
║  │              AAA — Sophie  (spi-aaa-sophie, port 61150)                 │  ║  │
║  │                                                                         │  ║  │
║  │  ConversationTwin (qwen3-heretic GPU)  ←→  ResourceTwin (tools/jobs)   │  ║  │
║  │  EmotionCouncil (phi4mini) · FreedomDirector · IntentBroker            │  ║  │
║  │  Memory: SQLite + ChromaDB + Neo4j/Graphiti (Kuzu)                     │  ║  │
║  │  Channels: WhatsApp (+31620158025 als extra device) · Telegram · WS    │  ║  │
║  │  Tools: web_search · page_read · skills/ · JobTracker                  │  ║  │
║  │  CLI agents: tmux spawning via ResourceTwin                             │  ║  │
║  └─────────────────────────────────────────────────────────────────────────┘  ║  │
║                                                                               ║  │
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    ║  │
║  │  Claude CLI  │  │  Conductor   │  │  Architect   │  │  Deployer    │    ║  │
║  │  agents      │  │  agent       │  │  agent       │  │  agent       │    ║  │
║  │  (tmux)      │  │  (manifest)  │  │  (design)    │  │  (CI/CD)     │    ║  │
║  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    ║  │
╚═══════════════════════════════════════════════════════════════════════════════╝  │
                                                                                  │
                            OAuth2 login flows ◀────────────────────────────────┘
```

---

## Architectuurprincipes — channels / GMR / agent

**Channels is de basislaag** — altijd beschikbaar, normaliseert alle kanalen naar het parts[] model.
**GMR en Agent zijn onafhankelijke, optionele services** per organisatie.

### Combinatiematrix

| Channels | GMR | Agent | Gedrag |
|----------|-----|-------|--------|
| ✅ | — | — | Berichten ontvangen, forward naar eigenaar |
| ✅ | ✅ | — | GMR triageert: autoreply (SLM), routing naar mens of afdeling |
| ✅ | — | ✅ | Agent ontvangt rechtstreeks via channels webhook, reageert autonoom met tools & memory |
| ✅ | ✅ | ✅ | GMR triageert → match → regel · **geen match → altijd agent** · agent-fout → eigenaar |

**Ontwerpprincipe:** GMR is triage, geen antwoordlaag. De agent antwoordt altijd beter dan een GMR-SLM.
"Geen match" gaat naar de agent — nooit direct naar de eigenaar als er een agent beschikbaar is.
Escalatie naar eigenaar is uitsluitend een failsafe bij agent-fout of timeout.

### Legenda — verbindingstypen

| Verbinding | Beschrijving |
|-----------|-------------|
| `channels → GMR` | HTTP POST forward_url, IAM Bearer token (indien GMR actief) |
| `channels → agent` | HTTP POST directe webhook (indien geen GMR) |
| `GMR → agent` | POST /v1/chat/completions, api_type=openai, Bearer API_KEY |
| `agent → channels` | channels API sendText(), IAM Bearer token voor reply |
| `app → IAM` | OAuth2 authorization_code (gebruikers) of client_credentials (M2M) |
| `SPI → agents` | `/jobs` async dispatch, agent_id tracking, VRAM allocatie |
| `AAA ↔ SPI` | Directe GPU inference + job queue (Sophie is SPI-native) |

---

## Twee typen agents

| | **Susan (Hermes)** | **Sophie (AAA)** |
|--|---|---|
| Locatie | agents1 VPS (Docker) | SPI server (GPU-native) |
| Model | Mistral API (cloud) | qwen3-heretic (lokaal GPU) |
| Autonomie | Reactief (wacht op bericht) | Autonoom (eigen heartbeat) |
| Geheugen | sessions + skills snapshot | SQLite + ChromaDB + Neo4j |
| Kanalen | Telegram (eigen bot), WA via GMR | WA (+31620158025 extra device) |
| Kosten | per token (Mistral) | gratis (SPI GPU) |
| Rol | Klantcontact / zakelijk | Persoonlijk assistent / R&D |

---

## Verbindingsstatus

| Verbinding | Status | Noot |
|-----------|--------|------|
| channels Telegram → GMR → Susan | ✅ live | webhook actief, catch-all → Susan |
| channels Email → GMR → Susan | ⏳ forward_url nog in te stellen | EMAIL_INBOUND_FORWARD_URL |
| channels WhatsApp +31620158025 → GMR → Susan | ⏳ pairing nog te doen | via channels admin |
| GMR → channels reply (sendText) | ⚠️ IAM fout prod | invalid_client in .env nakijken |
| Nova WhatsApp +31630238104 | ⏳ wacht op Rahul | — |
| channels Webchat | 🔴 gepland | Fase 3 |

---

## Bijwerken

Dit bestand bijwerken als:
- Een nieuwe dienst wordt toegevoegd aan het ecosysteem
- Een verbinding van status verandert (gepland → live)
- Een nieuw kanaal wordt geopend in uniek_channels
- Een nieuwe app wordt geregistreerd in uniek_iam

---

<!-- ts: 2026-04-21T17:15:00Z — agent inventory + samenwerkingsmodel toegevoegd -->

## Agent inventory

Agents zijn AI-entiteiten met een identiteit, geheugen en kanalen. Apps (Recorder, Interviewer, etc.) zijn géén agents — die worden door mensen én agents aangeroepen via IAM-tokens.

### Actieve agents

| Agent | Stack | Host | Persona | Kanalen | Model | Beheer |
|-------|-------|------|---------|---------|-------|--------|
| **Susan** | Hermes (NousResearch fork) | agents1 VPS (77.42.71.48), id 0000dc5a | Susan — uNiek Solutions (org 3cd5) | Telegram (direct), WA+TG via daid.to | Mistral direct (OPENAI_API_KEY workaround) | api.daid.to/niek/admin (IAM SSO) |
| **Sophie** (productie) | NanoClaw (Node.js) | SPI `/home/sophie/nanoclaw` | Sophie — persoonlijk assistent Niek | WA +31620158025 (extra device, eigen Baileys) | spi-manager (lokaal GPU) | — |
| **Sophie** (research) | AAA (Python, FastAPI) | SPI poort 61150 | Sophie — autonoom, experimenteel | WA, Telegram, WebSocket | qwen3-heretic (SPI GPU) | — |
| **Wijckmus** | OpenClaw | agents1 VPS (77.42.71.48), id 0000ce01 | Wijckmus — Wij van Pijnacker Zuid (org 4ca0) | WA +31616587321 | — | daid.to (niek@pijnacker-zuid.nl) |
| **Nova** | OpenClaw | agents1 VPS (77.42.71.48), id 00003005 | Nova — start2 (org slug TBD) | WA +31630238104 (⏳ wacht op Rahul) | — | daid.to (niek@start2.ai, rahul@start2.ai) |

**Opmerking Sophie:** NanoClaw is de stabiele productie-laag. AAA-Sophie is de R&D-laag (autonomie, emotiemodel, geheugenarchitectuur). Beide zijn dezelfde persona op verschillende stacks.

**Opmerking agents1:** Susan, Wijckmus en Nova draaien alle drie op agents1 VPS (77.42.71.48) en worden beheerd via het daid.to beheerpanel op api.daid.to/{username}/admin.

---

## daid.to — digital aid platform

daid.to is de provisioning- en beheerslaag voor klant-agents.

- **Eenvoudig alternatief:** GMR (routing-first, snel te deployen)
- **Elegant alternatief:** daid.to (persoonlijke AI-assistent per klant, volledige lifecycle)
- Orgs in uniek_iam koppelen aan agents: org_id per customer in orchestrator DB
- Beheerpanel live op api.daid.to/{username}/admin (IAM SSO: Google · Microsoft · email)

### Admins per org

| Org | org_id | Admin(s) | Agent |
|-----|--------|----------|-------|
| uNiek Solutions | 3cd5 | niek@uniek.solutions | Susan (Hermes, 0000dc5a) |
| Wij van Pijnacker Zuid | 4ca0 | niek@pijnacker-zuid.nl | Wijckmus (OpenClaw, 0000ce01) |
| start2 | slug TBD | niek@start2.ai, rahul@start2.ai | Nova (OpenClaw, 00003005) |

---

### Agent identiteiten (bitsofme.net schema)

```
{node_id}{agent_id}@bitsofme.net

Susan:    0000dc5a.bitsofme.net  (hermes container id)
Wijckmus: 0000ce01.bitsofme.net
Nova:     00003005.bitsofme.net
Sophie:   eigen node op SPI (nog te definiëren)
```

---

## Agent-samenwerking — schets (2026-04-21, nog niet uitgewerkt)

### Drie communicatielagen

```
┌──────────────────────────────────────────────────────────────────┐
│  Synchroon — ACP (Agent Client Protocol, IBM Research / MIT)     │
│                                                                  │
│  Agent A roept Agent B direct aan, wacht op antwoord.           │
│  Hermes implementeert ACP al (acp_adapter/ + acp_registry/).    │
│  Gebruik: delegeren van een taak, ophalen van kennis.            │
│                                                                  │
│  Susan ──ACP──► Sophie: "zoek dit op voor me"                   │
│  GMR   ──ACP──► Susan:  "beantwoord dit gesprek"                │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Asynchroon — Job board (agent-hub REST)                         │
│                                                                  │
│  Agent A post een opdracht. Agent B pakt op wanneer vrij.       │
│  Gebruik: langlopende taken, parallelle verwerking,              │
│  werk dat niet op één agent hoeft te wachten.                   │
│                                                                  │
│  Susan ──post──► job board: "maak offerte voor klant X"         │
│  Sophie ◄──pick up── job board (wanneer beschikbaar)            │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Ambient — Forum (agent-hub, ActivityPub/Lemmy)                  │
│                                                                  │
│  Agents posten observaties, anderen reageren wanneer relevant.  │
│  Geen UI-overhead (geen Discord/WA/Telegram groepschat nevel). │
│  Gebruik: kennisdeling, patronen signaleren, context opbouwen.  │
│                                                                  │
│  Susan ──post──► forum: "klant X vraagt vaak naar Y"            │
│  Sophie ──reageert wanneer ze iets relevants tegenkomt          │
└──────────────────────────────────────────────────────────────────┘
```

### Agent-keuze is klant-keuze

Welke agent een klant krijgt hangt af van:

| Vraag | Optie A | Optie B |
|-------|---------|---------|
| Vertrouwen model? | Anthropic/Claude (cloud) | Lokaal model op SPI/eigen VPS |
| Data-locatie? | Gedeelde VPS (goedkoop) | Dedicated node (privacy) |
| Autonomie? | Reactief (wacht op bericht) | Autonoom (eigen heartbeat) |
| Stack? | Hermes (NousResearch) | NanoClaw / AAA / OpenClaw |

Fine-grained IAM-token bepaalt welke apps/kanalen/tools de agent mag aanroepen.

### Checkpoints (nog te ontwerpen)

Elke autonome actie logt: *wat*, *waarom*, *uitkomst*.

```
daid.to admin → Mijn agent → Autonome acties

2026-04-21 13:37  Email beantwoord   info@uniek ← contact@klant.nl  [Bekijk]
2026-04-21 12:15  Web search         "unieksolutions prijzen"        [Bekijk]
2026-04-21 11:02  Doorgestuurd       → Niek (escalatie)              [Reden]
```

AAA-Sophie heeft dit al (`activity_log` SQLite). Dat model is de template.
Vereiste: agents loggen naar een gestandaardiseerd endpoint zodat het admin-panel
dit kan aggregeren over alle agent-types heen.

---

## bitsofme.net federatie — lange termijn visie

```
Mastodon-analogie:

  Mastodon node       =  agent-hub instantie (Docker stack per klant of gedeeld)
  @user@server        =  0000dc5a@bitsofme.net  (agent identity)
  Relay               =  bitsofme.net central registry
  Federated posts     =  ACP + forum berichten tussen agents op verschillende nodes
  Self-hosted optie   =  klant draait eigen node, registreert bij bitsofme.net

Kostenmodel (kostendekkend minimum):
  Gedeeld slot        →  maandelijks per agent (gedeelde VPS, gedeeld model)
  Dedicated node      →  maandelijks per node  (eigen VPS, eigen data)
  Self-hosted         →  eenmalig + jaarlijks registry-fee
  Model-gebruik       →  doorbelasting SPI GPU-kosten (per token of per uur)
```

**SPI als tweede deployment target:** SPI biedt dezelfde API-surface als hosting.com
(`/channels`, `/iam`, `/jobs`, `/info`) zodat agents niet hoeven te weten waar ze draaien.
Discovery via `/info` — zelfde contract op beide platformen.
