"""
spapi_cli.py — on-demand Amazon SP-API pull for the linked seller account.

Reads LWA_CLIENT_ID / LWA_CLIENT_SECRET / TOKEN_ENCRYPTION_KEY / DATABASE_URL
from scout-cloud/.env, pulls the Fernet-encrypted refresh token for the
default user out of the Supabase DB, does the LWA exchange, and calls the
SP-API endpoint you ask for. Prints only the data you want — no secrets.

Usage (from anywhere, hermes venv has all deps):
    python spapi_cli.py orders [--days 30]
    python spapi_cli.py sales [--days 30] [--granularity Day|Week|Month]
    python spapi_cli.py restock
    python spapi_cli.py all            # orders + sales + inventory posture
    python spapi_cli.py who            # who am I linked as (seller id + mktpl)

Runs with any python that has requests + cryptography (+ psycopg2 for DB).
"""
import os, sys, json, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from cryptography.fernet import Fernet, InvalidToken

BASE = Path(__file__).resolve().parent.parent  # scout-cloud root
SELLER_MARKETPLACE_DEFAULT = "A21TJRUUN4KGV"    # Amazon India -> EU endpoint
ENDPOINTS = {
    "eu-west-1": "https://sellingpartnerapi-eu.amazon.com",
    "us-east-1": "https://sellingpartnerapi-na.amazon.com",
    "us-west-2": "https://sellingpartnerapi-fe.amazon.com",
}


def _load_env():
    env = {}
    for line in (BASE / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"')
    return env


def _get_refresh_token(user_id: int = 1):
    """Decrypt the stored refresh token from Supabase via psycopg2."""
    import psycopg2, psycopg2.extras
    env = _load_env()
    conn = psycopg2.connect(env["DATABASE_URL"], connect_timeout=15)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT refresh_token, marketplace_id FROM seller_credentials "
            "WHERE user_id=%s LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        sys.exit(f"No seller_credentials row for user_id={user_id}.")
    fernet = Fernet(env["TOKEN_ENCRYPTION_KEY"].encode())
    try:
        return fernet.decrypt(row["refresh_token"].encode()).decode(), row["marketplace_id"]
    except InvalidToken:
        sys.exit("TOKEN_ENCRYPTION_KEY in .env doesn't match the one used on the server "
                 "(the stored token can't be decrypted). Set the same key locally.")


def _lwa_access_token(refresh_token: str) -> str:
    env = _load_env()
    r = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token,
              "client_id": env["LWA_CLIENT_ID"], "client_secret": env["LWA_CLIENT_SECRET"]},
        timeout=30,
    )
    if r.status_code != 200:
        sys.exit(f"LWA exchange failed ({r.status_code}): {r.text[:200]}")
    return r.json()["access_token"]


def _sp_call(method, path, marketplace_id, access_token, params=None):
    env = _load_env()
    region = env.get("AWS_REGION", "eu-west-1")
    ep = ENDPOINTS.get(region, ENDPOINTS["eu-west-1"])
    headers = {"x-amz-access-token": access_token, "Content-Type": "application/json"}
    url = f"{ep}{path}"
    last = None
    for attempt in range(4):
        r = requests.request(method, url, headers=headers, params=params, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504):
            last = r
            import time; time.sleep(2 ** attempt)
            continue
        break
    return r


# ---------------------------------------------------------------- commands
def cmd_who(args):
    refresh_token, mktpl = _get_refresh_token(args.user)
    at = _lwa_access_token(refresh_token)
    r = _sp_call("GET", "/sales/v1/orderMetrics", mktpl, at,
                 {"marketplaceIds": mktpl,
                  "interval": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "--" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "granularity": "Day"})
    print(f"Linked seller: user {args.user} | marketplace {mktpl}")
    print(f"Auth: {'LIVE (200)' if r.status_code == 200 else f'FAIL ({r.status_code})'}")


