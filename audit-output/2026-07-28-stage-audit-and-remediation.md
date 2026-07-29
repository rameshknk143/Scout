# ScoutVeda — Full Program Audit & Remediation

**Date:** 2026-07-28
**Scope:** Blueprint stages 0–6, audited against live code, live Supabase schema, git history, and CI config
**Repo at start:** `main` @ `0d6e9f7`, 17 modified + 2 untracked files
**Repo at end:** `main` @ `1ac8873` (pushed), Stage 5/6 bundle still uncommitted by design

> This is a *different* audit from the 2026-07-11/12 deployed-site audit in this
> folder (`final-report.md` / `issues.md`). That one probed the running site from
> outside. This one reads the source, the database, and the git history from inside.

---

## Method, and one honest caveat

The audit ran in two passes. **The first pass was incomplete.** It over-focused on
uncommitted code and under-checked what was actually deployed. It was challenged,
and the second pass is what found the production bug in §1. That is recorded here
because it is the reason the finding surfaced at all — not as a footnote.

Sources cross-checked:

| Source | What was checked |
|---|---|
| `api/db.py` | All five `*_MIGRATION` constants vs. the live Supabase schema |
| Supabase | `pg_tables`, `pg_roles`, row counts, security + performance advisors, empirical `set role` probes |
| `git log` / `git ls-tree` | What is actually deployed vs. what only exists in the working tree |
| `.github/workflows/` | Both cron workflows, schedules, and secret usage |
| `web/` build | `npm run build` including TypeScript |

---

## Verdict summary

| # | Finding | Severity | Was it live? | Status |
|---|---|---|---|---|
| 1 | Tautological inventory velocity | High | **Yes — 8 days** | ✅ Fixed & deployed |
| 2 | RLS disabled on all 13 tables | High | **Yes** | ✅ Fixed in production DB |
| 3 | Fabricated PPC ad metrics | High | No | ✅ Fixed (undeployed) |
| 4 | Fabricated team / audit / billing data | High | No | ✅ Fixed (undeployed) |
| 5 | Multi-tenant email leak in settings | High | No | ✅ Fixed (undeployed) |
| 6 | Spoofable audit-log endpoint | High | No | ✅ Fixed (undeployed) |
| 7 | Analytics defaulted to the fabricated tab | Medium | No | ✅ Fixed (undeployed) |
| 8 | Silent `catch {}` masking failures (×3) | Medium | No | ✅ Fixed (undeployed) |
| 9 | Duplicate PWA manifest | Low | No | ✅ Fixed (undeployed) |
| 10 | `WORKLOG.md` three commits behind | Low | n/a | ✅ Backfilled |
| 11 | `audit-output/` committed against its own policy | Low | n/a | ⚠️ **Open — needs a decision** |

**A key structural result:** of every fabrication found, **exactly one had ever
reached production.** Verified by reading HEAD directly — `git show HEAD:<file>`
for the settings, analytics, and API files returned no match for the fabricated
names, the `0.15`/`0.35` ad-spend ratios, or the `audit-logs` endpoint. The rest
were caught in the working tree before they ever shipped.

---

## 1. Tautological inventory velocity — the live bug

**Severity: high. Live for 8 days** (commit `0d6e9f7`, 2026-07-20 → 2026-07-28).

`web/app/dashboard/inventory/inventory-client.tsx` computed:

```
velocity      = clamp(ceil(stock / 30), 1, 25)
daysRemaining = stock / velocity
```

Substitute and the stock term cancels. `stock / (stock/30)` is just `30`, modified
only by the ceiling and the clamp. For any SKU holding roughly 30–750 units — most
real inventory — **"Stock Cover" read 23–30 days regardless of actual stock.**

| Actual stock | Reported cover |
|---:|---:|
| 60 units | 30 days |
| 300 units | 30 days |
| 750 units | 30 days |

The consequence was worse than a wrong number. The red pulsing **"⚠️ Order
Immediately"** badge was driven by `daysRemaining <= lead_time_days`, so with
`daysRemaining` pinned near 30 it effectively fired on `lead_time_days >= ~30` —
**a property of the supplier, not of the stock.** A slow supplier triggered the
alarm on a full shelf; a fast supplier silenced it on an empty one.

No sales data was consulted anywhere in the calculation, despite the code comment
reading "Estimated sales velocity based on catalog inventory and stock velocity."

### Why the fix is an empty state, not a better formula

Before writing a replacement, real velocity was checked for computability. It is
not available:

- `storefront_orders` — **0 rows**
- `storefront_sales_metrics` — 24 rows, but **aggregate-only**: `order_count`,
  `unit_count`, `total_sales_amount` per interval
