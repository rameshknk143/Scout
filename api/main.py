"""
Scout's business-logic API. Thin FastAPI wrapper around the same
profit_calculator / scorer / trend_radar logic Scout has always used —
only the data layer (db.py) changed, to talk to Supabase instead of a
local SQLite file.

Every endpoint except /health requires an X-Scout-Key header matching the
API_KEY environment variable. The Next.js frontend calls this server-side
(Server Components / Server Actions), so the key never reaches the browser
bundle. Still worth knowing: it's one shared key for a single personal user,
not a real per-user auth model — fine for this tool's scope, not something
to reuse if it ever stopped being personal-only.
"""

import html
import math
import os
import re

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import alerts
import db
import listing_analyzer
import profit_calculator
import scorer
import trend_radar

API_KEY = os.environ["API_KEY"]

# Developer sideload testing only. Never set on Render — with the flag absent,
# the mock-code path below cannot be reached in production.
ALLOW_MOCK_LWA = os.environ.get("ALLOW_MOCK_LWA") == "1"

# Amazon ASINs are exactly 10 chars, A-Z/0-9. Validating before the value is
# interpolated into amazon.in URLs or used in queries keeps those paths inert.
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


def clean_asin(asin: str) -> str:
    asin = (asin or "").strip().upper()
    if not ASIN_RE.match(asin):
        raise HTTPException(status_code=400, detail=f"Invalid ASIN format: {asin!r}")
    return asin

# Keep in sync with scraper/collector.py's CATEGORIES dict keys.
CATEGORIES = [
    "Electronics Accessories", "Home & Kitchen", "Beauty & Personal Care",
    "Sports & Fitness", "Toys & Games", "Stationery/Office", "Pet Supplies",
    "Car Accessories", "Garden & Outdoors", "Baby Products", "Watches & Gifting",
    "Clothing & Accessories", "Amazon Launchpad", "Amazon Renewed",
    "Apps & Games", "Bags, Wallets & Luggage", "Books", "Computers & Accessories",
    "Gift Cards", "Grocery & Gourmet Foods", "Health & Personal Care",
    "Home Improvement", "Industrial & Scientific", "Jewellery", "Kindle Store",
    "Movies & TV Shows", "Music", "Musical Instruments", "Shoes & Handbags",
    "Software", "Video Games",
]

app = FastAPI(title="Scout API")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_key(x_scout_key: str = Header(default="")):
    if x_scout_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Scout-Key header")


def df_to_records(df: pd.DataFrame):
    if df is None or df.empty:
        return []
    clean = df.replace({math.nan: None})
    for col in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[col]):
            clean[col] = clean[col].astype(str)
    records = clean.to_dict(orient="records")
    # dates (python datetime.date objects from trend_radar's collected_date column, if present)
    for r in records:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
            elif isinstance(v, float) and math.isnan(v):
                r[k] = None
            elif k == "title" and isinstance(v, str):
                # some titles were collected before html.unescape() was added
                # to collector.py — decode on read so old rows display clean too
                r[k] = html.unescape(v)
    return records


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/trend-radar/categories", dependencies=[Depends(require_key)])
def get_categories():
    return {"categories": CATEGORIES}


@app.get("/trend-radar/digest", dependencies=[Depends(require_key)])
def get_digest():
    digest = trend_radar.weekly_digest()
    return {
        "new_entrants": df_to_records(digest["new_entrants"]),
        "top_movers": df_to_records(digest["top_movers"]),
        "cross_category": df_to_records(digest["cross_category"]),
        "collection_dates": [d.isoformat() for d in digest["collection_dates"]],
    }


@app.get("/trend-radar/category/{category}", dependencies=[Depends(require_key)])
def get_category_table(category: str, list_type: str = "bestsellers"):
    table = trend_radar.category_table(category, list_type=list_type)
    return {"category": category, "list_type": list_type, "products": df_to_records(table)}


class ScoreRequest(BaseModel):
    asin: str
    buy_price: float
    category: str | None = None
    weight_grams: int = scorer.DEFAULT_WEIGHT_GRAMS
    fulfillment: str = scorer.DEFAULT_FULFILLMENT
    gst_rate_pct: int = scorer.DEFAULT_GST_RATE_PCT
    zone: str = scorer.DEFAULT_ZONE
    differentiation: int = 3
    operational_fit: int = 3
    notes: str = ""