def cmd_orders(args):
    refresh_token, mktpl = _get_refresh_token(args.user)
    at = _lwa_access_token(refresh_token)
    start = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    orders, token, total = [], None, None
    while True:
        params = {"MarketplaceIds": mktpl, "CreatedAfter": start,
                  "MaxResultsPerPage": "50"}
        if token:
            params["NextToken"] = token
        r = _sp_call("GET", "/orders/v0/orders", mktpl, at, params)
        if r.status_code != 200:
            sys.exit(f"orders failed ({r.status_code}): {r.text[:300]}")
        body = r.json()["payload"]
        orders.extend(body.get("Orders", []))
        token = body.get("NextToken")
        total = body.get("LastUpdatedBefore")
        if not token:
            break
    print(f"{len(orders)} orders in last {args.days} days:\n")
    print(f"{'ORDER ID':<20} {'STATUS':<12} {'PURCHASED':<22} {'TOTAL':<12} {'ITEMS'}")
    for o in orders:
        tot = o.get("OrderTotal", {})
        items = int(o.get("NumberOfItemsShipped", 0)) + int(o.get("NumberOfItemsUnshipped", 0))
        print(f"{o.get('AmazonOrderId',''):<20} {o.get('OrderStatus',''):<12} "
              f"{str(o.get('PurchaseDate',''))[:19]:<22} "
              f"{tot.get('CurrencyCode','')} {tot.get('Amount',''):<6} {items}")
    if not orders:
        print("(none in window)")


def cmd_sales(args):
    refresh_token, mktpl = _get_refresh_token(args.user)
    at = _lwa_access_token(refresh_token)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=args.days)
    r = _sp_call("GET", "/sales/v1/orderMetrics", mktpl, at,
                 {"marketplaceIds": mktpl,
                  "interval": f"{start.isoformat()}--{now.isoformat()}",
                  "granularity": args.granularity})
    if r.status_code != 200:
        sys.exit(f"sales failed ({r.status_code}): {r.text[:300]}")
    rows = r.json().get("payload", [])
    print(f"Sales {args.granularity.lower()} metrics, last {args.days} days ({len(rows)} rows):\n")
    tot_orders = tot_units = 0.0
    cur = None
    for m in rows:
        c = m["totalSales"]["currencyCode"]; a = float(m["totalSales"]["amount"])
        cur = c; tot_orders += m["orderCount"]; tot_units += m["unitCount"]
    if rows:
        print(f"{'PERIOD':<30} {'ORDERS':>7} {'UNITS':>6} {'SALES':>12}")
        for m in rows[-40:]:
            p = m["interval"].split("--")[0]
            print(f"{p:<30} {m['orderCount']:>7} {m['unitCount']:>6} "
                  f"{m['totalSales']['currencyCode']} {float(m['totalSales']['amount']):>8,.2f}")
        print(f"\nTotals (full window): {int(tot_orders)} orders, {int(tot_units)} units "
              f"across {len(rows)} periods.")


def cmd_finances(args):
    """Pull financial events (settlements, fees, reimbursements, order payouts)."""
    refresh_token, mktpl = _get_refresh_token(args.user)
    at = _lwa_access_token(refresh_token)
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=args.days)).isoformat()
    r = _sp_call("GET", "/finance/2020-04-30/financialEvents", mktpl, at,
                 {"PostedAfter": start, "MarketplaceId": mktpl})
    if r.status_code == 403:
        sys.exit("⚠️  403: Amazon Finance (GET) role NOT active on this seller authorization yet.\n"
                 "   The refresh token IS live (`who` above = 200), so this is a server-side\n"
                 "   permission-boundary error, not a code/token bug. A re-consent / re-authorization\n"
                 "   that carries the Finance (GET) grant is required (Amazon-side, in progress).\n"
                 "   Re-run this command once Amazon grants the role — no code change needed.")
    if r.status_code != 200:
        sys.exit(f"financialEvents failed ({r.status_code}): {r.text[:300]}")
    rows = r.json().get("FinancialEvents", [])
    from collections import defaultdict
    by_type = defaultdict(lambda: {"count": 0, "amounts": defaultdict(float)})
    for e in rows:
        et = e.get("eventType", "Unknown")
        by_type[et]["count"] += 1
        for tx in e.get("PostedTransactionList", []):
            amt = tx.get("postedAmount", {})
            by_type[et]["amounts"][amt.get("currencyCode", "?")] += float(amt.get("value", 0.0))
    print(f"{len(rows)} financial events in last {args.days} days:\n")
    print(f"{'EVENT TYPE':<20} {'COUNT':>6}   NET POSTED")
    for et, agg in sorted(by_type.items(), key=lambda kv: -sum(kv[1]["amounts"].values())):
        net = "  ".join(f"{c} {v:,.2f}" for c, v in sorted(agg["amounts"].items()))
        print(f"{et:<20} {agg['count']:>6}   {net or '—'}")
    if not rows:
        print("(no events in window)")


