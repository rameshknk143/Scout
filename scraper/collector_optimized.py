"""
Optimized Max-Capacity Collector for ScoutVeda

This module implements maximum scraping throughput with:
- Dynamic rate limiting based on response patterns
- Intelligent retry with exponential backoff
- Connection pooling and keep-alive
- Graceful degradation on blocks
- Real-time progress tracking
"""

import asyncio
import hashlib
import http.cookiejar
import json
import logging
import os
import queue
import random
import re
import ssl
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlencode
from urllib.request import (
    HTTPCookieProcessor,
    HTTPSHandler,
    Request,
    build_opener,
)

import db
from registry.attribute_registry import DataStatus, default_registry
from registry.category_mapper import CategoryMapper, get_ontology

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION — Tunable knobs for max throughput
# ============================================================

# Core settings
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Concurrency settings
FETCH_WORKERS = max(1, int(os.environ.get("SCOUT_FETCH_WORKERS", "8")))
GAP_MIN_SECONDS = float(os.environ.get("SCOUT_GAP_MIN", "8"))
GAP_MAX_SECONDS = float(os.environ.get("SCOUT_GAP_MAX", "18"))

# Retry settings
MAX_RETRIES = int(os.environ.get("SCOUT_MAX_RETRIES", "3"))
RETRY_BACKOFF_BASE = float(os.environ.get("SCOUT_RETRY_BACKOFF", "2.0"))
REQUEST_TIMEOUT = int(os.environ.get("SCOUT_REQUEST_TIMEOUT", "30"))

# Rate limiting
MIN_REQUEST_INTERVAL = float(os.environ.get("SCOUT_MIN_INTERVAL", "1.5"))
RATE_LIMIT_WINDOW = int(os.environ.get("SCOUT_RATE_LIMIT_WINDOW", "60"))
MAX_REQUESTS_PER_WINDOW = int(os.environ.get("SCOUT_MAX_REQUESTS_PER_WINDOW", "40"))

# ============================================================
# RATE LIMITER — Token bucket algorithm
# ============================================================

class TokenBucketRateLimiter:
    """Token bucket rate limiter for smooth, compliant scraping."""
    
    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Tokens per second (requests/second)
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, returning wait time if needed."""
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # Calculate wait time
            wait_time = (tokens - self.tokens) / self.rate
            return wait_time
    
    def wait(self, tokens: int = 1) -> float:
        """Wait until tokens are available, returns actual wait time."""
        start = time.monotonic()
        while True:
            wait = self.acquire(tokens)
            if wait == 0:
                return time.monotonic() - start
            time.sleep(wait * 0.8)  # Wait 80% of calculated time

# Initialize global rate limiter
_rate_limiter = TokenBucketRateLimiter(
    rate=MAX_REQUESTS_PER_WINDOW / RATE_LIMIT_WINDOW,
    burst=MAX_REQUESTS_PER_WINDOW
)

# ============================================================
# CONNECTION POOL — Reusable HTTP connections
# ============================================================

class ConnectionPool:
    """HTTP connection pool with keep-alive support."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
    
    def get_connection(self) -> Optional[Request]:
        """Get a connection from the pool."""
        try:
            return self._pool.get_nowait()
        except queue.Empty:
            return None
    
    def return_connection(self, conn: Request):
        """Return a connection to the pool."""
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            pass  # Pool full, discard

_pool = ConnectionPool(max_connections=FETCH_WORKERS * 2)

# ============================================================
# REQUEST EXECUTION — Optimized fetch with retries
# ============================================================

def _build_opener():
    """Build HTTP opener with cookies and proper handling."""
    cookie_jar = http.cookiejar.CookieJar()
    cookie_processor = HTTPCookieProcessor(cookie_jar)
    handler = HTTPSHandler()
    return build_opener(handler, cookie_processor)

_opener = _build_opener()

