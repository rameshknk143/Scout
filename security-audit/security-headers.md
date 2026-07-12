# Transport, Headers, Cookies, CORS

All observations from passive `curl` on 2026-07-12 (UTC).

## TLS / transport
- HTTPS enforced; valid cert (Vercel-managed). No mixed-content (single-origin app).
- **HSTS present and strong** on web: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (2 years) [/login and / both]. ✅
- API (Render/Cloudflare) responses did **not** show HSTS on `/health` — Cloudflare edge typically adds it, but not observed here (Low; the API is called server-side over HTTPS regardless).

## Web security headers — `/login` (200) and `/` (307)
| Header | Present? | Value / Note |
|---|---|---|
| `Strict-Transport-Security` | ✅ | 2y, includeSubDomains, preload |
| `Content-Security-Policy` | ❌ | **absent** — no XSS defense-in-depth |
| `X-Frame-Options` / CSP `frame-ancestors` | ❌ | **absent** — page is framable (clickjacking) |
| `X-Content-Type-Options` | ❌ | **absent** — MIME-sniffing not blocked |
| `Referrer-Policy` | ❌ | **absent** |
| `Permissions-Policy` | ❌ | **absent** |
| `Access-Control-Allow-Origin` | ⚠️ `*` | on the static login HTML (Vercel default for prerendered asset) |
| `Cache-Control` | ℹ️ | `public, max-age=0, must-revalidate` |
| `X-Vercel-*`, `X-Nextjs-*`, `Etag`, `Age` | ℹ️ | deployment metadata (normal, low value to attacker) |

→ See findings **SEC-01** (missing headers) and **SEC-02** (framable password page + ACAO:*).

## Cookies (from source; not re-elicited live to avoid a login POST)
- `scout_auth`: `httpOnly ✅`, `secure ✅`, `sameSite=lax ✅`, `path=/`, `maxAge 90d`.
- **Value = the site password** (not a random/derived session token) → finding **SEC-03**.
- `httpOnly` blocks JS theft; `secure` blocks plaintext; `sameSite=lax` mitigates cross-site POST CSRF. Good flags; weak value semantics.

## CORS posture (API)
- `GET /health` with `Origin: https://evil.example.com` → **200 but NO `Access-Control-Allow-Origin` header returned** → browsers cannot read the response cross-origin (default same-origin block). ✅
- `OPTIONS /watchlist` preflight → **405 `allow: GET`** → no `CORSMiddleware` mounted at all.
- Source confirms: **no `CORSMiddleware` / `add_middleware` anywhere** in `api/main.py` (grep: 0 matches). The `ALLOWED_ORIGINS` env in `render.yaml` is therefore **dead config** → finding **SEC-06**.
- Net effect: safe by default — the API is key-gated and called server-to-server; a browser on another origin cannot attach `X-Scout-Key` nor read responses. No credentialed-CORS wildcard risk (there is no cookie auth on the API).

## Redirects
- `http`/all unauth paths → 307 → `/login?from=<path>`. Open-redirect check: `from` is used as a post-login redirect target (`web/proxy.ts`/login). **Value is a same-origin path** in observed flows; whether an absolute external URL in `from` is honored was **not actively tested** (would be an active test) — flagged for Phase 3 (see remediation).

## Error handling (info-leak)
- Web: production masks details — "The specific message is omitted in production builds" [observed console]. ✅
- API 500 (drawer bug): returns generic `Internal Server Error`, **no stack trace / no framework internals leaked** [observed]. ✅
- Source maps: `<chunk>.js.map` → **403 Forbidden** (not served). ✅
- Well-known sensitive paths `/.env`, `/.env.local`, `/.git/config`, `/.git/HEAD`, `/package.json`, `/api/.env` → all **307 → login** (proxy catches; none served). ✅
