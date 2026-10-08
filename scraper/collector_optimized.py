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
    ProxyHandler,
    Request,
    build_opener,
)

import db
from registry.attribute_registry import DataStatus, default_registry
from registry.category_mapper import CategoryMapper

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
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Concurrency settings — OPTIMIZED FOR SAFE THROUGHPUT
FETCH_WORKERS = max(1, int(os.environ.get("SCOUT_FETCH_WORKERS", "12")))
GAP_MIN_SECONDS = float(os.environ.get("SCOUT_GAP_MIN", "4"))
GAP_MAX_SECONDS = float(os.environ.get("SCOUT_GAP_MAX", "10"))

# Retry settings
MAX_RETRIES = int(os.environ.get("SCOUT_MAX_RETRIES", "2"))
RETRY_BACKOFF_BASE = float(os.environ.get("SCOUT_RETRY_BACKOFF", "2.0"))
REQUEST_TIMEOUT = int(os.environ.get("SCOUT_REQUEST_TIMEOUT", "30"))

# Rate limiting — COMPLIANT WITH AMAZON SAFETY GUIDELINES
# Conservative: 60 req/min (1 req/sec) = Safe zone, undetectable
# Aggressive: 90-120 req/min (1.5-2 req/sec) = Moderate risk
MIN_REQUEST_INTERVAL = float(os.environ.get("SCOUT_MIN_INTERVAL", "0.8"))
RATE_LIMIT_WINDOW = int(os.environ.get("SCOUT_RATE_LIMIT_WINDOW", "60"))
MAX_REQUESTS_PER_WINDOW = int(os.environ.get("SCOUT_MAX_REQUESTS_PER_WINDOW", "60"))  # SAFE: 1 req/sec

# Residential / SOCKS proxy — routes the (datacenter) GitHub/VM egress IP through
# a residential address so Amazon serves real product HTML instead of the empty
# bot-walled page. This is what removes the laptop dependency: the laptop works
# today ONLY because its home IP is residential. With SCOUT_PROXY set, the cloud
# collector gets the same advantage without the laptop being on.
#
# Supported forms (all read from the env below, injected by the workflow secrets):
#   http://host:port                      (residential HTTP/HTTPS proxy)
#   https://user:pass@host:port          (authenticated)
#   socks5://host:port  /  socks5h://…   (SOCKS; needs PySocks, else falls back to
#                                          raw urllib which does NOT speak SOCKS —
#                                          use an HTTP proxy for the collector)
PROXY_URL = os.environ.get("SCOUT_PROXY", "").strip()

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
    burst=1
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
    handlers = [HTTPSHandler()]
    if PROXY_URL:
        # HTTP(S) proxies work with the stdlib; SOCKS would need PySocks and
        # the collector is deliberately dependency-light, so warn if given.
        if PROXY_URL.lower().startswith("socks"):
            logger.warning("[collector] SCOUT_PROXY is SOCKS (%s…) — stdlib urllib "
                           "cannot speak SOCKS; using the direct connection. "
                           "Set an http:// proxy to route egress.", "[configured]")
        else:
            proxy_handler = ProxyHandler({"http": PROXY_URL, "https": PROXY_URL})
            handlers.append(proxy_handler)
            logger.info("[collector] routing egress through proxy %s", "[configured]")
    handlers.append(cookie_processor)
    return build_opener(*handlers)

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
            _rate_limiter.wait()
            # Apply the advertised per-worker pacing; the limiter caps the total.
            time.sleep(random.uniform(GAP_MIN_SECONDS, GAP_MAX_SECONDS))
            
            # Build request
            req = Request(url, headers=HEADERS)
            req.add_header("Accept-Encoding", "gzip, deflate")
            req.add_header("Cache-Control", "no-cache")
            
            # Execute with timeout
            start = time.time()
            response = (session or _opener).open(req, timeout=REQUEST_TIMEOUT)
            elapsed = time.time() - start
            
            # Read content
            try:
                html = response.read()
            finally:
                response.close()
            
            # Handle compression
            content_encoding = response.headers.get("Content-Encoding", "")
            if "gzip" in content_encoding:
                import gzip
                html = gzip.decompress(html)
            elif "deflate" in content_encoding:
                import zlib
                try:
                    html = zlib.decompress(html)
                except zlib.error:
                    html = zlib.decompress(html, -zlib.MAX_WBITS)
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

