<!--
ts: 2025-12-31T13:20:05Z | git: <to-be-filled> | path: <relative-path>
-->

# Project Bootstrap – START

This file is the single entrypoint for starting a new project.

## Agent Bootstrap via SPI `/info`

**Default rule for all agents:** start discovery at the SPI Manager index, not by guessing endpoints.

Primary bootstrap endpoints:
- LAN: `http://192.168.42.21:63115/info`
- Tailscale: `http://100.123.174.47:63115/info`
- Local on SPI host: `http://localhost:63115/info`

Use `/info` first to discover what SPI currently exposes. Then follow the linked capability surfaces such as models, jobs, services, message, image, audio, video, and file handling.

### Endpoint change rule

When adding or modifying endpoints:
- update the SPI `/info` index so agents discover the new capability from the default entrypoint
- update the relevant `API.md` / `APIMCP.md` contract
- update `STATUS.md` with the live state
- update `VERSIONS.md` or deployment docs when the change affects dev/accept/prod parity

Treat endpoint exposure as a small DTAP contract:
- **Dev**: implement and test the endpoint
- **Accept**: verify compatibility and discovery
- **Prod**: expose through `/info` only when operational

## Bootstrap File Index

All projects use these standard files. **Owner** = who is responsible for filling and maintaining.

### Process & Workflow
| File | Purpose | Owner |
|---|---|---|
| **WORKFLOW.md** | Pipeline activities, SIPOC per node, subprocess drill-downs | Conductor / Human |
| **USERSTORIES.md** | Stories for all actors (human + agent), acceptance criteria | Conductor / Ticketmaster |
| **RUBRICS.md** | Quality gates per activity: criteria, weights, thresholds | Conductor / Ticketmaster |
| **TESTS.md** | Test strategy, coverage requirements, story→test mapping | Tester agent / Human |

### Project State
| File | Purpose | Owner |
|---|---|---|
| **README.md** | Project index and quick reference | Human (initial) |
| **START.md** | This file — bootstrap entrypoint | Human |
| **STATUS.md** | Current state, progress, known issues | Conductor |
| **BACKLOG.md** | Prioritized work items (synced with /opt/tickets) | Conductor / Ticketmaster |
| **NEXT_SESSION.md** | Session continuation prompt (update at >50% context) | Agent (end of session) |

### Technical (Agent-Specific)
| File | Purpose | Owner |
|---|---|---|
| **ARCHITECTURE.md** | System design, technical decisions, ADRs | Architect agent |
| **DESIGN.md** | UI/UX specifications, interaction patterns | Architect / Designer agent |
| **APIMCP.md** | API and MCP contract (if applicable) | Architect agent |
| **VERSIONS.md** | Multi-environment version tracking, DTAP locations | Deployer agent / Human |

### Operations
| File | Purpose | Owner |
|---|---|---|
| **DEPLOY.md** | Deployment procedures + secret *locations* per environment | Human / Deployer agent |
| ~~SECRETS.md~~ | **Deprecated** — use `.env.example` + DEPLOY.md instead | — |
| **MIGRATION_CHECKLIST.md** | Verification checklist for migrations | Human |
| **PORTS.md** | Port allocation registry | Human |
| **SSH_KEYS.md** | SSH key management per environment | Human |

### Development Lifecycle
| File | Purpose | Owner |
|---|---|---|
| **SDLC_PIPELINE.md** | Stage-based development: dev/test/deploy/prod agents, RBAC, handoffs | Human / Pipeline admin |
| **CODING_RULES.md** | Development standards, git workflow, security patterns | Human |

### Machine-Executable Config (generated from docs above)
| File | Purpose | Source doc |
|---|---|---|
| `config/manifest.yaml` | Phase/activity agent assignment + commands | WORKFLOW.md |
| `config/rubrics.yaml` | Rubrics in machine-readable form | RUBRICS.md |

### Development
- **ticket.md** - Ticket template for /opt/tickets integration

---

## Document Ownership Model

```
Human designs:      WORKFLOW.md → Conductor executes manifest.yaml
Conductor fills:    STATUS.md, BACKLOG.md, USERSTORIES.md, RUBRICS.md
Agents fill:        ARCHITECTURE.md, DESIGN.md, TESTS.md, VERSIONS.md
All docs inform:    Agent context packets (injected at task assignment, not read at runtime)
Tickets drive:      Individual work items — structured DB, not markdown
```

**Key rule:** Docs are the design record (human-readable, LLM context).
Config YAML is the executable form (machine-readable, agent runtime).
Tickets are individual work items (structured, queryable, stateful).

---

## Bootstrap Steps

