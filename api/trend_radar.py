"""
Trend Radar detection logic. Pure query/analysis functions over the
`snapshots` table — no separate stored "trends" table, everything is
computed on demand from db.get_all_snapshots_df() (cheap at this data
volume: a few thousand rows/day).

Cold-start note (surfaced by the frontend, not here): with only one night of
data collected, every ASIN is technically a "new entrant" and there is no
day-over-day rank history for "movers" — that's expected, not a bug.
"""

import pandas as pd

import db


def _snapshots_df():
    df = db.get_all_snapshots_df()
    if df.empty:
        return df
    df["collected_at"] = pd.to_datetime(df["collected_at"])
    df["collected_date"] = df["collected_at"].dt.date
    return df


def distinct_collection_dates(df=None):
    """Sorted list of distinct calendar dates data has been collected on."""
    df = _snapshots_df() if df is None else df
    if df.empty:
        return []
    return sorted(df["collected_date"].unique())


def new_entrants(category=None, top_n=100, df=None):
    """ASINs whose EARLIEST snapshot ever recorded is from the most recent
    collection run — i.e. first time we've ever seen them. On a fresh DB
    (one collection run so far) this returns every product, which is the
    expected cold-start behaviour."""
    df = _snapshots_df() if df is None else df
    if df.empty:
        return pd.DataFrame()

    if category:
        df = df[df["category"] == category]
        if df.empty:
            return pd.DataFrame()

    df = df[df["rank"] <= top_n]
    latest_date = df["collected_date"].max()

    first_seen = df.groupby("asin")["collected_date"].min().rename("first_seen_date")
    latest_rows = df[df["collected_date"] == latest_date].drop_duplicates("asin", keep="last")
    merged = latest_rows.merge(first_seen, on="asin")

    entrants = merged[merged["first_seen_date"] == latest_date]
    cols = ["asin", "category", "rank", "title", "price", "rating", "review_count"]
    return entrants[cols].sort_values(["category", "rank"]).reset_index(drop=True)


def velocity(asin):
    """Rank history for a single ASIN across all collection runs so far.
    Returns dict with earliest/latest rank + delta (positive = improved,
    i.e. rank number went down), or None if the ASIN has no history."""
    hist = db.get_history(asin)
    if not hist:
        return None
    ranked = [h for h in hist if h["rank"] is not None]
    if len(ranked) < 1:
        return None

    first, last = ranked[0], ranked[-1]
    return {
        "asin": asin,
        "title": last["title"],
        "category": last["category"],
        "snapshots": len(ranked),
        "first_seen": first["collected_at"],
        "first_rank": first["rank"],
        "latest_seen": last["collected_at"],
        "latest_rank": last["rank"],
        "delta": first["rank"] - last["rank"],
    }


def top_movers(category=None, min_snapshots=2, limit=20, df=None):
    """ASINs with the biggest rank improvement (delta = first_rank -
    latest_rank, positive = climbing) across their full collection history.
    Requires at least `min_snapshots` collection runs per ASIN — on a
    single-night DB this will be empty, which is expected."""
    df = _snapshots_df() if df is None else df
    if df.empty:
        return pd.DataFrame()
    if category:
        df = df[df["category"] == category]

    df = df.dropna(subset=["rank"]).sort_values("collected_at")
    counts = df.groupby("asin").size()
    eligible = counts[counts >= min_snapshots].index
    if len(eligible) == 0:
        return pd.DataFrame()

    df = df[df["asin"].isin(eligible)]
    first = df.groupby("asin").first()
    last = df.groupby("asin").last()

    movers = pd.DataFrame({
        "asin": first.index,
        "title": last["title"].values,
        "category": last["category"].values,
        "first_rank": first["rank"].values,
        "latest_rank": last["rank"].values,
    })
    movers["delta"] = movers["first_rank"] - movers["latest_rank"]
    movers = movers[movers["delta"] > 0].sort_values("delta", ascending=False)
    return movers.head(limit).reset_index(drop=True)


def cross_category_hits(min_categories=2, df=None):
    """ASINs appearing (in their latest snapshot) across multiple distinct
    categories — signals appeal beyond a single niche."""
    df = _snapshots_df() if df is None else df
    if df.empty:
        return pd.DataFrame()

    latest_idx = df.groupby(["asin", "category"])["collected_at"].idxmax()
    latest = df.loc[latest_idx]

    cat_counts = latest.groupby("asin")["category"].nunique()
    hits_asins = cat_counts[cat_counts >= min_categories].index
    if len(hits_asins) == 0:
        return pd.DataFrame()

    hits = latest[latest["asin"].isin(hits_asins)]
    agg = hits.groupby("asin").agg(
        title=("title", "first"),
        categories=("category", lambda s: ", ".join(sorted(set(s)))),
        num_categories=("category", "nunique"),
        best_rank=("rank", "min"),
    ).reset_index()
    return agg.sort_values("num_categories", ascending=False).reset_index(drop=True)


def weekly_digest():
    """Rollup used by the Trend Radar homepage: new entrants, top movers,
    and cross-category hits, all computed live.

    Fetches the snapshots table exactly once and shares it across all four
    sub-queries — previously each one called _snapshots_df() independently,
    meaning a single digest request pulled the entire table 4x over.
    """
    df = _snapshots_df()
    return {
        "new_entrants": new_entrants(df=df),
        "top_movers": top_movers(df=df),
        "cross_category": cross_category_hits(df=df),
        "collection_dates": distinct_collection_dates(df=df),
    }


def category_table(category, list_type="bestsellers"):
    """Full latest-snapshot table for one category, for the per-category
    drill-down view. Uses the latest exact collection run (timestamp), not
    just the latest calendar date — a day with 2+ runs (manual re-triggers,
    debugging, etc.) would otherwise show every run's rows stacked together
    instead of just the most recent one."""
    df = _snapshots_df()
    if df.empty:
        return pd.DataFrame()
    df = df[(df["category"] == category) & (df["list_type"] == list_type)]
    if df.empty:
        return pd.DataFrame()
    latest_run = df["collected_at"].max()
    df = df[df["collected_at"] == latest_run]
    cols = ["rank", "asin", "title", "price", "rating", "review_count", "image_url"]
    return df[cols].sort_values("rank").reset_index(drop=True)
