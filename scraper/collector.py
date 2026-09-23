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
- Depth (added 2026-09-09): each list is fetched at page 1 AND page 2.
  Measured live on three categories that day, not assumed:
      page 1 (no query string) -> ranks  1-30, 30 ASINs
      page 2 (?pg=2)           -> ranks 51-80, 30 ASINs, ZERO overlap with p1
      page 3 / page 4          -> HTTP 400, a 2,163-byte error page
  So a bestseller list is exactly two server-rendered pages deep and this
  change is an exact 2x on rows, not an estimate. Ranks 31-50 and 81-100
  exist on Amazon's own paging but are NOT server-rendered — they arrive
  client-side, the same reason Movers & Shakers was excluded above. Do not
  add a pg=3; it is not a slug or a header problem, the list simply ends.
  Use the bare "?pg=2" form: the "ref=zg_bs_pg_2" variant was captcha'd on
  1 of 3 categories in the same test while "?pg=2" passed 3 of 3.
- Fetching is CONCURRENT (added 2026-09-09) because doubling the page count
  sequentially would have cost ~107 min/run — over 3,000 GitHub Actions
  minutes a month against a 2,000-minute allowance, i.e. the depth was
  unaffordable without this. Workers pull from one shared queue and each
  keeps its own polite delay between its own fetches. Read SCOUT_FETCH_WORKERS
  below before raising it: the honest cost of concurrency is a higher
  aggregate request rate from a single IP, which is what actually gets a
  scraper blocked.
