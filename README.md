<!--
ts: 2025-05-21T00:00:00Z | git: <to-be-filled> | path: /opt/projects/uniek_connect
-->

# uNiek Connect

Central OAuth connector service for external APIs (calendars, tasks, email, messaging)

## Project Overview

**Status:** Phase 1 In Progress - Google & Microsoft Connectors Complete
**Purpose:** Centralized OAuth token management and API connectors for Google, Microsoft, Apple, Nextcloud
**Repository:** https://github.com/unieksolutions/uniek_connect
**Development:** `/opt/projects/uniek_connect` (source of truth)
**Integration:** This code will be copied to `/opt/projects/organaizer/oauth-connector` for local use
**Production:** `/opt/products/uniek_connect` (future multi-tenant SaaS)

## ✅ Implemented (Phase 1)

### Google Connectors
- **OAuth 2.0** - Authorization flow with automatic token refresh
- **Calendar API** - List calendars, events, date filtering, attendees
- **Tasks API** - List task lists, tasks, subtasks, status filtering

### Microsoft Connectors
- **OAuth 2.0 (MSAL)** - Authorization flow with Graph API integration
- **Calendar API** - List calendars, events, OData filtering, attendees
- **To Do API** - _In progress (UC-008)_

### Token Management
- **Automatic Refresh** - Expired tokens refreshed automatically
- **Encryption** - Refresh tokens encrypted at rest (Fernet AES-128)
- **Token API** - Retrieve valid access tokens for consuming services

## 🚧 Planned (Phase 1)

### Apple & Nextcloud
- **Apple Calendar & Reminders** - CalDAV/CardDAV integration
- **Nextcloud Calendar & Tasks** - CalDAV/CardDAV integration

## 📋 Future (Phase 2)
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

## API Endpoints

### OAuth Authorization
- `GET /auth/google/login` - Initiate Google OAuth flow
- `GET /auth/google/callback` - Google OAuth callback
- `DELETE /auth/google/revoke?account_email={email}` - Revoke Google token
- `GET /auth/microsoft/login` - Initiate Microsoft OAuth flow
- `GET /auth/microsoft/callback` - Microsoft OAuth callback
- `DELETE /auth/microsoft/revoke?account_email={email}` - Revoke Microsoft token

### Token Management
- `GET /api/tokens/{provider}/{account_email}` - Get valid access token (auto-refresh)
- `GET /api/tokens/{provider}/{account_email}/status` - Check token status

### Google Calendar
- `GET /calendars/google?account_email={email}` - List calendars
- `GET /calendars/google/{calendar_id}/events?account_email={email}` - List events
- `GET /calendars/google/{calendar_id}/events/{event_id}?account_email={email}` - Get event

### Google Tasks
- `GET /tasks/google?account_email={email}` - List task lists
- `GET /tasks/google/{tasklist_id}/items?account_email={email}` - List tasks
- `GET /tasks/google/{tasklist_id}/items/{task_id}?account_email={email}` - Get task
- `GET /tasks/google/{tasklist_id}/items/{task_id}/subtasks?account_email={email}` - List subtasks

### Microsoft Calendar
- `GET /calendars/microsoft?account_email={email}` - List calendars
- `GET /calendars/microsoft/{calendar_id}/events?account_email={email}` - List events
- `GET /calendars/microsoft/{calendar_id}/events/{event_id}?account_email={email}` - Get event

**Interactive API Docs:** http://localhost:61300/docs

## Deployment Options

### Option A: Standalone (Current)
Run as independent service for development/testing:

### Option B: Integrated in Organaizer (Recommended)
Copy to Organaizer project as subcomponent:
```bash
cp -r /opt/projects/uniek_connect /opt/projects/organaizer/oauth-connector
```
See `/opt/projects/organaizer/docs/OAUTH_CONNECTOR_SETUP.md` for full integration guide.

## Quick Start

```bash
cd /opt/projects/uniek_connect
source venv/bin/activate  # venv already exists
python -m api.main
```

**Server:** http://localhost:61300
**API Docs:** http://localhost:61300/docs
**Health:** http://localhost:61300/health

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
