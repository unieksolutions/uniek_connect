<!--
ts: 2025-05-21T00:00:00Z | git: <to-be-filled> | path: /opt/projects/uniek_connect
-->

# ARCHITECTURE

uNiek Connect - Central OAuth Connector Service

## System Overview

**Purpose:** Centralized OAuth token management and API connector service for external platforms (Google, Microsoft, Apple, Nextcloud)

**Core Responsibilities:**
1. OAuth 2.0 authorization flows for multiple providers
2. Secure token storage with encryption at rest
3. Automatic token refresh before expiration
4. API for token retrieval by consuming services
5. Data fetching endpoints (calendars, tasks, email)
6. Multi-tenant support for organizations and users

**Technology Stack:**
- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (production) / SQLite (development)
- **OAuth Libraries:** google-auth, microsoft-authentication-library
- **Encryption:** cryptography (Fernet symmetric encryption)
- **Task Scheduler:** APScheduler (token refresh background jobs)
- **Web Server:** Uvicorn (ASGI)

## Architecture Decisions (ADRs)

### ADR-001: Central OAuth Service
**Date:** 2025-05-21
**Status:** Accepted
**Context:** Multiple uNiek Solutions projects (Organaizer, uniek_iam, future services) need OAuth access to Google/Microsoft APIs
**Decision:** Build centralized connector service instead of per-project OAuth implementations
**Consequences:**
- ✅ Single OAuth implementation maintained in one place
- ✅ Consistent security model across all projects
- ✅ Easier to add new providers (Apple, Nextcloud)
- ✅ Centralized token management and monitoring
- ⚠️ Single point of failure (mitigated by high availability)
- ⚠️ Requires multi-tenant support from day 1

### ADR-002: Web-Based OAuth Flow (Not Desktop)
**Date:** 2025-05-21
**Status:** Accepted
**Context:** OAuth can be done via web redirects or embedded browser
**Decision:** Use standard web-based OAuth with redirect URLs
**Consequences:**
- ✅ Standard OAuth 2.0 flow (no special requirements)
- ✅ Works on all devices (desktop, mobile, tablet)
- ✅ No embedded browser dependencies
- ✅ User sees official Google/Microsoft login pages
- ⚠️ Requires web UI for authorization flow

### ADR-003: Token Encryption at Rest
**Date:** 2025-05-21
**Status:** Accepted
**Context:** OAuth tokens grant access to user data
**Decision:** Encrypt refresh tokens at rest using Fernet (AES-128)
**Consequences:**
- ✅ Tokens protected if database is compromised
- ✅ Symmetric encryption (fast, simple key management)
- ⚠️ Encryption key must be securely stored (env variable)
- ⚠️ Key rotation requires re-encrypting all tokens

### ADR-004: PostgreSQL for Production
**Date:** 2025-05-21
**Status:** Accepted
**Context:** Need reliable database with ACID guarantees
**Decision:** PostgreSQL for production, SQLite for development
**Consequences:**
- ✅ Reliable, battle-tested database
- ✅ Strong consistency guarantees
- ✅ Support for row-level locking (token refresh)
- ✅ SQLite for local development (no setup needed)
- ⚠️ Need PostgreSQL instance on SPI