"""

import html
import os
import queue
import random
import re
import sys
import threading
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

# --- Throughput knobs. All env-overridable so a bad night can be rolled back
# --- from the workflow file without a code change or a redeploy.
#
# PAGES: which pages of each list to fetch. "1" alone restores the exact
# pre-2026-09-09 behaviour. Do not put 3 in here — verified HTTP 400.
PAGES = tuple(
    int(p) for p in os.environ.get("SCOUT_PAGES", "1,2").split(",") if p.strip()
)

# COLLECT_LIST_TYPES: which list types the run actually fetches, per category
# and per page. Env-overridable for the same reason SCOUT_PAGES is: a
# decision to trim or restore a list type is made in the workflow file, not
# in code.
#
# Default 2026-09-22: collect ALL four list types. Amazon.in's server-rendering
# of these lists is unstable — on any given night a list type serves 30 items
# for some categories and 0 for others (verified from the VM, 8 s spacing:
# most-gifted alive on beauty, dead on pet-supplies, in the SAME run; same for
# most-wished-for and several new-releases categories). That rotation is why
# the 18–22 Sep nightly totals fell from ~6,100 to ~3,500: no code bug, the
# data source is just serving fewer lists on those nights.
#
# The robust answer is to KEEP collecting all four types every night so that
# whenever Amazon serves a category on a given night we capture it, and when
# they rotate a type back fully the run report's cross-checks call out the
# swing. A real headless browser does not help — it renders the same empty
# shell Amazon serves to curl; the emptiness is server-side, not JS-hydrated.
#
# If you want to TRIM the run (fewer fetches), set SCOUT_LIST_TYPES to a subset
# — e.g. "bestsellers,new-releases". Anything in LIST_TYPES that you OMIT then
# becomes watch-only: the liveness probe below fetches a few sentinels for it
# each night and, on the night it serves full lists again, prints the one-line
# re-enable step. The trade is deliberate: trim = cheaper nights, miss data on
# categories that are briefly alive. Default is the opposite: capture everything.
COLLECT_LIST_TYPES = tuple(
    t for t in os.environ.get("SCOUT_LIST_TYPES", "").split(",") if t.strip()
) or tuple(LIST_TYPES.keys())

# Sentinels the liveness probe fetches (page 1 only) for any list type NOT in
# COLLECT_LIST_TYPES: four well-populated categories. A live list serves a
# full 30 items, so 30 on a sentinel is the revival signal. Sequential with
# the normal politeness gap — deliberately NOT on the concurrent hot path,
# because the probe is 4 x N fetches and exists to stay invisible to the
# rate limiter.
LIVENESS_PROBE_SENTINELS = [
    ("Electronics Accessories", "electronics"),
    ("Beauty & Personal Care", "beauty"),
    ("Toys & Games", "toys"),
    ("Home & Kitchen", "kitchen"),
]
LIVENESS_PROBE_MIN_ROWS = 30

# FETCH_WORKERS: how many fetches are in flight at once.
#
# The trade, stated plainly because it is easy to get wrong: Amazon sees the
# same request rate PER URL PATH either way, but it sees N times the rate from
# ONE IP, and blocking is per-IP. At 1 worker / 10-30 s the runner made ~2.3
# requests/min. The defaults below (4 workers, 20-45 s) make ~7.4/min — about
# 3x today's aggregate rate, not 4x, because the gap was widened to partly pay
# for the extra concurrency. If the run starts drawing captchas, lower this
# FIRST (it is the aggregate rate that matters), and only then reconsider PAGES.
FETCH_WORKERS = max(1, int(os.environ.get("SCOUT_FETCH_WORKERS", "4")))
GAP_MIN_SECONDS = float(os.environ.get("SCOUT_GAP_MIN", "20"))
GAP_MAX_SECONDS = float(os.environ.get("SCOUT_GAP_MAX", "45"))

# --- Sub-category collection (added 2026-09-23) ---------------------------------
# The 31 top-level CATEGORIES above give ~3,500 rows/night. Sub-categories are
# the row-growth lever: Amazon.in serves its OWN distinct 30-item bestseller
# (and new-releases) list for every browse-node, and we discovered 382 of them
# live (browse_tree_full.json -> subcats.json, committed next to this module).
#
# All knobs are env-overridable for the same reason SCOUT_PAGES is: dial the
# volume up or down from the workflow file with no code change, no redeploy.
# Defaults are set to fit the 2,000-min private-repo GitHub cap (session 2 of
# the nightly pair); raise them only once the runner is unlimited (public repo
# or a self-hosted runner), when minutes are no longer the constraint.
SUBCATS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subcats.json")
# How many sub-categories a sub-cat run touches. 0 or missing file = disabled.
SUBCAT_MAX = int(os.environ.get("SCOUT_SUBCAT_MAX", "60"))
# List types the sub-cat run fetches (default the two that render reliably;
# most-gifted / most-wished-for are volatile, see COLLECT_LIST_TYPES note).
SUBCAT_LIST_TYPES = tuple(
    t for t in os.environ.get("SCOUT_SUBCAT_LIST_TYPES", "bestsellers,new-releases").split(",")
    if t.strip()
)
# Pages per sub-cat list. Default page 1 only: sub-node lists are short and
# page-1 is the one that always renders, so depth buys little and costs a real
# fetch. Enable "1,2" once a run proves sub-node depth is clean.
SUBCAT_PAGES = tuple(
    int(p) for p in os.environ.get("SCOUT_SUBCAT_PAGES", "1").split(",") if p.strip()
)


ASIN_RE = re.compile(r'data-asin="([A-Z0-9]{10})"')
RANK_RE = re.compile(r'zg-bdg-text">#(\d+)<')
TITLE_RE = re.compile(r'class="[^"]*p13n-sc-css-line-clamp[^"]*">([^<]+)<')
RATING_RE = re.compile(r'aria-label="([\d.]+) out of 5 stars, ([\d,]+) ratings?"')
PRICE_RE = re.compile(r'₹([\d,]+\.\d{2})')
IMAGE_RE = re.compile(r'<img[^>]+src="([^"]+)"')

# --- Additional field extractors for 327-framework Phase 1 -------------------
# Brand: extract from URL path segment before /dp/ (e.g., "/Portronics-Earphones-.../dp/")
BRAND_URL_RE = re.compile(r'/([A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*)/dp/')
# Size tier hints from title (NOT_APPLICABLE if none match)
SIZE_TIER_RE = re.compile(
    r'\b(small|compact|mini|micro|petite)\b'
    r'|\b(jumbo|large|big|standard|full-size|regular)\b',
    re.I
)
# Product type hint: first meaningful word after brand in title
PRODUCT_TYPE_RE = re.compile(
    r'(?:earphone|headphone|speaker|charger|cable|cover|case|watch|shirt|pant|dress|shoe|book|tablet|phone|laptop|camera|toy|bag|bottle|lamp|fan|motor|blade|pillow|blanket)',
    re.I
)


def _extract_brand(url):
    """Extract brand from Amazon URL slug. Returns None if not found."""
    m = BRAND_URL_RE.search(url)
    if not m:
        return None
    raw = m.group(1)
    # Take the first component before any hyphens (Amazon slugs are hyphenated)
    parts = raw.split('-')
    if not parts:
        return None
    # Heuristic: brand is usually 1-2 capitalized words, stop at common non-brand terms
    brand_words = []
    SKIP = {'the', 'and', 'for', 'with', 'by', 'in', 'on', 'at', 'to', 'a', 'an'}
    for w in parts[:4]:
        # Keep if it looks like a proper noun (starts with uppercase, all alpha)
        if w[0].isupper() and w.isalpha() and len(w) >= 2 and w.lower() not in SKIP:
            brand_words.append(w)
        elif brand_words:
            break  # stopped at first non-brand-like word
    return ' '.join(brand_words) if brand_words else None


def _detect_size_tier(title):
    """Detect size tier hint from title. Returns 'small', 'large', or None."""
    if not title:
        return None
    m = SIZE_TIER_RE.search(title)
    return m.group(1).lower() if m else None


def _detect_product_type(title, category):
    """Detect rough product type from title keywords. Returns None if unclear."""
    if not title:
        return None
    m = PRODUCT_TYPE_RE.search(title)
    if m:
        return m.group(1).lower()
    return None


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
            # Phase 1 extras (327-framework)
            "brand": _extract_brand(block),
            "size_tier_hint": _detect_size_tier(html.unescape(title_m.group(1).strip()) if title_m else None),
            "product_type_hint": _detect_product_type(
                html.unescape(title_m.group(1).strip()) if title_m else None,
                ""
            ),
        })
    return products


class NoSuchPage(ValueError):
    """Page N fetched cleanly and holds zero product cards.

    Measured 2026-09-09: for a short list (Music new-releases has 2 products,
    Movies & TV Shows 7), "?pg=2" returns a real HTTP 200 page that clears the
    40 KB floor and carries no captcha text, but contains zero data-asin
    matches. That has to be told apart from a failure: lumping a dozen
    structurally-empty page 2s in with real failures would put permanent noise
    in the exact signal meant to detect a block, which is how the degraded runs
    hid for weeks the last time.

    But this condition ALONE does not prove the list merely ended. The same
    test showed a nonexistent browse-node slug also returns a clean 200 with no
    products. So one empty deep page is only trustworthy as "the list ended"
    when page 1 of the SAME list succeeded, and a *fleet-wide* spike in empty
    deep pages is a soft block, not thirty short lists. Both cross-checks live
    in _print_run_report, because neither can be made from inside one job."""


def build_url(slug, list_type, page=1):
    """Page 1 keeps the exact bare URL the collector has always used — no
    query string appended — so the request that has worked for two months is
    byte-identical. Only page 2+ carries ?pg=N."""
    url = BASE_URL.format(path=LIST_TYPES[list_type], slug=slug)
    return url if page == 1 else f"{url}?pg={page}"


def collect_category(label, slug, list_type="bestsellers", page=1, collected_at=None):
    """Fetch + parse one category/list-type/page combination. Returns list of
    snapshot-row dicts. Raises on failure (caller is responsible for
    catching/logging).

    `rank` is whatever Amazon's own zg-bdg-text badge says, so page-2 rows
    carry their true ranks (51-80) with no offset arithmetic. Never compute a
    rank from list position — the two pages are not contiguous.

    `collected_at` MUST be passed by run() so that every page of one list
    shares a single timestamp. See _group_timestamp for why this is not
    cosmetic. It falls back to now() only for a direct call outside run()."""
    url = build_url(slug, list_type, page)
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
        # A deep page that fetched cleanly and holds zero product cards is a
        # list that ended, not a page that was refused. fetch() has already
        # proved this response is >40 KB and captcha-free, so the emptiness is
        # Amazon's answer, not an interstitial. Page 1 never gets this benefit
        # of the doubt — an empty page 1 is always a fault.
        if page > 1 and not products:
            raise NoSuchPage(
                f"page {page} fetched clean ({len(page_html):,} chars) but holds "
                f"0 product cards — list ended, or a deep-page block; the run "
                f"report decides which"
            )
        raise ValueError(
            f"parsed only {len(valid)} valid products ({len(products)} raw asin matches) "
            f"— page likely truncated, blocked, or a placeholder response"
        )

    now = collected_at or datetime.now(timezone.utc).isoformat()
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
            "brand": p.get("brand"),
            "size_tier_hint": p.get("size_tier_hint"),
            "product_type_hint": p.get("product_type_hint"),
            "collected_at": now,
        })
    return rows


def load_subcats(max_count=None):
    """Return an ordered {label: slug} dict of sub-categories, shaped exactly
    like CATEGORIES so it can be passed straight to run(categories=...).

    Read from subcats.json (committed beside this module). The compound slug
    "electronics/1388867031" is what Amazon's /gp/bestsellers/ route accepts:
    {list_path}/{top_slug}/{browse_node}/ -> that node's own 30-item list.
    Truncated to max_count (default SUBCAT_MAX) so a run's fetch budget stays
    bounded and env-tunable. Empty/absent file returns {} (mode is a no-op)."""
    import json
    import collections
    try:
        with open(SUBCATS_JSON) as f:
            data = json.load(f)
    except FileNotFoundError:
        return collections.OrderedDict()
    subs = data.get("subcategories", [])
    limit = max_count if max_count is not None else SUBCAT_MAX
    out = collections.OrderedDict()
    for s in subs[:limit]:
        out[s["label"]] = s["slug"]
    return out


def run_subcats(max_count=None, dry_run=False):
    """Sub-category run: fetches Amazon's per-browse-node lists instead of the
    31 top-level ones. Reuses run() so fetching, insertion, the liveness probe,
    and the run report are all identical to a normal night. The category label
    for a sub-node is "Top > Leaf", so a sub-node row and its parent top-level
    row are distinct snapshots (and the uq_snapshots_row index keys on the
    category string, so they never collide)."""
    targets = load_subcats(max_count)
    if not targets:
        print("[subcats] no sub-categories available (missing subcats.json or "
              "SUBCAT_MAX=0) — nothing to do.")
        return {}
    print(f"[subcats] {len(targets)} sub-category lists | "
          f"types={list(SUBCAT_LIST_TYPES)} | pages={list(SUBCAT_PAGES)} "
          f"{'| DRY RUN' if dry_run else ''}")
    return run(
        categories=targets,
        list_types=list(SUBCAT_LIST_TYPES),
        pages=SUBCAT_PAGES,
        dry_run=dry_run,
    )


def _job_key(label, list_type, page):
    """Page 1 keys are unchanged ("Label [bestsellers]") so every existing log
    grep and eyeball still works; only page 2+ is suffixed."""
    return f"{label} [{list_type}]" if page == 1 else f"{label} [{list_type} p{page}]"


def _group_timestamp(label, list_type, group_ts, group_lock):
    """One collected_at per (category, list_type), shared by all of its pages.

    This is a correctness requirement, not tidiness. Two things downstream read
    the timestamp as "when this list was last observed":

      * api/db.get_latest_runs_by_category_list_type() takes
        MAX(collected_at) GROUP BY (category, list_type), and
        api/alerts._check_dropout flags any watched ASIN whose newest row is
        older than that MAX as "dropped from list". Page 2 is fetched after
        page 1, so a per-page timestamp would make MAX the page-2 time and
        every single top-30 ASIN would look dropped, every night. Caught by
        code review on 2026-09-09, before this ever ran.

      * uq_snapshots_row is UNIQUE(asin, category, list_type, collected_at).
        Sharing the stamp means an ASIN that Amazon happens to show on both
        pages (a reshuffle between the two fetches) is deduped to one row by
        the existing ON CONFLICT DO NOTHING, instead of landing twice at two
        different ranks for the same run.

    The stamp is taken when the FIRST page of the group is collected, which
    keeps the existing behaviour exactly: before this change each
    (category, list_type) already carried a single time, spread across the run
    as its turn came up. Nothing about page 1 changes."""
    key = (label, list_type)
    with group_lock:
        if key not in group_ts:
            group_ts[key] = datetime.now(timezone.utc).isoformat()
        return group_ts[key]


def _fetch_worker(worker_id, jobs_q, results_q, group_ts, group_lock):
    """Pull (label, slug, list_type, page) off the shared queue until it is
    empty. Fetch and parse only — no database access happens on a worker
    thread. db.get_conn() opens a fresh connection per call so concurrent
    writes would in fact be safe, but keeping every INSERT on the main thread
    means one writer and no chance of N connections against a free-tier pooler.

    Results go onto results_q the moment they are ready, and the main thread
    inserts them as they arrive rather than after the last fetch. That ordering
    matters: the workflow now carries a 75-minute timeout, and a run killed at
    the cap must keep everything it had already collected. "Partial data beats
    no data" is this module's stated rule (see the header) and a batch-at-the-
    end design quietly breaks it.
    """
    # Stagger the start so N workers do not all fire their first request in the
    # same instant — that opening burst is the most visible thing a rate
    # limiter sees.
    time.sleep(worker_id * (GAP_MIN_SECONDS / max(1, FETCH_WORKERS)))

    first = True
    while True:
        try:
            label, slug, list_type, page = jobs_q.get_nowait()
        except queue.Empty:
            return

        if not first:
            time.sleep(random.uniform(GAP_MIN_SECONDS, GAP_MAX_SECONDS))
        first = False

        key = _job_key(label, list_type, page)
        try:
            stamp = _group_timestamp(label, list_type, group_ts, group_lock)
            rows = collect_category(label, slug, list_type, page, collected_at=stamp)
            result = {"ok": True, "rows_parsed": len(rows), "rows": rows,
                      "page": page, "slug": slug}
        except NoSuchPage as e:
            result = {"ok": False, "empty": True, "error": str(e),
                      "page": page, "slug": slug}
        except Exception as e:
            result = {"ok": False, "error": str(e), "page": page, "slug": slug}

        results_q.put((key, result))


def run(categories=None, list_types=None, pages=None, dry_run=False):
    """Run the collector across the given categories x list types x pages
    (default: all categories, all 4 supported list types, pages 1 and 2).
    Returns a summary dict keyed by "label [list_type]" / "label [list_type p2]":
    {"ok": True, "rows": N} | {"ok": False, "error": str}.

    Fetching is concurrent (FETCH_WORKERS), inserting is not. Each worker keeps
    its own GAP_MIN..GAP_MAX delay between its own fetches, so the per-URL-path
    politeness is unchanged from the sequential version; what rises is the
    aggregate rate from the single runner IP. See the module docstring.

    dry_run=True fetches and parses exactly as normal but writes nothing and
    never touches the database — used to prove a change against live Amazon
    without putting a single row at risk.
    """
    if not dry_run:
        db.init_db()
    targets = categories or CATEGORIES
    types = list_types or list(COLLECT_LIST_TYPES)
    pages = pages or PAGES

    jobs = [
        (label, slug, lt, pg)
        for label, slug in targets.items()
        for lt in types
        for pg in pages
    ]
    # Interleave so the queue never hands out the same slug twice in a row:
    # consecutive jobs from one category would otherwise be the fastest way to
    # look like a crawler on one URL path.
    jobs.sort(key=lambda j: (j[3], j[2]))

    jobs_q = queue.Queue()
    for j in jobs:
        jobs_q.put(j)

    results_q = queue.Queue()
    group_ts, group_lock = {}, threading.Lock()
    started = time.time()
    print(f"[cfg]  {len(jobs)} fetches | pages={list(pages)} | workers={FETCH_WORKERS} "
          f"| gap={GAP_MIN_SECONDS:.0f}-{GAP_MAX_SECONDS:.0f}s"
          f"{' | DRY RUN, no writes' if dry_run else ''}")

    threads = [
        threading.Thread(
            target=_fetch_worker,
            args=(i, jobs_q, results_q, group_ts, group_lock),
            daemon=True,
        )
        for i in range(FETCH_WORKERS)
    ]
    for t in threads:
        t.start()

    # Single-threaded write phase, running CONCURRENTLY with the fetching: each
    # result is inserted as soon as a worker produces it, so whatever has landed
    # by the time the job is killed is already committed.
    summary = {}
    while len(summary) < len(jobs):
        try:
            key, r = results_q.get(timeout=5)
        except queue.Empty:
            # Every worker gone with jobs still outstanding means threads died
            # rather than finished. Stop waiting; the loop below names what is
            # missing instead of hanging until the workflow timeout.
            if not any(t.is_alive() for t in threads):
                break
            continue
        summary[key] = _write_one(key, r, dry_run)

    for t in threads:
        t.join(timeout=10)

    for label, slug, list_type, page in jobs:
        key = _job_key(label, list_type, page)
        if key not in summary:
            summary[key] = {"ok": False, "error": "worker produced no result"}
            print(f"[FAIL] {key:<48} ({slug}) -> worker produced no result")

    # Watch the dropped list types (sequential, polite, write-free). Skipped
    # on dry-run: a --dry-run invocation exists to prove a change against
    # live Amazon without side effects, and a 16-fetch watch pass is a
    # side effect.
    if not dry_run:
        _run_liveness_probe(types)

    _print_run_report(summary, time.time() - started)
    return summary


def _write_one(key, r, dry_run):
    """Insert one job's rows and log the outcome. Returns its summary entry."""
    slug = r.get("slug", "")
    if not r["ok"] and r.get("empty"):
        print(f"[none] {key:<48} ({slug}) -> {r['error']}")
        return {"ok": False, "empty": True, "error": r["error"]}
    if not r["ok"]:
        print(f"[FAIL] {key:<48} ({slug}) -> {r['error']}")
        return {"ok": False, "error": r["error"]}
    if dry_run:
        n = r["rows_parsed"]
        print(f"[dry]  {key:<48} ({slug}) -> {n} rows parsed, not written")
        return {"ok": True, "rows": n, "dry_run": True}
    try:
        n = db.insert_snapshot_rows(r["rows"])
        print(f"[ok]   {key:<48} ({slug}) -> {n} rows")
        return {"ok": True, "rows": n}
    except Exception as e:
        # An insert failure must not take the run down: the remaining fetches
        # are still worth landing, and a transient Supabase blip should cost
        # one list, not the night.
        print(f"[FAIL] {key:<48} ({slug}) -> insert failed: {e}")
        return {"ok": False, "error": f"insert failed: {e}"}


