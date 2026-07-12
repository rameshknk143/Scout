# Scout — Issues, Risks & Observations

Severity: 🔴 broken/blocking · 🟠 misleading/risky · 🟡 quality/polish. Confidence: High/Medium/Low.

## 🔴 1. Product Detail Drawer broken platform-wide (production, right now) — High
- **Symptom** [Observed]: every "Inspect Details/Inspect/Analyze" opens a drawer stuck at "LOADING REAL-TIME METRICS…" forever; console: HTTP 500 + masked Server Components error. Affects Dashboard, Watchlist, Alerts, Product Database.
- **Root cause** [Code, exact]: `api/main.py:418` `calc["weight_fee"]` and `:419,451` `calc["gst_on_amazon_fees"]` — keys that don't exist; calculator returns `weight_or_pickpack_fee` (`api/profit_calculator.py:102`) and no GST-on-fees key → `KeyError` → 500 for **all** ASINs (verified on 3, incl. unknown ASIN).
- **Irony**: introduced by `a4b3fc0` — the commit that fixed the previous review findings ("integrate real profit calculator").
- **Fix**: rename to `weight_or_pickpack_fee`; compute GST on fees as `amazon_fees_subtotal * 0.18` or drop the field; also make the client render an error state instead of an infinite spinner (`ProductDetailDrawer.tsx` catch path leaves `product=null` with no message).

## 🔴 2. Keyword Suggestion Harvester non-functional, fails silently — High
- **Symptom** [Observed on production]: seed "phone case" → ~40 s → zero results, UI resets to idle, no error anywhere.
- **Root cause** [Observed at network level]: `completion.amazon.com/search-services/query-action` returns an **empty HTML page** (dead/deprecated endpoint) — from any network, not just Vercel. All 27 fetch failures are swallowed (`catch {}` → `[]`).
- **Fix path**: reverse-engineer Amazon.in's current autocomplete XHR (the `completion.amazon.in/api/2017/suggestions` shape returned CloudFront 502 in a quick probe — needs proper session params; *not verifiable from here*). Minimum immediate fix: surface "0 results / upstream error" distinctly instead of silent idle.

## 🟠 3. Dashboard "Recommended Next Actions" & action-strip fabricate specifics — High
- [Observed on production]: card 1 currently shows **"Restock ASIN B08L7V6YF2"** — a hardcoded fallback ASIN that exists in no dataset (fires whenever no watchlist score <60: `trend-radar-client.tsx` `|| "B08L7V6YF2"`, `|| "B07W8P8M82"`). Card 2 ("Competitor price fell 12%") is fully static text. Action strip uses `|| 1` / `|| 2` so it never shows zero.
- **Risk**: presented as operational advice ("restock within 7 days") with a nonexistent product — could drive a real errand.
- **Fix**: render nothing (or an honest empty state) when the underlying condition has no matching row.

## 🟠 4. Dashboard KPI "Estimated Revenue/Sales/Margin" are heuristics dressed as metrics — Medium
- [Code]: units = score×5.2; revenue = units×buy×1.5; margin = fixed-formula estimate. Current display: "₹1,81,21,756 revenue / 2,742 units" from 8 validations — dominated by one ₹33,999 phone validation; "-5% avg margin" [Observed]. Tooltips say "calculated/projections" but the numbers read as business actuals; the "Dynamic" chip and "+1 this week" change-label are decorative.
- **Fix**: label as "modeled estimate", show the formula in tooltip, or compute from real snapshot prices.

## 🟠 5. Inventory page presents synthesized defaults as stock audit — High confidence it's synthetic; Medium impact
- [Observed]: my product (never given stock data) shows "100 units, 14 days lead, 20 days cover, Re-order 18 Jul 2026 (in 6d)". [Code]: constants, no stock field exists in `my_products`; "Update Levels" has no persistence endpoint. Alerts-drawer price regex fallback `|| 299` is the same pattern in miniature.

## 🟠 6. Listing Health mislabels opportunity score as "Listing Quality Score" — High
- [Observed 62.1%/62.6% == validation scores; Code `main.py:355` `score = row["score"]`]. The two numbers measure different things (sourcing opportunity vs listing copy quality); `/listing` computes an actual quality score that this page ignores.

## 🟡 7. `/analytics` orphaned + duplicate header — High
- No sidebar link (removed in redesign) — reachable only by URL; page renders two stacked "Analytics" H1s (page.tsx + client component both render headers) [Observed].

## 🟡 8. Dead chrome: Settings & Documentation are `href="#"`; top-bar search, date-range selector, and notification bell (with red dot) have no handlers [Code+Observed].

## 🟠 9. Security posture (fine for personal tool; do not scale as-is) — High confidence, Low current risk
- `scout_auth` cookie value **is the site password**; logout doesn't exist; 90-day life. Single shared `API_KEY` for all API access; no rate limiting on login (unlimited guesses) [Code].
- Secrets in plaintext `web/.env.local` (normal for local dev) — ensure it stays untracked (it is).
- Auth proxy leaks nothing (nonexistent = existent paths) [Observed] — good.
- HTTPS everywhere; API key never in client bundle (`server-only` guard) [Code] — good.

## 🟡 10. Verify fee table: referral ₹0.00 for Electronics Accessories @ ₹499 [Observed] — plausible (Amazon.in zero-referral brackets exist) but confirm `api/data/fee_tables.json` against the current Amazon.in rate card — Low confidence there's an error, cheap to check.

## 🟡 11. Cache staleness can mislead after writes — Medium
- Observed a ≤60s window where `/` showed pre-purge data while `/analytics` showed post-purge (Next data-cache `revalidate:60` + SWR). Purge scripts / external DB writes don't call `updateTag("watchlist")`, so cross-page inconsistency is expected briefly. Not a bug per se; document or lower revalidate for the dashboard.

## 🟡 12. Repo hygiene
- `WORKLOG.md` last entry 2026-07-09 — the entire redesign + 19 commits (incl. two production incidents found here) are unlogged, violating the project's own continuity rule (`CLAUDE.md`).
- Orphaned dead code in repo: `components/Onboarding.tsx`, `PremiumHero.tsx`, `app/login/login-form.tsx`, `components/3d/DashboardBackground.tsx` returns null; `PREMIUM_3D_*.md` docs describe a superseded design.
- Local shell cannot push (no git credential helper here) — pushes happen from the other agent's environment; deploy provenance therefore inferred from behavior, not refs (see final-report).

## Corrections made during this audit (for the record)
- Earlier statement "B0FAKE12345 still in production watchlist / purge partially executed" was **wrong** — it was a stale-cache read; a fresh load confirmed the purge completed (8 clean rows). Findings above reflect the corrected state.