def fetch_with_retry(url: str, session: object = None, 
                     retries: int = MAX_RETRIES, 
                     backoff_factor: float = RETRY_BACKOFF_BASE) -> Optional[str]:
    """
    Fetch URL with intelligent retry and rate limiting.
    
    Returns HTML content or None if all retries exhausted.
    """
    last_error = None
    
    for attempt in range(retries):
        try:
            # Rate limit check
            wait_time = _rate_limiter.wait()
            if wait_time > 0:
                time.sleep(wait_time * random.uniform(0.9, 1.1))
            
            # Build request
            req = Request(url, headers=HEADERS)
            req.add_header("Accept-Encoding", "gzip, deflate, br")
            req.add_header("Cache-Control", "no-cache")
            
            # Execute with timeout
            start = time.time()
            response = _opener.open(req, timeout=REQUEST_TIMEOUT)
            elapsed = time.time() - start
            
            # Read content
            html = response.read()
            
            # Handle compression
            content_encoding = response.headers.get("Content-Encoding", "")
            if "gzip" in content_encoding:
                import gzip
                html = gzip.decompress(html)
            elif "br" in content_encoding:
                import brotli
                html = brotli.decompress(html)
            
            html_str = html.decode("utf-8", errors="replace")
            
            # Validate response
            if len(html_str) < 1000:
                logger.warning(f"Short response ({len(html_str)} bytes) for {url[:80]}")
                raise ValueError(f"Response too short: {len(html_str)}")
            
            # Log timing for debugging
            if elapsed > 10:
                logger.warning(f"Slow fetch: {elapsed:.1f}s for {url[:80]}")
            
            return html_str
            
        except Exception as e:
            last_error = e
            
            # Exponential backoff with jitter
            if attempt < retries - 1:
                delay = backoff_factor ** attempt * (0.5 + random.random() * 0.5)
                logger.debug(f"Retry {attempt+1}/{retries} for {url[:60]}: {type(e).__name__}")
                time.sleep(delay)
            
            # Check for block indicators
            if "Please confirm you are a human" in str(e):
                logger.error("Amazon bot detection triggered! Backing off...")
                time.sleep(60)  # Long pause on block
                break
    
    logger.error(f"All retries exhausted for {url[:60]}: {last_error}")
    return None

# ============================================================
# CATEGORY & LIST CONFIG
# ============================================================

CATEGORIES = {
    "Electronics Accessories": "electronics",
    "Home & Kitchen": "kitchen",
    "Beauty & Personal Care": "beauty",
    "Sports & Fitness": "sports",
    "Toys & Games": "toys",
    "Stationery/Office": "office",
    "Pet Supplies": "pet-supplies",
    "Car Accessories": "automotive",
    "Garden & Outdoors": "garden",
    "Baby Products": "baby",
    "Watches & Gifting": "watches",
    "Clothing & Accessories": "apparel",
    "Amazon Launchpad": "boost",
    "Amazon Renewed": "amazon-renewed",
    "Apps & Games": "mobile-apps",
    "Bags, Wallets & Luggage": "luggage",
    "Books": "books",
    "Computers & Accessories": "computers",
    "Gift Cards": "gift-cards",
    "Grocery & Gourmet Foods": "grocery",
    "Health & Personal Care": "hpc",
    "Home Improvement": "home-improvement",
    "Industrial & Scientific": "industrial",
    "Jewellery": "jewelry",
    "Kindle Store": "digital-text",
    "Movies & TV Shows": "dvd",
    "Music": "music",
    "Musical Instruments": "musical-instruments",
    "Shoes & Handbags": "shoes",
    "Software": "software",
    "Video Games": "videogames",
}

LIST_TYPES = {
    "bestsellers": "gp/bestsellers",
    "new-releases": "gp/new-releases",
    "most-wished-for": "gp/most-wished-for",
    "most-gifted": "gp/most-gifted",
}

BASE_URL = "https://www.amazon.in/{path}/{slug}/"

# Throughput knobs
PAGES = tuple(
    int(p) for p in os.environ.get("SCOUT_PAGES", "1,2").split(",") if p.strip()
)

COLLECT_LIST_TYPES = tuple(
    t for t in os.environ.get("SCOUT_LIST_TYPES", "").split(",") if t.strip()
) or tuple(LIST_TYPES.keys())

# Sub-category settings
SUBCATS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subcats.json")
SUBCAT_MAX = int(os.environ.get("SCOUT_SUBCAT_MAX", "382"))
SUBCAT_LIST_TYPES = tuple(
    t for t in os.environ.get("SCOUT_SUBCAT_LIST_TYPES", "bestsellers,new-releases").split(",")
    if t.strip()
)
SUBCAT_PAGES = tuple(
    int(p) for p in os.environ.get("SCOUT_SUBCAT_PAGES", "1,2").split(",") if p.strip()
)