def _page_of_key(key):
    """Recover the page number from a summary key. Page 1 keys carry no marker
    (they are the original format), deeper ones end in " pN]"."""
    m = re.search(r" p(\d+)\]$", key)
    return int(m.group(1)) if m else 1


def _run_liveness_probe(probed_types):
    """For list types dropped out of the nightly collect, fetch a few
    well-populated sentinels (page 1 only) and report whether Amazon has
    brought the feature back. Sequential with the normal politeness gap so
    the probe stays invisible to the rate limiter.

    Writes nothing and records nothing in the run report: this is a
    watchman, not a collector. When a probed type serves full lists again
    on a MAJORITY of sentinels, this prints the one-line re-enable step
    (add it back to SCOUT_LIST_TYPES in the workflow file). A single
    sentinel going live is not enough — the sweep on 2026-09-22 found
    most-gifted/most-wished-for in flux, alive on some categories and dead
    on others, so a 1-of-4 reading is "still dying", not "revived"."""
    dropped = [t for t in LIST_TYPES if t not in probed_types]
    if not dropped:
        return
    print()
    print(f"=== liveness probe (watching {len(dropped)} dropped list type(s): "
          f"{', '.join(dropped)}) ===")
    for lt in dropped:
        live = proven = 0
        for label, slug in LIVENESS_PROBE_SENTINELS:
            key = _job_key(label, lt, 1)
            try:
                time.sleep(random.uniform(GAP_MIN_SECONDS, GAP_MAX_SECONDS))
                rows = collect_category(label, slug, lt, 1, collected_at=None)
                n = len(rows)
            except (NoSuchPage, ValueError) as e:
                # A clean fetch that parses to 0 items IS a reading (the
                # "still dead" answer); only a failed fetch is unproven.
                m = re.search(r"parsed only (\d+) valid products", str(e))
                n = int(m.group(1)) if m else 0
            except Exception as e:
                print(f"  [probe] {key:<48} ({slug}) -> fetch error: "
                      f"{str(e)[:70]} (unproven)")
                continue
            proven += 1
            if n >= LIVENESS_PROBE_MIN_ROWS:
                live += 1
                print(f"  [probe] {key:<48} ({slug}) -> {n} rows  <-- REVIVED")
            else:
                print(f"  [probe] {key:<48} ({slug}) -> {n} rows")
        if proven == 0:
            print(f"  {lt}: probe inconclusive — every sentinel fetch "
                  f"errored; re-check tomorrow's run before acting.")
        elif live * 2 >= proven:
            suggestion = ",".join(list(COLLECT_LIST_TYPES) + [lt])
            print(f"  ** {lt} serving full lists on {live}/{proven} sentinel(s) "
                  f"again. Re-enable by adding it to SCOUT_LIST_TYPES in "
                  f".github/workflows/nightly-collect.yml, e.g. "
                  f"SCOUT_LIST_TYPES: \"{suggestion}\"")
        else:
            print(f"  {lt} still serving 0 items on {proven} proven "
                  f"sentinel(s) — Amazon has not revived it. Staying watch-only.")


