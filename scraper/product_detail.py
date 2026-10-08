"""Shared product-page validation and immutable observation storage."""
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

ASIN = re.compile(r"^[A-Z0-9]{10}$")


def stock_state(text):
    text = (text or "").lower()
    if any(word in text for word in ("unavailable", "out of stock", "not available", "sold out")):
        return 0
    if "in stock" in text or "available to ship" in text:
        return 1
    return None


def parse_detail(page_html, asin, *, schema_category=None, schema_product_type=None,
                 schema_context=None):
    if not ASIN.fullmatch(asin):
        raise ValueError("Invalid ASIN")
    soup = BeautifulSoup(page_html, "html.parser")
    identity = soup.select_one('input#ASIN, input[name="ASIN"]')
    identity_value = identity.get("value", "").strip().upper() if identity else None
    if identity_value and identity_value != asin:
        raise ValueError("Product page ASIN differs from requested ASIN")
    canonical = soup.select_one('link[rel="canonical"]')
    match = re.search(r"/dp/([A-Z0-9]{10})", canonical.get("href", "")) if canonical else None
    if match and match.group(1) != asin:
        raise ValueError("Canonical product differs from requested ASIN")
    if identity is not None and not identity_value and not match:
        raise ValueError("Blank ASIN input requires a matching canonical product URL")
    title = soup.select_one("#productTitle")
    if not title:
        raise ValueError("No product title: blocked or unsupported page")
    data = {"asin": asin, "title": title.get_text(" ", strip=True),
            "collected_at": datetime.now(timezone.utc).isoformat()}
    brand = soup.select_one("#bylineInfo")
    if brand:
        value = brand.get_text(" ", strip=True)
        value = re.sub(r"^Visit the (.*?) Store$", r"\1", value, flags=re.I)
        value = re.sub(r"^Brand\s*:\s*", "", value, flags=re.I)
        data["brand"] = value
    for selector in ("#corePriceDisplay_desktop_feature_div .a-price:not(.a-text-price) .a-offscreen",
                     "#corePrice_feature_div .a-price:not(.a-text-price) .a-offscreen",
                     "#priceblock_ourprice", "#priceblock_dealprice",
                     "#centerCol .a-price:not(.a-text-price) .a-offscreen"):
        element = soup.select_one(selector)
        if element:
            match = re.search(r"(?:â‚¹|INR|Rs\.?)?\s*([\d,]+(?:\.\d{1,2})?)", element.get_text())
            if match:
                price = float(match.group(1).replace(",", ""))
                if 0 < price <= 10_000_000:
                    data["price"] = price
                    break
    if "price" not in data:
        whole = soup.select_one("#centerCol .a-price:not(.a-text-price) .a-price-whole")
        if whole:
            digits = re.sub(r"[^\d]", "", whole.get_text())
            fraction = whole.parent.select_one(".a-price-fraction")
            cents = re.sub(r"[^\d]", "", fraction.get_text()) if fraction else "00"
            if digits and len(cents) <= 2:
                value = float(digits + "." + cents.ljust(2, "0"))
                if 0 < value <= 10_000_000:
                    data["price"] = value
    availability = soup.select_one("#availability, #outOfStock")
    if availability:
        text = availability.get_text(" ", strip=True)
        data["availability_text"] = text[:200]
        data["in_stock"] = stock_state(text)
        if data["in_stock"] == 0:
            data.pop("price", None)
    rating = soup.select_one("#acrPopover, #averageCustomerReviews .a-icon-alt")
    if rating:
        match = re.search(r"([0-5](?:\.\d+)?)", rating.get("title") or rating.get_text())
        if match:
            data["rating"] = float(match.group(1))
    reviews = soup.select_one("#acrCustomerReviewText, [data-hook='total-review-count']")
    if reviews:
        match = re.search(r"[\d,]+", reviews.get_text())
        if match:
            data["review_count"] = int(match.group().replace(",", ""))
    seller = soup.select_one("#sellerProfileTriggerId, #merchant-info, #merchantInfoText")
    if seller:
        data["seller"] = seller.get_text(" ", strip=True)[:200]
    image = soup.select_one("#landingImage, #imgBlkFront")
    if image:
        data["image_url"] = image.get("data-old-hires") or image.get("src")
    if schema_category:
        from registry.amazon_schema import AmazonSchema
        from registry.category_mapper import CategoryMapper
        mapped = CategoryMapper().map(asin, title=data['title'], existing_category=schema_category)
        schema_product_type = schema_product_type or mapped.get('product_type')
        if schema_product_type:
            data['product_type'] = schema_product_type
        if mapped.get('subcategory'):
            data['subcategory'] = mapped['subcategory']
        pairs = []
        for table in soup.select('#productDetails_techSpec_section_1, #productDetails_techSpec_section_2, #productDetails_detailBullets_sections1, #productOverview_feature_div, #productDetails_feature_div table'):
            for row in table.select('tr'):
                cells = row.select('th, td')
                if len(cells) == 2:
                    pairs.append(tuple(cell.get_text(' ', strip=True).replace('\u200e', '').strip() for cell in cells))
        for li in soup.select('#detailBullets_feature_div li'):
            text = li.get_text(' ', strip=True).replace('\u200e', '')
            if ':' in text:
                label, value = text.split(':', 1)
                pairs.append((label.strip(), value.strip()))
        data['attribute_observations'] = AmazonSchema().extract_specifications(
            pairs, category=schema_category, product_type=schema_product_type,
            source_url=f'https://www.amazon.in/dp/{asin}', context=schema_context)
        data['attribute_observations']['classification_evidence'] = {
            'source':mapped.get('source'), 'confidence':mapped.get('confidence'),
            'product_type':schema_product_type, 'provided_category':schema_category}
        surface = {}
        bullets = [item.get_text(' ', strip=True) for item in soup.select('#feature-bullets li .a-list-item')]
        bullets = [text for text in bullets if text and text != 'See more product details']
        if bullets:
            surface['bullets'] = bullets
        description = soup.select_one('#productDescription')
        if description and description.get_text(' ', strip=True):
            surface['description'] = description.get_text(' ', strip=True)
        for key, raw in surface.items():
            data['attribute_observations']['observations'].append(AmazonSchema().observation(
                key, raw, category=schema_category, product_type=schema_product_type,
                source_url=f'https://www.amazon.in/dp/{asin}', context=schema_context))
        if pairs:
            data['attribute_observations']['observations'].append(AmazonSchema().observation(
                'technical_specs', {'entries':[{'label':label,'value':value} for label,value in pairs]},
                category=schema_category,product_type=schema_product_type,
                source_url=f'https://www.amazon.in/dp/{asin}',context=schema_context))
    return data


