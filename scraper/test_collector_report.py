"""Unit tests for the collector's run report and its run-level invariants.

Everything here is offline — no amazon.in request, no database. It covers the
logic added on 2026-09-09 with page-2 depth and concurrent fetching, and in
particular the three defects that code review and testing found in that change
before it ever ran a night:

  1. page 1 and page 2 landing under different collected_at values, which would
     have made api/alerts flag every watched top-30 ASIN as "dropped from list"
     every single night (test_one_timestamp_per_list).
  2. a clean-but-empty deep page being read as "short list" when it can equally
     be a broken slug or a soft block (test_orphan_* and test_soft_block_*).
  3. the block warning firing on a sample of one, which trains people to ignore
     it (test_tiny_sample_is_silent).

Run:  python -m unittest test_collector_report -v
"""

import io
import contextlib
import os
import threading
import unittest

# collector imports db, which reads DATABASE_URL at import time. Nothing here
# connects; the value only has to exist. Point it somewhere that would fail
# loudly rather than somewhere real.
os.environ.setdefault("DATABASE_URL", "postgresql://unittest:unittest@127.0.0.1:1/nope")

import collector


def _report(summary):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        collector._print_run_report(summary, 100.0)
    return buf.getvalue()


def _key(name, page):
    return f"{name} [bestsellers]" if page == 1 else f"{name} [bestsellers p{page}]"


def _ok(n, page, prefix="C"):
    return {_key(f"{prefix}{i}", page): {"ok": True, "rows": 30} for i in range(n)}


def _empty(n, page, prefix="E"):
    return {_key(f"{prefix}{i}", page): {"ok": False, "empty": True, "error": "empty"}
            for i in range(n)}


def _failed(n, page, prefix="F"):
    return {_key(f"{prefix}{i}", page): {"ok": False, "error": "boom"} for i in range(n)}


class PageKeyTests(unittest.TestCase):
    def test_page_1_keys_keep_the_original_format(self):
        # Existing log greps and eyeballs depend on this shape being unchanged.
        self.assertEqual(collector._job_key("Home & Kitchen", "bestsellers", 1),
                         "Home & Kitchen [bestsellers]")

    def test_deep_page_keys_are_suffixed(self):
        self.assertEqual(collector._job_key("Home & Kitchen", "bestsellers", 2),
                         "Home & Kitchen [bestsellers p2]")

    def test_page_is_recoverable_from_the_key(self):
        self.assertEqual(collector._page_of_key("Home & Kitchen [bestsellers]"), 1)
        self.assertEqual(collector._page_of_key("Home & Kitchen [bestsellers p2]"), 2)
        # A category label containing a digit must not be mistaken for a page.
        self.assertEqual(collector._page_of_key("Top 100 Gifts [bestsellers]"), 1)


class GroupTimestampTests(unittest.TestCase):
    """The defect that would have fired a false alert on every watched ASIN."""

    def test_one_timestamp_per_list(self):
        ts, lock = {}, threading.Lock()
        p1 = collector._group_timestamp("Home & Kitchen", "bestsellers", ts, lock)
        p2 = collector._group_timestamp("Home & Kitchen", "bestsellers", ts, lock)
        self.assertEqual(p1, p2, "pages of one list must share collected_at, or "
                                 "MAX(collected_at) becomes the page-2 time and "
                                 "alerts._check_dropout fires on every top-30 ASIN")

    def test_different_lists_get_their_own_timestamp(self):
        ts, lock = {}, threading.Lock()
        a = collector._group_timestamp("Home & Kitchen", "bestsellers", ts, lock)
        b = collector._group_timestamp("Home & Kitchen", "new-releases", ts, lock)
        c = collector._group_timestamp("Toys & Games", "bestsellers", ts, lock)
        # Independence means three entries under three keys — not three
        # distinct values. Back-to-back calls can legally land on the same
        # microsecond (Windows Python <3.13 resolves time.time() at ~15.6ms),
        # and equal stamps across different (category, list_type) groups are
        # harmless: both downstream readers (alerts._check_dropout's
        # MAX(collected_at) and uq_snapshots_row) are scoped by
        # (category, list_type), never by collected_at alone.
        self.assertEqual(len(ts), 3)
        self.assertEqual(ts[("Home & Kitchen", "bestsellers")], a)
        self.assertEqual(ts[("Home & Kitchen", "new-releases")], b)
        self.assertEqual(ts[("Toys & Games", "bestsellers")], c)

    def test_concurrent_callers_still_agree(self):
        ts, lock = {}, threading.Lock()
        seen, seen_lock = [], threading.Lock()

        def grab():
            v = collector._group_timestamp("Home & Kitchen", "bestsellers", ts, lock)
            with seen_lock:
                seen.append(v)

        threads = [threading.Thread(target=grab) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(set(seen)), 1, "a race here reintroduces the alert bug")


