"""Independent liveness/storage check; never print connection credentials."""
import json
import os
from datetime import datetime, timezone
import psycopg2


def assess(row,size,now):
    reasons=[]
    if row is None:reasons.append('Worker has not reported a heartbeat')
    else:
        checked,status,detail=row
        if (now-checked).total_seconds()>6*3600:reasons.append('Worker heartbeat is more than six hours old')
        if status in ('ERROR','DEGRADED'):reasons.append('Worker reported '+status)
    if size>=int(os.environ.get('SCOUT_DATABASE_MAX_BYTES',460*1024*1024)):
        reasons.append('Database reached the collection storage guard')
    return reasons


def main():
    with psycopg2.connect(os.environ['DATABASE_URL'],connect_timeout=20) as conn,conn.cursor() as cur:
        cur.execute("SELECT checked_at,status,detail FROM public.scrape_worker_health WHERE component='weekly-coverage'")
        row=cur.fetchone()
        cur.execute('SELECT pg_database_size(current_database())');size=cur.fetchone()[0]
    reasons=assess(row,size,datetime.now(timezone.utc))
    print(json.dumps({'database_bytes':size,'problems':reasons,'worker':row[1] if row else None}))
    return 1 if reasons else 0


if __name__=='__main__':raise SystemExit(main())
