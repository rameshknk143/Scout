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
--     psql "$DATABASE_URL" -f fix_category_names.sql
--
-- Safe to re-run: each WHERE matches only the old name.

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

SELECT 'after:  ' || category || ' / ' || list_type || ' = ' || count(*) AS state
FROM snapshots
WHERE category IN ('Beauty', 'Grocery & Gourmet', 'Maxun Visual Scrape',
                   'Electronics', 'Competitor Watchlist',
                   'Beauty & Personal Care', 'Grocery & Gourmet Foods')
GROUP BY category, list_type ORDER BY category;

COMMIT;
