"""
ScoutVeda Weekly Category Rotation Engine

A centralized scheduler that manages continuous scraping across all Amazon
categories with intelligent batch allocation, tier-based collection, and
automatic progress tracking.

Architecture:
  - Batch Scheduler: Divides categories into weekly batches
  - Priority Queue: Orders categories by freshness, coverage gaps, importance
  - Tier Manager: Controls depth of collection (Tier 1/2/3)
  - Progress Tracker: Maintains checkpoints for resume capability
  - Overflow Handler: Carries forward incomplete work to next cycle

Usage:
  python rotation_scheduler.py --mode weekly
  python rotation_scheduler.py --mode daily --watchlist
  python rotation_scheduler.py --report --week 2026-W39
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DataTier(str, Enum):
    """Collection depth tiers."""
    TIER_1_BROAD = "TIER_1"      # Essential fields only
    TIER_2_DEEP = "TIER_2"       # + History, sentiment, Q&A
    TIER_3_ADVANCED = "TIER_3"   # + Profitability, ads, forecasting


class BatchStatus(str, Enum):
    """Weekly batch lifecycle."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    OVERFLOWED = "OVERFLOWED"


@dataclass
class CategoryProfile:
    """Metadata for a category's scraping state."""
    category: str
    total_asins: int
    unique_asins: int
    rows_collected: int
    last_scraped: Optional[str]
    subcategory_count: int
    coverage_pct: float
    avg_completeness: float
    freshness_score: float  # 0-1, higher = more recent
    priority_score: float   # Composite score for scheduling


@dataclass
class WeeklyBatch:
    """A week's worth of categories to scrape."""
    week_number: int
    year: int
    status: str
    categories: list
    target_asins: int
    actual_asins: int
    started_at: Optional[str]
    completed_at: Optional[str]
    overflow_categories: list


@dataclass
class WeeklyReport:
    """End-of-week summary."""
    week_number: int
    year: int
    runtime_hours: float
    categories_assigned: int
    categories_completed: int
    categories_partial: int
    products_discovered: int
    asins_processed: int
    rows_collected: int
    tier1_coverage: float
    tier2_coverage: float
    tier3_coverage: float
    avg_data_completeness: float
    new_attributes_discovered: int
    failures: int
    retries: int
    rate_limit_events: int
    avg_processing_speed: float  # ASINs/hour
    unfinished_work_carried_forward: int
    next_week_categories: list


