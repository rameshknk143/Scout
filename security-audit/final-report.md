# Scout — Security Audit, Final Report

**Target:** https://scout-omega-seven.vercel.app/ (web) + backend https://scout-api-3yvy.onrender.com
**Date:** 2026-07-12 (UTC) · **Type:** Passive assessment (Phase 1–2) + full local source review · **Active testing (Phase 3): NOT performed — awaiting written approval**

## 1. Scope tested
- The exact host `scout-omega-seven.vercel.app`, its public/gated routes and static assets.
- The backend it calls (`scout-api-3yvy.onrender.com`) — headers/CORS/auth observed passively; treated as in-scope because it is the app's own data plane and the requester owns it.
- Local source in this workspace (`web/`, `api/`, `render.yaml`, lockfiles).

## 2. Authorization for active testing
**Not granted in writing yet.** Ownership is established (requester's own repo/deployments/credentials, owner-directed session), which authorizes passive assessment and owner reads. Active tests (injection/fuzzing, auth-bypass, open-redirect probe, CSRF/IDOR checks, rate-limit testing, any state change) are **withheld** until you reply with explicit approval. Nothing was brute-forced, no forms were submitted, no data was written or read beyond owner-authorized passive observation.

## 3. Attack-surface inventory (summary)
Next.js 16.2.10 (Vercel) → server-side `X-Scout-Key` → FastAPI (Render/Cloudflare) → Supabase Postgres; nightly GitHub-Actions scraper; optional OpenRouter AI. One public page (`/login`); 14 gated app routes; 24 API endpoints (all key-gated except `/health`). No browser storage; no trackers; one third-party asset (drei HDRI). Full detail: `attack-surface.md`, and the functional map in `../audit-output/`.

## 4. Confirmed findings (11 total; none Critical/High)
| ID | Title | Severity | Confidence |
|---|---|---|---|
| SEC-01 | Missing security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy) | Medium | Confirmed |
| SEC-02 | Login (password) page framable + `ACAO: *` → clickjacking | Medium | Confirmed |
| SEC-03 | Session cookie value **is** the site password (not a revocable token) | Medium | Confirmed |
| SEC-04 | No login rate limiting / lockout | Medium | High |
| SEC-05 | Credential-as-cookie + no CSP ⇒ amplified XSS blast radius (compound) | Medium | High |
| SEC-06 | `ALLOWED_ORIGINS` set but no CORS middleware consumes it (dead config) | Low | Confirmed |
| SEC-07 | Python API deps unpinned (`>=`), no lockfile/hashes | Low | Confirmed |
| SEC-08 | Secrets in plaintext `web/.env.local` (must stay untracked) | Low | Confirmed |
| SEC-09 | No logout; 90-day session | Low | Confirmed |
| SEC-10 | `from` post-login redirect — open-redirect **not verified** (needs Phase 3) | Informational | Not verifiable |
| SEC-11 | Login page loads third-party HDRI from githubusercontent/githack | Low | Confirmed |

**Overall risk: LOW** for the current single-user, password-gated, no-PII personal tool. The theme across findings is *defense-in-depth and credential hygiene*, not an open door. If this is ever exposed to more users, SEC-01/03/04 become important to fix first.

## 5. Controls confirmed working (positives)
Strong HSTS (2y preload) · HTTPS everywhere · no source-map exposure (`.map`→403) · no sensitive-file exposure (`.env`/`.git`→307) · API key server-side only + API enforces 401 · cookie httpOnly+secure+sameSite=lax (httpOnly verified in-browser) · production error masking, API 500 leaks no stack trace · no route-enumeration oracle · no browser storage, no trackers · current dependency versions, reproducible web build.

## 6. Coverage & what was NOT tested
**Verified:** transport/headers/TLS/redirects, cookie flags, CORS posture (headers + source), source-map/file exposure, client bundle + browser storage + console, dependency versions, auth/session design (source present), third-party egress.
**Not verifiable from here:** Supabase RLS/network config, Render/Vercel platform settings, edge WAF/rate-limit rules, actual cloud secret values, GitHub Actions run history — **the running infrastructure's server-side and database security could not be fully verified from public access; only the source code was.**
**Intentionally not done (Phase 3 gate):** open-redirect (SEC-10), CSRF on server actions, IDOR on `/…/{asin}` routes, input-validation/injection payloads, rate-limit behavior, forced-browsing — all listed with safe methods in `remediation-plan.md §P3`.

## 7. Next steps
1. Reply **"yes, run active tests"** to authorize the Phase 3 safe verification set (esp. SEC-10 open-redirect and CSRF/IDOR spot-checks) — all non-destructive, slow, no data change.
2. Independently, apply P1 quick wins: security headers (SEC-01/02), token-not-password cookie (SEC-03), logout + shorter session (SEC-09). See `remediation-plan.md`.

## Deliverables
`README.md` · `attack-surface.md` · `security-headers.md` · `data-privacy.md` · `dependency-review.md` · `findings.md` (11) · `evidence.md` (+`evidence-login.png`) · `remediation-plan.md` · `final-report.md`