- **Neither table carries an `asin` column**

There is no per-SKU run rate in the database to divide by. Substituting a
different estimate would have repeated the same mistake in a new costume.

### What changed

- `getVelocity()` deleted outright.
- **Stock Cover** and **Re-order Forecast** now render a neutral
  `Needs sales data` chip with a tooltip explaining the missing dependency.
- The stock-level column no longer turns red based on the bogus threshold.
- MiniStat **"Reorder Warnings"** (a fabricated count) → **"Total Units in Stock"**
  (a real sum).
- An on-page panel states plainly what is missing and what would populate it.

**Shipped as `1ac8873`** — the only commit created by this audit.

---

## 2. RLS disabled on every table — confirmed exploitable

**Severity: high. Was live.** Now fixed in the production database.

Row Level Security was off on all 13 tables in `public`. This was proven, not
assumed:

```sql
set local role anon;
select count(*) from public.seller_credentials;   -- returned 1
```

`anon` could also read `users`, `email_otps`, `my_products`, and
`storefront_sales_metrics`. Anyone holding the project's publishable anon key —
which is by design not a secret — could read them over PostgREST. The Amazon
refresh token is Fernet-encrypted at rest, so that column would have yielded
ciphertext; the email addresses and OTP records would not have.

### Why locking it down was safe

Three facts, each verified before touching anything:

1. `pg_roles` — `postgres` has `rolbypassrls = true`; `anon` and `authenticated`
   do not.
2. `pg_tables` — `postgres` owns all 13 tables.
3. `web/` contains **zero** supabase-js references.

Nothing in the product reaches these tables over PostgREST. So enabling RLS with
**no policies at all** is a deny-all for the public API and a complete no-op for
the backend.

### Migration applied

Name: `enable_rls_lockdown_public_schema`

```sql
alter table public.audit_logs               enable row level security;
alter table public.email_otps               enable row level security;
alter table public.my_products              enable row level security;
alter table public.org_members              enable row level security;
alter table public.seller_credentials       enable row level security;
alter table public.snapshots                enable row level security;
alter table public.storefront_orders        enable row level security;
alter table public.storefront_sales_metrics enable row level security;
alter table public.sync_jobs                enable row level security;
alter table public.users                    enable row level security;
alter table public.validations              enable row level security;
alter table public.workspace_members        enable row level security;
alter table public.workspaces               enable row level security;

-- Second layer: strip privileges outright, so a future `create policy` typo
-- cannot silently re-open a table.
revoke all on all tables in schema public from anon, authenticated;

-- Make it stick for tables created later by db.init_db migrations.
alter default privileges in schema public revoke all on tables from anon, authenticated;
```

### Verification after applying

Every table probed as `anon`, with `postgres` counts taken in the same transaction:

| Table | anon | postgres rows |
|---|---|---:|
| audit_logs | BLOCKED | 0 |
| email_otps | BLOCKED | 3 |
| my_products | BLOCKED | 1 |
| org_members | BLOCKED | 0 |
| seller_credentials | BLOCKED | 1 |
| snapshots | BLOCKED | 66,228 |
| storefront_orders | BLOCKED | 0 |
| storefront_sales_metrics | BLOCKED | 24 |
| sync_jobs | BLOCKED | 11 |
| users | BLOCKED | 1 |
| validations | BLOCKED | 8 |
| workspace_members | BLOCKED | 1 |
| workspaces | BLOCKED | 1 |

13/13 blocked for `anon`; `postgres` reads everything unchanged.

The Supabase security advisor now reports **only** `rls_enabled_no_policy` at
**INFO** level on those 13 tables. That is the intended and correct end state for
this architecture — the ERROR-level `rls_disabled_in_public` findings are gone,
and "RLS on, no policies" is precisely the deny-all that was wanted. It is not a
residual problem.

---

## 3. Fabricated PPC advertising metrics

**Never deployed.** `api/ppc_analytics.py` (untracked) invented its headline numbers:

```python
ad_spend   = round(total_sales * 0.15, 2)
ad_revenue = round(total_sales * 0.35, 2)
```

…and then labelled the result `"connected": True` with the status message
*"Computed from connected Storefront Sales Metrics."* Every downstream figure —
ACoS, TACoS, ROAS, organic revenue — was derived from those two constants, so the
whole panel was a restatement of `total_sales` with three decorative ratios.

Storefront data cannot separate ad-attributed revenue from organic revenue. That
split requires the Amazon Advertising API, which is not connected.

**Fixed:** returns `"connected": False`, `"ad_metrics_available": False`, and
`None` for `total_ad_spend`, `total_ad_revenue`, `organic_revenue`, `acos_pct`,
`tacos_pct`, and `roas`. The genuinely measured fields — `total_sales_amount`,
`total_units`, `order_count` — pass through as real values. Two distinct status
messages depending on whether sales metrics exist at all.

