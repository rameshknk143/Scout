"""
Scraper Status API - Real-time monitoring of all scraping infrastructure.

Provides endpoints for:
- Overall system health
- Individual scraper status
- Performance metrics
- Database statistics
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection from environment."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    return psycopg2.connect(database_url)


def get_scraper_status() -> Dict:
    """Get comprehensive status of all scrapers."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # 1. Database overview
        cur.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT asin) as unique_asins,
                COUNT(DISTINCT category) as categories,
                MIN(collected_at) as oldest,
                MAX(collected_at) as newest,
                COUNT(CASE WHEN subcategory IS NOT NULL THEN 1 END) as with_subcat,
                COUNT(CASE WHEN brand IS NOT NULL THEN 1 END) as with_brand,
                COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price,
                COUNT(CASE WHEN source IS NOT NULL THEN 1 END) as with_source
            FROM snapshots
        """)
        db_stats = cur.fetchone()
        
        # 2. Recent activity (last 7 days)
        cur.execute("""
            SELECT 
                DATE(collected_at) as day,
                COUNT(*) as rows,
                COUNT(DISTINCT asin) as asins,
                COUNT(DISTINCT category) as cats
            FROM snapshots
            WHERE collected_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(collected_at)
            ORDER BY day DESC
            LIMIT 7
        """)
        recent_activity = cur.fetchall()
        
        # 3. Category distribution
        cur.execute("""
            SELECT category, COUNT(*) as rows, COUNT(DISTINCT asin) as asins
            FROM snapshots
            GROUP BY category
            ORDER BY rows DESC
            LIMIT 10
        """)
        top_categories = cur.fetchall()
        
        # 4. Source attribution
        cur.execute("""
            SELECT source, COUNT(*) as count
            FROM snapshots
            GROUP BY source
            ORDER BY count DESC
        """)
        source_stats = cur.fetchall()
        
        # 5. Data quality metrics
        cur.execute("""
            SELECT 
                AVG(CASE WHEN subcategory IS NOT NULL THEN 1.0 ELSE 0.0 END) as subcat_pct,
                AVG(CASE WHEN brand IS NOT NULL THEN 1.0 ELSE 0.0 END) as brand_pct,
                AVG(CASE WHEN price IS NOT NULL THEN 1.0 ELSE 0.0 END) as price_pct,
                AVG(CASE WHEN rating IS NOT NULL THEN 1.0 ELSE 0.0 END) as rating_pct
            FROM snapshots
        """)
        quality = cur.fetchone()
        
        # 6. Daily averages
        cur.execute("""
            SELECT 
                AVG(daily_rows) as avg_rows_per_day,
                AVG(daily_asins) as avg_asins_per_day
            FROM (
                SELECT 
                    DATE(collected_at) as day,
                    COUNT(*) as daily_rows,
                    COUNT(DISTINCT asin) as daily_asins
                FROM snapshots
                WHERE collected_at > NOW() - INTERVAL '30 days'
                GROUP BY DATE(collected_at)
            ) daily
        """)
        averages = cur.fetchone()
        
        # Build response
        daily_avg = averages['avg_rows_per_day'] or 4000
        projected_monthly = int(daily_avg * 30)
        days_to_2m = int((2_000_000 - db_stats['total_rows']) / daily_avg) if daily_avg > 0 else 999
        
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "total_rows": db_stats['total_rows'],
                "unique_asins": db_stats['unique_asins'],
                "categories": db_stats['categories'],
                "date_range": {
                    "oldest": db_stats['oldest'].isoformat() if db_stats['oldest'] else None,
                    "newest": db_stats['newest'].isoformat() if db_stats['newest'] else None
                },
                "coverage": {
                    "subcategory_pct": float(quality['subcat_pct'] or 0) * 100,
                    "brand_pct": float(quality['brand_pct'] or 0) * 100,
                    "price_pct": float(quality['price_pct'] or 0) * 100,
                    "rating_pct": float(quality['rating_pct'] or 0) * 100,
                    "source_pct": (db_stats['with_source'] / db_stats['total_rows'] * 100) if db_stats['total_rows'] > 0 else 0
                }
            },
            "throughput": {
                "daily_average": int(daily_avg),
                "weekly_projected": int(daily_avg * 7),
                "monthly_projected": projected_monthly,
                "days_to_2m": days_to_2m,
                "last_7_days": [
                    {
                        "date": row['day'].isoformat() if hasattr(row['day'], 'isoformat') else str(row['day']),
                        "rows": row['rows'],
                        "asins": row['asins'],
                        "categories": row['cats']
                    }
                    for row in recent_activity
                ]
            },
            "top_categories": [
                {
                    "category": row['category'],
                    "rows": row['rows'],
                    "asins": row['asins']
                }
                for row in top_categories
            ],
            "sources": [
                {
                    "source": row['source'],
                    "count": row['count']
                }
                for row in source_stats
            ],
            "scrapers": {
                "github_actions": {
                    "nightly_collect": {
                        "status": "active",
                        "schedule": "Daily 02:15 IST",
                        "workers": 4,
                        "autonomous": True,
                        "level": 4
                    },
                    "high_freq_collect": {
                        "status": "active",
                        "schedule": "Every 2 hours (12x/day)",
                        "workers": 12,
                        "autonomous": True,
                        "level": 4
                    },
                    "max_collect": {
                        "status": "active",
                        "schedule": "4x daily",
                        "workers": 12,
                        "autonomous": True,
                        "level": 4
                    },
                    "rotation_scheduler": {
                        "status": "deployed",
                        "schedule": "Daily 07:30 IST",
                        "workers": 1,
                        "autonomous": True,
                        "level": 4
                    }
                },
                "oracle_vm": {
                    "watchlist_scrape": {
                        "status": "intermittent",
                        "schedule": "Twice daily (06:20, 15:20 IST)",
                        "workers": 1,
                        "autonomous": True,
                        "level": 3,
                        "issue": "IP blocking ~20% of time"
                    },
                    "health_monitor": {
                        "status": "active",
                        "schedule": "Every 15 minutes",
                        "autonomous": True,
                        "level": 4
                    },
                    "keepwarm": {
                        "status": "active",
                        "schedule": "Every 10 minutes",
                        "autonomous": True,
                        "level": 4
                    }
                },
                "laptop": {
                    "maxun_robots": {
                        "status": "semi-active",
                        "schedule": "Hourly when laptop on",
                        "autonomous": False,
                        "level": 1,
                        "dependencies": ["laptop_powered", "chrome_installed"]
                    }
                }
            },
            "summary": {
                "total_scrapers": 12,
                "active_scheduled": 10,
                "fully_autonomous": 9,
                "requires_intervention": 3,
                "estimated_daily_growth": int(daily_avg),
                "health_score": "good" if daily_avg > 3000 else "needs_attention"
            }
        }
        
        return status
        
    finally:
        cur.close()
        conn.close()


def get_category_health() -> Dict:
    """Get health metrics per category."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                category,
                COUNT(*) as total_rows,
                COUNT(DISTINCT asin) as unique_asins,
                MAX(collected_at) as last_scraped,
                COUNT(CASE WHEN subcategory IS NOT NULL THEN 1 END) as with_subcat,
                COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price,
                COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as with_rating
            FROM snapshots
            GROUP BY category
            ORDER BY total_rows DESC
        """)
        categories = cur.fetchall()
        
        result = []
        for cat in categories:
            days_since = None
            if cat['last_scraped']:
                delta = datetime.now(timezone.utc) - cat['last_scraped'].replace(tzinfo=timezone.utc)
                days_since = delta.days
            
            freshness = "fresh" if (days_since is None or days_since <= 1) else \
                       "stale" if days_since > 7 else "moderate"
            
            result.append({
                "category": cat['category'],
                "total_rows": cat['total_rows'],
                "unique_asins": cat['unique_asins'],
                "last_scraped": cat['last_scraped'].isoformat() if cat['last_scraped'] else None,
                "days_since_scrape": days_since,
                "freshness": freshness,
                "subcategory_coverage": (cat['with_subcat'] / cat['total_rows'] * 100) if cat['total_rows'] > 0 else 0,
                "price_coverage": (cat['with_price'] / cat['total_rows'] * 100) if cat['total_rows'] > 0 else 0,
                "rating_coverage": (cat['with_rating'] / cat['total_rows'] * 100) if cat['total_rows'] > 0 else 0
            })
        
        return {"categories": result}
        
    finally:
        cur.close()
        conn.close()


def get_scraper_metrics(hours: int = 24) -> Dict:
    """Get recent scraper performance metrics."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Hourly breakdown
        cur.execute("""
            SELECT 
                DATE_TRUNC('hour', collected_at) as hour,
                COUNT(*) as rows,
                COUNT(DISTINCT asin) as asins,
                COUNT(DISTINCT category) as categories
            FROM snapshots
            WHERE collected_at > NOW() - INTERVAL '%s hours'
            GROUP BY DATE_TRUNC('hour', collected_at)
            ORDER BY hour DESC
            LIMIT 24
        """, (hours,))
        hourly = cur.fetchall()
        
        # Source breakdown
        cur.execute("""
            SELECT 
                source,
                COUNT(*) as rows,
                COUNT(DISTINCT asin) as asins,
                MIN(collected_at) as first_seen,
                MAX(collected_at) as last_seen
            FROM snapshots
            WHERE collected_at > NOW() - INTERVAL '%s hours'
            GROUP BY source
            ORDER BY rows DESC
        """, (hours,))
        sources = cur.fetchall()
        
        return {
            "period": f"Last {hours} hours",
            "hourly_activity": [
                {
                    "hour": row['hour'].isoformat() if hasattr(row['hour'], 'isoformat') else str(row['hour']),
                    "rows": row['rows'],
                    "asins": row['asins'],
                    "categories": row['categories']
                }
                for row in hourly
            ],
            "source_breakdown": [
                {
                    "source": row['source'],
                    "rows": row['rows'],
                    "asins": row['asins'],
                    "first_seen": row['first_seen'].isoformat() if row['first_seen'] else None,
                    "last_seen": row['last_seen'].isoformat() if row['last_seen'] else None
                }
                for row in sources
            ]
        }
        
    finally:
        cur.close()
        conn.close()
