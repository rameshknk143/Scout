"""
Listing Quality Score (Phase 2.1) -- rule-based, no AI/LLM call. Ram was
explicit he doesn't want to add a paid API key for this, so instead of
AI-generated title/bullet copy, this checks objective, verifiable things:
whether the title/bullets/images are actually there and reasonably sized,
plus how the ASIN's own price/rating/review-count compare to its category
peers (using Scout's own snapshot data -- no extra scraping needed for that
part). A scoped-down but genuinely useful version of "the easy one" from
PLATFORM-VISION.md, not the full AI-copywriter vision -- that stays parked
until Ram decides the per-call AI cost is worth it.

Fetches the live product detail page on demand (one ASIN, one click -- not
part of collector.py's nightly batch, and not the same URL shape it reads).

Amazon's bot detection on individual product pages turned out to be a much
bigger problem from Render's datacenter IP than it first looked in local
testing: the desktop /dp/{asin} page came back bot-blocked on every single
attempt, for every ASIN tried, both from Render's IP and separately from a
home connection later in the same day (i.e. not just transient rate-limiting
from earlier testing volume -- a real, repeatable block specific to that
URL). Verified directly: Amazon's *mobile* product page
(/gp/aw/d/{asin}) is a different endpoint with different bot-detection
treatment -- came back clean on every attempt, back-to-back, for ASINs the
desktop page was blocking 100% of the time. This module tries the mobile
page first for that reason, and only falls back to the desktop page (kept
as a second independent strategy, not removed) if mobile is ever blocked
too. If every attempt across both fails, this raises ListingFetchError
rather than silently returning an empty or fabricated score -- Ram sees an
honest "try again" message.
"""

import html
import random
import re
import time

import pandas as pd
import requests

import ai_client
import db
import trend_radar

DESKTOP_URL = "https://www.amazon.in/dp/{asin}"
DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DESKTOP_HEADERS = {"User-Agent": DESKTOP_USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}

# Amazon's mobile product page -- tried first; see module docstring for why.
MOBILE_URL = "https://www.amazon.in/gp/aw/d/{asin}"
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
MOBILE_HEADERS = {"User-Agent": MOBILE_USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}

FETCH_STRATEGIES = [
    (MOBILE_URL, MOBILE_HEADERS),
    (DESKTOP_URL, DESKTOP_HEADERS),
]
FETCH_ATTEMPTS_PER_STRATEGY = 2
RETRY_DELAY_RANGE = (3, 6)
MIN_REAL_PAGE_BYTES = 50_000  # the bot-check interstitial is ~5KB; real pages are 300KB+

TITLE_MIN_LEN = 80
TITLE_MAX_LEN = 200
BULLET_TARGET_COUNT = 5
BULLET_MIN_LEN = 50
IMAGE_TARGET_COUNT = 6

SUGGEST_ATTEMPTS = 3  # openrouter/free's random pick occasionally lands on a non-instruct model


class ListingFetchError(Exception):
    pass


def fetch_detail_page(asin):
    for url_template, headers in FETCH_STRATEGIES:
        for attempt in range(FETCH_ATTEMPTS_PER_STRATEGY):
            resp = requests.get(url_template.format(asin=asin), headers=headers, timeout=20)
            if (
                resp.status_code == 200
                and "Continue shopping" not in resp.text
                and len(resp.text) > MIN_REAL_PAGE_BYTES
            ):
                return resp.text
            if attempt < FETCH_ATTEMPTS_PER_STRATEGY - 1:
                time.sleep(random.uniform(*RETRY_DELAY_RANGE))
    raise ListingFetchError(
        "Amazon blocked every attempt to load this product page (bot-check "
        "interstitial), on both the mobile and desktop page. Rare, but it "
        "happens on individual product pages more than on category pages -- "
        "try again in a moment."
    )


def _clean_text(raw):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw))).strip()