class RunReportTests(unittest.TestCase):
    def test_healthy_run_is_silent(self):
        self.assertNotIn("WARN", _report({**_ok(30, 1), **_ok(30, 2)}))

    def test_a_few_short_lists_are_silent(self):
        # Short lists genuinely have no page 2 (Music new-releases has 2
        # products). Expected, and must never be reported as failure.
        out = _report({**_ok(30, 1), **_ok(26, 2), **_empty(4, 2)})
        self.assertNotIn("WARN", out)
        self.assertIn("no-such-page", out)

    def test_tiny_sample_is_silent(self):
        # "1 of 1 failed" is 100% and means nothing; amazon.in throws single
        # transient failures routinely.
        self.assertNotIn("WARN", _report({**_ok(1, 1), **_failed(1, 2)}))

    def test_hard_block_warns(self):
        self.assertIn("hard-failed", _report({**_ok(30, 1), **_ok(10, 2), **_failed(20, 2)}))

    def test_soft_block_warns(self):
        # Amazon serving clean, empty deep pages fleet-wide looks job-by-job
        # identical to a lot of short lists. Only the rate separates them.
        self.assertIn("clean-but-empty", _report({**_ok(30, 1), **_ok(5, 2), **_empty(25, 2)}))

    def test_orphaned_empty_pages_warn(self):
        # An empty page 2 whose page 1 also failed is a broken list, not a
        # short one, and must not sit in a reassuring bucket.
        out = _report({"F0 [bestsellers]": {"ok": False, "error": "boom"},
                       "F0 [bestsellers p2]": {"ok": False, "empty": True, "error": "empty"}})
        self.assertIn("page 1 also failed", out)

    def test_orphans_do_not_inflate_the_soft_block_rate(self):
        summary = {**_ok(30, 1), **_ok(20, 2), **_empty(10, 2, prefix="E"),
                   **{_key(f"E{i}", 1): {"ok": False, "error": "boom"} for i in range(10)}}
        out = _report(summary)
        self.assertIn("page 1 also failed", out)
        self.assertNotIn("clean-but-empty", out,
                         "broken slugs must not be able to fake a soft block")

    def test_rows_are_totalled_per_page(self):
        out = _report({**_ok(2, 1), **_ok(2, 2)})
        self.assertIn("page 1: 2 ok, 0 failed, 0 no-such-page, 60 rows", out)
        self.assertIn("page 2: 2 ok, 0 failed, 0 no-such-page, 60 rows", out)
        self.assertIn("TOTAL  : 120 rows", out)


class PagesConfigTests(unittest.TestCase):
    def test_page_three_is_not_a_default(self):
        # Verified 2026-09-09: pg=3 returns HTTP 400. Adding it would spend a
        # request per list on a guaranteed error.
        self.assertNotIn(3, collector.PAGES)

    def test_page_one_url_is_unchanged(self):
        # The request that has worked for two months must stay byte-identical.
        self.assertEqual(collector.build_url("kitchen", "bestsellers", 1),
                         "https://www.amazon.in/gp/bestsellers/kitchen/")

    def test_deep_page_uses_the_bare_pg_form(self):
        # "ref=zg_bs_pg_2" drew a captcha on 1 of 3 categories in the same test
        # where "?pg=2" passed 3 of 3.
        self.assertEqual(collector.build_url("kitchen", "bestsellers", 2),
                         "https://www.amazon.in/gp/bestsellers/kitchen/?pg=2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