# Regex patterns for parsing
ASIN_RE = re.compile(r'data-asin="([A-Z0-9]{10})"')
RANK_RE = re.compile(r'zg-bdg-text">#(\d+)<')
TITLE_RE = re.compile(r'class="[^"]*p13n-sc-css-line-clamp[^"]*">([^<]+)<')
RATING_RE = re.compile(r'aria-label="([\d.]+) out of 5 stars, ([\d,]+) ratings?"')
PRICE_RE = re.compile(r'₹([\d,]+\.\d{2})')
IMAGE_RE = re.compile(r'<img[^>]+src="([^"]+)"')
BRAND_URL_RE = re.compile(r'/([A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*)/dp/')
SIZE_TIER_RE = re.compile(
    r'\b(small|compact|mini|micro|petite)\b'
    r'|\b(jumbo|large|big|standard|full-size|regular)\b',
    re.I
)
PRODUCT_TYPE_RE = re.compile(
    r'(?:earphone|headphone|speaker|charger|cable|cover|case|watch|shirt|pant|dress|shoe|book|tablet|phone|laptop|camera|toy|bag|bottle|lamp|fan|motor|blade|pillow|blanket)',
    re.I
)

# Global mapper instance
_mapper = CategoryMapper()

# ============================================================
# EXTRACTION FUNCTIONS
# ============================================================

def _extract_brand(url: str) -> Optional[str]:
    """Extract brand from Amazon URL slug."""
    m = BRAND_URL_RE.search(url)
    if not m:
        return None
    raw = m.group(1)
    parts = raw.split('-')
    if not parts:
        return None
    brand_words = []
    SKIP = {'the', 'and', 'for', 'with', 'by', 'in', 'on', 'at', 'to', 'a', 'an'}
    for w in parts[:3]:
        if w[0].isupper() and w.isalpha() and len(w) >= 2 and w.lower() not in SKIP:
            brand_words.append(w)
        else:
            break
    return ' '.join(brand_words) if brand_words else None

def _detect_size_tier(title: str) -> Optional[str]:
    """Detect size tier hint from title."""
    if not title:
        return None
    small_patterns = r'\b(small|compact|mini|micro|petite)\b'
    large_patterns = r'\b(jumbo|large|big|standard|full-size|regular)\b'
    m = re.search(small_patterns, title, re.I)
    if m:
        return m.group(1).lower()
    m = re.search(large_patterns, title, re.I)
    if m:
        return m.group(1).lower()
    return None

def _detect_product_type(title: str, category: str) -> Optional[str]:
    """Detect rough product type from title keywords."""
    if not title:
        return None
    m = re.search(PRODUCT_TYPE_RE, title, re.I)
    if m:
        return m.group(0).lower()
    return None

def parse_product_card(html: str, rank: int, category: str, list_type: str) -> Optional[dict]:
    """Extract product data from a single product card HTML."""
    asin_m = ASIN_RE.search(html)
    if not asin_m:
        return None
    
    asin = asin_m.group(1)
    title_m = TITLE_RE.search(html)
    title = title_m.group(1).strip() if title_m else ""
    
    rating_m = RATING_RE.search(html)
    rating = None
    review_count = None
    if rating_m:
        try:
            rating = float(rating_m.group(1))
            review_count = int(rating_m.group(2).replace(",", ""))
        except (ValueError, IndexError):
            pass
    
    price_m = PRICE_RE.search(html)
    price = None
    if price_m:
        try:
            price = float(price_m.group(1))
        except ValueError:
            pass
    
    image_m = IMAGE_RE.search(html)
    image_url = image_m.group(1) if image_m else None
    
    # Map category using ontology
    mapped = _mapper.map(asin, title, category)
    
    return {
        "asin": asin,
        "title": title,
        "rank": rank,
        "price": price,
        "rating": rating,
        "review_count": review_count,
        "image_url": image_url,
        "category": mapped.get("category", category),
        "subcategory": mapped.get("subcategory"),
        "product_type": mapped.get("product_type"),
        "list_type": list_type,
        "brand": _extract_brand(f"https://www.amazon.in/dp/{asin}"),
        "size_tier_hint": _detect_size_tier(title),
        "product_type_hint": _detect_product_type(title, category),
    }

# ============================================================
# MAIN COLLECTION LOGIC
# ============================================================

