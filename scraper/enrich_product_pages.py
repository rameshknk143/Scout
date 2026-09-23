"""
Product-page enrichment for top ASINs.

Designed to run AFTER the nightly broad collection, targeting the top-10 
ASINs per category/list_type that don't yet have rich fields populated.

Uses a HEADLESS BROWSER (Playwright) to bypass Amazon's bot wall on product pages.
Only works when run from a clean/residential IP (not datacenter).

Architecture:
- Fetch top-N unenriched ASINs from Supabase
- For each, fetch product page via Playwright (polite 4-8s gap)
- Extract brand, stock status, seller, dimensions, weight, material, warranty
- Upsert into snapshots table (same row, enriched fields)

To deploy: Install Playwright on ARM VM, run this as a third nightly session
or as a standalone cron job.
"""
import os
import re
import sys
import time
import random
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

# Import ontology for category-aware enrichment
import sys
sys.path.insert(0, str(Path(__file__).parent))
try:
    from ontology_engine import AmazonProductOntology, get_ontology
    ONTOLOGY = get_ontology()
except ImportError:
    ONTOLOGY = None

# Suppress Playwright warnings
os.environ["PLAYWRIGHT_LOG_LEVEL"] = "error"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Product page selectors
SELECTORS = {
    "title": "#productTitle",
    "brand": "[data-asin] + span.a-text-normal",  # Fallback
    "brand_path": 'a[href*="/品牌"] span',  # Hindi site fallback
    "price": ".a-price-whole",
    "rating": ".averageCustomerReviews",
    "reviews": ".totalReviewCountText",
    "stock": "#availability span",
    "seller": "#merchantInfoText",
    "dimensions": "#productDetails_divIdProductDescription li:has-text(\"Product Dimensions\")",
    "weight": "#productDetails_divIdProductDescription li:has-text(\"Item Weight\")",
}


def fetch_with_browser(page, asin, retries=2):
    """Fetch product page using Playwright browser."""
    url = f"https://www.amazon.in/dp/{asin}"
    for attempt in range(retries + 1):
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # Let JS render
            html = page.content()
            if len(html) > 100_000:  # Real product page
                return html
        except Exception as e:
            if attempt < retries:
                time.sleep(5 * (attempt + 1))
    return None


