# Sync Engine (Blueprint Stage 3) — Design Spec

## Goal

Formalize the nightly Amazon storefront sync into a robust job runner: retries
on transient failures, a persisted history of every sync attempt, and
wave-batching so the system doesn't need rework as connected-account count
grows. No new infrastructure — the same GitHub Actions cron trigger, the same
single Render web service.

## Non-goals (explicitly out of scope for this stage)

- A frontend progress UI. This stage only makes sync history queryable via an
  authenticated JSON endpoint. A dashboard page is a later, separate piece of
  work once there's more than one account to look at.
- Failure alerting (email on failed sync). Persisted history is enough for now
  — revisit once there are enough accounts that manually checking doesn't
  scale.
- A dedicated worker process / external queue (Celery, RQ, etc.). Sync stays
  synchronous, inside the existing API request that the cron job calls. Real
  queue infrastructure is a future migration if/when account volume demands
  it, not a now problem.
- Concurrency within a wave. Waves are batches for pacing, not parallelism —
  accounts inside a wave still sync one at a time. Parallelizing is a
  performance optimization for a future stage, not needed at current scale.

## Current state (baseline, verified by direct code read)

- `.github/workflows/nightly-storefront-sync.yml` cron-triggers
  `POST /storefront/sync-all` on the deployed API.
- `main.py:806-821` (`sync_all_storefronts`) loops every `user_id` from
  `db.get_user_ids_with_credentials()` sequentially, calling
  `amazon_sp_api.sync_storefront_data(user_id)` per account. Each call is
  already wrapped in try/except inside `sync_storefront_data`, so one
  account's failure can't crash the batch or block others — that guarantee is
  kept, not rebuilt.
- `amazon_sp_api.py`: `get_sp_api_access_token` (line 16), `sync_sales_metrics`
  (line 85), `sync_recent_orders` (line 129) each make one `requests` call and
  raise immediately on any non-200 — no retry, no distinction between a
  rate-limit (`429`) and a real failure (`401`/`403`).
- No job-history table exists anywhere (`sync_jobs`, `sync_runs`, etc. — zero
  matches). Failures are `print()`-ed to Render's log stream and returned in
  the HTTP response body only; nothing is persisted.
- `init_db()` (where all schema migrations live) never runs in production —
  Render's start command is `uvicorn main:app`, not `python db.py`. Confirmed
  during Stage 1. Any new table must be applied by hand via Supabase
  `execute_sql`, same as `WORKSPACE_MIGRATION` was.

## Data model

New table, added via idempotent migration (`CREATE TABLE IF NOT EXISTS`,
matching the existing `WORKSPACE_MIGRATION` / `GOOGLE_AUTH_MIGRATION` pattern
in `db.py`):

```sql
CREATE TABLE IF NOT EXISTS sync_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wave_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',   -- 'running' | 'ok' | 'error'
    attempts INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user ON sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_started ON sync_jobs(started_at);
```

Timestamps stored as ISO-8601 text, consistent with every other table in this
schema (`created_at`, `joined_at`, etc. are all `TEXT`, not native
`TIMESTAMP` — matching existing convention, not introducing a new one).

## Components

### 1. `api/amazon_sp_api.py` — retry helper

A small internal retry wrapper (no new dependency — `tenacity` is not in
`requirements.txt` and the existing 4-package footprint stays minimal):

```python
import time

def _call_with_retry(fn, max_attempts=3, backoff_base=2):
    """Calls fn() (a zero-arg callable that performs one HTTP request and
    raises on failure). Retries on 429/5xx with exponential backoff.
    Re-raises immediately on any other error (e.g. 401/403 — retrying a bad
    credential wastes time and delays a real failure signal)."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(), attempt
        except SpApiRetryableError as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(backoff_base ** attempt)
    raise last_error
```

`sync_sales_metrics` and `sync_recent_orders` change their non-200 handling
to raise `SpApiRetryableError` for `429` and `5xx`, and a plain `Exception`
(unchanged today) for everything else. Callers use `_call_with_retry` to wrap
the request and capture the attempt count.

`SpApiRetryableError` is a new small exception class in the same file.

`get_sp_api_access_token` (the LWA token exchange, line 16) is deliberately
**not** wrapped in retry. A failure there is almost always a credential
problem (expired/revoked refresh token, wrong client secret) rather than a
rate limit — retrying a bad credential three times with backoff just delays
a failure that was never going to succeed. It keeps its current
fail-immediately behavior.

