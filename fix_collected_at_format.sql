-- Normalise 60 snapshots rows that carry a different timestamp format.
--
-- Background. On 2026-08-11 the Maxun rows were corrected for a 5h30m timezone
-- error with `UPDATE ... (collected_at::timestamptz - interval '5 hours 30 minutes')::text`.
-- The values became right, but the ::text cast writes Postgres' own format
--
--     2026-08-11 05:38:14+00        (space, +00)
--
-- while every other row was written by Python's datetime.isoformat()
--
--     2026-08-11T05:42:15+00:00     (T, +00:00)
--
-- collected_at is a TEXT column, so this is not cosmetic. ' ' is 0x20 and 'T' is
-- 0x54, so a space-formatted row sorts BELOW every T-formatted row of the same
-- date. That breaks the query in api/db.py:621-642 which picks each product's most
-- recent snapshot:
--
--     SELECT DISTINCT ON (asin) * FROM snapshots ... ORDER BY asin, collected_at DESC
--
-- A newer space-formatted row loses to an older T-formatted one, so "latest price"
-- can silently resolve to a stale value. The ASC ordering at db.py:559/583 puts the
-- same rows at the wrong position on price-history charts.
--
-- Safe to re-run: the WHERE clause only matches the space format, and once a row is
-- rewritten it no longer matches. Affects 60 rows as of 2026-08-11.
--
--     psql "$DATABASE_URL" -f fix_collected_at_format.sql

BEGIN;

SELECT 'before: ' || count(*) || ' space-format row(s)'
FROM snapshots WHERE collected_at LIKE '% %';

UPDATE snapshots
SET collected_at = to_char(collected_at::timestamptz AT TIME ZONE 'UTC',
                           'YYYY-MM-DD"T"HH24:MI:SS') || '+00:00'
WHERE collected_at LIKE '% %';

SELECT 'after:  ' || count(*) || ' space-format row(s) (expect 0)'
FROM snapshots WHERE collected_at LIKE '% %';

COMMIT;

-- The durable fix is to stop storing instants as text at all:
--     ALTER TABLE snapshots ALTER COLUMN collected_at TYPE timestamptz
--         USING collected_at::timestamptz;
-- That removes this whole class of bug, but it rewrites ~108k rows and the API
-- passes strings for this column, so it needs its own testing pass first.