def parse_listing(page_html):
    # Title marker differs between the mobile page (<span id="title">,
    # tried first since that's the page fetched first) and the desktop page
    # (id="productTitle") -- try both rather than assuming which one this
    # HTML came from.
    title = None
    for pattern in (r'<span id="title"[^>]*>\s*(.*?)\s*</span>', r'id="productTitle"[^>]*>\s*(.*?)\s*</span>'):
        m = re.search(pattern, page_html, re.S)
        if m:
            title = _clean_text(m.group(1))
            break

    bullets = []
    m = re.search(r'id="feature-bullets"(.*?)id="[a-zA-Z]', page_html, re.S)
    if m:
        for span in re.findall(r'<span class="a-list-item">\s*(.*?)\s*</span>', m.group(1), re.S):
            text = _clean_text(span)
            if text:
                bullets.append(text)

    # data-num-of-images is the mobile page's own image count attribute;
    # hiRes-URL counting is the desktop-page fallback.
    m = re.search(r'data-num-of-images="(\d+)"', page_html)
    image_count = int(m.group(1)) if m else len(set(re.findall(r'"hiRes":"([^"]+)"', page_html)))

    rating = None
    m = re.search(r"([\d.]+) out of 5 stars", page_html)
    if m:
        rating = float(m.group(1))

    return {
        "title": title,
        "bullets": bullets,
        "image_count": image_count,
        "rating": rating,
        "reviews": _extract_reviews(page_html),
    }


_REVIEW_BOILERPLATE = (
    "Brief content visible, double tap to read full content.",
    "Full content visible, double tap to read brief content.",
)


def _extract_reviews(page_html):
    """Amazon's own embedded "top reviews" on the mobile product page --
    only found there, not on the desktop page (verified: the desktop page
    has zero review text anywhere in its server-rendered HTML). Typically
    6-10 of Amazon's own featured reviews, each with real text and a
    matching star rating, extracted from the exact same page fetch
    fetch_detail_page() already made -- no second request. This is NOT the
    complete review history (the dedicated reviews page redirects to
    Amazon's login page, a real policy wall, not a bot-block workaround),
    but it's real, unfabricated customer feedback, not a sample of one."""
    texts = re.findall(r'data-hook="reviewText"[^>]*>(.*?)</div>\s*</div>', page_html, re.S)
    stars = re.findall(
        r'data-hook="review-star-rating"[^>]*>\s*<span[^>]*>([\d.]+) out of 5 stars</span>',
        page_html, re.S,
    )

    reviews = []
    seen = set()
    for i, raw in enumerate(texts):
        text = _clean_text(raw)
        for boilerplate in _REVIEW_BOILERPLATE:
            text = text.replace(boilerplate, "")
        text = text.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        reviews.append({"text": text, "rating": float(stars[i]) if i < len(stars) else None})
    return reviews


def _title_check(title):
    if not title:
        return 0.0, ["Could not read the product title from the page."]
    gaps = []
    length = len(title)
    if length < TITLE_MIN_LEN:
        score = 50.0
        gaps.append(f"Title is short ({length} chars) -- likely under-using available keyword space.")
    elif length > TITLE_MAX_LEN:
        score = 70.0
        gaps.append(f"Title is long ({length} chars) -- risks truncation or suppression in some categories.")
    else:
        score = 100.0
    if re.search(r"([A-Za-z])\1{3,}", title) or title.count("!") > 2:
        score = min(score, 60.0)
        gaps.append("Title has unusual repeated characters or excess punctuation.")
    return score, gaps


def _bullets_check(bullets):
    count = len(bullets)
    if count == 0:
        return 0.0, ["No bullet points found -- a major gap, this is prime real estate for conversion."]
    gaps = []
    if count < BULLET_TARGET_COUNT:
        gaps.append(f"Only {count}/5 bullet points used -- Amazon allows 5.")
    short = [b for b in bullets if len(b) < BULLET_MIN_LEN]
    if short:
        gaps.append(f"{len(short)} bullet(s) are quite short (<{BULLET_MIN_LEN} chars) -- likely thin on detail.")
    score = max(0.0, min(100.0, (count / BULLET_TARGET_COUNT) * 100 - len(short) * 8))
    return score, gaps


