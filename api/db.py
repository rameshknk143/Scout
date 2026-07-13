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

# Encrypts Amazon SP-API refresh tokens at rest so a DATABASE_URL leak alone
# doesn't hand over seller-account access. Key lives only in the API server's
# env (Render), never in the DB or repo. Generate one with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# If unset, tokens are stored as before (plaintext) so nothing breaks — but set it.
TOKEN_ENCRYPTION_KEY = os.environ.get("TOKEN_ENCRYPTION_KEY")
_fernet = Fernet(TOKEN_ENCRYPTION_KEY.encode()) if TOKEN_ENCRYPTION_KEY else None


def _encrypt_token(value):
    if _fernet and value:
        return _fernet.encrypt(value.encode()).decode()
    return value


def _decrypt_token(value):
    if _fernet and value:
        try:
            return _fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            return value  # legacy row saved before encryption was enabled
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


if __name__ == "__main__":
    init_db()
    print("Initialized Supabase Postgres schema.")
