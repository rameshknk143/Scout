"""
Scout's database layer — Postgres (Supabase) version.

Same table shapes and the same function signatures as the original local
SQLite db.py, so collector.py / scorer.py / trend_radar.py don't need their
own logic touched, only this import. Connection string comes from the
DATABASE_URL environment variable (Supabase gives you this directly).
"""

import html
import logging
import os
import threading
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection pool — reuse connections across requests instead of opening a
# fresh TCP socket on every call. min=2 keeps two warm connections alive;
# max=10 is plenty for this single-user tool. Initialised lazily on first use
# so a missing DATABASE_URL at import time doesn't crash the whole process.
# ---------------------------------------------------------------------------
_pool: psycopg2.pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()

def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:  # double-checked locking
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    dsn=DATABASE_URL,
                )
                logger.info("DB connection pool initialised (min=2, max=10)")
    return _pool

DATABASE_URL = os.environ["DATABASE_URL"]

# Fernet is built lazily, only when a seller token is actually
# encrypted/decrypted. This keeps token handling fail-closed (a missing
# TOKEN_ENCRYPTION_KEY raises the moment you try to store/read credentials)
# WITHOUT crashing the whole API — and every non-Amazon feature — at import
# time just because the key isn't configured. The nightly collector never
# touches tokens, so it's unaffected either way.
def _get_fernet():
    key = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set — refusing to store or read Amazon "
            "seller credentials in plaintext. Set it in the API server environment."
        )
    return Fernet(key.encode())


def _encrypt_token(value):
    if value:
        return _get_fernet().encrypt(value.encode()).decode()
    return value


def _decrypt_token(value):
    if value:
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Legacy plaintext tokens are no longer allowed for security.
            return None
    return value

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id SERIAL PRIMARY KEY,
    asin TEXT NOT NULL,
    category TEXT NOT NULL,
    list_type TEXT NOT NULL,
    rank INTEGER,
    title TEXT,
    price REAL,
    rating REAL,
    review_count INTEGER,
    image_url TEXT,
    collected_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_asin ON snapshots(asin);
CREATE INDEX IF NOT EXISTS idx_snapshots_category ON snapshots(category, list_type, collected_at);

CREATE TABLE IF NOT EXISTS validations (
    id SERIAL PRIMARY KEY,
    asin TEXT NOT NULL,
    title TEXT,
    category TEXT,
    score REAL,
    verdict TEXT,
    buy_price REAL,
    notes TEXT,
    validated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS my_products (
    id SERIAL PRIMARY KEY,
    asin TEXT UNIQUE NOT NULL,
    title TEXT,
    sku TEXT,
    supplier_cost REAL,
    shipping_fee REAL,
    target_margin REAL,
    supplier_details TEXT,
    current_stock INTEGER DEFAULT 100,
    lead_time_days INTEGER DEFAULT 14,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_credentials (
    id SERIAL PRIMARY KEY,
    selling_partner_id TEXT UNIQUE NOT NULL,
    refresh_token TEXT NOT NULL,
    marketplace_id TEXT DEFAULT 'A21TJRUUN4KGV',
    connected_at TEXT NOT NULL
);

-- Multi-tenant accounts. snapshots stays global (shared market data from the
-- nightly collector); validations / my_products / seller_credentials get scoped
-- per user via the migrate_multitenant() migration below.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));

