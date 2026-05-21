<!--
ts: 2026-05-05T00:00:00Z | git: <to-be-filled> | path: <relative-path>
-->
# DESIGN

> **Standard frontend stack reference:** `/opt/bootstrap/design/FRONTEND_STACK.md`
> Contains canonical CDN versions for Tabulator, Chart.js, a11y-bar, and multitenancy theming.
> Always check there before adding a frontend dependency.

> **Screen context & responsive layout:** `/opt/bootstrap/design/SCREEN_CONTEXT.md`
> Contains the mandatory `screenCtx` utility, responsive card grid, Tabulator/Chart.js mobile
> config, and the `fitTextToContainer` pattern for fixed-display screens.

---

## Report & Visualization Tools

Standard tools for data display and reporting in uNiek projects:

### Tables — Tabulator 6.3.1
See `/opt/bootstrap/design/FRONTEND_STACK.md` for CDN, init pattern and usage examples.
**When to use:** Any structured data grid (tickets, logs, users, results).

### Charts — Chart.js 4.4.7
See `/opt/bootstrap/design/FRONTEND_STACK.md` for CDN and standard bar/line patterns.
**When to use:** Trends, distributions, progress over time.

### Test / Run Reports — built-in HTML + JSON
For agent-generated reports (test runs, pipeline results, audit logs):
- Write `reports/latest/summary.json` (machine-readable, schema in ARCHITECTURE.md)
- Write `reports/latest/summary.html` (human-readable, uses Tabulator for result table)
- Archive timestamped copies in `reports/YYYY-MM-DD_HH-MM/`
- Reports are gitignored — never committed

### Notifications
Standard notification channels (in priority order):
1. **ntfy** — `POST https://ntfy.sh/{topic}` — lightweight, no auth required for public topics
2. **Telegram** — Bot API, `POST /sendMessage` — good for structured messages
3. **WhatsApp** — via configured WA Business API or Twilio
Use ntfy for automated alerts; Telegram/WhatsApp for user-facing or high-priority notifications.

---

UI/UX specifications and design guidelines for this project.

---

## Design Type

**Select the primary interface type for this project:**

- ☐ **Web Application** - Browser-based interface (responsive)
- ☐ **CLI Tool** - Command-line interface
- ☐ **API Service** - No UI (API-only)
- ☐ **Mobile App** - Native or hybrid mobile app
- ☐ **Desktop App** - Native desktop application
- ☐ **Hybrid** - Multiple interface types

---

## WEB APPLICATION DESIGN REQUIREMENTS

### Screen Context & Responsive Design (MANDATORY)

**Screen Context Utility — ALTIJD OPNEMEN:**
Gebruik de `screenCtx` utility uit `/opt/bootstrap/design/SCREEN_CONTEXT.md`.
Dit stelt `data-factor`, `data-touch`, `data-dpr`, `data-orient` in op `<html>`.

**Factoren:**
| Factor | Breedte | Typisch apparaat |
|--------|---------|-----------------|
| `phone`   | < 640px  | Smartphone staand/liggend |
| `tablet`  | 640–1023px | Tablet, grote telefoon landscape |
| `desktop` | 1024–1599px | Laptop, desktop |
| `wide`    | 1600px+  | Groot beeldscherm |

**Mobile-First Approach:**
- Schrijf CSS voor phone eerst (default), overschrijf voor grotere schermen
- Test op: phone 360px touch, tablet 768px, desktop 1200px, wide 1920px
- Gebruik NOOIT hardcoded aantal kolommen — gebruik `auto-fill` + `minmax`

**Responsive Requirements:**
- ✅ `screenCtx` utility aanwezig in hoofd-JS
- ✅ Card dashboards gebruiken CSS Grid `auto-fill` + `minmax(280px, 1fr)`
- ✅ Tabulator heeft `responsiveLayout: "collapse"` + `responsive` per kolom
- ✅ Chart.js heeft `maintainAspectRatio: false` + CSS-gestuurde containerhoogte
- ✅ Touch-friendly buttons (min 44×44px, via `[data-touch="1"]` selector)
- ✅ **HIGH-DPI MOBILE FONTS** (zie sectie hieronder)
- ✅ Geen horizontaal scrollen (behalve intentionele datatables)
- ✅ Viewport meta: `<meta name="viewport" content="width=device-width, initial-scale=1">`

### Accessibility Bar (MANDATORY voor alle webprojecten)

