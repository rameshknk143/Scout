"""
Watchlist alert-checking logic (M7). "Watched" = every ASIN that has been
run through the Validator at least once -- the validations table already
IS Scout's watchlist (see main.py's /watchlist endpoint), so this doesn't
introduce a new "add to watchlist" concept, it adds real signal-checking on
top of the one that already exists.

For each watched ASIN, this looks at its full snapshots history (already
collected nightly by collector.py -- no new data source) and compares the
two most recent snapshots per (category, list_type) series to flag:
  - price_change    : price moved >= PRICE_CHANGE_PCT since last snapshot
  - entered_top3     : rank crossed into the top 3 for the first time
  - rank_climbing     : rank improved by >= RANK_CLIMB_POSITIONS
  - rank_sliding      : rank worsened by >= RANK_SLIDE_POSITIONS
  - review_surge      : review count jumped by >= REVIEW_SURGE_PCT (and a
                         minimum absolute count, so a 2-review product
                         going to 3 doesn't count as a "surge")
  - dropped_from_list : the ASIN was present in an earlier run of this
                         category/list_type but is missing from the latest
                         one -- the closest signal this scraper can see to
                         a stock-out. It reads the public ranked list, not
                         live inventory, so it genuinely can't tell "out of
                         stock" apart from "just fell below the top 30" --
                         the alert message says "dropped from list", not
                         "out of stock", to stay honest about that.

Roadmap's fifth item ("new entrant into a watched keyword's top-3") doesn't
map onto Scout today -- there's no keyword-search collection (that's gated
behind Brand Registry confirmation, Phase 4). entered_top3 above is the
closest real equivalent: a watched ASIN newly ranking in the top 3 of a
category/list_type it's already tracked in.
"""

import db

PRICE_CHANGE_PCT = 8
RANK_CLIMB_POSITIONS = 5
RANK_SLIDE_POSITIONS = 10
REVIEW_SURGE_PCT = 15
REVIEW_SURGE_MIN_ABS = 10

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _watched_asins():
    df = db.get_all_validations_df()
    if df.empty:
        return []
    latest = df.sort_values("validated_at").groupby("asin").last().reset_index()
    return latest[["asin", "title", "category"]].to_dict("records")


def _series_by_list(history):
    series = {}
    for row in history:
        key = (row["category"], row["list_type"])
        series.setdefault(key, []).append(row)
    for points in series.values():
        points.sort(key=lambda r: r["collected_at"])
    return series


def _check_series(asin, title, category, list_type, points):
    alerts = []
    if len(points) < 2:
        return alerts

    prev, latest = points[-2], points[-1]
    base = {"asin": asin, "title": title, "category": category, "list_type": list_type}

    if prev["price"] and latest["price"] and prev["price"] > 0:
        pct = (latest["price"] - prev["price"]) / prev["price"] * 100
        if abs(pct) >= PRICE_CHANGE_PCT:
            direction = "dropped" if pct < 0 else "rose"
            alerts.append({
                **base,
                "alert_type": "price_change",
                "severity": "medium",
                "message": f"Price {direction} {abs(pct):.0f}% (₹{prev['price']:.0f} → ₹{latest['price']:.0f})",
                "detail": {"prev_price": prev["price"], "latest_price": latest["price"], "pct_change": round(pct, 1)},
                "detected_at": latest["collected_at"],
            })

    if prev["rank"] and latest["rank"]:
        delta = prev["rank"] - latest["rank"]
        if latest["rank"] <= 3 and prev["rank"] > 3:
            alerts.append({
                **base,
                "alert_type": "entered_top3",
                "severity": "high",
                "message": f"Entered top 3 (was #{prev['rank']}, now #{latest['rank']})",
                "detail": {"prev_rank": prev["rank"], "latest_rank": latest["rank"]},
                "detected_at": latest["collected_at"],
            })
        elif delta >= RANK_CLIMB_POSITIONS:
            alerts.append({
                **base,
                "alert_type": "rank_climbing",
                "severity": "medium",
                "message": f"Climbed {delta} ranks (#{prev['rank']} → #{latest['rank']})",
                "detail": {"prev_rank": prev["rank"], "latest_rank": latest["rank"], "delta": delta},
                "detected_at": latest["collected_at"],
            })
        elif -delta >= RANK_SLIDE_POSITIONS:
            alerts.append({
                **base,
                "alert_type": "rank_sliding",
                "severity": "low",
                "message": f"Slid {-delta} ranks (#{prev['rank']} → #{latest['rank']})",
                "detail": {"prev_rank": prev["rank"], "latest_rank": latest["rank"], "delta": delta},
                "detected_at": latest["collected_at"],
            })

    if prev["review_count"] and latest["review_count"] is not None:
        gain = latest["review_count"] - prev["review_count"]
        pct = (gain / prev["review_count"] * 100) if prev["review_count"] > 0 else 0
        if gain >= REVIEW_SURGE_MIN_ABS and pct >= REVIEW_SURGE_PCT:
            alerts.append({
                **base,
                "alert_type": "review_surge",
                "severity": "medium",
                "message": f"Reviews up {pct:.0f}% (+{gain}, {prev['review_count']} → {latest['review_count']})",
                "detail": {"prev_reviews": prev["review_count"], "latest_reviews": latest["review_count"], "gain": gain},
                "detected_at": latest["collected_at"],
            })

    return alerts


def _check_dropout(asin, title, category, list_type, points, latest_run_by_list):
    if not points:
        return []
    last_seen = points[-1]
    latest_run = latest_run_by_list.get((category, list_type))
    if latest_run and last_seen["collected_at"] < latest_run:
        label = list_type.replace("-", " ")
        return [{
            "asin": asin, "title": title, "category": category, "list_type": list_type,
            "alert_type": "dropped_from_list",
            "severity": "low",
            "message": f"No longer in {label} top 30 for {category} (last seen #{last_seen['rank']})",
            "detail": {"last_rank": last_seen["rank"], "last_seen_at": last_seen["collected_at"]},
            "detected_at": latest_run,
        }]
    return []


def compute_alerts():
    watched = _watched_asins()
    if not watched:
        return []

    df = db.get_all_snapshots_df()
    latest_run_by_list = {}
    if not df.empty:
        latest_run_by_list = df.groupby(["category", "list_type"])["collected_at"].max().to_dict()

    all_alerts = []
    for w in watched:
        history = db.get_history(w["asin"])
        if not history:
            continue
        title = w["title"] or history[-1]["title"] or w["asin"]
        for (category, list_type), points in _series_by_list(history).items():
            all_alerts.extend(_check_series(w["asin"], title, category, list_type, points))
            all_alerts.extend(_check_dropout(w["asin"], title, category, list_type, points, latest_run_by_list))

    all_alerts.sort(key=lambda a: (_SEVERITY_ORDER.get(a["severity"], 3), a["detected_at"]))
    return all_alerts