def get_targets(days=None, limit=100, top_rank=None):
    import db
    if days is not None and days < 1:
        raise ValueError("days must be positive")
    if limit < 1:
        raise ValueError("limit must be positive")
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT asin, category, title, rank FROM (
                    SELECT DISTINCT ON (asin) asin, category, title, rank,
                        collected_at
                    FROM snapshots WHERE list_type <> 'product-detail'
                    ORDER BY asin, collected_at DESC, id DESC
                ) latest
                WHERE (%s IS NULL OR collected_at >= NOW() - %s * INTERVAL '1 day')
                  AND (%s IS NULL OR rank <= %s)
                  AND NOT EXISTS (SELECT 1 FROM snapshots detail
                      WHERE detail.asin=latest.asin AND detail.list_type='product-detail'
                        AND detail.collected_at >= NOW() - INTERVAL '1 day')
                ORDER BY collected_at DESC, asin LIMIT %s
            """, (days, days, top_rank, top_rank, limit))
            return [{"asin": row[0], "category": row[1], "title": row[2], "rank": row[3]}
                    for row in cur.fetchall()]


def save_observation(data, category=None):
    """Append a newly timed product-detail row; never update an older capture."""
    import db
    if not data.get("title") or not ASIN.fullmatch(data.get("asin", "")):
        raise ValueError("Cannot store an unidentified product page")
    if category is None:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT category FROM snapshots WHERE asin=%s "
                            "ORDER BY collected_at DESC, id DESC LIMIT 1", (data["asin"],))
                row = cur.fetchone()
                if not row:
                    raise ValueError("No category configured for this ASIN")
                category = row[0]
    observed_at = data.get("collected_at") or datetime.now(timezone.utc).isoformat()
    row = {**data, "category": category, "list_type": "product-detail",
           "rank": None, "source": "product-page", "collected_at": observed_at}
    for key in ("price", "rating", "review_count", "image_url"):
        row.setdefault(key, None)
    from registry.observation_store import ObservationStore, deliver
    store = ObservationStore()
    store.enqueue([row])
    # Both insert and detail update commit together. Replay uses the same timestamp.
    fields = ("in_stock", "availability_text", "seller", "fulfillment", "dimensions",
              "weight", "material", "warranty", "bsr_rank", "bsr_category", "ram", "storage", "processor",
              "display_size", "battery_capacity", "fabric", "net_weight", "ingredients")
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO snapshots
                (asin,category,list_type,rank,title,price,rating,review_count,image_url,
                 collected_at,brand,subcategory,product_type,source)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING RETURNING id""",
                tuple(row.get(key) for key in ("asin", "category", "list_type", "rank", "title",
                      "price", "rating", "review_count", "image_url", "collected_at", "brand",
                      "subcategory", "product_type", "source")))
            inserted = cur.fetchone()
            if not inserted:
                return 0
            selected = [key for key in fields if key in data]
            if selected:
                cur.execute("UPDATE snapshots SET " + ", ".join(key + "=%s" for key in selected)
                            + ", enriched_at=NOW() WHERE id=%s",
                            tuple(data[key] for key in selected) + (inserted[0],))
            else:
                cur.execute("UPDATE snapshots SET enriched_at=NOW() WHERE id=%s", (inserted[0],))
            accepted = deliver(cur, store.pending())
    store.acknowledge(accepted)
    return 1
