# Workspace Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "workspace" (business) concept alongside "user" (person) in ScoutVeda's database, with every account auto-provisioned into its own workspace, so a future teammate or second business can be supported without a risky data migration later.

**Architecture:** Two new Postgres tables (`workspaces`, `workspace_members`) plus a nullable `workspace_id` column added to the five existing user-owned tables. A single idempotent function, `ensure_workspace_for_user()`, is called from inside `db.create_user()` so every signup path (email+password, Google) provisions a workspace automatically with zero endpoint changes. Existing queries keep working unchanged — this phase only adds the new columns/tables and backfills Ram's existing data; nothing yet reads or filters by `workspace_id`.

**Tech Stack:** Python 3.13, FastAPI, psycopg2 (raw SQL, no ORM), Postgres via Supabase, Render (backend host, auto-deploys on push to `main`).

## Global Constraints

- **Additive only.** No `DROP`, `DELETE`, or destructive `ALTER` anywhere in this plan. Every migration statement uses `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`.
- **No query-layer changes.** Every existing endpoint keeps reading/writing by `user_id` exactly as today. `workspace_id` is populated but not enforced or relied upon by any query in this phase.
- **No UI changes.** Nothing user-visible changes in this phase.
- **Amazon Seller account linking is untouched** — explicitly out of scope (confirmed with Ram).
- **The `snapshots` table (nightly-collected market data) is untouched** — it's global, shared data with no owner concept and is not part of this work at all.
- **Idempotent migrations only** — every SQL statement must be safe to run more than once without error or duplicate side effects (matches the existing `MULTITENANT_MIGRATION` / `GOOGLE_AUTH_MIGRATION` pattern already in `api/db.py`).
- **Supabase project ID for all live verification steps:** `uijfkvvoncfmaxlvnfhq`.
- **Live backend URL for HTTP checks:** `https://scout-api-3yvy.onrender.com`.

---

## Task 1: Workspace schema + provisioning/backfill functions

**Files:**
- Modify: `api/db.py:216-219` (insert new migration constant immediately after `GOOGLE_AUTH_MIGRATION`)
- Modify: `api/db.py:243-248` (`init_db()` — add one line)
- Modify: `api/db.py` (insert new functions immediately after `init_db()`, before the `# --- Accounts` section at line 251)

**Interfaces:**
- Produces: `db.ensure_workspace_for_user(user_id: int, full_name: str | None = None) -> int` (returns workspace_id)
- Produces: `db.get_workspace_id_for_user(user_id: int) -> int | None`
- Produces: `db.backfill_workspace_for_user(user_id: int) -> dict[str, int]` (table name → rows updated)
- Produces: `db.count_workspace_rows() -> dict[str, dict[str, int]]` (table name → `{"total": N, "tagged": N}`)

- [ ] **Step 1: Add the `WORKSPACE_MIGRATION` constant**

In `api/db.py`, immediately after the existing `GOOGLE_AUTH_MIGRATION` block (ends at line 219 with `"""`), insert:

```python


# Introduces the workspace/business concept alongside individual user accounts.
# Every account gets exactly one workspace, auto-provisioned by
# ensure_workspace_for_user() below -- see docs/superpowers/specs/
# 2026-07-19-workspace-foundation-design.md for the full rationale. Purely
# additive: new tables, and a nullable column added to existing tables, so
# this can never fail against existing data or lose anything.
WORKSPACE_MIGRATION = """
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
    role TEXT NOT NULL DEFAULT 'owner',
    joined_at TEXT NOT NULL,
    UNIQUE (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);

ALTER TABLE validations              ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL;
ALTER TABLE my_products              ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL;
ALTER TABLE seller_credentials       ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL;
ALTER TABLE storefront_sales_metrics ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL;
ALTER TABLE storefront_orders        ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL;
"""
```

- [ ] **Step 2: Wire it into `init_db()`**

In `api/db.py`, find:

```python
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(MULTITENANT_MIGRATION)
            cur.execute(GOOGLE_AUTH_MIGRATION)
```

