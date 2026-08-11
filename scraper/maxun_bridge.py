"""
Maxun -> ScoutVeda bridge.

Maxun cannot post to ScoutVeda directly. Two independent reasons, both verified
in Maxun's source on 2026-08-10:

  1. Its WebhookConfig (server/src/models/Robot.ts) has no headers field, and
     sendWebhookWithRetry calls axios.post(url, payload, {timeout, validateStatus})
     with no headers. So it can never send the X-Scout-Key that /ingest/maxun
     requires via Depends(require_key).
  2. The run_completed payload carries only runId/robotId/robotName/status/
     finishedAt (+ optional markdown/html/links/summary). The scraped rows are
     NOT in it.

So this relay pulls instead of being pushed to:

    Maxun  GET /api/robots/{id}/runs          (x-api-key)   find new successes
           GET /api/robots/{id}/runs/{runId}  (x-api-key)   fetch data.listData
      ->   map columns onto the snapshots schema
      ->   ScoutVeda POST /ingest/maxun       (X-Scout-Key)

Config is entirely environment-driven. No secret is ever written to disk or
logged; --dry-run prints rows but never the keys.

    set MAXUN_API_KEY=...        Maxun UI -> API key
    set MAXUN_ROBOT_ID=...       robot whose runs to forward
    set SCOUT_API_KEY=...        same value as Render's API_KEY env var
    set SCOUT_API_URL=https://scout-api-3yvy.onrender.com   (default)
    set MAXUN_API_URL=http://127.0.0.1:8080                 (default)

    python maxun_bridge.py --dry-run     # show what would be sent
    python maxun_bridge.py               # forward new runs
    python maxun_bridge.py --run-id X    # force one specific run
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# 127.0.0.1, not localhost. On Windows localhost resolves to ::1 first, and on
# 2026-08-10 a stray `python -m http.server 8080` bound [::]:8080 while Maxun held
# only 0.0.0.0:8080 - so every call silently hit the wrong server and the bridge
# 404'd for a day. Pinning IPv4 makes that class of hijack impossible.
MAXUN_API_URL = os.environ.get("MAXUN_API_URL", "http://127.0.0.1:8080").rstrip("/")
SCOUT_API_URL = os.environ.get(
    "SCOUT_API_URL", "https://scout-api-3yvy.onrender.com"
).rstrip("/")
MAXUN_API_KEY = os.environ.get("MAXUN_API_KEY")
MAXUN_ROBOT_ID = os.environ.get("MAXUN_ROBOT_ID")
SCOUT_API_KEY = os.environ.get("SCOUT_API_KEY")

STATE_FILE = Path(__file__).with_name(".maxun_bridge_state.json")

# Timezone Maxun's server reports its run times in. Override if the stack is ever
# moved off this laptop: MAXUN_TZ_OFFSET="+00:00" for a UTC container.
_off = os.environ.get("MAXUN_TZ_OFFSET", "+05:30")
MAXUN_TZ = timezone(timedelta(
    hours=int(_off[:3]),
    minutes=int(_off[0] + _off[4:6]),
))

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
ASIN_IN_URL_RE = re.compile(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})")

# Maxun column names come from whoever built the robot in the point-and-click
# recorder, so they are never guaranteed. Match on a normalised form and accept
# the common variants rather than demanding exact headers.
FIELD_ALIASES = {
    "asin": ("asin", "productid", "product_id"),
    "title": ("title", "name", "product", "productname", "producttitle"),
    "price": ("price", "cost", "mrp", "sellingprice", "currentprice"),
    "rating": ("rating", "stars", "star", "avgrating", "averagerating"),
    "review_count": ("reviewcount", "reviews", "numreviews", "ratingscount",
                     "totalreviews", "reviewscount"),
    "image_url": ("imageurl", "image", "img", "thumbnail", "imagesrc", "imglink"),
    "url": ("url", "link", "producturl", "productlink", "href"),
    "rank": ("rank", "position", "no", "sno", "serial"),
}


# Content signatures, used when the headers are useless. Maxun's recorder names
# columns "Label 1..N" unless the person recording renames every one by hand, and
# renaming cannot help anyway when the recorder generalises a field into several
# alternative selectors: the Grocery robot spreads titles across Label 9/10/11
# (17+8+7 of 30 rows), so no single column IS the title. Classify by what the
# values look like, then coalesce the candidates per row.
IMAGE_RE = re.compile(r"^https?://\S+\.(?:jpg|jpeg|png|webp|gif)(?:[?#]|$)", re.I)
PRICE_RE = re.compile(r"[₹$€£]\s*[\d,]+(?:\.\d+)?")
RATING_RE = re.compile(r"([0-5](?:\.\d+)?)\s*out of\s*5", re.I)
RANK_RE = re.compile(r"^#\s*\d+$")
COUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})*$|^\d{1,9}$")
# Review links carry the ASIN too, so they rescue rows whose product link is blank.
ASIN_ANYWHERE_RE = re.compile(r"/(?:dp|gp/product|product-reviews|product)/([A-Z0-9]{10})")

# Real product titles here run 40-120 chars. The same robot also captures "Watch
# the video" (15 chars) as its own column, so a generous floor keeps that junk out.
MIN_TITLE_LEN = 25


def norm(key):
    """Normalise a column header for alias matching."""
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def classify_value(value):
    """Guess which field a single scraped cell holds, or None if unclear."""
    s = str(value or "").strip()
    if not s:
        return None
    if IMAGE_RE.match(s):
        return "image_url"
    if s.lower().startswith("http"):
        # Only a real product link is a url; review links are still mined for ASIN.
        return "url" if ASIN_IN_URL_RE.search(s) else None
    if PRICE_RE.search(s):
        return "price"
    if RATING_RE.search(s):          # before COUNT: "4.3 out of 5 stars  22,189"
        return "rating"
    if RANK_RE.match(s):
        return "rank"
    if COUNT_RE.match(s):
        return "review_count"
    if len(s) >= MIN_TITLE_LEN:
        return "title"
    return None


def infer_column_roles(rows):
    """Return {field: [column, ...]} ordered by how many rows each column fills.

    A column has to be consistent to count - at least 60% of its non-empty values
    must agree - so a stray number inside a title column cannot rename the column.
    """
    tally = {}
    for row in rows:
        for key, value in row.items():
            role = classify_value(value)
            if role:
                slot = tally.setdefault(key, {})
                slot[role] = slot.get(role, 0) + 1

    candidates = {}
    for key, roles in tally.items():
        total = sum(roles.values())
        role, hits = max(roles.items(), key=lambda kv: kv[1])
        if hits / total >= 0.6:
            candidates.setdefault(role, []).append((hits, key))

    return {role: [k for _, k in sorted(v, reverse=True)]
            for role, v in candidates.items()}


def first_filled(row, columns):
    """First non-empty value across a field's candidate columns."""
    for col in columns:
        value = row.get(col)
        if str(value or "").strip():
            return value
    return None


