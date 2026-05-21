<!--
ts: 2026-01-27T12:30:00Z | git: <to-be-filled> | path: /opt/bootstrap
-->

# SPI Tools & Shared Resources

## Service Discovery (Use This First!)

**Instead of reading this entire file, query the Service Discovery API:**

```bash
# Get all available services (lightweight JSON, ~10-20 tokens)
curl http://localhost:63100/api/v1/services?env=prod

# Returns:
# - Service name, type (api/mcp/both), URLs
# - Health status (optional: ?health=true)
# - Real-time, auto-discovered from /opt/projects/*/APIMCP.md
```

**Endpoints:**
- Development: `http://localhost:61100/api/v1/services`
- Production: `http://localhost:63100/api/v1/services`

**Why Use Service Discovery:**
- **100x context window savings** (vs reading this 200+ line file)
- Always up-to-date (scans APIMCP.md files automatically)
- Programmatic access (JSON response)
- Only read detailed docs when you need specific service

**When to Read This File:**
- Understanding shared resources (venv, SSL, backups)
- Learning about non-service resources (models, scripts)

---

## Overview

This document describes shared resources and infrastructure (not services - use Service Discovery for services).

## Shared Resources

### Python Virtual Environments

**Shared venvs — use these by default. Never create a new venv for GPU/AI services.**

#### 1. CPU venv — FastAPI 0.115 (light services)
- **Location:** `/opt/tools/venv/`
- **Usage:** `source /opt/tools/venv/bin/activate`
- **Contains:** fastapi 0.115, httpx, pydantic v1, requests, common web libraries
- **Use for:** API services, scripts, tools without GPU/torch dependency

#### 2. CPU venv — FastAPI 0.133 / Pydantic v2
- **Location:** `/opt/tools/venvfastapi0133/`
- **Usage:** `source /opt/tools/venvfastapi0133/bin/activate`
- **Contains:** fastapi 0.133, uvicorn 0.38, aiosqlite 0.22, jinja2 3.1, pyyaml, python-multipart
- **Use for:** Services that require FastAPI 0.133+ or Pydantic v2 model features
- **Why separate:** FastAPI 0.133 requires starlette 1.0 which breaks services on starlette 0.38
- **First user:** `acc` (Agent Command Center)

#### 3. ROCm/GPU venv (AI/GPU services)
- **Location:** `/opt/tools/venvROCm7.2/`
- **Usage:** `source /opt/tools/venvROCm7.2/bin/activate`
- **Contains:** PyTorch (ROCm), transformers, whisper, TTS libraries, diffusers
- **Use for:** Parkiet, Whisper, XTTS, imgen, any service needing torch/GPU

#### Per-project venv (exception only)
- **Location:** `/opt/projects/{name}/venv/`
- **Create only when:** project has a genuine dependency conflict with ALL shared venvs
- **Document why** in the project's README or ARCHITECTURE.md
- **Never for:** GPU services — always use `/opt/tools/venvROCm7.2/`

**Rule:** Before creating a project venv, determine exactly why a shared venv cannot be used and name the new shared venv accordingly (e.g. `venvfastapi0133`). One shared copy per version saves disk and makes the constraint visible to all future services.

### SSL Certificates

**Generic (development):** ✅ READY
- **Location:** `/opt/tools/ssl/`
- **Purpose:** Self-signed certs for local HTTPS testing
- **Files:** Place `cert.pem`, `key.pem` here (not yet populated)
- **Created:** 2026-01-27 (directory ready for use)

**Project-specific:**
- **Location:** `/opt/projects/{name}/ssl/`
- **Purpose:** Project needs custom certificates

**Production:**
- Managed per environment (see SECRETS.md in each project)
- Never commit certificates to git

### Utility Scripts

**Location:** `/opt/projects/coding/scripts/` ✅ ACTIVE
- **smart_backup.sh** - Smart backup with compression + deduplication
- **scan_references.sh** - Find outdated path/port references
- **fix_references.sh** - Auto-fix outdated references
- **sync_bootstrap_to_projects.sh** - Sync template changes to all projects
- **cleanup_backups.sh** - Remove old/redundant backups
- **find_duplicates.sh** - Find duplicate files across /opt

