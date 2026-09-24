"""
Enrich top-ranked ASINs with product-page data.

After the main nightly collection lands ~8k snapshot rows, this script:
1. Queries the DB for "fresh" top-10 ASINs per category/list_type that
   don't yet have rich fields populated
2. Fetches each product's detail page (separate, polite — 4s gap)
3. Extracts additional fields: brand, stock status, seller, rank_category,
   dimensions, weight, material, warranty, bullet points, etc.
4. Writes enriched data back to the same snapshots table (upsert by
   (asin, category, list_type, collected_at))

Designed to run AFTER the main collector job in the same workflow night,
or as a standalone cron on the ARM VM.
"""
import os
import re
import sys
import time
import random
from datetime import datetime, timezone

import requests

# Reuse collector's patterns where possible
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}

# Product-page extractors
TITLE_RE = re.compile(r'id="productTitle"[^>]*value="([^"]+)"')
BRAND_RE = re.compile(r'"brand"\s*:\s*"([^"]+)"')
PRICE_RE = re.compile(r'"price"\s*:\s*\{\s*"symbol"\s*:\s*"₹"\s*,\s*"value"\s*:\s*"([\d,]+\.?\d*)"')
RATING_RE = re.compile(r'aria-label="([\d.]+) out of 5 stars')
REVIEW_RE = re.compile(r'(\d+(?:,\d+)*)\s+global ratings')
BSR_RE = re.compile(r'Best\s+Seller\s+Rank\s*#?(\d+)\sin\s+(\w(?:[\w\s\-]+))')
STOCK_RE = re.compile(r'"availability[^"]*"\s*:\s*"([^"]+)"')
SOLD_BY_RE = re.compile(r'Sold by\s+([^\n<"]+)')
DIM_RE = re.compile(r'Product Dimensions\s*:\s*([\d\.]+\s*(?:cm|inches?)\s*[×x]\s*[\d\.]+\s*(?:cm|inches?)\s*[×x]\s*[\d\.]+\s*(?:cm|inches?))', re.I)
WEIGHT_RE = re.compile(r'Item Weight\s*:\s*([\d\.]+\s*(?:g|kg|oz|lb))', re.I)
MATERIAL_RE = re.compile(r'Material Type\s*:\s*([^\n<]+)', re.I)
WARRANTY_RE = re.compile(r' Warranty\s*[:\-]\s*([^\n<]{3,100})', re.I)


def fetch_product_page(asin, retries=2):
    """Fetch a single Amazon product detail page."""
    url = f"https://www.amazon.in/dp/{asin}"
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25)
            resp.raise_for_status()
            html = resp.text
            # Verify it's a real product page (not bot wall)
            if len(html) > 50_000 and "automated access" not in html.lower():
                return html
        except Exception:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
    return None


def parse_product_page(html, asin):
    """Extract all available fields from a product page HTML block."""
    data = {"asin": asin}

    # Title
    m = TITLE_RE.search(html)
    if m:
        import html as html_mod
        data["title_enriched"] = html_mod.unescape(m.group(1).strip())

    # Brand
    m = BRAND_RE.search(html)
    if m:
        data["brand"] = m.group(1)

    # Price
    m = PRICE_RE.search(html)
    if m:
        try:
            data["price"] = float(m.group(1).replace(",", ""))
        except ValueError:
            pass

    # Rating & reviews
    m = RATING_RE.search(html)
    if m:
        try:
            data["rating"] = float(m.group(1))
        except ValueError:
            pass
    m = REVIEW_RE.search(html)
    if m:
        try:
            data["review_count"] = int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    # BSR
    m = BSR_RE.search(html)
    if m:
        try:
            data["bsr_rank"] = int(m.group(1))
            data["bsr_category"] = m.group(2).strip()
        except ValueError:
            pass

    # Stock status
    m = STOCK_RE.search(html)
    if m:
        avail = m.group(1).lower()
        data["in_stock"] = 1 if "in stock" in avail or "available" in avail else 0
        data["availability_text"] = m.group(1)[:100]

    # Seller
    m = SOLD_BY_RE.search(html)
    if m:
        seller = m.group(1).strip()
        if seller and len(seller) > 1:
            data["seller"] = seller[:120]

    # Dimensions
    m = DIM_RE.search(html)
    if m:
        data["dimensions"] = m.group(1).strip()

    # Weight
    m = WEIGHT_RE.search(html)
    if m:
        data["weight"] = m.group(1).strip()

    # Material
    m = MATERIAL_RE.search(html)
    if m:
        data["material"] = m.group(1).strip()[:200]

    # Warranty
    m = WARRANTY_RE.search(html)
    if m:
        data["warranty"] = m.group(1).strip()[:100]

    return data


def get_conn():
    """Get a Supabase connection."""
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn


def main():
    """Main enrichment flow."""
    print(f"[enrich] starting at {datetime.now(timezone.utc).isoformat()}")

    # Get top-10 unenriched ASINs per category/list_type
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (category, list_type)
            asin, category, list_type, rank, title, price, rating, review_count
        FROM snapshots
        WHERE (brand IS NULL OR brand = '')
          AND collected_at >= now() - interval '7 days'
        ORDER BY category, list_type, rank ASC
        LIMIT 300
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"[enrich] found {len(rows)} unenriched top-10 ASINs to process")

    enriched = 0
    failed = 0
    for i, row in enumerate(rows):
        asin, category, list_type, rank, title, price, rating, review_count = row

        if rank is None or rank > 10:
            continue  # only enrich top-10

        html = fetch_product_page(asin)
        if not html:
            failed += 1
            print(f"  [FAIL] {asin} [{category}] product page unreachable")
            time.sleep(random.uniform(4, 8))
            continue

        data = parse_product_page(html, asin)
        if not data:
            failed += 1
            continue

        # Write enrichment back (upsert)
        conn = get_conn()
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
              AND category = %s
              AND list_type = %s
              AND collected_at = (SELECT MAX(collected_at) FROM snapshots s2
                                 WHERE s2.asin = %s AND s2.category = %s AND s2.list_type = %s)
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
            asin, category, list_type, asin, category, list_type
        ))
        conn.commit()
        cur.close()
        conn.close()

        enriched += 1
        if enriched % 10 == 0:
            print(f"  progress: {enriched}/{len(rows)} enriched, {failed} failed")

        # Polite delay between product page fetches
        time.sleep(random.uniform(4, 8))

    print(f"[enrich] done: {enriched} enriched, {failed} failed out of {len(rows)} targets")


if __name__ == "__main__":
    main()
