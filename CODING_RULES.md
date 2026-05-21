# CODING RULES - SPI Development Standards

Essential coding standards for all SPI development work.

## Essential Rules

### Output & Communication
- **One-line steps:** Maximum 10 words per step
- **Multi-line blocks:** Only for scripts/config, note context clearly
- **SSH sessions:** Keep responses ≤25 lines (limited scroll-back)
- **Exact commands:** Use absolute paths, concrete commands
- **Ask questions:** When >50% unclear about requirements

### Git Workflow
- **Commit regularly:** After each logical change
- **ALWAYS push:** `git push` after every commit (backup protection)
- **Update README:** With every commit
- **GitHub push:** Use SSH (`git@github.com:unieksolutions/repo.git`) — `id_ed25519` key is linked to the unieksolutions account. HTTPS + PAT fails due to credential.helper=store conflicts.
- **PAT location:** `/opt/tools/.env` (fallback reference only — prefer SSH)
- **Commit messages:** Clear, concise, explain WHY not just WHAT

### Backups
- **Before modifying:** Create snapshot in `/opt/backups/{project}_{datetime}/`
- **Backup tool:** `/opt/projects/scripts/backup_snapshot.sh <path>`
- **Timestamp format:** Canonical NL (YYYY-MM-DDThh-mm)
- **Include metadata:** `.backup_info` with git hash, repo URL, source path

### Command Execution
- **NEVER sudo:** CLI agents hang with sudo commands
- **When sudo needed:** Write exact command, ask user to run it, wait for output
- **Do yourself:** Don't ask user to run what agent can execute
- **Port scanning:** ALWAYS scan before starting new services

### External Resources
- **SPI Manager (WLM):** `http://localhost:63115` (prod) / `http://localhost:61115` (dev)
  - **⚠️ MANDATORY:** ALL AI/GPU requests MUST go through spi-manager (:65000)
  - **NEVER** call backends directly (Parkiet :65400, ComfyUI :61620, etc.)
  - **Why:** spi-manager tracks ALL resources (VRAM, RAM, CPU, disk) + start/stop services
  - Include `agent_id` in all requests for tracking
  - API docs: `/opt/projects/spi-manager/API.md`
  - Architecture: `/opt/projects/spi-manager/ARCHITECTURE.md` (resource management principle)
  - Service discovery: `GET /registry/services` (find neo4j, chromadb, rocketchat, etc.)
- **Shared config:** `/opt/tools/.env` for credentials
- **Virtual env:** `/opt/tools/venv` for Python (check existing packages first)
- **PHP CLI:** Installed system-wide for linting/tests
- **SSL certs:** `/opt/tools/ssl/` (see README.md for framework setup)

### Development Environment
- **Source of truth:** `/opt/projects/{project}` (development)
- **Acceptance:** `/opt/accept/{project}` (staging)
- **Production:** `/opt/tools/{project}` or `/opt/products/{project}`
- **Deploy via scripts:** Never write directly to accept/production

### Deployment Security (CRITICAL)
- **NO .md files in deployment:** Project docs stay in /opt/projects ONLY
  - Exclude: `--exclude '*.md'` in rsync
  - Exception: User-facing docs (user guides, help pages)
- **Secrets management — `.env.example` pattern (NOT SECRETS.md):**
  - `.env.example` — variable names + placeholders, **commit this** ✓
  - `.env` — real values, **always gitignored** ✗
  - Production secrets → platform secret store (Render dashboard, Railway vars, Vault)
  - Document secret *locations* in DEPLOY.md, never the values
  - **SECRETS.md is deprecated** — do not create, do not use. Real risk: ends up on GitHub.

### Web Development
- **Default:** Responsive web interfaces
- **Design system:** Follow `/opt/bootstrap/DESIGN.md`
- **Multilingual:** Support NL as default (see DESIGN.md)
- **Accessibility:** WCAG 2.1 AA minimum

### Testing
- **Before deployment:** Test in development environment
- **Migration testing:** Test with existing data/users
- **Rollback plan:** Document in DEPLOY.md before deploying

