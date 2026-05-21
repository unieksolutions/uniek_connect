<!--
ts: 2026-04-17T00:00:00Z | git: main | path: /opt/bootstrap
-->

# INTEGRATION.md — Platform Integration Guide

This document describes how to integrate an application with platform services.
Each section covers one platform service. Use the filled-in sections as a reference;
copy the pattern for new integrations.

**Audience:** Application-building agents and developers who need to connect their
application to a shared platform service.

**How to use:**
1. Read the section for the service you are integrating with
2. Follow the steps in order — each step has a prerequisite gate
3. Use the acceptance criteria as your definition of done
4. Reference the linked project docs for deeper technical detail

---

## Services

| Service | Status | Description |
|---------|--------|-------------|
| [uNiek IAM](#uNiek-IAM) | ✅ Available | Identity, authentication, authorisation, SSO |
| [SPI Manager](#SPI-Manager) | ⬜ Template | Agent orchestration and service discovery |

---

---

## uNiek IAM

**What it provides:** Single Sign-On (SSO), OAuth2/OIDC, JWT-based identity,
role-based access control (RBAC), provisioning, webhooks, audit logging, and a
self-describing integration contract for all uNiek Solutions applications.

**Production URL:** `https://unieksolutions.nl/iam`
**Acceptance URL:** `https://accept.unieksolutions.nl/iam`
**Project docs:** `/opt/projects/uniek_iam/`
**Discovery (RFC 8414):** `GET {base_url}/.well-known/openid-configuration`
**Discovery (direct):** `GET {base_url}/api/v1/oauth2/.well-known/openid-configuration`
**Info (endpoint catalogus):** `GET {base_url}/api/v1/info`

---

### Contract first

Applications must integrate against the IAM contract, not against app-specific
handholding. `uniek_iam` tells the application what it needs to do; the
application follows that contract.

Default rule for application work:
- start at `/opt/bootstrap/INTEGRATION.md#uNiek-IAM`
- implement the generic onboarding contract first
- only add app-specific overlays when the generic contract is insufficient

---

### Environment model

Every application has at least two IAM registrations:
- `accept` / `staging`
- `production` / `live`

These are separate OAuth2 applications in IAM.

Each registration gets its own:
- `client_id`
- `client_secret`
- `redirect_uris`
- environment-specific `.env` values

**Never reuse one OAuth2 registration across acceptance and production.**

---

### Architecture layers

```
[Browser / App]
      ↓  OAuth2 authorization code flow
[uNiek IAM]   ← PHP, JWT RS256 now, Ed25519 dual-stack planned, MySQL
      ↓  claims + webhooks + onboarding contract
[Application] ← validates tokens, maps org/roles, provisions users
```

An application connects to IAM in the following layers. Implement them in order:

| Layer | What the application must do |
|-------|------------------------------|
| 1 — Register | Register app instance per environment and receive credentials |
| 2 — Configure | Set `IAM_*` variables and callback URLs in `.env` |
| 3 — Authenticate | Implement OAuth2 authorization code flow |
| 4 — Validate identity | Verify JWT or introspect token; fetch userinfo |
| 5 — Link tenant | Map IAM organisation to app tenant/customer |
| 6 — Authorize | Map IAM roles/scopes to app permissions |
| 7 — Provision | Auto-create or backfill user on first login |
| 8 — React | Handle revocation/webhook events and optional agent flows |

---

### Required environment variables

Each app instance should expect at least:

```env
IAM_BASE_URL=https://accept.unieksolutions.nl/iam
IAM_CLIENT_ID=<environment-specific client id>
IAM_CLIENT_SECRET=<environment-specific client secret>
IAM_AUTHORIZE_URL={base}/api/v1/oauth2/authorize
IAM_TOKEN_URL={base}/api/v1/oauth2/token
IAM_USERINFO_URL={base}/api/v1/oauth2/userinfo
IAM_JWKS_URL={base}/api/v1/oauth2/.well-known/jwks.json
IAM_INTROSPECT_URL={base}/api/v1/oauth2/introspect
IAM_LOGOUT_URL={base}/api/v1/auth/logout
```

Store only in `.env`. Never commit to git.

---

### API versioning — v1 (verplicht vanaf 2026-04-17)

De IAM API is gemigreerd naar versioned endpoints. **Gebruik altijd het `/api/v1/` prefix.**

**Endpoint-catalogus:**
- Accept: `GET https://accept.unieksolutions.nl/iam/api/v1/info`
- Productie: `GET https://unieksolutions.nl/iam/api/v1/info`

**Migratietabel:**

| Oud (deprecated) | Nieuw (v1) |
|------------------|------------|
| `/api/oauth2/authorize.php` | `/api/v1/oauth2/authorize` |
| `/api/oauth2/token.php` | `/api/v1/oauth2/token` |
| `/api/oauth2/userinfo.php` | `/api/v1/oauth2/userinfo` |
| `/api/oauth2/introspect.php` | `/api/v1/oauth2/introspect` |
| `/api/auth/logout.php` | `/api/v1/auth/logout` |
| `/api/auth/login.php` | `/api/v1/auth/login` |
| `/api/management/applications/register.php` | `/api/v1/management/applications/register` |

**Backwards compatibility:**
Oude URLs (met `.php` extensie of zonder `/v1/` prefix) werken nog, maar sturen automatisch een deprecation-waarschuwing naar `iam_endpoints@uniek.solutions` (max 1x per dag per endpoint). Migreer zo snel mogelijk.

**Uitzondering — JWKS en OIDC discovery:** deze URLs zijn niet gewijzigd:
- `GET {base}/.well-known/openid-configuration`
- `GET {base}/api/oauth2/.well-known/jwks.json`

---

### Integration rules (applies to every app)

**1. Prefer IAM-side rules over application hardcoding**
- Avoid code changes for every new role, tenant, or claim variant.
- Keep role translation, claim projection, tenant mapping, and scope policy in IAM-side data/config where possible.
- If app-specific claims are needed, keep one stable namespace per app and let IAM fill values rule-driven.

**2. Keep the application contract stable**
- Prefer standard claims and scopes first.
- If custom claims are needed, keep shape stable across environments.
- Do not hardcode per-customer authorization rules in the app.

**3. Validate tokens properly**
- Verify JWT signature via JWKS or use introspection.
- Do not merely decode a JWT payload and trust it.
- Current deployments use `RS256`; plan for Ed25519 dual-stack migration.

**4. Separate documentation from operations**
- `/info` is the small public index.
- `/tools` and `/skills` describe detailed contracts and workflows.
- `/info/tokens` documents token behavior.
- `/tokens` is the operational validation/introspection surface.

---

### Generic onboarding flow

```
1. Register `app_accept` in IAM
2. Register `app_prod` in IAM
3. Set per-environment IAM_* variables in the app
4. Implement OAuth2 callback
5. Exchange code for token
6. Validate JWT / introspect token
7. Fetch userinfo
8. Resolve tenant via iam_org_id
9. Map roles/scopes to app permissions
10. Provision or backfill user by iam_user_id
11. Establish local app session
12. Handle revocation / logout / webhook events
```

---

### Tenant linking requirements

Application-side database should support an explicit IAM organisation link.

**Tenant table requirement:**
```sql
ALTER TABLE {tenants_table}
    ADD COLUMN iam_org_id VARCHAR(36) NULL UNIQUE;
```

Rules:
- lookup tenant by `iam_org_id`
- if missing: fail clearly; do not silently create a tenant
- provisioning depends on this mapping being complete

---

### User provisioning requirements

Application-side user table should support a stable IAM user link.

**User table requirement:**
```sql
ALTER TABLE {users_table}
    ADD COLUMN iam_user_id VARCHAR(36) NULL UNIQUE;
```

Rules:
- lookup by `iam_user_id` first
- fall back to `email` only for backfill/migration
- first login must be idempotent
- second login must not create duplicates
- if the app still has password login for local users, IAM-provisioned users must not accidentally gain local-password access unless explicitly intended

---

### Authorization requirements

Rules:
- read roles from IAM, not from the app's own stale role table
- map by stable contract
- deny unknown roles by default
- re-check authorization on protected requests, not just at login time
- revoke access when IAM role binding is revoked

Note:
- Some current flows return role **names**, not slugs. Verify the actual contract before mapping.

---

### Agent / machine access

For machine integrations:
- use `client_credentials`
- accept Bearer tokens on API endpoints intended for agents
- validate scopes per endpoint
- do not allow agent tokens on user-session-only flows

---

### Acceptance checklist

- [ ] App has separate `accept` and `production` IAM registrations
- [ ] App `.env` contains environment-specific `IAM_*` variables
- [ ] OAuth2 callback exchanges code successfully
- [ ] JWT is verified via JWKS or introspection
- [ ] `iam_org_id` mapping resolves tenant/customer correctly
- [ ] `iam_user_id` provisioning works and is idempotent
- [ ] Roles/scopes are mapped explicitly and deny unknown values
- [ ] Logout and revocation behavior are handled cleanly
- [ ] No credentials are committed to code or docs

---

### Zero-testing implementation guide

**Goal:** follow this section exactly and the integration works on first deploy, no debugging needed.

### Library verification — ed25519, sodium, JWT, JWKS

Before implementing token validation, verify your runtime has the correct libraries.
A misconfigured library causes silent failures or incorrect validation.

#### PHP

```php
// 1. Check ext-sodium (preferred) of sodium_compat fallback
if (!extension_loaded('sodium')) {
    // Load sodium_compat — must be in your project
    require_once __DIR__ . '/path/to/sodium_compat/autoload.php';
    // Verify: sodium_compat must define sodium_crypto_sign_verify_detached()
}
if (!function_exists('sodium_crypto_sign_verify_detached')) {
    throw new RuntimeException('sodium not available — cannot verify Ed25519 signatures');
}

// 2. Verify JWKS reachable and contains Ed25519 key
$jwks = json_decode(file_get_contents('https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json'), true);
$edKeys = array_filter($jwks['keys'], fn($k) => $k['kty'] === 'OKP' && $k['crv'] === 'Ed25519');
if (empty($edKeys)) {
    throw new RuntimeException('No Ed25519 key found in JWKS');
}

// 3. Verify JWT structure before validation (3 base64url segments)
function isWellFormedJwt(string $token): bool {
    $parts = explode('.', $token);
    return count($parts) === 3 && !empty($parts[0]) && !empty($parts[1]) && !empty($parts[2]);
}

// 4. Always validate: iss, aud, exp, signature — never skip any
// Use /opt/bootstrap/security/php/Jwt.php (shared library)
```

#### Python

```python
import httpx, base64, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# 1. Fetch JWKS and extract Ed25519 key
jwks = httpx.get('https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json').json()
ed_keys = [k for k in jwks['keys'] if k.get('kty') == 'OKP' and k.get('crv') == 'Ed25519']
assert ed_keys, 'No Ed25519 key in JWKS'

# 2. Verify JWT structure
def is_well_formed_jwt(token: str) -> bool:
    parts = token.split('.')
    return len(parts) == 3 and all(parts)

# 3. Always validate iss, aud, exp — use shared library: /opt/bootstrap/security/python/jwt_verify.py
```

#### JavaScript / Node

```javascript
// Use /opt/bootstrap/security/js/jwt.js (shared library)
// Verify jose or equivalent can handle EdDSA (OKP/Ed25519)
import { createRemoteJWKSet, jwtVerify } from 'jose'

const JWKS = createRemoteJWKSet(new URL('https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json'))

async function verifyToken(token, expectedAudience) {
  const { payload } = await jwtVerify(token, JWKS, {
    issuer: 'https://unieksolutions.nl/iam',   // or accept URL
    audience: expectedAudience,
    algorithms: ['EdDSA'],
  })
  return payload
}
```

#### Common failure patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `Call to undefined function sodium_crypto_sign_verify_detached` | ext-sodium not loaded, sodium_compat not included | Add `require sodium_compat/autoload.php` in bootstrap **before** any JWT class is loaded |
| `Unexpected issuer` | JWT `iss` = production URL, app expects accept URL | Check `BASE_URL` in IAM `.env`; must match per environment |
| `Malformed JWT` | Token is a traditional hex token, not a JWT | Use `client_credentials` or `authorization_code` flow to get a JWT |
| `No Ed25519 key in JWKS` | JWKS endpoint returns RS256 keys only | Check IAM has Ed25519 keys generated (`/keys/ed25519_private.pem`) |
| `Unexpected audience` | JWT `aud` does not match app config | Verify `IAM_AUDIENCE` in channels/app `.env` matches what IAM issues |

---

#### Step 0 — Discover endpoints (never hardcode URLs)

Always start from the OIDC discovery document:

```
GET {IAM_BASE_URL}/.well-known/openid-configuration
```

Production:
```
GET https://unieksolutions.nl/iam/api/v1/oauth2/.well-known/openid-configuration
```

This returns the canonical URLs for all endpoints. Use these values — do not guess or hardcode.

**Known endpoint map:**
| Key | Production | Accept/staging |
|-----|-----------|----------------|
| `issuer` | `https://unieksolutions.nl/iam` | `https://accept.unieksolutions.nl/iam` |
| `authorization_endpoint` | `https://unieksolutions.nl/iam/api/v1/oauth2/authorize` | idem (accept base) |
| `token_endpoint` | `https://unieksolutions.nl/iam/api/v1/oauth2/token` | idem |
| `userinfo_endpoint` | `https://unieksolutions.nl/iam/api/v1/oauth2/userinfo` | idem |
| `jwks_uri` | `https://unieksolutions.nl/iam/api/v1/oauth2/.well-known/jwks.json` | idem |
| `introspection_endpoint` | `https://unieksolutions.nl/iam/api/v1/oauth2/introspect` | idem |
| `end_session_endpoint` | `https://unieksolutions.nl/iam/api/v1/auth/logout` | idem |
| `info` | `https://unieksolutions.nl/iam/api/v1/info` | idem (accept base) |

**The `issuer` differs per environment.** Always read from the discovery document and set `IAM_ISSUER` in `.env`. Never hardcode.

---

#### Step 1 — Register the app in IAM

Use the Management API to register your application. Run this per environment (accept én productie):

```bash
curl -X POST https://unieksolutions.nl/iam/api/v1/management/applications/register \
  -H "Authorization: Bearer <MANAGEMENT_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "yourapp",
    "base_url": "https://yourapp.nl",
    "redirect_uris": ["https://yourapp.nl/auth/callback"],
    "description": "Korte omschrijving",
    "allows_client_credentials": false,
    "allowed_scopes": ""
  }'
```

Voor machine-to-machine (agent/service zonder gebruiker):
```json
{
  "allows_client_credentials": true,
  "allowed_scopes": "yourapp:read yourapp:write"
}
```

**Accept URL:** vervang `unieksolutions.nl` door `accept.unieksolutions.nl`.

**MANAGEMENT_API_TOKEN:** de tokenwaarde staat in `/opt/tools/.env` (sleutel: `IAM_MANAGEMENT_TOKEN`). Lees die waarde uit en gebruik hem als Bearer token. Staat die sleutel er niet in, vraag hem dan op bij de platform-eigenaar — schrijf de waarde nooit naar een `.md` bestand of git repo.

Je ontvangt per omgeving:
- `client_id` — stabiele identifier, veilig in config
- `client_secret` — **eenmalig getoond**, direct opslaan in `.env`
- `admin_user.temp_password` — tijdelijk wachtwoord voor de app-admin user, ook eenmalig

Register **twee aparte apps**: één voor accept/staging, één voor productie.

---

#### Step 2 — Configure .env

Production `.env`:
```env
IAM_BASE_URL=https://unieksolutions.nl/iam
IAM_CLIENT_ID=yourapp_<hash>
IAM_CLIENT_SECRET=<secret>
IAM_REDIRECT_URI=https://yourapp.nl/auth/callback
IAM_AUTHORIZE_URL=https://unieksolutions.nl/iam/api/v1/oauth2/authorize
IAM_TOKEN_URL=https://unieksolutions.nl/iam/api/v1/oauth2/token
IAM_USERINFO_URL=https://unieksolutions.nl/iam/api/v1/oauth2/userinfo
IAM_JWKS_URL=https://unieksolutions.nl/iam/api/v1/oauth2/.well-known/jwks.json
IAM_ISSUER=https://unieksolutions.nl/iam
IAM_AUDIENCE=yourapp
```

Accept/staging `.env` — only these values change:
```env
IAM_BASE_URL=https://accept.unieksolutions.nl/iam
IAM_CLIENT_ID=yourapp_<accept-hash>        # separate registration
IAM_CLIENT_SECRET=<accept-secret>
IAM_REDIRECT_URI=https://accept.yourapp.nl/auth/callback
IAM_AUTHORIZE_URL=https://accept.unieksolutions.nl/iam/api/v1/oauth2/authorize
IAM_TOKEN_URL=https://accept.unieksolutions.nl/iam/api/v1/oauth2/token
IAM_USERINFO_URL=https://accept.unieksolutions.nl/iam/api/v1/oauth2/userinfo
IAM_JWKS_URL=https://accept.unieksolutions.nl/iam/api/v1/oauth2/.well-known/jwks.json
IAM_ISSUER=https://accept.unieksolutions.nl/iam
IAM_AUDIENCE=yourapp
```

`IAM_ISSUER` and `IAM_AUDIENCE` must be validated in every token you receive.

---

#### Step 3 — Login redirect (authorization request)

Generate a `state` token (cryptographically random, min 16 bytes), store it in the **server-side session**, then redirect:

```
GET {IAM_AUTHORIZE_URL}
  ?response_type=code
  &client_id={IAM_CLIENT_ID}
  &redirect_uri={IAM_REDIRECT_URI}          ← must match registration exactly
  &scope=openid profile email roles
  &state={random_state}
```

**Pitfall:** `redirect_uri` is compared byte-for-byte. Trailing slash, http vs https, or a port difference = `redirect_uri_mismatch` error.

---

#### Step 4 — Callback handler

The callback receives `?code=...&state=...`.

```php
// 1. Validate state — CSRF protection
if (!isset($_GET['state']) || $_GET['state'] !== $_SESSION['oauth_state']) {
    http_response_code(403); exit('Invalid state');
}
unset($_SESSION['oauth_state']);

// 2. Check for error response
if (isset($_GET['error'])) {
    // error: $_GET['error'], description: $_GET['error_description']
    http_response_code(400); exit($_GET['error_description'] ?? $_GET['error']);
}

// 3. Exchange code for tokens
$response = http_post($IAM_TOKEN_URL, [
    'grant_type'    => 'authorization_code',
    'code'          => $_GET['code'],
    'redirect_uri'  => $IAM_REDIRECT_URI,   // must match authorize request exactly
    'client_id'     => $IAM_CLIENT_ID,
    'client_secret' => $IAM_CLIENT_SECRET,
]);

$tokens = json_decode($response, true);
// contains: access_token, token_type, expires_in, (id_token if openid scope)
```

**Pitfall:** The code is single-use. Any retry or double-submit returns `invalid_grant`. Do not log the code.

---

#### Step 5 — Validate the token

**Option A — JWKS validation (preferred, no extra request):**

```php
// 1. Fetch JWKS (cache for 5 minutes)
$jwks = json_decode(file_get_contents($IAM_JWKS_URL), true);

// 2. Decode header to find kid
$header = json_decode(base64url_decode(explode('.', $access_token)[0]), true);

// 3. Find matching key by kid
$key = find_key_by_kid($jwks['keys'], $header['kid']);

// 4. Verify signature (RS256 currently, Ed25519 planned)
// Use a JWT library or openssl_verify with the public key

// 5. Verify claims — ALL of these, in this order:
$payload = json_decode(base64url_decode(explode('.', $access_token)[1]), true);

if ($payload['iss'] !== $IAM_ISSUER)  { reject('wrong issuer'); }
if ($payload['aud'] !== $IAM_AUDIENCE){ reject('wrong audience'); }
if ($payload['exp'] < time())         { reject('token expired'); }
if ($payload['nbf'] > time())         { reject('token not yet valid'); }
```

**Option B — introspection (simpler, extra request):**

```
POST {IAM_INTROSPECT_URL}
  client_id={IAM_CLIENT_ID}
  client_secret={IAM_CLIENT_SECRET}
  token={access_token}

→ { "active": true, "sub": "...", "email": "...", "roles": [...] }
→ { "active": false }  ← treat as 401
```

**Pitfall:** Never trust a JWT by only base64-decoding it. Always verify the signature.

---

#### Step 6 — Fetch userinfo

```
GET {IAM_USERINFO_URL}
Authorization: Bearer {access_token}

→ {
    "sub": "<iam_user_id>",
    "email": "user@example.com",
    "email_verified": true,
    "name": "Jan de Vries",
    "organization": { "id": "<iam_org_id>", "name": "Amsfort College" },
    "roles": {
        "global": ["super_admin"],
        "applications": { "2": ["SIS Administrator"] }
    },
    "roles_flat": ["super_admin", "SIS Administrator"]
  }
```

**`roles_flat`** is de aanbevolen manier voor role-checks in applicaties:
```php
$roles = $userinfo['roles_flat'] ?? [];
```
`roles` (genest object) is beschikbaar voor applicaties die per-app onderscheid nodig hebben.
⚠️ Oude integraties die `$userinfo['roles']` als flat array lezen moeten migreren naar `roles_flat`.

Store `sub` as `iam_user_id` and `organization.id` as `iam_org_id` in your local database.

---

#### Step 7 — Resolve tenant

```php
$tenant = db_find_one('SELECT * FROM tenants WHERE iam_org_id = ?', [$userinfo['organization']['id']]);

if (!$tenant) {
    // Do NOT silently create. Either:
    // a) Show an "organization not known" error and contact admin
    // b) Auto-provision if your app supports self-onboarding
    http_response_code(403); exit('Organization not registered');
}
```

---

#### Step 8 — Provision or match user

```php
// Always look up by iam_user_id first
$user = db_find_one('SELECT * FROM users WHERE iam_user_id = ?', [$userinfo['sub']]);

if (!$user) {
    // Backfill: try email match for migrated users
    $user = db_find_one('SELECT * FROM users WHERE email = ?', [$userinfo['email']]);
    if ($user) {
        db_update('users', ['iam_user_id' => $userinfo['sub']], ['id' => $user['id']]);
    } else {
        // New user — auto-provision
        $user = db_insert('users', [
            'iam_user_id' => $userinfo['sub'],
            'email'       => $userinfo['email'],
            'name'        => $userinfo['name'],
            'tenant_id'   => $tenant['id'],
        ]);
    }
}
```

**Pitfall:** If you check email first without `iam_user_id`, two IAM users with the same email in different orgs will collide.

---

#### Step 9 — Map roles

```php
$iam_roles = $userinfo['roles'] ?? [];

// Define your mapping explicitly — deny anything not listed
$role_map = [
    'qron.global_admin' => 'admin',
    'qron.editor'       => 'editor',
    'qron.viewer'       => 'viewer',
];

$app_roles = [];
foreach ($iam_roles as $role) {
    if (isset($role_map[$role])) {
        $app_roles[] = $role_map[$role];
    }
}

if (empty($app_roles)) {
    http_response_code(403); exit('No valid role for this application');
}
```

**Pitfall:** Do not grant access if no role maps — deny by default.

---

#### Step 10 — Establish local session

```php
session_regenerate_id(true); // prevent session fixation

$_SESSION['user_id']    = $user['id'];
$_SESSION['iam_sub']    = $userinfo['sub'];
$_SESSION['roles']      = $app_roles;
$_SESSION['tenant_id']  = $tenant['id'];
$_SESSION['expires_at'] = time() + $tokens['expires_in'];

header('Location: /dashboard');
exit;
```

**Pitfall:** Always call `session_regenerate_id(true)` after login to prevent session fixation attacks.

---

#### Step 11 — Logout

```php
// 1. Destroy local session
session_destroy();

// 2. Redirect to IAM logout (clears IAM session)
$logout_url = $IAM_LOGOUT_URL . '?post_logout_redirect_uri=' . urlencode($APP_BASE_URL);
header('Location: ' . $logout_url);
exit;
```

---

#### Common failure patterns

| Symptom | Cause | Fix |
|---------|-------|-----|
| `redirect_uri_mismatch` | URI in request ≠ registered URI | Check trailing slash, http/https, exact match |
| `invalid_grant` | Code already used or expired | Codes are single-use; do not retry |
| `401 Unexpected issuer` | `iss` in token ≠ `IAM_ISSUER` in `.env` | Set `IAM_ISSUER` per environment from discovery doc |
| `401 Invalid audience` | `aud` in token ≠ app identifier | Confirm `aud` value with IAM registration |
| User logs in but gets wrong tenant | `iam_org_id` not stored or not used for lookup | Always resolve tenant via `iam_org_id`, not name |
| Duplicate users on every login | Lookup by email only, not `iam_user_id` | Look up by `iam_user_id` first |
| Session lost after login | Redirect before session write completes | Write session, then redirect |
| Works on accept, fails on production | Hardcoded accept URLs in `.env` | Use environment-specific `.env` per deploy |

---

---

## uniek_channels — Email versturen

Alle applicaties sturen e-mail via uniek_channels (Brevo). Geen directe SMTP/PHPMailer/Brevo API keys in de app zelf.

### Endpoint

```
POST https://unieksolutions.nl/channels/api/channels/email/send
Authorization: Bearer <token>
Content-Type: application/json
```

### Body

```json
{
  "to": "ontvanger@voorbeeld.nl",
  "to_name": "Naam Ontvanger",
  "subject": "Onderwerp",
  "body_html": "<p>HTML inhoud</p>",
  "body_text": "Platte tekst (fallback)",
  "from_name": "Naam Afzender",
  "from_email": "noreply@jouwdomein.nl",
  "reply_to": "support@jouwdomein.nl",
  "correlation_id": "optioneel-eigen-id"
}
```

### Token ophalen

```
POST https://unieksolutions.nl/iam/api/v1/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
client_id=<jouw_client_id>
client_secret=<jouw_secret>
scope=channels:email:send
```

Token is 1 uur geldig — cache het in de request-levensduur.

### Geautoriseerde from_email domeinen (Brevo)

| App | Toegestane from_email domeinen |
|-----|-------------------------------|
| sis | @schoolinfoscherm.nl |
| daidto | @daid.to |
| iam | @unieksolutions.nl |
| shop | @unieksolutions.nl, @uniek.solutions |
| channels | @unieksolutions.nl |

### Accept-omgeving

Zelfde aanpak, andere base URL:
- Channels: `https://accept.unieksolutions.nl/channels/api/channels/email/send`
- IAM token: `https://accept.unieksolutions.nl/iam/api/v1/oauth2/token`

### Referentie-implementatie

Zie `/opt/projects/uniek_iam/includes/Mailer.php` voor een complete PHP-implementatie.

---

## Platform Security Standard — API Microservices

> **Implementeer dit niet zelf.** Gebruik de gedeelde library:
> `/opt/bootstrap/security/` — beschikbaar voor PHP, Node.js en Python.
> Zie `README.md` aldaar voor gebruiksinstructies.

**Van toepassing op:** alle interne API microservices in het uNiek ecosysteem
(kanalen, bridges, adapters, agents). Dit zijn services die niet direct door
een browser/gebruiker worden aangeroepen, maar door andere services of de
PHP-laag.

**Doel:** één universeel beveiligingspatroon zodat elke nieuwe microservice
dezelfde aanpak volgt en niet opnieuw uitgevonden hoeft te worden.

---

### Beveiligingslagen (verplicht, in volgorde)

```
Request
  │
  ▼
1. IP whitelist        — blokkeer alles buiten toegestane IPs
  │
  ▼
2. Rate limiting       — max N req/min per IP
  │
  ▼
3. Bearer token        — IAM JWKS validatie (EdDSA/Ed25519)
  │
  ▼
4. Scope check         — endpoint-specifieke scope vereist
  │
  ▼
Handler
```

**Uitzonderingen:**
- `/health` — geen auth, geen IP-check (voor externe monitoring/uptime checks)
- `/qr` en vergelijkbare beheer-UI's — alleen IP-whitelist, geen token

---

### IP Whitelist

Vaste IPs voor het uNiek platform:

| Omgeving | IP | Omschrijving |
|----------|----|--------------|
| hosting.com (productie PHP) | `185.146.22.239` | unieksolutions.nl |
| SPI (beheer / agents) | `88.159.37.158` | Extern IP SPI thuis |
| bitsofme-agents1 (Hetzner) | `77.42.71.48` | Agent VPS |
| start2-ai-vps (Hetzner) | `46.224.254.191` | AI VPS |

Configureer via `ALLOWED_IPS` environment variable (kommagescheiden).
Blokkeer niet-whitelisted IPs met HTTP 403 vóór verdere verwerking.

---

### Rate Limiting

- Default: **60 requests per minuut per IP**
- Configureerbaar via `RATE_LIMIT_RPM` environment variable
- Antwoord bij overschrijding: `HTTP 429 Too Many Requests`
- Header meegeven: `Retry-After: <seconds>`

---

### Bearer Token (IAM JWKS)

Elke microservice valideert tokens zelf via JWKS — geen centrale gateway.

```
Authorization: Bearer <access_token>
```

Validatiestappen:
1. Haal publieke sleutels op via `IAM_JWKS_URL` (cache 5 minuten)
2. Verwacht `alg: EdDSA`, `kty: OKP`, `crv: Ed25519`
3. Valideer: signature, `exp`, `nbf`, `iss`, `aud`
4. Controleer vereiste scope per endpoint
5. Weiger verlopen of ongeldige tokens met `HTTP 401`
6. Weiger tokens zonder juiste scope met `HTTP 403`

Environment variables:
```env
IAM_JWKS_URL=https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json
```

---

### Scopes per kanaal (uniek_channels)

| Endpoint | Vereiste scope |
|----------|---------------|
| `*/send/*` | `channels:{kanaal}:send` |
| `*/chat/*` | `channels:{kanaal}:send` |
| `*/admin/*`, `/disconnect`, `/reconnect` | `channels:{kanaal}:admin` |
| `/health` | — (open) |
| `/qr`, `/status` | IP-whitelist only |

---

### Message ID — universeel berichtmodel

**Elk verzonden bericht krijgt een `message_id` terug.**
Elk inbound event dat betrekking heeft op een eerder bericht verwijst
naar dat `message_id`.

Dit geldt voor:
- replies (antwoord op bericht)
- reactions/emoji (reactie op bericht)
- read receipts (bericht gelezen)
- delivery receipts (bericht bezorgd)
- poll responses (antwoord op poll, verwijst naar poll `message_id`)
- edits (bewerking van bericht)
- deletes (intrekking van bericht)

**Outbound response (altijd):**
```json
{ "success": true, "message_id": "ABCDEF123456" }
```

**Inbound webhook payload (altijd):**
```json
{
  "event": "message",
  "type": "<type>",
  "from": "+31612345678",
  "from_jid": "31612345678@s.whatsapp.net",
  "message_id": "<id-van-dit-bericht>",
  "reply_to_message_id": "<id-van-het-bericht-waarop-gereageerd-wordt>",
  "timestamp": 1713180000,
  "push_name": "Jan",
  "parts": [ ... ]
}
```

`reply_to_message_id` is aanwezig bij: replies, reactions, poll_responses,
read_receipts, delivery_receipts, edits, deletes.

---

### Foutresponses (standaard)

| Code | Betekenis |
|------|-----------|
| 400 | Ongeldige request body |
| 401 | Geen of ongeldig token |
| 403 | IP niet toegestaan, of scope ontbreekt |
| 429 | Rate limit overschreden |
| 503 | Backend (bijv. WhatsApp) niet verbonden |

---

### Implementatie checklist nieuwe microservice

- [ ] IP whitelist middleware als eerste laag
- [ ] Rate limiter als tweede laag
- [ ] JWKS token validatie als derde laag
- [ ] Scope check per endpoint
- [ ] `/health` vrijgesteld van auth
- [ ] Alle outbound responses bevatten `message_id`
- [ ] Alle inbound webhooks bevatten `message_id` + `reply_to_message_id`
- [ ] `ALLOWED_IPS`, `RATE_LIMIT_RPM`, `IAM_JWKS_URL` in `.env`
- [ ] Geen credentials in code of docs

---

## SPI Manager

**What it provides:** {one-line description}

**Production URL:** {url}
**Acceptance URL:** {url}
**Project docs:** {path}
**Discovery:** {endpoint}

---

### Architecture layers

```
{diagram}
```

| Layer | Epic | What the application must do |
|-------|------|------------------------------|
| 1 — {name} | EPIC 1 | {description} |

---

### EPIC 1 — {title}

**Goal:** {goal}

**Application must implement:**
- {step}

**Acceptance criteria:**
- [ ] {criterion}

---

### Security requirements

- [ ] {requirement}
