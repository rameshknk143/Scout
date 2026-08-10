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
    set MAXUN_API_URL=http://localhost:8080                 (default)

    python maxun_bridge.py --dry-run     # show what would be sent
    python maxun_bridge.py               # forward new runs
    python maxun_bridge.py --run-id X    # force one specific run
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

MAXUN_API_URL = os.environ.get("MAXUN_API_URL", "http://localhost:8080").rstrip("/")
SCOUT_API_URL = os.environ.get(
    "SCOUT_API_URL", "https://scout-api-3yvy.onrender.com"
).rstrip("/")
MAXUN_API_KEY = os.environ.get("MAXUN_API_KEY")
MAXUN_ROBOT_ID = os.environ.get("MAXUN_ROBOT_ID")
SCOUT_API_KEY = os.environ.get("SCOUT_API_KEY")

STATE_FILE = Path(__file__).with_name(".maxun_bridge_state.json")

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


def norm(key):
    """Normalise a column header for alias matching."""
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


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
            return datetime.strptime(raw.lower().replace("am", "AM").replace("pm", "PM"),
                                     fmt).isoformat()
        except ValueError:
            continue
    return None


def map_rows(rows, category, list_type, collected_at=None):
    """Convert Maxun rows into /ingest/maxun items. Returns (items, skipped)."""
    if not rows:
        return [], 0
    colmap = build_column_map(rows[0])
    items, skipped = [], 0

    for row in rows:
        rec = {}
        for raw_key, field in colmap.items():
            rec[field] = row.get(raw_key)

        asin = str(rec.get("asin") or "").strip().upper()
        if not ASIN_RE.match(asin):
            # Most Amazon list scrapes capture the product link but not the ASIN
            # as its own column - recover it from the URL rather than dropping
            # an otherwise good row.
            m = ASIN_IN_URL_RE.search(str(rec.get("url") or ""))
            asin = m.group(1) if m else ""
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


def main():
    ap = argparse.ArgumentParser(description="Forward Maxun run output into ScoutVeda.")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be sent; contact ScoutVeda not at all")
    ap.add_argument("--run-id", help="forward this run even if already forwarded")
    ap.add_argument("--category", default="Maxun Visual Scrape")
    ap.add_argument("--list-type", default="custom-scrape")
    ap.add_argument("--limit", type=int, default=5,
                    help="max new runs to forward in one pass")
    args = ap.parse_args()

    if not MAXUN_ROBOT_ID:
        sys.exit("MAXUN_ROBOT_ID is not set. List robots with: GET /api/robots")

    state = load_state()
    done = set(state.get("forwarded_run_ids", []))

    if args.run_id:
        target_ids = [args.run_id]
    else:
        listing = maxun_get("/api/robots/%s/runs" % MAXUN_ROBOT_ID)
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
        detail = maxun_get("/api/robots/%s/runs/%s" % (MAXUN_ROBOT_ID, run_id))
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
