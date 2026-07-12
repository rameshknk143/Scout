# Scout — Data-Flow & Storage Audit

Legend: **[O]** observed directly (live traffic/UI/API), **[C]** verified in local source code, **[I]** inferred from evidence, **[NV]** not verifiable from public access.

## Architecture (evidence-based)

```
Amazon.in public pages ──(nightly GitHub Actions cron, scraper/collector.py)──► Supabase Postgres [C]
                                                                                    │
Amazon.in mobile product page ──(on-demand, listing_analyzer)──► FastAPI on Render ◄┘
Amazon completion API (DEAD) ──(keywords server action)──► Vercel server action     │
OpenRouter free tier ──(listing suggest / review summary)──► FastAPI on Render      │
                                                                                    ▼
                              Next.js 16 (App Router, RSC) on Vercel ──► Browser (React 19)
                              server-only api.ts adds X-Scout-Key; key never in client bundle [C]
```

- Hosting web: Vercel (`Server: Vercel`, `X-Vercel-Id: bom1::…`) [O]. Framework: Next.js 16.2.10 + Turbopack, React 19 [C, and Next dev overlay observed on localhost].
- Hosting API: Render (`render.yaml`, service name `scout-api`; URL `scout-api-3yvy.onrender.com`) [C+O].
- Database: Supabase Postgres — `api/db.py` uses `psycopg2` with `DATABASE_URL`; api/main.py docstring says "talk to Supabase instead of a local SQLite file" [C]. Server-side only; **not directly reachable from the public site** [NV for its internal schema beyond what code shows].
- Analytics/trackers: none found — no third-party analytics scripts in `web/app/layout.tsx` or observed network traffic [O/C].
- Fonts: Google Fonts Inter via `next/font` (self-hosted at build) [C].

## Flow 1 — Login
`password (user) → <form action> POST (server action, Vercel) → compare vs SITE_PASSWORD env → Set-Cookie scout_auth=<password> httpOnly/secure/lax/90d → redirect` [C, O]
- Storage: single httpOnly cookie. No localStorage/sessionStorage use found anywhere in `web/` [C: no matches for localStorage/sessionStorage].
- Proxy check on every request: cookie value string-equals env [C].

## Flow 2 — Dashboard read path
`RSC render (Vercel) → api.digest()/watchlist()/alerts() → fetch https://scout-api-3yvy.onrender.com/* with X-Scout-Key header → FastAPI → pandas over Supabase → JSON → RSC props → HTML streamed to browser` [C, O]
- Caching [C]: reads use Next data-cache `revalidate: 60`; watchlist/alerts also tagged `"watchlist"`; validator writes call `updateTag("watchlist")` for read-your-own-writes.
- **Observed cache artifact** [O]: after a server-side DB purge, `/` served a stale 12-row watchlist while `/analytics` showed fresh 8 rows; a later reload of `/` showed 8. Stale-while-revalidate at the tag/data-cache layer — worth knowing when judging "is the purge done".

## Flow 3 — Validator write path
`form → scoreAsin server action → POST /validator/score (X-Scout-Key) → scorer.score_asin() → INSERT validations row (Supabase) → updateTag("watchlist") → UI result card` [C, O tested end-to-end]

## Flow 4 — Product Database query
`filter form (client state) → Apply → searchProductDatabase server action → GET /product-database?q&category&min_price&max_price&min_rank&max_rank&limit&offset → SQL WHERE over snapshots → {products,total} → client table + pagination` [C, O]

## Flow 5 — Drawer (broken)
`row click → getDrawerDetails(asin) → GET /products/{asin}/drawer-details → merge snapshot+validation+my_product → profit_calculator.calculate(...) → KeyError "weight_fee" → 500 → client catch → console.error → spinner forever` [C root cause, O behavior]

## Flow 6 — Keywords (broken upstream)
`seed → gatherKeywords server action (runs on Vercel) → 27× fetch completion.amazon.com …query-action → endpoint returns empty HTML (not JSON) → every parse swallowed → [] → UI idle state` [C, O; upstream deadness observed from independent network too]

## Flow 7 — Listing analyze (live scrape)
`ASIN → POST /listing/analyze → Render fetches https://www.amazon.in/gp/aw/d/{asin} (mobile page) → rule-based score + peers from own snapshots + embedded reviews → JSON` [C]; optional `/listing/suggest` & `/listing/review-summary` call OpenRouter (`api/ai_client.py`) [C]. Amazon bot-checks make results non-deterministic; 502 with message on fetch failure [C].

## Flow 8 — Nightly collection
`GitHub Actions cron 20:45 UTC → python scraper/collector.py → scrape 31 categories × 4 list types → INSERT snapshots (Supabase)` [C]; freshness evidenced by digest collection_dates and 10–11 Jul alert timestamps [O].

## Storage inventory

| Store | What | Where seen | Notes |
|---|---|---|---|
| Supabase Postgres | `snapshots` (3,680 rows visible via API), `validations` (8), `my_products` (1); history per ASIN | [C code paths; O via API] | Server-side only; connection string is a Render/Actions secret [NV contents beyond API surface] |
| Cookie `scout_auth` | session gate | [O, C] | value = site password; httpOnly, secure, lax, 90d |
| Next data cache (Vercel) | 60s revalidate + `watchlist` tag | [C; O staleness artifact] | |
| localStorage / sessionStorage | none used | [C] | |
| Client state | filters, drafts, tabs — React state only | [C] | lost on reload by design |

## Third parties (complete list found)
| Service | Role | Evidence |
|---|---|---|
| Vercel | web hosting + server actions | headers [O] |
| Render | FastAPI hosting | render.yaml [C], URL [O] |
| Supabase | Postgres | api/main.py docstring, psycopg2 + DATABASE_URL [C] |
| GitHub Actions | nightly scraper cron | workflow file [C] |
| Amazon.in | scraped data source (bestsellers, mobile product pages) | collector.py, listing_analyzer.py [C] |
| completion.amazon.com | keyword suggestions — **dead** | actions.ts [C]; empty-HTML response [O] |
| OpenRouter | optional AI suggestions/summaries | ai_client.py [C] |
| Google Fonts (build-time) | Inter font | layout.tsx [C] |

## Not verifiable from public access
- Supabase project internals (schema beyond code, RLS, backups) — would need Supabase dashboard access.
- Render/Vercel env values, logs, region config — would need dashboard access (500 stack trace inferred from source instead).
- GitHub Actions run history — no `gh` CLI/credentials in this shell.
- Which exact commit each platform is on — inferred High-confidence from behavior fingerprints (see final-report.md), but not read from a deploy API.