# The weekly rotation engine feeds scrape_category() category names pulled
# from the live snapshots table, which uses short forms ("Sports", "Music",
# "Books") that don't match the CATEGORIES keys verbatim ("Sports & Fitness").
# This alias map bridges the two so the weekly cycle can actually scrape the
# categories it was assigned. Unknown names still fall back to _slugify().
_CATEGORY_SLUG_ALIASES = {
    "Sports": "sports",
    "Fitness": "sports",
    "Electronics": "electronics",
    "Computers": "computers",
    "Laptops": "computers",
    "Mobiles & Tablets": "mobiles",
    "Mobiles": "mobiles",
    "Tablets": "mobiles",
    "Headphones": "electronics",
    "Camera": "photo",
    "Home": "kitchen",
    "Kitchen": "kitchen",
    "Furniture": "kitchen",
    "Appliances": "appliances",
    "Home Appliances": "appliances",
    "Beauty": "beauty",
    "Cosmetics": "beauty",
    "Skincare": "beauty",
    "Hair Care": "beauty",
    "Personal Care": "hpc",
    "Health": "hpc",
    "Pharmacy": "hpc",
    "Grocery": "grocery",
    "Food": "grocery",
    "Gourmet": "grocery",
    "Pet": "pet-supplies",
    "Car": "automotive",
    "Automotive": "automotive",
    "Garden": "garden",
    "Outdoors": "garden",
    "Baby": "baby",
    "Toys": "toys",
    "Games": "toys",
    "Clothing": "apparel",
    "Apparel": "apparel",
    "Fashion": "apparel",
    "Shoes": "shoes",
    "Footwear": "shoes",
    "Handbags": "shoes",
    "Bags": "luggage",
    "Watches": "watches",
    "Jewellery": "jewelry",
    "Jewelry": "jewelry",
    "Jewelry & Watches": "watches",
    "Music": "music",
    "Instrument": "musical-instruments",
    "Instruments": "musical-instruments",
    "Movies": "dvd",
    "TV Shows": "dvd",
    "Software": "software",
    "Video Games": "videogames",
    "Gaming": "videogames",
    "Apps": "mobile-apps",
    "Home Improvement": "home-improvement",
    "Tools": "industrial",
    "Industrial": "industrial",
    "Stationery": "office",
    "Office": "office",
    "Office Supplies": "office",
    "Stationery/Office": "office",
}


def _slugify(name: str) -> str:
    """Best-effort slug for a category name with no known mapping.

    'Sports & Fitness' -> 'sports-fitness'. A wrong slug just produces a
    counted fetch failure in the runner; it never crashes the weekly cycle.
    """
    s = re.sub(r'[^a-z0-9&]+', '-', name.lower()).strip('-')
    s = s.replace('&', '-').replace('--', '-').strip('-')
    return s or "unknown"

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
    """Extract brand from an Amazon URL or product-link slug.

    The input can be a full URL OR a raw card's HTML: BRAND_URL_RE just
    locates the first '/<Slug>/dp/' link wherever it appears. Passing the
    card HTML is what makes brand extraction work (see _extract_brand_from_card).
    """
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

def _extract_brand_from_card(card_html: str) -> Optional[str]:
    """Extract the brand from the card's REAL product-link slug.

    A bestseller card contains a genuine link like
    '/Portronics-Earphones-.../dp/B0DDHM6D3L/...'. The old code
    reconstructed a bare 'https://www.amazon.in/dp/{asin}' URL with NO
    slug, so _extract_brand() returned None and the brand column stayed
    NULL for most rows (the 27.7% gap). Passing the card HTML lets
    BRAND_URL_RE find the real slug.
    """
    if not card_html:
        return None
    return _extract_brand(card_html)