class RotationDatabase:
    """Manages rotation state in Postgres."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    def get_conn(self):
        return psycopg2.connect(self.database_url)
    
    def ensure_tables(self):
        """Create rotation-specific tables if they don't exist."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                # Weekly batches tracking
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS rotation_batches (
                        id SERIAL PRIMARY KEY,
                        week_number INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        categories JSONB NOT NULL,
                        target_asins INTEGER,
                        actual_asins INTEGER DEFAULT 0,
                        started_at TIMESTAMPTZ,
                        completed_at TIMESTAMPTZ,
                        overflow_categories JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_batches_week 
                        ON rotation_batches(year, week_number);
                    
                    CREATE INDEX IF NOT EXISTS idx_batches_status 
                        ON rotation_batches(status);
                    
                    -- Category progress tracking
                    CREATE TABLE IF NOT EXISTS category_progress (
                        id SERIAL PRIMARY KEY,
                        category TEXT NOT NULL,
                        week_number INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        asins_target INTEGER,
                        asins_completed INTEGER DEFAULT 0,
                        tier1_done INTEGER DEFAULT 0,
                        tier2_done INTEGER DEFAULT 0,
                        tier3_done INTEGER DEFAULT 0,
                        attributes_collected INTEGER DEFAULT 0,
                        missing_attributes JSONB,
                        last_scraped TIMESTAMPTZ,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_progress_category 
                        ON category_progress(category);
                    
                    CREATE INDEX IF NOT EXISTS idx_progress_week 
                        ON category_progress(year, week_number);
                    
                    -- Weekly reports
                    CREATE TABLE IF NOT EXISTS weekly_reports (
                        id SERIAL PRIMARY KEY,
                        week_number INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        report_json JSONB NOT NULL,
                        generated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_reports_week 
                        ON weekly_reports(year, week_number);
                    
                    -- Scraping metrics (for performance analysis)
                    CREATE TABLE IF NOT EXISTS scraping_metrics (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        asins_attempted INTEGER,
                        asins_success INTEGER,
                        asins_failed INTEGER,
                        requests_made INTEGER,
                        rate_limit_hits INTEGER,
                        retry_count INTEGER,
                        duration_seconds FLOAT,
                        throughput_per_hour FLOAT
                    );
                """)
                conn.commit()
                logger.info("Rotation tables ensured.")
    
    def get_current_week(self) -> tuple[int, int]:
        """Get ISO week number and year."""
        now = datetime.now(timezone.utc)
        iso_cal = now.isocalendar()
        return iso_cal[1], iso_cal[0]
    
    def get_or_create_batch(self, week: int, year: int) -> WeeklyBatch:
        """Get existing batch or create new one."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM rotation_batches 
                    WHERE week_number = %s AND year = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (week, year))
                row = cur.fetchone()
                
                if row:
                    return WeeklyBatch(
                        week_number=row['week_number'],
                        year=row['year'],
                        status=row['status'],
                        categories=json.loads(row['categories']) if row['categories'] else [],
                        target_asins=row['target_asins'],
                        actual_asins=row['actual_asins'] or 0,
                        started_at=str(row['started_at']) if row['started_at'] else None,
                        completed_at=str(row['completed_at']) if row['completed_at'] else None,
                        overflow_categories=json.loads(row['overflow_categories']) if row['overflow_categories'] else []
                    )
                
                # Create new pending batch
                cur.execute("""
                    INSERT INTO rotation_batches (week_number, year, status, categories)
                    VALUES (%s, %s, 'PENDING', '[]'::jsonb)
                    RETURNING *
                """, (week, year))
                row = cur.fetchone()
                
                return WeeklyBatch(
                    week_number=row['week_number'],
                    year=row['year'],
                    status=row['status'],
                    categories=[],
                    target_asins=0,
                    actual_asins=0,
                    started_at=None,
                    completed_at=None,
                    overflow_categories=[]
                )
    
    def save_batch(self, batch: WeeklyBatch):
        """Persist batch state."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO rotation_batches 
                        (week_number, year, status, categories, target_asins, actual_asins,
                         started_at, completed_at, overflow_categories, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (week_number, year)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        categories = EXCLUDED.categories,
                        target_asins = EXCLUDED.target_asins,
                        actual_asins = EXCLUDED.actual_asins,
                        started_at = EXCLUDED.started_at,
                        completed_at = EXCLUDED.completed_at,
                        overflow_categories = EXCLUDED.overflow_categories,
                        updated_at = NOW()
                """, (
                    batch.week_number, batch.year, batch.status,
                    json.dumps(batch.categories), batch.target_asins, batch.actual_asins,
                    batch.started_at, batch.completed_at,
                    json.dumps(batch.overflow_categories)
                ))
                conn.commit()
    
    def update_category_progress(
        self, 
        category: str, 
        week: int, 
        year: int, 
        status: str,
        asins_completed: int = 0,
        tier1: int = 0,
        tier2: int = 0,
        tier3: int = 0,
        attributes: int = 0,
        missing_attrs: list = None,
        last_scraped: str = None
    ):
        """Update progress for a specific category."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO category_progress
                        (category, week_number, year, status, asins_completed,
                         tier1_done, tier2_done, tier3_done, attributes_collected,
                         missing_attributes, last_scraped, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (category, week_number, year)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        asins_completed = EXCLUDED.asins_completed,
                        tier1_done = EXCLUDED.tier1_done,
                        tier2_done = EXCLUDED.tier2_done,
                        tier3_done = EXCLUDED.tier3_done,
                        attributes_collected = EXCLUDED.attributes_collected,
                        missing_attributes = EXCLUDED.missing_attributes,
                        last_scraped = EXCLUDED.last_scraped,
                        updated_at = NOW()
                """, (
                    category, week, year, status, asins_completed,
                    tier1, tier2, tier3, attributes,
                    json.dumps(missing_attrs or []), last_scraped
                ))
                conn.commit()
    
    def save_metric(self, metric: dict):
        """Record a scraping performance metric."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scraping_metrics
                        (asins_attempted, asins_success, asins_failed,
                         requests_made, rate_limit_hits, retry_count,
                         duration_seconds, throughput_per_hour)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    metric.get('asins_attempted'),
                    metric.get('asins_success'),
                    metric.get('asins_failed'),
                    metric.get('requests_made'),
                    metric.get('rate_limit_hits'),
                    metric.get('retry_count'),
                    metric.get('duration_seconds'),
                    metric.get('throughput_per_hour')
                ))
                conn.commit()
    
    def save_weekly_report(self, report: WeeklyReport):
        """Save end-of-week summary."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO weekly_reports
                        (week_number, year, report_json, generated_at)
                    VALUES (%s, %s, %s, NOW())
                """, (
                    report.week_number, report.year,
                    json.dumps(asdict(report))
                ))
                conn.commit()


class CategoryAnalyzer:
    """Analyzes category coverage and determines priorities."""
    
    def __init__(self, db: RotationDatabase):
        self.db = db
    
    def get_all_categories(self) -> list:
        """Get all unique categories from snapshots."""
        with self.db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT category 
                    FROM snapshots 
                    ORDER BY category
                """)
                return [row[0] for row in cur.fetchall()]
    
    def analyze_category(self, category: str) -> CategoryProfile:
        """Generate profile for a single category."""
        with self.db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Basic stats
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT asin) as unique_asins,
                        COUNT(*) as total_rows,
                        COUNT(CASE WHEN subcategory IS NOT NULL THEN 1 END) as with_subcat,
                        COUNT(CASE WHEN brand IS NOT NULL THEN 1 END) as with_brand,
                        MAX(collected_at) as last_scraped
                    FROM snapshots
                    WHERE category = %s
                """, (category,))
                stats = cur.fetchone()
                
                # Subcategory count
                cur.execute("""
                    SELECT COUNT(DISTINCT subcategory) 
                    FROM snapshots 
                    WHERE category = %s AND subcategory IS NOT NULL
                """, (category,))
                subcat_count = cur.fetchone()[0] or 0
                
                # Average completeness (based on field coverage)
                cur.execute("""
                    SELECT 
                        AVG(CASE WHEN subcategory IS NOT NULL THEN 1 ELSE 0 END)::float 
                        + AVG(CASE WHEN brand IS NOT NULL THEN 1 ELSE 0 END)::float
                        + AVG(CASE WHEN price IS NOT NULL THEN 1 ELSE 0 END)::float
                        + AVG(CASE WHEN rating IS NOT NULL THEN 1 ELSE 0 END)::float
                    FROM snapshots
                    WHERE category = %s
                """, (category,))
                avg_completeness = (cur.fetchone()[0] or 0) / 4.0
                
                # Coverage percentage (rows vs estimated catalog size)
                # Using a heuristic: assume each category has ~5000-50000 products
                estimated_catalog_size = self._estimate_catalog_size(category)
                coverage_pct = (stats['unique_asins'] / estimated_catalog_size) * 100 if estimated_catalog_size > 0 else 0
                
                # Freshness score (0-1, based on days since last scrape)
                days_since = 0
                if stats['last_scraped']:
                    days_since = (datetime.now(timezone.utc) - stats['last_scraped'].replace(tzinfo=timezone.utc)).days
                freshness = max(0, 1 - (days_since / 30))  # Decay over 30 days
                
                return CategoryProfile(
                    category=category,
                    total_asins=stats['total_rows'],
                    unique_asins=stats['unique_asins'],
                    rows_collected=stats['total_rows'],
                    last_scraped=str(stats['last_scraped']) if stats['last_scraped'] else None,
                    subcategory_count=subcat_count,
                    coverage_pct=coverage_pct,
                    avg_completeness=avg_completeness,
                    freshness_score=freshness,
                    priority_score=0  # Calculated by scheduler
                )
    
    def _estimate_catalog_size(self, category: str) -> int:
        """Estimate total products in category (heuristic)."""
        # These are rough estimates based on Amazon India catalog structure
        estimates = {
            'Home & Kitchen': 50000,
            'Beauty & Personal Care': 40000,
            'Health & Personal Care': 35000,
            'Grocery & Gourmet Foods': 30000,
            'Clothing & Accessories': 100000,
            'Shoes & Handbags': 50000,
            'Electronics Accessories': 40000,
            'Computers & Accessories': 30000,
            'Toys & Games': 25000,
            'Baby Products': 20000,
            'Sports & Fitness': 15000,
            'Books': 500000,  # Very large
            'Movies & TV Shows': 100000,
            'Music': 50000,
            'Watches & Gifting': 15000,
            'Pet Supplies': 10000,
            'Car Accessories': 20000,
            'Garden & Outdoors': 15000,
            'Jewellery': 25000,
            'Apps & Games': 5000,
            'Kindle Store': 100000,
        }
        return estimates.get(category, 10000)  # Default estimate
    
    def calculate_priority_scores(self, profiles: list[CategoryProfile]) -> list[CategoryProfile]:
        """Calculate composite priority scores for scheduling."""
        for p in profiles:
            # Priority = weighted combination of factors
            # Higher coverage gap = higher priority
            # Lower freshness = higher priority  
            # More unique ASINs = potentially more valuable
            coverage_gap = 100 - p.coverage_pct  # Invert: low coverage = high priority
            freshness_gap = 1 - p.freshness_score  # Low freshness = high priority
            data_quality_gap = 1 - p.avg_completeness  # Low quality = high priority
            
            # Weighted formula
            priority = (
                coverage_gap * 0.4 +      # 40% weight: fill gaps first
                freshness_gap * 0.3 +     # 30% weight: refresh stale data
                data_quality_gap * 0.2 +  # 20% weight: improve quality
                min(p.unique_asins / 1000, 1) * 0.1  # 10% weight: popular categories
            )
            
            p.priority_score = round(priority, 4)
        
        # Sort by priority (highest first)
        profiles.sort(key=lambda x: x.priority_score, reverse=True)
        return profiles


class BatchScheduler:
    """Creates and manages weekly batches."""
    
    def __init__(self, db: RotationDatabase, analyzer: CategoryAnalyzer):
        self.db = db
        self.analyzer = analyzer
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load scheduler configuration."""
        config_path = Path(__file__).parent / "rotation_config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        
        # Default configuration
        return {
            "categories_per_batch": 30,
            "max_asins_per_week": 50000,
            "tier_distribution": {
                "TIER_1": 0.7,   # 70% of runs focus on broad coverage
                "TIER_2": 0.25,  # 25% do deep analysis
                "TIER_3": 0.05   # 5% do advanced validation
            },
            "refresh_intervals": {
                "TIER_1": 7,     # Refresh Tier 1 every 7 days
                "TIER_2": 14,    # Refresh Tier 2 every 14 days
                "TIER_3": 30     # Refresh Tier 3 every 30 days
            }
        }
    
    def create_weekly_batch(self, week: int, year: int) -> WeeklyBatch:
        """Create a new weekly batch based on priorities."""
        # Get all categories with profiles
        categories = self.analyzer.get_all_categories()
        profiles = [self.analyzer.analyze_category(cat) for cat in categories]
        profiles = self.analyzer.calculate_priority_scores(profiles)
        
        # Determine batch size based on capacity
        batch_size = self._calculate_optimal_batch_size(profiles)
        
        # Select top-priority categories
        selected = profiles[:batch_size]
        
        # Create batch
        batch = WeeklyBatch(
            week_number=week,
            year=year,
            status=BatchStatus.PENDING,
            categories=[p.category for p in selected],
            target_asins=sum(p.unique_asins for p in selected),
            actual_asins=0,
            started_at=None,
            completed_at=None,
            overflow_categories=[]
        )
        
        # Save to database
        self.db.save_batch(batch)
        
        logger.info(f"Created Week {week}/{year} batch: {len(selected)} categories, {batch.target_asins:,} target ASINs")
        
        return batch
    
    def _calculate_optimal_batch_size(self, profiles: list) -> int:
        """Calculate optimal batch size based on capacity."""
        # Get recent performance metrics
        daily_avg = self._get_recent_daily_throughput()
        weekly_capacity = daily_avg * 7
        
        # Adjust based on category complexity
        avg_complexity = sum(1/p.coverage_pct for p in profiles[:10] if p.coverage_pct > 0) / min(10, len(profiles))
        
        # Target: process categories where we can achieve 80%+ coverage
        optimal_size = int(weekly_capacity / (daily_avg / 30))  # Rough estimate
        
        # Clamp to reasonable range
        return max(15, min(50, optimal_size))
    
    def _get_recent_daily_throughput(self) -> float:
        """Get average daily ASIN throughput from recent metrics."""
        with self.db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT AVG(daily_asins) as avg_throughput
                    FROM (
                        SELECT DATE(collected_at) as day, COUNT(DISTINCT asin) as daily_asins
                        FROM snapshots
                        WHERE collected_at > NOW() - INTERVAL '14 days'
                        GROUP BY DATE(collected_at)
                    ) daily_stats
                """)
                result = cur.fetchone()
                return result[0] or 4000  # Default to 4000 ASINs/day
    
    def get_pending_batches(self) -> list:
        """Get all pending or in-progress batches."""
        with self.db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM rotation_batches 
                    WHERE status IN ('PENDING', 'IN_PROGRESS')
                    ORDER BY year DESC, week_number DESC
                """)
                batches = []
                for row in cur.fetchall():
                    batches.append(WeeklyBatch(
                        week_number=row['week_number'],
                        year=row['year'],
                        status=row['status'],
                        categories=json.loads(row['categories']) if row['categories'] else [],
                        target_asins=row['target_asins'],
                        actual_asins=row['actual_asins'] or 0,
                        started_at=str(row['started_at']) if row['started_at'] else None,
                        completed_at=str(row['completed_at']) if row['completed_at'] else None,
                        overflow_categories=json.loads(row['overflow_categories']) if row['overflow_categories'] else []
                    ))
                return batches