def _print_run_report(summary, elapsed_seconds):
    """A verdict from the data, not from the exit code — the same rule the VM
    tasks already follow. A run that fetched 248 pages and landed 40 rows exits
    0 exactly like a healthy one unless something says otherwise here."""
    by_page = {}
    for key, r in summary.items():
        page = _page_of_key(key)
        b = by_page.setdefault(page, {"ok": 0, "fail": 0, "empty": 0, "rows": 0})
        if r.get("ok"):
            b["ok"] += 1
            b["rows"] += r.get("rows", 0)
        elif r.get("empty"):
            b["empty"] += 1
        else:
            b["fail"] += 1

    print()
    print(f"=== run report ({elapsed_seconds / 60:.1f} min) ===")
    total_rows = 0
    for page in sorted(by_page):
        b = by_page[page]
        total_rows += b["rows"]
        print(f"  page {page}: {b['ok']} ok, {b['fail']} failed, "
              f"{b['empty']} no-such-page, {b['rows']} rows")
    print(f"  TOTAL  : {total_rows} rows")

    # Cross-check 1: an empty deep page is only believable as "the list ended"
    # if page 1 of that same list worked. If page 1 failed too, the whole list
    # is broken and page 2's silence is meaningless — say so rather than let it
    # sit in a reassuring bucket.
    orphaned = []
    for key, r in summary.items():
        if not r.get("empty"):
            continue
        p1_key = key.replace(" p2]", "]").replace(" p3]", "]")
        p1 = summary.get(p1_key)
        if p1 is not None and not p1.get("ok"):
            orphaned.append(key)
    if orphaned:
        print(f"  [WARN] {len(orphaned)} empty deep page(s) belong to lists whose "
              f"page 1 also failed — not short lists, broken lists: "
              f"{', '.join(sorted(orphaned)[:4])}"
              f"{' …' if len(orphaned) > 4 else ''}")

    # Cross-check 2: a deep page that HARD-FAILS everywhere is a block. Empty
    # pages are counted separately and kept out of this denominator so they can
    # never dilute a real block into looking normal.
    for page in sorted(p for p in by_page if p > 1):
        b = by_page[page]
        # A minimum sample, for the same reason cross-check 3 has one: "1 of 1
        # failed" is 100% and means nothing. amazon.in throws transient single
        # failures routinely — one was observed mid-test on 2026-09-09 — and a
        # warning that fires on a debug run of one category would train someone
        # to ignore it on the night it is real.
        attempted = b["ok"] + b["fail"]
        if attempted >= 8 and b["fail"] / attempted > 0.25:
            print(
                f"  [WARN] page {page} hard-failed on {b['fail']}/{attempted} "
                f"({b['fail'] / attempted:.0%}) of the lists that have one. "
                f"Too many to be anything but a block: lower "
                f"SCOUT_FETCH_WORKERS before touching anything else."
            )

        # Cross-check 3: the soft block. Amazon serving clean, empty deep pages
        # fleet-wide looks identical, job by job, to a lot of short lists. Only
        # the rate tells them apart. Most bestseller lists carry 100 products,
        # so short lists are the exception; if most lists with a healthy page 1
        # suddenly have no page 2, depth has been switched off, not outgrown.
        # Orphans (page 1 failed too) are excluded — cross-check 1 owns those,
        # and counting them here would let broken slugs inflate the rate.
        empty_with_healthy_p1 = b["empty"] - sum(
            1 for k in orphaned if _page_of_key(k) == page
        )
        denom = b["ok"] + empty_with_healthy_p1
        if denom >= 8 and empty_with_healthy_p1 / denom > 0.4:
            print(
                f"  [WARN] page {page} came back clean-but-empty on "
                f"{empty_with_healthy_p1}/{denom} "
                f"({empty_with_healthy_p1 / denom:.0%}) of lists whose page 1 was "
                f"fine. Short lists are the exception, not the rule — suspect a "
                f"deep-page soft block and compare against the previous run "
                f"before trusting tonight's depth."
            )


if __name__ == "__main__":
    # --dry-run fetches and parses for real but writes nothing. Pulled out of
    # argv before positional parsing so it can go anywhere on the line.
    dry = "--dry-run" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--dry-run"]

    # --subcats: run only the sub-category lists (browse nodes in subcats.json),
    # a separate nightly session from the top-level run. --dry-run still works.
    if "--subcats" in sys.argv:
        sys.argv = [a for a in sys.argv if a != "--subcats"]
        run_subcats(dry_run=dry)
        sys.exit(0)

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
        run(matches, [list_type_arg] if list_type_arg else None, dry_run=dry)
    else:
        run(dry_run=dry)
