"""
Database migration for Master Attribute Registry.

Adds new columns to the snapshots table to support:
- Category hierarchy (category, subcategory, product_type)
- Data status tracking (data_status_json)
- Dynamic attribute storage (dynamic_attributes_json)
- Completeness scoring (completeness_score)

Run this once to migrate existing data.
"""

import os
import sys
from datetime import datetime, timezone

# Add scraper directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from psycopg2.extras import execute_values

from db import get_conn, DATABASE_URL


MIGRATION_SQL = """
-- Add new columns to snapshots table
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS subcategory TEXT;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS product_type TEXT;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS data_status_json JSONB;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS dynamic_attributes_json JSONB;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS completeness_score REAL;
ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS schema_version INTEGER DEFAULT 1;

-- Create index for faster querying by category hierarchy
CREATE INDEX IF NOT EXISTS idx_snapshots_category_hierarchy 
    ON snapshots(category, subcategory, product_type);

-- Create index for completeness filtering
CREATE INDEX IF NOT EXISTS idx_snapshots_completeness 
    ON snapshots(completeness_score) WHERE completeness_score IS NOT NULL;

-- Update existing rows with default values
UPDATE snapshots 
SET 
    schema_version = 1,
    data_status_json = '{"asin": "COLLECTED", "title": "COLLECTED"}'::jsonb
WHERE schema_version IS NULL;
"""

BACKWARD_COMPAT_SQL = """
-- Ensure backward compatibility: add any missing core columns
-- These may already exist from previous migrations

-- Add brand if missing (for older databases)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='snapshots' AND column_name='brand') THEN
        ALTER TABLE snapshots ADD COLUMN brand TEXT;
    END IF;
END $$;

-- Add size_tier_hint if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='snapshots' AND column_name='size_tier_hint') THEN
        ALTER TABLE snapshots ADD COLUMN size_tier_hint TEXT;
    END IF;
END $$;

-- Add product_type_hint if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='snapshots' AND column_name='product_type_hint') THEN
        ALTER TABLE snapshots ADD COLUMN product_type_hint TEXT;
    END IF;
END $$;
"""


def run_migration():
    """Execute the migration."""
    print("[Migration] Starting database migration...")
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Run backward compatibility first
            print("[Migration] Running backward compatibility checks...")
            cur.execute(BACKWARD_COMPAT_SQL)
            
            # Run main migration
            print("[Migration] Applying new columns...")
            cur.execute(MIGRATION_SQL)
            
            # Verify migration
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'snapshots' 
                AND column_name IN (
                    'subcategory', 'product_type', 
                    'data_status_json', 'dynamic_attributes_json',
                    'completeness_score', 'schema_version'
                )
                ORDER BY column_name
            """)
            
            columns = cur.fetchall()
            print(f"[Migration] Verified {len(columns)} new columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name} ({col_type})")
            
            # Count total rows
            cur.execute("SELECT COUNT(*) FROM snapshots")
            total_rows = cur.fetchone()[0]
            print(f"[Migration] Total rows in snapshots: {total_rows:,}")
    
    print("[Migration] Migration complete!")
    return True


def test_migration():
    """Test migration on a sample ASIN."""
    print("\n[Test] Testing migration with sample data...")
    
    # Find a sample ASIN
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT asin, title, category, collected_at 
                FROM snapshots 
                ORDER BY collected_at DESC 
                LIMIT 1
            """)
            row = cur.fetchone()
            
            if not row:
                print("[Test] No snapshots found. Migration test skipped.")
                return False
            
            asin, title, category, collected_at = row
            print(f"[Test] Sample ASIN: {asin}")
            print(f"[Test] Category: {category}")
    
    # Test inserting with new fields
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO snapshots 
                (asin, category, list_type, rank, title, price, rating, 
                 review_count, image_url, collected_at, brand, size_tier_hint, 
                 product_type_hint, subcategory, product_type, 
                 data_status_json, schema_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                ON CONFLICT DO NOTHING
            """, (
                "B0TEST0001",  # Test ASIN
                "Electronics > Headphones",
                "bestsellers",
                1,
                "Test Product Title",
                1999.0,
                4.5,
                100,
                "https://example.com/image.jpg",
                datetime.now(timezone.utc).isoformat(),
                "TestBrand",
                None,
                "over_ear",
                "Headphones",
                "over_ear",
                '{"asin": "COLLECTED", "title": "COLLECTED", "brand": "COLLECTED"}'
            ))
            conn.commit()
            
            # Verify insert
            cur.execute("SELECT asin, subcategory, product_type FROM snapshots WHERE asin = 'B0TEST0001'")
            result = cur.fetchone()
            
            if result:
                print(f"[Test] Insert verified: asin={result[0]}, subcategory={result[1]}, product_type={result[2]}")
                print("[Test] Migration test PASSED")
                return True
            else:
                print("[Test] Migration test FAILED")
                return False


if __name__ == "__main__":
    if "DATABASE_URL" not in os.environ:
        print("ERROR: DATABASE_URL environment variable required")
        sys.exit(1)
    
    test_first = "--test" in sys.argv
    
    if test_first:
        if test_migration():
            run_migration()
        else:
            print("Test failed. Migration aborted.")
            sys.exit(1)
    else:
        run_migration()
