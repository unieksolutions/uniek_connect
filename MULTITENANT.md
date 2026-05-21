<!--
ts: 2026-05-15T00:00:00Z | path: /opt/bootstrap/MULTITENANT.md
-->

# Multitenant White-Label Checklist

Standaard aanpak voor uNiek-projecten die door meerdere organisaties gebruikt worden,
elk met een eigen subdomein en huisstijl.

**Referentie-implementatie:** `/opt/projects/shopje` — dit project is volledig uitgewerkt.

---

## Architectuur

```
shop.mijndomein.tld  (CNAME → shop.unieksolutions.nl)
        ↓
Caddy / .htaccess   (domein → org slug mapping)
        ↓
Applicatie          (laadt theme via IAM, past CSS vars toe)
        ↓
IAM /api/public/theme.php  (geeft primary, secondary, logo_url, font)
```

**Org-context bepalen (voorkeursvolgorde):**
1. URL-pad: `/{app}/{org-slug}/` of `/{org-slug}/`
2. Header gezet door Caddy: `X-Org-Slug: mijnorganisatie`
3. Ingelogde gebruiker: org-slug uit JWT-token

**Theme caching:**
- Sla theme op in lokale DB/cache (SQLite `settings` tabel, of bestand)
- Sla `iam_theme_cached_at` op — vernieuw na TTL (standaard: 1 uur)
- **Shared hosting (A2/bitsofme):** poll-based (TTL), geen webhooks mogelijk
- **VPS:** TTL óf webhook van IAM bij theme-update

---

## Checklist per project

### 1. Org-slug in URL
- [ ] Org slug zichtbaar in URL-pad (`/{slug}/` of subdomain via Caddy/htaccess)
- [ ] Slug wordt uit `REQUEST_URI` / route gehaald (niet hardcoded)
- [ ] Fallback naar default org als geen slug aanwezig

### 2. IAM integratie
- [ ] `IAM_BASE_URL`, `IAM_APP_ID`, `IAM_CLIENT_ID`, `IAM_CLIENT_SECRET` in `.env`
- [ ] OAuth2 login-flow werkt (redirect → callback → JWT opslaan)
- [ ] JWT wordt gevalideerd bij elk request (JWKS of token introspection)
- [ ] Org-slug uit JWT beschikbaar na login

### 3. Theme ophalen & cachen
- [ ] `fetch_and_cache_theme(token)` functie aanwezig (zie shopje `api/theme.php`)
- [ ] Aanroep: na succesvolle login, en bij TTL-verlopen cache
- [ ] Gecachte velden: `primary_color`, `secondary_color`, `logo_url`, `font_family`, `org_name`
- [ ] `iam_theme_cached_at` opgeslagen — TTL check bij elke page load
- [ ] Fallback: uNiek defaults (`#AACA38`, `#F8AC2E`, `Quicksand`) als IAM niet bereikbaar

### 4. CSS custom properties
- [ ] Elke pagina heeft deze `:root` fallbacks:
  ```css
  :root {
      --brand-primary:   #AACA38;
      --brand-secondary: #F8AC2E;
      --brand-font:      'Quicksand', sans-serif;
  }
  ```
- [ ] Componenten gebruiken `var(--brand-primary)` etc. (geen hardcoded kleuren)
- [ ] Theme-waarden worden als inline `<style>` geïnjecteerd in `<head>` (server-side of via JS)

### 5. Logo
- [ ] `<img id="tenant-logo" src="..." alt="...">` aanwezig in header
- [ ] Fallback: uNiek logo als `logo_url` leeg is
- [ ] Logo URL komt uit gecachte theme, niet hardcoded

### 6. "Maak een voorstel" knop (optioneel)
- [ ] `<a id="tenant-proposal-btn">` in header (verborgen als geen `proposal_url`)
- [ ] Wordt zichtbaar als `proposal_url` aanwezig is in theme response

### 7. Caddy / routing configuratie
- [ ] Caddy-blok aanwezig voor `{app}.unieksolutions.nl/{slug}` routing
- [ ] Custom domein mapping gedocumenteerd (welk domein → welke org slug)
- [ ] HTTPS werkt op custom domein (Let's Encrypt via Caddy)
- [ ] Op shared hosting: `.htaccess` RewriteRule voor slug-routing

### 8. Testen
- [ ] Getest met minimaal 2 organisaties (verschillende kleuren/logo's)
- [ ] Getest: theme-update in IAM → cache vervalt → nieuwe stijl geladen
- [ ] Getest op mobile (phone + tablet) via screenCtx
- [ ] Getest: onbekende org slug → foutmelding of redirect

---

---

## IAM Login Routing — voor applicatiebouwers

Na een succesvolle login (wachtwoord, Google SSO of Microsoft SSO) bepaalt IAM
waar de gebruiker naartoe gaat. **Applicatiebouwers hoeven dit niet zelf te implementeren.**

### Redirect prioriteit (vastgelegd in `includes/LoginRouter.php`)

```
1. OAuth2 flow actief (redirect_uri aanwezig)
      → stuur naar redirect_uri?code=...&state=...
        De applicatie handelt de code-exchange af en stuurt de gebruiker
        naar zijn eigen landingspagina voor ingelogde gebruikers.

2. Geen OAuth2 flow (directe IAM-login):
      super_admin rol  → /iam/super_admin/index.php
      org_admin rol    → /iam/admin/index.php
      andere rol       → /iam/account/profile.php
```

### Wat de applicatie moet doen na ontvangst van de OAuth2 callback

1. Wissel de `code` in voor een access token via `POST /iam/api/oauth2/token.php`
2. Valideer het JWT (JWKS: `/iam/.well-known/jwks.json`)
3. Lees rollen uit het token: `roles.applications.{app_id}[]`
4. Stuur de gebruiker door naar de landingspagina van jouw applicatie

IAM stuurt de gebruiker altijd naar de `redirect_uri` van de applicatie —
nooit rechtstreeks naar een applicatiepagina. De applicatie is verantwoordelijk
voor de routing binnen zijn eigen domein.

### Admin navigatie-knop

IAM-pagina's die `LoginRouter::adminNav($userId)` aanroepen tonen automatisch
een ⚙ Super Admin of 🏢 Org Admin knop in de header als de gebruiker die rol heeft.
Applicaties die hun eigen UI bouwen hoeven dit niet te kopiëren — het is alleen
relevant voor IAM-eigen beheerpagina's.

---

## Referentie-code (shopje)

| Bestand | Functie |
|---------|---------|
| `api/tenant.php` | Slug uit URL halen, tenant config laden |
| `api/theme.php` | `fetch_and_cache_iam_theme()` + CSS-injectie |
| `api/config.php` | IAM env vars laden |
| `.env.example` | Template voor IAM configuratie |

---

## Notities

- **Shared hosting:** geen sudo, geen systemd, geen webhooks → altijd TTL-cache
- **VPS:** TTL-cache werkt altijd; webhook is optionele verbetering
- Tenant-registry hardcoden is tijdelijk toegestaan als DB-lookup nog niet klaar is,
  maar markeer met `// TODO: replace with DB lookup`
- Theme-fetch mag mislukken (timeout/IAM down) — app blijft werken met cache/fallback