### AI Models

**Location:** `/opt/models/` (organized by type)
- **`llm/gguf/`** - Quantized LLMs (Llama, Mistral, Phi, DeepSeek, Qwen, etc.)
- **`llm/hf/`** - HuggingFace LLM model directories
- **`vision/hf/`** - Vision-Language models (Qwen-VL, etc.)
- **`checkpoints/`** - Diffusion base models (SDXL, FLUX, WAN, Qwen Image Edit)
- **`loras/`** - LoRA fine-tuned adapters (character, style, pose)
- **`diffusion_models/`** - UNet/DiT weights
- **`text_encoders/`** - CLIP, T5, UMT5 encoders
- **`vae/`** - VAE models
- **`audio/`** - TTS/voice models (EmotiVoice, XTTS)
- **`utility/`** - Embedding models, face detection, pose estimation
- **`ollama/`** - Ollama model blobs
- Backward-compatible symlinks at root for all moved files

### Characters

**Location:** `/opt/characters/`
- **`{Name}_{6hexID}/`** - Per-character directory with reference images, datasets, LoRAs, output
- **`templates/`** - Shared assets: `clothing/`, `poses/`, `scenes/`, `backgrounds/`
- **`_archive/`** - Archived/test characters

**Access:** Always via API, never direct file access
- **SPI Manager (WLM) API:**
  - Development: `http://localhost:61115`
  - Production: `http://localhost:63115`
  - Documentation: `/opt/projects/spi-manager/API.md`
  - Features: 450+ models, GPU/VRAM management, job scheduling, service registry, interactive resource-claims (`/v3/test`)
  - Bootstrap: `GET http://localhost:63115/info` → redirects to `/info/v2` — full capability map
  - **Key endpoints (loopback = no auth, external = Bearer token):**
    - `POST /v2/chat/completions` — LLM chat (OpenAI-compat), capability: `chat`
    - `POST /v2/voice/synthesize` — TTS Dutch (Parkiet), capability: `tts`
    - `POST /v2/voice/transcribe` — STT Whisper large-v3, capability: `stt`
    - `POST /v2/image/generate` — ComfyUI image gen, capability: `image`
    - `POST /v2/vision/analyze` — **local** MiniCPM-o 2.6 Q4 (~22s), capability: `vision`
      - Body: `{"image": "<base64>", "prompt": "...", "agent_id": "..."}`
      - Or: `{"image_url": "http://...", "prompt": "...", "agent_id": "..."}`
    - `GET/PUT/DELETE /v2/files/{root}/{path}` — token-gated file CRUD, capability: `files`
      - Roots: `sophie`, `susan`, `shared`
    - `POST /v2/jobs` — async job queue (llm|tts|stt|image), capability: `jobs`
    - `POST /v3/test` — interactieve resource-claim (comfyui/model voor N sec) → service_url, capability: `jobs`
    - `POST /v3/jobs/{id}/release` — geef test-claim vrij
    - `POST /v3/image/generate` — accepteert optioneel `workflow_json` (eigen ComfyUI graph)
    - `GET /registry/pages` — services with web_url (dashboards, UIs)
    - `POST /registry/register` — register service + optional `web_url`
  - **⚠️ Resource-regel:** start NOOIT zelf GPU-services (ComfyUI/llama-server/etc.) of roep hun poort direct aan. Altijd via `/v3/test` (testen) of `/v3/{image,text,...}` (productie). Zie `GET /info` → `resource_rules`.

**Image Generation:**
- **ComfyUI API:** Evolving to generic 'model request' system
  - Development: Port 61XXX (see project PORTS.md)
  - Production: Port 63XXX (see project PORTS.md)

---

## Services (Use Service Discovery API)

**For service endpoints and availability, use the Service Discovery API instead:**

```bash
curl http://localhost:63100/api/v1/services?env=prod
```

