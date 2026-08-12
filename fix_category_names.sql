-- Normalise snapshots.category onto the names the API actually knows.
--
-- api/main.py's CATEGORIES (31 names, kept in sync with scraper/collector.py's
-- CATEGORIES dict) is what the Trend Radar dropdown is built from. Rows sitting
-- under a name outside that list are collected, stored, and then never shown;
-- rows sitting under the WRONG name inside it are worse, because they are shown.
--
-- State of the table as read on 2026-08-13:
--
--   category                list_type      rows  what they actually are
--   ----------------------  -------------  ----  --------------------------------
--   Beauty                  bestsellers      90  Maxun Beauty robot
--   Beauty                  watchlist         6  VM deep-tracker
--   Grocery & Gourmet       bestsellers     150  Maxun Grocery robot
--   Maxun Visual Scrape     custom-scrape    60  Maxun Grocery robot, hand-run
--   Electronics             watchlist        54  VM deep-tracker (phone cases)
--   Competitor Watchlist    watchlist        36  VM deep-tracker
--   Health & Personal Care  watchlist         6  VM deep-tracker - IN CATEGORIES
--   Home & Kitchen          watchlist         6  VM deep-tracker - IN CATEGORIES
--
-- Two independent causes, both fixed at source before this file was written:
--
--   1. MAXUN_ROBOTS was configured with the names Amazon puts on the page
--      ("Beauty", "Grocery & Gourmet") rather than the names collector.py writes
--      ("Beauty & Personal Care", "Grocery & Gourmet Foods"). Fixed in
--      laptop.env, and maxun_bridge.py now refuses a --category that is not in
--      collector.py's CATEGORIES, so it cannot recur.
--
--   2. push_to_scoutveda.py set the category from `rank_category`, the department
--      parsed off the BSR line. Invisible while the watchlist was three phone
--      cases that all said "Electronics"; once targets.txt went to 15 ASINs it
--      started writing real category names. Fixed 2026-08-13 - see section 4.
--
-- This file repairs the rows already written.
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
   OR list_type = 'watchlist'
GROUP BY category, list_type ORDER BY category;

-- 1-2. The two Maxun bestseller robots. Straight rename onto the canonical name.
--
-- The list_type filter is load-bearing, not defensive. 'Beauty' is no longer only
-- the Maxun robot: since targets.txt went to 15 ASINs the VM deep-tracker has been
-- writing watchlist rows under it too (6 as of 2026-08-13). Without the filter this
-- statement would sweep those into the canonical Beauty category, which is exactly
-- what section 4 exists to prevent.
UPDATE snapshots SET category = 'Beauty & Personal Care'
WHERE category = 'Beauty' AND list_type = 'bestsellers';

UPDATE snapshots SET category = 'Grocery & Gourmet Foods'
WHERE category = 'Grocery & Gourmet' AND list_type = 'bestsellers';

-- 3. Same Grocery robot, forwarded by hand before --category was required. The
-- titles are the same Aashirvaad/Fortune/Tata rows. list_type is deliberately
-- left as custom-scrape: these were a hand-run, not a ranked bestseller capture,
-- and claiming otherwise would put unranked rows into the bestsellers table.
UPDATE snapshots SET category = 'Grocery & Gourmet Foods'
WHERE category = 'Maxun Visual Scrape';

-- 4. Every watchlist row onto 'Competitor Watchlist'.
--
-- The deep-tracker's history is split across five names. push_to_scoutveda.py set
-- the category from `rank_category` - the department parsed off the BSR line,
-- "#1,714 in Electronics" - falling back to CATEGORY. While the target list was
-- three phone cases that always said 'Electronics' and looked deliberate. Widening
-- targets.txt to 15 ASINs across four departments turned it into:
--
--     Electronics             54     (phone cases)
--     Competitor Watchlist    36     (before rank_category won)
--     Beauty                   6
--     Health & Personal Care   6     <-- already inside CATEGORIES
--     Home & Kitchen           6     <-- already inside CATEGORIES
--
-- The last two are the damaging ones: weekly_digest() in api/trend_radar.py filters
-- by category but NOT by list_type (only category_table does), so those 12 rows are
-- being fed into those categories' new_entrants and top_movers as though they were
-- bestseller captures. Fixed at source on 2026-08-13 - the push script now always
-- sends CATEGORY - so this repairs the rows already written.
--
-- Written against list_type rather than a list of names so it also catches whatever
-- department a future target lands in, if the source fix is ever regressed.
UPDATE snapshots SET category = 'Competitor Watchlist'
WHERE list_type = 'watchlist' AND category <> 'Competitor Watchlist';

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
   OR list_type = 'watchlist'
GROUP BY category, list_type ORDER BY category;

COMMIT;