Elke pagina met UI MOET een a11y-bar bevatten (sticky, bovenaan):
- 🌐 Taalwissel | Dys dyslexie-font | a− / A+ lettergrootte | 🌙 dag/nacht

Volledig patroon + CSS: `/opt/bootstrap/design/FRONTEND_STACK.md` → sectie "Accessibility Bar"
Werkend voorbeeld: `/opt/projects/interviewer/index.html`

### Multitenancy Theming (indien van toepassing)

Bij meerdere organisaties per project:
- CSS custom properties: `--brand-primary`, `--brand-secondary`, `--brand-font`
- Geladen via `applyTenantTheme(orgSlug)` vanuit uniek_iam API
- Standaard fallback: uNiek huisstijl (`#AACA38`, `#F8AC2E`, Quicksand)
- "Maak een voorstel" knop in header (verborgen als niet ingesteld)

Volledig patroon: `/opt/bootstrap/design/FRONTEND_STACK.md` → sectie "Multitenancy Theming"

---

### HIGH-DPI Mobile Font Sizing (CRITICAL)

**⚠️ PROBLEM:** Modern phones (OnePlus, Samsung, iPhone) have high pixel density. CSS pixels ≠ device pixels. A "24px" font looks tiny on these screens.

**❌ WRONG - Using rem or small px as default:**
```css
body { font-size: 16px; }  /* Too small on high-DPI */
body { font-size: 1rem; }  /* Scales wrong */
```

**✅ CORRECT - Mobile-first with large px values:**
```css
/* DEFAULT = MOBILE (large fonts) */
body { font-size: 40px; }
h1 { font-size: 52px; }
h2 { font-size: 44px; }
p, li { font-size: 36px; }
.button { font-size: 40px; }

/* DESKTOP = smaller fonts */
@media (min-width: 1024px) {
    body { font-size: 24px; }
    h1 { font-size: 3.5rem; }
    h2 { font-size: 2rem; }
    p, li { font-size: 1.3rem; }
    .button { font-size: 1.8rem; }
}
```

**Minimum Mobile Font Sizes (px):**
| Element | Minimum Size |
|---------|--------------|
| Body text | 36-40px |
| H1 | 48-52px |
| H2 | 44px |
| Buttons/CTA | 40px |
| Labels | 34px |
| Form inputs | 34px |
| Footer | 32px |

**Alternative: vw units (viewport-relative)**
```css
body { font-size: 5vw; }   /* 5% of viewport width */
h1 { font-size: 8vw; }
h2 { font-size: 6vw; }

/* Clamp for min/max bounds */
body { font-size: clamp(20px, 5vw, 40px); }
```

**Testing Checklist:**
- [ ] Test on actual high-DPI phone (not just browser DevTools)
- [ ] OnePlus, Samsung Galaxy, iPhone 12+ are common high-DPI devices
- [ ] If text looks small on phone but fine in DevTools, you hit this issue

---

### User Role Analysis (MANDATORY)

**Before designing ANY interface, document user roles:**

For each user role, answer:
1. **Who are they?** (Role name, expertise level)
2. **What activities do they perform?** (Primary tasks)
3. **What are their goals?** (What they want to achieve)
4. **What is their intent?** (Why they use this interface)

**Example:**
```markdown
**Role: School Administrator**
- Activities: Add/edit slides, manage screens, view statistics
- Goals: Display school announcements efficiently, minimal time spent
- Intent: Keep students informed without technical complexity
```

**Design decisions must map to user roles** - If a feature doesn't serve a documented role's goals, question if it's needed.

---

### Data Table Standards (MANDATORY)