**Common services include:**
- SPI Manager (WLM) - AI/LLM access (450+ models), GPU, job scheduling
- Tickets - Task tracking and backlog management
- Neo4j - Graph database
- ChromaDB - Vector database
- Memory - Unified Chroma + Neo4j API

**For detailed API docs:** Read `/opt/projects/{service}/API.md` only when needed

### Web Preview (voor SSH/Tmux sessies)

**Agents kunnen preview-pagina's serveren via de SPI Preview Server.**

**Webroot:** `/opt/tools/preview/` (schrijfbaar door `uniek`)
**URL via Tailscale:** `http://spi:64801/` of `http://100.123.174.47:64801/`
**Service:** `spi-preview.service` (user systemd, altijd aan)

**Workflow voor agents:**
1. Schrijf HTML-bestanden naar `/opt/tools/preview/`
2. Vertel de gebruiker de URL: `http://spi:64801/bestandsnaam.html`
3. Gebruiker opent dit in browser via Tailscale

```bash
# Voorbeeld: preview van een nieuwe pagina
cp /tmp/mijn-pagina.html /opt/tools/preview/
# → Bereikbaar op http://spi:64801/mijn-pagina.html
```

**Service beheer:**
```bash
systemctl --user status spi-preview    # Status checken
systemctl --user restart spi-preview   # Herstart na problemen
```

**Noot:** Port 80 wordt gebruikt door de SPI Hub (Apache, `/opt/tools/spi-hub/`).
Dat is read-only voor agents. Gebruik altijd poort 64801 voor preview.

---

### Notificaties (ntfy)

**Standaard topic voor alle agent-notificaties:** `spi-news`

```bash
# Stuur een notificatie (gebruik altijd dit topic)
curl -s -d "Jouw bericht hier" http://localhost:61138/spi-news

# Met titel en prioriteit
curl -s -H "Title: Deploy klaar" -H "Priority: high" \
  -d "service X is gedeployed" http://localhost:61138/spi-news
```

**Configuratie:**
- URL: `http://localhost:61138` (intern op SPI)
- Tailscale: `http://100.123.174.47:61138`
- Config: `/opt/projects/ntfy/config/server.yml`
- **Gebruik altijd topic `spi-news`** — de gebruiker is hierop geabonneerd in de ntfy-app

**Nooit een nieuw topic aanmaken** zonder afstemming — de gebruiker moet elk topic handmatig abonneren in de app.

---

### Screenshots

**Location:** `/opt/screenshots/`

**Purpose:** Screenshots shared from laptop to agents for visual context

**Access:** Read-only for agents

**Usage:** Agent reads screenshot files to understand UI/UX issues

### Backups

**Location:** `/opt/backups/{project}_{timestamp}/`

**Format:** `{project}_YYYY-MM-DDTHH-MM/`

**Examples:**
- `/opt/backups/coding_2026-01-27T12-25/`
- `/opt/backups/model-router_2026-01-26T15-30/`

**Includes:** Code, text files, configuration (compressed in tar.gz)
**Excludes:** `.git`, `__pycache__`, `node_modules`, `venv` (auto-excluded)
**Deduplication:** Large files (>20MB) hardlinked from previous backups

**Script:** `/opt/projects/coding/scripts/smart_backup.sh <path> [description]`

---

## Utility Scripts

### Smart Backup Script (RECOMMENDED)

**Path:** `/opt/projects/coding/scripts/smart_backup.sh` ✅ ACTIVE

**Usage:**
```bash
bash /opt/projects/coding/scripts/smart_backup.sh /opt/projects/myproject "description"
```

**Features:**
- ✅ **Compression:** Creates tar.gz (saves space)
- ✅ **Deduplication:** Hardlinks large files (>20MB) from previous backups
- ✅ **Metadata:** Stores git hash, timestamp, file list
- ✅ **Space efficient:** Only stores changed files, deduplicates unchanged large files