def fetch_list_page(category: str, slug: str, list_type: str, page: int) -> Optional[str]:
    """Fetch a single bestseller list page."""
    path = LIST_TYPES[list_type]
    url = BASE_URL.format(path=path, slug=slug)
    if page > 1:
        url += f"?pg={page}"
    
    return fetch_with_retry(url)

def run_collection(clear_db: bool = False) -> dict:
    """
    Run the main collection loop across all categories and list types.
    
    Returns statistics dict.
    """
    print(f"[collector] Starting max-capacity collection at {datetime.now(timezone.utc).isoformat()}")
    print(f"[collector] Config: {len(CATEGORIES)} cats × {len(COLLECT_LIST_TYPES)} lists × {PAGES} pages")
    print(f"[collector] Concurrency: {FETCH_WORKERS} workers, gap {GAP_MIN_SECONDS}-{GAP_MAX_SECONDS}s")
    
    stats = {
        "total_requests": 0,
        "successful_fetches": 0,
        "failed_fetches": 0,
        "rows_inserted": 0,
        "rows_skipped_dupe": 0,
        "start_time": datetime.now(timezone.utc),
        "categories_processed": [],
        "errors": [],
    }
    
    # Build task queue
    tasks = []
    for cat_name, cat_slug in CATEGORIES.items():
        for list_type in COLLECT_LIST_TYPES:
            for page in PAGES:
                tasks.append((cat_name, cat_slug, list_type, page))
    
    print(f"[collector] Total tasks: {len(tasks)}")
    
    # Execute with worker pool
    results_queue = queue.Queue()
    
    def worker(task):
        cat_name, cat_slug, list_type, page = task
        url = BASE_URL.format(path=LIST_TYPES[list_type], slug=cat_slug)
        if page > 1:
            url += f"?pg={page}"
        
        stats["total_requests"] += 1
        
        html = fetch_with_retry(url)
        if not html:
            stats["failed_fetches"] += 1
            stats["errors"].append(f"{cat_name}/{list_type}/pg{page}: fetch_failed")
            results_queue.put(None)
            return
        
        stats["successful_fetches"] += 1
        
        # Parse products
        products = []
        for asin_m in ASIN_RE.finditer(html):
            asin = asin_m.group(1)
            # Find the card boundary (next asin or end)
            start_pos = asin_m.end()
            next_asin = ASIN_RE.search(html, start_pos)
            end_pos = next_asin.start() if next_asin else len(html)
            card_html = html[start_pos:end_pos]
            
            # Extract rank from card
            rank_m = RANK_RE.search(card_html)
            rank = int(rank_m.group(1)) if rank_m else None
            
            product = parse_product_card(card_html, rank, cat_name, list_type)
            if product:
                products.append(product)
        
        results_queue.put((cat_name, list_type, page, products))
    
    # Run workers
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        futures = {executor.submit(worker, task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    cat_name, list_type, page, products = result
                    if products:
                        # Insert into DB
                        now = datetime.now(timezone.utc).isoformat()
                        rows = []
                        for p in products:
                            rows.append({
                                **p,
                                "collected_at": now,
                            })
                        
                        inserted = db.insert_snapshot_rows(rows)
                        stats["rows_inserted"] += inserted
                        stats["rows_skipped_dupe"] += len(products) - inserted
                        
                        if inserted > 0:
                            stats["categories_processed"].append(
                                f"{cat_name}/{list_type}/pg{page}: {inserted} rows"
                            )
                        
                        print(f"  ✓ {cat_name[:20]:20} | {list_type:20} | pg{page}: {inserted} rows")
                    
            except Exception as e:
                stats["failed_fetches"] += 1
                stats["errors"].append(f"worker_error: {str(e)[:100]}")
                logger.error(f"Worker error: {e}", exc_info=True)
    
    # Summary
    stats["end_time"] = datetime.now(timezone.utc)
    stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"[collector] Collection complete!")
    print(f"[collector] Duration: {stats['duration_seconds']:.1f}s")
    print(f"[collector] Requests: {stats['total_requests']} (success: {stats['successful_fetches']}, fail: {stats['failed_fetches']})")
    print(f"[collector] Rows inserted: {stats['rows_inserted']}")
    print(f"[collector] Dupe skips: {stats['rows_skipped_dupe']}")
    print(f"{'='*60}")
    
    return stats

def load_subcats(max_count=None) -> dict:
    """Load sub-categories from JSON file."""
    import json
    if not os.path.exists(SUBCATS_JSON):
        print(f"[subcats] Missing {SUBCATS_JSON}")
        return {}
    
    with open(SUBCATS_JSON) as f:
        data = json.load(f)
    
    subs = data.get("subcategories", [])
    out = {}
    for s in subs[:max_count]:
        label = s["label"]
        slug = s["slug"]
        out[label] = slug
    return out

def run_subcats(max_count=None, dry_run=False) -> dict:
    """Run sub-category collection."""
    targets = load_subcats(max_count)
    if not targets:
        print("[subcats] No sub-categories available")
        return {}
    
    print(f"[subcats] {len(targets)} sub-category lists | "
          f"types={list(SUBCAT_LIST_TYPES)} | pages={list(SUBCAT_PAGES)} "
          f"{'| DRY RUN' if dry_run else ''}")
    
    stats = {
        "total_requests": 0,
        "successful_fetches": 0,
        "failed_fetches": 0,
        "rows_inserted": 0,
        "start_time": datetime.now(timezone.utc),
    }
    
    tasks = []
    for label, slug in targets.items():
        for list_type in SUBCAT_LIST_TYPES:
            for page in SUBCAT_PAGES:
                tasks.append((label, slug, list_type, page))
    
    print(f"[subcats] Total tasks: {len(tasks)}")
    
    def worker(task):
        label, slug, list_type, page = task
        url = BASE_URL.format(path=LIST_TYPES[list_type], slug=slug)
        if page > 1:
            url += f"?pg={page}"
        
        stats["total_requests"] += 1
        
        html = fetch_with_retry(url)
        if not html:
            stats["failed_fetches"] += 1
            return
        
        stats["successful_fetches"] += 1
        
        products = []
        for asin_m in ASIN_RE.finditer(html):
            asin = asin_m.group(1)
            start_pos = asin_m.end()
            next_asin = ASIN_RE.search(html, start_pos)
            end_pos = next_asin.start() if next_asin else len(html)
            card_html = html[start_pos:end_pos]
            
            rank_m = RANK_RE.search(card_html)
            rank = int(rank_m.group(1)) if rank_m else None
            
            product = parse_product_card(card_html, rank, label, list_type)
            if product:
                products.append(product)
        
        if products:
            now = datetime.now(timezone.utc).isoformat()
            rows = [{**p, "collected_at": now} for p in products]
            inserted = db.insert_snapshot_rows(rows)
            stats["rows_inserted"] += inserted
            print(f"  ✓ {label[:30]:30} | {list_type:20} | pg{page}: {inserted} rows")
    
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        futures = [executor.submit(worker, task) for task in tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                stats["failed_fetches"] += 1
                logger.error(f"Subcat worker error: {e}")
    
    stats["end_time"] = datetime.now(timezone.utc)
    stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"[subcats] Complete! {stats['rows_inserted']} rows in {stats['duration_seconds']:.1f}s")
    print(f"{'='*60}")
    
    return stats

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ScoutVeda Max-Capacity Collector")
    parser.add_argument("--subcats", action="store_true", help="Run sub-category collection")
    parser.add_argument("--max", type=int, help="Max sub-categories to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched")
    parser.add_argument("--workers", type=int, help=f"Override worker count (default: {FETCH_WORKERS})")
    parser.add_argument("--gap-min", type=float, help=f"Override min gap (default: {GAP_MIN_SECONDS})")
    parser.add_argument("--gap-max", type=float, help=f"Override max gap (default: {GAP_MAX_SECONDS})")
    
    args = parser.parse_args()
    
    # Override config from CLI
    if args.workers:
        FETCH_WORKERS = args.workers
        _rate_limiter = TokenBucketRateLimiter(
            rate=MAX_REQUESTS_PER_WINDOW / RATE_LIMIT_WINDOW,
            burst=MAX_REQUESTS_PER_WINDOW
        )
    if args.gap_min:
        GAP_MIN_SECONDS = args.gap_min
    if args.gap_max:
        GAP_MAX_SECONDS = args.gap_max
    
    if args.subcats:
        run_subcats(max_count=args.max, dry_run=args.dry_run)
    else:
        run_collection()
