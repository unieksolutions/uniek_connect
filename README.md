<!--
ts: 2025-05-21T00:00:00Z | git: <to-be-filled> | path: /opt/projects/uniek_connect
-->

# uNiek Connect

Central OAuth connector service for external APIs (calendars, tasks, email, messaging)

## Project Overview

**Status:** Bootstrap Complete
**Purpose:** Centralized OAuth token management and API connectors for Google, Microsoft, Apple, Nextcloud
**Repository:** https://github.com/unieksolutions/uniek_connect
**Development:** `/opt/projects/uniek_connect` (source of truth)
**Production:** `/opt/products/uniek_connect`

## Phase 1: Core Connectors
- **Calendars:** Google, Microsoft 365, Apple, Nextcloud
- **Task Lists:** Google Tasks, Microsoft To Do, Apple Reminders, Nextcloud Tasks
- **Goal:** Extract tasks and deadlines for AI priority scoring

## Phase 2: Communication Channels (Future)
- Email, WhatsApp, Telegram (integration with existing channels)

## Documentation

- [START.md](START.md) - Bootstrap instructions and file index
- [STATUS.md](STATUS.md) - Current project status and progress
- [BACKLOG.md](BACKLOG.md) - Prioritized work items
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design and system architecture
- [DESIGN.md](DESIGN.md) - UI/UX specifications
- [VERSIONS.md](VERSIONS.md) - Multi-environment version tracking
- [DEPLOY.md](DEPLOY.md) - Deployment procedures per environment
- [SECRETS.md](SECRETS.md) - Credential locations and access per environment
- [APIMCP.md](APIMCP.md) - API and MCP implementation details

## Quick Start

```bash
cd /opt/projects/uniek_connect
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with OAuth credentials
python -m api.main
```

**Ports:** 61300 (dev), 61301 (accept), 61302 (prod)

## Standards

**Language:**
- English for code and documentation
- UI multilingual (NL default)

**Source of Truth:**
- Development: `/opt/projects/uniek_connect`
- See VERSIONS.md for staging/production locations

**Ticket Integration:**
- All work items tracked in `/opt/tickets` service
- BACKLOG.md synced with ticket service