def build_column_map(sample_row):
    """Map this robot's actual column names onto our field names."""
    mapping = {}
    for raw_key in sample_row:
        n = norm(raw_key)
        for field, aliases in FIELD_ALIASES.items():
            if field in mapping.values():
                continue
            if n in aliases:
                mapping[raw_key] = field
                break
    return mapping


def to_number(value):
    """Pull a number out of scraped text: '₹1,234.00' -> 1234.0, '4.3 out of 5' -> 4.3."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"\d[\d,]*\.?\d*", str(value))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"forwarded_run_ids": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def maxun_get(path):
    if not MAXUN_API_KEY:
        sys.exit("MAXUN_API_KEY is not set.")
    r = requests.get(
        "%s%s" % (MAXUN_API_URL, path),
        headers={"x-api-key": MAXUN_API_KEY},
        timeout=45,
    )
    r.raise_for_status()
    return r.json()


def extract_rows(run):
    """Pull the scraped table out of a run. List scrapes land in data.listData."""
    data = (run or {}).get("data") or {}
    rows = []
    for bucket in ("listData", "textData", "crawlData", "searchData"):
        blob = data.get(bucket)
        if not blob:
            continue
        if isinstance(blob, list):
            rows.extend(x for x in blob if isinstance(x, dict))
        elif isinstance(blob, dict):
            # Usually {selectorName: [ {...}, {...} ]}
            for value in blob.values():
                if isinstance(value, list):
                    rows.extend(x for x in value if isinstance(x, dict))
                elif isinstance(value, dict):
                    rows.append(value)
    return rows


def run_finished_iso(run):
    """Maxun stores finishedAt as new Date().toLocaleString(), e.g.
    '30/7/2026, 12:23:10 am' - day-first en-IN, not ISO.

    Returns ISO-8601, or None to let the API stamp ingest time. Returning None
    on any doubt is deliberate: a wrong date silently bends a price trend, while
    a slightly late one only matters for runs forwarded long after the fact.
    """
    raw = (run or {}).get("finishedAt") or (run or {}).get("startedAt")
    if not raw:
        return None
    raw = str(raw).strip()
    try:                                    # already ISO? use it
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y, %I:%M:%S %p", "%d/%m/%Y, %H:%M:%S"):
        try:
            naive = datetime.strptime(
                raw.lower().replace("am", "AM").replace("pm", "PM"), fmt)
        except ValueError:
            continue
        # toLocaleString() has no offset, so the wall clock is the Maxun host's
        # local time - IST here. Stamping it as UTC put every row 5h30m into the
        # future. Attach the offset and hand the API a real UTC instant.
        return naive.replace(tzinfo=MAXUN_TZ).astimezone(timezone.utc).isoformat()
    return None


def map_rows(rows, category, list_type, collected_at=None):
    """Convert Maxun rows into /ingest/maxun items. Returns (items, skipped)."""
    if not rows:
        return [], 0
    colmap = build_column_map(rows[0])
    named = set(colmap.values())
    # Headers win when the robot was recorded with real column names; content
    # inference only fills the fields they left unresolved.
    inferred = {f: cols for f, cols in infer_column_roles(rows).items()
                if f not in named}
    items, skipped = [], 0

    for row in rows:
        rec = {}
        for raw_key, field in colmap.items():
            rec[field] = row.get(raw_key)
        for field, cols in inferred.items():
            if not str(rec.get(field) or "").strip():
                rec[field] = first_filled(row, cols)

        asin = str(rec.get("asin") or "").strip().upper()
        if not ASIN_RE.match(asin):
            # Most Amazon list scrapes capture the product link but not the ASIN
            # as its own column - recover it from the URL rather than dropping
            # an otherwise good row. Scan every cell, not just the mapped url:
            # a row with no product link often still has a review link.
            asin = ""
            for value in row.values():
                m = ASIN_ANYWHERE_RE.search(str(value or ""))
                if m:
                    asin = m.group(1)
                    break
        if not ASIN_RE.match(asin):
            skipped += 1
            continue

        title = rec.get("title")
        items.append({
            "asin": asin,
            "title": str(title).strip() if title else None,
            "category": category,
            "list_type": list_type,
            "rank": int(to_number(rec.get("rank"))) if to_number(rec.get("rank")) else None,
            "price": to_number(rec.get("price")),
            "rating": to_number(rec.get("rating")),
            "review_count": int(to_number(rec.get("review_count")))
                            if to_number(rec.get("review_count")) else None,
            "image_url": rec.get("image_url") or None,
            "url": rec.get("url") or None,
            # Maxun's run finish time, so a run forwarded days later (laptop was
            # off) is filed under when it was scraped, not when it was sent.
            "collected_at": collected_at,
        })

    return items, skipped


def post_to_scoutveda(items, category):
    if not SCOUT_API_KEY:
        sys.exit("SCOUT_API_KEY is not set.")
    r = requests.post(
        "%s/ingest/maxun" % SCOUT_API_URL,
        headers={"X-Scout-Key": SCOUT_API_KEY, "Content-Type": "application/json"},
        json={"items": items, "category": category},
        timeout=120,
    )
    if r.status_code == 404:
        sys.exit(
            "ScoutVeda returned 404 for /ingest/maxun.\n"
            "That endpoint exists only in the uncommitted api/main.py - it is not\n"
            "deployed yet. Commit and push api/main.py so Render picks it up, then\n"
            "re-run this bridge."
        )
    r.raise_for_status()
    return r.json()


def canonical_categories():
    """The category names collector.py writes, read from its source.

    Parsed rather than imported because `import collector` needs DATABASE_URL and
    this bridge deliberately never holds one - it posts through the API. Parsed
    rather than copied because a copy is exactly how this broke: MAXUN_ROBOTS was
    configured with "Beauty" and "Grocery & Gourmet", which are what the Amazon
    page calls them, while collector.py and the API's CATEGORIES both say
    "Beauty & Personal Care" and "Grocery & Gourmet Foods". 240 rows landed under
    names the Trend Radar has no entry for and were invisible in the UI.

    Returns an empty set if collector.py cannot be read, so a missing file
    degrades to the old no-validation behaviour rather than blocking a run.
    """
    src_path = Path(__file__).with_name("collector.py")
    try:
        src = src_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    block = re.search(r"^CATEGORIES\s*=\s*\{(.*?)^\}", src, re.S | re.M)
    if not block:
        return set()
    return set(re.findall(r'"([^"]+)"\s*:', block.group(1)))


def main():
    ap = argparse.ArgumentParser(description="Forward Maxun run output into ScoutVeda.")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be sent; contact ScoutVeda not at all")
    ap.add_argument("--run-id", help="forward this run even if already forwarded")
    ap.add_argument("--robot-id", default=MAXUN_ROBOT_ID,
                    help="robot to forward (default: MAXUN_ROBOT_ID)")
    # No default, and checked against collector.py below. A hand-run that silently
    # invented "Maxun Visual Scrape" put the Grocery robot's rows under two category
    # names, which splits any chart grouped by category. Better to refuse than guess.
    ap.add_argument("--category", required=True,
                    help='ScoutVeda category, e.g. "Grocery & Gourmet Foods"')
    ap.add_argument("--list-type", default="custom-scrape")
    ap.add_argument("--limit", type=int, default=5,
                    help="max new runs to forward in one pass")
    args = ap.parse_args()

    known = canonical_categories()
    if known and args.category not in known:
        close = [c for c in known if c.lower().startswith(args.category.lower()[:6])]
        sys.exit(
            "Unknown category %r.\n"
            "It must match collector.py's CATEGORIES exactly, or these rows land "
            "under a name the API's CATEGORIES list does not contain and they never "
            "appear in the Trend Radar.%s\n"
            "Known: %s" % (
                args.category,
                ("\nDid you mean: %s" % ", ".join(repr(c) for c in close)) if close else "",
                ", ".join(sorted(known)),
            )
        )

    robot_id = args.robot_id
    if not robot_id:
        sys.exit("No robot. Set MAXUN_ROBOT_ID or pass --robot-id. "
                 "List them with: GET /api/robots")

    state = load_state()
    done = set(state.get("forwarded_run_ids", []))

    if args.run_id:
        target_ids = [args.run_id]
    else:
        listing = maxun_get("/api/robots/%s/runs" % robot_id)
        runs = listing.get("runs") or listing.get("data") or []
        if isinstance(runs, dict):
            runs = runs.get("items", [])
        target_ids = [
            r.get("runId") for r in runs
            if str(r.get("status", "")).lower() in ("success", "completed")
            and r.get("runId") and r.get("runId") not in done
        ][: args.limit]

    if not target_ids:
        print("No new successful runs to forward.")
        return

    print("Forwarding %d run(s): %s" % (len(target_ids), ", ".join(target_ids)))

    for run_id in target_ids:
        detail = maxun_get("/api/robots/%s/runs/%s" % (robot_id, run_id))
        run = detail.get("run") or {}
        rows = extract_rows(run)
        items, skipped = map_rows(rows, args.category, args.list_type,
                                  collected_at=run_finished_iso(run))

        print("\nrun %s: %d scraped row(s) -> %d valid item(s), %d skipped (no usable ASIN)"
              % (run_id, len(rows), len(items), skipped))

        if not items:
            print("  nothing usable; not forwarding. Check the robot's column names.")
            if rows:
                print("  columns seen: %s" % ", ".join(map(str, rows[0].keys())))
            continue

        if args.dry_run:
            for it in items[:5]:
                print("  %s | %s | price=%s rating=%s reviews=%s"
                      % (it["asin"], (it["title"] or "")[:52],
                         it["price"], it["rating"], it["review_count"]))
            if len(items) > 5:
                print("  ... and %d more" % (len(items) - 5))
            continue

        result = post_to_scoutveda(items, args.category)
        print("  ScoutVeda: %s" % json.dumps(result))
        done.add(run_id)
        state["forwarded_run_ids"] = sorted(done)
        state["last_forwarded_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)

    if args.dry_run:
        print("\n(dry run - nothing was sent and no state was written)")


if __name__ == "__main__":
    main()
