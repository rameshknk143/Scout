"""
R2 self-test (2026-08-31): prove insert_snapshot_rows is idempotent.

Runs the REAL insert function from BOTH db.py copies (api/ = Render ingest,
scraper/ = GitHub collector) against the production Supabase database with a
fake ASIN and a sentinel list_type:
  insert #1 -> must return 1 (row lands)
  insert #2 -> must return 0 (unique index + ON CONFLICT swallows it)
then deletes the test row so the database is left exactly as it was.

Run:  uv run --with psycopg2-binary python scripts/r2_selftest.py
Reads DATABASE_URL from scout-cloud/.env. Never prints the URL.
"""

import importlib.util
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")

TEST_ASIN = "B0R2SELFXX"  # 10 chars, fails ASIN_RE only in shape — ingest is not used here
TEST_CATEGORY = "R2 Selftest"
TEST_LIST_TYPE = "r2-selftest"


def load_database_url():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("DATABASE_URL not found in .env")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_rows():
    ts = datetime.now(timezone.utc).isoformat()
    return [{
        "asin": TEST_ASIN, "category": TEST_CATEGORY, "list_type": TEST_LIST_TYPE,
        "rank": 1, "title": "R2 self-test row (safe to delete)",
        "price": 1.0, "rating": 5.0, "review_count": 1,
        "image_url": None, "collected_at": ts,
    }], ts


def cleanup(url, ts):
    import psycopg2
    conn = psycopg2.connect(url, connect_timeout=30)
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM snapshots WHERE asin = %s AND list_type = %s AND collected_at = %s",
            (TEST_ASIN, TEST_LIST_TYPE, ts),
        )
        deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def test_module(db, label):
    rows, ts = make_rows()
    first = db.insert_snapshot_rows(rows)
    second = db.insert_snapshot_rows(rows)
    print(f"{label}: insert#1={first} (expect 1), insert#2={second} (expect 0)")
    assert first == 1, f"{label}: first insert should land exactly 1 row, got {first}"
    assert second == 0, f"{label}: duplicate insert must be swallowed by ON CONFLICT, got {second}"
    return ts


def main():
    os.environ["DATABASE_URL"] = load_database_url()
    url = os.environ["DATABASE_URL"]

    # defensive pre-clean: remove any leftovers from an earlier aborted run
    import psycopg2
    conn = psycopg2.connect(url, connect_timeout=30)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM snapshots WHERE asin = %s AND list_type = %s",
                    (TEST_ASIN, TEST_LIST_TYPE))
        if cur.rowcount:
            print(f"pre-clean: removed {cur.rowcount} leftover test row(s)")
    conn.commit()
    conn.close()

    api_db = load_module(os.path.join(ROOT, "api", "db.py"), "r2_api_db")
    ts1 = test_module(api_db, "api/db.py     (Render ingest)")

    scraper_db = load_module(os.path.join(ROOT, "scraper", "db.py"), "r2_scraper_db")
    ts2 = test_module(scraper_db, "scraper/db.py  (GH collector)")

    d1 = cleanup(url, ts1)
    d2 = cleanup(url, ts2)
    print(f"cleanup: deleted {d1}+{d2} test rows (expect 2)")

    leftovers = 0
    import psycopg2
    conn = psycopg2.connect(url, connect_timeout=30)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM snapshots WHERE asin = %s AND list_type = %s",
            (TEST_ASIN, TEST_LIST_TYPE),
        )
        leftovers = cur.fetchone()[0]
    conn.close()

    assert leftovers == 0, f"test rows left behind: {leftovers}"
    print("ALL PASS: both insert paths are idempotent; DB left clean")


if __name__ == "__main__":
    main()
