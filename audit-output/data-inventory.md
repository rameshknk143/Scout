# Scout — Data Inventory

Important classification: **nothing on this site is truly public** except the login page and API `/health`. All datasets below sit behind the owner's password/API key and were extracted with **owner authorization** (the requester owns the site, repo, and credentials). "Public" in this report means "returned by the deployed service", not "world-readable".

| # | Dataset | Endpoint | Fields | Rows extracted | Update behavior | Extraction status |
|---|---|---|---|---|---|---|
| 1 | Bestseller snapshots ("Product Database") | GET `/product-database` | asin, title, category, rank, price, rating, review_count, image_url | **3,680 / 3,680** (37 pages, limit=100) | Nightly GitHub Actions cron 20:45 UTC (02:15 IST), 31 categories × 4 list types | ✅ complete; 0 dupes; 0 malformed |
| 2 | Categories | GET `/trend-radar/categories` | category | 31 | static list in code | ✅ |
| 3 | Weekly digest | GET `/trend-radar/digest` | new_entrants(rank,asin,title,price,rating,review_count,image_url), top_movers(asin,title,category,first_rank,latest_rank,delta), cross_category(asin,title,categories,num_categories,best_rank), collection_dates | 421 records + 1 dates record | derived at request time from snapshots | ✅ |
| 4 | Validations (watchlist) | GET `/watchlist` | id, asin, title, category, score, verdict, buy_price, notes, validated_at | 8 | written by Validator; purged of junk rows on 2026-07-11 | ✅ — **owner's own business data** (notes may contain sourcing info); keep private |
| 5 | Alerts | GET `/alerts` | asin, title, category, list_type, alert_type, severity, message, detail, detected_at | 3 | computed per request from last 2 collection runs | ✅ |
| 6 | My Products | GET `/my-products` | asin, title, sku, supplier_cost, shipping_fee, target_margin, supplier_details, created_at | 1 | owner-entered | ✅ — **owner's private sourcing data**; keep private |
| 7 | Listing health | GET `/listing-health` | asin, title, score, verdict, gaps[], price | 2 | derived per request | ✅ |
| 8 | Drawer details | GET `/products/{asin}/drawer-details` | (see functional-analysis §3) | 0 | — | ❌ endpoint 500s (issues.md #1) |
| 9 | Category tables | GET `/trend-radar/category/{c}?list_type=` | same as #1 subset | not bulk-extracted | same nightly source as #1 | ⏭ skipped — redundant with #1 (would be 124 more requests for the same snapshot rows); method documented in tools/extract.mjs pattern |
| 10 | Compare | POST `/products/compare` | per-ASIN snapshot+validation merge | not extracted | derived | ⏭ read-only, derived from #1/#4 |

## Provenance & validation
- Every JSONL record carries `_source_endpoint` and `_retrieved_at` (UTC ISO); product rows also `_page`. Request log: `tools/request-log.json` (43 requests, timestamps, status, attempt#).
- Validated against UI samples: "Yesteryear…" (ASIN 0008839042, Books, #13, ₹437, 63,709 reviews, 4.2★) and "The Intelligent Investor" (0062312685, #14, price null "—", 52,027, 4.5★) — extraction matches the deployed `/product-database` page exactly, including the null price rendering as "—".
- Category distribution across all 31 categories (top: Shoes & Handbags 170, Clothing & Accessories 169, Movies & TV 149 …), consistent with "31 categories × up to 30 ranks × 4 list types minus overlaps".
- Known data-quality quirks inside the dataset (upstream, not extraction): `title` null for some rows (UI shows "(no title)"), `price` null when Amazon page didn't expose it, ASINs starting `00…` are book ISBN-10s (normal for Amazon).

## Sensitive-data handling
- No third-party personal data encountered anywhere. Reviews are not stored server-side (Review Miner returns them per request; none extracted).
- Owner-sensitive fields (validation `notes`, my_products `supplier_details`) are present in `scraped-data.jsonl` because the owner requested a complete inventory — current rows contain empty/benign values ("" and none observed with supplier text). Recommendation: keep `audit-output/` out of git (it is currently untracked; see README).
- The API key and site password appear **nowhere** in these outputs (extractor reads the key at runtime from `web/.env.local`).
