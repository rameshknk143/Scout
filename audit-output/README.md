# Scout Deployed-Site Audit — audit-output/

Evidence-based audit of **https://scout-omega-seven.vercel.app** (and its backend **https://scout-api-3yvy.onrender.com**), performed 2026-07-11/12 with:
- full local source access (this repo, git HEAD `a4b3fc0`),
- owner-authorized login and API key (this is the owner's own personal, password-gated tool — nothing was bypassed),
- a real Chrome session for UI behavior, `curl` for protocol behavior, and a rate-limited Node extractor for data.

**Start here → `final-report.md`** (executive summary + priorities), then `issues.md` (12 findings with exact file:line root causes).

## Files
| File | What |
|---|---|
| `final-report.md` | Executive summary, deployment provenance, coverage, recommendations, limitations |
| `issues.md` | 🔴🟠🟡 findings with evidence, confidence, and fixes (incl. 2 features broken on production right now) |
| `site-map.md` | Full route inventory: public + authenticated, per-route status |
| `functional-analysis.md` | All 15 features: trigger → inputs → processing → network → output → edge cases |
| `data-flow.md` | Architecture, 8 data flows, storage inventory, third parties, not-verifiables |
| `network-endpoints.csv` | All 24 endpoints: method, params, purpose, auth, evidence |
| `data-inventory.md` | Every dataset, fields, update cadence, extraction status, sensitivity notes |
| `scraped-data.csv` | 3,680 product-snapshot rows (the full Product Database) |
| `scraped-data.jsonl` | 4,146 records incl. auxiliary datasets, one JSON/line with `_source_endpoint` + `_retrieved_at` provenance |
| `scrape-log.md` | Timestamps, request counts, rate limits, skips, and a writes-disclosure |
| `tools/` | `extract.mjs` (reproducible extractor), `request-log.json`, `extract-summary.json` |

## Reproduce
```bash
cd audit-output/tools && node extract.mjs
# reads API key at runtime from ../../web/.env.local; never writes secrets to outputs
```

## Handling
- This folder is **untracked** — keep it out of git (contains the owner's watchlist/sourcing rows; pushing the repo would also auto-deploy).
- "Public data" here means "served by the deployed app to its authorized user" — the only truly world-readable surfaces are `/login` and API `/health`.

> ⚠️ **The "untracked" note above is out of date.** As of 2026-07-28 all 14 files in
> this folder, including `scraped-data.csv` and `scraped-data.jsonl`, are tracked in
> git. The repo appears to be private, and the files were re-scanned for credentials
> with no matches — but the statement above should not be relied on. See
> `2026-07-28-stage-audit-and-remediation.md` §11 for the two ways to resolve it.

## Related audits
| File | What |
|---|---|
| `2026-07-28-stage-audit-and-remediation.md` | Source-side audit of blueprint stages 0–6: 11 findings, remediation, and the RLS lockdown applied to production |
