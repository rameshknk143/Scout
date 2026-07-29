import os
import time
import requests
from datetime import datetime, timedelta, timezone
import db

MARKETPLACE_ENDPOINTS = {
    # North America Region (NA)
    "ATVPDKIKX0DER": "https://sellingpartnerapi-na.amazon.com",  # USA
    "A2EUQ1WTGCTBG2": "https://sellingpartnerapi-na.amazon.com",  # Canada
    "A1AM78C64UM0Y8": "https://sellingpartnerapi-na.amazon.com",  # Mexico
    "A2Q3Y263D00KWC": "https://sellingpartnerapi-na.amazon.com",  # Brazil
    # Europe Region (EU)
    "A21TJRUUN4KGV": "https://sellingpartnerapi-eu.amazon.com",  # India
    "A1F83G8C2ARO7P": "https://sellingpartnerapi-eu.amazon.com",  # UK
    "A1PA6795UKMFR9": "https://sellingpartnerapi-eu.amazon.com",  # Germany
    "A13V1IB3VIYZZH": "https://sellingpartnerapi-eu.amazon.com",  # France
    "APJ6JRA9NG5V4": "https://sellingpartnerapi-eu.amazon.com",  # Italy
    "A1RKKUPIHCS9HS": "https://sellingpartnerapi-eu.amazon.com",  # Spain
    "A1805IZSGTT6HS": "https://sellingpartnerapi-eu.amazon.com",  # Netherlands
    "A2NODRKZP88ZB9": "https://sellingpartnerapi-eu.amazon.com",  # Sweden
    "A33AVAJ2PDY3EV": "https://sellingpartnerapi-eu.amazon.com",  # Turkey
    "A2VIGQ35RCS4UG": "https://sellingpartnerapi-eu.amazon.com",  # UAE
    # Far East Region (FE)
    "A1VC38T7YXB528": "https://sellingpartnerapi-fe.amazon.com",  # Japan
    "A39IBJ37TRP1C6": "https://sellingpartnerapi-fe.amazon.com",  # Australia
    "A19VAU5U5O7RUS": "https://sellingpartnerapi-fe.amazon.com",  # Singapore
}
# Defaults to EU endpoint if an unknown marketplace slips through.
DEFAULT_ENDPOINT = "https://sellingpartnerapi-eu.amazon.com"


class SpApiRetryableError(Exception):
    """Raised for SP-API responses that are safe to retry: 429 (rate limit)
    and 5xx (transient server error). Any other failure (401/403/400, etc.)
    should NOT use this — retrying a bad request just delays the real
    error."""


