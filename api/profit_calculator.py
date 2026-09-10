"""
Scout M3 — India Profit Calculator.
Pure calculation engine. Import calculate() from other scripts, or run this
file directly with --demo to see a worked example.
"""

import json
import os

FEE_TABLE_PATH = os.path.join(os.path.dirname(__file__), "data", "fee_tables.json")


def load_fee_table():
    with open(FEE_TABLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _band_lookup(value, bands, amount_key):
    """First band whose max_price is None or value <= max_price (inclusive)."""
    for band in bands:
        if band["max_price"] is None or value <= band["max_price"]:
            return band[amount_key]
    return bands[-1][amount_key]


def _closing_fee(sell_price, bands):
    return _band_lookup(sell_price, bands, "fee")


def _referral_pct_from_bands(sell_price, bands):
    return _band_lookup(sell_price, bands, "pct")


def _weight_handling_fee_easy_ship(weight_grams, zone, cfg):
    if weight_grams <= cfg["base_slab_upto_grams"]:
        return cfg["base_fee"][zone]
    if weight_grams <= cfg["next_slab_upto_grams"]:
        return cfg["next_slab_fee"][zone]
    extra_grams = weight_grams - cfg["next_slab_upto_grams"]
    extra_slabs = -(-extra_grams // 500)  # ceil division
    return cfg["next_slab_fee"][zone] + extra_slabs * cfg["additional_per_500g_fee"][zone]


def _fba_pick_pack_fee(weight_grams, is_oversize, cfg):
    if is_oversize:
        return cfg["heavy_bulky_per_unit"]
    fee = cfg["standard_upto_1kg"]
    if weight_grams <= 1000:
        return fee
    extra_upto_5kg_grams = min(weight_grams, 5000) - 1000
    extra_kg_upto_5 = -(-extra_upto_5kg_grams // 1000)  # ceil kg
    fee += extra_kg_upto_5 * cfg["additional_per_kg_upto_5kg"]
    if weight_grams > 5000:
        extra_after_5kg_grams = weight_grams - 5000
        extra_5kg_slabs = -(-extra_after_5kg_grams // 5000)  # ceil 5kg slabs
        fee += extra_5kg_slabs * cfg["additional_per_5kg_after"]
    return fee


def calculate(
    sell_price,
    buy_price,
    category,
    weight_grams,
    fulfillment,           # "easy_ship" | "fba" | "self_ship"
    gst_rate_pct,           # product's GST rate, e.g. 5/12/18/28 (depends on HSN code)
    zone="national",         # only used for easy_ship
    is_oversize=False,       # only used for fba (Heavy & Bulky)
    returns_pct=5,
    ppc_per_unit=0,
    own_shipping_cost=0,     # only used for self_ship
    referral_pct_override=None,
    fees=None,
    gst_registered=True,
    storage_cuft_months=0,
):
    if fees is None:
        fees = load_fee_table()

    referral_bands_by_cat = fees["referral_fee_by_category"]
    category_key = category if category in referral_bands_by_cat else "other_default"
    if referral_pct_override is not None:
        referral_pct = referral_pct_override
    else:
        referral_pct = _referral_pct_from_bands(
            sell_price, referral_bands_by_cat[category_key]
        )
    referral_fee = sell_price * referral_pct / 100.0

    closing_by_fulfillment = fees["closing_fee_by_fulfillment"]
    closing_bands = closing_by_fulfillment.get(
        fulfillment, closing_by_fulfillment["easy_ship"]
    )
    closing_fee = _closing_fee(sell_price, closing_bands)

    if fulfillment == "easy_ship":
        wh_cfg = fees["weight_handling_fee_easy_ship"]
        weight_fee = _weight_handling_fee_easy_ship(weight_grams, zone, wh_cfg)
        if sell_price <= 300:
            discount = wh_cfg.get("easy_ship_under_300_weight_discount_rupees", 0)
            weight_fee = max(0.0, weight_fee - discount)
    elif fulfillment == "fba":
        weight_fee = _fba_pick_pack_fee(
            weight_grams, is_oversize, fees["fba_pick_pack_fee_rupees"]
        )
    else:  # self_ship
        weight_fee = own_shipping_cost

    storage_rate = fees.get("fba_storage_fee_per_cuft_month_rupees", 50)
    storage_fee = (storage_cuft_months or 0) * storage_rate

    amazon_fees_ex_gst = referral_fee + closing_fee + weight_fee + storage_fee
    gst_fee_pct = fees.get("gst_on_amazon_fees_pct", fees.get("_meta", {}).get("gst_on_fees_pct", 18))
    gst_on_amazon_fees = amazon_fees_ex_gst * gst_fee_pct / 100.0

    # sell_price and buy_price are GST-inclusive (Amazon list price / typical supplier quote).
    taxable_sell = sell_price / (1 + gst_rate_pct / 100.0)
    taxable_buy = buy_price / (1 + gst_rate_pct / 100.0)
    gross_margin = taxable_sell - taxable_buy

    if gst_registered:
        # 18% GST on Amazon fees is ITC for a GST-registered seller — not a cash cost.
        cash_amazon_cost = amazon_fees_ex_gst
    else:
        cash_amazon_cost = amazon_fees_ex_gst + gst_on_amazon_fees

    returns_provision = sell_price * returns_pct / 100.0

    net_margin_rupees = (
        gross_margin - cash_amazon_cost - ppc_per_unit - returns_provision
    )
    net_margin_pct = (net_margin_rupees / sell_price * 100.0) if sell_price else 0.0

    # Breakeven sell_price (GST-inclusive) at which net margin = 0, holding
    # buy price, referral %, closing, weight/pick-pack, storage, ppc and
    # returns % constant. Closing is a step function of price so this is the
    # same closed-form approximation as before, now using the cash GST model:
    #   S/(1+g) - B/(1+g) - m*(S*r + F) - P - S*ret = 0
    # where m=1 if GST-registered (ITC), else 1.18; F = closing+weight+storage.
    gst_factor = 1 + gst_rate_pct / 100.0
    fee_gst_mult = 1.0 if gst_registered else (1 + gst_fee_pct / 100.0)
    r = referral_pct / 100.0
    ret = returns_pct / 100.0
    fixed_fees = closing_fee + weight_fee + storage_fee
    denom = (1.0 / gst_factor) - (fee_gst_mult * r) - ret
    numer = taxable_buy + fee_gst_mult * fixed_fees + ppc_per_unit
    breakeven_price = (numer / denom) if denom > 0 else None

    # Max ad spend as % of GST-inclusive sell_price that still breaks even
    # after cash Amazon cost and the returns provision.
    ppc_headroom = gross_margin - cash_amazon_cost - returns_provision
    breakeven_acos_pct = (ppc_headroom / sell_price * 100.0) if sell_price else 0.0

    gst_on_amazon_fees_rounded = round(gst_on_amazon_fees, 2)
    return {
        "referral_fee": round(referral_fee, 2),
        "closing_fee": round(closing_fee, 2),
        "weight_or_pickpack_fee": round(weight_fee, 2),
        "storage_fee": round(storage_fee, 2),
        "amazon_fees_subtotal": round(amazon_fees_ex_gst, 2),
        "gst_on_amazon_fees": gst_on_amazon_fees_rounded,
        "gst_on_amazon_fees_info_only": gst_on_amazon_fees_rounded,  # alias
        "cash_amazon_cost": round(cash_amazon_cost, 2),
        "gst_registered": bool(gst_registered),
        "taxable_sell": round(taxable_sell, 2),
        "taxable_buy": round(taxable_buy, 2),
        "gross_margin_pre_fee": round(gross_margin, 2),
        "returns_provision": round(returns_provision, 2),
        "net_margin_rupees": round(net_margin_rupees, 2),
        "net_margin_pct": round(net_margin_pct, 2),
        "breakeven_price": round(breakeven_price, 2) if breakeven_price is not None else None,
        "breakeven_acos_pct": round(breakeven_acos_pct, 2),
        "verdict": _verdict(net_margin_pct),
        "referral_pct_applied": referral_pct,
        "category_key": category_key,
        "basis": "net_margin_pct is percent of GST-inclusive selling price",
        "notes": "net_margin_pct is percent of GST-inclusive selling price",
    }


def _verdict(net_margin_pct):
    if net_margin_pct >= 20:
        return "Strong"
    if net_margin_pct >= 10:
        return "Workable"
    if net_margin_pct >= 0:
        return "Thin"
    return "Loss"


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        result = calculate(
            sell_price=1199,
            buy_price=450,
            category="electronics_accessories",
            weight_grams=300,
            fulfillment="easy_ship",
            gst_rate_pct=18,
            zone="national",
            returns_pct=5,
            ppc_per_unit=60,
        )
        for k, v in result.items():
            print(f"{k}: {v}")
    else:
        print("Run with --demo to see a worked example, or import calculate() from your own script.")