def _extract_brand_from_title(title: str) -> Optional[str]:
    """Extract brand from product title using known brand patterns."""
    if not title:
        return None
    
    # Common Indian brands (prioritized)
    KNOWN_BRANDS = [
        'boAt', 'Noise', 'Portronics', 'Porter', 'Philips', 'Sony', 'Samsung',
        'LG', 'Apple', 'Xiaomi', 'Realme', 'OnePlus', 'Poco', 'Redmi',
        'Nike', 'Adidas', 'Puma', 'US Polo', 'Allen Solly', 'Roadster',
        'Only', 'Van Heusen', 'Arrow', 'H&M', 'Zara', 'Levi\'s', 'Wrangler',
        'Nivea', 'Dove', 'Lakme', 'Maybelline', 'The Body Shop',
        'Bajaj', 'Whirlpool', 'Godrej', 'IFB', 'Haier', 'Morphy Richards',
        'Milton', 'Havells', 'Brompton', 'Amaron', 'Kent', 'Eureka Forbes',
        'Prestige', 'Butterfly', 'AGARO', 'Wakefit', 'Sleepwell', 'Duroflex',
        'Campus', 'Reebok', 'Fila', 'Sparx', 'Crocs', 'Bata', 'Clarks',
        'Titan', 'Tanishq', 'CaratLane', 'Malabar', 'Kalyan',
        'Amul', 'Nestle', 'Cadbury', 'Parle', 'Britannia',
        'Horlicks', 'Boost', 'Bournvita', 'Vimal', 'Fortune', 'Saffola',
        'TATA', 'Colgate', 'Patanjali', 'Dabur', 'Himalaya',
        'Curology', 'Minimalist', 'The Ordinary', 'Plum', 'Biotique',
        'Ugaoo', 'Mamaearth', 'Wow Skin Science', 'Fixderma',
        'Dr. Sheths', 'Dot & Key', 'Neutrogena', 'Garnier',
    ]
    
    title_lower = title.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in title_lower:
            return brand
    
    # Fallback: first capitalized word
    words = title.split()
    if words:
        first = words[0]
        if first[0].isupper() and len(first) > 2 and first.isalpha():
            if first.lower() not in ('The', 'New', 'Best', 'Premium', 'Original'):
                return first
    
    return None

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
    m = PRODUCT_TYPE_RE.search(title)
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
    
    # Map category using ontology (top-level label now enriched with a
    # title-inferred subcategory/product_type — see CategoryMapper.map)
    mapped = _mapper.map(asin, title, category)
    
    # Brand: prefer a known-brand match in the title (cleanest), then the
    # card's real product-link slug (the old bare /dp/{asin} URL had no
    # slug, so this returned None and the brand column stayed NULL).
    brand = _extract_brand_from_title(title) or _extract_brand_from_card(html)
    
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
        "brand": brand,
        "size_tier_hint": _detect_size_tier(title),
        "product_type_hint": _detect_product_type(title, category),
        "source": "collector",
    }

# ============================================================
# MAIN COLLECTION LOGIC
# ============================================================

def fetch_list_page(category: str, slug: str, list_type: str, page: int, session=None) -> Optional[str]:
    """Fetch a single bestseller list page."""
    path = LIST_TYPES[list_type]
    url = BASE_URL.format(path=path, slug=slug)
    if page > 1:
        url += f"?pg={page}"
    
    return fetch_with_retry(url, session=session)

