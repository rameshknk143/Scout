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

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

import alerts
import db
import profit_calculator
import scorer
import trend_radar

API_KEY = os.environ["API_KEY"]

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
        asin=req.asin,
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
    return {"validations": df_to_records(df)}


@app.get("/alerts", dependencies=[Depends(require_key)])
def get_alerts():
    return {"alerts": alerts.compute_alerts()}


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