### Temporary Files & Cleanup
- **Naming convention:** Use `_test` or `_temp` suffix for temporary files
  - Examples: `config_test.yaml`, `backup_temp.sql`, `output_test.txt`
- **After testing:** Either move to `/opt/backups/` OR delete completely
- **Never leave behind:** Clean up temp files before finishing work
- **Pattern to find:** `find . -name "*_test*" -o -name "*_temp*"`
- **Session end:** Remove ALL temporary files created during session

### Documentation
- **Bootstrap structure:** Use templates from `/opt/bootstrap/`
- **File limit:** ~15K tokens per file
- **Don't create new:** Update existing bootstrap docs
- **Reference details:** Link to specific sections, don't duplicate

## Key References

For detailed information, see:
- **Shared tools:** `/opt/bootstrap/TOOLS.md`
- **API/MCP patterns:** `/opt/bootstrap/APIMCP.md`
- **Port allocation:** `/opt/bootstrap/PORTS.md`
- **Deployment workflows:** `/opt/bootstrap/DEPLOY.md`
- **Design/UX:** `/opt/bootstrap/DESIGN.md`
- **SPI Manager API:** `/opt/projects/spi-manager/API.md`
- **Project bootstrap:** `/opt/bootstrap/START.md`

## Quick Commands

```bash
# Create backup
/opt/tools/scripts/backup_snapshot.sh /opt/projects/myproject

# Scan ports
ss -tlnp | grep :61

# Check service status
systemctl status myservice

# Git workflow
git add -A && git commit -m "message" && git push

# SPI Manager health (dev)
curl http://localhost:61115/health

# SPI Manager health (prod)
curl http://localhost:63115/health
```

## Deploy Checklist — Verplicht voor alle projecten

Elke agent die DEPLOY.md schrijft of `run_deploy` uitvoert MOET dit volgen.

### 1. deploy_cmd vereisten

```bash
# Correct — env vars mee, venv-pad, log naar bestand, process-check daarna
USE_MEMORY_STORE=true nohup /pad/naar/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port PORT &> /pad/naar/app.log &
sleep 3 && ss -tlnp | grep :PORT || echo "FAILED: process not listening"
```

- **Altijd:** absoluut pad naar venv python (`/opt/projects/.../venv/bin/python`)
- **Altijd:** `&> app.log &` — stdout én stderr loggen, proces in background
- **Altijd:** process-check na 3s — `ss -tlnp | grep :PORT`
- **Nooit:** exit code van `nohup` vertrouwen (altijd 0, ook bij crash)

### 2. Env vars — contract

| App gebruikt | deploy_cmd moet |
|---|---|
| `os.getenv()` zonder `load_dotenv()` | Env vars expliciet exporteren in cmd |
| `load_dotenv()` | `.env` aanwezig zijn met alle verplichte vars |
| Beide | Beide bovenstaande |

**Regel:** Als `DATABASE_URL`, `USE_MEMORY_STORE` of andere verplichte vars bestaan → staan ze in deploy_cmd of `.env`. Nooit veronderstellen dat ze al gezet zijn.

### 3. DEPLOY.md verplichte velden

```markdown
| deploy_cmd  | `USE_VAR=val nohup /venv/bin/python -m uvicorn ... &> app.log &` |
| health_url  | `http://localhost:PORT/health`  |
| port        | PORT                            |
| rollback_cmd| `pkill -f "uvicorn app.main" \|\| true` |
```

`health_url` is **verplicht** — zonder health_url scoort observe altijd 50 of lager.

### 4. Process-verificatie in deploy_cmd

Na de nohup-regel altijd een check:

```bash
sleep 3 && curl -sf http://localhost:PORT/health || \
  (echo "DEPLOY FAILED — check app.log:"; tail -20 app.log; exit 1)