1. Copy all templates from /opt/bootstrap into project root.
2. Fill README.md (project overview) and WORKFLOW.md (pipeline + SIPOCs).
3. Define USERSTORIES.md and RUBRICS.md — Conductor uses these to assign work.
4. Generate config/manifest.yaml and config/rubrics.yaml from the above.
5. Fill ARCHITECTURE.md and DESIGN.md (or let Architect agent do it in first cycle).
6. Initialize VERSIONS.md with development environment.
7. Setup dev/test environments — fill TESTS.md.
8. Configure deployment (DEPLOY.md).
9. IAM integration is OPTIONAL and deferred.

## ⚠️ GPU & Model Access — MANDATORY

**SPI Manager is the authoritative control plane for ALL GPU-consuming work on SPI.**

- ALL inference, image gen, video, training, TTS/STT, local LLM residency → through SPI Manager
- SPI queues, schedules, reports ETA, preempts lower-priority workloads, tracks ownership
- If resources unavailable → expect `queued` / `blocked_by` / ETA responses — **do not bypass**
- Direct unmanaged GPU processes started outside SPI are **operational debt** and may be stopped by policy

**LLM inference:** `POST http://192.168.42.21:63115/v2/chat/completions` with `agent_id` required
**Prewarm model:** `POST http://192.168.42.21:63115/admin/local-models/start {"model": "<name>"}`
**Discovery:** `GET http://192.168.42.21:63115/info` — authoritative entrypoint for all capabilities

### How to test/build — sanctioned paths (do NOT start services directly)

| Wil je... | Doe dit |
|---|---|
| Iteratief testen/debuggen (ComfyUI, model) | `POST /v3/test` `{resource, vram_gb, hold_s}` → poll job tot `running` → `result.service_url` → werk direct → `POST /v3/jobs/{id}/release` zodra klaar |
| Eigen ComfyUI workflow draaien | `POST /v3/image/generate` met `workflow_json` veld — spi-manager regelt VRAM + ComfyUI lifecycle |
| Productie-inference | `POST /v3/{image,text,vision,audio}/...` — fire-and-forget job |
| Model uitproberen | `POST /v3/test` met `resource=model` + `model_key` — of gewoon `/v3/text/generate` |

**NOOIT:** `python main.py --port 61620` (of welke GPU-service dan ook zelf starten),
`systemctl start` van GPU-services buiten SPI om, of directe poort-calls zonder een
test-job/productie-job. SPI detecteert ongemanagede GPU-processen en kan ze stoppen
zodra een managed job de VRAM nodig heeft — directe launches mislukken dus sowieso.

**Volledige regels:** `GET /info` → secties `tools.test` + `resource_rules`.

## Important Rules

- No agent may start work without reading this file.
- Source of truth is always /opt/projects/<project-name>
- Update VERSIONS.md after each deployment
- All backlog items synced with /opt/tickets service
- Update documentation when you're over 50% context window and write the prompt for the next session in NEXT_SESSION.md
- Commit to Github when this context window is reached (see SECRETS.md for GitHub PAT location)
- Only edit files in /opt/projects directly, never in /opt/tools or /opt/products unless specifically instructed to

## 🛠️ Tool Discovery (Zero Context Window Cost!)

**Discover available services programmatically:**

```bash
# Get all available services (10-20 tokens vs 2,000+ from docs)
curl http://localhost:63100/api/v1/services?env=prod

# Returns: service name, type (api/mcp/both), URLs, health status
# Only read detailed docs (/opt/projects/{service}/API.md) when you need them
```

**Service Discovery API:**
- Development: `http://localhost:61100/api/v1/services`
- Production: `http://localhost:63100/api/v1/services`
- Query params: `?env=dev|accept|prod` and `?health=true|false`
- Auto-scans `/opt/projects/*/APIMCP.md` for service metadata
- **100x context window savings** (lightweight JSON vs reading full docs)

### Core Documentation (Read As Needed)
- **`/opt/bootstrap/ECOSYSTEM.md`** - Ecosysteem architectuur: alle diensten, agents en verbindingen. **Lees dit als je werkt aan channels, GMR, IAM of agents** — bevat de combinatiematrix (channels/GMR/agent optioneel), verbindingsstatus en ontwerpprincipes. Interactief diagram op SPI: `https://192.168.42.21:63443/ui/static/ecosystem-messaging.html`
- **`/opt/bootstrap/TOOLS.md`** - Shared resources guide (venv, SSL, backups)
- **`/opt/bootstrap/CODING_RULES.md`** - Mandatory coding standards
- **`/opt/bootstrap/APIMCP.md`** - API and MCP design patterns
- **`/opt/bootstrap/SERVICE_CONTRACT.md`** - Universeel service-contract: verplichte endpoints (`/info`, `/tokens`, `/tools`, `/skills`, `/health`), auth-standaard, scope-naamgeving, foutformaat en migratieprioritering. **Elke uNiek service implementeert dit contract.**
- **`/opt/bootstrap/INTEGRATION.md`** - IAM integratie-gids voor applicatiebouwers (OAuth2, JWT, auto-provisioning)
- **`/opt/projects/spi-manager/API.md`** - AI models and GPU access (422+ models)