---

## 4. Fabricated team, audit, and billing data

**Never deployed.** `web/app/dashboard/settings/settings-client.tsx`:

| What it showed | Reality |
|---|---|
| Teammates "Ananya Sharma", "Rajesh Kumar" | Hardcoded seed arrays |
| 4 audit rows, all IP `192.168.1.2` | Hardcoded |
| "3 / 5 Seats" (twice), "1 / 3 Accounts", "84 / Unlimited", "4 Logs Recorded" | Hardcoded |

Both data loaders ended in an empty `catch (err) {}`, which meant the fake seed
data **persisted on screen as though it were real** whenever the API call failed.
That is the failure mode that turns a placeholder into a lie.

**Fixed:** seeds removed; real error states; `ACCOUNT_LIMIT` / `SEAT_LIMIT`
constants with counts computed from actual state and bar widths derived from them.

---

## 5. Multi-tenant email leak

**Never deployed.** The same file synthesized an "owner" row hardcoded to
`rameshknk143@gmail.com`. On a multi-tenant product this would have rendered the
owner's personal email address into **every other tenant's** settings page.

**Fixed:** synthesized row removed entirely.

Also in this file, the invite flow claimed *"Invitation saved & dispatched to …"*
when no mail-sending code exists anywhere in the codebase — and worse, its `catch`
block reported **success on failure**. Now: honest copy stating no email is sent,
the button reads "Add Member" rather than "Send Invite", and failures report as
failures.

---

## 6. Spoofable audit log

**Never deployed.** Flagged by an automated security review mid-session and
confirmed valid against the real code.

`POST /saas/audit-logs` accepted `actor_email`, `action`, `target`, **and
`ip_address` straight from the request body** — while the UI presents that table
as an *"Immutable record of sensitive workspace actions."* Any authenticated
tenant could have written arbitrary attributed history.

**Fixed:**

- The endpoint is **removed entirely.** Verified free to remove: `web/lib/api.ts`
  only ever issued a `GET`; no `POST` wrapper existed.
- The one real writer, `add_org_member`, now derives the actor server-side via
  `db.get_user_by_id(user_id)` and validates `role` against a server-side
  `ORG_MEMBER_ROLES` set.
- New `_client_ip(request)` helper reads the **rightmost** `X-Forwarded-For`
  entry. This direction matters: Render *appends* the true peer address, so
  anything a client forges lands to the **left** of it. The leftmost entry — the
  one most code naively takes — is attacker-controlled.
- `db.log_audit_event`'s `ip_address` default changed from the fabricated
  `"127.0.0.1"` to `None`. An unknown IP is now NULL, not a plausible-looking
  placeholder.

---

## 7–9. Remaining fixes

- **Analytics landing tab** defaulted to `"ppc"`, so the fabricated panel was the
  first thing a user saw on that page. Now defaults to `"overview"`.
- **Third silent catch** (`analytics-client.tsx`) left a permanent *"Loading
  Amazon Advertising API status…"* on failure. Now a real error state with a
  Retry action. The banner is three-way: loading / error / normal.
- **Duplicate PWA manifest** — `web/app/manifest/route.ts` and
  `web/public/manifest.json` were byte-identical. Kept the static file (CDN-served,
  no serverless invocation), deleted the route, and corrected
  `layout.tsx`'s `manifest:` reference to `/manifest.json`.

### Ruled out as false positives

- `web/app/dashboard/trend-radar/trend-radar-client.tsx:206` — `sell * 0.15 + 100`
  is a margin estimate, but it carries an explicit comment marking it a **labelled
  research estimate, "never as booked profit."** Presenting a labelled estimate as
  an estimate is categorically different from presenting an invention as a
  measurement. Left as-is.
- Three remaining empty `catch {}` blocks (`trend-radar-client.tsx:248`,
  `SetupWizard.tsx:51`, `Sidebar.tsx:46`) are `localStorage` `JSON.parse` guards.
  Swallowing those is correct.

---

## 11. `audit-output/` is committed against its own stated policy ⚠️ OPEN

**New finding, surfaced while filing this report.**

`audit-output/README.md` line 32 states:

> This folder is **untracked** — keep it out of git (contains the owner's
> watchlist/sourcing rows; pushing the repo would also auto-deploy).

That is **false as of today.** All 14 files are tracked, including:

- `scraped-data.csv` — 1,110,743 bytes (3,680 product-snapshot rows)
- `scraped-data.jsonl` — 2,155,444 bytes (4,146 records)