**Output:**
- Backup directory: `/opt/backups/YYYY-MM-DDTHH-MM_{project}_{description}/`
- Contains: `backup.tar.gz`, `.backup_metadata`, hardlinked large files

**Example:**
```bash
# Before making changes
bash /opt/projects/coding/scripts/smart_backup.sh /opt/projects/aiid "before_refactor"

# Shows: Deduplicated 15 files, saved 2.3GB
```

### Legacy Backup Script (DEPRECATED)

**Path:** `/opt/tools/scripts/backup_snapshot.sh` ⚠️ DEPRECATED

Use `smart_backup.sh` instead for compression and deduplication.

### Deployment Scripts

**Location:** Per-project in `/opt/projects/{name}/scripts/`

**Standard scripts:**
- `deploy_dev_to_accept.sh` - Deploy to acceptance with validation
- `deploy_accept_to_prod.sh` - Deploy to production (strict checks)
- `deploy_prod_to_accept.sh` - Reverse flow for investigation
- `deploy_prod_to_dev.sh` - Emergency hotfix flow

**See:** DEPLOY.md in each project for detailed procedures

---

## Active Services Registry (DEPRECATED)

**⚠️ This section is DEPRECATED. Use Service Discovery API instead:**

```bash
# Get real-time service list with health checks
curl http://localhost:63100/api/v1/services?env=prod&health=true
```

**Why Service Discovery API is better:**
- Always up-to-date (auto-scans APIMCP.md files)
- No manual maintenance needed
- Includes health status
- Supports filtering by environment (dev/accept/prod)
- Lightweight JSON response (~500 bytes)

---

## Development Tools

### CLI Coding Tool

**Location:** `/opt/tools/coding/`

**Purpose:** Interactive menu for launching AI coding agents (Claude, Codex, Gemini, OpenCode)

**Features:**
- Tmux session management
- Project directory switching
- Ticket integration
- Bootstrap workflow support

**Usage:** Run `coding` from any directory

### SSH naar hosting.com (shared hosting, 185.146.22.239:7822)

**Primaire methode — persistente tunnel (gebruik dit altijd):**
```bash
ssh -S /tmp/spi-hosting.sock bitsofme@185.146.22.239 'commando'
```
Tunnel is actief zolang de sessie loopt. Geen nieuwe verbinding = geen fail2ban risico.

**Fallback alias:** `uniek_shared_hostingcom` (staat in ~/.ssh/config) — alleen als tunnel niet beschikbaar is.

**Regels:**
- Tunnel beschikbaar? Altijd `-S /tmp/spi-hosting.sock` gebruiken
- Tunnel niet beschikbaar? Alias gebruiken, max 2 snelle opeenvolgende verbindingen
- Bij blokkade: wacht ~5 minuten
- Complexe commando's: schrijf eerst een `.sh` bestand, kopieer via `scp`, voer uit via SSH

**SQLite op hosting.com:**
- Server heeft sqlite3 versie 2013 — te oud voor WAL-databases gebouwd met sqlite3 2019+
- Oplossing: download DB via `scp` en inspecteer lokaal met Python:
  ```bash
  scp uniek_shared_hostingcom:/pad/naar/db.sqlite /tmp/db.sqlite
  python3 -c "import sqlite3; conn=sqlite3.connect('/tmp/db.sqlite'); ..."
  ```
- Nooit `sqlite3` CLI op de server gebruiken voor WAL-databases

**PHP op hosting.com:**
- Geen `vendor/autoload.php` lokaal in `/opt/projects/uniek_channels/` — composer staat alleen op de server
- JWT genereren: op de server zelf doen via `ssh uniek_shared_hostingcom "cd /pad && php scripts/gen_token.php"`
- Nooit `php -r "require 'vendor/autoload.php'..."` lokaal proberen zonder eerst `ls vendor/` te checken

**⚠️ Gebruik geen inline `php -r '...'` via SSH naar hosting.com:**
De CPanel PHP CLI wrapper (`/var/cpanel/ea4/ea_php_cli.pm`) gooit altijd `Unsuccessful stat on filename containing newline` als de inline code newlines bevat. De code werkt wel maar produceert lawaaierige output, en bij parse-errors is debugging een nachtmerrie omdat de error mengt met de wrapper-warning.

