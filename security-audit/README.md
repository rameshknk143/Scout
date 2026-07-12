# Scout — Security Audit

**Target (in scope):** https://scout-omega-seven.vercel.app/ (exact host) + its backend the site calls, https://scout-api-3yvy.onrender.com, and the local source in this workspace.
**Date:** 2026-07-12 (UTC)
**Auditor:** Claude Code (passive assessment + local source review)

## Authorization status
- **Ownership:** established across this working session — the target is the requester's own project: repo `rameshknk143/Scout`, their Vercel (web) and Render (API) deployments, credentials in `web/.env.local`, and all prior testing was owner-directed.
- **Active testing:** **NOT performed.** Per the engagement's own safety gate, active tests (injection/fuzzing payloads, auth-bypass attempts, CORS/CSRF exploit probes, brute force, state-changing requests) are withheld pending **explicit written approval** ("yes, run active tests"). This report is Phase 1–2 only.
- What *was* done: passive HTTP header/TLS/redirect inspection, non-invasive CORS header observation (single GET/OPTIONS with an `Origin`), source-map and well-known-path existence checks (a handful, low rate), and full local source review. No forms submitted, no data changed, no secrets exfiltrated. Two auth'd read sessions earlier this session already covered functional behavior.

## Methodology
1. **Source-first inventory** — read the Next.js app (`web/`), FastAPI backend (`api/`), `proxy.ts` auth gate, `render.yaml`, lockfiles, and env handling.
2. **Passive live checks** — `curl -I`/`-D` for headers, TLS, redirects, cookies; one cross-origin `Origin` GET + one OPTIONS to observe CORS; `.map` and well-known sensitive paths at low rate.
3. **Cross-reference** — every finding cites a header observation, a source `file:line`, or a live status code.

## Coverage & limitations
- **Verifiable:** transport/headers, cookie flags, CORS posture, source-map/file exposure, client bundle handling, dependency versions, auth/session design (source is present).
- **Server-side implementation and database security were partially verifiable from source** (the code is in this workspace) **but the running infrastructure was not** — Supabase RLS/network rules, Render/Vercel platform config, WAF/rate-limit rules at the edge, and actual secret values in the cloud were **not** inspected (no dashboard access from here).
- Active exploitation of any suspected issue was intentionally **not** attempted (gate). Findings are labeled Confirmed / High / Medium / Low / Not verifiable accordingly.

## Files
`attack-surface.md` · `security-headers.md` · `data-privacy.md` · `dependency-review.md` · `findings.md` · `evidence.md` · `remediation-plan.md` · `final-report.md`

## Handling
Keep this folder **untracked** (it references infra details). No secrets, tokens, passwords, or personal data are reproduced in any file here — all redacted.