Change to:

```python
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(MULTITENANT_MIGRATION)
            cur.execute(GOOGLE_AUTH_MIGRATION)
            cur.execute(WORKSPACE_MIGRATION)
```

- [ ] **Step 3: Add the provisioning, backfill, and count-check functions**

Immediately after `init_db()` (before the `# --- Accounts` comment at line 251), insert:

```python

# --- Workspaces -----------------------------------------------------------
# A "workspace" represents one business. Every user belongs to exactly one
# today, auto-provisioned below; workspace_members is many-to-many so a
# person could join/own a second workspace later with no schema change.
# Nothing else in the app queries by workspace_id yet.

def ensure_workspace_for_user(user_id, full_name=None):
    """Idempotent: if `user_id` already belongs to a workspace, returns its
    id unchanged and creates nothing. Otherwise creates a new workspace
    owned by them and returns its id. Called automatically by create_user()
    for every new signup (email+password and Google both funnel through it)."""
    from datetime import datetime, timezone
    existing = get_workspace_id_for_user(user_id)
    if existing is not None:
        return existing

    name = f"{full_name}'s Workspace" if full_name else "My Workspace"
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO workspaces (name, owner_user_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                (name, user_id, now),
            )
            workspace_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO workspace_members (workspace_id, user_id, role, joined_at) VALUES (%s, %s, %s, %s)",
                (workspace_id, user_id, "owner", now),
            )
    return workspace_id


def get_workspace_id_for_user(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT workspace_id FROM workspace_members WHERE user_id = %s LIMIT 1", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None


def backfill_workspace_for_user(user_id):
    """One-time: tag this user's existing rows (created before workspaces
    existed) with their workspace_id. Purely additive -- only fills rows
    where workspace_id IS NULL; never touches user_id or deletes anything.
    Idempotent: safe to run more than once (a table with no untagged rows
    left is simply a no-op). Returns rows-updated count per table."""
    workspace_id = ensure_workspace_for_user(user_id)
    counts = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            for table in ("validations", "my_products", "seller_credentials", "storefront_sales_metrics", "storefront_orders"):
                cur.execute(
                    f"UPDATE {table} SET workspace_id = %s WHERE user_id = %s AND workspace_id IS NULL",
                    (workspace_id, user_id),
                )
                counts[table] = cur.rowcount
    return counts


def count_workspace_rows():
    """Row counts per user-owned table: total rows vs. rows already tagged
    with a workspace_id. Used as the before/after safety check when
    backfilling -- `total` must be identical before and after; only
    `tagged` should change."""
    counts = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            for table in ("validations", "my_products", "seller_credentials", "storefront_sales_metrics", "storefront_orders"):
                cur.execute(f"SELECT count(*), count(workspace_id) FROM {table}")
                total, tagged = cur.fetchone()
                counts[table] = {"total": total, "tagged": tagged}
    return counts
```

- [ ] **Step 4: Compile check**

Run: `cd api && python -m py_compile db.py`
Expected: no output, exit code 0.

- [ ] **Step 5: Commit**

```bash
git add api/db.py
git commit -m "feat(db): workspace schema + provisioning/backfill functions

Adds workspaces + workspace_members tables, a nullable workspace_id
column on the 5 user-owned tables, and ensure_workspace_for_user() /
get_workspace_id_for_user() / backfill_workspace_for_user() /
count_workspace_rows(). Purely additive -- not yet wired into
create_user() or deployed. See docs/superpowers/specs/
2026-07-19-workspace-foundation-design.md."
```

---

## Task 2: Auto-provision a workspace on every signup

**Files:**
- Modify: `api/db.py:268-277` (`create_user`)

**Interfaces:**
- Consumes: `ensure_workspace_for_user(user_id: int, full_name: str | None = None) -> int` (from Task 1, same module)
- Produces: `db.create_user(...)` — same signature and return shape as before; behavior gains a side effect (workspace auto-created for the new user).

- [ ] **Step 1: Modify `create_user` to provision a workspace after inserting the user**