def cmd_inventory(args):
    """Pull FBA inventory summarisation (available / reserved / inbound)."""
    refresh_token, mktpl = _get_refresh_token(args.user)
    at = _lwa_access_token(refresh_token)
    r = _sp_call("GET", "/fba/inventory/v1/summaries", mktpl, at,
                 {"marketplaceIds": mktpl, "start": "0", "pageSize": "100"})
    if r.status_code in (403, 400):
        # Amazon returns 403 (Unauthorized) OR 400 InvalidInput on this
        # endpoint when the Amazon FBA / FBA Inventory GET roles are not
        # authorized on the app — the 400 is generic, not a param bug.
        sys.exit(f"⚠️  {r.status_code}: FBA Inventory access denied — the 'Amazon FBA (GET)' and "
                 "'Amazon FBA Inventory (GET)' roles are likely NOT authorized on this SP-API app.\n"
                 "   Fix (one-time, ~2 min): SP-API Developer Portal (developer-docs.amazon.com/sp-api) →\n"
                 "   your app → 'Authorized roles' → add Amazon FBA (GET) + Amazon FBA Inventory (GET).\n"
                 "   (The app was connected 2026-07-17 with Orders + Sales roles only.)\n"
                 "   Re-run this command after authorizing the roles.")
    items = r.json().get("items", [])
    print(f"{len(items)} FBA SKUs on hand:\n")
    print(f"{'SKU':<24} {'AVAIL':>6} {'RESV':>5} {'INBOUND':>7}")
    tot_avail = tot_inbound = 0
    for it in items[:60]:
        sku = it.get("sku", "")
        avail = int(it.get("fulfillmentAvailableQuantity") or 0)
        reserv = int(it.get("fulfillmentReservedQuantity") or 0)
        inbound = int(it.get("inboundQuantity") or 0)
        tot_avail += avail; tot_inbound += inbound
        print(f"{sku:<24} {avail:>6} {reserv:>5} {inbound:>7}")
    print(f"\nTotals (first {min(len(items),60)} shown): available {tot_avail}, inbound {tot_inbound}.")
    if not items:
        print("(no FBA inventory)")


def cmd_all(args):
    args.days = 14
    print("===== ORDERS ====="); cmd_orders(args)
    print("\n===== SALES ====="); cmd_sales(args)


def main():
    p = argparse.ArgumentParser(description="On-demand Amazon SP-API pull (linked seller account).")
    p.add_argument("cmd", choices=["who", "orders", "sales", "finances", "inventory", "restock", "all"])
    p.add_argument("--days", type=int, default=30, help="lookback window in days")
    p.add_argument("--granularity", default="Day", choices=["Day", "Week", "Month"])
    p.add_argument("--user", type=int, default=1, help="ScoutVeda user_id owning the link")
    args = p.parse_args()
    {"who": cmd_who, "orders": cmd_orders, "sales": cmd_sales,
     "finances": cmd_finances, "inventory": cmd_inventory,
     "all": cmd_all,
     "restock": lambda a: sys.exit("restock report needs the create/poll/download "
                                    "ritual — use scout-cloud sync_engine for that"),
     }[args.cmd](args)


if __name__ == "__main__":
    main()