def _call_with_retry(fn, max_attempts=3, backoff_base=2):
    """Calls fn() (a zero-arg callable performing one HTTP request that
    raises SpApiRetryableError on a transient failure). Retries up to
    max_attempts times with exponential backoff (backoff_base ** attempt
    seconds between tries). Any other exception propagates immediately —
    no retry. On final exhaustion, attaches how many attempts were made to
    the raised exception as `.attempts`, so callers can record it even on
    failure. Returns (result, attempts_used) on success."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(), attempt
        except SpApiRetryableError as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(backoff_base ** attempt)
    last_error.attempts = max_attempts
    raise last_error


def get_sp_api_access_token(refresh_token: str) -> str:
    """Exchanges a Selling Partner refresh token for a temporary access token via LWA."""
    lwa_url = "https://api.amazon.com/auth/o2/token"
    client_id = os.environ.get("LWA_CLIENT_ID")
    client_secret = os.environ.get("LWA_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("LWA_CLIENT_ID and LWA_CLIENT_SECRET are not set in environment.")

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    res = requests.post(lwa_url, data=payload)
    if res.status_code != 200:
        raise Exception(f"LWA token exchange failed: {res.text}")
        
    return res.json().get("access_token")


def sync_storefront_data(user_id: int) -> dict:
    """
    Main orchestration function to sync sales metrics and orders for a user.
    If using mock credentials or ALLOW_MOCK_LWA is enabled, it generates high-fidelity simulated statistics.
    Return dict always includes "attempts": how many tries the SP-API calls
    needed in total (1 for the mock path or any failure before a network
    call was attempted) — used by sync_engine.py to record sync_jobs history.
    """
    user_creds = db.get_seller_credentials(user_id)

    if not user_creds:
        return {"ok": False, "error": "No connected Amazon Seller account found. Please link your account in Settings first.", "attempts": 1}

    cred = user_creds[0]
    selling_partner_id = cred["selling_partner_id"]
    refresh_token = cred["refresh_token"]
    marketplace_id = cred.get("marketplace_id") or "A21TJRUUN4KGV"

    # A None token means db decryption returned nothing — the server's
    # TOKEN_ENCRYPTION_KEY doesn't match the key the token was saved with.
    # Surface it clearly instead of crashing on None.startswith below.
    if not refresh_token:
        return {"ok": False, "error": "Stored Amazon token could not be decrypted on the server (TOKEN_ENCRYPTION_KEY mismatch). Set TOKEN_ENCRYPTION_KEY on Render to the value it was saved with.", "attempts": 1}

    # Check if credentials are mock/sandbox
    is_mock = refresh_token.startswith("mock") or os.environ.get("ALLOW_MOCK_LWA") == "1"

    if is_mock:
        result = _run_simulation_sync(user_id, selling_partner_id, marketplace_id)
        result.setdefault("attempts", 1)
        return result

    try:
        access_token = get_sp_api_access_token(refresh_token)
        endpoint = MARKETPLACE_ENDPOINTS.get(marketplace_id, DEFAULT_ENDPOINT)

        # 1. Sync Sales Metrics (Last 14 days)
        sales_attempts = sync_sales_metrics(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        # 2. Sync Recent Orders
        orders_attempts = sync_recent_orders(user_id, selling_partner_id, marketplace_id, endpoint, access_token)

        return {"ok": True, "message": "Storefront data synchronized successfully.", "attempts": max(sales_attempts, orders_attempts)}
    except Exception as e:
        # Do NOT fabricate data on failure. A real sync error must surface as an
        # honest error so the dashboard shows real/empty state, never simulated
        # numbers dressed up as the seller's actual sales.
        print(f"SP-API live sync failed: {e}")
        return {"ok": False, "error": f"Amazon sync failed: {e}", "attempts": getattr(e, "attempts", 1)}


def sync_sales_metrics(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str) -> int:
    """Queries SP-API /sales/v1/orderMetrics and caches the results. Retries
    the network call on a transient failure. Returns the number of attempts
    it took (1 if it succeeded on the first try)."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }

    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)

    interval = f"{start_date.isoformat()}--{end_date.isoformat()}"
    url = f"{endpoint}/sales/v1/orderMetrics"
    params = {
        "marketplaceIds": marketplace_id,
        "interval": interval,
        "granularity": "Day"
    }

    def _request():
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 429 or res.status_code >= 500:
            raise SpApiRetryableError(f"SP-API Sales OrderMetrics query failed ({res.status_code}): {res.text}")
        if res.status_code != 200:
            raise Exception(f"SP-API Sales OrderMetrics query failed: {res.text}")
        return res

    res, attempts = _call_with_retry(_request)

    metrics = res.json().get("payload", [])
    for metric in metrics:
        # Interval is formatted as: 2026-07-15T00:00:00Z--2026-07-16T00:00:00Z
        interval_start = metric["interval"].split("--")[0]
        order_count = metric["orderCount"]
        unit_count = metric["unitCount"]
        total_sales_amount = float(metric["totalSales"]["amount"])
        currency = metric["totalSales"]["currencyCode"]

        db.save_storefront_sales_metric(
            user_id=user_id,
            selling_partner_id=selling_partner_id,
            marketplace_id=marketplace_id,
            interval_start=interval_start,
            order_count=order_count,
            unit_count=unit_count,
            total_sales_amount=total_sales_amount,
            currency=currency
        )

    return attempts


