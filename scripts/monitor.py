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
# .strip() is load-bearing. The repository secret was saved with a trailing
# newline, and urllib rejects a header value containing one outright --
# "ValueError: Invalid header value" on all seven authenticated checks, which
# reads exactly like the API being broken. A key with surrounding whitespace is
# never the intended value, so strip it here instead of relying on whoever
# pastes it next getting the selection right.
KEY = os.environ.get("SCOUT_KEY", "").strip()

# Everything Ram reads is IST. The servers all run UTC -- Render, the GitHub
# runner, the Oracle VM -- so every timestamp that reaches a human gets
# converted here rather than making him do the +5:30 in his head.
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30), "IST")


def ist(value):
    """Any ISO-8601 timestamp -> 'DD Mon HH:MM IST'."""
    if not value:
        return "never"
    text = str(value).replace("Z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        return str(value)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(IST).strftime("%d %b %H:%M IST")

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


@check("deployed build")
def _version():
    status, body = get(f"{BASE}/version", key=KEY)
    assert status == 200, f"expected 200, got {status}"
    commit = (body or {}).get("commit", "")
    assert commit and commit != "dev", f"service does not know its build: {body!r}"

    # Compared against the last commit that touched api/, not against HEAD.
    # render.yaml sets `rootDir: api`, so Render deliberately does not rebuild
    # for a commit that only changes scripts/ or a workflow. Against HEAD this
    # line reads "main is <newer sha>" after every monitoring-only push, which
    # is indistinguishable from a deploy that failed.
    #
    # Reported, deliberately not asserted either way: a real mismatch is usually
    # just Render mid-build, and failing on that would cry wolf every time
    # anything ships. A genuinely stuck deploy shows up as this line disagreeing
    # across several hourly runs.
    expected = os.environ.get("EXPECTED_COMMIT", "")
    if expected:
        state = "current" if commit == expected else f"api/ is at {expected[:8]}"
        return f"{commit[:8]} ({state})"
    return commit[:8]


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
    age = (datetime.datetime.now(IST).date() - newest).days
    assert age <= MAX_STALE_DAYS, (
        f"newest data is {newest:%d %b} ({age} days old) -- a collector has stopped")
    return f"newest {newest:%d %b} ({age}d old)"


@check("nightly collector")
def _collector():
    """The check above is table-wide, which is not good enough on its own.

    The laptop robots write hourly, so whole-table freshness stays green even if
    the nightly collector stops dead — and the collector is 96k of ~114k rows
    and the only source of the most-gifted / most-wished-for / new-releases
    lists. Nothing is allowed to depend on the laptop being on, so this asks
    about the collector specifically.

    The other two writers are printed but NOT asserted: the laptop runs about an
    hour a day by design, and the VM deep-tracker is a known-degraded pipeline
    (datacenter-IP rate limiting). Failing on either would be noise.
    """
    status, body = get(f"{BASE}/pipelines", key=KEY)
    assert status == 200, f"expected 200, got {status}"
    collector = (body or {}).get("nightly_collector") or {}
    age = collector.get("age_hours")
    assert age is not None, "collector has never written a row"

    others = "  ".join(
        f"{n.split('_')[0]} {ist(body[n].get('last_seen'))}"
        for n in ("vm_watchlist", "laptop_maxun") if body.get(n)
    )
    # Runs 20:45 UTC and takes ~1.5h, so ~25h is the normal worst case. 48h
    # tolerates one entirely missed night before shouting.
    assert age <= 48, f"collector last wrote {age}h ago -- it has stopped"
    return f"{age}h ago (advisory: {others})"


@check("vm scrape yield")
def _yield():
    """How much of the last VM pass actually landed.

    This is the check that removes "go and watch the 15:20 run" from anyone's
    job. The VM scrapes 15 targets twice a day and amazon.in blocks its Oracle
    datacenter IP intermittently, so a pass returns anywhere from 15 down to 2 —
    and until now the only way to know which was to read cron.log over SSH.

    Half the target list is the line. Below that the run is not producing usable
    price history, and the cause is essentially always the same one, so the
    message says so rather than making someone re-derive it.
    """
    status, body = get(f"{BASE}/pipelines", key=KEY)
    assert status == 200, f"expected 200, got {status}"
    vm = (body or {}).get("vm_watchlist") or {}
    got, want = vm.get("last_pass_asins") or 0, vm.get("targets") or 15
    when = ist(vm.get("last_seen"))
    assert got >= want / 2, (
        f"last pass landed only {got} of {want} targets at {when}. "
        "amazon.in is refusing the VM's datacenter IP -- check the phone tunnel "
        "(SOCKS on 127.0.0.1:1080); with it up this should be 15 of 15"
    )
    return f"{got} of {want} at {when}"


@check("vm alive (dead-man's switch)")
def _deadman():
    """The only check here that the VM cannot possibly perform for itself.

    Everything else in this system reports its own failures: a scrape that
    breaks says so, a push that cannot reach the API says so. A VM that is
    powered off, kernel panicked, or cut off from the network says nothing --
    and nothing is exactly what a healthy quiet night also looks like.

    So this asks the API, from outside, whether the VM has been reporting. It
    is a POST because it has a side effect by design: the API mails the alarm
    itself, which means a dead VM is reported even in the window before anyone
    notices this workflow went red.
    """
    request = urllib.request.Request(
        f"{BASE}/ops/deadman", data=b"{}", method="POST",
        headers={"X-Scout-Key": KEY, "Content-Type": "application/json",
                 "User-Agent": "scoutveda-monitor"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read() or "{}")
    except urllib.error.HTTPError as exp:
        raise AssertionError(f"deadman check returned HTTP {exp.code}") from exp

    ages = body.get("components") or {}
    summary = ", ".join(f"{name} {age}m" for name, age in sorted(ages.items()))
    assert body.get("ok"), (
        f"{body.get('reason') or 'no heartbeat from ' + ', '.join(body.get('stale', []))} "
        f"-- the scraping VM is presumed down. Check the Oracle console first, "
        f"then 'systemctl list-timers scout-*' on the box. Ages: {summary}")
    return f"{body.get('checked', 0)} component(s) reporting: {summary}"


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
print(f"ScoutVeda monitor  {datetime.datetime.now(IST):%d %b %Y %H:%M IST}")
print(f"api {BASE}\nweb {WEB}\n")
for ok, name, detail in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
print()

if failed:
    print(f"{len(failed)} of {len(results)} checks FAILED")
    sys.exit(1)
print(f"all {len(results)} checks passed")
