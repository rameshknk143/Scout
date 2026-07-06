"""
Scout's nightly collector. Fetches amazon.in Best Sellers pages for a fixed
list of broad-discovery categories, parses each product card, and writes one
snapshot row per product into the database (via db.insert_snapshot_rows).

Cloud version: runs via GitHub Actions on a schedule, writing to Supabase
Postgres instead of a local SQLite file. Logic is unchanged from the original
laptop version — only db.py's connection layer changed.

Run manually:  python collector.py
Run for one category only (debugging):  python collector.py electronics

Design notes (see BLUEPRINT / plan for full context):
- v1 covers Best Sellers only. Movers & Shakers / New Releases / Most Wished
  For / Most Gifted are a deliberate follow-up, not an oversight.
- Amazon's CSS classes are hashed/versioned (e.g. "_cDEzb_..._3mJ9Z") and
  likely change on redeploys, so parsing matches stable substrings/attributes
  instead: zg-bdg-text (rank), data-asin (asin), p13n-sc-css-line-clamp
  (title), the "X out of 5 stars, Y ratings" aria-label (rating+reviews),
  and a plain rupee-amount regex (price).
- "Gifting/Novelty" has no real Amazon bestsellers browse node at all —
  substituted with "watches" (Watches & Gifting), a real, gift-heavy category.
- Any single category's fetch/parse failure is logged and skipped; it never
  aborts the rest of the run. Partial data beats no data.
"""

import html
import random
import re
import sys
import time
from datetime import datetime, timezone

import requests

import db

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-IN,en;q=0.9",
}

# category label -> amazon.in bestsellers browse-node slug
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
    "Watches & Gifting": "watches",  # substitute for non-existent "Gifting/Novelty" node
}

LIST_TYPE = "bestsellers"  # v1 scope: Best Sellers only
BASE_URL = "https://www.amazon.in/gp/bestsellers/{slug}/"

ASIN_RE = re.compile(r'data-asin="([A-Z0-9]{10})"')
RANK_RE = re.compile(r'zg-bdg-text">#(\d+)<')
TITLE_RE = re.compile(r'class="[^"]*p13n-sc-css-line-clamp[^"]*">([^<]+)<')
RATING_RE = re.compile(r'aria-label="([\d.]+) out of 5 stars, ([\d,]+) ratings?"')
PRICE_RE = re.compile(r'₹([\d,]+\.\d{2})')
IMAGE_RE = re.compile(r'<img[^>]+src="([^"]+)"')


def fetch(url, timeout=20, retries=1):
    """GET with one retry on failure. Returns response text or raises."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(3)
    raise last_err


def parse_products(html):
    """Split the page into per-product blocks (one per data-asin occurrence)
    and extract fields from each block. Returns a list of dicts (fields may
    be None if a given field wasn't found for that product)."""
    matches = list(ASIN_RE.finditer(html))
    products = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        block = html[start:end]

        asin = m.group(1)
        rank_m = RANK_RE.search(block)
        title_m = TITLE_RE.search(block)
        rating_m = RATING_RE.search(block)
        price_m = PRICE_RE.search(block)
        image_m = IMAGE_RE.search(block)

        rating = float(rating_m.group(1)) if rating_m else None
        review_count = int(rating_m.group(2).replace(",", "")) if rating_m else None
        price = float(price_m.group(1).replace(",", "")) if price_m else None

        products.append({
            "asin": asin,
            "rank": int(rank_m.group(1)) if rank_m else None,
            "title": html.unescape(title_m.group(1).strip()) if title_m else None,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "image_url": image_m.group(1) if image_m else None,
        })
    return products


def collect_category(label, slug):
    """Fetch + parse one category. Returns list of snapshot-row dicts.
    Raises on failure (caller is responsible for catching/logging)."""
    url = BASE_URL.format(slug=slug)
    html = fetch(url)
    products = parse_products(html)

    valid = [p for p in products if p["asin"] and p["title"]]
    if not valid:
        raise ValueError(
            f"parsed 0 valid products (got {len(products)} raw asin matches) "
            f"— page may be a placeholder/blocked response"
        )

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for p in valid:
        rows.append({
            "asin": p["asin"],
            "category": label,
            "list_type": LIST_TYPE,
            "rank": p["rank"],
            "title": p["title"],
            "price": p["price"],
            "rating": p["rating"],
            "review_count": p["review_count"],
            "image_url": p["image_url"],
            "collected_at": now,
        })
    return rows


def run(categories=None):
    """Run the collector across the given categories (default: all).
    Returns a summary dict: {label: {"ok": True, "rows": N} | {"ok": False, "error": str}}."""
    db.init_db()
    targets = categories or CATEGORIES
    summary = {}

    labels = list(targets.items())
    for idx, (label, slug) in enumerate(labels):
        try:
            rows = collect_category(label, slug)
            n = db.insert_snapshot_rows(rows)
            summary[label] = {"ok": True, "rows": n}
            print(f"[ok]   {label:<24} ({slug}) -> {n} rows")
        except Exception as e:
            summary[label] = {"ok": False, "error": str(e)}
            print(f"[FAIL] {label:<24} ({slug}) -> {e}")

        if idx < len(labels) - 1:
            delay = random.uniform(10, 30)
            time.sleep(delay)

    return summary


if __name__ == "__main__":
    if len(sys.argv) > 1:
        slug_arg = sys.argv[1]
        matches = {lbl: s for lbl, s in CATEGORIES.items() if s == slug_arg or lbl == slug_arg}
        if not matches:
            print(f"Unknown category/slug: {slug_arg}")
            print("Known categories:", ", ".join(CATEGORIES))
            sys.exit(1)
        run(matches)
    else:
        run()
