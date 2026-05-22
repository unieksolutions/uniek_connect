<!--
ts: 2025-05-21T00:00:00Z | git: <to-be-filled> | path: /opt/projects/uniek_connect
-->
# BACKLOG

Work items for uNiek Connect - Central OAuth Connector Service

**⚠️ IMPORTANT:** All items in this BACKLOG.md should be synchronized with the ticket service.
**Ticket service is leading** - use the API to create, update, and manage work items:

- **API Base:** `http://192.168.42.21:5401`
- **Web UI:** `http://192.168.42.21:5549`
- **List tickets:** `GET /tickets?project=uniek_connect&state=todo,doing`
- **Create ticket:** `POST /tickets` with JSON body
- **Update ticket:** `PATCH /tickets/{ticket_id}` with JSON body
- **Get ticket:** `GET /tickets/{ticket_id}`

Sync this file with tickets API regularly to keep work visible in both places.

## Priority Queue

### High Priority - Phase 1: Core Infrastructure

#### UC-001: Architecture & Design ✅
- [x] Design OAuth flow architecture (web-based authorization, token storage)
- [x] Design database schema (oauth_tokens, token_scopes, connected_accounts)
- [x] Design API endpoints (auth flows, token retrieval, data fetching)
- [x] Document security model (encryption at rest, token rotation)
- [x] Define multi-tenant strategy (user isolation, organization support)

#### UC-002: FastAPI Skeleton ✅
- [x] Create Python venv with FastAPI dependencies
- [x] Implement config.py (Pydantic settings from .env)
- [x] Implement database.py (SQLAlchemy models)
- [x] Implement main.py (FastAPI app with lifespan, CORS)
- [x] Create health endpoint
- [x] Test skeleton on port 61300

#### UC-003: Google OAuth Connector
- [ ] Register OAuth app in Google Cloud Console
- [ ] Configure OAuth scopes (Calendar, Tasks read/write)
- [ ] Implement /auth/google/login endpoint
- [ ] Implement /auth/google/callback endpoint
- [ ] Implement token storage in database
- [ ] Implement token refresh logic
- [ ] Test with niek@uniek.solutions account

#### UC-004: Google Calendar Connector
- [ ] Implement Google Calendar API client
- [ ] Create /calendars/google endpoint (list calendars)
- [ ] Create /calendars/google/{id}/events endpoint (get events)
- [ ] Implement date range filtering
- [ ] Test with real Google account

#### UC-005: Google Tasks Connector
- [ ] Implement Google Tasks API client
- [ ] Create /tasks/google endpoint (list task lists)
- [ ] Create /tasks/google/{id}/items endpoint (get tasks)
- [ ] Implement status filtering (pending, completed)
- [ ] Test with real Google account

### Medium Priority - Phase 1: Microsoft Support

#### UC-006: Microsoft OAuth Connector
- [ ] Register OAuth app in Azure/Entra
- [ ] Configure OAuth scopes (Calendar, Tasks read/write)
- [ ] Implement /auth/microsoft/login endpoint
- [ ] Implement /auth/microsoft/callback endpoint
- [ ] Implement token storage (same schema as Google)
- [ ] Test with Microsoft 365 account

#### UC-007: Microsoft Calendar Connector
- [ ] Implement Microsoft Graph API client
- [ ] Create /calendars/microsoft endpoint (list calendars)
- [ ] Create /calendars/microsoft/{id}/events endpoint (get events)
- [ ] Implement date range filtering
- [ ] Test with real Microsoft 365 account

#### UC-008: Microsoft To Do Connector
- [ ] Implement Microsoft Graph API client for Tasks
- [ ] Create /tasks/microsoft endpoint (list task lists)
- [ ] Create /tasks/microsoft/{id}/items endpoint (get tasks)
- [ ] Implement status filtering
- [ ] Test with real Microsoft 365 account

### Medium Priority - Phase 1: Token API

#### UC-009: Token Retrieval API
- [ ] Create /api/tokens/{provider}/{account} endpoint
- [ ] Implement token validation (check expiry)
- [ ] Implement automatic token refresh
- [ ] Add authentication (API key or session)
- [ ] Document API for consuming projects

#### UC-010: Token Management UI
- [ ] Create simple web UI for OAuth authorization
- [ ] Show connected accounts
- [ ] Show token status (valid, expired, revoked)
- [ ] Allow manual token revocation
- [ ] Test on mobile (responsive design)

### Low Priority - Phase 2: Apple & Nextcloud

#### UC-011: Apple Calendar & Reminders
- [ ] Research Apple CalDAV/CardDAV API
- [ ] Implement Apple OAuth (if available) or app-specific passwords
- [ ] Implement calendar connector
- [ ] Implement reminders connector
- [ ] Test with real Apple account

#### UC-012: Nextcloud Calendar & Tasks
- [ ] Research Nextcloud CalDAV/CardDAV API
- [ ] Implement OAuth or username/password auth
- [ ] Implement calendar connector
- [ ] Implement tasks connector
- [ ] Test with Nextcloud instance

### Future - Phase 3: Communication Channels

#### UC-013: Email Connectors (Architecture)
- [ ] Research integration with existing channels in uNiek ecosystem
- [ ] Design architecture for email as channel (agents, GMR, humans)
- [ ] Define scope: read-only vs read/write
- [ ] Consider Gmail API, Microsoft Graph (Outlook), IMAP/SMTP

#### UC-014: Messaging Connectors (Architecture)
- [ ] Research integration with existing WhatsApp/Telegram bridges
- [ ] Define scope: extract tasks/deadlines vs full channel access
- [ ] Consider privacy and security implications

## Completed
- [x] UC-000: Bootstrap project structure from /opt/bootstrap templates (2025-05-21)
- [x] UC-001: Architecture & Design - OAuth flows, database schema, API specs, security model (2025-05-21)
- [x] UC-002: FastAPI skeleton - config, database models, app setup, health endpoint (2025-05-22)
