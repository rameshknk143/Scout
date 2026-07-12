# Data & Privacy Review

## Data collected / stored (from source + observed API)
| Data | Where | Sensitivity | Notes |
|---|---|---|---|
| Site password | env `SITE_PASSWORD`; mirrored into `scout_auth` cookie | High (it's the only credential) | single shared secret |
| API key | env `API_KEY`; sent as `X-Scout-Key` server-side | High | single shared key; not in client bundle |
| DB connection string | Render env `DATABASE_URL` | High | server-side only; not web-reachable |
| Bestseller snapshots | Supabase `snapshots` (~3,680 rows) | Low (public marketplace data) | scraped from Amazon.in |
| Validations / watchlist | Supabase `validations` | Medium | owner's sourcing decisions + free-text `notes` |
| My Products | Supabase `my_products` | Medium | supplier cost / `supplier_details` free text |
| Amazon reviews (Review Miner) | not persisted | Low | fetched per request, returned, not stored [code] |

No end-user PII is collected (single-operator tool; no registration, no profiles, no emails, no payment data).

## Browser storage
- `localStorage` / `sessionStorage`: **not used** — verified live: 0 keys each on `/login`; grep: 0 matches in `web/`. No service worker.
- Cookies: only `scout_auth` (httpOnly — verified live: `document.cookie` empty in-browser).
- Client state is in-memory React only.

## Third-party browser requests (observed live on /login)
- **drei HDRI environment map** fetched from `raw.githack.com` → `raw.githubusercontent.com` (`pmndrs/drei-assets`) via `<Environment preset="studio" />`. Leaks each visitor's IP + referer to GitHub/githack and creates an external availability/supply-chain dependency. Privacy impact Low (no PII in the request), but it's the only cross-origin call the browser makes. → SEC-11. Fix: self-host the .hdr.
- No analytics, ads, fonts-CDN (Inter is self-hosted via `next/font`), or tag managers.

## Transmission
- All traffic HTTPS. Web ↔ API over HTTPS with server-side key header. No third-party analytics/ad beacons observed or in code.
- Egress to third parties: Amazon.in (scrape), OpenRouter (optional AI text — sends listing titles/bullets/reviews, i.e. public product copy, not user PII), Supabase (DB writes).

## Privacy disclosures
- No privacy policy, cookie banner, or ToS page exists (307→login for everything) — acceptable for a private single-user tool; would be required if it ever serves other users.

## Retention
- No retention/deletion mechanism for `validations`/`my_products` beyond manual DB edits. Nightly snapshots accumulate (no visible pruning) — storage-growth/hygiene note, not a privacy risk (public data).

## Privacy risk summary
Low overall, because there are no third-party end users and no PII. The meaningful confidentiality asset is the **owner's own sourcing intelligence** (validations notes, supplier details), protected only by the single shared password — see findings SEC-03/SEC-04/SEC-10.