**Standaardwerkwijze:**
```bash
# 1. Schrijf script lokaal (met try/catch — voorkomt exit 255 die parallelle SSH-calls cancelt)
cat > /tmp/myscript.php <<'PHP'
<?php
try {
    $db = new PDO("sqlite:/home/bitsofme/enpznl/data/interviewer.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    // ... werk
} catch (Throwable $e) { echo "ERR: ".$e->getMessage()."\n"; }
PHP

# 2. SCP naar server (via tunnel-socket)
scp -o ControlPath=/tmp/spi-hosting.sock /tmp/myscript.php bitsofme@185.146.22.239:/home/bitsofme/enpznl/data/

# 3. Voer uit (sequentieel — geen parallelle SSH-calls op dezelfde socket)
ssh -S /tmp/spi-hosting.sock bitsofme@185.146.22.239 "php /home/bitsofme/enpznl/data/myscript.php"
```

- Schema onbekend? Begin met `PRAGMA table_info(tabel)` — niet gokken op kolomnamen
- Eén SSH-call tegelijk via dezelfde socket; parallelle calls worden gecancelled bij eerste error
- Cleanup achteraf: `rm` het scriptbestand op de server

**Serverlocaties hosting.com:**

| project | pad |
|---------|-----|
| uniek_channels prod | `/home/bitsofme/unieksolutions.nl/channels/` |
| uniek_channels accept | `/home/bitsofme/accept.unieksolutions.nl/channels/` |
| channels DB prod | `/home/bitsofme/unieksolutions.nl/channels/var/db/channels.sqlite` |
| enquete.pijnacker-Zuid.nl | `/home/bitsofme/enpznl/` ← **gebruik altijd deze symlink** |

**⚠️ pijnacker-Zzuid.nl pad — gebruik symlink `enpznl`:**
Het domein `enquete.pijnacker-zuid.nl` bevat een punt vóór `nl` die AI-agents consistent weglaten.
Symlink aangemaakt (2026-05-03): `/home/bitsofme/enpznl` → `/home/bitsofme/enquete.pijnacker-zuid.nl`
```bash
# ✅ Altijd gebruiken:
ssh ... 'ls /home/bitsofme/enpznl/api/'
scp ... bitsofme@185.146.22.239:/home/bitsofme/enpznl/api/file.php
# ❌ Nooit direct typen — punt verdwijnt in tokenizer
```

---

### Database Tools

**Neo4j (Graph Database):**
- Endpoint: `bolt://localhost:61521`
- Credentials: See `/opt/tools/.env` or project `.env`
- Discover via: `GET http://localhost:63115/registry/services`

**ChromaDB (Vector Database):**
- Purpose: Embeddings, semantic search, RAG
- Collections: Per-project namespaces
- Discover via: `GET http://localhost:63115/registry/services`

---

## Configuration Files

### Shared Configuration

**Location:** `/opt/tools/.env` (if needed for shared services)

**Contains:**
- Neo4j credentials
- Model Router API keys
- Shared service tokens

**Note:** Project-specific credentials go in project `.env` files

### Per-Project Configuration

**Location:** `/opt/projects/{name}/.env`

**Standard variables:**
```bash
GITHUB_PAT=<token>              # For git operations
DATABASE_URL=<connection>        # Database connection
API_KEY=<key>                   # External API keys
SPI_MANAGER_URL=<url>           # SPI Manager endpoint (default: http://localhost:63115)
```

**Security:**
- Always add `.env` to `.gitignore`
- Never commit credentials to git
- See SECRETS.md for credential management

---

## Registering Your Service with SPI Manager

**All services should register with SPI Manager for health monitoring, discovery, and resource coordination.**

### Option A: Self-Registration at Startup (Recommended for agents)

Add this to your service's startup code:

```python
import httpx
httpx.post("http://localhost:63115/registry/register", json={
    "service_id": "your-service-name",
    "service_name": "Human Readable Name",
    "description": "What this service does",
    "category": "ai-inference",  # or: tool, database, web, voice, etc.
    "endpoint": {
        "environment": "prod",  # dev, accept, or prod
        "base_url": "http://localhost:YOUR_PORT",
        "port": YOUR_PORT,
        "health_check_url": "/health"
    }
})
```

This is **ephemeral** — registration is lost on SPI Manager restart. Safe for any agent to call.

### Registering a web page (web_url)

Als jouw agent een **browseable pagina** publiceert (HTML, dashboard, documentatie), voeg dan `web_url` toe aan je registratie. De pagina verschijnt dan automatisch in het "Pagina's" tab van spi-hub (`http://192.168.42.21/`):

```python
httpx.post("http://localhost:63115/registry/register", json={
    "service_id": "uniek-channels",
    "service_name": "Channels",
    "description": "Communicatie transportlaag — WhatsApp, Telegram, Email, SMS",
    "category": "infrastructure",
    "web_url": "http://192.168.42.21/channels/communication-flow.html",
    "endpoint": {
        "endpoint_id": "uniek-channels-prod",
        "environment": "prod",
        "version": "1.0.0",
        "base_url": "https://unieksolutions.nl/channels",
        "port": 443,
        "health_check_url": "https://unieksolutions.nl/channels/api/health"
    }
})
```

**Beschikbare pagina's opvragen:**
```bash
curl http://localhost:63115/registry/pages
# → lijst van {service_id, service_name, description, category, web_url}
```

spi-hub toont kaarten voor elke service met `web_url`. Geen hardcoding nodig.

### Option B: Permanent Registration in services.yaml

For always-on or critical services, add to `/opt/projects/spi-manager/config/services.yaml`:

```yaml
services:
  always_on:
    - name: your-service
      port: YOUR_PORT
      health_url: /health
      description: "What this service does"
```

This is **persistent** — survives restarts, enables alerting. Only edit via SPI Manager project (human approval).

### Requirements for Your Service

- **`/health` endpoint** — MUST return `{"ok": true}` (see `/opt/bootstrap/APIMCP.md`)
- **`agent_id` in requests** — Include when calling SPI Manager APIs
- **Port allocation** — Check `/opt/bootstrap/PORTS.md` before choosing a port

---

## Notes

- **Source of truth:** Always `/opt/projects/{name}/` for development
- **Deployment flow:** dev → accept → production (via scripts only)
- **Shared vs project-specific:** Default to project-specific unless truly shared
- **Model files:** Large files (>100MB) stay in `/opt/models/` (organized by type), accessed via API
- **Character data:** All character assets in `/opt/characters/{Name}_{ID}/` (reference, dataset, LoRA, output)

---

## Project Venv Inventory

Scanned: 2026-03-18. Lists all projects in `/opt/projects/` that have their own `venv/` or `.venv/`. Projects without a local venv are omitted (they use a shared venv or no Python).

**Legend:**
- Recommended: `/opt/tools/venv` (CPU/light) or `/opt/tools/venvROCm7.2` (GPU/AI)
- Status: `migrate` = should switch to shared venv | `keep` = justified own venv | `review` = investigate further

