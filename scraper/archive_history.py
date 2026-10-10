"""Read-only, streaming history export. No deletion or automatic pruning.

Archives retain every column and original identifier. A repeatable-read snapshot
keeps the row count and streamed data consistent while collection continues.
Use an authenticated DATABASE_URL; credentials and rows are never logged.
"""
import argparse
import gzip
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

TABLES = {'snapshots': 'collected_at', 'field_observations': 'observed_at',
          'snapshots_backup_20260831': None}


def verify(path, expected_count, expected_sha=None):
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, 'rb') as stream:
        for line in stream:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError('Archive row must be an object')
            digest.update(line)
            count += 1
    checksum = digest.hexdigest()
    if count != expected_count or (expected_sha and checksum != expected_sha):
        raise ValueError('Archive count/checksum mismatch; retain cloud history')
    return checksum


def export(conn, table, destination, before=None):
    from psycopg2 import sql
    if table not in TABLES:
        raise ValueError('Unsupported archive table')
    if before and not TABLES[table]:
        raise ValueError('Backup exports must include the whole table')
    if before and before.tzinfo is None:
        raise ValueError('Cutoff must include timezone')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    archive = destination / (table + '-' + token + '.jsonl.gz')
    temporary = archive.with_suffix('.partial')
    relation = sql.Identifier('public', table)
    where = sql.SQL(' WHERE {} < %s').format(sql.Identifier(TABLES[table])) if before else sql.SQL('')
    params = (before,) if before else ()
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL('SELECT count(*) FROM {}').format(relation) + where, params)
            expected = cur.fetchone()[0]
            cur.execute("SELECT column_name,data_type,udt_name,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (table,))
            columns = cur.fetchall()
        count = 0
        with conn.cursor(name='archive_' + token) as cur:
            cur.itersize = 1000
            cur.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t').format(relation) + where, params)
            with gzip.open(temporary, 'wb') as stream:
                for row in cur:
                    stream.write(row[0].encode('utf8') + b'\n')
                    count += 1
        if count != expected:
            raise ValueError('Archive export incomplete')
        checksum = verify(temporary, expected)
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        temporary.replace(archive)
        manifest = {'version': 1, 'table': table, 'rows': expected,
                    'before': before.isoformat() if before else None,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'uncompressed_sha256': checksum,
                    'compressed_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                    'columns': columns, 'archive': archive.name,
                    'cloud_history_removed': False}
        receipt = archive.with_suffix('.manifest.json')
        receipt.write_text(json.dumps(manifest, indent=2), encoding='utf8')
        conn.commit()
        return archive, receipt, manifest
    except BaseException:
        conn.rollback()
        temporary.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', choices=sorted(TABLES), required=True)
    parser.add_argument('--before', help='Exclusive timezone-aware ISO cutoff')
    parser.add_argument('--destination', required=True)
    parser.add_argument('--second-copy', help='Optional independent archive location')
    args = parser.parse_args()
    import psycopg2
    cutoff = datetime.fromisoformat(args.before.replace('Z', '+00:00')) if args.before else None
    with psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=20,
                          options='-c statement_timeout=120000') as conn:
        archive, receipt, manifest = export(conn, args.table, args.destination, cutoff)
    if args.second_copy:
        second = Path(args.second_copy).resolve()
        if second == archive.parent.resolve():
            raise ValueError('Second copy must use another destination')
        second.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive, second / archive.name)
        shutil.copy2(receipt, second / receipt.name)
        verify(second / archive.name, manifest['rows'], manifest['uncompressed_sha256'])
    print(json.dumps({'table': args.table, 'rows': manifest['rows'],
                      'verified': True, 'cloud_history_removed': False}))


if __name__ == '__main__':
    main()
