# Scout — Functional Analysis (feature by feature)

Method: local source code (this workspace, git HEAD `a4b3fc0`) read in full for the web app and API; deployed behavior verified in a real Chrome session against https://scout-omega-seven.vercel.app on 2026-07-11/12. Every claim below is tagged **[Observed]** (seen live), **[Code]** (verified in source), or **[Inferred]** (evidence-based inference).

---

## 1. Authentication
- **Trigger**: any request without valid `scout_auth` cookie → 307 to `/login?from=<path>` [Observed].
- **Input**: single password, required. Validation: exact string match against `SITE_PASSWORD` env var, server-side (`web/lib/auth-actions.ts`) [Code].
- **Flow**: React 19 `useActionState` form → server action `login()` → on success sets cookie `scout_auth` = the site password itself (httpOnly, secure, sameSite=lax, maxAge 90 days) → redirect to `from` [Code]; login round-trip works on production [Observed].
- **Edge cases**: wrong password → `{error:"Wrong password."}` rendered inline [Code]. No rate limiting, no lockout, no CSRF token beyond Next's server-action defaults [Code].
- **Security observations** (see issues.md #9): cookie value equals the password (not a derived session token); single shared credential; API key is a single shared header key. Acceptable for a personal single-user tool; not multi-user ready.

## 2. Dashboard (`/`)
- **Server side**: `Promise.all` of `api.digest()`, `api.watchlist()` (catch→[]), `api.alerts()` (catch→[]) streamed behind Suspense [Code]. `dynamic="force-dynamic"` prevents build-time prerender [Code].
- **KPI row** [Observed + Code]: Monthly Sales = Σ round(score×5.2) per validation; Revenue = Σ round(score×5.2×buy_price×1.5); Margin = mean of (sell−buy−(sell×0.15+100))/sell where sell=buy×1.5. These are **heuristics labeled "Dynamic"**, not marketplace data (issues.md #4). Live values updated correctly after DB purge (12→8 validations; margin −18%→−5%) [Observed].
- **Action strip** [Code]: counts use `|| 1` and `|| 2` fallbacks — shows "1 price drop / 2 opportunities" even when zero (fabricated minimums, issues.md #3).
- **Recommended Next Actions** [Code+Observed]: picks first watchlist ASIN with score<60 else hardcoded `B08L7V6YF2`; score<75 else `B07W8P8M82`; middle card is fully static text. On current data the fallback fired: production showed **B08L7V6YF2, an ASIN not present in any dataset** [Observed].
- **Tabs** [Observed]: Watchlist table (search + category/verdict filters + CSV export, client-side); Radar tab (revenue/margin line chart scaled off the same heuristics; top-4 opportunity list); Bestsellers Explorer (list-type + category selects → server action `getCategoryTable` → live table + "review entrenchment" bar chart).
- **CSV export** [Code]: builds `data:text/csv` client-side from the watchlist array; quotes titles; no server call.
- **Row click → drawer**: see §3.

## 3. Product Detail Drawer (used on Dashboard, Watchlist, Alerts, Product Database)
- **Trigger**: "Inspect Details"/"Inspect"/"Analyze" button per row → `getDrawerDetails(asin)` server action → GET `/products/{asin}/drawer-details` [Code].
- **Deployed behavior**: **broken for every ASIN — HTTP 500** [Observed: B0FN87GSPK via UI; B0D4DZ7WL2, B0DSKNKCYX, B000000000 via direct API]. UI symptom: drawer opens and spins on "LOADING REAL-TIME METRICS..." indefinitely; error only in console [Observed].
- **Root cause** [Code, High confidence]: `api/main.py:418-419,451` reads `calc["weight_fee"]` and `calc["gst_on_amazon_fees"]`, but `profit_calculator.calculate()` returns `weight_or_pickpack_fee` and has no `gst_on_amazon_fees` key (`api/profit_calculator.py:100-110`) → `KeyError` on every request. Fix is a two-key rename (+ compute GST on fees or drop it).
- **Design intent** (once fixed) [Code]: merges latest snapshot + latest validation + my-products row; real fee math via `profit_calculator`; 7-day BSR/price chart from `db.get_history()`; audit checklist from title length / review count / rating / rank. Remaining honesty gaps: rating falls back to literal 4.2, reviews to 95; "Buy Box Status: Active (100% Share)" and "Fulfillment: FBA" removed per latest commit… **partially** — Buy Box/Fulfillment cards were removed from the API payload path but the drawer still renders estimated monthly sales as `reviews×1.5` [Code].

## 4. Product Sourcing Validator (`/validator`)
- **Inputs** [Observed]: ASIN (required, prefilled from `?asin=` query param [Code: `useSearchParams`]), buy price (default 100), weight (300g), GST (18%), fulfillment (easy_ship), optional category, two 1–5 sliders, notes.
- **Flow** [Code]: server action `scoreAsin` → POST `/validator/score` → `scorer.score_asin()` scrapes/reads data, computes weighted components (Demand 25 / Competition 20 / Margin 20 / Trend 15 / Differentiation 10 / Operational fit 10), **writes a row to `validations`**, then `updateTag("watchlist")` for read-your-own-writes.
- **Verified end-to-end** (2026-07-11, this build + this production API): B0D4DZ7WL2 @ ₹180 → 62.1 WATCH, real component breakdown, net margin 53.5%, sell ₹899 [Observed]. That row persists in production data [Observed in extraction].
- **Errors** [Code]: generic catch → "Couldn't score that ASIN…" message.

## 5. Profit & Fees Calculator (`/profit-calculator`)
- **Flow** [Code]: server action → POST `/profit-calculator` → pure computation from `fee_tables.json` (referral % by category/price band, closing fees by band, Easy Ship/FBA weight fees by zone, GST on fees, returns provision). No DB write.
- **Live production test** [Observed]: ₹499 sell / ₹150 buy / 300g / Electronics Accessories / Easy Ship / 18% / National → Verdict "Strong", Net margin 39.6%, ₹197.81/unit, breakeven ₹235, breakeven ACoS 44.6%, fees: referral ₹0.00, closing ₹10, fulfillment ₹63, returns provision ₹24.95, total ₹73.
- **Flag** (Low confidence): referral ₹0.00 for Electronics Accessories @ ₹499 — check `fee_tables.json` against Amazon.in's current rate card; zero-referral brackets exist but this is worth confirming (issues.md #10).

## 6. Amazon Product Database (`/product-database`)
- **Flow** [Code]: client filters (q, category, min/max price, min/max BSR) held as draft state, applied on submit → server action `searchProductDatabase` → GET `/product-database?...` → SQL over `snapshots` (`db.query_snapshots`, `count_snapshots`), paginated 25/page in UI.
- **Live** [Observed]: 3,680 products, 148 pages; Books rows match extraction exactly (see data-inventory.md). Pagination prev/next with disabled states [Code+Observed].
- **Row click** → same broken drawer (§3).

## 7. Activity / Alerts (`/alerts`)
- **Flow** [Code]: `alerts.compute_alerts()` compares the two most recent collection runs per watched (validated) ASIN: price_change, entered_top3, rank_climbing, rank_sliding, review_surge, dropped_from_list, severity high/medium/low.
- **Live** [Observed]: 3 alerts, all "LOW" (rank sliding #13→#23; dropped from Sports & Fitness top-30; dropped from Toys & Games top-30) with real timestamps (10–11 Jul 2026). Search + severity/type filters client-side [Code]. Honest empty state explains the 2-run requirement [Code].
- **Drawer from alert row** [Code]: parses ₹ price out of the alert message with regex, `|| 299` fallback — synthetic when absent (minor, issues.md #5-adjacent).

## 8. Keyword Suggestion Harvester (`/keywords`)
- **Claimed**: "runs 27 recursive queries (base + a–z) against Amazon's autocomplete" [Observed copy].
- **Flow** [Code]: server action `gatherKeywords` → 27 fetches to `completion.amazon.com/search-services/query-action?...&mkt=3...` in chunks of 5, position-weighted scoring, top-100 normalized to 1–100 relevancy, intent from word count.
- **Live production test** [Observed]: seed "phone case" → ~40s pending → **zero results, silent reset to idle state, no error UI, no console error**.
- **Root cause** [Observed at endpoint level]: `completion.amazon.com/search-services/query-action` returns an **empty HTML page, not JSON**, even from a residential connection — the upstream endpoint is dead/deprecated. Every `fetchSuggestions` throws on `res.json()`/shape-check and is swallowed → `[]`. The modern `completion.amazon.in/api/2017/suggestions` returned CloudFront 502 in a quick probe; a working replacement needs proper reverse-engineering of Amazon.in's current suggest XHR (not verifiable from public access here).
- **Verdict**: feature non-functional everywhere, fails silently (issues.md #2).

## 9. Listing Optimizer (`/listing`)
- **Tabs** [Observed]: "Live Listing Analyzer" and "Scribbles Keyword Sandbox" (Helium-10-Scribbles-style: paste keywords, live strike-through as they're used in title/bullets — client-only per code).
- **Analyzer flow** [Code]: POST `/listing/analyze` → `listing_analyzer.analyze_listing`: fetches Amazon **mobile** product page (`/gp/aw/d/{asin}`), rule-based scoring of title/bullets/images, category benchmark from own snapshots, peers table (top-8 from Trend Radar data), Review Miner (~8–10 embedded reviews); separate optional AI calls: `/listing/suggest`, `/listing/review-summary` (OpenRouter free tier; 503 with honest message when unavailable) [Code].
- **Live-scrape dependency**: results vary with Amazon bot-checks; endpoint returns 502 with explanation on fetch failure [Code]. Not re-exercised during this crawl (was verified working earlier on this build per WORKLOG and prior session).

## 10. My Products (`/my-products`)
- **Flow** [Code]: GET/POST `/my-products`, DELETE `/my-products/{asin}`; stats (SKUs, avg landed cost, avg target margin) computed client-side.
- **Live** [Observed]: shows the one row created during owner testing (B0D4DZ7WL2, ₹150+₹20, 30%); form defaults 150/20/30.
- **Validation** [Code]: ASIN required only; numbers not bounded (`valuemax=0` artifacts in a11y tree suggest missing max attrs — cosmetic).

## 11. Inventory Operations (`/inventory`)
- **Flow** [Code]: reads `/my-products`; **stock, lead time, velocity are client-side defaults** (100 units, 14 days, fixed daily velocity → "20 days cover", reorder date), not stored user data. "Update Levels" exists but no persistence path for stock levels was found in the API [Code].
- **Live** [Observed]: my saved product shows "100 units / 14 days / reorder 18 Jul 2026 (in 6d)" — synthesized (issues.md #5).

## 12. Listing Health (`/listing-health`)
- **Flow** [Code: `api/main.py:342-373`]: latest validation per ASIN + latest snapshot → gaps: title <150 chars, reviews <10, rating <4.0. "Score" column = the **validation opportunity score**, presented as "Listing Quality Score" [Observed 62.1%/62.6%] — misleading label (issues.md #6).

## 13. Competitor Analysis (`/competitor-analysis`)
- **Flow** [Code: `/products/compare`]: for each submitted ASIN (up to 5): latest snapshot + latest validation, returns price/rank/rating/reviews/score/verdict/found. Read-only. Missing ASINs → `found:false`, score fallback 50, verdict WATCH [Code].
- **Live**: form renders with add/remove slots [Observed]; compare submit not browser-tested (time-boxed).

## 14. Analytics (`/analytics`)
- **Flow** [Code]: aggregates validations client-side (totals, verdict counts, category counts, top-10 candidates, avg score bars).
- **Live** [Observed]: totals 8/2/65.9/0 consistent with post-purge DB. **Orphaned route** (no nav link) and **duplicate page header** (page.tsx h1 + client h1) [Observed].

## 15. Nightly data collection (background, not a page)
- **Flow** [Code: `.github/workflows/nightly-collect.yml` + `scraper/collector.py`]: GitHub Actions cron `45 20 * * *` UTC (02:15 IST) → scrapes Amazon.in bestseller/new-releases/most-wished-for/most-gifted lists for 31 categories → writes snapshots to Supabase Postgres (`DATABASE_URL` secret).
- **Evidence it runs**: digest `collection_dates`, alert timestamps of 10–11 Jul, 3,680 snapshot rows across 31 categories [Observed via API extraction]. Runtime logs not accessible from this audit (GitHub Actions UI not queried — no `gh` CLI available in this shell).
