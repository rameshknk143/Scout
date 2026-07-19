# Workspace Foundation — Design Spec

**Date:** 2026-07-19
**Status:** Design discussed and agreed with Ram in conversation; this document is the written record, pending his final read-through
**Blueprint reference:** Stage 1 ("Organization/Workspace data model")

## Context

ScoutVeda is currently solo-operated (one real account: Ram). Two things are expected on a
known timeline:

- **~1–6 months out:** the product goes live to real strangers signing up as customers.
- **~6–12 months out:** Ram expects to add one or more teammates working alongside him.

Today, every piece of user-owned data (validations, saved products, Amazon seller
credentials, storefront sales/orders) is tagged directly with `user_id` — a strict
one-person-owns-this-row model. This was deliberately hardened earlier (see the
2026-07-19 data-scoping fix, commit `7b3fb60`, verified live with a real two-account
isolation test).

That per-person model has no way to represent "these two people share access to the same
business." Bolting that on later, once there's live production data and possibly a team
mid-onboarding, would be a much riskier migration than doing it now while there's one
account and nothing user-facing depends on it yet.

## Goals

- Introduce a "workspace" (business) as a first-class concept, separate from "user"
  (person), so a future teammate can be added without a rebuild.
- Every existing and future account gets its own workspace automatically — zero manual
  setup, zero new UI, zero visible change today.
- Tag existing user-owned data with its workspace alongside its existing user tag, so a
  future cutover to workspace-scoped queries is a small, contained change instead of
  repeating the full endpoint-by-endpoint migration done for Stage 0.
- Absolute data safety: this is an additive-only change. No row is ever deleted, moved,
  or overwritten. Verified with an explicit before/after row-count check across every
  table, shown to Ram directly.

## Non-goals (explicitly out of scope for this pass)

- **No query-layer cutover.** Every endpoint keeps reading/writing by `user_id` exactly
  as today. `workspace_id` is populated but not yet enforced or relied upon anywhere.
- **No team invite UI, no roles/permissions UI, no "switch workspace" UI.** Nothing
  user-visible changes.
- **No change to Amazon Seller account linking.** Explicitly confirmed with Ram — stays
  exactly as currently built (user-scoped), not touched by this work.
- **The nightly-collected `snapshots` table is out of scope entirely.** It is global,
  shared market data with no owner concept, and nothing in this design touches it.

## Data model

Two new tables:

```sql
CREATE TABLE IF NOT EXISTS workspaces (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_members (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'owner',   -- 'owner' | 'member' (member unused until teams ship)
    joined_at TEXT NOT NULL,
    UNIQUE (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);
```

Add a nullable `workspace_id` column (idempotent `ADD COLUMN IF NOT EXISTS`) to the five
existing user-owned tables: `validations`, `my_products`, `seller_credentials`,
`storefront_sales_metrics`, `storefront_orders`. Nullable so the column-add itself can
never fail or block on existing data.

## Rollout plan

1. **Auto-provisioning function:** `ensure_workspace_for_user(user_id)` — idempotent;
   creates a workspace named after the user (e.g. "Ramesh's Workspace") and a
   `workspace_members` row with role `owner`, but only if the user doesn't already have
   one. Both signup paths (email+password, after OTP verification, and Google sign-in)
   converge on the same `db.create_user()` call, so hooking the auto-provisioning in
   right there covers every future account from one single integration point. Called
   once by hand for Ram's existing account as a one-time backfill.
2. **Backfill existing rows:** for Ram's account, resolve his workspace_id and `UPDATE`
   every existing row across the five tables to set `workspace_id` where it's currently
   NULL and `user_id` matches. Purely additive — no `user_id` values change, no rows are
   touched other than filling in the new column.
3. **Safety check (run and shown to Ram, not just described):**
   - Before: `SELECT count(*) FROM <table>` for every affected table.
   - After: the same counts again.
   - Confirm every count is identical, and confirm the new `workspace_id` values are
     correctly populated (e.g. `count(*) WHERE workspace_id IS NOT NULL` matches the
     row count that was expected to be backfilled).

## Testing

- Compile-check all touched Python files.
- Re-run the same style of live two-account isolation test used for Stage 0: confirm a
  second real (throwaway) account gets its own separate workspace, sees none of Ram's
  data, and that Ram's data and workspace are unaffected — then delete the throwaway
  account.
- Confirm the row-count safety check (above) passes with zero discrepancies before
  calling this done.

## Future work (not now — flagged so it isn't lost)

- When teammates are actually needed: switch the relevant endpoints from
  `user_id`-scoped queries to `workspace_id`-scoped queries (resolved from
  `workspace_members` for the logged-in user), and build the invite/roles UI. Because the
  data is already tagged, this becomes a scoped, well-understood change instead of a
  ground-up migration.
- Multi-workspace-per-user support (a person owning/joining more than one business) is
  already representable in this schema (`workspace_members` is many-to-many) — no further
  schema change needed when that's wanted.
