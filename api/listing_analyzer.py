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
Verified directly before building this: Amazon's bot detection on individual
/dp/{asin} pages is meaningfully stricter than on the bestseller/list pages
collector.py already reads reliably -- roughly half of direct requests came
back as a "Continue shopping" interstitial instead of the real page, even
with a warmed-up session and matching headers. A short retry (this is a
single on-demand request, not a 124-fetch nightly run, so a couple of
spaced-out attempts is a reasonable budget) got through on the 3rd try in
testing. If every attempt is still blocked, this raises ListingFetchError
rather than silently returning an empty or fabricated score -- Ram sees an
honest "try again" message.
"""

import html
import random
import re
import time

import requests

import ai_client
import db
import trend_radar

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}

FETCH_ATTEMPTS = 3
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
    for attempt in range(FETCH_ATTEMPTS):
        resp = requests.get(f"https://www.amazon.in/dp/{asin}", headers=HEADERS, timeout=20)
        if (
            resp.status_code == 200
            and "Continue shopping" not in resp.text
            and len(resp.text) > MIN_REAL_PAGE_BYTES
        ):
            return resp.text
        if attempt < FETCH_ATTEMPTS - 1:
            time.sleep(random.uniform(*RETRY_DELAY_RANGE))
    raise ListingFetchError(
        "Amazon blocked every attempt to load this product page (bot-check "
        "interstitial). This happens on individual product pages more than "
        "on category pages -- try again in a moment."
    )


def _clean_text(raw):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw))).strip()


def parse_listing(page_html):
    title = None
    m = re.search(r'id="productTitle"[^>]*>\s*(.*?)\s*</span>', page_html, re.S)
    if m:
        title = _clean_text(m.group(1))

    bullets = []
    m = re.search(r'id="feature-bullets"(.*?)id="[a-zA-Z]', page_html, re.S)
    if m:
        for span in re.findall(r'<span class="a-list-item">\s*(.*?)\s*</span>', m.group(1), re.S):
            text = _clean_text(span)
            if text:
                bullets.append(text)

    image_count = len(set(re.findall(r'"hiRes":"([^"]+)"', page_html)))

    rating = None
    m = re.search(r"([\d.]+) out of 5 stars", page_html)
    if m:
        rating = float(m.group(1))

    return {"title": title, "bullets": bullets, "image_count": image_count, "rating": rating}


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


def _category_benchmark(category, list_type, own_price, own_reviews):
    if not category:
        return None
    table = trend_radar.category_table(category, list_type=list_type or "bestsellers")
    if table.empty:
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

    benchmark = _category_benchmark(resolved_category, list_type, own_price, own_reviews)
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
        "gaps": gaps,
    }


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

    # openrouter/free picks a random free model per call -- including, in
    # testing, a content-safety classifier that replied "User Safety: safe"
    # instead of writing anything. A bad pick isn't rare enough to ignore,
    # so retry a few times (each retry re-rolls the random pick) rather than
    # surfacing whatever garbage the first roll happened to return. Keeps
    # the best partial result seen across attempts instead of an all-or-nothing.
    best = None
    for _ in range(SUGGEST_ATTEMPTS):
        raw = ai_client.chat(system_prompt, user_prompt)
        if not raw:
            continue

        title_match = re.search(r"SUGGESTED TITLE:\s*(.+)", raw)
        suggested_title = title_match.group(1).strip() if title_match else None
        suggested_bullets = [b.strip() for b in re.findall(r"^\d+\.\s*(.+)$", raw, re.MULTILINE)][:5]

        if not suggested_title and not suggested_bullets:
            continue

        candidate = {"title": suggested_title, "bullets": suggested_bullets}
        if suggested_title and len(suggested_bullets) >= 3:
            return candidate  # good enough, stop rolling

        if best is None or len(suggested_bullets) > len(best["bullets"]):
            best = candidate

    return best
