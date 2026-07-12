# Scout — Site Map & Route Inventory

Deployed site: https://scout-omega-seven.vercel.app/ (Vercel, `bom1` region observed in `X-Vercel-Id`)
Backend API: https://scout-api-3yvy.onrender.com (Render, FastAPI)
Deployed version evidence: behavior matches local git HEAD `a4b3fc0` (see final-report.md §Deployment provenance).
Crawl method: every route probed unauthenticated (curl, 2026-07-11), then every route visited authenticated in a real Chrome session (owner-authorized login).

## Public (unauthenticated) surface

| URL | Status | Notes |
|---|---|---|
| `/login` | 200 | The only public page. Light theme, 3D hero (three.js), single password field + Sign In. Footer: "Version 1.0 • © 2026 KNK Enterprises". |
| Every other path | 307 → `/login?from=<path>` | Auth proxy (`web/proxy.ts`) matches all paths except `_next/static`, `_next/image`, `favicon.ico`. Nonexistent paths behave identically to real ones (no route enumeration leak). |
| `/robots.txt` | 307 → login | Does not exist; intercepted by proxy. No crawl rules published. |
| `/sitemap.xml` | 307 → login | Does not exist. |
| API `/health` | 200 `{"ok":true}` | Only unauthenticated API endpoint. |
| API all others | 401 without `X-Scout-Key` header | Shared-key auth. |

## Authenticated route map (all verified loading on production, 2026-07-11/12)

| Route | Title / Purpose | Key UI | Data source | Status |
|---|---|---|---|---|
| `/` | Dashboard ("Good evening, Ram") | KPI cards ×5, Action strip, Recommended Next Actions ×3, tabs: Catalog & Watchlist / Business Performance & Radar / Bestsellers Category Explorer; per-row "Inspect Details" drawer | `api.digest()`, `api.watchlist()`, `api.alerts()` (server components) | Loads. **Drawer broken (500)** — see issues.md #1. Next-Actions card shows hardcoded fallback ASIN — issues.md #3 |
| `/login` | Sign In | Password form (server action `login`) | `SITE_PASSWORD` env | Works; sets `scout_auth` cookie (httpOnly, secure, 90d) |
| `/alerts` | Activity / Alerts Log | Info note, search, severity/type filters, table | `api.alerts()` | Works; 3 real alerts shown |
| `/validator` | Product Sourcing Validator | ASIN + cost/weight/GST/fulfillment/category form, 2 sliders, score result card | POST `/validator/score` (writes a validation row) | Loads on prod; full submit flow verified previous day on same build+API (score 62.1 result observed). Not re-submitted during this crawl to avoid extra DB writes |
| `/product-database` | Amazon Product Database | Search, category select, price/BSR min-max filters, paginated table (25/page), row drawer | GET `/product-database` | Works; "3,680 products found", Page 1 of 148 |
| `/competitor-analysis` | Competitor Analysis | Up to 5 ASIN inputs, "Compare side-by-side" | POST `/products/compare` (read-only per source) | Form loads. Compare submit not exercised in browser (time-boxed); endpoint verified read-only in code |
| `/keywords` | Keyword Suggestion Harvester | Seed keyword input, results table (relevancy/intent) | Server action → `completion.amazon.com` | Page loads; **feature dead** — returns 0 results silently, upstream endpoint returns empty HTML (issues.md #2) |
| `/watchlist` | Trend Explorer & Watchlist | Search, category/verdict filters, CSV export, table + drawer | `api.watchlist()` | Works; "8 of 8 opportunity validations shown" |
| `/my-products` | My Products | Stats row, Add Catalog Listing form, trackings table with Remove | GET/POST/DELETE `/my-products` | Works; shows 1 saved product (created during owner testing) |
| `/listing` | Listing Quality Score / Optimizer | Tabs: Live Listing Analyzer / Scribbles Keyword Sandbox; ASIN + category form | POST `/listing/analyze`, `/listing/suggest`, `/listing/review-summary` | Loads; analyze flow exercised on this build previously (live Amazon scrape — can vary run to run) |
| `/listing-health` | Listing Health | Stats (Audited 2, Avg 62.4%, Alerts 0), audit table with gaps | GET `/listing-health` | Works; note: "quality score" equals the validation *opportunity* score (issues.md #6) |
| `/inventory` | Inventory Operations | Stats, Active Stock Audits table, Update Levels | GET `/my-products` + client-side defaults | Loads; **stock figures are synthesized defaults** (100 units / 14d lead) not user data — issues.md #5 |
| `/analytics` | Analytics | Stat grid, verdict/category charts, top candidates, avg-score bars | `api.watchlist()` | Loads **but orphaned — no sidebar link** (direct URL only) and renders a duplicate "Analytics" header — issues.md #7 |
| `/profit-calculator` | Profit & Amazon Fees Calculator | Price/cost/weight/category/fulfillment/GST/zone form, verdict + fee breakdown | POST `/profit-calculator` (pure computation) | Works; live test: ₹499/₹150/300g/Electronics Acc./Easy Ship → Strong, 39.6%, ₹197.81/unit |

## Navigation notes
- Sidebar sections: Overview / Research / Catalog & Listings / Operations. All items now enabled (no disabled placeholders remain in this build).
- Sidebar "Settings" and "Documentation" links are `href="#"` — dead links (issues.md #8).
- Top bar global search, date-range selector ("Last 30 Days"), and notification bell are visual-only — no handlers (issues.md #8).
- `/analytics` is reachable but not linked from anywhere.

## Broken behavior observed during crawl
- Product detail drawer: every "Inspect Details" opens a right slide-over stuck at "LOADING REAL-TIME METRICS..." forever (API 500). Console: `Failed to load resource: 500` + masked Server Components error.
- Two transient `Page.captureScreenshot` timeouts during crawling (tooling, not site).
- `THREE.WebGLRenderer: Context Lost` console log after login navigation (login page's 3D canvas being torn down; cosmetic).
- A11y console issues on login: "No label associated with a form field", "form field should have id/name" (6×).
