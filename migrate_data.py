"""
One-off migration: copy every row from the local laptop SQLite database
(scout/data/scout.db) into the new Supabase Postgres database.

Run this once, locally, after the Supabase project exists and DATABASE_URL
is set. Safe to re-run — it upserts nothing, so re-running would duplicate
rows; only run it once per Supabase project.

Usage:
    DATABASE_URL="postgresql://..." python migrate_data.py
"""

import os
import sqlite3

import psycopg2
import psycopg2.extras

LOCAL_DB = os.path.join(
    os.path.dirname(__file__), "..", "scout", "data", "scout.db"
)


def read_local():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    snapshots = [dict(r) for r in conn.execute("SELECT * FROM snapshots")]
    validations = [dict(r) for r in conn.execute("SELECT * FROM validations")]
    conn.close()
    return snapshots, validations


def main():
    database_url = os.environ["DATABASE_URL"]
    snapshots, validations = read_local()
    print(f"Read {len(snapshots)} snapshot rows and {len(validations)} validation rows from {LOCAL_DB}")

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id SERIAL PRIMARY KEY, asin TEXT NOT NULL, category TEXT NOT NULL,
            list_type TEXT NOT NULL, rank INTEGER, title TEXT, price REAL,
            rating REAL, review_count INTEGER, image_url TEXT, collected_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS validations (
            id SERIAL PRIMARY KEY, asin TEXT NOT NULL, title TEXT, category TEXT,
            score REAL, verdict TEXT, buy_price REAL, notes TEXT, validated_at TEXT NOT NULL
        );
    """)

    if snapshots:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO snapshots
               (asin, category, list_type, rank, title, price, rating, review_count, image_url, collected_at)
               VALUES %s""",
            [(r["asin"], r["category"], r["list_type"], r["rank"], r["title"], r["price"],
              r["rating"], r["review_count"], r["image_url"], r["collected_at"]) for r in snapshots],
        )

    if validations:
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO validations
               (asin, title, category, score, verdict, buy_price, notes, validated_at)
               VALUES %s""",
            [(r["asin"], r["title"], r["category"], r["score"], r["verdict"],
              r["buy_price"], r["notes"], r["validated_at"]) for r in validations],
        )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM snapshots")
    snap_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM validations")
    val_count = cur.fetchone()[0]
    print(f"Supabase now has {snap_count} snapshot rows and {val_count} validation rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
