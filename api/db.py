"""
Scout's database layer — Postgres (Supabase) version.

Same table shapes and the same function signatures as the original local
SQLite db.py, so collector.py / scorer.py / trend_radar.py don't need their
own logic touched, only this import. Connection string comes from the
DATABASE_URL environment variable (Supabase gives you this directly).
"""

import html
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from cryptography.fernet import Fernet, InvalidToken

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
    collected_at TEXT NOT NULL
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


@contextmanager
def get_conn():
    # NOTE: no connection-wide cursor_factory here on purpose — pandas.read_sql_query
    # expects plain tuple rows from cursor.fetchall(). A RealDictCursor default at the
    # connection level silently corrupts pandas' column/row mapping. Functions that want
    # dict-like rows ask for RealDictCursor explicitly on their own cursor instead.
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(MULTITENANT_MIGRATION)


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


def create_user(email, password_hash, full_name, email_verified=True):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO users (email, password_hash, full_name, email_verified, created_at)
                   VALUES (lower(%s), %s, %s, %s, %s) RETURNING id, email, full_name, email_verified""",
                (email, password_hash, full_name, email_verified, datetime.now(timezone.utc).isoformat()),
            )
            return dict(cur.fetchone())


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


def get_all_snapshots_df():
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM snapshots", conn)


def log_validation(asin, title, category, score, verdict, buy_price, notes, validated_at):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO validations
                   (asin, title, category, score, verdict, buy_price, notes, validated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (asin, title, category, score, verdict, buy_price, notes, validated_at),
            )


def get_all_validations_df():
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM validations ORDER BY validated_at DESC", conn
        )


def update_validation_notes(asin, notes):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE validations SET notes = %s WHERE asin = %s",
                (notes, asin),
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


def get_my_products():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM my_products ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]


def save_my_product(asin, title=None, sku=None, supplier_cost=0.0, shipping_fee=0.0, target_margin=30.0, supplier_details="", current_stock=100, lead_time_days=14):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO my_products
                   (asin, title, sku, supplier_cost, shipping_fee, target_margin, supplier_details, current_stock, lead_time_days, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (asin) DO UPDATE SET
                       title = EXCLUDED.title,
                       sku = EXCLUDED.sku,
                       supplier_cost = EXCLUDED.supplier_cost,
                       shipping_fee = EXCLUDED.shipping_fee,
                       target_margin = EXCLUDED.target_margin,
                       supplier_details = EXCLUDED.supplier_details,
                       current_stock = EXCLUDED.current_stock,
                       lead_time_days = EXCLUDED.lead_time_days""",
                (asin, title, sku, supplier_cost, shipping_fee, target_margin, supplier_details, current_stock, lead_time_days, datetime.now(timezone.utc).isoformat()),
            )


def delete_my_product(asin):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM my_products WHERE asin = %s", (asin,))


def save_seller_credentials(selling_partner_id, refresh_token, marketplace_id='A21TJRUUN4KGV'):
    from datetime import datetime, timezone
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO seller_credentials
                   (selling_partner_id, refresh_token, marketplace_id, connected_at)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (selling_partner_id) DO UPDATE SET
                       refresh_token = EXCLUDED.refresh_token,
                       marketplace_id = EXCLUDED.marketplace_id,
                       connected_at = EXCLUDED.connected_at""",
                (selling_partner_id, _encrypt_token(refresh_token), marketplace_id, datetime.now(timezone.utc).isoformat()),
            )


def get_seller_credentials():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM seller_credentials ORDER BY connected_at DESC")
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["refresh_token"] = _decrypt_token(r.get("refresh_token"))
            return rows


def delete_seller_credentials(selling_partner_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM seller_credentials WHERE selling_partner_id = %s",
                (selling_partner_id,),
            )


def get_watchlist_with_latest_snapshots():
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
                   ORDER BY v.validated_at DESC"""
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


def get_drawer_data(asin):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Latest snapshot
            cur.execute("SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at DESC LIMIT 1", (asin,))
            snap = cur.fetchone()
            if snap:
                snap = dict(snap)
                if snap.get("title"):
                    snap["title"] = html.unescape(snap["title"])

            # 2. History (last 7)
            cur.execute("SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at DESC LIMIT 7", (asin,))
            history = [dict(r) for r in cur.fetchall()]
            history.reverse()

            # 3. Validation matching this ASIN
            cur.execute("SELECT * FROM validations WHERE asin = %s LIMIT 1", (asin,))
            val = cur.fetchone()
            if val:
                val = dict(val)

            # 4. My Product matching this ASIN
            cur.execute("SELECT * FROM my_products WHERE asin = %s LIMIT 1", (asin,))
            my_prod = cur.fetchone()
            if my_prod:
                my_prod = dict(my_prod)

            return snap, history, val, my_prod


if __name__ == "__main__":
    init_db()
    print("Initialized Supabase Postgres schema.")
