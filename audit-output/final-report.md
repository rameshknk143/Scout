# Scout Deployed-Site Audit — Final Report

**Target**: https://scout-omega-seven.vercel.app (web, Vercel) + https://scout-api-3yvy.onrender.com (API, Render)
**Audited**: 2026-07-11/12 (UTC) · **Auditor**: Claude Code, with full local source access (this workspace) and owner-authorized credentials
**Scope**: public surface, authenticated surface (owner login), API contract, data flows, full data extraction. No security controls bypassed; no destructive actions; zero new writes during the audit crawl.

---

## Executive summary

Scout is a genuinely working personal product-intelligence system: a password-gated Next.js 16 app on Vercel, a keyed FastAPI backend on Render, a Supabase Postgres store, and a nightly GitHub-Actions scraper that has real, fresh data in it (3,680 bestseller snapshots across 31 Amazon.in categories; alerts computed from run-over-run changes as recently as 11 Jul). The core decision tools — **Validator, Profit Calculator, Product Database, Alerts, Watchlist, My Products** — work end-to-end on production and compute from real data.

Two features are **broken on production right now**, and both fail silently or near-silently:

1. **Product Detail Drawer** (the most-clicked element, used on 4 pages) — every open → API 500 → infinite spinner. Root-caused to exact lines: `api/main.py:418-419,451` read dict keys (`weight_fee`, `gst_on_amazon_fees`) that `profit_calculator.calculate()` never returns (`weight_or_pickpack_fee`, no GST-on-fees key) → `KeyError` for all ASINs. Introduced by the newest commit `a4b3fc0` — the very commit that "resolved final code review findings." Two-line fix.
2. **Keyword Harvester** — the upstream `completion.amazon.com` endpoint is dead (returns empty HTML from any network); all 27 sub-queries silently swallow errors → always "0 results" with no error UI.

A third class of issue is **fabricated-looking data presented as operational fact**: the dashboard's "Recommended Next Actions" currently tells the owner to restock **B08L7V6YF2** — a hardcoded fallback ASIN that exists nowhere in the data; the Inventory page invents "100 units / reorder 18 Jul"; KPI revenue (₹1.81 crore) is a score-based heuristic labeled only "Dynamic"; Listing Health relabels the sourcing-opportunity score as "Listing Quality Score." For a tool meant to drive purchasing decisions, these are the highest-priority credibility fixes after the two hard breaks.

Security is appropriate for a single-user personal tool (everything gated, no route enumeration leak, API key kept server-side) with known non-scalable shortcuts (cookie = password, one shared key, no login rate-limit).

## Deployment provenance (how we know what's live)
- Local git HEAD: `a4b3fc0`. This shell cannot reach GitHub (no credentials), so refs weren't compared directly — instead the deployment was **fingerprinted**: the production API serves endpoints that exist only in the newest commits (`/product-database`, `/my-products`, `/listing-health`, `/watchlist/notes` → 405 on GET) and exhibits the drawer `KeyError` that only `a4b3fc0` can produce (earlier code returned 200 on the same route, observed same-day). The web build shows the newest UI (light theme, all 12 nav items, no duplicate-key console error → the `a4b3fc0` rowKey fix). **Conclusion (High confidence)**: both Vercel and Render run code equivalent to local HEAD `a4b3fc0`; the GitHub remote receives pushes from the other agent's environment and both platforms auto-deploy from it.
- Corollary: during the audit window the DB junk-purge landed live (12 → 8 validations), which initially masqueraded as "purge didn't work" via a ≤60 s stale cache — corrected in findings (issues.md, corrections section).

## What was tested (coverage)
- **Pages**: 14/14 discovered routes loaded authenticated on production (route list from source = exhaustive; nonexistent-path behavior verified separately). 1 public page tested unauthenticated. Coverage method: source-derived route map × live crawl.
- **Features exercised live on production**: login, dashboard tabs & filters, drawer (bug repro ×2 surfaces + 3 ASINs via API), alerts table/filters, product-database search+pagination (UI + full API pull), keywords harvest (failure repro), profit calculator (full computation), my-products list, inventory, listing page tabs, listing-health, analytics, watchlist. **Exercised on this exact build earlier (same prod API), not repeated to avoid writes**: validator submit (wrote 62.1-score row that is visible in today's extraction), my-products save. **Not exercised**: my-products DELETE (destructive), compare submit & listing analyze re-run (time-boxed; endpoints verified read-only in source), `/listing/suggest`+`review-summary` AI calls (external cost; 503-path verified in code).
- **Endpoints observed/documented**: 24 (network-endpoints.csv) — 100% of the API surface defined in `api/main.py`.
- **Records extracted**: 4,146 (3,680 product snapshots = 100% of reported total; 466 auxiliary). 43 requests, 0 failures, 0 duplicates, 0 malformed, ~0.18 req/s. Sample-validated against the deployed UI.

## Key numbers
| Metric | Value |
|---|---|
| Public pages | 1 (`/login`) + API `/health` |
| Authenticated routes | 14, all load |
| Working features | 10 of 13 user-facing features fully functional |
| Broken features | 2 hard-broken (drawer, keywords), 1 orphaned page (analytics) |
| Data extracted | 3,680/3,680 products + 466 aux records, full provenance |
| Console errors on prod | drawer 500 (repro), THREE context-lost (cosmetic), a11y form-label issues |
| New writes by audit | 0 (2 disclosed rows from prior owner-requested testing) |

## Priority recommendations
1. **Fix drawer 500** — rename `calc["weight_fee"]`→`calc["weight_or_pickpack_fee"]`, replace `gst_on_amazon_fees` with `amazon_fees_subtotal*0.18` or drop; add an error state to the drawer UI. (Minutes of work; restores the most-used interaction.)
2. **Kill or fix silent failures** — keywords: show upstream-error state; drawer: same. A tool that silently shows nothing teaches you to distrust it.
3. **Remove fabricated specifics** — hardcoded fallback ASINs in Next Actions, `|| 1`/`|| 2` alert counts, invented inventory stock, mislabeled "Listing Quality Score", `|| 299` price fallback. Prefer honest empty states (the codebase already does this well elsewhere — e.g. Alerts' cold-start note).
4. **Label KPI heuristics as estimates** (or compute from snapshot prices).
5. Re-link or remove `/analytics` (and its duplicate header); delete orphaned components; add the missing WORKLOG entries (2 days of work + 2 production incidents currently unlogged).
6. When convenient: login rate-limit + random session token instead of password-as-cookie (before this ever becomes multi-user).

## Limitations
- Server logs (Render/Vercel), Supabase internals, GitHub Actions history, and platform configs were **not accessible** from this environment — the 500's stack trace is code-derived (High confidence), not log-confirmed.
- Deployed-commit identity is fingerprint-inferred (High confidence), not read from a deploy API.
- Amazon-scrape-dependent features (listing analyzer) are non-deterministic by nature; a single-day audit can't characterize their reliability distribution.
- `/trend-radar/category/*` tables were not bulk-pulled (redundant with the product-database dataset); compare/AI endpoints not exercised live (documented from source).

## Deliverables index
`README.md` · `site-map.md` · `functional-analysis.md` · `data-flow.md` · `network-endpoints.csv` · `data-inventory.md` · `scraped-data.csv` (3,680 rows) · `scraped-data.jsonl` (4,146 records) · `scrape-log.md` · `issues.md` · `tools/` (extractor + request log + summary)