def parse_product_html(html, asin, category=None, subcategory=None):
    """Extract all available fields from product page HTML.
    
    Uses ontology to determine which category-specific attributes to extract.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    data = {"asin": asin}
    
    # Title
    title_el = soup.select_one("#productTitle")
    if title_el:
        data["title_enriched"] = title_el.get_text(strip=True)[:500]
    
    # Brand
    brand_el = soup.select_one('span.a-text-bold')
    if not brand_el:
        brand_el = soup.select_one('#bylineInfo')
    if brand_el:
        data["brand"] = brand_el.get_text(strip=True)[:100]
    
    # Price
    price_el = soup.select_one(".a-price-whole")
    if price_el:
        try:
            data["price"] = float(price_el.get_text().replace(",", ""))
        except ValueError:
            pass
    
    # Rating
    rating_el = soup.select_one(".averageCustomerReviews")
    if rating_el:
        m = re.search(r"([\d.]+)", rating_el.get_text())
        if m:
            try:
                data["rating"] = float(m.group(1))
            except ValueError:
                pass
    
    # Reviews
    review_el = soup.select_one(".totalReviewCountText")
    if review_el:
        m = re.search(r"([\d,]+)", review_el.get_text())
        if m:
            try:
                data["review_count"] = int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    
    # Stock
    stock_el = soup.select_one("#availability span")
    if stock_el:
        text = stock_el.get_text().lower()
        data["in_stock"] = 1 if "in stock" in text or "available" in text else 0
        data["availability_text"] = stock_el.get_text().strip()[:100]
    
    # Seller
    seller_el = soup.select_one("#merchantInfoText")
    if seller_el:
        data["seller"] = seller_el.get_text(strip=True)[:120]
    
    # Dimensions & Weight (from product details)
    details = soup.select("#productDetails_feature_div li")
    for li in details:
        text = li.get_text(strip=True)
        if "Product Dimensions" in text:
            data["dimensions"] = text.split(":", 1)[-1].strip()[:200]
        elif "Item Weight" in text:
            data["weight"] = text.split(":", 1)[-1].strip()[:100]
        elif "Material Type" in text:
            data["material"] = text.split(":", 1)[-1].strip()[:200]
    
    # Warranty
    warranty_text = soup.get_text()
    if "warranty" in warranty_text.lower():
        m = re.search(r"(?:warranty|guarantee)[^\.]*", warranty_text, re.I)
        if m:
            data["warranty"] = m.group(0)[:100]
    
    # Category-specific extraction using ontology
    if ONTOLOGY and category:
        schema = ONTOLOGY.get_schema(category, subcategory)
        for attr in schema.attributes:
            if attr.name in data:
                continue  # Already extracted
            
            # Try to extract based on attribute name patterns
            if attr.name == "ram":
                for li in details:
                    text = li.get_text(strip=True)
                    if "RAM" in text or "memory" in text.lower():
                        m = re.search(r"(\d+)\s*GB", text)
                        if m:
                            data["ram"] = f"{m.group(1)}GB"
                            break
            
            elif attr.name == "storage":
                for li in details:
                    text = li.get_text(strip=True)
                    if "storage" in text.lower() or "capacity" in text.lower():
                        m = re.search(r"(\d+)\s*(GB|TB)", text, re.I)
                        if m:
                            data["storage"] = f"{m.group(1)}{m.group(2)}"
                            break
            
            elif attr.name == "processor":
                for li in details:
                    text = li.get_text(strip=True)
                    if "processor" in text.lower() or "cpu" in text.lower():
                        data["processor"] = text.split(":", 1)[-1].strip()[:100]
                        break
            
            elif attr.name == "display_size":
                for li in details:
                    text = li.get_text(strip=True)
                    if "display" in text.lower() or "screen" in text.lower():
                        m = re.search(r"([\d.]+)\s*inch", text, re.I)
                        if m:
                            data["display_size"] = f"{m.group(1)} inch"
                            break
            
            elif attr.name == "battery_capacity":
                for li in details:
                    text = li.get_text(strip=True)
                    if "battery" in text.lower():
                        m = re.search(r"(\d+)\s*mAh", text, re.I)
                        if m:
                            data["battery_capacity"] = f"{m.group(1)}mAh"
                            break
            
            elif attr.name == "fabric" or attr.name == "material":
                # Already extracted above
                pass
            
            elif attr.name == "size" and subcategory:
                # Extract size from title or details
                for li in details:
                    text = li.get_text(strip=True)
                    if "size" in text.lower():
                        data["size"] = text.split(":", 1)[-1].strip()[:50]
                        break
    
    # Dynamic attribute discovery - register any new fields found
    if ONTOLOGY:
        for key, value in data.items():
            if key not in ONTOLOGY.attributes and value:
                # Auto-register new attribute
                from ontology_engine import AttributeSpec
                new_attr = AttributeSpec(
                    name=key,
                    data_type="string",
                    description=f"Discovered field: {key}",
                    tier=2,
                    source="product_page",
                    categories=[category] if category else [],
                    is_dynamic=True
                )
                ONTOLOGY.register_attribute(new_attr)
    
    return data


def get_top_unenriched(limit=50):
    """Query Supabase for top-N unenriched ASINs."""
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (category, list_type)
            asin, category, list_type, rank
        FROM snapshots
        WHERE (brand IS NULL OR brand = '')
          AND collected_at >= now() - interval '7 days'
        ORDER BY category, list_type, rank ASC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def upsert_enrichment(data):
    """Upsert enrichment fields into snapshots table."""
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("""
        UPDATE snapshots SET
            brand = COALESCE(%s, brand),
            bsr_rank = COALESCE(%s, bsr_rank),
            bsr_category = COALESCE(%s, bsr_category),
            in_stock = COALESCE(%s, in_stock),
            availability_text = COALESCE(%s, availability_text),
            seller = COALESCE(%s, seller),
            dimensions = COALESCE(%s, dimensions),
            weight = COALESCE(%s, weight),
            material = COALESCE(%s, material),
            warranty = COALESCE(%s, warranty)
        WHERE asin = %s
          AND collected_at = (
              SELECT MAX(collected_at) FROM snapshots s2
              WHERE s2.asin = %s
          )
    """, (
        data.get("brand"),
        data.get("bsr_rank"),
        data.get("bsr_category"),
        data.get("in_stock"),
        data.get("availability_text"),
        data.get("seller"),
        data.get("dimensions"),
        data.get("weight"),
        data.get("material"),
        data.get("warranty"),
        data["asin"],
        data["asin"],
    ))
    conn.commit()
    cur.close()
    conn.close()


def main():
    """Main enrichment flow."""
    print(f"[enrich] Starting product-page enrichment at {datetime.now(timezone.utc).isoformat()}")
    
    # Get targets
    targets = get_top_unenriched(limit=50)
    print(f"[enrich] Found {len(targets)} ASINs to enrich")
    
    if not targets:
        print("[enrich] Nothing to do")
        return
    
    # Use Playwright for browser-based fetching
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        enriched = 0
        failed = 0
        
        for i, row in enumerate(targets):
            asin, category, list_type, rank = row
            
            if rank is None or rank > 10:
                continue  # Only top-10
            
            print(f"  [{i+1}/{len(targets)}] Enriching {asin} (rank {rank}, {category})...")
            
            html = fetch_with_browser(page, asin)
            if not html:
                failed += 1
                print(f"    FAILED: could not fetch product page")
                time.sleep(random.uniform(4, 8))
                continue
            
            # Parse category to get subcategory
            subcategory = None
            if category and " > " in category:
                parts = category.split(" > ")
                if len(parts) > 1:
                    subcategory = parts[-1]
            
            data = parse_product_html(html, asin, category=category, subcategory=subcategory)
            if not data:
                failed += 1
                continue
            
            upsert_enrichment(data)
            enriched += 1
            print(f"    OK: brand={data.get('brand', 'N/A')[:30]}...")
            
            # Polite delay
            if i < len(targets) - 1:
                time.sleep(random.uniform(4, 8))
        
        browser.close()
    
    print(f"[enrich] Complete: {enriched} enriched, {failed} failed")


if __name__ == "__main__":
    if "DATABASE_URL" not in os.environ:
        print("ERROR: DATABASE_URL environment variable required")
        sys.exit(1)
    main()
