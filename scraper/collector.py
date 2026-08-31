"""
Scout's nightly collector. Fetches amazon.in list pages (Best Sellers, New
Releases, Most Wished For, Most Gifted) for a fixed list of broad-discovery
categories, parses each product card, and writes one snapshot row per
product into the database (via db.insert_snapshot_rows).

Cloud version: runs via GitHub Actions on a schedule, writing to Supabase
Postgres instead of a local SQLite file. Logic is unchanged from the original
laptop version — only db.py's connection layer changed.

Run manually (all categories x all list types):  python collector.py
Run for one category only, all list types (debugging):  python collector.py electronics

Design notes (see BLUEPRINT / plan for full context):
- Expanded 2026-07-08 from Best Sellers only to 4 list types. Movers &
  Shakers was investigated and deliberately excluded: verified across
  multiple categories that its pages return zero server-side-rendered
  products for every category tested (real HTTP 200, correct <title>, but
  the product-card HTML is entirely absent — likely populated client-side
  via JS rather than server-rendered like the other four list types). Not
  achievable with this scraper's plain-HTTP approach without a much bigger
  investment (headless browser). Revisit only if that trade-off changes.
- Amazon's CSS classes are hashed/versioned (e.g. "_cDEzb_..._3mJ9Z") and
  likely change on redeploys, so parsing matches stable substrings/attributes
  instead: zg-bdg-text (rank), data-asin (asin), p13n-sc-css-line-clamp
  (title), the "X out of 5 stars, Y ratings" aria-label (rating+reviews),
  and a plain rupee-amount regex (price).
- "Gifting/Novelty" has no real Amazon bestsellers browse node at all —
  substituted with "watches" (Watches & Gifting), a real, gift-heavy category.
- Any single category/list-type fetch/parse failure is logged and skipped;
  it never aborts the rest of the run. Partial data beats no data.
"""

import html
import os
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

# category label -> amazon.in bestsellers browse-node slug.
# The original 11 (through "Watches & Gifting") are load-bearing: renaming
# any of these labels would fragment existing trend history under a new
# label, since the DB has months of rows tagged with the exact text below.
# Add new categories freely; never rename an existing key.
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
    # Expanded 2026-07-08 to cover all 31 of Amazon.in's real bestseller
    # categories (verified against the live nav, not guessed) per Ram's
    # request for full coverage rather than a curated subset.
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

# list_type key -> amazon.in URL path segment. Movers & Shakers deliberately
# excluded — see module docstring for why (verified zero server-rendered
# products across multiple categories, not a slug problem).
LIST_TYPES = {
    "bestsellers": "gp/bestsellers",
    "new-releases": "gp/new-releases",
    "most-wished-for": "gp/most-wished-for",
    "most-gifted": "gp/most-gifted",
}
BASE_URL = "https://www.amazon.in/{path}/{slug}/"

ASIN_RE = re.compile(r'data-asin="([A-Z0-9]{10})"')
RANK_RE = re.compile(r'zg-bdg-text">#(\d+)<')
TITLE_RE = re.compile(r'class="[^"]*p13n-sc-css-line-clamp[^"]*">([^<]+)<')
RATING_RE = re.compile(r'aria-label="([\d.]+) out of 5 stars, ([\d,]+) ratings?"')
PRICE_RE = re.compile(r'₹([\d,]+\.\d{2})')
IMAGE_RE = re.compile(r'<img[^>]+src="([^"]+)"')


MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)

SCRAPEOPS_API_KEY = os.environ.get("SCRAPEOPS_API_KEY")

