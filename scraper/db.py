"""
Scout's database layer — Postgres (Supabase) version.

Same table shapes and the same function signatures as the original local
SQLite db.py, so collector.py / scorer.py / trend_radar.py don't need their
own logic touched, only this import. Connection string comes from the
DATABASE_URL environment variable (Supabase gives you this directly).
"""

import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id SERIAL PRIMARY KEY,
    asin TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    product_type TEXT,
    list_type TEXT NOT NULL,
    rank INTEGER,
    title TEXT,
    price REAL,
    rating REAL,
    review_count INTEGER,
    image_url TEXT,
    collected_at TIMESTAMPTZ NOT NULL,
    brand TEXT,
    size_tier_hint TEXT,
    product_type_hint TEXT
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
    (except id). Returns number of rows actually inserted.

    ON CONFLICT DO NOTHING pairs with the uq_snapshots_row unique index
    (asin, category, list_type, collected_at): a replayed push --all, a
    retried ingest, or any double-delivery now inserts 0 instead of
    duplicating history. execute_values(fetch=True) returns the exact
    accumulated inserted-row list across pages (cur.rowcount would only
    reflect the last page; psycopg2 paginates at 100 rows)."""
    if not rows:
        return 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            inserted = psycopg2.extras.execute_values(
                cur,
                """INSERT INTO snapshots
                   (asin, category, list_type, rank, title, price, rating,
                    review_count, image_url, collected_at, brand, size_tier_hint, product_type_hint,
                    subcategory, product_type, source)
                   VALUES %s ON CONFLICT DO NOTHING RETURNING id""",
                [
                    (
                        r["asin"], r["category"], r["list_type"], r["rank"],
                        r["title"], r["price"], r["rating"], r["review_count"],
                        r["image_url"], r["collected_at"],
                        r.get("brand"), r.get("size_tier_hint"), r.get("product_type_hint"),
                        r.get("subcategory"), r.get("product_type"),
                        r.get("source", "collector"),
                    )
                    for r in rows
                ],
                fetch=True,
            )
            return len(inserted)


def get_latest_snapshot(asin):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at DESC LIMIT 1",
                (asin,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def get_history(asin):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM snapshots WHERE asin = %s ORDER BY collected_at ASC",
                (asin,),
            )
            return [dict(r) for r in cur.fetchall()]


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


def upsert_enrichment(data: dict) -> int:
    """Update enriched fields for the latest snapshot of an ASIN.
    
    Returns 1 if updated, 0 if no matching row found.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE snapshots SET
                    title = COALESCE(%s, title),
                    brand = COALESCE(%s, brand),
                    price = COALESCE(%s, price),
                    rating = COALESCE(%s, rating),
                    review_count = COALESCE(%s, review_count),
                    subcategory = COALESCE(%s, subcategory),
                    product_type = COALESCE(%s, product_type),
                    in_stock = COALESCE(%s, in_stock),
                    availability_text = COALESCE(%s, availability_text),
                    seller = COALESCE(%s, seller),
                    fulfillment = COALESCE(%s, fulfillment),
                    dimensions = COALESCE(%s, dimensions),
                    weight = COALESCE(%s, weight),
                    material = COALESCE(%s, material),
                    warranty = COALESCE(%s, warranty),
                    ram = COALESCE(%s, ram),
                    storage = COALESCE(%s, storage),
                    processor = COALESCE(%s, processor),
                    display_size = COALESCE(%s, display_size),
                    battery_capacity = COALESCE(%s, battery_capacity),
                    fabric = COALESCE(%s, fabric),
                    net_weight = COALESCE(%s, net_weight),
                    ingredients = COALESCE(%s, ingredients)
                WHERE asin = %s
                  AND collected_at = (
                      SELECT MAX(collected_at) FROM snapshots s2
                      WHERE s2.asin = %s
                  )
            """, (
                data.get("title"),
                data.get("brand"),
                data.get("price"),
                data.get("rating"),
                data.get("review_count"),
                data.get("subcategory"),
                data.get("product_type"),
                data.get("in_stock"),
                data.get("availability_text"),
                data.get("seller"),
                data.get("fulfillment"),
                data.get("dimensions"),
                data.get("weight"),
                data.get("material"),
                data.get("warranty"),
                data.get("ram"),
                data.get("storage"),
                data.get("processor"),
                data.get("display_size"),
                data.get("battery_capacity"),
                data.get("fabric"),
                data.get("net_weight"),
                data.get("ingredients"),
                data["asin"],
                data["asin"],
            ))
            affected = cur.rowcount
            conn.commit()
            return affected


if __name__ == "__main__":
    init_db()
    print("Initialized Supabase Postgres schema.")
