# Attack Surface Inventory

## Technologies (evidence-backed)
| Layer | Tech | Evidence |
|---|---|---|
| Web host | Vercel | `Server: Vercel`, `X-Vercel-Id: bom1::…`, `X-Vercel-Cache: HIT` [live headers] |
| Web framework | Next.js 16.2.10 (App Router, RSC, Turbopack), React 19.2.4 | `package-lock.json` [exact]; `X-Nextjs-Prerender`, `Vary: rsc,next-router-*` [live] |
| API host | Render, behind Cloudflare | `x-render-origin-server: uvicorn`, `Server: cloudflare` [live]; `render.yaml` [code] |
| API framework | FastAPI + Uvicorn (Python) | `api/main.py`, `api/requirements.txt` [code] |
| Database | Supabase Postgres | `api/db.py` psycopg2 + `DATABASE_URL`; `api/main.py` docstring [code] |
| Nightly job | GitHub Actions cron | `.github/workflows/nightly-collect.yml` [code] |
| Optional AI | OpenRouter (free tier) | `api/ai_client.py` [code] |
| Analytics/trackers | **None found** | no scripts in `web/app/layout.tsx`; no tracker requests observed [code+live] |

## Web routes (all gated except /login)
- Public: `/login` (200). Everything else → **307 → `/login?from=<path>`** via `web/proxy.ts` matcher `((?!_next/static|_next/image|favicon.ico).*)`.
- Authenticated app routes (14): `/`, `/alerts`, `/analytics`, `/keywords`, `/listing`, `/listing-health`, `/product-database`, `/profit-calculator`, `/validator`, `/watchlist`, `/my-products`, `/inventory`, `/competitor-analysis`. (Full behavior in ../audit-output/site-map.md.)
- Nonexistent paths behave identically to real ones (307) → **no route-enumeration oracle** [live].

## Forms / input surfaces
| Form | Route | Method | State-changing? |
|---|---|---|---|
| Login (password) | `/login` | server action `login` | sets cookie |
| Validator | `/validator` | server action → POST `/validator/score` | **writes DB row** |
| My Products add | `/my-products` | server action → POST `/my-products` | **writes DB row** |
| My Products remove | `/my-products` | → DELETE `/my-products/{asin}` | **deletes DB row** |
| Watchlist notes | drawer | → POST `/watchlist/notes` | writes |
| Profit calc | `/profit-calculator` | POST `/profit-calculator` | no write (pure calc) |
| Product DB filters | `/product-database` | GET `/product-database` | no write |
| Competitor compare | `/competitor-analysis` | POST `/products/compare` | no write |
| Keyword harvest | `/keywords` | server action → external Amazon endpoint | no write (dead upstream) |
| Listing analyze | `/listing` | POST `/listing/analyze` (+ AI) | no write |

Client input validation is minimal (numeric fields lack max bounds); server side uses Pydantic models for typed API params [code]. **Input-handling exploit testing withheld pending active-test approval.**

## API endpoints (24) — auth model
- All except `GET /health` require header `X-Scout-Key == API_KEY` (single shared key) [`api/main.py: require_key`].
- Keyless request → **401** [live: `/watchlist` without key].
- Key is injected **server-side only** (`web/lib/api.ts` has `import "server-only"`) → never reaches the browser bundle [code].
- Full endpoint table: ../audit-output/network-endpoints.csv.

## Auth / session (from source)
- Password gate: `web/lib/auth-actions.ts` compares to `SITE_PASSWORD`; sets cookie `scout_auth` = **the password value itself**, `httpOnly, secure, sameSite=lax, path=/, maxAge 90d`.
- Proxy: `web/proxy.ts` optimistic cookie check (string-equals env), no server session store.
- No registration, no logout, no password reset, no MFA (single-user design).

## Secrets management
- `web/.env.local`: `API_URL`, `SITE_PASSWORD`, `API_KEY` (plaintext, local). Untracked (git status: not listed).
- `render.yaml`: `DATABASE_URL`, `API_KEY` marked `sync:false` (set in Render dashboard); `ALLOWED_ORIGINS` hardcoded to `http://localhost:3000` — **but no code consumes it** (see findings SEC-06).
- Helper scripts `set_github_secret.py`, `migrate_data.py` handle secrets locally [code] — not web-exposed.

## Third-party data egress
Amazon.in (scrape source), OpenRouter (optional AI), Supabase (DB), completion.amazon.com (dead). No user PII leaves to third parties; no ad/analytics beacons.