def fetch(url, timeout=25, retries=2):
    """GET with retries, header rotation, and optional ScrapeOps proxy API fallback."""
    last_err = None
    
    # Try direct fetch with rotating user-agents first
    header_options = [
        HEADERS,
        {
            "User-Agent": MOBILE_USER_AGENT,
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    ]
    
    for attempt in range(retries + 1):
        headers = header_options[attempt % len(header_options)]
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            text = resp.text
            # Verify it's a real Amazon page and not a bot interstitial
            if len(text) > 40_000 and "automated access" not in text.lower() and "enter the characters" not in text.lower():
                return text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                
    # If direct fetch was blocked and SCRAPEOPS_API_KEY is available, route via free proxy API
    if SCRAPEOPS_API_KEY:
        try:
            proxy_url = f"https://proxy.scrapeops.io/v1/?api_key={SCRAPEOPS_API_KEY}&url={url}"
            resp = requests.get(proxy_url, timeout=35)
            resp.raise_for_status()
            if len(resp.text) > 40_000:
                return resp.text
        except Exception as e:
            last_err = e

    raise last_err or ValueError(f"Failed to fetch valid Amazon page for {url}")



def parse_products(page_html):
    """Split the page into per-product blocks (one per data-asin occurrence)
    and extract fields from each block. Returns a list of dicts (fields may
    be None if a given field wasn't found for that product).

    NOTE: parameter is named page_html, not html — a bare `html` here would
    shadow the `import html` module used below for html.unescape(), which
    silently broke every single category (AttributeError swallowed by
    collect_category's per-category try/except, so the whole nightly run
    "succeeded" while collecting zero rows). Don't rename this back.
    """
    matches = list(ASIN_RE.finditer(page_html))
    products = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(page_html)
        block = page_html[start:end]

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


def collect_category(label, slug, list_type="bestsellers"):
    """Fetch + parse one category/list-type combination. Returns list of
    snapshot-row dicts. Raises on failure (caller is responsible for
    catching/logging)."""
    url = BASE_URL.format(path=LIST_TYPES[list_type], slug=slug)
    page_html = fetch(url)
    products = parse_products(page_html)

    valid = [p for p in products if p["asin"] and p["title"]]
    # Sanity floor, not just a zero-check -- but sized from measured data, not
    # vibes: some categories are legitimately tiny (Music new-releases has 2,
    # Movies & TV Shows 3, every night). A floor of 10 would have rejected
    # those real fetches forever; a floor of 2 still catches the failure mode
    # that matters: a blocked/placeholder page that parses to 0-1 stray ASINs.
    # Bigger pages are already gated by fetch()'s 40 KB + captcha-text checks
    # before parsing. (Audit 31 Aug: "no post-parse sanity check".)
    if len(valid) < 2:
        raise ValueError(
            f"parsed only {len(valid)} valid products ({len(products)} raw asin matches) "
            f"— page likely truncated, blocked, or a placeholder response"
        )

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for p in valid:
        rows.append({
            "asin": p["asin"],
            "category": label,
            "list_type": list_type,
            "rank": p["rank"],
            "title": p["title"],
            "price": p["price"],
            "rating": p["rating"],
            "review_count": p["review_count"],
            "image_url": p["image_url"],
            "collected_at": now,
        })
    return rows


def run(categories=None, list_types=None):
    """Run the collector across the given categories x list types (default:
    all categories, all 4 supported list types). Returns a summary dict
    keyed by "label [list_type]": {"ok": True, "rows": N} | {"ok": False, "error": str}.
    One polite delay between every individual fetch, not just per category —
    this is now 31 x 4 = up to 124 fetches/run, so pacing matters more than
    it did at 31."""
    db.init_db()
    targets = categories or CATEGORIES
    types = list_types or list(LIST_TYPES.keys())
    summary = {}

    jobs = [(label, slug, lt) for label, slug in targets.items() for lt in types]
    for idx, (label, slug, list_type) in enumerate(jobs):
        key = f"{label} [{list_type}]"
        try:
            rows = collect_category(label, slug, list_type)
            n = db.insert_snapshot_rows(rows)
            summary[key] = {"ok": True, "rows": n}
            print(f"[ok]   {key:<45} ({slug}) -> {n} rows")
        except Exception as e:
            summary[key] = {"ok": False, "error": str(e)}
            print(f"[FAIL] {key:<45} ({slug}) -> {e}")

        if idx < len(jobs) - 1:
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
        list_type_arg = sys.argv[2] if len(sys.argv) > 2 else None
        if list_type_arg and list_type_arg not in LIST_TYPES:
            print(f"Unknown list type: {list_type_arg}")
            print("Known list types:", ", ".join(LIST_TYPES))
            sys.exit(1)
        run(matches, [list_type_arg] if list_type_arg else None)
    else:
        run()