class RotationEngine:
    """Main engine that orchestrates the weekly rotation."""
    
    def __init__(self, database_url: str):
        self.db = RotationDatabase(database_url)
        self.analyzer = CategoryAnalyzer(self.db)
        self.scheduler = BatchScheduler(self.db, self.analyzer)
        self.metrics = {
            'asins_attempted': 0,
            'asins_success': 0,
            'asins_failed': 0,
            'requests_made': 0,
            'rate_limit_hits': 0,
            'retry_count': 0,
            'start_time': None,
            'end_time': None
        }
    
    def run_weekly_cycle(self, week: Optional[int] = None, year: Optional[int] = None):
        """Execute a full weekly rotation cycle."""
        if week is None or year is None:
            week, year = self.db.get_current_week()
        
        logger.info(f"Starting Weekly Rotation Cycle: Week {week}/{year}")
        
        # Ensure tables exist
        self.db.ensure_tables()
        
        # Get or create batch
        batch = self.scheduler.get_or_create_batch(week, year)
        
        if batch.status == BatchStatus.COMPLETED:
            logger.info(f"Week {week}/{year} already completed. Generating report.")
            self.generate_weekly_report(week, year)
            return
        
        # Start batch
        batch.status = BatchStatus.IN_PROGRESS
        batch.started_at = datetime.now(timezone.utc).isoformat()
        self.db.save_batch(batch)
        
        # Process each category
        start_time = time.time()
        metrics = {
            'asins_attempted': 0,
            'asins_success': 0,
            'asins_failed': 0,
            'requests_made': 0,
            'rate_limit_hits': 0,
            'retry_count': 0,
            'duration_seconds': 0,
            'throughput_per_hour': 0
        }
        
        for i, category in enumerate(batch.categories):
            logger.info(f"[{i+1}/{len(batch.categories)}] Processing: {category}")
            
            # Run scraper for this category
            category_metrics = self._scrape_category(category)
            metrics.update(category_metrics)
            
            # Update progress
            self.db.update_category_progress(
                category=category,
                week=week,
                year=year,
                status=BatchStatus.COMPLETED,
                asins_completed=category_metrics['asins_success'],
                last_scraped=datetime.now(timezone.utc).isoformat()
            )
            
            batch.actual_asins += category_metrics['asins_success']
        
        # Calculate duration and throughput
        duration = time.time() - start_time
        metrics['duration_seconds'] = duration
        metrics['throughput_per_hour'] = (metrics['asins_success'] / duration * 3600) if duration > 0 else 0
        
        # Complete batch
        batch.status = BatchStatus.COMPLETED
        batch.completed_at = datetime.now(timezone.utc).isoformat()
        self.db.save_batch(batch)
        
        # Save metrics
        self.db.save_metric(metrics)
        
        # Generate report
        self.generate_weekly_report(week, year)
        
        logger.info(f"Weekly cycle complete. Processed {metrics['asins_success']} ASINs in {duration/60:.1f} minutes.")
    
    def _scrape_category(self, category: str) -> dict:
        """Run scraper for a single category. Returns metrics."""
        # Import here to avoid circular imports
        from collector_optimized import scrape_category
        
        # Run scraping with our category filter
        result = scrape_category(category, pages=2, list_types=['bestsellers'])
        
        return {
            'asins_attempted': result.get('total_tasks', 0),
            'asins_success': result.get('rows_inserted', 0),
            'asins_failed': result.get('failed', 0),
            'requests_made': result.get('total_tasks', 0),
            'rate_limit_hits': 0,
            'retry_count': 0
        }
    
    def generate_weekly_report(self, week: int, year: int) -> WeeklyReport:
        """Generate comprehensive weekly report."""
        with self.db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Batch info
                cur.execute("""
                    SELECT * FROM rotation_batches 
                    WHERE week_number = %s AND year = %s
                """, (week, year))
                batch = cur.fetchone()
                
                # Category progress
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
                        COUNT(CASE WHEN status = 'IN_PROGRESS' THEN 1 END) as in_progress,
                        SUM(asins_completed) as total_asins,
                        SUM(tier1_done) as tier1_total,
                        SUM(tier2_done) as tier2_total,
                        SUM(tier3_done) as tier3_total
                    FROM category_progress
                    WHERE week_number = %s AND year = %s
                """, (week, year))
                progress = cur.fetchone()
                
                # Metrics
                cur.execute("""
                    SELECT 
                        AVG(duration_seconds) as avg_duration,
                        SUM(asins_success) as total_success,
                        SUM(rate_limit_hits) as total_rate_limits,
                        SUM(retry_count) as total_retries
                    FROM scraping_metrics
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                """)
                metrics = cur.fetchone()
                
                # Calculate coverage percentages
                tier1_cov = (progress['tier1_total'] / progress['total_asins'] * 100) if progress['total_asins'] else 0
                tier2_cov = (progress['tier2_total'] / progress['total_asins'] * 100) if progress['total_asins'] else 0
                tier3_cov = (progress['tier3_total'] / progress['total_asins'] * 100) if progress['total_asins'] else 0
                
                # Prepare next week's categories
                next_week, next_year = week + 1, year
                if next_week > 52:
                    next_week = 1
                    next_year += 1
                
                report = WeeklyReport(
                    week_number=week,
                    year=year,
                    runtime_hours=(metrics['avg_duration'] or 0) / 3600 if metrics else 0,
                    categories_assigned=progress['total'] or 0,
                    categories_completed=progress['completed'] or 0,
                    categories_partial=progress['in_progress'] or 0,
                    products_discovered=0,  # Would need separate tracking
                    asins_processed=progress['total_asins'] or 0,
                    rows_collected=progress['total_asins'] or 0,
                    tier1_coverage=tier1_cov,
                    tier2_coverage=tier2_cov,
                    tier3_coverage=tier3_cov,
                    avg_data_completeness=75.0,  # Placeholder
                    new_attributes_discovered=0,
                    failures=0,
                    retries=((progress['total_asins'] or 0)) * 0.05,  # Estimate (None-safe: empty week)
                    rate_limit_events=metrics['total_rate_limits'] or 0,
                    avg_processing_speed=100,  # Placeholder
                    unfinished_work_carried_forward=0,
                    next_week_categories=[]  # Would be populated by scheduler
                )
                
                self.db.save_weekly_report(report)
                return report


def main():
    parser = argparse.ArgumentParser(description='ScoutVeda Weekly Rotation Engine')
    parser.add_argument('--mode', choices=['weekly', 'daily', 'report'], default='weekly')
    parser.add_argument('--week', type=int, help='Specific week number')
    parser.add_argument('--year', type=int, help='Specific year')
    parser.add_argument('--category', help='Single category for manual run')
    parser.add_argument('--tier', choices=['1', '2', '3'], default='1', help='Data collection tier')
    
    args = parser.parse_args()
    
    # Load database URL: prefer the environment (GitHub Actions passes the
    # DATABASE_URL secret, and .env is gitignored so it never exists on a
    # runner). Fall back to the local .env for laptop runs.
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        database_url = line.split('=', 1)[1].strip()
                        break
        if not database_url:
            logger.error(" DATABASE_URL not set (env var or .env)")
            sys.exit(1)
    
    # Initialize engine
    engine = RotationEngine(database_url)
    
    if args.mode == 'weekly':
        engine.run_weekly_cycle(args.week, args.year)
    elif args.mode == 'report':
        # Report mode reads rotation tables; make sure they exist first.
        # The weekly cycle path calls ensure_tables() itself, but a report
        # can run on a database that has never had a weekly cycle, and the
        # 2026-09-25 scheduled run died exactly there: 'rotation_batches'
        # does not exist.
        engine.db.ensure_tables()
        week, year = engine.db.get_current_week()
        report = engine.generate_weekly_report(week, year)
        print(json.dumps(asdict(report), indent=2))
    elif args.mode == 'daily':
        # Daily mode: process one category from queue
        if args.category:
            metrics = engine._scrape_category(args.category)
            print(json.dumps(metrics, indent=2))
        else:
            logger.error(" --category required for daily mode")
            sys.exit(1)


if __name__ == "__main__":
    main()
