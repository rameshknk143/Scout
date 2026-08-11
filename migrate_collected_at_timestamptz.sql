-- snapshots.collected_at: TEXT -> TIMESTAMPTZ
--
-- Why. Storing instants as text is the root cause of two bugs already fixed by
-- hand on this table:
--
--   1. 2026-08-11, the +5h30m IST/UTC error in the Maxun rows.
--   2. 2026-08-12, fix_collected_at_format.sql - a ::text cast wrote Postgres'
--      own "2026-08-11 05:38:14+00" format into a column where every other row
--      used Python's "2026-08-11T05:42:15+00:00". On TEXT that is not cosmetic:
--      ' ' is 0x20 and 'T' is 0x54, so the space rows sorted BELOW every T row
--      of the same date and `ORDER BY asin, collected_at DESC` (api/db.py:642,
--      :814) silently returned a stale snapshot as "latest".
--
-- Both are the same class of bug and neither is possible once the column has a
-- real type: Postgres then compares instants, not characters, and rejects a
-- malformed value at write time instead of storing it and sorting it wrongly.
--
-- ORDER OF OPERATIONS - the API must be deployed first.
-- psycopg2 returns str for TEXT and datetime for timestamptz, so this migration
-- changes the Python type every reader sees. The readers were made tolerant of
-- both in the same commit as this file:
--   - api/main.py day_label()      was s["collected_at"][-5:]
--   - api/main.py df_to_records()  pins pandas Timestamps to isoformat()
--   - api/alerts.py                compares two DB values, so both move together
--   - api/trend_radar.py           already pd.to_datetime()'d the column
-- Deploy that to Render, confirm it is live, and only then run this.
--
--     psql "$DATABASE_URL" -f migrate_collected_at_timestamptz.sql
--
-- Cost. ~108k rows as of 2026-08-12. ALTER COLUMN ... TYPE rewrites the table
-- and rebuilds idx_snapshots_category under an ACCESS EXCLUSIVE lock, so reads
-- and writes block for the duration - a few seconds at this size. The whole
-- thing is one transaction: if anything fails, nothing changes.
--
-- Re-running is a no-op: the guard below exits early once the type is right.

BEGIN;

-- Do not sit in a queue holding an ACCESS EXCLUSIVE lock request, which would
-- block every reader behind us. Fail fast instead and retry when it is quiet.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '5min';

SELECT 'before: ' || data_type AS state
FROM information_schema.columns
WHERE table_name = 'snapshots' AND column_name = 'collected_at';

-- Refuse to run if any value would not survive the cast. Without this the ALTER
-- would abort anyway, but this names the offending rows instead of one opaque
-- error, and it costs a single sequential scan.
DO $$
DECLARE
    bad_count integer;
    sample    text;
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_name = 'snapshots' AND column_name = 'collected_at') <> 'text'
    THEN
        RAISE NOTICE 'collected_at is already migrated - nothing to do';
        RETURN;
    END IF;

    SELECT count(*), min(collected_at) INTO bad_count, sample
    FROM snapshots
    WHERE collected_at IS NOT NULL
      AND NOT (collected_at ~ '^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}');

    IF bad_count > 0 THEN
        RAISE EXCEPTION 'aborting: % row(s) are not ISO-8601 timestamps, e.g. %',
            bad_count, sample;
    END IF;

    -- Values are timezone-aware ISO-8601 in UTC. The explicit AT TIME ZONE 'UTC'
    -- covers any row that somehow lost its offset: without it Postgres would
    -- apply the server's TimeZone setting and shift those rows.
    EXECUTE $sql$
        ALTER TABLE snapshots
        ALTER COLUMN collected_at TYPE timestamptz
        USING (CASE
                 WHEN collected_at ~ '(Z|[+-]\d{2}(:?\d{2})?)$'
                   THEN collected_at::timestamptz
                 ELSE (collected_at::timestamp AT TIME ZONE 'UTC')
               END)
    $sql$;
END $$;

SELECT 'after:  ' || data_type AS state
FROM information_schema.columns
WHERE table_name = 'snapshots' AND column_name = 'collected_at';

SELECT 'rows:   ' || count(*)
    || '  newest=' || max(collected_at)
    || '  oldest=' || min(collected_at) AS state
FROM snapshots;

COMMIT;

-- After this runs, api/db.py:582's `collected_at::timestamptz` is a redundant
-- no-op. It is kept so the query still works against an un-migrated database.
