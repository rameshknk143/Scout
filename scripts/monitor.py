"""End-to-end health check for the ScoutVeda API and web app.

Exits 0 if every check passes, 1 if any fails. Run from GitHub Actions
(.github/workflows/monitor.yml), which turns a non-zero exit into a failed
workflow run, which is what actually reaches Ram by email.

WHY THIS EXISTS, given /health already returns 200
--------------------------------------------------
/health is `return {"ok": True}`. It has no require_key dependency and it
touches no database, deliberately, so it is safe and cheap to ping from a
public runner every 10 minutes. The cost of that is that it cannot fail for
any reason short of the process being down. Both real outages this system has
had were invisible to it:

  * the Trend Radar returning 500 on every authenticated route, while /health
    stayed green the whole time;
  * a collector silently not running, so the API served stale data perfectly.

So the checks below deliberately go through the authenticated routes and look
at the data that comes back, not just the status code.

Stdlib only, on purpose: no pip install step in the workflow, so a run is a
few seconds and cannot break because of a dependency resolution failure.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("SCOUT_API_BASE", "https://scout-api-3yvy.onrender.com").rstrip("/")
WEB = os.environ.get("SCOUT_WEB_BASE", "https://scoutveda.com").rstrip("/")
KEY = os.environ.get("SCOUT_KEY", "")

# Generous because Render's free tier cold start is 30-60s. The workflow is
# scheduled inside the VM keep-warm window so it should never actually pay
# that, but a timeout here would be a false alarm, and a false alarm that
# happens nightly is worse than no monitor at all.
TIMEOUT = 90

# Fail only after two consecutive missed nights. The nightly collector runs at
# 20:45 UTC, so at 03:00 UTC the newest collection date is legitimately
# "yesterday" -- a threshold of 1 would page every single morning.
MAX_STALE_DAYS = 2

# Populated by the laptop Maxun robots hourly and by the nightly collector, so
# it should never be empty. Named explicitly rather than "whatever the first
# category is" so that a category-name regression shows up as a failure here
# instead of quietly passing against some other category.
SAMPLE_CATEGORY = "Home & Kitchen"

results = []


def check(name):
    """Register a check. The function returns a detail string, or raises."""
    def wrap(fn):
        try:
            detail = fn()
            results.append((True, name, detail))
        except Exception as exc:                     # noqa: BLE001 - report, never crash
            results.append((False, name, f"{type(exc).__name__}: {exc}"))
        return fn
    return wrap


def get(url, key=None):
    """GET returning (status, parsed_json_or_None). Does not raise on 4xx/5xx."""
    req = urllib.request.Request(url, headers={"User-Agent": "scoutveda-monitor"})
    if key is not None:
        req.add_header("X-Scout-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exp:
        raw, status = exp.read(), exp.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, None


# --- liveness ---------------------------------------------------------------

@check("api /health")
def _health():
    status, body = get(f"{BASE}/health")
    assert status == 200, f"expected 200, got {status}"
    assert body == {"ok": True}, f"unexpected body {body!r}"
    return "200 ok"


# --- the API is not wide open ----------------------------------------------
# require_key is one decorator argument on each route. Dropping it would not
# break any page -- the web app sends the key anyway -- so nothing else in the
# system would notice that the whole API had become public.

@check("auth enforced (no key)")
def _no_key():
    status, _ = get(f"{BASE}/trend-radar/digest")
    assert status == 401, f"expected 401 without a key, got {status}"
    return "401 as expected"


@check("auth enforced (bad key)")
def _bad_key():
    status, _ = get(f"{BASE}/trend-radar/digest", key="not-the-real-key")
    assert status == 401, f"expected 401 with a wrong key, got {status}"
    return "401 as expected"


# --- authenticated routes actually work ------------------------------------

@check("trend-radar/categories")
def _categories():
    status, body = get(f"{BASE}/trend-radar/categories", key=KEY)
    assert status == 200, f"expected 200, got {status}"
    cats = (body or {}).get("categories") or []
    assert len(cats) >= 25, f"only {len(cats)} categories returned"
    return f"{len(cats)} categories"


@check("trend-radar/digest")
def _digest():
    status, body = get(f"{BASE}/trend-radar/digest", key=KEY)
    assert status == 200, f"expected 200, got {status}"
    for field in ("new_entrants", "top_movers", "cross_category", "collection_dates"):
        assert field in (body or {}), f"missing field {field!r}"
    return (f"{len(body['new_entrants'])} new entrants, "
            f"{len(body['top_movers'])} movers")


@check("data freshness")
def _fresh():
    status, body = get(f"{BASE}/trend-radar/digest", key=KEY)
    assert status == 200, f"digest returned {status}, cannot judge freshness"
    dates = (body or {}).get("collection_dates") or []
    assert dates, "no collection dates at all -- the table is empty"
    newest = datetime.date.fromisoformat(max(dates)[:10])
    age = (datetime.datetime.now(datetime.timezone.utc).date() - newest).days
    assert age <= MAX_STALE_DAYS, (
        f"newest data is {newest} ({age} days old) -- a collector has stopped")
    return f"newest {newest} ({age}d old)"


@check(f"category table ({SAMPLE_CATEGORY})")
def _category():
    url = f"{BASE}/trend-radar/category/{urllib.parse.quote(SAMPLE_CATEGORY)}"
    status, body = get(url, key=KEY)
    assert status == 200, f"expected 200, got {status}"
    products = (body or {}).get("products") or []
    assert products, "category returned zero products"
    return f"{len(products)} products"


# --- the site people actually open -----------------------------------------

@check("web app")
def _web():
    req = urllib.request.Request(WEB, headers={"User-Agent": "scoutveda-monitor"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        assert resp.status == 200, f"expected 200, got {resp.status}"
    return "200 ok"


# --- report -----------------------------------------------------------------

failed = [r for r in results if not r[0]]
width = max(len(name) for _, name, _ in results)
print(f"ScoutVeda monitor  {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M UTC}")
print(f"api {BASE}\nweb {WEB}\n")
for ok, name, detail in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
print()

if failed:
    print(f"{len(failed)} of {len(results)} checks FAILED")
    sys.exit(1)
print(f"all {len(results)} checks passed")