-- Backs signup + password-reset OTP flows. code_hash is a peppered SHA-256 (no
-- plaintext codes). payload holds pending signup data (name + password hash) so
-- the account is created only after the email is verified.
CREATE TABLE IF NOT EXISTS email_otps (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    purpose TEXT NOT NULL,
    payload TEXT,
    expires_at TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_email_otps_lookup ON email_otps(lower(email), purpose, created_at);

CREATE TABLE IF NOT EXISTS storefront_sales_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    selling_partner_id TEXT NOT NULL,
    marketplace_id TEXT NOT NULL,
    interval_start TEXT NOT NULL,
    order_count INTEGER NOT NULL,
    unit_count INTEGER NOT NULL,
    total_sales_amount REAL NOT NULL,
    currency TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_storefront_sales_user_date
    ON storefront_sales_metrics(user_id, selling_partner_id, marketplace_id, interval_start);

CREATE TABLE IF NOT EXISTS storefront_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amazon_order_id TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    order_status TEXT NOT NULL,
    amount REAL,
    currency TEXT,
    items_count INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_storefront_orders_user_id
    ON storefront_orders(user_id, amazon_order_id);
"""


# Adds per-user scoping to the user-owned tables without disturbing the shared
# `snapshots` data. Idempotent: safe to run on every startup. Existing rows keep
# user_id = NULL (owned by nobody, invisible to all tenants) until an admin
# claims them via claim_legacy_data(). The UNIQUE constraints move to composite
# (user_id, key) so two tenants can independently track the same ASIN / seller.
MULTITENANT_MIGRATION = """
ALTER TABLE validations        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE my_products        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE seller_credentials ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_validations_user ON validations(user_id);
CREATE INDEX IF NOT EXISTS idx_my_products_user ON my_products(user_id);
CREATE INDEX IF NOT EXISTS idx_seller_credentials_user ON seller_credentials(user_id);

ALTER TABLE my_products        DROP CONSTRAINT IF EXISTS my_products_asin_key;
ALTER TABLE seller_credentials DROP CONSTRAINT IF EXISTS seller_credentials_selling_partner_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_my_products_user_asin
    ON my_products(user_id, asin);
CREATE UNIQUE INDEX IF NOT EXISTS uq_seller_credentials_user_spid
    ON seller_credentials(user_id, selling_partner_id);
"""

# Google sign-in creates accounts with no password at all — Google has already
# verified the email, so there's nothing to hash. auth_provider is informational
# only (surfaced later if we ever need "you signed up with Google" messaging);
# login logic doesn't branch on it — a NULL password_hash already fails closed
# in auth.verify_password.
GOOGLE_AUTH_MIGRATION = """
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'password';
"""


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

STAGE5_SAAS_MIGRATION = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    actor_email TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    ip_address TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at);

CREATE TABLE IF NOT EXISTS org_members (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'Analyst',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_org_members_owner ON org_members(owner_id);
"""


@contextmanager
def get_conn():
    # NOTE: no connection-wide cursor_factory here on purpose — pandas.read_sql_query
    # expects plain tuple rows from cursor.fetchall(). A RealDictCursor default at the
    # connection level silently corrupts pandas' column/row mapping. Functions that want
    # dict-like rows ask for RealDictCursor explicitly on their own cursor instead.
    #
    # Connections are now drawn from the pool and returned after each use,
    # eliminating the 200-500ms TCP handshake cost on every API call.
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(MULTITENANT_MIGRATION)
            cur.execute(GOOGLE_AUTH_MIGRATION)
            cur.execute(WORKSPACE_MIGRATION)
            cur.execute(SYNC_JOBS_MIGRATION)
            cur.execute(STAGE5_SAAS_MIGRATION)


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


# --- Accounts -----------------------------------------------------------------
def get_user_by_email(email):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE lower(email) = lower(%s)", (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_id(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


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


def update_user_password(email, password_hash):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE lower(email) = lower(%s)",
                (password_hash, email),
            )
            return cur.rowcount > 0


# --- Email OTPs ---------------------------------------------------------------
def save_otp(email, code_hash, purpose, expires_at, payload=None):
    """Store a fresh OTP, clearing any prior ones for this email+purpose so only
    the newest code is ever valid."""
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM email_otps WHERE lower(email) = lower(%s) AND purpose = %s",
                (email, purpose),
            )
            cur.execute(
                """INSERT INTO email_otps (email, code_hash, purpose, payload, expires_at, attempts, created_at)
                   VALUES (lower(%s), %s, %s, %s, %s, 0, %s)""",
                (email, code_hash, purpose, payload, expires_at, datetime.now(timezone.utc).isoformat()),
            )


