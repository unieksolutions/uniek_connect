<!--
ts: 2026-04-14T00:00:00Z | path: /opt/bootstrap/SERVICE_CONTRACT.md
-->

# Service Contract — uNiek Ecosysteem Standaard

Elke service die onderdeel is van het uNiek ecosysteem **MOET** dit contract implementeren.
Het contract maakt services zelfbeschrijvend voor zowel mensen als agents.

---

## Verplichte Endpoints

### `GET /info` — Discovery (rate-limited)

Publiek toegankelijk. Beschrijft wat de service doet, welke endpoints beschikbaar zijn
en onder welke voorwaarden.

**Rate limit:** 60 req/min per IP

Response:
```json
{
  "service": "uniek_iam",
  "version": "1.2.0",
  "description": "Identity & Application Management",
  "auth": {
    "type": "bearer",
    "jwks_url": "https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json",
    "token_url": "https://unieksolutions.nl/iam/api/oauth2/token.php"
  },
  "endpoints": [
    {
      "path": "/api/oauth2/authorize.php",
      "method": "GET",
      "auth_required": false,
      "description": "Start OAuth2 authorization flow",
      "scopes": []
    },
    {
      "path": "/api/admin/users",
      "method": "GET",
      "auth_required": true,
      "description": "List users",
      "scopes": ["users:read"]
    }
  ],
  "rate_limits": {
    "/info": "60/min",
    "/tokens": "60/min",
    "default": "300/min"
  }
}
```

---

### `GET /tokens` — Token validatie (rate-limited)

Vereist Bearer token. Valideert het token en toont welke rechten het heeft,
optioneel gefilterd op een specifiek endpoint.

**Rate limit:** 60 req/min per token

Request (optioneel):
```
GET /tokens?check_endpoint=/api/admin/users&check_method=GET
Authorization: Bearer <access_token>
```

Response:
```json
{
  "valid": true,
  "expires_in": 3542,
  "subject": "user_abc123",
  "scopes": ["users:read", "users:write"],
  "org": "unieksolutions",
  "app": "iam_admin",
  "endpoint_access": {
    "path": "/api/admin/users",
    "method": "GET",
    "allowed": true,
    "missing_scopes": []
  }
}
```

Bij ongeldig token:
```json
{ "valid": false, "reason": "expired" }
```

---

### `GET /tools` — Atomaire capabilities (MCP-compatibel)

Vereist Bearer token. Toont welke atomaire acties beschikbaar zijn voor de caller,
op basis van diens scopes. MCP-compatibel formaat.

```json
{
  "tools": [
    {
      "name": "create_user",
      "description": "Maak een nieuwe gebruiker aan binnen een organisatie",
      "required_scope": "users:create",
      "available": true,
      "input_schema": {
        "type": "object",
        "properties": {
          "email": { "type": "string" },
          "org_id": { "type": "string" },
          "role": { "type": "string" }
        },
        "required": ["email", "org_id"]
      }
    },
    {
      "name": "delete_user",
      "description": "Verwijder een gebruiker",
      "required_scope": "users:delete",
      "available": false,
      "reason": "Scope users:delete ontbreekt in token"
    }
  ]
}
```

`available: false` tools worden wél getoond — agent weet wat er bestaat maar niet mag.

---

### `GET /skills` — Samengestelde workflows

Vereist Bearer token. Toont welke samengestelde workflows beschikbaar zijn.
Een skill combineert meerdere tools in een gedefinieerde volgorde.

```json
{
  "skills": [
    {
      "name": "onboard_user",
      "description": "Registreer, verifieer en wijs rol toe aan nieuwe gebruiker",
      "steps": ["create_user", "send_verification_email", "assign_role"],
      "available": true,
      "required_scopes": ["users:create", "channels:email:send", "roles:assign"]
    },
    {
      "name": "register_application",
      "description": "Registreer een nieuwe applicatie en genereer credentials",
      "steps": ["create_application", "generate_credentials", "assign_default_scopes"],
      "available": false,
      "reason": "Scope management:applications:write ontbreekt"
    }
  ]
}
```

---

### `GET /health` — Health check

Altijd publiek. Geen auth vereist.

```json
{
  "status": "ok",
  "dependencies": {
    "database": "ok",
    "iam": "ok",
    "channels": "degraded"
  }
}
```

Status waarden: `ok` | `degraded` | `down`

---

## Authenticatie Standaard

Alle endpoints (behalve `/info` en `/health`) vereisen:

```
Authorization: Bearer <JWT>
```

- Token uitgegeven door `uniek_iam` via OAuth2 (`authorization_code` of `client_credentials`)
- Formaat: JWT RS256
- Validatie via JWKS: `https://unieksolutions.nl/iam/api/oauth2/.well-known/jwks.json`
- Verlopen tokens: `401 Unauthorized` + `{ "error": "token_expired" }`
- Onvoldoende scopes: `403 Forbidden` + `{ "error": "insufficient_scope", "required": ["..."] }`

---

## Standaard Foutresponses

| HTTP | Code | Betekenis |
|------|------|-----------|
| 400 | `invalid_request` | Ontbrekende of ongeldige parameters |
| 401 | `unauthorized` | Geen of ongeldig token |
| 401 | `token_expired` | Token verlopen |
| 403 | `insufficient_scope` | Token geldig, scope ontbreekt |
| 404 | `not_found` | Resource bestaat niet |
| 422 | `validation_error` | Request body ongeldig |
| 429 | `rate_limited` | Te veel verzoeken |
| 503 | `service_unavailable` | Dependency niet bereikbaar |

Fout-response formaat:
```json
{
  "error": "insufficient_scope",
  "message": "Scope users:delete is vereist",
  "required_scopes": ["users:delete"],
  "docs": "/info"
}
```

---

## Scope Naamgeving

Formaat: `{resource}:{actie}`

Acties: `read` | `create` | `update` | `delete` | `send` | `verify` | `invite` | `assign`

Voorbeelden:
- `users:read`, `users:create`, `users:delete`
- `organisations:read`, `organisations:create`
- `channels:email:send`, `channels:otp:verify`
- `management:applications:write`

---

## Rate Limiting Headers

Elke response bevat:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 247
X-RateLimit-Reset: 1744636800
```

---

## Migratie IST → SOLL

Services implementeren dit contract incrementeel. Volgorde:

1. `/health` — altijd als eerste (simpel)
2. `/info` — discovery, geen auth nodig
3. `/tokens` — validatie, hergebruik bestaande JWT-logica
4. `/tools` — capabilities op basis van scopes
5. `/skills` — samengestelde workflows (optioneel, fase 2)

**Prioriteitsvolgorde migratie:**
1. `uniek_iam` (referentie-implementatie)
2. `uniek_channels` (greenfield — native bouwen)
3. `sis`
4. `shopje`
5. `daid.to` (na channels)
6. `interviewer`
7. `qronme`
8. `meetingrecorder`