**Aanbevolen library: [Tabulator](https://tabulator.info/) v6+**
Tabulator is de standaard voor gestructureerde datatabellen in uNiek-projecten. Gebruik Tabulator via CDN:
```html
<link href="https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://unpkg.com/tabulator-tables@6.3.1/dist/js/tabulator.min.js"></script>
```

**Tabulator rendering richtlijnen:**
- Gebruik `layout: 'fitColumns'` voor automatische kolombreedte
- Tekstkleur automatisch bepalen via luminantie van achtergrondkleur (contrast-detectie):
  ```js
  const [r,g,b] = hexToRgb(bgColor);
  const lum = (0.299*r + 0.587*g + 0.114*b) / 255;
  const textColor = lum > 0.5 ? '#111111' : '#ffffff';
  ```
- Achtergrond altijd `transparent` — kleur komt van de container/template
- Alle Tabulator CDN-stijlen overschrijven met `!important` waar nodig voor theming
- Gebruik een `feature flag` (`TABULATOR_ENABLED`) voor gefaseerde uitrol

All tables displaying structured data MUST have:

**1. Sortable Columns**
- ✅ Click column header to sort (ascending/descending)
- ✅ Visual indicator (▲▼) for sort direction
- ✅ Default sort on most relevant column

**2. Filterable Columns**
- ✅ Filter inputs above or within column headers
- ✅ Real-time filtering (as user types) OR filter button
- ✅ Clear filters button

**3. Persistent Settings**
- ✅ Remember user's sort/filter preferences (localStorage or user profile)
- ✅ Restore settings on page reload
- ✅ "Reset to default" option

**4. Mobile-Friendly Tables**
- ❌ **NO double scrollbars** (horizontal + vertical = bad UX)
- ✅ Use responsive patterns:
  - **Card view** on mobile (each row = card with labels)
  - **Swipeable columns** (show 2-3 key columns, swipe for more)
  - **Expandable rows** (tap row to see all fields)
  - **Vertical layout** (fields stacked, labels visible)

**Example Mobile Table Pattern:**
```html
<!-- Desktop: Traditional table -->
<table class="desktop-only">...</table>

<!-- Mobile: Card view -->
<div class="mobile-cards">
  <div class="card">
    <div class="field"><label>Name:</label> John Doe</div>
    <div class="field"><label>Email:</label> john@example.com</div>
  </div>
</div>
```

---

### uNiek Solutions Branding (MANDATORY)

**EVERY web project MUST include:**

**1. Favicon (CRITICAL - NEVER SKIP)**
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```
- Location: Project root (public/web directory)
- Source: `/opt/design-system/unieksolutions/favicon/` (if exists) or create from logo

**2. Brand Colors**
```css
:root {
  --uniek-green: #AACA38;      /* Primary brand color */
  --uniek-orange: #F8AC2E;     /* Secondary accent */
  --uniek-dark: #1D1D1D;       /* Text/headings */
  --uniek-gray: #6B7280;       /* Secondary text */
  --uniek-light: #F5F5F5;      /* Backgrounds */
}
```

**3. Typography**
- **Font:** Quicksand (primary), system font stack (fallback)
- **Headings:** Quicksand Bold
- **Body:** Quicksand Regular (400)
- **Load from:** Google Fonts or self-hosted

**4. Logo Placement**
- Top-left corner (navigation)
- Footer (with copyright: "© 2026 uNiek Solutions")
- Link logo to homepage or dashboard

---

### Reusable Module Integration

**Standard Modules:**
- **uniek_iam** - Identity and Access Management (authentication, user management)
- **uniek_weare** - Team/organization management

**Integration Guidelines:**
1. **Clone as submodule or package dependency** (don't copy-paste code)
2. **Configuration via environment variables** (`.env`)
3. **Minimal customization** - Use module's default UI/UX where possible
4. **Override only when necessary** - Document customizations in ARCHITECTURE.md
5. **Keep modules updated** - Pull latest versions regularly

**Example Integration:**
```bash
# As git submodule
git submodule add https://github.com/unieksolutions/uniek_iam.git modules/iam

# As npm package (if applicable)
npm install @unieksolutions/iam
```

**Configuration:**
```bash
# .env
IAM_BASE_URL=https://iam.uniek.solutions
IAM_CLIENT_ID=project_xyz
IAM_CLIENT_SECRET=<secret>
```

---

### Open Source License Page (MANDATORY)

**Every project MUST have `/about` page listing:**

**1. All Open Source Dependencies**
- Library name
- Version used
- License type (MIT, Apache 2.0, GPL, etc.)
- Link to repository or license text

**2. Example `/about` Page:**
```html
<h1>About This Project</h1>
<p>Project description...</p>

<h2>Open Source Software Used</h2>
<table>
  <thead>
    <tr>
      <th>Library</th>
      <th>Version</th>
      <th>License</th>
      <th>Link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Plyr</td>
      <td>3.7.8</td>
      <td>MIT</td>
      <td><a href="https://github.com/sampotts/plyr">GitHub</a></td>
    </tr>
    <tr>
      <td>Tailwind CSS</td>
      <td>3.4.0</td>
      <td>MIT</td>
      <td><a href="https://tailwindcss.com">Website</a></td>
    </tr>
  </tbody>
</table>
```

**3. Generate License List:**
```bash
# For Node.js projects
npx license-checker --summary

# For Python projects
pip-licenses --format=markdown

# For PHP projects
composer licenses
```

**4. Keep Updated:**
- Regenerate when dependencies change
- Include in deployment checklist

---

## UI/UX Best Practices

### Navigation
- Clear, consistent navigation across all pages
- Breadcrumbs for deep hierarchies
- Active state for current page
- Mobile: Hamburger menu for space efficiency

### Forms
- Label every input field
- Show validation errors inline (near field)
- Disable submit button while processing
- Success/error messages prominent
- Required fields marked with asterisk (*)

### Loading States
- Show loading spinner for async operations
- Skeleton screens for initial page load
- Progress bars for long operations (>3 seconds)

### Accessibility
- Semantic HTML (header, nav, main, footer)
- Alt text for all images
- ARIA labels where needed
- Keyboard navigation support (tab order)
- Color contrast ratio ≥4.5:1 (WCAG AA)

### Performance
- Lazy load images below fold
- Minify CSS/JS for production
- Compress images (WebP format)
- Cache static assets
- Target: First Contentful Paint <2s

---

## Design Checklist

**Before deploying any web interface:**

**Screen & Responsive:**
- [ ] `screenCtx` utility aanwezig (`data-factor`/`data-touch` op `<html>`)
- [ ] Card dashboard gebruikt `auto-fill` + `minmax` (geen hardcoded kolommen)
- [ ] Tabulator: `responsiveLayout: "collapse"` + `responsive` per kolom
- [ ] Chart.js: `maintainAspectRatio: false` + CSS container-hoogte
- [ ] Getest op phone (360px touch), tablet (768px), desktop (1200px), wide (1920px)

**Accessibility:**
- [ ] a11y-bar aanwezig (taal / dyslexie / font-grootte / dag-nacht)
- [ ] OpenDyslexic font geladen
- [ ] Keyboard navigatie werkt (tab-volgorde logisch)
- [ ] Kleurcontrast ≥ 4.5:1 (WCAG AA)
- [ ] Alt-tekst op alle afbeeldingen

**Inhoud & Data:**
- [ ] User roles gedocumenteerd (activiteiten / doelen / intent)
- [ ] Datatabellen sorteerbaar en filterbaar
- [ ] Tabelinstellingen persistent (localStorage of profiel)
- [ ] Geen dubbele scrollbalken

**Huisstijl:**
- [ ] Favicon aanwezig en correct
- [ ] uNiek branding (kleuren, logo, Quicksand font) — OF tenant theming
- [ ] Multitenancy: `applyTenantTheme()` + "Maak een voorstel" knop (indien van toepassing)
- [ ] CSS custom properties `--brand-primary` / `--brand-secondary` als fallback

**Overig:**
- [ ] Herbruikbare modules geïntegreerd (indien van toepassing)
- [ ] `/about` pagina met OSS licenties
- [ ] Performance getest (< 2s First Contentful Paint)

---

## CLI Tool Design (If Applicable)

**For command-line interfaces:**

### Commands
- Clear, verb-based commands (`create`, `list`, `delete`)
- Consistent naming across all commands
- Help text for every command (`--help`)

### Output
- Concise by default, verbose with `--verbose`
- Structured output option (`--json`, `--yaml`)
- Color-coded (errors=red, success=green, info=blue)
- Progress bars for long operations

### Error Messages
- Clear, actionable error messages
- Suggest fixes ("Did you mean...?")
- Exit codes: 0=success, 1=error, 2=usage error

---

## API Service Design (If Applicable)

**For API-only services:**

### Endpoints
- RESTful conventions (GET, POST, PUT, DELETE)
- Versioned (`/v1/resource`)
- Consistent response format (JSON)
- Pagination for list endpoints

### Documentation
- OpenAPI/Swagger spec
- Interactive docs (Swagger UI, Redoc)
- Example requests/responses
- Authentication guide

### Error Responses
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": {}
  }
}
```

---

## Design System Reference

**For detailed design guidelines:**
- `/opt/design-system/unieksolutions/` - Brand assets, guidelines (if exists)
- `/opt/bootstrap/APIMCP.md` - API design patterns
- Project-specific mockups/wireframes (if created)

---

## Related Documentation

- **ARCHITECTURE.md** - Technical implementation of design decisions
- **START.md** - Available design tools and resources
- **/opt/bootstrap/APIMCP.md** - API design patterns

---

**Last Updated:** 2026-01-29
**Template Version:** 2.0 (Web design requirements added)
