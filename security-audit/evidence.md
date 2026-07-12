# Evidence (sanitized)

All requests passive (GET/HEAD/OPTIONS), low rate, 2026-07-12 UTC. Secrets redacted.

## E1 — Web headers (`/login`, HTTP 200)
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Cache-Control: public, max-age=0, must-revalidate
Content-Type: text/html; charset=utf-8
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
X-Matched-Path: /login
X-Nextjs-Prerender: 1
X-Vercel-Cache: HIT
X-Vercel-Id: bom1::7pskd-…            (redacted tail)
```
Absent: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy → SEC-01, SEC-02.

## E2 — Auth gate (`/`, HTTP 307)
```
HTTP/1.1 307 Temporary Redirect
Location: /login?from=%2F
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

## E3 — API CORS posture
```
# GET /health  (Origin: https://evil.example.com)
HTTP/1.1 200 OK
Content-Type: application/json
Server: cloudflare
x-render-origin-server: uvicorn
# → NO Access-Control-Allow-Origin returned  (browser cannot read cross-origin)

# OPTIONS /watchlist  (preflight)
HTTP/1.1 405 Method Not Allowed
allow: GET
# → no CORSMiddleware mounted
```
→ SEC-06. Cross-check: `grep -n "CORS|add_middleware|allow_origins" api/*.py` = 0 matches.

## E4 — API auth enforced
```
# GET /watchlist  (no X-Scout-Key)
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

## E5 — No source-map / sensitive-file exposure
```
/_next/static/chunks/<hash>.js       → 200  (31,878 bytes)
/_next/static/chunks/<hash>.js.map   → 403
/.env  /.env.local  /.git/config  /.git/HEAD  /package.json  /api/.env  → 307 (→ /login)
```

## E6 — Cookie definition (source, redacted)
`web/lib/auth-actions.ts:20-26`
```
cookieStore.set("scout_auth", process.env.SITE_PASSWORD!, {
  httpOnly: true, secure: true, sameSite: "lax", path: "/",
  maxAge: 60 * 60 * 24 * 90,           // 90 days
});
```
Value = password → SEC-03; 90-day life → SEC-09.

## E7 — API error handling (no info leak)
`GET /products/B0D4DZ7WL2/drawer-details` (key present) → `HTTP 500`, body `Internal Server Error` (generic; no stack trace). [Functional bug tracked separately in ../audit-output/issues.md #1.]

## E8 — Dependency versions
`web/package-lock.json` (lockfileVersion 3): next 16.2.10, react/react-dom 19.2.4, three 0.185.1, framer-motion 12.42.2, recharts 3.9.2, @react-three/fiber 9.6.1, drei 10.7.7.
`api/requirements.txt`: fastapi>=0.115.0, uvicorn>=0.30.6, psycopg2-binary>=2.9.9, pandas>=2.2.2, pydantic>=2.9.2, requests>=2.32.5 → SEC-07.

## E9 — Browser passive observations (`/login`, real Chrome session)
- `document.cookie` → **empty** (auth cookie is httpOnly; no JS-readable cookie).
- `localStorage` / `sessionStorage` → **0 keys** each; no service worker. No client-side storage of any kind.
- Scripts on page: **12, all first-party** (`scout-omega-seven.vercel.app/_next/static/...`). No analytics/tracker/ad hosts.
- Meta tags: only `viewport`, `description` (no CSP `<meta>`).
- Password input `autocomplete=""` → console verbose hint suggests `new-password` (minor a11y/UX, not security-material).
- **Third-party asset (SEC-11):** network log shows
  `GET https://raw.githack.com/pmndrs/drei-assets/…/hdri/studio_small_03_1k.hdr → 301`
  `GET https://raw.githubusercontent.com/pmndrs/drei-assets/…/hdri/studio_small_03_1k.hdr → 304`
  triggered by `<Environment preset="studio" />` (`PremiumLanding.tsx:134`).
- Console: only Three.js deprecation warnings + the autocomplete hint — **no secrets/tokens logged**, no error leakage.
- Screenshot: `evidence-login.png`.

## Reproduction notes
Header checks: `curl -sI <url>` / `curl -s -D - -o /dev/null <url> -H "Origin: …"`. File checks: `curl -s -o /dev/null -w "%{http_code}" <url>`. No authentication used for any evidence above except E7 (owner API key, redacted). No data written, no forms submitted.
