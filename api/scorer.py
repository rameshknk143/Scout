"""
Scout M5 — Opportunity Scorer v1 (no Keepa yet).

Hybrid scorer, same spirit as the Profit Calculator: auto-compute whatever
Scout's own collected data already knows, ask for the rest via a short
manual form.

Weights (BLUEPRINT M5): Demand 25 / Competition 20 / Margin 20 / Trend 15 /
Differentiation 10 / Operational fit 10.

Auto from Scout's own snapshots: Demand (BSR rank + review count), Competition
(how entrenched the category's incumbents already are), Trend (rank velocity /
new-entrant signal from trend_radar.py).
Manual input: buy/cost price (-> Margin, via profit_calculator.calculate()),
optional weight/fulfillment/GST overrides, a 1-5 differentiation judgment, a
1-5 operational-fit judgment.

Private-label framing: Ram has no existing brand — Scout is for finding
what to launch as a NEW private-label product, not for optimizing an
existing brand's listings. Differentiation/Operational-fit should be judged
through that lens (can a new, unbranded entrant win this category, not "can
I resell this").

Cold-start caveat: if an ASIN has no Scout collection history yet (not in any
of the 11 tracked categories, or Scout has only been running a few days),
Demand/Competition/Trend fall back to a neutral 50 and the result carries a
`caveats` list explaining why — scores get more reliable after 1-2 weeks of
nightly collection.
"""

import math
from datetime import datetime, timezone

import db
import profit_calculator
import trend_radar

WEIGHTS = {
    "demand": 25,
    "competition": 20,
    "margin": 20,
    "trend": 15,
    "differentiation": 10,
    "operational_fit": 10,
}

# Trend Radar category label -> fee_tables.json referral-fee category key
CATEGORY_TO_FEE_KEY = {
    "Electronics Accessories": "electronics_accessories",
    "Home & Kitchen": "home_kitchen",
    "Beauty & Personal Care": "beauty_personal_care",
    "Sports & Fitness": "sports_fitness",
    "Toys & Games": "toys",
    "Stationery/Office": "office",
    "Pet Supplies": "pet_supplies",
    "Car Accessories": "automotive_parts",
    "Garden & Outdoors": "garden",
    "Baby Products": "baby",
    "Watches & Gifting": "watches",
}

DEFAULT_WEIGHT_GRAMS = 300
DEFAULT_FULFILLMENT = "easy_ship"
DEFAULT_GST_RATE_PCT = 18
DEFAULT_ZONE = "national"


def _log_scale_0_100(value, cap=10000):
    """0 at value=0, 100 at value>=cap, log-scaled in between (so the
    difference between 10 and 100 reviews matters more than 9000 vs 9100)."""
    if value is None or value <= 0:
        return 0.0
    return min(100.0, math.log10(value + 1) / math.log10(cap + 1) * 100)


def _demand_score(asin):
    """From the ASIN's latest Scout snapshot: better rank + more reviews =
    more demand. Returns (score, available:bool)."""
    snap = db.get_latest_snapshot(asin)
    if not snap:
        return 50.0, False

    rank_score = None
    if snap.get("rank"):
        rank_score = max(0.0, 100.0 - min(snap["rank"] - 1, 100))

    reviews_score = _log_scale_0_100(snap.get("review_count"))

    if rank_score is not None:
        return (rank_score + reviews_score) / 2, True
    return reviews_score, True


def _competition_score(category):
    """From the category's full snapshot table: the more entrenched
    (highly-reviewed) the incumbents already ranking, the tougher the
    competition, the lower the opportunity score. Returns (score, available)."""
    if not category:
        return 50.0, False
    table = trend_radar.category_table(category)
    if table.empty:
        return 50.0, False

    median_reviews = table["review_count"].dropna().median()
    if median_reviews is None or (isinstance(median_reviews, float) and math.isnan(median_reviews)):
        return 50.0, False

    entrenchment = _log_scale_0_100(median_reviews)
    return max(0.0, 100.0 - entrenchment), True