### Key Locations
- **Development:** `/opt/projects/<project-name>/` (READ/WRITE access, source of truth)
- **Acceptance:** `/opt/accept/<project-name>/` (read-only, deploy via scripts)
- **Production (tools):** `/opt/tools/<project-name>/` (shared tools, deploy via scripts)
- **Production (services):** `/opt/products/<project-name>/` (web services, deploy via scripts)
- **Shared resources:** `/opt/tools/venv/`, `/opt/tools/ssl/`, `/opt/models/` (organized by type, see TOOLS.md)
- **Characters:** `/opt/characters/{Name}_{ID}/` (centralized character data, see TOOLS.md)
- **Backups:** `/opt/backups/{project}_{timestamp}/` (code/text only, not media/models)
- **Credentials:** Project-specific in `/opt/projects/{projectname}/.env` (see SECRETS.md)

### Working in SSH Sessions (25-line limit)
- **Output visibility:** Last ≤25 lines only (limited scroll-back)
- **Summarize actions:** Always use last few lines for summary/next steps
- **Never run sudo:** Write exact command, ask user to run it
- **Commit AND push:** Always `git push` after commit (local = no backup)

### Documentation Rules
- **NEVER create new .md files** unless explicitly requested
- **Update existing bootstrap files:** README, STATUS, BACKLOG, ARCHITECTURE, etc.
- **Single intent per file:** Max ~15K tokens
- **Read as needed:** Don't read all docs upfront, lazy load when task requires

## 🤖 AI Model & GPU Access (For All Agents)

**All SPI services have access to centralized AI models and GPU resources via the SPI Manager (WLM).**

### Quick Reference:
- **API Documentation:** `/opt/projects/spi-manager/API.md` - Complete guide for agents
- **Available models:** 422+ models (OpenAI, Anthropic, Google, Venice, Mistral, Groq, local)
- **Development API:** http://localhost:61115
- **Production API:** http://localhost:63115
- **Interactive docs:** http://localhost:61115/docs (Swagger UI)

### Common Operations for Agents:

**Discover available models:**
```bash
GET http://localhost:61115/models
# Returns 422+ models with availability, cost, and capabilities
```

**Get LLM completion:**
```bash
POST http://localhost:61115/invoke
{
  "prompt": "Your prompt here",
  "agent_id": "your-service-name",  # REQUIRED for tracking
  "model": "auto"  # or specify: "claude-3-7-sonnet-20250219"
}
```

**Check GPU/VRAM availability:**
```bash
GET http://localhost:61115/gpu/status
# Returns: total_vram_gb, used_vram_gb, free_vram_gb, loaded_models
```

**Request VRAM for GPU workload:**
```bash
POST http://localhost:61115/gpu/allocate
{
  "requester": "your-service-name",
  "required_vram_gb": 10.0,
  "priority": 7  # 1-10: Video(9) > Image(7) > LLM(5)
}
# WLM will evict idle models if needed
# Returns: allocation_id for cleanup later
```

**Release VRAM allocation:**
```bash
POST http://localhost:61115/gpu/release
{
  "allocation_id": "alloc_abc123",
  "restore_models": false
}
```

### Agent Requirements:
⚠️ **ALWAYS include `agent_id` in all requests** - Required for:
- Usage tracking and analytics
- Budget management per service
- Cost attribution
- Performance monitoring

### Register Your Service with SPI Manager:
```bash
POST http://localhost:63115/registry/register
{
  "service_id": "your-service-name",
  "service_name": "Human Readable Name",
  "description": "What this service does",
  "endpoint": {
    "environment": "prod",
    "base_url": "http://localhost:YOUR_PORT",
    "port": YOUR_PORT,
    "health_check_url": "/health"
  }
}
```
**See:** `/opt/bootstrap/TOOLS.md` → "Registering Your Service" for full details.

### Full Documentation:
📚 **Complete API guide:** `/opt/projects/spi-manager/API.md`
🛠️ **All available tools:** `/opt/bootstrap/TOOLS.md`
📋 **Coding standards:** `/opt/bootstrap/CODING_RULES.md`