def _images_check(image_count):
    if image_count == 0:
        return 30.0, ["Could not detect product images on the page -- worth checking manually."]
    if image_count < IMAGE_TARGET_COUNT:
        return 60.0, [f"Only {image_count} images detected -- Amazon recommends 6-9 for a full visual story."]
    return 100.0, []


def _category_benchmark(table, own_price, own_reviews):
    if table is None or table.empty:
        return None

    result = {}
    if own_price is not None:
        prices = table["price"].dropna()
        if len(prices) >= 3:
            result["price_percentile"] = round((prices < own_price).mean() * 100)
            result["category_median_price"] = round(float(prices.median()), 2)
    if own_reviews is not None:
        reviews = table["review_count"].dropna()
        if len(reviews) >= 3:
            result["review_percentile"] = round((reviews < own_reviews).mean() * 100)
            result["category_median_reviews"] = int(reviews.median())
    return result or None


def _top_peers(table, exclude_asin, limit=8):
    """Top-ranked category peers (rank/price/rating/reviews), for Ram to
    actually see who he's up against rather than just a percentile number.
    Reuses the same category_table() fetch _category_benchmark() uses --
    no extra scraping or DB query, just surfacing data Scout already has."""
    if table is None or table.empty:
        return []
    peers = table[table["asin"] != exclude_asin].head(limit)
    records = []
    for _, row in peers.iterrows():
        records.append({
            "asin": row["asin"],
            "title": row["title"],
            "rank": int(row["rank"]) if pd.notna(row["rank"]) else None,
            "price": float(row["price"]) if pd.notna(row["price"]) else None,
            "rating": float(row["rating"]) if pd.notna(row["rating"]) else None,
            "review_count": int(row["review_count"]) if pd.notna(row["review_count"]) else None,
        })
    return records


def analyze_listing(asin, category=None):
    page_html = fetch_detail_page(asin)
    parsed = parse_listing(page_html)

    # Reuse Scout's own tracked data for this ASIN where available, rather
    # than re-deriving price/reviews from the live page -- it's the same
    # data source collector.py already trusts, and saves re-parsing prices
    # off a page layout that varies a lot more than the bestseller lists.
    snap = db.get_latest_snapshot(asin)
    own_price = snap.get("price") if snap else None
    own_rating = parsed["rating"] or (snap.get("rating") if snap else None)
    own_reviews = snap.get("review_count") if snap else None
    resolved_category = category or (snap.get("category") if snap else None)
    list_type = snap.get("list_type") if snap else "bestsellers"

    title_score, title_gaps = _title_check(parsed["title"])
    bullets_score, bullets_gaps = _bullets_check(parsed["bullets"])
    images_score, images_gaps = _images_check(parsed["image_count"])

    components = {
        "title": round(title_score),
        "bullets": round(bullets_score),
        "images": round(images_score),
    }
    overall = round(sum(components.values()) / len(components))
    gaps = title_gaps + bullets_gaps + images_gaps

    table = (
        trend_radar.category_table(resolved_category, list_type=list_type or "bestsellers")
        if resolved_category else pd.DataFrame()
    )
    benchmark = _category_benchmark(table, own_price, own_reviews)
    if benchmark:
        if benchmark.get("price_percentile", 0) >= 80:
            gaps.append(
                f"Priced higher than {benchmark['price_percentile']}% of this category's top "
                f"sellers (category median ₹{benchmark['category_median_price']:.0f})."
            )
        if benchmark.get("review_percentile") is not None and benchmark["review_percentile"] <= 20:
            gaps.append(
                f"Review count is in the bottom {benchmark['review_percentile']}% of this "
                f"category's top sellers -- expect an uphill trust battle at launch."
            )
    peers = _top_peers(table, asin)

    return {
        "asin": asin,
        "title": parsed["title"],
        "category": resolved_category,
        "score": overall,
        "components": components,
        "bullets": parsed["bullets"],
        "image_count": parsed["image_count"],
        "rating": own_rating,
        "price": own_price,
        "review_count": own_reviews,
        "benchmark": benchmark,
        "peers": peers,
        "reviews": parsed["reviews"],
        "gaps": gaps,
    }