**Mitigating:** `https://github.com/rameshknk143/Scout` returns HTTP 404 to an
unauthenticated request, which is GitHub's behavior for private repositories. So
this is very likely contained — worth confirming in repo settings.

**Also checked:** the tracked audit files were scanned for credential patterns
(`sk-`, `rnd_`, JWT prefixes, Amazon `Atzr|` tokens, `TOKEN_ENCRYPTION_KEY`,
`service_role`, bearer tokens). **No matches** — the extractor's claim that it
never writes secrets to outputs holds up.

**Why it still matters:** if the repo is ever flipped to public or a collaborator
is added, the sourcing data goes with it — and the README would actively mislead
whoever makes that call.

**Decision needed — two clean options:**

1. **Untrack it:** `git rm -r --cached audit-output/` + add to `.gitignore`. Note
   this removes it from future commits but **not from history** — the blobs remain
   reachable in prior commits.
2. **Accept it:** correct the README so it states the folder *is* tracked and the
   repo must stay private.

Not actioned unilaterally: which one is right is a judgment call about how the
repo will be used, and option 1's history caveat deserves an explicit choice.

---

## Verified clean

- **All five migrations are applied live** — `MULTITENANT`, `GOOGLE_AUTH`,
  `WORKSPACE`, `SYNC_JOBS`, `STAGE5_SAAS`. No repeat of the earlier `auth_provider`
  incident where a migration was written but never run.
- **Both GitHub Actions crons** are correctly staggered (20:45 / 21:15 UTC) and
  carry no Amazon secrets.
- **All `/saas` and `/analytics` endpoints** are gated by `require_key` +
  `require_user`.
- **The keyword multi-source fallback** shipped in `0d6e9f7` is genuinely good
  code — a real Amazon-US → Amazon-IN → Google chain that returns an honest empty
  array on total failure. Worth noting that the same commit contained both the
  best and the worst code found in this audit.
- **No new dependencies** introduced anywhere.
- **`npm run build`** — clean, TypeScript included, 18/18 routes.
- **Python syntax checks** pass on `main.py`, `db.py`, `ppc_analytics.py`.

---

## Still uncommitted (by design)

The working tree retains ~1,500 insertions across 16 files: Stage 5 (audit logs +
team management, tables already live), Stage 6 (PPC), a 3 → 16 marketplace
expansion, plus fixes 3–9 above.

These were deliberately **not** shipped with the inventory fix. Fixes 3–9 all
correct code that was never deployed, so holding them costs nothing in production
risk, while pushing them would have shipped the entire unreviewed Stage 5/6 bundle
in the same commit.

**One item worth committing on its own merit:** an `@app.on_event("startup")` hook
in `main.py` calling `db.init_db()`. Every migration is already idempotent, so this
would structurally end the "migration written but never applied in production" bug
class — which has now bitten this project twice.

---

## What was actually changed today

| Target | Change | State |
|---|---|---|
| Supabase production DB | `enable_rls_lockdown_public_schema` | **Applied & verified** |
| `main` branch | `1ac8873` — inventory fix | **Pushed** |
| `web/app/dashboard/inventory/inventory-client.tsx` | Velocity estimator removed | **Deployed** |
| 16 other files | Fixes 3–9 | Uncommitted |
| `WORKLOG.md` | 2026-07-20 backfill + 2026-07-28 entry | Written |
| `audit-output/` | This report | Written |

### Deploy verification — what could and could not be confirmed

**Confirmed:** `1ac8873` is on `origin/main`; the Vercel project is git-connected
to `main`; `https://www.scoutveda.com` serves HTTP 200 with a healthy landing page
and no build-failure notice.

**Not confirmed:** that the new Vercel build finished and was promoted. Neither the
`vercel` nor `gh` CLI is installed on this machine, and the landing page is served
from edge cache (`x-vercel-cache: HIT`) with no build ID exposed, so there was no
way to compare deployments from here.

**To close that gap:** open the Vercel dashboard for project `scout`, or simply
load the Inventory page — Stock Cover and Re-order Forecast should read
**"Needs sales data"**, and the fourth tile should read **"Total Units in Stock"**.

---

## The principle this audit was run against

From `WORKLOG.md`, 2026-07-17:

> **Never fabricate data — always show an honest empty/error state.**

Every finding above is an instance of that principle being violated, and every fix
is an application of it. The recurring pattern is worth naming: **none of this code
looked wrong on review.** `ceil(stock/30)` is a reasonable line. Dividing stock by
velocity is a reasonable line. `total_sales * 0.15` is a reasonable line. The
defect only becomes visible when you ask what the output actually depends on — and
a circular metric passes every local inspection precisely because each individual
operation is plausible.
