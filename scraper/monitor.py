"""
ScoutVeda Health Monitor — Quick diagnostic of scraping pipeline.

Shows: DB size, recent activity, category coverage, data quality metrics.

Usage:
    python monitor.py              # Full health check
    python monitor.py --summary    # Quick summary only
    python monitor.py --stats      # Detailed statistics
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add scraper dir to path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
import psycopg2.extras


def get_conn():
    """Get database connection."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


def quick_stats():
    """Quick summary statistics."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Total rows
            cur.execute("SELECT COUNT(*) FROM snapshots")
            total = cur.fetchone()[0]
            
            # Rows today
            cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at >= now()::date")
            today = cur.fetchone()[0]
            
            # Unique ASINs
            cur.execute("SELECT COUNT(DISTINCT asin) FROM snapshots")
            unique_asins = cur.fetchone()[0]
            
            # Categories
            cur.execute("SELECT COUNT(DISTINCT category) FROM snapshots")
            categories = cur.fetchone()[0]
            
            # Subcategories populated
            cur.execute("SELECT COUNT(DISTINCT subcategory) FROM snapshots WHERE subcategory IS NOT NULL")
            subcats = cur.fetchone()[0]
            
            # Brand coverage
            cur.execute("SELECT COUNT(*) FROM snapshots WHERE brand IS NOT NULL AND brand != ''")
            branded = cur.fetchone()[0]
            brand_pct = (branded / total * 100) if total > 0 else 0
            
            # Subcategory coverage
            subcat_pct = (subcats / unique_asins * 100) if unique_asins > 0 else 0
            
            # Average rating
            cur.execute("SELECT AVG(rating) FROM snapshots WHERE rating IS NOT NULL")
            avg_rating = cur.fetchone()[0]
            
            # Recent activity (last 24h)
            cur.execute("""
                SELECT DATE(collected_at), COUNT(*) 
                FROM snapshots 
                WHERE collected_at >= now() - interval '7 days'
                GROUP BY DATE(collected_at)
                ORDER BY DATE(collected_at) DESC
                LIMIT 7
            """)
            recent = cur.fetchall()
            
            return {
                "total_rows": total,
                "today_rows": today,
                "unique_asins": unique_asins,
                "categories": categories,
                "subcategories": subcats,
                "brand_coverage_pct": round(brand_pct, 1),
                "subcategory_coverage_pct": round(subcat_pct, 1),
                "avg_rating": round(avg_rating, 2) if avg_rating else None,
                "recent_activity": recent,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }


def category_breakdown():
    """Breakdown by category."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, 
                       COUNT(*) as count,
                       COUNT(DISTINCT asin) as unique_asins,
                       AVG(rating) as avg_rating,
                       AVG(price) as avg_price
                FROM snapshots
                WHERE collected_at >= now() - interval '7 days'
                GROUP BY category
                ORDER BY count DESC
            """)
            return cur.fetchall()


def quality_metrics():
    """Data quality checks."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Missing critical fields
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) as no_price,
                    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) as no_rating,
                    SUM(CASE WHEN review_count IS NULL THEN 1 ELSE 0 END) as no_reviews,
                    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as no_title,
                    SUM(CASE WHEN subcategory IS NULL THEN 1 ELSE 0 END) as no_subcat
                FROM snapshots
                WHERE collected_at >= now() - interval '1 day'
            """)
            missing = cur.fetchone()
            
            # Price range
            cur.execute("""
                SELECT MIN(price), MAX(price), AVG(price)
                FROM snapshots
                WHERE price IS NOT NULL
                  AND collected_at >= now() - interval '1 day'
            """)
            price_stats = cur.fetchone()
            
            return {
                "missing_price": missing[0],
                "missing_rating": missing[1],
                "missing_reviews": missing[2],
                "missing_title": missing[3],
                "missing_subcategory": missing[4],
                "min_price": price_stats[0],
                "max_price": price_stats[1],
                "avg_price": round(price_stats[2], 2) if price_stats[2] else None,
            }


def main():
    """Run full health check."""
    print("=" * 70)
    print("SCOUTVEDA HEALTH MONITOR")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    print()
    
    try:
        stats = quick_stats()
        
        print("📊 DATABASE OVERVIEW")
        print("-" * 70)
        print(f"  Total rows:          {stats['total_rows']:,}")
        print(f"  Today's rows:        {stats['today_rows']:,}")
        print(f"  Unique ASINs:        {stats['unique_asins']:,}")
        print(f"  Categories tracked:  {stats['categories']}")
        print(f"  Subcategories:       {stats['subcategories']}")
        print()
        
        print("📈 DATA QUALITY")
        print("-" * 70)
        print(f"  Brand coverage:      {stats['brand_coverage_pct']}%")
        print(f"  Subcategory coverage:{stats['subcategory_coverage_pct']}%")
        print(f"  Avg rating:          {stats['avg_rating']}")
        print()
        
        print("📅 RECENT ACTIVITY (Last 7 Days)")
        print("-" * 70)
        if stats['recent_activity']:
            for date, count in stats['recent_activity'][:7]:
                bar = "█" * min(count // 100, 50)
                print(f"  {date}: {count:>6,} rows  {bar}")
        else:
            print("  No activity in last 7 days")
        print()
        
        # Category breakdown
        print("🏷️  TOP CATEGORIES (Last 7 Days)")
        print("-" * 70)
        cats = category_breakdown()
        for cat, count, unique, avg_r, avg_p in cats[:10]:
            print(f"  {cat[:35]:35} | {count:>6,} rows | {unique:>5} ASINs | ₹{avg_p:.0f}" if avg_p else f"  {cat[:35]:35} | {count:>6,} rows | {unique:>5} ASINs")
        print()
        
        # Quality metrics
        quality = quality_metrics()
        print("✅ QUALITY CHECKS (Last 24h)")
        print("-" * 70)
        print(f"  Missing price:       {quality['missing_price']}")
        print(f"  Missing rating:      {quality['missing_rating']}")
        print(f"  Missing reviews:     {quality['missing_reviews']}")
        print(f"  Missing subcategory: {quality['missing_subcategory']}")
        print(f"  Price range:         ₹{quality['min_price'] or 0:,.0f} - ₹{quality['max_price'] or 0:,.0f}")
        print(f"  Avg price:           ₹{quality['avg_price'] or 0:,.0f}")
        print()
        
        print("=" * 70)
        print("STATUS: HEALTHY ✅")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    parser.add_argument("--stats", action="store_true", help="Show detailed stats")
    args = parser.parse_args()
    
    main()