Find:

```python
def create_user(email, password_hash, full_name, email_verified=True, auth_provider="password"):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO users (email, password_hash, full_name, email_verified, created_at, auth_provider)
                   VALUES (lower(%s), %s, %s, %s, %s, %s) RETURNING id, email, full_name, email_verified""",
                (email, password_hash, full_name, email_verified, datetime.now(timezone.utc).isoformat(), auth_provider),
            )
            return dict(cur.fetchone())
```

Replace with:

```python
def create_user(email, password_hash, full_name, email_verified=True, auth_provider="password"):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO users (email, password_hash, full_name, email_verified, created_at, auth_provider)
                   VALUES (lower(%s), %s, %s, %s, %s, %s) RETURNING id, email, full_name, email_verified""",
                (email, password_hash, full_name, email_verified, datetime.now(timezone.utc).isoformat(), auth_provider),
            )
            user = dict(cur.fetchone())
    # Outside the `with` block on purpose: releases this connection back to
    # the pool before ensure_workspace_for_user() draws its own, instead of
    # holding two pooled connections open at once for one signup.
    ensure_workspace_for_user(user["id"], full_name)
    return user
```

- [ ] **Step 2: Compile check**

Run: `cd api && python -m py_compile db.py`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add api/db.py
git commit -m "feat(db): auto-provision a workspace on every new signup

create_user() now calls ensure_workspace_for_user() right after the
INSERT. Both signup paths (email+password after OTP verification, and
Google sign-in) funnel through create_user(), so this is the single
integration point for every future account -- no endpoint changes
needed."
```

---

## Task 3: Deploy and verify the schema is live

**Files:** none (deploy + verification only)

**Interfaces:**
- Consumes: nothing new — this task deploys Tasks 1 and 2's commits.

- [ ] **Step 1: Push to deploy**

```bash
git push origin main
```

Render auto-deploys from `main` and runs `init_db()` on startup, which applies `WORKSPACE_MIGRATION`.

- [ ] **Step 2: Poll until the new deploy is live**

Run (repeat every ~15s until it returns `200`, up to ~5 minutes):

```bash
curl -s -o /dev/null -w "%{http_code}\n" --max-time 30 https://scout-api-3yvy.onrender.com/health
```

Expected: `200`.

- [ ] **Step 3: Verify the new tables and columns exist**

Use the Supabase MCP tool (`execute_sql`, `project_id: uijfkvvoncfmaxlvnfhq`):

```sql
SELECT
  (SELECT to_regclass('public.workspaces') IS NOT NULL) AS workspaces_table_exists,
  (SELECT to_regclass('public.workspace_members') IS NOT NULL) AS workspace_members_table_exists,
  (SELECT count(*) FROM information_schema.columns
     WHERE table_name IN ('validations','my_products','seller_credentials','storefront_sales_metrics','storefront_orders')
       AND column_name = 'workspace_id') AS tables_with_workspace_id_column;