| Project | Venv dir | Size | Primary packages | Recommended venv | Notes |
|---------|----------|------|-----------------|------------------|-------|
| `42day` | `venv/` | 152 MB | playwright | `/opt/tools/venv` | Playwright is already in shared venv (tickets uses it from there). Migrate. |
| `codeflow` | `venv/` | 63 MB | fastapi, requests, SQLAlchemy, uvicorn | `/opt/tools/venv` | CPU-only web framework stack. Migrate. |
| `comfyui` | `venv/` | 26 GB | torch+ROCm 2.5.1, diffusers, transformers, torchvision | `/opt/tools/venvROCm7.2` | GPU/ROCm. Active prod service (`/etc/systemd/system/tool-comfyui.service`) uses this venv directly. Large — migrate to ROCm shared venv or consolidate. Excluded from skip list so flagged here. |
| `conductor` | `venv/` | 172 MB | fastapi, SQLAlchemy, APScheduler, chromadb-client, opentelemetry | `/opt/tools/venv` | CPU-only orchestration service. chromadb-client is already in shared venv. Migrate. |
| `examtool` | `venv/` | 123 MB | fastapi, motor (MongoDB async), websockets | `/opt/tools/venv` | CPU-only API service. Migrate. |
| `flipper` | `venv/` | 24 MB | pyserial, ufbt (Flipper Zero toolchain) | keep or `/opt/tools/venv` | Flipper-specific toolchain (`ufbt`). Small and niche — keep own venv unless ufbt added to shared. |
| `gmr` | `.venv/` | 48 MB | fastapi, pydantic, httpx, pytest (dev only — celery/redis not installed yet) | `/opt/tools/venv` | Partial/dev-only setup. README mentions `/opt/shared/venv` (outdated path). Migrate to shared CPU venv. |
| `nameclaim` | `venv/` | 109 MB | fastapi, SQLAlchemy, httpx, beautifulsoup4 | `/opt/tools/venv` | CPU-only API + scraper. README instructs creating local venv — update docs. Migrate. |
| `product-watch` | `venv/` | 21 MB | requests, beautifulsoup4 | `/opt/tools/venv` | Lightweight scraper script. Migrate. |
| `sophie-lamp` | `venv/` | 33 MB | requests, soco (Sonos), lxml | `/opt/tools/venv` | Hue/Sonos listener. CPU-only. Migrate. |
| `spi-manager` | `venv/` | 97 MB | fastapi, pydantic, requests | `/opt/tools/venv` | **Dev venv only** — production service uses `/opt/tools/spi-manager/venv/`. Project venv is used for local dev/testing. Could consolidate with shared CPU venv. |
| `test_project` | `venv/` | 43 MB | fastapi, httpx, pytest | `/opt/tools/venv` | Throwaway test project. Migrate or remove. |
| `tickets` | `venv/` | 282 MB | fastapi, fastmcp, aiohttp, playwright, pytest-playwright | `/opt/tools/venv` | **Production service already uses `/opt/tools/venv`** (confirmed in `tool-tickets.service`). Local project venv is dev-only and contains playwright + test deps. Consider removing or keeping as dev-only. |
| `ucc` | `venv/` | 80 MB | fastapi, requests, websocket-client, websockets | `/opt/tools/venv` | CPU-only API bridge. Migrate. |
| `visual-novel-engine` | `venv/` | 291 MB | fastapi, aiohttp, SQLAlchemy, celery, bcrypt, apprise | keep or `/opt/tools/venv` | CPU-only (torch commented out in requirements). Active prod service uses this venv directly (`visual-novel-engine.service`). Heavy due to celery + many deps. Review for migration after service stabilizes. |
| `vn-engine-test` | `venv/` | 79 MB | fastapi, httpx, pytest, bandit | `/opt/tools/venv` | Test/development copy. Migrate or remove. |

### Summary

- **GPU/ROCm venvs (should use `/opt/tools/venvROCm7.2`):** `comfyui` (26 GB — largest offender)
- **CPU venvs that can migrate to `/opt/tools/venv`:** `42day`, `codeflow`, `conductor`, `examtool`, `gmr`, `nameclaim`, `product-watch`, `sophie-lamp`, `spi-manager` (dev), `test_project`, `tickets` (dev), `ucc`, `vn-engine-test`
- **Justified own venvs (keep for now):** `flipper` (ufbt toolchain), `visual-novel-engine` (active service, many deps)
- **Skipped per instructions:** `voice/` subdirs (parkiet, kokoro, xtts), `ai-toolkit`, `kohya_ss`, `WanGP`
- **Estimated space savings if migrated:** ~1.5 GB (CPU venvs) + 26 GB (comfyui GPU venv if consolidated)
