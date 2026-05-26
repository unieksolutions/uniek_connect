<!--
ts: 2025-05-21T00:00:00Z | git: <to-be-filled> | path: /opt/projects/uniek_connect
-->
# STATUS

**Last Updated:** 2025-05-22
**Status:** Phase 1 - Google Connector Implementation

## Current State

### ✅ Completed
- **UC-000:** Project structure bootstrapped from /opt/bootstrap templates
- **UC-001:** Architecture & Design complete
  - 5 ADRs documented (central service, web OAuth, encryption, PostgreSQL, RESTful API)
  - System architecture diagram
  - OAuth 2.0 flow design (authorization + token refresh)
  - Database schema: 5 tables (organizations, users, oauth_tokens, api_keys, audit_logs)
  - API endpoint specifications (OAuth, tokens, calendars, tasks, admin)
  - Security model: 7 controls
  - Multi-tenant strategy with MVP path
- **UC-002:** FastAPI skeleton implementation complete
  - Python venv with 43 dependencies (FastAPI, SQLAlchemy, OAuth libs)
  - config.py: Pydantic settings (database, OAuth, CORS, logging)
  - database.py: 5 SQLAlchemy models with indexes
  - main.py: FastAPI app with lifespan, CORS middleware
  - Health + root endpoints working on port 61300
  - Fernet encryption key generated for token security
  - Default organization + user seeded in database
- **UC-003:** Google OAuth connector complete
  - OAuth login endpoint: `GET /auth/google/login`
  - OAuth callback endpoint: `GET /auth/google/callback`
  - OAuth revoke endpoint: `DELETE /auth/google/revoke`
  - Token encryption/decryption helpers (Fernet AES-128)
  - Token retrieval API: `GET /api/tokens/google/{email}`
  - Token status check: `GET /api/tokens/google/{email}/status`
  - Automatic token refresh on expiration
  - CSRF protection via session state validation
  - Session middleware added (itsdangerous)
- **UC-004:** Google Calendar connector complete
  - List calendars: `GET /calendars/google?account_email={email}`
  - List events: `GET /calendars/google/{id}/events?account_email={email}`
  - Get single event: `GET /calendars/google/{id}/events/{event_id}?account_email={email}`
  - Date range filtering (time_min, time_max parameters)
  - All-day event support
  - Attendee information included
- **UC-005:** Google Tasks connector complete
  - List task lists: `GET /tasks/google?account_email={email}`
  - List tasks: `GET /tasks/google/{tasklist_id}/items?account_email={email}`
  - Get single task: `GET /tasks/google/{tasklist_id}/items/{task_id}?account_email={email}`
  - List subtasks: `GET /tasks/google/{tasklist_id}/items/{task_id}/subtasks?account_email={email}`
  - Status filtering (needsAction, completed)
  - Show completed/hidden filters
  - Subtask hierarchy support
- **UC-006:** Microsoft OAuth connector complete
  - OAuth login endpoint: `GET /auth/microsoft/login`
  - OAuth callback endpoint: `GET /auth/microsoft/callback`
  - OAuth revoke endpoint: `DELETE /auth/microsoft/revoke`
  - Token encryption/decryption (Fernet AES-128)
  - Token retrieval API: `GET /api/tokens/microsoft/{email}`
  - Token status check: `GET /api/tokens/microsoft/{email}/status`
  - Automatic token refresh with MSAL
  - CSRF protection via session state
  - Microsoft Graph scopes (Calendars.Read, Tasks.Read, User.Read)
- README.md filled with project overview
- BACKLOG.md populated with 14 work items
- Port allocation: 61300 (dev), 61301 (accept), 61302 (prod)

### 🚧 In Progress
- **UC-007:** Microsoft Calendar connector (next)

### ⏳ Planned
- Microsoft Calendar + To Do connectors (UC-007, UC-008)
- Token retrieval API (UC-009)
- Token management UI (UC-010)

## Architecture Decisions

### ADR-001: Central OAuth Service (Pending)
**Context:** Multiple uNiek Solutions projects need OAuth access to Google/Microsoft APIs
**Decision:** Build reusable connector service instead of per-project OAuth implementations
**Status:** Accepted
**Consequences:**
- Single OAuth implementation for all projects
- Centralized token management and security
- Projects request tokens via API instead of implementing OAuth flows
- Requires multi-tenant support from the start

## Next Steps
1. Fill ARCHITECTURE.md with OAuth flow design
2. Fill BACKLOG.md with Phase 1 tasks
3. Design database schema for token storage
4. Design API endpoints for token retrieval
5. Start implementation with Google connector

## Issues & Blockers
None currently