@app.post("/validator/score", dependencies=[Depends(require_key)])
def score_asin(req: ScoreRequest):
    return scorer.score_asin(
        asin=clean_asin(req.asin),
        buy_price=req.buy_price,
        category=req.category,
        weight_grams=req.weight_grams,
        fulfillment=req.fulfillment,
        gst_rate_pct=req.gst_rate_pct,
        zone=req.zone,
        differentiation=req.differentiation,
        operational_fit=req.operational_fit,
        notes=req.notes,
    )


@app.get("/watchlist", dependencies=[Depends(require_key)])
def get_watchlist():
    df = db.get_all_validations_df()
    records = df_to_records(df)
    for r in records:
        snap = db.get_latest_snapshot(r["asin"])
        r["price"] = snap["price"] if snap else None
        r["review_count"] = snap["review_count"] if snap else None
    return {"validations": records}


class WatchlistNotesRequest(BaseModel):
    asin: str
    notes: str


@app.post("/watchlist/notes", dependencies=[Depends(require_key)])
def update_watchlist_notes(req: WatchlistNotesRequest):
    db.update_validation_notes(req.asin, req.notes)
    return {"ok": True}


class AmazonCallbackRequest(BaseModel):
    code: str
    selling_partner_id: str
    marketplace_id: str = "A21TJRUUN4KGV"


@app.post("/auth/amazon/callback", dependencies=[Depends(require_key)])
def amazon_callback(req: AmazonCallbackRequest):
    import requests
    lwa_url = "https://api.amazon.com/auth/o2/token"
    client_id = os.environ.get("LWA_CLIENT_ID")
    client_secret = os.environ.get("LWA_CLIENT_SECRET")
    
    if ALLOW_MOCK_LWA and req.code.startswith("mock"):
        # Developer testing/sideload bypass — only reachable when ALLOW_MOCK_LWA=1
        # is explicitly set (never on Render), so it can't be triggered in prod.
        refresh_token = "mock_refresh_token_sideloaded_12345"
    else:
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=500,
                detail="Scout application credentials (LWA_CLIENT_ID / LWA_CLIENT_SECRET) are not configured on the Render server."
            )
            
        payload = {
            "grant_type": "authorization_code",
            "code": req.code,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        res = requests.post(lwa_url, data=payload)
        if res.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {res.text}"
            )
            
        tokens = res.json()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Amazon did not return a refresh token. Make sure you approved all requested catalog and order permissions."
            )
        
    db.save_seller_credentials(
        selling_partner_id=req.selling_partner_id,
        refresh_token=refresh_token,
        marketplace_id=req.marketplace_id
    )
    return {"ok": True, "selling_partner_id": req.selling_partner_id}


@app.get("/auth/amazon/status", dependencies=[Depends(require_key)])
def amazon_status():
    credentials = db.get_seller_credentials()
    connected = len(credentials) > 0
    return {
        "connected": connected,
        "accounts": [
            {
                "selling_partner_id": c["selling_partner_id"],
                "marketplace_id": c["marketplace_id"],
                "connected_at": c["connected_at"]
            } for c in credentials
        ]
    }


@app.get("/alerts", dependencies=[Depends(require_key)])
def get_alerts():
    return {"alerts": alerts.compute_alerts()}


class ListingAnalyzeRequest(BaseModel):
    asin: str
    category: str | None = None


@app.post("/listing/analyze", dependencies=[Depends(require_key)])
def analyze_listing(req: ListingAnalyzeRequest):
    try:
        return listing_analyzer.analyze_listing(clean_asin(req.asin), category=req.category)
    except listing_analyzer.ListingFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))


class ListingSuggestRequest(BaseModel):
    title: str | None = None
    bullets: list[str] = []
    category: str | None = None
    gaps: list[str] = []


@app.post("/listing/suggest", dependencies=[Depends(require_key)])
def suggest_listing_improvements(req: ListingSuggestRequest):
    suggestions = listing_analyzer.suggest_improvements(
        req.title, req.bullets, req.category, req.gaps
    )
    if suggestions is None:
        raise HTTPException(
            status_code=503,
            detail="AI suggestions aren't available right now (no key configured, or the free model didn't respond) -- the quality score above doesn't depend on this.",
        )
    return suggestions


class ReviewItem(BaseModel):
    text: str
    rating: float | None = None


class ReviewSummaryRequest(BaseModel):
    reviews: list[ReviewItem] = []


