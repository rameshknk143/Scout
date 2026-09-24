"""
Watchlist Deep Scraper — Collects detailed product data for tracked ASINs.

Scrapes product pages for specific ASINs (watchlist) to enrich existing
records with detailed specs, reviews, Q&A, and competitive intelligence.

Usage:
    python watchlist_scrape.py              # Scrape all watchlist ASINs
    python watchlist_scrape.py --asin B08X  # Scrape specific ASIN
    python watchlist_scrape.py --days 7     # Only ASINs from last 7 days
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import db
from registry.attribute_registry import DataStatus, default_registry
from registry.category_mapper import CategoryMapper

# Configuration
MAX_CONCURRENT = int(os.environ.get("WATCHLIST_CONCURRENT", "5"))
REQUEST_TIMEOUT = int(os.environ.get("WATCHLIST_TIMEOUT", "30"))
DELAY_BETWEEN_REQUESTS = float(os.environ.get("WATCHLIST_DELAY", "2.0"))

# Optional egress proxy (same knob as collector_optimized.py). When set,
# all watchlist fetches route through it — e.g. a residential proxy, which
# unblocks datacenter-IP egress that Amazon bot-walls. No-op when unset.
PROXY_URL = os.environ.get("SCOUT_PROXY", "").strip()
def _proxies_dict():
    if not PROXY_URL:
        return None
    return {"http": PROXY_URL, "https": PROXY_URL}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Selectors for product page extraction
SELECTORS = {
    "title": "#productTitle",
    "brand": "#bylineInfo span.a-text-normal",
    "price_whole": ".a-price-whole",
    "price_fraction": ".a-price-fraction",
    "rating": ".averageCustomerReviews span",
    "review_count": ".totalReviewCountText",
    "stock": "#availability span",
    "seller": "#merchantInfoText",
    "dimensions": "#productDetails_divIdProductDescription li:has-text('Product Dimensions')",
    "weight": "#productDetails_divIdProductDescription li:has-text('Item Weight')",
    "material": "#productDetails_divIdProductDescription li:has-text('Material Type')",
    "warranty": "#productDetails_divIdProductDescription li:has-text('Warranty')",
    "first_available": "#detailBulletsWrapper_featuredivision li:has-text('Date First Available')",
}

# Regex patterns
PRICE_RE = re.compile(r'₹([\d,]+(?:\.\d{2})?)')
RATING_RE = re.compile(r'([0-5](?:\.\d+)?)')
REVIEW_COUNT_RE = re.compile(r'([\d,]+)')


def fetch_product_page(asin: str, retries: int = 3) -> tuple[bool, str]:
    """Fetch product page HTML with retry logic."""
    url = f"https://www.amazon.in/dp/{asin}"
    proxies = _proxies_dict()
    
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                proxies=proxies,
            )
            
            if resp.status_code == 200 and len(resp.content) > 50000:
                return True, resp.text
            
            # Check for bot detection
            if b"captcha" in resp.content.lower() or b"robot" in resp.content.lower():
                print(f"  ⚠ Bot detection on {asin}, backing off...")
                time.sleep(10 * (attempt + 1))
                continue
            
            print(f"  ⚠ HTTP {resp.status_code} for {asin}, retry {attempt+1}/{retries}")
            time.sleep(2 * (attempt + 1))
            
        except requests.exceptions.Timeout:
            print(f"  ⏱ Timeout on {asin}, retry {attempt+1}/{retries}")
            time.sleep(3 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error on {asin}: {type(e).__name__}")
            if attempt < retries - 1:
                time.sleep(2)
    
    return False, ""


def parse_product_page(html: str, asin: str) -> dict:
    """Extract all available fields from product page."""
    soup = BeautifulSoup(html, 'html.parser')
    data = {"asin": asin}
    
    # Title
    title_el = soup.select_one("#productTitle")
    if title_el:
        data["title"] = title_el.get_text(strip=True)[:500]
    
    # Brand
    brand_el = soup.select_one("#bylineInfo span.a-text-normal")
    if not brand_el:
        brand_el = soup.select_one('span.a-text-bold')
    if brand_el:
        data["brand"] = brand_el.get_text(strip=True)[:100]
    
    # Price
    price_el = soup.select_one(".a-price-whole")
    if price_el:
        try:
            price_str = price_el.get_text().replace(",", "")
            fraction_el = soup.select_one(".a-price-fraction")
            fraction = fraction_el.get_text() if fraction_el else "00"
            data["price"] = float(f"{price_str}.{fraction}")
        except ValueError:
            pass
    
    # Rating & Reviews
    rating_el = soup.select_one(".averageCustomerReviews span")
    if rating_el:
        m = RATING_RE.search(rating_el.get_text())
        if m:
            data["rating"] = float(m.group(1))
    
    reviews_el = soup.select_one(".totalReviewCountText")
    if reviews_el:
        m = REVIEW_COUNT_RE.search(reviews_el.get_text())
        if m:
            data["review_count"] = int(m.group(1).replace(",", ""))
    
    # Stock status
    stock_el = soup.select_one("#availability span")
    if stock_el:
        text = stock_el.get_text().lower()
        data["in_stock"] = 1 if "in stock" in text or "available" in text else 0
        data["availability_text"] = stock_el.get_text().strip()[:100]
    
    # Seller
    seller_el = soup.select_one("#merchantInfoText")
    if seller_el:
        data["seller"] = seller_el.get_text(strip=True)[:120]
        data["fulfillment"] = "FBA" if "Ships from and sold by Amazon" in seller_el.get_text() else "FBM"
    
    # Product details
    details = soup.select("#productDetails_feature_div li")
    for li in details:
        text = li.get_text(strip=True)
        if "Product Dimensions" in text:
            data["dimensions"] = text.split(":", 1)[-1].strip()[:200]
        elif "Item Weight" in text:
            data["weight"] = text.split(":", 1)[-1].strip()[:100]
        elif "Material Type" in text:
            data["material"] = text.split(":", 1)[-1].strip()[:200]
        elif "Warranty" in text or "Guarantee" in text:
            data["warranty"] = text.split(":", 1)[-1].strip()[:100]
        elif "Date First Available" in text:
            date_text = text.split(":", 1)[-1].strip()
            data["first_available_date"] = date_text
    
    # Categories from page
    breadcrumb = soup.select_one("#breadcrumb li:last-child")
    if breadcrumb:
        data["category_path"] = breadcrumb.get_text(strip=True)
    
    # Use ontology to determine schema
    mapper = CategoryMapper()
    category = data.get("category_path", "Unknown")
    mapped = mapper.map(asin, data.get("title"), category)
    data["subcategory"] = mapped.get("subcategory")
    data["product_type"] = mapped.get("product_type")
    
    # Extract additional attributes based on category
    if mapped.get("category") == "Electronics":
        _extract_electronics_attrs(data, soup)
    elif mapped.get("category") == "Fashion":
        _extract_fashion_attrs(data, soup)
    elif mapped.get("category") == "Grocery":
        _extract_grocery_attrs(data, soup)
    
    return data


def _extract_electronics_attrs(data: dict, soup: BeautifulSoup):
    """Extract electronics-specific attributes."""
    details = soup.select("#productDetails_feature_div li")
    for li in details:
        text = li.get_text(strip=True)
        
        # RAM
        if "RAM" in text or "Memory" in text:
            m = re.search(r'(\d+)\s*GB', text, re.I)
            if m:
                data["ram"] = f"{m.group(1)}GB"
        
        # Storage
        elif "Storage" in text or "Capacity" in text:
            m = re.search(r'(\d+)\s*(GB|TB)', text, re.I)
            if m:
                data["storage"] = f"{m.group(1)}{m.group(2)}"
        
        # Processor
        elif "Processor" in text or "CPU" in text:
            data["processor"] = text.split(":", 1)[-1].strip()[:100]
        
        # Display
        elif "Display" in text or "Screen" in text:
            m = re.search(r'([\d.]+)\s*inch', text, re.I)
            if m:
                data["display_size"] = f"{m.group(1)} inch"
        
        # Battery
        elif "Battery" in text:
            m = re.search(r'(\d+)\s*mAh', text, re.I)
            if m:
                data["battery_capacity"] = f"{m.group(1)}mAh"
        
        # Camera
        elif "Camera" in text or "Pixel" in text:
            m = re.search(r'(\d+)\s*MP', text, re.I)
            if m:
                data["camera_mp"] = f"{m.group(1)}MP"
    
    # Check for wireless/noise cancellation in title
    title = data.get("title", "").lower()
    if "wireless" in title or "bluetooth" in title:
        data["wireless"] = True
    if "noise cancelling" in title or "anc" in title:
        data["noise_cancellation"] = True


def _extract_fashion_attrs(data: dict, soup: BeautifulSoup):
    """Extract fashion-specific attributes."""
    details = soup.select("#productDetails_feature_div li")
    for li in details:
        text = li.get_text(strip=True)
        
        if "Material" in text or "Fabric" in text:
            data["fabric"] = text.split(":", 1)[-1].strip()[:200]
        elif "Size" in text and "Available" in text:
            data["size_options"] = text.split(":", 1)[-1].strip()[:100]
        elif "Pattern" in text:
            data["pattern"] = text.split(":", 1)[-1].strip()[:100]
        elif "Fit" in text:
            data["fit"] = text.split(":", 1)[-1].strip()[:50]


def _extract_grocery_attrs(data: dict, soup: BeautifulSoup):
    """Extract grocery-specific attributes."""
    details = soup.select("#productDetails_feature_div li")
    for li in details:
        text = li.get_text(strip=True)
        
        if "Net Weight" in text or "Quantity" in text:
            data["net_weight"] = text.split(":", 1)[-1].strip()[:100]
        elif "Ingredients" in text:
            data["ingredients"] = text.split(":", 1)[-1].strip()[:500]
        elif "Vegetarian" in text or "Non-Vegetarian" in text:
            data["vegetarian"] = "Yes" in text or "Vegetarian" in text


def get_watchlist_asins(days: int = None) -> list:
    """Get ASINs from watchlist or recent unenriched records."""
    conn = db.get_conn()
    cur = conn.cursor()
    
    if days:
        cur.execute("""
            SELECT DISTINCT asin, category, title 
            FROM snapshots 
            WHERE collected_at >= now() - interval '%s days'
            ORDER BY collected_at DESC
        """, (days,))
    else:
        # Get ASINs that need enrichment (missing key fields)
        cur.execute("""
            SELECT DISTINCT ON (asin) asin, category, title
            FROM snapshots
            WHERE brand IS NULL OR subcategory IS NULL
            ORDER BY asin, collected_at DESC
            LIMIT 100
        """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{"asin": r[0], "category": r[1], "title": r[2]} for r in rows]


def upsert_enrichment(data: dict):
    """Upsert enrichment data into snapshots table."""
    conn = db.get_conn()
    cur = conn.cursor()
    
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
            ingredients = COALESCE(%s, ingredients),
            enriched_at = now()
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
    
    conn.commit()
    cur.close()
    conn.close()


def main():
    """Main watchlist scraping loop."""
    print(f"[watchlist] Starting deep scrape at {datetime.now(timezone.utc).isoformat()}")
    
    # Get ASINs to process
    asin_list = get_watchlist_asins(days=7)
    print(f"[watchlist] Found {len(asin_list)} ASINs to enrich")
    
    if not asin_list:
        print("[watchlist] Nothing to do")
        return
    
    stats = {
        "total": len(asin_list),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "start_time": datetime.now(timezone.utc),
    }
    
    # Process with concurrency limit
    import asyncio
    
    async def process_async():
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def process_one(item):
            async with semaphore:
                asin = item["asin"]
                print(f"  [{stats['success'] + stats['failed'] + 1}/{stats['total']}] Processing {asin}...")
                
                # Fetch page
                success, html = await asyncio.to_thread(fetch_product_page, asin)
                
                if not success:
                    stats["failed"] += 1
                    return
                
                # Parse data
                data = await asyncio.to_thread(parse_product_page, html, asin)
                
                # Upsert
                await asyncio.to_thread(upsert_enrichment, data)
                
                stats["success"] += 1
                print(f"    ✓ Enriched: {data.get('brand', 'N/A')} | {data.get('subcategory', 'N/A')}")
                
                # Delay to be polite
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        tasks = [process_one(item) for item in asin_list]
        await asyncio.gather(*tasks)
    
    # Run async loop
    asyncio.run(process_async())
    
    # Summary
    duration = (datetime.now(timezone.utc) - stats["start_time"]).total_seconds()
    print(f"\n{'='*60}")
    print(f"[watchlist] Complete!")
    print(f"[watchlist] Duration: {duration:.1f}s")
    print(f"[watchlist] Success: {stats['success']}/{stats['total']}")
    print(f"[watchlist] Failed: {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, help="Only process ASINs from last N days")
    parser.add_argument("--asin", type=str, help="Process specific ASIN")
    args = parser.parse_args()
    
    if args.asin:
        # Single ASIN mode
        asin_list = [{"asin": args.asin, "category": "Unknown", "title": ""}]
    else:
        asin_list = get_watchlist_asins(days=args.days)
    
    if asin_list:
        main()
    else:
        print("[watchlist] No ASINs to process")