def _run_tasks_with_stats(stats: dict, tasks: list, prefix: str = "collector") -> dict:
    """Fetch on workers; account and write on the main thread."""
    for key in ("total_requests", "successful_fetches", "failed_fetches",
                "rows_inserted", "rows_skipped_dupe", "rows_parsed",
                "parse_failures", "storage_errors"):
        stats.setdefault(key, 0)
    stats.setdefault("errors", [])
    # Pages in one logical list capture must have the same replay identity.
    observed_at = stats["start_time"].isoformat()

    def worker(task):
        label, slug, list_type, page = task
        url = BASE_URL.format(path=LIST_TYPES[list_type], slug=slug)
        if page > 1:
            url += f"?pg={page}"
        page_html = fetch_with_retry(url)
        if not page_html:
            return task, None
        products = []
        matches = list(ASIN_RE.finditer(page_html))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(page_html)
            card = page_html[match.start():end]
            rank_match = RANK_RE.search(card)
            rank = int(rank_match.group(1)) if rank_match else None
            product = parse_product_card(card, rank, label, list_type)
            if product and product.get("title"):
                products.append({**product, "collected_at": observed_at})
        return task, products

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        futures = {executor.submit(worker, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            stats["total_requests"] += 1
            try:
                _, rows = future.result()
            except Exception as exc:
                stats["parse_failures"] += 1
                stats["errors"].append(f"{task}: fetch_or_parse_error:{type(exc).__name__}")
                continue
            if rows is None:
                stats["failed_fetches"] += 1
                continue
            stats["successful_fetches"] += 1
            stats["rows_parsed"] += len(rows)
            if not rows:
                stats["parse_failures"] += 1
                stats["errors"].append(f"{task}: no_valid_cards")
                continue
            try:
                inserted = db.insert_snapshot_rows(rows)
            except Exception as exc:
                stats["storage_errors"] += 1
                stats["errors"].append(f"{task}: storage_error:{type(exc).__name__}")
                logger.error("%s storage failed: %s", prefix, type(exc).__name__)
                continue
            stats["rows_inserted"] += inserted
            stats["rows_skipped_dupe"] += len(rows) - inserted
            if inserted and "categories_processed" in stats:
                stats["categories_processed"].append(f"{task[0]}/{task[2]}/pg{task[3]}: {inserted} rows")
    stats["end_time"] = datetime.now(timezone.utc)
    stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    stats["suspected_bot_wall"] = (stats["successful_fetches"] > 0
                                   and stats["rows_parsed"] == 0)
    stats["failed_tasks"] = (stats["failed_fetches"] + stats["parse_failures"]
                             + stats["storage_errors"])
    print(f"[{prefix}] {len(tasks)} tasks; parsed={stats['rows_parsed']} "
          f"inserted={stats['rows_inserted']} failed={stats['failed_tasks']}")
    return stats


def run_collection(clear_db: bool = False, dry_run: bool = False) -> dict:
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
    
    return stats if dry_run else _run_tasks_with_stats(stats, tasks, "collector")

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
    
    if dry_run:
        return stats
    
    return _run_tasks_with_stats(stats, tasks, "subcats")

def scrape_category(category: str, pages: int = 2,
                   list_types: list = None) -> dict:
    """Bounded single-category collection — the entry point the weekly
    rotation engine uses instead of the all-collections run_collection().

    Fetches the given list pages for ONE category only, inserts the parsed
    snapshot rows via the shared runner (db.insert_snapshot_rows), and
    returns a flat stats dict shaped for rotation_engine._scrape_category():
    total_tasks, rows_inserted, failed, rows_parsed, requests_made,
    suspected_bot_wall, duration_seconds.
    """
    list_types = list_types or ["bestsellers"]
    if any(lt not in LIST_TYPES for lt in list_types):
        raise ValueError("Unknown list type")

    # Resolve the category to a browse slug. The rotation engine feeds this
    # category names pulled from the live snapshots table (53 of them, e.g.
    # "Sports", "Music"), which do not always match the CATEGORIES dict keys
    # verbatim ("Sports & Fitness"). Previously an unknown name raised
    # ValueError here, so the whole weekly cycle failed on nearly every
    # category and added zero rows. Now: known map -> alias map -> a
    # best-effort slugified name (a bad slug just yields a counted fetch
    # failure, never a crash).
    targets = {**CATEGORIES, **load_subcats()}
    if category in targets:
        slug = targets[category]
    elif category in _CATEGORY_SLUG_ALIASES:
        slug = _CATEGORY_SLUG_ALIASES[category]
        logger.info("[scrape_category] %r resolved via alias -> %r", category, slug)
    else:
        slug = _slugify(category)
        logger.warning(
            "[scrape_category] %r not in CATEGORIES/subcats/aliases; "
            "using derived slug %r (best effort).", category, slug)

    page_list = tuple(range(1, max(1, pages) + 1))
    tasks = [
        (category, slug, lt, pg)
        for lt in list_types
        if lt in LIST_TYPES
        for pg in page_list
    ]

    logger.info("[scrape_category] %s: %d list pages (types=%s)",
                category, len(tasks), list(list_types))

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
    _run_tasks_with_stats(stats, tasks, f"scrape:{category[:20]}")

    return {
        "category": category,
        "total_tasks": len(tasks),
        "rows_inserted": stats.get("rows_inserted", 0),
        "rows_parsed": stats.get("rows_parsed", 0),
        "failed": stats.get("failed_tasks", 0),
        "requests_made": stats.get("total_requests", 0),
        "suspected_bot_wall": stats.get("suspected_bot_wall", False),
        "duration_seconds": stats.get("duration_seconds", 0.0),
    }

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
            burst=1
        )
    if args.gap_min:
        GAP_MIN_SECONDS = args.gap_min
    if args.gap_max:
        GAP_MAX_SECONDS = args.gap_max
    
    if args.subcats:
        stats = run_subcats(max_count=args.max, dry_run=args.dry_run)
    else:
        stats = run_collection(dry_run=args.dry_run)

    # ---- Auto-stealth retry ------------------------------------------------
    # Evidence (25 Sep): the 12-worker/4-10s-gap burst gets bot-walled (248
    # fetches, 0 rows) while the 4-worker/20-45s-gap nightly pass lands
    # thousands of rows from the SAME datacenter IPs. Amazon walls the burst,
    # not just the IP class. So when a fast pass comes back walled, re-run it
    # with the nightly-proven stealth pacing before declaring failure.
    #
    # Guarded by SCOUT_AUTO_STEALTH (default on). Skipped for dry runs,
    # explicit CLI pacing, and large subcat lists (stealth would overrun the
    # job timeout). Dedupe is ON-CONFLICT-based, so a retry that lands rows
    # costs no duplicates.
    auto_stealth = os.environ.get("SCOUT_AUTO_STEALTH", "1") != "0"
    stealth_done = os.environ.get("_SCOUT_STEALTH_DONE") == "1"
    explicit_pacing = bool(args.workers or args.gap_min or args.gap_max)

    if (not args.dry_run and stats and stats.get("suspected_bot_wall")
            and auto_stealth and not stealth_done and not explicit_pacing):
        # Only top-level (248 tasks) is small enough to finish at stealth
        # pacing inside the 50-min job timeout; a 1528-task subcat pass
        # would not, and the nightly already covers it.
        total_tasks = 31 * 4 * 2  # cats × lists × pages, matches CATEGORIES
        if stats["total_requests"] <= total_tasks * 1.2:
            print("\n[collector] Bot-walled on fast pacing. Auto-retrying in "
                  "stealth mode: 4 workers, 30 req/min rate cap.")
            # Module-level scope: these assignments update the module globals
            # that run_collection()/fetch_with_retry() read at call time.
            FETCH_WORKERS = 4
            GAP_MIN_SECONDS = 20.0
            GAP_MAX_SECONDS = 45.0
            os.environ["_SCOUT_STEALTH_DONE"] = "1"
            _rate_limiter = TokenBucketRateLimiter(rate=30 / RATE_LIMIT_WINDOW, burst=1)
            if args.subcats:
                stats = run_subcats(max_count=args.max, dry_run=False)
            else:
                stats = run_collection()

    # A run where every fetch "succeeded" but 0 rows parsed means Amazon is
    # bot-walling the egress IP — not a dedup, not a code bug. Exit 3 (distinct
    # from the usual 1) so the workflow can alert and the log says WHY, instead
    # of showing a green "success" that hides the drop.
    if not args.dry_run and stats and stats.get("suspected_bot_wall"):
        print("\n[collector] EXIT 3: suspected bot-wall (fetches succeeded, 0 rows parsed).", file=sys.stderr)
        print("[collector] Set SCOUT_PROXY to a residential proxy to unblock "
              "datacenter IPs at full speed.", file=sys.stderr)
        sys.exit(3)

    if not args.dry_run and stats:
        if stats.get("storage_errors"):
            sys.exit(2)
        if stats.get("failed_fetches") and not stats.get("rows_parsed"):
            sys.exit(1)