def sync_recent_orders(user_id: int, selling_partner_id: str, marketplace_id: str, endpoint: str, access_token: str) -> int:
    """Queries SP-API /orders/v0/orders and caches details. Retries the
    network call on a transient failure. Returns the number of attempts it
    took (1 if it succeeded on the first try)."""
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json"
    }

    # SP-API Orders rejects fractional seconds / offset form; it needs plain
    # ISO-8601 with a trailing Z (e.g. 2026-07-17T00:00:00Z), or it 400s.
    created_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{endpoint}/orders/v0/orders"
    params = {
        "MarketplaceIds": marketplace_id,
        "CreatedAfter": created_after,
        "MaxResultsPerPage": 20
    }

    def _request():
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 429 or res.status_code >= 500:
            raise SpApiRetryableError(f"SP-API Orders query failed ({res.status_code}): {res.text}")
        if res.status_code != 200:
            raise Exception(f"SP-API Orders query failed: {res.text}")
        return res

    res, attempts = _call_with_retry(_request)

    orders = res.json().get("payload", {}).get("Orders", [])
    for order in orders:
        amazon_order_id = order["AmazonOrderId"]
        purchase_date = order["PurchaseDate"]
        order_status = order["OrderStatus"]

        # Order total might be missing if pending or cancelled
        order_total = order.get("OrderTotal", {})
        amount = float(order_total.get("Amount", 0.0)) if order_total else 0.0
        currency = order_total.get("CurrencyCode", "INR") if order_total else "INR"
        items_count = int(order.get("NumberOfItemsUnshipped", 0)) + int(order.get("NumberOfItemsShipped", 0))
        if items_count == 0:
            items_count = 1

        db.save_storefront_order(
            user_id=user_id,
            amazon_order_id=amazon_order_id,
            purchase_date=purchase_date,
            order_status=order_status,
            amount=amount,
            currency=currency,
            items_count=items_count
        )

    return attempts


def _run_simulation_sync(user_id: int, selling_partner_id: str, marketplace_id: str, warning=None) -> dict:
    """Generates high-fidelity simulated sales charts and recent orders for sandbox/demo connections."""
    import random
    
    # 1. Generate 14 days of chronological sales history
    now = datetime.now(timezone.utc)
    currency = "INR" if marketplace_id == "A21TJRUUN4KGV" else ("USD" if marketplace_id == "ATVPDKIKX0DER" else "GBP")
    base_amount = 12000.0 if currency == "INR" else (250.0 if currency == "USD" else 180.0)
    
    for i in range(14):
        date = (now - timedelta(days=14 - i)).replace(hour=0, minute=0, second=0, microsecond=0)
        interval_start = date.isoformat().replace("+00:00", "Z")
        
        # Introduce a minor random daily fluctuation and weekend dip
        day_of_week = date.weekday()
        weekend_factor = 0.7 if day_of_week in (5, 6) else 1.1
        random_factor = random.uniform(0.85, 1.25)
        
        order_count = int(random.uniform(5, 15) * weekend_factor)
        unit_count = int(order_count * random.uniform(1.0, 1.3))
        total_sales_amount = round(order_count * base_amount * random_factor, 2)
        
        db.save_storefront_sales_metric(
            user_id=user_id,
            selling_partner_id=selling_partner_id,
            marketplace_id=marketplace_id,
            interval_start=interval_start,
            order_count=order_count,
            unit_count=unit_count,
            total_sales_amount=total_sales_amount,
            currency=currency
        )
        
    # 2. Generate simulated recent orders
    statuses = ["Shipped", "Unshipped", "Pending", "Cancelled"]
    status_weights = [0.7, 0.15, 0.1, 0.05]
    
    for i in range(8):
        order_time = now - timedelta(hours=i * 12 + random.randint(1, 6))
        purchase_date = order_time.isoformat().replace("+00:00", "Z")
        
        amazon_order_id = f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
        order_status = random.choices(statuses, weights=status_weights)[0]
        
        amount = round(random.uniform(1, 3) * base_amount, 2)
        items_count = random.choice([1, 1, 2, 3])
        
        db.save_storefront_order(
            user_id=user_id,
            amazon_order_id=amazon_order_id,
            purchase_date=purchase_date,
            order_status=order_status,
            amount=amount,
            currency=currency,
            items_count=items_count
        )
        
    res = {"ok": True, "message": "Demo storefront simulation sync complete."}
    if warning:
        res["warning"] = warning
    return res