def get_active_otp(email, purpose):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM email_otps
                   WHERE lower(email) = lower(%s) AND purpose = %s
                   ORDER BY created_at DESC LIMIT 1""",
                (email, purpose),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def increment_otp_attempts(otp_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE email_otps SET attempts = attempts + 1 WHERE id = %s RETURNING attempts",
                (otp_id,),
            )
            r = cur.fetchone()
            return r[0] if r else 0


def delete_otps(email, purpose):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM email_otps WHERE lower(email) = lower(%s) AND purpose = %s",
                (email, purpose),
            )


def count_recent_otps(email, purpose, since_iso):
    """How many OTPs were issued for this email+purpose since a timestamp — for
    per-hour send throttling."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) FROM email_otps
                   WHERE lower(email) = lower(%s) AND purpose = %s AND created_at >= %s""",
                (email, purpose, since_iso),
            )
            return cur.fetchone()[0]


def insert_snapshot_rows(rows):
    """rows: list of dicts with keys matching the snapshots columns
    (except id). Returns number of rows inserted."""
    if not rows:
        return 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """INSERT INTO snapshots
                   (asin, category, list_type, rank, title, price, rating,
                    review_count, image_url, collected_at)
                   VALUES %s""",
                [
                    (
                        r["asin"], r["category"], r["list_type"], r["rank"],
                        r["title"], r["price"], r["rating"], r["review_count"],
                        r["image_url"], r["collected_at"],
                    )
                    for r in rows
                ],
            )
    return len(rows)


def _clean_title(row):
    # Some titles were collected before collector.py started decoding HTML
    # entities (e.g. "L&#x27;Oreal") — unescape on read so old rows display
    # clean too, not just newly-collected ones.
    if row and row.get("title"):
        row["title"] = html.unescape(row["title"])
    return row


def get_latest_snapshot(asin):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at DESC LIMIT 1",
                (asin,),
            )
            row = cur.fetchone()
            return _clean_title(dict(row)) if row else None


def get_history(asin):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at ASC",
                (asin,),
            )
            return [_clean_title(dict(r)) for r in cur.fetchall()]


def get_all_snapshots_df(days: int = 7):
    """Load snapshots for the last `days` calendar days.

    Capping at 7 days is more than enough for trend detection (new entrants
    need only the last run; movers need at least 2; cross-category just needs
    the latest snapshot per ASIN) while keeping the result set small and fast (< 1s).
    """
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query(
            # The ::timestamptz cast is a no-op now that the column is
            # timestamptz, and is kept only so this query still runs against a
            # database that predates the 2026-08-12 migration - there it is
            # required, or Postgres raises "operator does not exist: text >=
            # timestamp with time zone" and the whole digest 500s.
            # make_interval(days => %s) keeps the window count parameterised.
            """
            SELECT * FROM snapshots
            WHERE collected_at::timestamptz >= NOW() - make_interval(days => %s)
            ORDER BY collected_at ASC
            """,
            conn,
            params=(days,),
        )


def log_validation(asin, title, category, score, verdict, buy_price, notes, validated_at, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO validations
                   (asin, title, category, score, verdict, buy_price, notes, validated_at, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (asin, title, category, score, verdict, buy_price, notes, validated_at, user_id),
            )


def get_all_validations_df(user_id):
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM validations WHERE user_id = %s ORDER BY validated_at DESC", conn, params=(user_id,)
        )


def update_validation_notes(asin, notes, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE validations SET notes = %s WHERE asin = %s AND user_id = %s",
                (notes, asin, user_id),
            )


def query_snapshots(query_text=None, category=None, min_price=None, max_price=None, min_rank=None, max_rank=None, limit=100, offset=0):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = "SELECT DISTINCT ON (asin) * FROM snapshots WHERE 1=1"
            params = []
            if query_text:
                sql += " AND (asin ILIKE %s OR title ILIKE %s)"
                params.extend([f"%{query_text}%", f"%{query_text}%"])
            if category:
                sql += " AND category = %s"
                params.append(category)
            if min_price is not None:
                sql += " AND price >= %s"
                params.append(min_price)
            if max_price is not None:
                sql += " AND price <= %s"
                params.append(max_price)
            if min_rank is not None:
                sql += " AND rank >= %s"
                params.append(min_rank)
            if max_rank is not None:
                sql += " AND rank <= %s"
                params.append(max_rank)
            
            sql += " ORDER BY asin, collected_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(sql, tuple(params))
            return [_clean_title(dict(r)) for r in cur.fetchall()]


def count_snapshots(query_text=None, category=None, min_price=None, max_price=None, min_rank=None, max_rank=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            sql = "SELECT COUNT(DISTINCT asin) FROM snapshots WHERE 1=1"
            params = []
            if query_text:
                sql += " AND (asin ILIKE %s OR title ILIKE %s)"
                params.extend([f"%{query_text}%", f"%{query_text}%"])
            if category:
                sql += " AND category = %s"
                params.append(category)
            if min_price is not None:
                sql += " AND price >= %s"
                params.append(min_price)
            if max_price is not None:
                sql += " AND price <= %s"
                params.append(max_price)
            if min_rank is not None:
                sql += " AND rank >= %s"
                params.append(min_rank)
            if max_rank is not None:
                sql += " AND rank <= %s"
                params.append(max_rank)
            
            cur.execute(sql, tuple(params))
            return cur.fetchone()[0]


def get_my_products(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM my_products WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return [dict(r) for r in cur.fetchall()]


def save_my_product(asin, user_id, title=None, sku=None, supplier_cost=0.0, shipping_fee=0.0, target_margin=30.0, supplier_details="", current_stock=100, lead_time_days=14):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO my_products
                   (asin, user_id, title, sku, supplier_cost, shipping_fee, target_margin, supplier_details, current_stock, lead_time_days, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, asin) DO UPDATE SET
                       title = EXCLUDED.title,
                       sku = EXCLUDED.sku,
                       supplier_cost = EXCLUDED.supplier_cost,
                       shipping_fee = EXCLUDED.shipping_fee,
                       target_margin = EXCLUDED.target_margin,
                       supplier_details = EXCLUDED.supplier_details,
                       current_stock = EXCLUDED.current_stock,
                       lead_time_days = EXCLUDED.lead_time_days""",
                (asin, user_id, title, sku, supplier_cost, shipping_fee, target_margin, supplier_details, current_stock, lead_time_days, datetime.now(timezone.utc).isoformat()),
            )