```

Als de check faalt → deploy_cmd geeft non-zero exit → EDE registreert als failure.

### 5. Bekende valkuilen

❌ `nohup cmd &` — exit 0 betekent niets, process kan direct crashen
❌ `.env` aanmaken maar app laadt hem niet (`load_dotenv()` vergeten)
❌ Relatief pad in deploy_cmd (`venv/bin/python`) — werkt niet vanuit systemd
❌ Port hardcoden in app.main — altijd via `os.getenv("PORT", "DEFAULT")`
❌ health_url weglaten uit DEPLOY.md — observe kan niet meten

## Common Mistakes to Avoid

❌ Running sudo in CLI agents (hangs)
❌ Running systemctl in CLI agents (not allowed)
❌ Forgetting to push after commit (no backup)
❌ Starting service without scanning ports (conflicts)
❌ Writing to /opt/accept or /opt/products directly (use deploy scripts)
❌ Creating new .md files (update existing bootstrap docs)
❌ Hardcoding credentials (use /opt/{stage}/{projectname}/.env or SECRETS.md)
❌ Single environment database (split dev/staging/prod)
❌ Skipping migration testing (breaks existing data)

---

**Last Updated:** 2026-01-08
**Maintained by:** SPI Development Team

---

## Feature Flags - MANDATORY for Production Services

**CRITICAL:** All services deployed to `/opt/products/` MUST implement feature flags.

### Why This Is Mandatory

Feature flags enable:
- Automated testing with features enabled/disabled
- Safe deployments (rollback without code changes)
- A/B testing and gradual rollouts
- Emergency killswitch for broken features

### Minimum Implementation

Every production service MUST have:

1. **config/feature_flags.yaml** - Feature flag definitions
2. **Feature flag library** - Code to check flags (see ARCHITECTURE.md)
3. **Admin API** - Endpoints to view/toggle flags
4. **Tests** - Use feature flag overrides in tests

### Example Structure

```
/opt/products/myservice/
├── config/
│   └── feature_flags.yaml        # ← REQUIRED
├── utils/
│   └── feature_flags.py          # ← REQUIRED
├── api/
│   └── admin_features.py         # ← REQUIRED (admin endpoints)
└── tests/
    └── test_features.py          # ← REQUIRED (flag tests)
```

### Deployment Validation

Before `deploy_accept_to_prod.sh`:
- Script CHECKS for `config/feature_flags.yaml`
- Script FAILS if feature flags not implemented
- Script VERIFIES admin API responds

### Non-Compliance

Services without feature flags:
- ❌ Cannot deploy to `/opt/products/`
- ❌ Cannot pass acceptance testing
- ❌ Blocked by deployment scripts

See `/opt/bootstrap/ARCHITECTURE.md` for full implementation guide.

---

## IAM Application Registration (M2M / client_credentials)

### Regel: agents registreren zichzelf niet

Alleen de **IAM-agent** mag applicaties registreren in uNiek IAM via de Management API.
Andere agents vragen registratie aan via een mens of via een gestructureerde taak.

**Nooit doen:**
- De `MANAGEMENT_API_TOKEN` opvragen in een agent-prompt
- De token opslaan in `.md` bestanden, git, of agent-context
- Registraties uitvoeren vanuit een niet-IAM agent

**Correct patroon:**
1. Agent-prompt beschrijft: naam, base_url, benodigde scopes
2. Mens vraagt de IAM-agent om de registratie uit te voeren
3. IAM-agent haalt token op uit `/opt/tools/.env` (sleutel: `IAM_MANAGEMENT_TOKEN`)
4. IAM-agent geeft `client_id` + `client_secret` terug aan mens
5. Mens plaatst credentials in `.env` van de betreffende service

**Token endpoint (M2M):**
```
POST https://unieksolutions.nl/iam/api/v1/oauth2/token
grant_type=client_credentials
client_id=<client_id>
client_secret=<client_secret>
scope=<scopes>
```

**Credentials opslaan:** altijd in `.env` van de service, nooit in `.md` of git.

Zie `/opt/bootstrap/INTEGRATION.md` voor het volledige integratie-patroon.

