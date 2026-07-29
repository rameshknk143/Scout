"""
ScoutVeda PPC & Advertising Analytics Engine (Blueprint Stage 6).

ACoS, TACoS, ROAS and campaign performance all require spend data from the Amazon
Advertising API, which is a separate authorization from SP-API and is not connected
yet (Amazon Dev Support case #21243620901).

Storefront sales metrics alone cannot produce these figures: nothing in
storefront_sales_metrics or storefront_orders distinguishes ad-attributed revenue
from organic revenue. Rather than estimate that split, this module reports the real
storefront totals it does have and returns an explicit not-connected state for every
advertising metric.
"""

from typing import Dict, List, Any


def calculate_ppc_performance(validations: List[Dict[str, Any]], sales_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_sales = sum(m.get("total_sales_amount", 0) for m in sales_metrics)
    total_units = sum(m.get("unit_count", 0) for m in sales_metrics)
    order_count = sum(m.get("order_count", 0) for m in sales_metrics)

    if sales_metrics:
        status_message = (
            "Storefront sales are syncing, but advertising metrics need the Amazon "
            "Advertising API. That authorization is still pending (case #21243620901), "
            "so ACoS, TACoS and ROAS cannot be calculated yet."
        )
    else:
        status_message = (
            "Amazon Advertising API connection pending. Connect your Seller Central ad "
            "account to fetch live campaign ACoS & TACoS."
        )

    return {
        # Advertising is not connected — no ad metric below is measurable yet.
        "connected": False,
        "status_message": status_message,
        "ad_metrics_available": False,
        "total_ad_spend": None,
        "total_ad_revenue": None,
        "organic_revenue": None,
        "acos_pct": None,
        "tacos_pct": None,
        "roas": None,
        "campaigns": [],
        "target_acos_pct": 20.0,
        "target_tacos_pct": 10.0,
        # Real, measured storefront figures from the nightly SP-API sync.
        "total_sales_amount": total_sales,
        "total_units": total_units,
        "order_count": order_count,
    }