def delete_my_product(asin, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM my_products WHERE asin = %s AND user_id = %s", (asin, user_id))


def save_seller_credentials(selling_partner_id, refresh_token, user_id, marketplace_id='A21TJRUUN4KGV'):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO seller_credentials
                   (selling_partner_id, refresh_token, marketplace_id, connected_at, user_id)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, selling_partner_id) DO UPDATE SET
                       refresh_token = EXCLUDED.refresh_token,
                       marketplace_id = EXCLUDED.marketplace_id,
                       connected_at = EXCLUDED.connected_at""",
                (selling_partner_id, _encrypt_token(refresh_token), marketplace_id, datetime.now(timezone.utc).isoformat(), user_id),
            )


def get_seller_credentials(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM seller_credentials WHERE user_id = %s ORDER BY connected_at DESC", (user_id,))
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["refresh_token"] = _decrypt_token(r.get("refresh_token"))
            return rows


def delete_seller_credentials(selling_partner_id, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM seller_credentials WHERE selling_partner_id = %s AND user_id = %s",
                (selling_partner_id, user_id),
            )


def get_user_ids_with_credentials():
    """Distinct user_ids that have at least one connected Amazon seller account.
    Used by the daily /storefront/sync-all job to refresh every seller."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT user_id FROM seller_credentials WHERE user_id IS NOT NULL")
            return [r[0] for r in cur.fetchall()]


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


