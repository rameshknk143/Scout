-- Normalise snapshots.category onto the names the API actually knows.
--
-- api/main.py's CATEGORIES (31 names, kept in sync with scraper/collector.py's
-- CATEGORIES dict) is what the Trend Radar dropdown is built from. Five names in
-- the table are not in it, so those rows are collected, stored, and then never
-- shown:
--
--   category               list_type      rows  what they actually are
--   ---------------------  -------------  ----  ---------------------------------
--   Beauty                  bestsellers      90  Maxun Beauty robot
--   Grocery & Gourmet       bestsellers     150  Maxun Grocery robot
--   Maxun Visual Scrape     custom-scrape    60  Maxun Grocery robot, hand-run
--   Electronics             watchlist        48  VM deep-tracker (phone cases)
--   Competitor Watchlist    watchlist        18  VM deep-tracker (phone cases)
--
-- Cause. MAXUN_ROBOTS was configured with the names Amazon puts on the page
-- ("Beauty", "Grocery & Gourmet") rather than the names collector.py writes
-- ("Beauty & Personal Care", "Grocery & Gourmet Foods"). Fixed at source in
-- laptop.env, and maxun_bridge.py now refuses a --category that is not in
-- collector.py's CATEGORIES, so it cannot recur. This file repairs the rows
-- already written.
--
-- It also deletes one mislabelled pass (30 rows) - see section 5, which explains
-- why a delete and not a rename, and what was checked first.
--
--     psql "$DATABASE_URL" -f fix_category_names.sql
--
-- Safe to re-run: each WHERE matches only the old name, and the DELETE in section
-- 5 is pinned to one exact timestamp that nothing will write again.

BEGIN;

SELECT 'before: ' || category || ' / ' || list_type || ' = ' || count(*) AS state
FROM snapshots
WHERE category IN ('Beauty', 'Grocery & Gourmet', 'Maxun Visual Scrape',
                   'Electronics', 'Competitor Watchlist')
GROUP BY category, list_type ORDER BY category;

-- 1-2. The two Maxun bestseller robots. Straight rename onto the canonical name.
UPDATE snapshots SET category = 'Beauty & Personal Care'
WHERE category = 'Beauty';

UPDATE snapshots SET category = 'Grocery & Gourmet Foods'
WHERE category = 'Grocery & Gourmet';

-- 3. Same Grocery robot, forwarded by hand before --category was required. The
-- titles are the same Aashirvaad/Fortune/Tata rows. list_type is deliberately
-- left as custom-scrape: these were a hand-run, not a ranked bestseller capture,
-- and claiming otherwise would put unranked rows into the bestsellers table.
UPDATE snapshots SET category = 'Grocery & Gourmet Foods'
WHERE category = 'Maxun Visual Scrape';

-- 4. The VM deep-tracker wrote 'Competitor Watchlist' until 2026-08-10 and
-- 'Electronics' after, so its own history is split across two names. Consolidate
-- onto the original.
--
-- Deliberately NOT renamed to a canonical category. weekly_digest() in
-- api/trend_radar.py filters by category but not by list_type (only
-- category_table does), so folding these rows into 'Electronics Accessories'
-- would feed deep-tracked competitor snapshots into that category's new_entrants
-- and top_movers. Keeping them under a name outside CATEGORIES is what keeps
-- them out of the Trend Radar, which is correct for a watchlist.
UPDATE snapshots SET category = 'Competitor Watchlist'
WHERE category = 'Electronics' AND list_type = 'watchlist';

-- 5. One mislabelled pass: 30 Grocery rows written under 'Health & Personal Care'
-- at 2026-08-11T18:18:00Z.
--
-- Cause, and it was mine. laptop.env's MAXUN_ROBOTS was rewritten in place at
-- 23:48 IST on 2026-08-11 to use the canonical category names. The laptop loop
-- was mid-cycle and picked up the new list against the old robot ordering, so
-- for exactly one pass the Grocery robot's output was filed under the Health &
-- Personal Care name. The pass at 18:20:37Z and everything after it is correct
-- (verified: the current HPC top rows are Surf Excel / Presto / Tide, not Lay's
-- and Tata Salt).
--
-- Deleted rather than renamed. Verified before writing this:
--   * the Grocery pass at 18:24:13Z has the identical ASIN set AND identical
--     ranks, so these 30 rows are a pure duplicate - renaming would create a
--     second Grocery capture 6 minutes off the first;
--   * 0 of the 30 ASINs exist only in this pass, so nothing is lost;
--   * 0 of the 30 appear in Health & Personal Care at any other time, which is
--     why leaving them makes all 30 show up as HPC "new entrants" in the Trend
--     Radar and then as "dropped from list" on the next pass.
DELETE FROM snapshots
WHERE category = 'Health & Personal Care'
  AND collected_at = '2026-08-11T18:18:00+00:00';

SELECT 'after:  ' || category || ' / ' || list_type || ' = ' || count(*) AS state
FROM snapshots
WHERE category IN ('Beauty', 'Grocery & Gourmet', 'Maxun Visual Scrape',
                   'Electronics', 'Competitor Watchlist',
                   'Beauty & Personal Care', 'Grocery & Gourmet Foods')
GROUP BY category, list_type ORDER BY category;

COMMIT;