REVIEW_SUMMARY_ATTEMPTS = 3
MIN_REVIEWS_FOR_SUMMARY = 3


def summarize_reviews(reviews):
    """AI-clustered pros/cons from the review snippets _extract_reviews()
    pulled off the same page fetch as the listing score -- see that
    function's docstring for what these are and aren't. Returns None if AI
    isn't configured, there aren't enough reviews to say anything
    meaningful, or every retry attempt fails to produce something usable."""
    usable = [r for r in reviews if r.get("text")]
    if not ai_client.is_configured() or len(usable) < MIN_REVIEWS_FOR_SUMMARY:
        return None

    review_text = "\n".join(f"- ({r['rating']}★) {r['text']}" for r in usable)
    user_prompt = (
        f"Here are {len(usable)} real customer reviews for an Amazon India product "
        f"(Amazon's own featured reviews, not the full history):\n{review_text}\n\n"
        "Summarize the recurring PROS and CONS customers actually mention. Only include "
        "points that genuinely appear in the reviews above -- never invent feedback that "
        "isn't there. Do not show your reasoning or thinking -- reply with ONLY the final "
        "list, in exactly this format and nothing else (this is an example to show the "
        "format, write your own real points, don't copy it):\n"
        "PROS:\n- Tastes great\n- Good value for money\nCONS:\n- Packaging could be sturdier"
    )
    system_prompt = (
        "You analyze real Amazon customer reviews to extract recurring themes. Only "
        "summarize what's actually said -- never invent feedback. Output ONLY the final "
        "PROS/CONS list in the requested format -- no reasoning, no preamble, no restating "
        "the reviews."
    )

    best = None
    for _ in range(REVIEW_SUMMARY_ATTEMPTS):
        raw = ai_client.chat(system_prompt, user_prompt)
        # A clean response is a short bulleted list; anything this long is
        # almost certainly a reasoning model dumping its chain-of-thought
        # instead of following the format -- verified in production (one
        # response included lines like "But the user wants recurring
        # themes... However, in the example format..."). Skip parsing it
        # rather than risk that leaking into "cons".
        if not raw or len(raw) > 1200:
            continue

        pros_match = re.search(r"PROS:\s*(.*?)(?:CONS:|$)", raw, re.S)
        cons_match = re.search(r"CONS:\s*(.*)", raw, re.S)
        pros = _parse_bullet_lines(pros_match.group(1)) if pros_match else []
        cons = _parse_bullet_lines(cons_match.group(1)) if cons_match else []

        if not pros and not cons:
            continue

        candidate = {"pros": pros, "cons": cons}
        if len(pros) >= 2 and len(cons) >= 1:
            return candidate
        if best is None or (len(pros) + len(cons)) > (len(best["pros"]) + len(best["cons"])):
            best = candidate

    return best


_REASONING_LEAK_MARKERS = re.compile(
    r"\b(let me|i need to|the user|however|so i should|but the|recurring pros|recurring cons"
    r"|mentioned in review|reviews? \d)",
    re.IGNORECASE,
)
# Catches a reasoning model quoting one of the *input* reviews back verbatim
# (e.g. "1. (5.0★) Excellent taste") instead of writing a synthesized point --
# verified in production, slipped past the markers above since it's not
# meta-commentary, just an echoed numbered input line.
_QUOTED_REVIEW_ECHO = re.compile(r"^\d+\.\s*\([\d.]+\s*(star|★)", re.IGNORECASE)


def _parse_bullet_lines(block):
    lines = [html.unescape(line.strip(" -•").strip()) for line in block.splitlines()]
    return [
        line for line in lines
        if line
        and len(line) <= 160
        and not _is_placeholder_echo(line)
        and not _REASONING_LEAK_MARKERS.search(line)
        and not _QUOTED_REVIEW_ECHO.match(line)
    ]