```

Expected: `workspaces_table_exists = true`, `workspace_members_table_exists = true`, `tables_with_workspace_id_column = 5`.

- [ ] **Step 4: No commit** (deploy-only task, nothing new to commit).

---

## Task 4: Backfill Ram's account, with the promised before/after safety check

**Files:** none (live data operation + verification only)

**Interfaces:**
- Consumes: the deployed `backfill_workspace_for_user()` and `count_workspace_rows()` logic from Task 1 (verified here by running their exact SQL directly, since these functions have no HTTP endpoint of their own).

- [ ] **Step 1: Count every row BEFORE touching anything**

Use the Supabase MCP tool (`execute_sql`, `project_id: uijfkvvoncfmaxlvnfhq`):

```sql
SELECT 'validations' AS tbl, count(*) AS total, count(workspace_id) AS tagged FROM validations
UNION ALL SELECT 'my_products', count(*), count(workspace_id) FROM my_products
UNION ALL SELECT 'seller_credentials', count(*), count(workspace_id) FROM seller_credentials
UNION ALL SELECT 'storefront_sales_metrics', count(*), count(workspace_id) FROM storefront_sales_metrics
UNION ALL SELECT 'storefront_orders', count(*), count(workspace_id) FROM storefront_orders;
```

Record every `total` value exactly as returned — this is the baseline every later count must match.

- [ ] **Step 2: Resolve Ram's workspace (auto-provisions one if Task 3's deploy hasn't triggered it yet — Ram's account predates this feature, so it needs the same one-time provisioning as a new signup would get automatically)**

```sql
INSERT INTO workspaces (name, owner_user_id, created_at)
SELECT 'Ram''s Workspace', 1, to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"')
WHERE NOT EXISTS (SELECT 1 FROM workspace_members WHERE user_id = 1)
RETURNING id;
```

If this returns a row, note the returned `id` as `<WORKSPACE_ID>`. If it returns zero rows (a workspace already exists for user 1), fetch it instead:

```sql
SELECT workspace_id FROM workspace_members WHERE user_id = 1;
```

Then (only if the first INSERT above actually created a new workspace) also insert the membership row:

```sql
INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
VALUES (<WORKSPACE_ID>, 1, 'owner', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'))
ON CONFLICT (workspace_id, user_id) DO NOTHING;
```

- [ ] **Step 3: Backfill — tag Ram's existing rows with his workspace_id**

Using the `<WORKSPACE_ID>` resolved in Step 2:

```sql
UPDATE validations SET workspace_id = <WORKSPACE_ID> WHERE user_id = 1 AND workspace_id IS NULL;
UPDATE my_products SET workspace_id = <WORKSPACE_ID> WHERE user_id = 1 AND workspace_id IS NULL;
UPDATE seller_credentials SET workspace_id = <WORKSPACE_ID> WHERE user_id = 1 AND workspace_id IS NULL;
UPDATE storefront_sales_metrics SET workspace_id = <WORKSPACE_ID> WHERE user_id = 1 AND workspace_id IS NULL;
UPDATE storefront_orders SET workspace_id = <WORKSPACE_ID> WHERE user_id = 1 AND workspace_id IS NULL;
```

- [ ] **Step 4: Count every row AFTER — this is the safety proof**

Re-run the exact same query from Step 1:

```sql
SELECT 'validations' AS tbl, count(*) AS total, count(workspace_id) AS tagged FROM validations
UNION ALL SELECT 'my_products', count(*), count(workspace_id) FROM my_products
UNION ALL SELECT 'seller_credentials', count(*), count(workspace_id) FROM seller_credentials
UNION ALL SELECT 'storefront_sales_metrics', count(*), count(workspace_id) FROM storefront_sales_metrics
UNION ALL SELECT 'storefront_orders', count(*), count(workspace_id) FROM storefront_orders;
```

Expected: every `total` value is **byte-for-byte identical** to Step 1's numbers. `tagged` should now be `>=` Step 1's `tagged` value for every table (equal to `total` for any table where every row belongs to user 1).

- [ ] **Step 5: Present the before/after numbers to Ram directly** (this is the safety check he explicitly asked for — show both tables side by side, not just "it worked").

- [ ] **Step 6: No commit** (live data operation only, no code changed).

---

## Task 5: Verify two different accounts get two different, isolated workspaces

**Files:** none (live verification only)

**Interfaces:**
- Consumes: the deployed `ensure_workspace_for_user` logic from Task 1 (exercised here via its exact SQL, for the same reason as Task 4 — no direct HTTP endpoint calls it in isolation).

- [ ] **Step 1: Create two throwaway test users**

Use the Supabase MCP tool (`execute_sql`, `project_id: uijfkvvoncfmaxlvnfhq`). Generate one Argon2 hash locally first:

```bash
cd api && python -c "
from argon2 import PasswordHasher
print(PasswordHasher().hash('WorkspaceIsolationTest2026!'))
"
```

Then insert two accounts with that hash (reuse the same hash for both — it's a throwaway check, deleted at the end of this task):

```sql
INSERT INTO users (email, password_hash, full_name, email_verified, created_at)
VALUES
  ('workspace-test-a-delete-me@example.com', '<HASH_FROM_ABOVE>', 'Test A', TRUE, to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"')),
  ('workspace-test-b-delete-me@example.com', '<HASH_FROM_ABOVE>', 'Test B', TRUE, to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'))
RETURNING id, email;
```

Note the two returned `id` values as `<USER_A_ID>` and `<USER_B_ID>`.

- [ ] **Step 2: Provision a workspace for each, exactly as `ensure_workspace_for_user` does**

```sql
INSERT INTO workspaces (name, owner_user_id, created_at)
VALUES ('Test A''s Workspace', <USER_A_ID>, to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'))
RETURNING id;
```

Note the returned id as `<WORKSPACE_A_ID>`, then:

```sql
INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
VALUES (<WORKSPACE_A_ID>, <USER_A_ID>, 'owner', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'));
```

Repeat both statements for User B, producing `<WORKSPACE_B_ID>`.

- [ ] **Step 3: Verify the two workspaces are completely distinct**

```sql
SELECT
  (SELECT workspace_id FROM workspace_members WHERE user_id = <USER_A_ID>) AS workspace_a,
  (SELECT workspace_id FROM workspace_members WHERE user_id = <USER_B_ID>) AS workspace_b,
  (SELECT count(*) FROM workspace_members wm_a
     JOIN workspace_members wm_b ON wm_a.workspace_id = wm_b.workspace_id
     WHERE wm_a.user_id = <USER_A_ID> AND wm_b.user_id = <USER_B_ID>) AS shared_workspace_rows;
```

Expected: `workspace_a` and `workspace_b` are **different numbers**, and `shared_workspace_rows = 0` — proving neither account's workspace overlaps with the other's.

- [ ] **Step 4: Clean up — delete both throwaway accounts and their workspaces completely**

```sql
DELETE FROM workspace_members WHERE user_id IN (<USER_A_ID>, <USER_B_ID>);
DELETE FROM workspaces WHERE id IN (<WORKSPACE_A_ID>, <WORKSPACE_B_ID>);
DELETE FROM users WHERE id IN (<USER_A_ID>, <USER_B_ID>);
```

- [ ] **Step 5: Confirm cleanup left no trace**

```sql
SELECT count(*) FROM users WHERE email LIKE 'workspace-test-%-delete-me@example.com';
```

Expected: `0`.

- [ ] **Step 6: No commit** (live verification only, no code changed).

---

## Plan Self-Review

**Spec coverage:**
- "Introduce workspace as a first-class concept" → Task 1 (schema).
- "Every account gets its own workspace automatically" → Task 2 (`create_user` wiring) + Task 4 Step 2 (one-time backfill for Ram's pre-existing account).
- "Tag existing data with workspace_id" → Task 4 Step 3.
- "Additive only, no query-layer cutover, no UI changes, Amazon linking untouched, snapshots untouched" → stated in Global Constraints, and no task touches any endpoint, any frontend file, `amazon_sp_api.py`, or the `snapshots` table.
- "Before/after row-count safety check shown to Ram" → Task 4 Steps 1, 4, 5.
- "Live two-account isolation proof" → Task 5.
- "Multi-workspace-per-user representable without further schema change" → satisfied by `workspace_members` being a many-to-many join table (no `UNIQUE(user_id)` constraint, only `UNIQUE(workspace_id, user_id)`) — no task needed, it's a property of the Task 1 schema.

**Placeholder scan:** No TBD/TODO markers. All SQL and Python is complete, runnable code, not descriptions of code.

**Type consistency:** `ensure_workspace_for_user(user_id, full_name=None)` is defined once in Task 1 and called with matching argument order/names in Task 2 (`ensure_workspace_for_user(user["id"], full_name)`) and Task 4 (implicitly, via its equivalent SQL). `backfill_workspace_for_user` and `count_workspace_rows` are defined in Task 1; their live-verification equivalents in Task 4 use identical table lists and column names.
