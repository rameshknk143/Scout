# Sync Engine (Blueprint Stage 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the loose, unrecoverable nightly sync loop with a proper job runner — retries transient Amazon SP-API failures, persists every attempt's outcome, and batches accounts into waves — with zero new infrastructure.

**Architecture:** Three additive pieces on top of the existing GitHub-Actions-cron → `POST /storefront/sync-all` flow: a `sync_jobs` history table + persistence functions in `db.py`, a retry-with-backoff wrapper around the two SP-API network calls in `amazon_sp_api.py`, and a new `sync_engine.py` module that owns wave-batching and job bookkeeping. `main.py`'s existing endpoint becomes a thin call into the new module.

**Tech Stack:** Python 3, FastAPI, psycopg2 (existing connection pool via `db.get_conn()`), no new dependencies.

## Global Constraints

- No new Python dependencies — `requirements.txt` stays at its current 8 packages (retry logic is hand-rolled, not `tenacity`).
- No new infrastructure — same single Render web service (`scout-api`), same GitHub Actions cron trigger. No worker process, no external queue.
- `init_db()` never runs in production (Render's start command is `uvicorn main:app`, not `python db.py` — confirmed during Stage 1). Any new migration must be applied by hand via the Supabase `execute_sql` tool before code that depends on it ships.
- Timestamps are stored as ISO-8601 `TEXT`, matching every existing table (`created_at`, `joined_at`, etc.) — not native `TIMESTAMP` columns.
- `get_sp_api_access_token` (the LWA token exchange) is NOT wrapped in retry — a failure there is a credential problem, not a rate limit, and retrying wastes time on something that will never succeed.
- Per-account sync failures must never abort the batch or block other accounts — this guarantee already exists (`sync_storefront_data`'s own try/except) and must be preserved, not rebuilt.
- No mocked tests. This codebase has no pytest suite (confirmed: only `api/test_email_delivery.py`, a manual script harness, exists). Verification is `python -m py_compile` for local syntax checks, plus live checks against the real deployed API and real database — same discipline used for Stage 0 and Stage 1.

---

### Task 1: Sync job persistence in `db.py`

**Files:**
- Modify: `api/db.py` (add migration constant near line 251, after `WORKSPACE_MIGRATION`; add `cur.execute(...)` call inside `init_db()` at line 281; add three new functions after `get_user_ids_with_credentials()`, currently at line 703-709)

**Interfaces:**
- Produces: `db.start_sync_job(user_id: int, wave_number: int) -> int` (returns new job id), `db.finish_sync_job(job_id: int, status: str, attempts: int, error: str | None) -> None`, `db.get_recent_sync_jobs(user_id: int | None = None, limit: int = 50) -> list[dict]`

- [ ] **Step 1: Add the migration constant**

In `api/db.py`, immediately after the `WORKSPACE_MIGRATION` closing `"""` (currently line 251), insert:

```python

# Persists every sync attempt from the nightly/manual storefront sync so
# failures are queryable instead of vanishing into Render's log stream.
# See docs/superpowers/specs/2026-07-19-sync-engine-design.md.
SYNC_JOBS_MIGRATION = """
CREATE TABLE IF NOT EXISTS sync_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wave_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    attempts INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user ON sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_started ON sync_jobs(started_at);
"""
```

- [ ] **Step 2: Wire it into `init_db()` for documentation parity**

In `api/db.py`, `init_db()` currently reads:

```python
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(MULTITENANT_MIGRATION)
            cur.execute(GOOGLE_AUTH_MIGRATION)
            cur.execute(WORKSPACE_MIGRATION)
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
            cur.execute(SYNC_JOBS_MIGRATION)
```

This keeps `init_db()` accurate as documentation even though it's dead code in production — the real migration apply happens by hand in Task 5.

- [ ] **Step 3: Add the three persistence functions**

Immediately after `get_user_ids_with_credentials()` (ends at line 709), insert:

```python


def start_sync_job(user_id, wave_number):
    """Inserts a status='running' sync_jobs row for one account's sync
    attempt and returns its id. Call finish_sync_job with this id once the
    attempt completes, whether it succeeds or fails — a job row must never
    be left stuck at 'running'."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sync_jobs (user_id, wave_number, status, started_at) "
                "VALUES (%s, %s, 'running', %s) RETURNING id",
                (user_id, wave_number, now),
            )
            return cur.fetchone()[0]


def finish_sync_job(job_id, status, attempts, error):
    """Updates a sync_jobs row to its final status ('ok' or 'error'), how
    many attempts the underlying SP-API calls needed, and the error message
    if any."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sync_jobs SET status = %s, attempts = %s, error = %s, finished_at = %s "
                "WHERE id = %s",
                (status, attempts, error, now, job_id),
            )


def get_recent_sync_jobs(user_id=None, limit=50):
    """Most recent sync_jobs rows, newest first. Filtered to one account if
    user_id is given."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if user_id is not None:
                cur.execute(
                    "SELECT * FROM sync_jobs WHERE user_id = %s ORDER BY started_at DESC LIMIT %s",
                    (user_id, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM sync_jobs ORDER BY started_at DESC LIMIT %s",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]
```

- [ ] **Step 4: Local syntax check**

Run (from `api/`):
```bash
python -m py_compile db.py
```
Expected: no output, exit code 0. (A real functional test needs a live database — that happens in Task 5 once this is deployed alongside the code that calls it.)

- [ ] **Step 5: Commit**

```bash
git add api/db.py
git commit -m "feat: add sync_jobs table and job persistence functions"
```

---

### Task 2: Retry-with-backoff in `amazon_sp_api.py`

**Files:**
- Modify: `api/amazon_sp_api.py` (add imports, exception class, and retry helper near the top; restructure `sync_sales_metrics` at line 85 and `sync_recent_orders` at line 129; update `sync_storefront_data` at line 39 to thread attempt counts through its return value)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `amazon_sp_api.sync_storefront_data(user_id: int) -> dict` — return dict now always includes an `"attempts": int` key alongside the existing `"ok"` and `"message"`/`"error"` keys. This is what Task 3's `sync_engine.py` reads to call `db.finish_sync_job`.

- [ ] **Step 1: Add the retry helper and exception class**

In `api/amazon_sp_api.py`, after the existing imports (line 1-4), add:

```python
import time
```

so the import block reads:

```python
import os
import time
import requests
from datetime import datetime, timedelta, timezone
import db
```

Then, immediately after `DEFAULT_ENDPOINT` (currently line 14) and before `get_sp_api_access_token`, insert:

```python

class SpApiRetryableError(Exception):
    """Raised for SP-API responses that are safe to retry: 429 (rate limit)
    and 5xx (transient server error). Any other failure (401/403/400, etc.)
    should NOT use this — retrying a bad request just delays the real
    error."""


def _call_with_retry(fn, max_attempts=3, backoff_base=2):
    """Calls fn() (a zero-arg callable performing one HTTP request that
    raises SpApiRetryableError on a transient failure). Retries up to
    max_attempts times with exponential backoff (backoff_base ** attempt
    seconds between tries). Any other exception propagates immediately —
    no retry. On final exhaustion, attaches how many attempts were made to
    the raised exception as `.attempts`, so callers can record it even on
    failure. Returns (result, attempts_used) on success."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(), attempt
        except SpApiRetryableError as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(backoff_base ** attempt)
    last_error.attempts = max_attempts
    raise last_error
```

- [ ] **Step 2: Restructure `sync_sales_metrics` to retry only the network call**

Replace the current body (lines 85-126):

```python
def sync_sales_metrics(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str):
    """Queries SP-API /sales/v1/orderMetrics and caches the results."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    interval = f"{start_date.isoformat()}--{end_date.isoformat()}"
    url = f"{endpoint}/sales/v1/orderMetrics"
    params = {
        "marketplaceIds": marketplace_id,
        "interval": interval,
        "granularity": "Day"
    }
    
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise Exception(f"SP-API Sales OrderMetrics query failed: {res.text}")
        
    metrics = res.json().get("payload", [])
    for metric in metrics:
        # Interval is formatted as: 2026-07-15T00:00:00Z--2026-07-16T00:00:00Z
        interval_start = metric["interval"].split("--")[0]
        order_count = metric["orderCount"]
        unit_count = metric["unitCount"]
        total_sales_amount = float(metric["totalSales"]["amount"])
        currency = metric["totalSales"]["currencyCode"]
        
        db.save_storefront_sales_metric(
            user_id=user_id,
            selling_partner_id=selling_partner_id,
            marketplace_id=marketplace_id,
            interval_start=interval_start,
            order_count=order_count,
            unit_count=unit_count,
            total_sales_amount=total_sales_amount,
            currency=currency
        )
```

with:

```python
def sync_sales_metrics(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str) -> int:
    """Queries SP-API /sales/v1/orderMetrics and caches the results. Retries
    the network call on a transient failure. Returns the number of attempts
    it took (1 if it succeeded on the first try)."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    interval = f"{start_date.isoformat()}--{end_date.isoformat()}"
    url = f"{endpoint}/sales/v1/orderMetrics"
    params = {
        "marketplaceIds": marketplace_id,
        "interval": interval,
        "granularity": "Day"
    }

    def _request():
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 429 or res.status_code >= 500:
            raise SpApiRetryableError(f"SP-API Sales OrderMetrics query failed ({res.status_code}): {res.text}")
        if res.status_code != 200:
            raise Exception(f"SP-API Sales OrderMetrics query failed: {res.text}")
        return res

    res, attempts = _call_with_retry(_request)

    metrics = res.json().get("payload", [])
    for metric in metrics:
        # Interval is formatted as: 2026-07-15T00:00:00Z--2026-07-16T00:00:00Z
        interval_start = metric["interval"].split("--")[0]
        order_count = metric["orderCount"]
        unit_count = metric["unitCount"]
        total_sales_amount = float(metric["totalSales"]["amount"])
        currency = metric["totalSales"]["currencyCode"]
        
        db.save_storefront_sales_metric(
            user_id=user_id,
            selling_partner_id=selling_partner_id,
            marketplace_id=marketplace_id,
            interval_start=interval_start,
            order_count=order_count,
            unit_count=unit_count,
            total_sales_amount=total_sales_amount,
            currency=currency
        )

    return attempts
```

- [ ] **Step 3: Restructure `sync_recent_orders` the same way**

Replace the current body (lines 129-172):

```python
def sync_recent_orders(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str):
    """Queries SP-API /orders/v0/orders and caches details."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    
    # SP-API Orders rejects fractional seconds / offset form; it needs plain
    # ISO-8601 with a trailing Z (e.g. 2026-07-17T00:00:00Z), or it 400s.
    created_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{endpoint}/orders/v0/orders"
    params = {
        "MarketplaceIds": marketplace_id,
        "CreatedAfter": created_after,
        "MaxResultsPerPage": 20
    }
    
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise Exception(f"SP-API Orders query failed: {res.text}")
        
    orders = res.json().get("payload", {}).get("Orders", [])
    for order in orders:
        amazon_order_id = order["AmazonOrderId"]
        purchase_date = order["PurchaseDate"]
        order_status = order["OrderStatus"]
        
        # Order total might be missing if pending or cancelled
        order_total = order.get("OrderTotal", {})
        amount = float(order_total.get("Amount", 0.0)) if order_total else 0.0
        currency = order_total.get("CurrencyCode", "INR") if order_total else "INR"
        items_count = int(order.get("NumberOfItemsUnshipped", 0)) + int(order.get("NumberOfItemsShipped", 0))
        if items_count == 0:
            items_count = 1
            
        db.save_storefront_order(
            user_id=user_id,
            amazon_order_id=amazon_order_id,
            purchase_date=purchase_date,
            order_status=order_status,
            amount=amount,
            currency=currency,
            items_count=items_count
        )
```

with:

```python
def sync_recent_orders(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str) -> int:
    """Queries SP-API /orders/v0/orders and caches details. Retries the
    network call on a transient failure. Returns the number of attempts it
    took (1 if it succeeded on the first try)."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }
    
    # SP-API Orders rejects fractional seconds / offset form; it needs plain
    # ISO-8601 with a trailing Z (e.g. 2026-07-17T00:00:00Z), or it 400s.
    created_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{endpoint}/orders/v0/orders"
    params = {
        "MarketplaceIds": marketplace_id,
        "CreatedAfter": created_after,
        "MaxResultsPerPage": 20
    }

    def _request():
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 429 or res.status_code >= 500:
            raise SpApiRetryableError(f"SP-API Orders query failed ({res.status_code}): {res.text}")
        if res.status_code != 200:
            raise Exception(f"SP-API Orders query failed: {res.text}")
        return res

    res, attempts = _call_with_retry(_request)

    orders = res.json().get("payload", {}).get("Orders", [])
    for order in orders:
        amazon_order_id = order["AmazonOrderId"]
        purchase_date = order["PurchaseDate"]
        order_status = order["OrderStatus"]
        
        # Order total might be missing if pending or cancelled
        order_total = order.get("OrderTotal", {})
        amount = float(order_total.get("Amount", 0.0)) if order_total else 0.0
        currency = order_total.get("CurrencyCode", "INR") if order_total else "INR"
        items_count = int(order.get("NumberOfItemsUnshipped", 0)) + int(order.get("NumberOfItemsShipped", 0))
        if items_count == 0:
            items_count = 1
            
        db.save_storefront_order(
            user_id=user_id,
            amazon_order_id=amazon_order_id,
            purchase_date=purchase_date,
            order_status=order_status,
            amount=amount,
            currency=currency,
            items_count=items_count
        )

    return attempts
```

- [ ] **Step 4: Thread attempt counts through `sync_storefront_data`**

Replace the current body (lines 39-82):

```python
def sync_storefront_data(user_id: int) -> dict:
    """
    Main orchestration function to sync sales metrics and orders for a user.
    If using mock credentials or ALLOW_MOCK_LWA is enabled, it generates high-fidelity simulated statistics.
    """
    user_creds = db.get_seller_credentials(user_id)

    if not user_creds:
        return {"ok": False, "error": "No connected Amazon Seller account found. Please link your account in Settings first."}
        
    cred = user_creds[0]
    selling_partner_id = cred["selling_partner_id"]
    refresh_token = cred["refresh_token"]
    marketplace_id = cred.get("marketplace_id") or "A21TJRUUN4KGV"

    # A None token means db decryption returned nothing — the server's
    # TOKEN_ENCRYPTION_KEY doesn't match the key the token was saved with.
    # Surface it clearly instead of crashing on None.startswith below.
    if not refresh_token:
        return {"ok": False, "error": "Stored Amazon token could not be decrypted on the server (TOKEN_ENCRYPTION_KEY mismatch). Set TOKEN_ENCRYPTION_KEY on Render to the value it was saved with."}

    # Check if credentials are mock/sandbox
    is_mock = refresh_token.startswith("mock") or os.environ.get("ALLOW_MOCK_LWA") == "1"
    
    if is_mock:
        return _run_simulation_sync(user_id, selling_partner_id, marketplace_id)
        
    try:
        access_token = get_sp_api_access_token(refresh_token)
        endpoint = MARKETPLACE_ENDPOINTS.get(marketplace_id, DEFAULT_ENDPOINT)

        # 1. Sync Sales Metrics (Last 14 days)
        sync_sales_metrics(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        # 2. Sync Recent Orders
        sync_recent_orders(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        return {"ok": True, "message": "Storefront data synchronized successfully."}
    except Exception as e:
        # Do NOT fabricate data on failure. A real sync error must surface as an
        # honest error so the dashboard shows real/empty state, never simulated
        # numbers dressed up as the seller's actual sales.
        print(f"SP-API live sync failed: {e}")
        return {"ok": False, "error": f"Amazon sync failed: {e}"}
```

with:

```python
def sync_storefront_data(user_id: int) -> dict:
    """
    Main orchestration function to sync sales metrics and orders for a user.
    If using mock credentials or ALLOW_MOCK_LWA is enabled, it generates high-fidelity simulated statistics.
    Return dict always includes "attempts": how many tries the SP-API calls
    needed in total (1 for the mock path or any failure before a network
    call was attempted) — used by sync_engine.py to record sync_jobs history.
    """
    user_creds = db.get_seller_credentials(user_id)

    if not user_creds:
        return {"ok": False, "error": "No connected Amazon Seller account found. Please link your account in Settings first.", "attempts": 1}
        
    cred = user_creds[0]
    selling_partner_id = cred["selling_partner_id"]
    refresh_token = cred["refresh_token"]
    marketplace_id = cred.get("marketplace_id") or "A21TJRUUN4KGV"

    # A None token means db decryption returned nothing — the server's
    # TOKEN_ENCRYPTION_KEY doesn't match the key the token was saved with.
    # Surface it clearly instead of crashing on None.startswith below.
    if not refresh_token:
        return {"ok": False, "error": "Stored Amazon token could not be decrypted on the server (TOKEN_ENCRYPTION_KEY mismatch). Set TOKEN_ENCRYPTION_KEY on Render to the value it was saved with.", "attempts": 1}

    # Check if credentials are mock/sandbox
    is_mock = refresh_token.startswith("mock") or os.environ.get("ALLOW_MOCK_LWA") == "1"
    
    if is_mock:
        result = _run_simulation_sync(user_id, selling_partner_id, marketplace_id)
        result.setdefault("attempts", 1)
        return result
        
    try:
        access_token = get_sp_api_access_token(refresh_token)
        endpoint = MARKETPLACE_ENDPOINTS.get(marketplace_id, DEFAULT_ENDPOINT)

        # 1. Sync Sales Metrics (Last 14 days)
        sales_attempts = sync_sales_metrics(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        # 2. Sync Recent Orders
        orders_attempts = sync_recent_orders(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        return {"ok": True, "message": "Storefront data synchronized successfully.", "attempts": max(sales_attempts, orders_attempts)}
    except Exception as e:
        # Do NOT fabricate data on failure. A real sync error must surface as an
        # honest error so the dashboard shows real/empty state, never simulated
        # numbers dressed up as the seller's actual sales.
        print(f"SP-API live sync failed: {e}")
        return {"ok": False, "error": f"Amazon sync failed: {e}", "attempts": getattr(e, "attempts", 1)}
```

- [ ] **Step 5: Local syntax check**

Run (from `api/`):
```bash
python -m py_compile amazon_sp_api.py
```
Expected: no output, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add api/amazon_sp_api.py
git commit -m "feat: retry SP-API calls with backoff on transient failures"
```

---

### Task 3: Wave-batching orchestration module

**Files:**
- Create: `api/sync_engine.py`

**Interfaces:**
- Consumes: `db.get_user_ids_with_credentials()` (existing), `db.start_sync_job`/`db.finish_sync_job` (Task 1), `amazon_sp_api.sync_storefront_data(user_id) -> dict` with `"attempts"` key (Task 2).
- Produces: `sync_engine.run_all_syncs() -> dict` returning `{"sellers": int, "succeeded": int, "results": list[dict]}` — same shape `main.sync_all_storefronts()` already returns today, so Task 4's wiring is a drop-in replacement.

- [ ] **Step 1: Write `api/sync_engine.py`**

```python
"""Orchestrates the nightly/manual storefront sync across every connected
seller account: batches accounts into waves (pacing insurance against
Amazon's rate limits as account count grows), and persists a sync_jobs row
for every account attempted. See
docs/superpowers/specs/2026-07-19-sync-engine-design.md."""

import time

import amazon_sp_api
import db

WAVE_SIZE = 5
WAVE_PAUSE_SECONDS = 2


def run_all_syncs() -> dict:
    """Refreshes every connected seller's storefront data. Accounts are
    processed in waves of WAVE_SIZE, with a WAVE_PAUSE_SECONDS pause between
    waves. Each account gets a sync_jobs row recording the outcome — a
    failure for one seller never fabricates data, blocks other sellers, or
    aborts the batch."""
    user_ids = db.get_user_ids_with_credentials()
    waves = [user_ids[i:i + WAVE_SIZE] for i in range(0, len(user_ids), WAVE_SIZE)]

    results = []
    for wave_number, wave in enumerate(waves, start=1):
        for uid in wave:
            job_id = db.start_sync_job(uid, wave_number)
            try:
                r = amazon_sp_api.sync_storefront_data(uid)
                status = "ok" if r.get("ok") else "error"
                db.finish_sync_job(job_id, status, r.get("attempts", 1), r.get("error"))
                results.append({"user_id": uid, "ok": bool(r.get("ok")), "error": r.get("error")})
            except Exception as e:
                # sync_storefront_data already catches its own exceptions and
                # returns {"ok": False, ...} — this is a last-resort guard so
                # a genuinely unexpected crash still closes out the job row
                # instead of leaving it stuck at status='running' forever.
                db.finish_sync_job(job_id, "error", 1, str(e))
                results.append({"user_id": uid, "ok": False, "error": str(e)})

        if wave_number < len(waves):
            time.sleep(WAVE_PAUSE_SECONDS)

    return {
        "sellers": len(user_ids),
        "succeeded": sum(1 for r in results if r["ok"]),
        "results": results,
    }
```

- [ ] **Step 2: Local syntax check**

Run (from `api/`):
```bash
python -m py_compile sync_engine.py
```
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add api/sync_engine.py
git commit -m "feat: add wave-batching sync orchestration module"
```

---

### Task 4: Wire `main.py`

**Files:**
- Modify: `api/main.py` (add `import sync_engine` to the import block at line 27-36; replace `sync_all_storefronts` body at lines 806-821; add a new `sync_jobs` endpoint after it)

**Interfaces:**
- Consumes: `sync_engine.run_all_syncs()` (Task 3), `db.get_recent_sync_jobs(user_id, limit)` (Task 1).

- [ ] **Step 1: Add the import**

In `api/main.py`, the import block currently reads (lines 27-36):

```python
import alerts
import amazon_sp_api
import auth
import db
import google_auth
import listing_analyzer
import password_breach
import profit_calculator
import scorer
import trend_radar
```

Change to (alphabetical, matching existing order):

```python
import alerts
import amazon_sp_api
import auth
import db
import google_auth
import listing_analyzer
import password_breach
import profit_calculator
import scorer
import sync_engine
import trend_radar
```

- [ ] **Step 2: Replace `sync_all_storefronts` and add the job-history endpoint**

Replace (lines 806-821):

```python
@app.post("/storefront/sync-all", dependencies=[Depends(require_key)])
def sync_all_storefronts():
    """Refresh every connected seller's storefront data. Authenticated by the
    shared X-Scout-Key only (no per-user header), so a scheduled job can run it
    daily. Per-seller results carry the real ok/error from the live SP-API call
    — a failure for one seller never fabricates data or blocks the others."""
    user_ids = db.get_user_ids_with_credentials()
    results = []
    for uid in user_ids:
        r = amazon_sp_api.sync_storefront_data(uid)
        results.append({"user_id": uid, "ok": bool(r.get("ok")), "error": r.get("error")})
    return {
        "sellers": len(user_ids),
        "succeeded": sum(1 for r in results if r["ok"]),
        "results": results,
    }
```

with:

```python
@app.post("/storefront/sync-all", dependencies=[Depends(require_key)])
def sync_all_storefronts():
    """Refresh every connected seller's storefront data, in waves, with
    retry-with-backoff on transient SP-API failures and a persisted
    sync_jobs row per attempt. Authenticated by the shared X-Scout-Key only
    (no per-user header), so a scheduled job can run it daily."""
    return sync_engine.run_all_syncs()


@app.get("/storefront/sync-jobs", dependencies=[Depends(require_key)])
def sync_jobs(user_id: int = Depends(require_user), limit: int = 20):
    """Recent sync history for the authenticated account — lets you confirm
    a night's sync actually ran (and how) without reading Render's logs."""
    return {"jobs": db.get_recent_sync_jobs(user_id=user_id, limit=limit)}
```

- [ ] **Step 3: Local syntax check**

Run (from `api/`):
```bash
python -m py_compile main.py
```
Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

```bash
git add api/main.py
git commit -m "feat: wire sync-all through sync_engine, add sync-jobs endpoint"
```

---

### Task 5: Apply migration and verify live

**Files:** none (deployment + verification only)

**Interfaces:** none — this task exercises Tasks 1-4 end to end against the real deployed API and real database.

- [ ] **Step 1: Apply `SYNC_JOBS_MIGRATION` by hand via Supabase**

The migration must exist in the database BEFORE the new code (which calls `db.start_sync_job`) is live — otherwise the first sync-all after deploy would crash on a missing table. Apply it first, using the Supabase `execute_sql` tool against project `uijfkvvoncfmaxlvnfhq`, with this exact SQL:

```sql
CREATE TABLE IF NOT EXISTS sync_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wave_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    attempts INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user ON sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_started ON sync_jobs(started_at);
```

Expected: statement succeeds, no rows returned (DDL). Confirm with a follow-up `SELECT count(*) FROM sync_jobs;` — expect `0`.

- [ ] **Step 2: Push to `main`**

```bash
git push origin main
```

Render auto-deploys `scout-api` from `main` — no manual deploy step needed for this backend-only change (no frontend/Vercel changes in this plan).

- [ ] **Step 3: Wait for the Render deploy, then confirm the API is healthy**

```bash
curl -s https://scout-api-3yvy.onrender.com/health
```

Expected: `200` with a healthy JSON body. If Render is still building, wait and retry.

- [ ] **Step 4: Trigger a real sync-all and confirm a job row is written**

```bash
curl -s -X POST https://scout-api-3yvy.onrender.com/storefront/sync-all -H "X-Scout-Key: <the real API_KEY>"
```

Expected: `{"sellers": 1, "succeeded": 1, "results": [...]}` — `succeeded` matches `sellers` for a healthy account.

Then query the job history for Ram's account (user_id=1):

```bash
curl -s "https://scout-api-3yvy.onrender.com/storefront/sync-jobs?limit=5" -H "X-Scout-Key: <the real API_KEY>" -H "X-Scout-User: 1"
```

Expected: `{"jobs": [{"status": "ok", "attempts": 1, "wave_number": 1, "started_at": ..., "finished_at": ..., ...}]}` — a real row, not empty.

- [ ] **Step 5: Verify the error path with a throwaway account (do NOT touch Ram's real credential)**

Same pattern used for the Stage 0 two-account isolation proof — create a real throwaway account, connect it with a deliberately invalid Amazon refresh token, trigger a sync, confirm the failure is captured correctly, then delete the throwaway account.

`seller_credentials.refresh_token` is stored Fernet-encrypted (`db._encrypt_token` / `_decrypt_token`, `api/db.py:63-76`) — inserting a *plaintext* bogus string directly would fail to decrypt (`InvalidToken` caught → `_decrypt_token` returns `None`) and hit the unrelated "TOKEN_ENCRYPTION_KEY mismatch" branch instead of the real LWA-failure branch this step means to test. The bogus token must be encrypted with the real key first, same as a real connect flow would produce:

1. Generate a validly-encrypted bogus token (run wherever `TOKEN_ENCRYPTION_KEY` is available — e.g. Render's shell, or locally with it exported):
   ```bash
   python -c "
   import os
   from cryptography.fernet import Fernet
   f = Fernet(os.environ['TOKEN_ENCRYPTION_KEY'].encode())
   print(f.encrypt(b'invalid-token-for-testing').decode())
   "
   ```
   Note the printed ciphertext — this is `<encrypted bogus token>` below. It decrypts successfully (so `sync_storefront_data` proceeds past the decrypt check) but isn't a real Amazon-issued token, so the LWA exchange itself genuinely fails — a realistic non-retryable credential error, not a fabricated one.
2. Create a throwaway user directly via Supabase `execute_sql` (no real login needed — `require_user` only trusts the `X-Scout-User` header, it doesn't check a session):
   ```sql
   INSERT INTO users (email, password_hash, full_name, email_verified, created_at, auth_provider)
   VALUES ('sync-test-throwaway@scoutveda.com', NULL, 'Sync Test', true, now()::text, 'password')
   RETURNING id;
   ```
   Note the returned `id` — this is `<throwaway id>` for the rest of this step.
3. Insert a `seller_credentials` row for that user using the encrypted value from step 1:
   ```sql
   INSERT INTO seller_credentials (user_id, selling_partner_id, refresh_token, marketplace_id)
   VALUES (<throwaway id>, 'A_FAKE_SP_ID_FOR_TEST', '<encrypted bogus token>', 'A21TJRUUN4KGV');
   ```
4. Trigger `POST /storefront/sync` with `X-Scout-User: <throwaway id>` — expect `400` with an error mentioning LWA token exchange failure.
5. Query `GET /storefront/sync-jobs?limit=5` with `X-Scout-User: <throwaway id>` — expect a row with `status='error'`, `attempts=1` (LWA failures are not retried, per the Global Constraints), and the real error text.
6. Delete the throwaway user (cascades to `seller_credentials` and `sync_jobs` via `ON DELETE CASCADE`):
   ```sql
   DELETE FROM users WHERE email = 'sync-test-throwaway@scoutveda.com';
   ```
7. Confirm deletion: `SELECT count(*) FROM users WHERE email = 'sync-test-throwaway@scoutveda.com';` — expect `0`.

- [ ] **Step 6: Confirm wave-batching runs correctly even at 1 account**

From the Step 4 response, confirm the single job row has `wave_number = 1` (not `0` or `null`) — proves the batching logic is exercised correctly even when there's only one wave.

- [ ] **Step 7: Update status docs**

Per Ram's explicit instruction to update documentation incrementally as Stage 3 lands (not just at the end):
1. Update the memory file `scoutveda-deploy-readiness.md` — mark Stage 3 backend-robustness work as DONE, with the real commit hashes from Tasks 1-4 and the live verification results from this task.
2. Update the blueprint Artifact's Stage 3 roadmap pill and Build Status callout to reflect completion, matching the pattern already used for Stage 0/1.
3. Regenerate `D:\Ram Claude Desk\ScoutVeda-Master-Blueprint.pdf` from the updated blueprint HTML, same process used earlier this session.