### 2. `api/db.py` — job persistence

```python
SYNC_JOBS_MIGRATION = """
CREATE TABLE IF NOT EXISTS sync_jobs ( ... as above ... );
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user ON sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_started ON sync_jobs(started_at);
"""
```

New functions, following the existing `get_conn()` context-manager pattern
used throughout `db.py`:

- `start_sync_job(user_id: int, wave_number: int) -> int` — inserts a
  `status='running'` row, returns the new `id`.
- `finish_sync_job(job_id: int, status: str, attempts: int, error: str | None) -> None`
  — updates `status`, `attempts`, `error`, `finished_at`.
- `get_recent_sync_jobs(user_id: int | None = None, limit: int = 50) -> list[dict]`
  — most recent jobs, optionally filtered by user, newest first.

`init_db()` gets `cur.execute(SYNC_JOBS_MIGRATION)` added for documentation
parity with the rest of the schema, but the migration is applied directly via
Supabase `execute_sql` before any code depending on the table ships — same
sequencing used for `WORKSPACE_MIGRATION`.

### 3. `api/sync_engine.py` — new module, orchestration only

```python
WAVE_SIZE = 5
WAVE_PAUSE_SECONDS = 2

def run_all_syncs() -> dict:
    """Replaces the loop body of main.sync_all_storefronts(). Batches
    accounts into waves, persists a sync_jobs row per attempt, and returns
    the same {sellers, succeeded, results} shape the endpoint already
    returns today, so no caller (including the GitHub Actions cron) needs
    to change."""
```

This module owns *only* orchestration (batching, timing, job-row
bookkeeping). It calls `amazon_sp_api.sync_storefront_data(user_id)` exactly
as `main.py` does today — the actual sync logic is untouched.

### 4. `api/main.py` — wire-up

`sync_all_storefronts` (line 806) becomes a thin call into
`sync_engine.run_all_syncs()`. `/storefront/sync` (single-user, line 798) is
unchanged — its error path already surfaces inline via `HTTPException`.

New read endpoint:

```python
@app.get("/storefront/sync-jobs", dependencies=[Depends(require_key)])
def sync_jobs(user_id: int = Depends(require_user), limit: int = 20):
    return {"jobs": db.get_recent_sync_jobs(user_id=user_id, limit=limit)}
```

Scoped to the authenticated user's own jobs — consistent with every other
per-user endpoint in this file. Not a UI; a JSON endpoint Ram can hit directly
to confirm a night's sync actually ran, until a real dashboard page exists.

## Error handling

- A single account's failure (even after exhausted retries) cannot abort the
  batch — the existing per-account try/except boundary in
  `sync_storefront_data` is preserved unchanged.
- Every job attempt is persisted regardless of outcome — `finish_sync_job` is
  called from a `finally`-equivalent path so a row is never left stuck at
  `status='running'` if something unexpected happens.
- Non-retryable errors (bad credentials, malformed request) fail on the first
  attempt rather than wasting up to 6 seconds (2+4, the two backoff sleeps
  before the 3rd and final attempt) retrying something that will never
  succeed.
- A `sync_jobs` row can be left stuck at `status='running'` only in the
  irreducible case where the database itself is unreachable at both the
  success/failure write AND the guard's own write attempt (`sync_engine.py`'s
  job-write calls are individually guarded so a single DB hiccup can't do
  this — see the implementation plan's Task 3 fix). No reaper/timeout sweep
  exists for this edge case yet; deferred until the deferred progress UI
  (a non-goal of this stage) needs to distinguish a truly-stuck row from a
  slow one.

## Testing / verification

Following the same discipline used for Stage 0 and Stage 1 — live
verification against real data, not just code review:

1. Trigger `POST /storefront/sync-all` for real against the deployed API.
2. Query `GET /storefront/sync-jobs` and confirm a row exists with
   `status='ok'`, `attempts=1`, correct `started_at`/`finished_at`.
3. Temporarily point at an invalid/expired token to force a real failure,
   confirm the row lands as `status='error'` with a real error message
   (not fabricated), then restore the real credential.
4. Confirm `WAVE_SIZE=5` with 1 account produces `wave_number=1` for that
   account — batching logic exercised even at current low volume.