@app.post("/listing/review-summary", dependencies=[Depends(require_key)])
def summarize_reviews(req: ReviewSummaryRequest):
    summary = listing_analyzer.summarize_reviews([r.model_dump() for r in req.reviews])
    if summary is None:
        raise HTTPException(
            status_code=503,
            detail="Couldn't summarize reviews right now (too few reviews found on the page, no AI key configured, or the free model didn't respond).",
        )
    return summary


class ProfitCalcRequest(BaseModel):
    sell_price: float
    buy_price: float
    category: str
    weight_grams: int
    fulfillment: str
    gst_rate_pct: int
    zone: str = "national"
    is_oversize: bool = False
    returns_pct: float = 5
    ppc_per_unit: float = 0
    own_shipping_cost: float = 0


@app.post("/profit-calculator", dependencies=[Depends(require_key)])
def calc_profit(req: ProfitCalcRequest):
    return profit_calculator.calculate(
        sell_price=req.sell_price,
        buy_price=req.buy_price,
        category=req.category,
        weight_grams=req.weight_grams,
        fulfillment=req.fulfillment,
        gst_rate_pct=req.gst_rate_pct,
        zone=req.zone,
        is_oversize=req.is_oversize,
        returns_pct=req.returns_pct,
        ppc_per_unit=req.ppc_per_unit,
        own_shipping_cost=req.own_shipping_cost,
    )


@app.get("/product-database", dependencies=[Depends(require_key)])
def get_product_database(
    q: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    min_rank: int = None,
    max_rank: int = None,
    limit: int = 100,
    offset: int = 0,
):
    products = db.query_snapshots(
        query_text=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rank=min_rank,
        max_rank=max_rank,
        limit=limit,
        offset=offset,
    )
    total = db.count_snapshots(
        query_text=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rank=min_rank,
        max_rank=max_rank,
    )
    return {"products": products, "total": total}


class MyProductRequest(BaseModel):
    asin: str
    title: str | None = None
    sku: str | None = None
    supplier_cost: float = 0.0
    shipping_fee: float = 0.0
    target_margin: float = 30.0
    supplier_details: str = ""
    current_stock: int = 100
    lead_time_days: int = 14


@app.get("/my-products", dependencies=[Depends(require_key)])
def get_my_products():
    products = db.get_my_products()
    return {"products": products}


@app.post("/my-products", dependencies=[Depends(require_key)])
def save_my_product(req: MyProductRequest):
    db.save_my_product(
        asin=clean_asin(req.asin),
        title=req.title,
        sku=req.sku,
        supplier_cost=req.supplier_cost,
        shipping_fee=req.shipping_fee,
        target_margin=req.target_margin,
        supplier_details=req.supplier_details,
        current_stock=req.current_stock,
        lead_time_days=req.lead_time_days,
    )
    return {"ok": True}


@app.delete("/my-products/{asin}", dependencies=[Depends(require_key)])
def delete_my_product(asin: str):
    db.delete_my_product(clean_asin(asin))
    return {"ok": True}


class CompetitorCompareRequest(BaseModel):
    asins: list[str]


@app.post("/competitor-analysis", dependencies=[Depends(require_key)])
def compare_competitors(req: CompetitorCompareRequest):
    results = []
    df = db.get_all_validations_df()
    for asin in req.asins:
        asin = asin.strip().upper()
        # list input: skip malformed entries rather than failing the whole compare
        if not ASIN_RE.match(asin):
            continue
        snap = db.get_latest_snapshot(asin)
        val = None
        if not df.empty:
            matches = df[df["asin"] == asin]
            if not matches.empty:
                val = matches.iloc[0].to_dict()
                
        results.append({
            "asin": asin,
            "title": snap["title"] if snap else (val["title"] if val else None),
            "price": snap["price"] if snap else (val["buy_price"] * 1.5 if val else None),
            "rank": snap["rank"] if snap else None,
            "rating": snap["rating"] if snap else None,
            "review_count": snap["review_count"] if snap else None,
            "score": val["score"] if val else 50.0,
            "verdict": val["verdict"] if val else "WATCH",
            "found": snap is not None or val is not None
        })
    return {"comparisons": results}