def suggest_improvements(title, bullets, category, gaps):
    """Separate step from analyze_listing() on purpose: this is the one AI
    call in Scout, hitting a free-tier router that can be slow or flaky, and
    it shouldn't hold up or risk the rule-based score, which already works
    reliably on its own. Takes the already-scraped listing info (no re-fetch
    of the Amazon page) and asks for a rewritten title + up to 5 bullets.
    Returns None if AI isn't configured, or if the call fails, or if the
    response couldn't be parsed into anything usable -- never a fabricated
    or partially-garbled suggestion."""
    if not ai_client.is_configured():
        return None

    bullet_text = "\n".join(f"- {b}" for b in bullets) if bullets else "(none found)"
    gap_text = "\n".join(f"- {g}" for g in gaps) if gaps else "- (no major gaps flagged)"
    user_prompt = (
        f"Category: {category or 'unknown'}\n"
        f"Current title: {title or '(missing)'}\n"
        f"Current bullet points:\n{bullet_text}\n\n"
        f"Automated quality checks flagged these gaps:\n{gap_text}\n\n"
        "Suggest ONE improved title (under 200 characters) and up to 5 improved "
        "bullet points for this Amazon India listing, addressing the flagged gaps. "
        "Be concrete and specific to this actual product, not generic filler. "
        "Reply in exactly this format and nothing else:\n"
        "SUGGESTED TITLE: <title>\n"
        "SUGGESTED BULLETS:\n"
        "1. <bullet>\n2. <bullet>\n3. <bullet>\n4. <bullet>\n5. <bullet>"
    )
    system_prompt = (
        "You are an experienced Amazon India listing copywriter. Follow the "
        "requested reply format exactly, with no preamble or extra commentary."
    )

    # openrouter/free picks a random free model per call -- verified in
    # production this can go wrong two different ways: a non-instruct model
    # (a content-safety classifier replied "User Safety: safe" instead of
    # writing anything), or an instruct model that echoes the prompt's own
    # <title>/<bullet> placeholder markers back verbatim instead of filling
    # them in. Retry a few times (each retry re-rolls the random pick)
    # rather than surfacing whatever garbage the first roll returns, and
    # reject placeholder echoes explicitly since they'd otherwise "parse"
    # successfully as fake real content.
    best = None
    for _ in range(SUGGEST_ATTEMPTS):
        raw = ai_client.chat(system_prompt, user_prompt)
        if not raw:
            continue

        title_match = re.search(r"SUGGESTED TITLE:\s*(.+)", raw)
        suggested_title = html.unescape(title_match.group(1).strip()) if title_match else None
        suggested_bullets = [
            html.unescape(b.strip()) for b in re.findall(r"^\d+\.\s*(.+)$", raw, re.MULTILINE)
        ][:5]

        if suggested_title and _is_placeholder_echo(suggested_title):
            suggested_title = None
        suggested_bullets = [b for b in suggested_bullets if not _is_placeholder_echo(b)]

        if not suggested_title and not suggested_bullets:
            continue

        candidate = {"title": suggested_title, "bullets": suggested_bullets}
        if suggested_title and len(suggested_bullets) >= 3:
            return candidate  # good enough, stop rolling

        if best is None or len(suggested_bullets) > len(best["bullets"]):
            best = candidate

    return best


def _is_placeholder_echo(text):
    """Catches a model echoing a prompt's own format markers back verbatim
    instead of writing real content -- both angle-bracket style ("<title>",
    "<bullet>") and bare placeholder words used in prompts elsewhere in
    this module ("point"). Real product copy essentially never contains
    angle brackets or is literally just the word "point", so this is a
    safe, simple filter."""
    stripped = text.strip().strip("<>[]").strip().lower()
    return "<" in text or ">" in text or stripped in {"title", "bullet", "point"}