def get_watchlist_with_latest_snapshots(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT v.*, s.price, s.review_count
                   FROM validations v
                   LEFT JOIN (
                       SELECT DISTINCT ON (asin) asin, price, review_count
                       FROM snapshots
                       ORDER BY asin, collected_at DESC
                   ) s ON v.asin = s.asin
                   WHERE v.user_id = %s
                   ORDER BY v.validated_at DESC""",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]


def get_snapshots_for_asins(asins):
    if not asins:
        return []
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM snapshots WHERE asin IN %s ORDER BY collected_at ASC",
                (tuple(asins),)
            )
            return [dict(r) for r in cur.fetchall()]


def get_latest_runs_by_category_list_type():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, list_type, MAX(collected_at) FROM snapshots GROUP BY category, list_type"
            )
            return {(row[0], row[1]): row[2] for row in cur.fetchall()}


def get_drawer_data(asin, user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Latest snapshot (global market data — not user-scoped)
            cur.execute("SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at DESC LIMIT 1", (asin,))
            snap = cur.fetchone()
            if snap:
                snap = dict(snap)
                if snap.get("title"):
                    snap["title"] = html.unescape(snap["title"])

            # 2. History: the newest snapshot of each of the last 7 DAYS.
            #
            # This was "ORDER BY collected_at DESC LIMIT 7", i.e. the last 7 rows.
            # That was the same thing back when every ASIN was captured once a
            # night, but the laptop's Maxun robots now refresh four categories
            # hourly, so the last 7 rows of a grocery ASIN are the last 7 *hours*
            # and the drawer chart drew a flat line across one afternoon. Measured
            # on 2026-08-12: 40% of the 9,191 ASINs had a chart spanning <= 2 days.
            #
            # The day key is an explicit UTC date, not substr() of the text form:
            # once collected_at is timestamptz its ::text rendering follows the
            # session TimeZone, which would silently regroup the chart per client.
            # The ::timestamptz cast is a no-op on the migrated column and parses
            # the ISO strings on a pre-migration database.
            #
            # DISTINCT ON needs its leading ORDER BY to match the distinct key, so
            # the per-day pick and the final chronological sort are separate steps.
            cur.execute(
                """
                SELECT * FROM (
                    SELECT DISTINCT ON ((collected_at::timestamptz AT TIME ZONE 'UTC')::date) *
                    FROM snapshots WHERE asin = %s
                    ORDER BY (collected_at::timestamptz AT TIME ZONE 'UTC')::date DESC,
                             collected_at DESC
                    LIMIT 7
                ) d ORDER BY collected_at ASC
                """,
                (asin,),
            )
            history = [dict(r) for r in cur.fetchall()]

            # 3. This user's validation matching this ASIN
            cur.execute("SELECT * FROM validations WHERE asin = %s AND user_id = %s LIMIT 1", (asin, user_id))
            val = cur.fetchone()
            if val:
                val = dict(val)

            # 4. This user's My Product matching this ASIN
            cur.execute("SELECT * FROM my_products WHERE asin = %s AND user_id = %s LIMIT 1", (asin, user_id))
            my_prod = cur.fetchone()
            if my_prod:
                my_prod = dict(my_prod)

            return snap, history, val, my_prod


def claim_legacy_data(user_id):
    """Assign all un-owned rows (user_id IS NULL — created before multi-tenancy)
    to `user_id`. Run once for the original owner after they create an account so
    their historical research, saved products, and seller credentials are visible
    to them again. Idempotent — a table with no NULL rows is simply a no-op.
    Returns a count per table."""
    counts = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            for table in ("validations", "my_products", "seller_credentials"):
                cur.execute(f"UPDATE {table} SET user_id = %s WHERE user_id IS NULL", (user_id,))
                counts[table] = cur.rowcount
    return counts


# --- Storefront Sync ----------------------------------------------------------
def save_storefront_sales_metric(user_id, selling_partner_id, marketplace_id, interval_start, order_count, unit_count, total_sales_amount, currency, workspace_id=None):
    """Persist one sales-metric interval.

    workspace_id must be written here. The workspace migration added the column
    as nullable so the ALTER could run against live data, but this INSERT was
    never updated to populate it -- so every sync since then wrote a row with a
    NULL workspace. Nothing broke visibly because the read path still filters on
    user_id alone, but those rows would silently vanish the moment any query
    scopes by workspace. Defaults to the user's own workspace when not passed.
    """
    from datetime import datetime, timezone
    if workspace_id is None:
        workspace_id = get_workspace_id_for_user(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO storefront_sales_metrics
                   (user_id, workspace_id, selling_partner_id, marketplace_id, interval_start, order_count, unit_count, total_sales_amount, currency, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, selling_partner_id, marketplace_id, interval_start)
                   DO UPDATE SET
                       workspace_id = COALESCE(EXCLUDED.workspace_id, storefront_sales_metrics.workspace_id),
                       order_count = EXCLUDED.order_count,
                       unit_count = EXCLUDED.unit_count,
                       total_sales_amount = EXCLUDED.total_sales_amount,
                       currency = EXCLUDED.currency,
                       updated_at = EXCLUDED.updated_at""",
                (user_id, workspace_id, selling_partner_id, marketplace_id, interval_start, order_count, unit_count, total_sales_amount, currency, datetime.now(timezone.utc).isoformat())
            )


def get_storefront_sales_metrics(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM storefront_sales_metrics 
                   WHERE user_id = %s 
                   ORDER BY interval_start ASC""",
                (user_id,)
            )
            return [dict(r) for r in cur.fetchall()]


def save_storefront_order(user_id, amazon_order_id, purchase_date, order_status, amount, currency, items_count, workspace_id=None):
    """Persist one storefront order. Same workspace_id omission as
    save_storefront_sales_metric had -- harmless so far only because this table
    is still empty, so fix it before the first order sync populates it."""
    from datetime import datetime, timezone
    if workspace_id is None:
        workspace_id = get_workspace_id_for_user(user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO storefront_orders
                   (user_id, workspace_id, amazon_order_id, purchase_date, order_status, amount, currency, items_count, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id, amazon_order_id)
                   DO UPDATE SET
                       workspace_id = COALESCE(EXCLUDED.workspace_id, storefront_orders.workspace_id),
                       order_status = EXCLUDED.order_status,
                       amount = EXCLUDED.amount,
                       currency = EXCLUDED.currency,
                       items_count = EXCLUDED.items_count,
                       updated_at = EXCLUDED.updated_at""",
                (user_id, workspace_id, amazon_order_id, purchase_date, order_status, amount, currency, items_count, datetime.now(timezone.utc).isoformat())
            )


