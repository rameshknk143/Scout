# Remediation Plan (prioritized)

## P1 — Quick, high-value (do first)
1. **Add security headers (SEC-01, SEC-02).** In `web/next.config.ts` add an async `headers()` returning for all routes:
   - `Content-Security-Policy` — start report-only, then enforce: `default-src 'self'; script-src 'self' 'unsafe-inline'` (tighten once Next inline needs are known) `; frame-ancestors 'none'; base-uri 'none'; object-src 'none'`
   - `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`
   - Remove/av oid `Access-Control-Allow-Origin: *` on HTML routes.
   Effort: ~30 min. Verifies with `curl -I`.
2. **Stop using the password as the cookie value (SEC-03).** Set `scout_auth` to a random opaque token (or HMAC-signed value keyed by a server secret); compare in `proxy.ts` against the signed value. Enables rotation + revocation. Effort: ~1 hr.
3. **Add a logout + shorten session (SEC-09).** A route/action that clears the cookie; drop lifetime to e.g. 7–14 days or sliding. Effort: ~20 min.

## P1 (cont.)
3b. **Self-host the drei HDRI (SEC-11).** Download `studio_small_03_1k.hdr`, place under `web/public/hdri/`, and change `<Environment preset="studio" />` → `<Environment files="/hdri/studio_small_03_1k.hdr" />` (and the `night` preset in `HeroScene.tsx` similarly). Removes the githubusercontent/githack dependency and unblocks a strict `connect-src 'self'` CSP. Effort: ~20 min.

## P2 — Hardening
4. **Login rate limiting (SEC-04).** Add Upstash/Vercel-KV ratelimit in the login action (e.g. 5/min/IP + exponential backoff). Keep the password ≥64-bit random. Effort: ~1 hr.
5. **Remove dead CORS config (SEC-06).** Delete `ALLOWED_ORIGINS` from `render.yaml`, or if the API will ever be browser-called, mount `CORSMiddleware` with an explicit allowlist (never `*` with credentials). Effort: 10 min.
6. **Pin Python deps + add scanning (SEC-07).** Generate `requirements.lock` (pip-tools/uv) with hashes; add `pip-audit` (api) and `npm audit --omit=dev` (web) to CI. Effort: ~1 hr.
7. **Secret hygiene (SEC-08).** Confirm `.gitignore` covers `.env*`; rotate `SITE_PASSWORD` + `API_KEY` if they've ever been shared in chat/logs/screenshots. Effort: 15 min.

## P3 — After written approval, verify by safe active test (Phase 3)
Run only these, slow and non-destructive, then re-classify findings:
- **Open redirect (SEC-10):** `GET /login?from=https://example.com`, observe post-login `Location`. Fix = enforce `from.startsWith("/")`.
- **CSRF on server actions:** confirm Next 16 Origin-validation is active for `scoreAsin`/`saveMyProduct`/`deleteMyProduct`.
- **IDOR:** `/products/{asin}/drawer-details`, `/my-products/{asin}` — single-user so low, but confirm no tenant assumptions.
- **Input validation:** benign boundary values on numeric API fields (negative/huge) — observe validation, no injection payloads.
- **Auth forced-browsing:** confirm no gated route renders without a valid cookie (spot-check 2–3 with no cookie — already 307 in passive run).

## Notes
- The API's "no CORS + key-gated + server-side-only key" posture is already sound — don't "fix" it by adding permissive CORS.
- These are hardening items on a **single-user personal tool**; none are Critical/High. Priority order assumes you may later expose it more widely — if so, P1+P4 become mandatory before that.
