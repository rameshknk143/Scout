"""
R2 (2026-08-31): make snapshot inserts idempotent.

1. Backs up snapshots -> snapshots_backup_20260831
2. Deletes exact-duplicate rows (same asin+category+list_type+collected_at,
   keeps the lowest id in each group)
3. Creates UNIQUE INDEX uq_snapshots_row ON snapshots(asin, category,
   list_type, collected_at) -- the constraint that ON CONFLICT DO NOTHING in
   api/db.py and scraper/db.py relies on.

Run:  uv run --with psycopg2-binary python scripts/r2_snapshots_unique_index.py
Reads DATABASE_URL from scout-cloud/.env. Never prints the URL.
"""

import os
import sys

import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")


def load_database_url():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
                if url:
                    return url
    sys.exit("DATABASE_URL not found in .env")


def count(cur, sql):
    cur.execute(sql)
    return cur.fetchone()[0]


def main():
    url = load_database_url()
    conn = psycopg2.connect(url, connect_timeout=30)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            before = count(cur, "SELECT COUNT(*) FROM snapshots")
            print(f"total rows before: {before}")

            # 1. backup (idempotent)
            cur.execute(
                "CREATE TABLE IF NOT EXISTS snapshots_backup_20260831 "
                "AS SELECT * FROM snapshots"
            )
            print("backup table: snapshots_backup_20260831 ready")

            # 2. how many duplicate groups / rows exist today?
            cur.execute(
                """SELECT COUNT(*), COALESCE(SUM(n)-COUNT(*), 0) FROM (
                     SELECT COUNT(*) AS n FROM snapshots
                     GROUP BY asin, category, list_type, collected_at
                     HAVING COUNT(*) > 1) g"""
            )
            groups, excess = cur.fetchone()
            print(f"duplicate groups: {groups}, excess rows: {excess}")

            if excess:
                cur.execute(
                    """DELETE FROM snapshots a
                       USING snapshots b
                       WHERE a.id > b.id
                         AND a.asin = b.asin
                         AND a.category = b.category
                         AND a.list_type = b.list_type
                         AND a.collected_at = b.collected_at"""
                )
                print(f"deleted duplicate rows: {cur.rowcount}")
            else:
                print("no duplicates found - nothing deleted")

            # 3. the unique index (idempotent)
            cur.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshots_row
                   ON snapshots (asin, category, list_type, collected_at)"""
            )
            print("unique index: uq_snapshots_row created/verified")

            after = count(cur, "SELECT COUNT(*) FROM snapshots")
            idx = count(
                cur,
                """SELECT COUNT(*) FROM pg_indexes
                   WHERE indexname = 'uq_snapshots_row'""",
            )
            conn.commit()
            print(f"total rows after: {after} (removed {before - after})")
            print(f"index present: {idx == 1}")
            print("COMMITTED")
    except Exception as e:
        conn.rollback()
        print(f"ROLLED BACK - error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
