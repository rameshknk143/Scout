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


def _closing_fee(sell_price, bands):
    for band in bands:
        if band["max_price"] is None or sell_price <= band["max_price"]:
            return band["fee"]
    return bands[-1]["fee"]


def _weight_handling_fee_easy_ship(weight_grams, zone, cfg):
    if weight_grams <= cfg["base_slab_upto_grams"]:
        return cfg["base_fee"][zone]
    if weight_grams <= cfg["next_slab_upto_grams"]:
        return cfg["next_slab_fee"][zone]
    extra_grams = weight_grams - cfg["next_slab_upto_grams"]
    extra_slabs = -(-extra_grams // 500)  # ceil division
    return cfg["next_slab_fee"][zone] + extra_slabs * cfg["additional_per_500g_fee"][zone]


def calculate(
    sell_price,
    buy_price,
    category,
    weight_grams,
    fulfillment,           # "easy_ship" | "fba" | "self_ship"
    gst_rate_pct,           # product's GST rate, e.g. 5/12/18/28 (depends on HSN code)
    zone="national",         # only used for easy_ship
    is_oversize=False,       # only used for fba
    returns_pct=5,
    ppc_per_unit=0,
    own_shipping_cost=0,     # only used for self_ship
    referral_pct_override=None,
    fees=None,
):
    if fees is None:
        fees = load_fee_table()

    referral_pct = (
        referral_pct_override
        if referral_pct_override is not None
        else fees["referral_fee_pct_by_category"].get(category, fees["referral_fee_pct_by_category"]["other_default"])
    )

    zero_threshold = fees["_meta"]["zero_referral_threshold_rupees"]
    referral_fee = 0.0 if sell_price <= zero_threshold else sell_price * referral_pct / 100

    closing_fee = _closing_fee(sell_price, fees["closing_fee_by_price_band"])

    if fulfillment == "easy_ship":
        weight_fee = _weight_handling_fee_easy_ship(weight_grams, zone, fees["weight_handling_fee_easy_ship"])
    elif fulfillment == "fba":
        weight_fee = fees["fba_pick_pack_fee_rupees"]["oversize" if is_oversize else "standard"]
    else:  # self_ship
        weight_fee = own_shipping_cost

    amazon_fees_subtotal = referral_fee + closing_fee + weight_fee
    gst_on_amazon_fees = amazon_fees_subtotal * fees["gst_on_amazon_fees_pct"] / 100

    # sell_price and buy_price are treated as GST-inclusive (how Amazon lists
    # and how suppliers usually quote). GST on the sale is a pass-through:
    # output tax collected minus input credit (on purchase + on Amazon's fees)
    # nets to ~zero cash effect, so real profit is computed on taxable values.
    taxable_sell = sell_price / (1 + gst_rate_pct / 100)
    taxable_buy = buy_price / (1 + gst_rate_pct / 100)
    gross_margin = taxable_sell - taxable_buy

    returns_provision = sell_price * returns_pct / 100

    net_margin_rupees = gross_margin - amazon_fees_subtotal - ppc_per_unit - returns_provision
    net_margin_pct = (net_margin_rupees / sell_price * 100) if sell_price else 0

    # Breakeven price: smallest sell_price at which net margin = 0, holding
    # buy price, fee %, ppc and returns % constant. Solved algebraically for
    # the case where referral fee applies (sell_price > zero_threshold); if
    # the breakeven point falls at/under the threshold, referral fee is 0 there.
    denom = 1 - (referral_pct / 100) - (returns_pct / 100) if sell_price > zero_threshold else 1 - (returns_pct / 100)
    breakeven_price = (taxable_buy * (1 + gst_rate_pct / 100) + closing_fee + weight_fee + ppc_per_unit) / denom if denom > 0 else None

    # Breakeven ACoS: max ad spend (as % of sale price) that still breaks even,
    # i.e. the margin room left over before PPC/returns are subtracted.
    margin_before_ppc_and_returns = gross_margin - amazon_fees_subtotal
    breakeven_acos_pct = (margin_before_ppc_and_returns / sell_price * 100) if sell_price else 0

    return {
        "referral_fee": round(referral_fee, 2),
        "closing_fee": round(closing_fee, 2),
        "weight_or_pickpack_fee": round(weight_fee, 2),
        "amazon_fees_subtotal": round(amazon_fees_subtotal, 2),
        "gst_on_amazon_fees_info_only": round(gst_on_amazon_fees, 2),
        "gross_margin_pre_fee": round(gross_margin, 2),
        "returns_provision": round(returns_provision, 2),
        "net_margin_rupees": round(net_margin_rupees, 2),
        "net_margin_pct": round(net_margin_pct, 2),
        "breakeven_price": round(breakeven_price, 2) if breakeven_price is not None else None,
        "breakeven_acos_pct": round(breakeven_acos_pct, 2),
        "verdict": _verdict(net_margin_pct),
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