def get_storefront_orders(user_id, limit=20):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM storefront_orders 
                   WHERE user_id = %s 
                   ORDER BY purchase_date DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            return [dict(r) for r in cur.fetchall()]


# --- Stage 5 SaaS Audit Logs & Team Members ---------------------------------

def log_audit_event(user_id, actor_email, action, target, ip_address=None):
    """Append one audit row. Callers must derive actor_email and ip_address
    server-side — never from request bodies. ip_address stays NULL when the real
    client address isn't known, rather than recording a placeholder that would
    read as fact."""
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO audit_logs (user_id, actor_email, action, target, ip_address, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, actor_email, action, target, ip_address, datetime.now(timezone.utc).isoformat())
            )


def get_audit_logs(user_id, limit=50):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM audit_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT %s""",
                (user_id, limit)
            )
            return [dict(r) for r in cur.fetchall()]


def add_org_member(owner_id, email, name=None, role="Analyst"):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO org_members (owner_id, email, name, role, status, created_at)
                   VALUES (%s, %s, %s, %s, 'active', %s)""",
                (owner_id, email, name, role, datetime.now(timezone.utc).isoformat())
            )


def get_org_members(owner_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM org_members WHERE owner_id = %s ORDER BY created_at ASC""",
                (owner_id,)
            )
            return [dict(r) for r in cur.fetchall()]


# targets.txt on the VM, as of 2026-08-13. Only used to render "3 of 15" in the
# monitor, so drifting out of sync makes a label slightly wrong, nothing worse.
VM_TARGET_COUNT = 15


def pipeline_freshness():
    """When each writer last landed a row, for monitoring.

    There is no `source` column on snapshots, so the three writers are told
    apart by what only they produce:

      * nightly collector — the ONLY writer of most-gifted, most-wished-for and
        new-releases. The laptop robots do bestsellers exclusively, so these
        three list_types identify the collector unambiguously.
      * VM deep-tracker — the only writer of list_type 'watchlist'.
      * laptop Maxun — bestsellers in the four categories it runs. This one
        overlaps with the collector, which also covers those categories, so its
        row count is a lower bound and its freshness is advisory only. It is
        expected to be stale for most of the day: the laptop runs roughly an
        hour a day by design, and nothing may depend on it being on.

    Returned as hours, computed in SQL against now(), so the answer does not
    depend on the caller's clock.
    """
    sources = {
        "nightly_collector": "list_type IN ('most-gifted', 'most-wished-for', 'new-releases')",
        "vm_watchlist": "list_type = 'watchlist'",
        "laptop_maxun": ("list_type = 'bestsellers' AND category IN "
                         "('Home & Kitchen', 'Health & Personal Care', "
                         "'Beauty & Personal Care', 'Grocery & Gourmet Foods')"),
    }
    out = {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            for name, where in sources.items():
                cur.execute(
                    f"""SELECT max(collected_at),
                               EXTRACT(EPOCH FROM (now() - max(collected_at))) / 3600.0,
                               count(*)
                        FROM snapshots WHERE {where}"""      # noqa: S608 - constants above, no input
                )
                last, age_h, rows = cur.fetchone()
                out[name] = {
                    "last_seen": last.isoformat() if last else None,
                    "age_hours": round(float(age_h), 2) if age_h is not None else None,
                    "rows": rows,
                }

            # How many distinct ASINs the VM's most recent pass actually landed.
            #
            # Total row count says nothing about whether a run went well: the VM
            # scrapes 15 targets twice a day, and amazon.in blocks its datacenter
            # IP intermittently, so a pass can return anywhere from 15 down to 2.
            # Without this the only way to know a run went badly was to read
            # cron.log on the VM by hand, which is not monitoring.
            #
            # A "pass" is grouped by the half-hour it landed in: one pass writes
            # its rows over a few minutes, and the two daily passes are 12h
            # apart, so there is no chance of merging two of them.
            cur.execute(
                """SELECT count(DISTINCT asin) FROM snapshots
                   WHERE list_type = 'watchlist'
                     AND collected_at >= (SELECT max(collected_at) - interval '30 minutes'
                                          FROM snapshots WHERE list_type = 'watchlist')"""
            )
            got = cur.fetchone()[0]
            out["vm_watchlist"]["last_pass_asins"] = got
            out["vm_watchlist"]["targets"] = VM_TARGET_COUNT
    return out


if __name__ == "__main__":
    init_db()
    print("Initialized Supabase Postgres schema.")