@app.get("/listing-health", dependencies=[Depends(require_key)])
def get_listing_health():
    df = db.get_all_validations_df()
    results = []
    if df.empty:
        return {"products": []}
    
    latest = df.sort_values("validated_at").groupby("asin").last().reset_index()
    for _, row in latest.iterrows():
        asin = row["asin"]
        snap = db.get_latest_snapshot(asin)
        
        gaps = []
        listing_score = 100
        
        title_len = len(snap["title"]) if snap and snap["title"] else 0
        if title_len < 150:
            gaps.append(f"Short product title ({title_len}/150+ chars)")
            listing_score -= 25
        if not snap or not snap.get("review_count") or snap["review_count"] < 10:
            gaps.append("Low review count (under 10 reviews)")
            listing_score -= 25
        if not snap or not snap.get("rating") or snap["rating"] < 4.0:
            gaps.append("Sub-optimal rating (under 4.0 ⭐)")
            listing_score -= 25
        if not snap or not snap.get("price") or snap["price"] <= 0:
            gaps.append("Missing price snapshot")
            listing_score -= 25
            
        listing_score = max(25, listing_score)
            
        results.append({
            "asin": asin,
            "title": row["title"] or (snap["title"] if snap else "Unknown Product"),
            "score": listing_score,
            "verdict": row["verdict"],
            "gaps": gaps,
            "price": snap["price"] if snap else None
        })
    return {"products": results}


@app.get("/products/{asin}/drawer-details", dependencies=[Depends(require_key)])
def get_drawer_details(asin: str):
    import profit_calculator
    from scorer import CATEGORY_TO_FEE_KEY

    asin = clean_asin(asin)
    snap = db.get_latest_snapshot(asin)
    history = db.get_history(asin)
    
    val = None
    df_val = db.get_all_validations_df()
    if not df_val.empty:
        matches = df_val[df_val["asin"] == asin]
        if not matches.empty:
            val = matches.iloc[0].to_dict()
            
    my_prod = None
    my_products = db.get_my_products()
    for mp in my_products:
        if mp["asin"] == asin:
            my_prod = mp
            break

    title = (snap["title"] if snap else None) or (val["title"] if val else None) or (my_prod["title"] if my_prod else None) or "Unknown Product"
    category = (snap["category"] if snap else None) or (val["category"] if val else None) or "General"
    buy_price = (my_prod["supplier_cost"] if my_prod else None) or (val["buy_price"] if val else None) or 150.0
    sell_price = (snap["price"] if snap else None) or (buy_price * 1.5)
    
    # Calculate real FBA / Easy Ship margin using profit_calculator
    fee_category = CATEGORY_TO_FEE_KEY.get(category, "other_default")
    calc = profit_calculator.calculate(
        sell_price=sell_price,
        buy_price=buy_price,
        category=fee_category,
        weight_grams=300,
        fulfillment="fba" if my_prod else "easy_ship",
        gst_rate_pct=18,
        zone="national"
    )

    referral_fee = calc["referral_fee"]
    closing_fee = calc["closing_fee"]
    shipping_fee = calc["weight_or_pickpack_fee"]
    total_fees = calc["amazon_fees_subtotal"] + calc["gst_on_amazon_fees_info_only"]
    net_margin = calc["net_margin_pct"]

    chart_points = []
    if history:
        for s in history[-7:]:
            chart_points.append({
                "day": s["collected_at"][-5:] if s["collected_at"] else "—",
                "BSR": s["rank"] if s["rank"] is not None else 5000,
                "Price": s["price"] if s["price"] is not None else sell_price
            })

    title_len = len(title)
    rank = snap["rank"] if snap else None
    rating = snap["rating"] if snap else None
    reviews = snap["review_count"] if snap else None

    audit_checklist = [
        {"check": f"Title length is optimized ({title_len}/150+ chars)", "pass": title_len >= 150},
        {"check": f"Review depth checked ({reviews or 0} reviews)", "pass": (reviews or 0) >= 10},
        {"check": f"Review rating checked ({rating or 0.0} stars)", "pass": (rating or 0.0) >= 4.0},
        {"check": f"Niche rank validated (BSR #{rank or 'N/A'})", "pass": rank is not None and rank <= 5000}
    ]

    return {
        "asin": asin,
        "title": title,
        "category": category,
        "price": sell_price,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "shipping_cost": shipping_fee,
        "fees": referral_fee + closing_fee + calc["gst_on_amazon_fees_info_only"],
        "net_margin": net_margin,
        "rating": rating if rating else 4.2,
        "reviews": reviews if reviews else 95,
        "score": val["score"] if val else 50.0,
        "verdict": val["verdict"] if val else "WATCH",
        "notes": val["notes"] if val else "",
        "trend_data": chart_points,
        "audit_checklist": audit_checklist
    }