### ADR-005: RESTful API (Not GraphQL)
**Date:** 2025-05-21
**Status:** Accepted
**Context:** API design for token retrieval and data fetching
**Decision:** RESTful API with clear resource endpoints
**Consequences:**
- ✅ Simple, well-understood API design
- ✅ Easy to document and test
- ✅ Standard HTTP caching works out of the box
- ✅ FastAPI has excellent REST support
- ⚠️ No flexible queries (vs GraphQL)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Consuming Services                           │
│  (Organaizer, uniek_iam, future apps)                          │
└────────────┬───────────────────────────────────────────────────┘
             │ API calls
             │ GET /api/tokens/{provider}/{account}
             │ GET /calendars/{provider}
             │ GET /tasks/{provider}
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    uNiek Connect (FastAPI)                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ OAuth Routes │  │ Token API    │  │ Data Fetch Routes    │ │
│  │ /auth/*/     │  │ /api/tokens/ │  │ /calendars /tasks    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘ │
│         │                  │                  │                 │
│  ┌──────▼──────────────────▼──────────────────▼──────────────┐ │
│  │               Token Manager                                │ │
│  │  - Validate tokens                                         │ │
│  │  - Refresh if expired                                      │ │
│  │  - Encrypt/decrypt                                         │ │
│  └──────┬───────────────────────────────────────────────────┬┘ │
│         │                                                     │  │
│  ┌──────▼──────────┐  ┌──────────────────────┐  ┌──────────▼┐ │
│  │ OAuth Providers │  │  Background Scheduler │  │  Database │ │
│  │ - Google        │  │  - Proactive refresh  │  │  Manager  │ │
│  │ - Microsoft     │  │  - Cleanup expired    │  └───────────┘ │
│  │ - Apple         │  └───────────────────────┘                │
│  │ - Nextcloud     │                                            │
│  └─────────────────┘                                            │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ OAuth callbacks
             │ Token storage (encrypted)
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                          │
│                                                                 │
│  Tables:                                                        │
│  - oauth_tokens     (encrypted refresh tokens)                 │
│  - token_scopes     (granted permissions)                      │
│  - connected_accounts (user → provider mappings)               │
│  - organizations    (multi-tenant support)                     │
└─────────────────────────────────────────────────────────────────┘

External OAuth Providers:
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Google  │  │Microsoft │  │  Apple   │  │Nextcloud │
│   APIs   │  │  Graph   │  │ CalDAV   │  │  APIs    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Components

#### 1. OAuth Routes (`/auth/{provider}/`)
- **Login Endpoint:** Generates OAuth authorization URL
- **Callback Endpoint:** Receives authorization code, exchanges for tokens
- **Revoke Endpoint:** Revokes tokens and deletes from database

#### 2. Token API (`/api/tokens/`)
- **Token Retrieval:** Returns valid access token for provider/account
- **Token Validation:** Checks expiry, refreshes if needed
- **Token Status:** Reports token health (valid, expired, revoked)

#### 3. Data Fetch Routes
- **Calendars:** List calendars and events (read-only or read/write)
- **Tasks:** List task lists and tasks (read-only or read/write)
- **Email (Phase 3):** Fetch emails, send emails
- **Messaging (Phase 3):** Send/receive messages

#### 4. Token Manager (Core Logic)
- **Encryption:** Encrypt refresh tokens before storing
- **Decryption:** Decrypt tokens when needed
- **Refresh Logic:** Automatically refresh tokens 5 minutes before expiry
- **Error Handling:** Handle revoked tokens, expired tokens, API errors

#### 5. Background Scheduler (APScheduler)
- **Proactive Refresh:** Check all tokens every 10 minutes, refresh if needed
- **Cleanup:** Delete expired tokens older than 90 days
- **Health Monitoring:** Log token status for monitoring

#### 6. OAuth Providers (Adapters)
- **Google:** google-auth-oauthlib + google-api-python-client
- **Microsoft:** msal (Microsoft Authentication Library)
- **Apple:** CalDAV/CardDAV protocol (if available)
- **Nextcloud:** CalDAV/CardDAV + Nextcloud API

---

## OAuth Flow Design

### Standard OAuth 2.0 Authorization Code Flow

```
User Browser          uNiek Connect         Google/Microsoft
     │                      │                       │
     │  1. Click "Connect"  │                       │
     │─────────────────────>│                       │
     │                      │                       │
     │  2. Redirect to      │                       │
     │     OAuth provider   │                       │
     │<─────────────────────│                       │
     │                      │                       │
     │  3. User logs in     │                       │
     │─────────────────────────────────────────────>│
     │                      │                       │
     │  4. Authorization    │                       │
     │     consent screen   │                       │
     │<─────────────────────────────────────────────│
     │                      │                       │
     │  5. User approves    │                       │
     │─────────────────────────────────────────────>│
     │                      │                       │
     │  6. Redirect back    │                       │
     │     with auth code   │                       │
     │<─────────────────────────────────────────────│
     │                      │                       │
     │  7. Auth code        │                       │
     │─────────────────────>│                       │
     │                      │                       │
     │                      │  8. Exchange code     │
     │                      │      for tokens       │
     │                      │──────────────────────>│
     │                      │                       │
     │                      │  9. Access + Refresh  │
     │                      │<──────────────────────│
     │                      │                       │
     │                      │ 10. Store tokens      │
     │                      │     (encrypted)       │
     │                      │──>[Database]          │
     │                      │                       │
     │  11. Success page    │                       │
     │<─────────────────────│                       │
```

### Flow Steps

**Step 1-2: Initiate Authorization**
```python
GET /auth/google/login?user_id=123&redirect_after=/dashboard

Response: 302 Redirect
Location: https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=...
  &redirect_uri=https://uniek-connect.spi.local/auth/google/callback
  &scope=https://www.googleapis.com/auth/calendar.readonly+...
  &response_type=code
  &state=encrypted_session_token
```

**Step 3-6: User Authorization (on Google/Microsoft site)**
- User logs in with their credentials
- User sees consent screen listing requested permissions
- User approves access
- Provider redirects back with authorization code

**Step 7-9: Token Exchange**
```python
GET /auth/google/callback?code=AUTH_CODE&state=SESSION_TOKEN

Backend:
1. Validate state token (CSRF protection)
2. Exchange auth code for tokens via Google API
3. Receive access_token (1 hour TTL) + refresh_token (permanent)
4. Encrypt refresh_token with Fernet
5. Store in database (oauth_tokens table)
6. Redirect user to success page
```

**Step 10-11: Token Storage**
```sql
INSERT INTO oauth_tokens (
  user_id,
  provider,
  account_email,
  access_token,
  refresh_token_encrypted,  -- Fernet encrypted
  token_expiry,
  scopes,
  created_at
) VALUES (
  123,
  'google',
  'user@example.com',
  'ya29.a0AfH6SMB...',
  'gAAAAABf3K9...',  -- Encrypted
  NOW() + INTERVAL '1 hour',
  'calendar.readonly,tasks.readonly',
  NOW()
);
```

### Token Refresh Flow

```
Consuming Service    uNiek Connect         Google/Microsoft
     │                      │                       │
     │  1. Request token    │                       │
     │─────────────────────>│                       │
     │                      │                       │
     │                      │  2. Check expiry      │
     │                      │─────>[Database]       │
     │                      │                       │
     │                      │  3. Token expired?    │
     │                      │      YES              │
     │                      │                       │
     │                      │  4. Decrypt refresh   │
     │                      │     token             │
     │                      │                       │
     │                      │  5. Request new token │
     │                      │──────────────────────>│
     │                      │                       │
     │                      │  6. New access token  │
     │                      │<──────────────────────│
     │                      │                       │
     │                      │  7. Update database   │
     │                      │─────>[Database]       │
     │                      │                       │
     │  8. Return token     │                       │
     │<─────────────────────│                       │
```

---

## Database Schema

### Table: `organizations`
Multi-tenant support - groups of users

```sql
CREATE TABLE organizations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
```

### Table: `users`
Users within organizations

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(organization_id, email)
);

CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
```

### Table: `oauth_tokens`
OAuth tokens for external providers

```sql
CREATE TABLE oauth_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,  -- 'google', 'microsoft', 'apple', 'nextcloud'
  account_email VARCHAR(255) NOT NULL,  -- Email of connected account

  -- Tokens
  access_token TEXT NOT NULL,
  refresh_token_encrypted TEXT,  -- Fernet encrypted
  token_expiry TIMESTAMP NOT NULL,

  -- Metadata
  scopes TEXT,  -- Comma-separated list
  token_type VARCHAR(50) DEFAULT 'Bearer',

  -- Status
  is_valid BOOLEAN DEFAULT TRUE,
  last_refresh_at TIMESTAMP,
  revoked_at TIMESTAMP,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, provider, account_email)
);

CREATE INDEX idx_oauth_tokens_user ON oauth_tokens(user_id);
CREATE INDEX idx_oauth_tokens_provider ON oauth_tokens(provider);
CREATE INDEX idx_oauth_tokens_expiry ON oauth_tokens(token_expiry);
CREATE INDEX idx_oauth_tokens_valid ON oauth_tokens(is_valid) WHERE is_valid = TRUE;
```

### Table: `api_keys`
API keys for consuming services to authenticate

```sql
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
  key_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA256 hash
  key_prefix VARCHAR(10) NOT NULL,  -- First 8 chars for identification
  name VARCHAR(255) NOT NULL,  -- "Organaizer API Key"

  -- Permissions
  scopes TEXT,  -- Comma-separated: 'tokens.read', 'calendars.read', etc.

  -- Status
  is_active BOOLEAN DEFAULT TRUE,
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_org ON api_keys(organization_id);
```

### Table: `audit_logs`
Security audit trail

```sql
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

  -- Event details
  action VARCHAR(100) NOT NULL,  -- 'oauth.authorized', 'token.refreshed', 'api.called'
  resource_type VARCHAR(50),  -- 'oauth_token', 'api_key', etc.
  resource_id INTEGER,

  -- Request details
  ip_address INET,
  user_agent TEXT,

  -- Result
  success BOOLEAN DEFAULT TRUE,
  error_message TEXT,

  -- Timestamp
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
```

---

## API Endpoints

### Authentication

All API calls require authentication via:
- **API Key:** `Authorization: Bearer api_xxx...` header
- **Session Cookie:** For web UI (after OAuth login)

### OAuth Routes

#### `GET /auth/{provider}/login`
Initiate OAuth flow

**Parameters:**
- `user_id` (required): User ID from consuming service
- `redirect_after` (optional): URL to redirect after success

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "encrypted_session_token"
}
```

Or: `302 Redirect` to authorization URL

---

#### `GET /auth/{provider}/callback`
OAuth callback handler

**Parameters:**
- `code`: Authorization code from provider
- `state`: Session token (CSRF protection)

**Response:**
```json
{
  "success": true,
  "account_email": "user@example.com",
  "scopes": ["calendar.readonly", "tasks.readonly"]
}
```

Or: `302 Redirect` to success page

---

#### `DELETE /auth/{provider}/revoke`
Revoke OAuth token

**Parameters:**
- `account_email` (required): Email of account to revoke

**Response:**
```json
{
  "success": true,
  "message": "Token revoked for user@example.com"
}
```

---

### Token API

#### `GET /api/tokens/{provider}/{account_email}`
Get valid access token for provider and account

**Response:**
```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "token_type": "Bearer",
  "expires_in": 3599,
  "scope": "calendar.readonly tasks.readonly"
}
```

**Error Response (401):**
```json
{
  "error": "token_expired",
  "message": "Token expired and refresh failed",
  "account_email": "user@example.com"
}
```

---

#### `GET /api/tokens/{provider}/{account_email}/status`
Check token status without retrieving token

**Response:**
```json
{
  "is_valid": true,
  "expires_in": 3599,
  "last_refresh": "2025-05-21T10:30:00Z",
  "scopes": ["calendar.readonly", "tasks.readonly"]
}
```

---

### Calendar Routes

#### `GET /calendars/{provider}`
List all calendars for user's connected accounts

**Parameters:**
- `account_email` (optional): Filter by specific account

**Response:**
```json
{
  "calendars": [
    {
      "id": "primary",
      "name": "Work Calendar",
      "account_email": "user@example.com",
      "provider": "google",
      "color": "#1E90FF",
      "is_primary": true
    }
  ]
}
```

---

#### `GET /calendars/{provider}/{calendar_id}/events`
Get calendar events

**Parameters:**
- `start_date`: ISO 8601 date (default: today)
- `end_date`: ISO 8601 date (default: 30 days from now)
- `max_results`: Max events (default: 100)

**Response:**
```json
{
  "events": [
    {
      "id": "evt_123",
      "summary": "Team Meeting",
      "start": "2025-05-21T14:00:00Z",
      "end": "2025-05-21T15:00:00Z",
      "location": "Conference Room A",
      "attendees": ["user@example.com", "colleague@example.com"],
      "is_all_day": false
    }
  ]
}
```

---

### Task Routes

#### `GET /tasks/{provider}`
List all task lists

**Parameters:**
- `account_email` (optional): Filter by specific account

**Response:**
```json
{
  "task_lists": [
    {
      "id": "list_123",
      "name": "Work Tasks",
      "account_email": "user@example.com",
      "provider": "google",
      "task_count": 15
    }
  ]
}
```

---

#### `GET /tasks/{provider}/{list_id}/items`
Get tasks from task list

**Parameters:**
- `status`: Filter by status ('pending', 'completed', 'all')
- `due_before`: ISO 8601 date (filter by due date)

**Response:**
```json
{
  "tasks": [
    {
      "id": "task_456",
      "title": "Review pull request",
      "status": "pending",
      "due_date": "2025-05-22T17:00:00Z",
      "priority": "high",
      "notes": "Check authentication logic"
    }
  ]
}
```

---

### Admin Routes

#### `GET /api/admin/accounts`
List all connected accounts for user

**Response:**
```json
{
  "accounts": [
    {
      "provider": "google",
      "account_email": "user@example.com",
      "scopes": ["calendar.readonly", "tasks.readonly"],
      "token_valid": true,
      "last_used": "2025-05-21T10:30:00Z",
      "connected_at": "2025-05-20T08:00:00Z"
    }
  ]
}
```

---

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "uniek-connect",
  "version": "0.1.0",
  "database": "connected",
  "token_refresh_scheduler": "running"
}
```

---

## Security Model

### Threat Model

**Assets to Protect:**
1. OAuth refresh tokens (permanent access to user data)
2. OAuth access tokens (temporary access to user data)
3. User account credentials
4. API keys for consuming services

**Threats:**
1. Database compromise (SQL injection, backup theft)
2. Man-in-the-middle attacks
3. CSRF attacks during OAuth flow
4. API key leakage
5. Unauthorized token access

### Security Controls

#### 1. Token Encryption at Rest
**Control:** Encrypt refresh tokens with Fernet (AES-128)
**Implementation:**
```python
from cryptography.fernet import Fernet

# Generate key once, store in env variable
encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")
fernet = Fernet(encryption_key)

# Encrypt before storing
refresh_token_encrypted = fernet.encrypt(refresh_token.encode())

# Decrypt when needed
refresh_token = fernet.decrypt(refresh_token_encrypted).decode()
```

**Key Management:**
- Encryption key stored in environment variable
- Never committed to git
- Rotated every 90 days (requires re-encryption)

---

#### 2. HTTPS Only
**Control:** All traffic over TLS 1.3
**Implementation:**
- Caddy reverse proxy terminates TLS
- HSTS headers enabled
- Redirect HTTP to HTTPS

---

#### 3. CSRF Protection
**Control:** State token in OAuth flow
**Implementation:**
```python
# Generate state token
state = secrets.token_urlsafe(32)
session["oauth_state"] = state

# Validate on callback
if request.args.get("state") != session.get("oauth_state"):
    raise ValueError("Invalid state token")
```

---

#### 4. API Key Authentication
**Control:** SHA256 hashed API keys
**Implementation:**
```python
# Generate API key
api_key = f"api_{secrets.token_urlsafe(32)}"
key_hash = hashlib.sha256(api_key.encode()).hexdigest()

# Store only hash
db.api_keys.insert(key_hash=key_hash, key_prefix=api_key[:8])

# Validate on request
provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
if provided_hash != stored_hash:
    raise Unauthorized()
```

---

#### 5. Rate Limiting
**Control:** Limit API requests per key
**Implementation:**
- 100 requests per minute per API key
- 10 OAuth authorizations per hour per user
- Redis-based sliding window

---

#### 6. Audit Logging
**Control:** Log all security events
**Events Logged:**
- OAuth authorizations
- Token refreshes
- API key usage
- Failed authentication attempts
- Token revocations

---

#### 7. Token Scopes
**Control:** Request minimal scopes needed
**Google Scopes:**
- `https://www.googleapis.com/auth/calendar.readonly` (read calendar)
- `https://www.googleapis.com/auth/tasks.readonly` (read tasks)

**Microsoft Scopes:**
- `Calendars.Read` (read calendar)
- `Tasks.Read` (read tasks)

---

## Multi-Tenant Strategy

### Isolation Levels

#### 1. Organization Level
- Each organization has separate API keys
- Users belong to organizations
- Row-level security: `WHERE organization_id = ?`

#### 2. User Level
- OAuth tokens scoped to individual users
- Users can only access their own connected accounts
- API endpoints require user authentication

### Data Access Patterns

**Pattern 1: Service-to-Service (via API Key)**
```python
# Consuming service (e.g., Organaizer) calls with API key
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(
    "https://uniek-connect/api/tokens/google/user@example.com",
    headers=headers
)

# uNiek Connect validates:
# 1. API key valid
# 2. API key belongs to organization
# 3. user@example.com belongs to same organization
# 4. Return token if all checks pass
```

**Pattern 2: User-Initiated (via Web UI)**
```python
# User clicks "Connect Google" in Organaizer
# Redirects to uNiek Connect OAuth flow
# After authorization, uNiek Connect:
# 1. Stores token for user
# 2. Redirects back to Organaizer
# 3. Organaizer can now request tokens via API key
```

### Single-User MVP vs Multi-Tenant

**Phase 1 (MVP):** Single user (Niek)
- Hardcode `organization_id = 1`
- Hardcode `user_id = 1`
- Skip authentication for now

**Phase 2:** Multi-tenant
- Implement API key authentication
- Add organization/user management
- Enforce row-level security

---

## Feature Flags (MANDATORY for /opt/products)

**All production services MUST implement feature flags for automated testing.**

### Why Feature Flags?

Feature flags enable:
- **A/B testing** - Test new features with subset of users
- **Gradual rollouts** - Deploy features incrementally
- **Emergency killswitch** - Disable broken features instantly
- **Automated testing** - Test environments can enable/disable features
- **Continuous deployment** - Deploy code without exposing features

### Implementation Requirements

**1. Configuration File**

Each service MUST have a feature flags configuration file:

```yaml
# config/feature_flags.yaml
features:
  new_ui:
    enabled: false
    description: "New responsive UI design"
    environments:
      dev: true
      accept: true
      prod: false

  api_v2:
    enabled: false
    description: "API v2 endpoints"
    rollout_percentage: 0  # 0-100
    environments:
      dev: true
      accept: false
      prod: false

  experimental_cache:
    enabled: false
    description: "Redis caching layer"
    requires: ["redis_available"]
```

**2. Feature Flag Library**

```python
# utils/feature_flags.py
import os
import yaml
from typing import Dict, Optional

class FeatureFlags:
    def __init__(self, config_path: str = "config/feature_flags.yaml"):
        self.env = os.getenv("ENVIRONMENT", "dev")
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def is_enabled(self, feature: str, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled"""
        if feature not in self.config["features"]:
            return False

        flag = self.config["features"][feature]

        # Check environment-specific setting
        if "environments" in flag:
            if self.env in flag["environments"]:
                if not flag["environments"][self.env]:
                    return False

        # Check global enabled
        if not flag.get("enabled", False):
            return False

        # Check rollout percentage
        if "rollout_percentage" in flag and user_id:
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            if (hash_val % 100) >= flag["rollout_percentage"]:
                return False

        return True

# Usage in code:
flags = FeatureFlags()

if flags.is_enabled("new_ui"):
    return render_new_ui()
else:
    return render_old_ui()
```

**3. Environment Variables**

Override via environment variables:
```bash
FEATURE_NEW_UI=true
FEATURE_API_V2=false
```

**4. Admin API Endpoints**

Production services MUST expose feature flag API:
```
GET  /api/admin/features          # List all flags
POST /api/admin/features/:name    # Toggle flag
GET  /api/admin/features/:name    # Get flag status
```

### Testing Integration

**Automated tests can enable/disable features:**

```python
# tests/test_new_feature.py
def test_new_ui_enabled():
    with override_feature("new_ui", enabled=True):
        response = client.get("/")
        assert "new-ui-class" in response.text

def test_new_ui_disabled():
    with override_feature("new_ui", enabled=False):
        response = client.get("/")
        assert "old-ui-class" in response.text
```

### Deployment Checklist

Before deploying to production:
- [ ] Feature flags implemented
- [ ] Tests use feature flag overrides
- [ ] config/feature_flags.yaml exists
- [ ] Admin API endpoints work
- [ ] Documentation updated

### Feature Flag Lifecycle

1. **Development** - Flag created, enabled in dev
2. **Acceptance Testing** - Enabled in accept
3. **Production Canary** - Enabled for 5% users
4. **Production Rollout** - Increase to 100%
5. **Flag Removal** - After feature stable for 30 days, remove flag and cleanup code