def _trend_score(asin):
    """From trend_radar's velocity signal: climbing rank = good trend.
    Returns (score, available)."""
    v = trend_radar.velocity(asin)
    if not v or v["snapshots"] < 2:
        return 50.0, False
    delta = v["delta"]  # positive = rank improved (climbing)
    score = max(0.0, min(100.0, 50 + delta * 2))
    return score, True


def _margin_score(sell_price, buy_price, category, weight_grams, fulfillment, gst_rate_pct, zone):
    fee_category = CATEGORY_TO_FEE_KEY.get(category, "other_default")
    result = profit_calculator.calculate(
        sell_price=sell_price,
        buy_price=buy_price,
        category=fee_category,
        weight_grams=weight_grams,
        fulfillment=fulfillment,
        gst_rate_pct=gst_rate_pct,
        zone=zone,
    )
    margin_pct = result["net_margin_pct"]
    score = max(0.0, min(100.0, margin_pct / 30 * 100))
    return score, result


def _verdict(total):
    if total >= 70:
        return "PURSUE"
    if total >= 50:
        return "WATCH"
    return "SKIP"


def score_asin(
    asin,
    buy_price,
    user_id,
    category=None,
    weight_grams=DEFAULT_WEIGHT_GRAMS,
    fulfillment=DEFAULT_FULFILLMENT,
    gst_rate_pct=DEFAULT_GST_RATE_PCT,
    zone=DEFAULT_ZONE,
    differentiation=3,
    operational_fit=3,
    notes="",
):
    """Score one ASIN. `category` should match a Trend Radar category label
    if known (improves Competition scoring + fee-category mapping); if the
    ASIN isn't in Scout's own snapshots at all, pass category=None and expect
    a cold-start caveat on Demand/Competition/Trend."""
    snap = db.get_latest_snapshot(asin)
    title = snap["title"] if snap else None
    resolved_category = category or (snap["category"] if snap else None)
    sell_price = snap["price"] if snap else None

    caveats = []

    demand, demand_ok = _demand_score(asin)
    if not demand_ok:
        caveats.append("No Scout collection history for this ASIN yet — Demand score is a neutral placeholder.")

    competition, comp_ok = _competition_score(resolved_category)
    if not comp_ok:
        caveats.append("No category snapshot data to gauge competition — Competition score is a neutral placeholder.")

    trend, trend_ok = _trend_score(asin)
    if not trend_ok:
        caveats.append("Not enough nightly history yet for a trend read (need 2+ collection runs) — Trend score is a neutral placeholder.")

    if sell_price is None:
        caveats.append("No known sell price from Scout data — using buy_price with a 0% assumed margin is not possible; margin score will be 0 unless you also know the intended sell price.")
        sell_price = buy_price  # degrades gracefully to a 0-margin score rather than crashing

    margin, margin_detail = _margin_score(sell_price, buy_price, resolved_category, weight_grams, fulfillment, gst_rate_pct, zone)

    diff_score = max(0.0, min(100.0, differentiation * 20))
    ops_score = max(0.0, min(100.0, operational_fit * 20))

    components = {
        "demand": demand,
        "competition": competition,
        "margin": margin,
        "trend": trend,
        "differentiation": diff_score,
        "operational_fit": ops_score,
    }
    total = sum(components[k] * WEIGHTS[k] / 100 for k in WEIGHTS)
    verdict = _verdict(total)

    result = {
        "asin": asin,
        "title": title,
        "category": resolved_category,
        "sell_price": sell_price,
        "buy_price": buy_price,
        "components": components,
        "weights": WEIGHTS,
        "score": round(total, 1),
        "verdict": verdict,
        "margin_detail": margin_detail,
        "caveats": caveats,
    }

    db.log_validation(
        asin=asin,
        title=title,
        category=resolved_category,
        score=result["score"],
        verdict=verdict,
        buy_price=buy_price,
        notes=notes,
        validated_at=datetime.now(timezone.utc).isoformat(),
        user_id=user_id,
    )

    return result
