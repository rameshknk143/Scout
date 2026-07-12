# Scrape / Access Log

## Rules & authorization
- `robots.txt`: does not exist on the deployed site (307 to /login) — no published crawl rules; site is private-by-design. No ToS page exists (personal tool).
- Authorization: site, repo, and credentials belong to the requester (owner). Login + keyed API access performed as owner-authorized. Boundary was flagged to the owner before authenticated work began.
- Rate limiting: 700 ms between API requests; retries ×3 with 1.5s/3s backoff. Total 43 requests over 242 s (≈0.18 req/s) against a free-tier Render service — deliberately gentle.

## Sessions
| When (UTC) | What | Result |
|---|---|---|
| 2026-07-11 ~19:15 | Unauthenticated probe: 16 paths + robots/sitemap + headers | all 307 except /login 200 |
| 2026-07-11 ~19:17 | API fingerprint: /health, keyless /watchlist (401), 6 keyed GETs + /watchlist/notes GET (405) | version = latest code; drawer-details 500 discovered |
| 2026-07-11 ~19:20–19:35 | Authenticated browser crawl of 14 routes; feature tests (drawer repro, keywords harvest, profit calc) | see site-map.md / functional-analysis.md |
| 2026-07-11 19:34:21–19:38:23 | Bulk extraction run (`tools/extract.mjs`) | 43 req, 0 failures |

## Extraction run detail (from tools/extract-summary.json)
- product-database: 37 pages × limit=100, offset 0→3600 → **3,680 rows** (total reported 3,680; 100% coverage)
- duplicates skipped: 0 · malformed skipped: 0 · request failures: 0 · retries used: 0
- small datasets: categories 31 · digest records 421+1 · watchlist 8 · alerts 3 · my-products 1 · listing-health 2 → 466 records
- outputs: `scraped-data.jsonl` (4,146 records, one JSON object/line, provenance fields `_source_endpoint`,`_retrieved_at`,`_page`) · `scraped-data.csv` (3,680 product rows + header) · `tools/request-log.json` (per-request timestamps/status/attempt)

## Skipped / rejected
- `/trend-radar/category/{c}` ×31×4: skipped as redundant (same snapshot rows as /product-database) — avoids 124 extra requests to a free-tier backend.
- `/products/{asin}/drawer-details`: rejected — endpoint 500s (bug, documented).
- POST endpoints (score, my-products write/delete, notes): not used for extraction; no new writes performed during the audit crawl.
- Amazon.in pages: not scraped directly by this audit (the app's own nightly collector data was used instead).

## Writes made to production during the overall engagement (disclosure)
- 2026-07-11 (earlier owner-requested live testing, prior to this audit prompt): 1 `validations` row (B0D4DZ7WL2, ₹180 → score 62.1) and 1 `my_products` row (B0D4DZ7WL2, ₹150+₹20, 30%). Both still present and visible in extracts. The audit crawl itself performed **zero** new writes.
- A junk-purge (commit `a4b3fc0`) executed by the other agent removed 4 older junk validations (B0FAKE12345, B0FN87GSPK, ₹100 test rows) between our first and second dashboard observations — first observation showed them via a ≤60s-stale cache; corrected in findings.
