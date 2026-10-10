"""Prune only an exact, verified archive approved by a local signing key.

The proof is signed only after private Drive upload/readback and local archive
verification. A missing/mutated/late-arriving row fails closed before deletion.
No arbitrary tables, SQL, cutoff widening, cascade or credentials in logs.
"""
import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from archive_history import TABLES, KEYS

PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)


def canonical(proof):
    return json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()


def authenticate(envelope, public_key, now=None):
    proof = envelope['proof']
    key = serialization.load_pem_public_key(Path(public_key).read_bytes())
    key.verify(base64.b64decode(envelope['signature'], validate=True), canonical(proof), PSS, hashes.SHA256())
    now = now or datetime.now(timezone.utc)
    approved = datetime.fromisoformat(proof['approved_at'])
    if approved.tzinfo is None or approved > now or now - approved > timedelta(hours=6):
        raise ValueError('Archive approval expired')
    if not proof.get('drive_file_id') or not proof.get('encrypted_sha256'):
        raise ValueError('Verified private cloud copy required')
    seen = set()
    for manifest in proof['tables']:
        table = manifest['table']
        if table not in TABLES or table in seen:
            raise ValueError('Invalid archive scope')
        seen.add(table)
        if manifest['rows'] < 0 or len(manifest['uncompressed_sha256']) != 64:
            raise ValueError('Invalid archive receipt')
        if 'ordered_sha256' in manifest and len(manifest['ordered_sha256']) != 64:
            raise ValueError('Invalid ordered archive receipt')
        if TABLES[table]:
            cutoff = datetime.fromisoformat(manifest['before'])
            if cutoff.tzinfo is None or cutoff > now - timedelta(hours=24):
                raise ValueError('At least 24 hours of recent cloud history must remain')
        elif manifest['before'] is not None:
            raise ValueError('Backup must be archived in full')
    if not seen:
        raise ValueError('Empty archive scope')
    return proof


def prune(conn, proof):
    from psycopg2 import sql
    # Freeze the approved relations before the second full comparison. Commit
    # all removals together; a mismatch in any table retains every table.
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout='15s'")
            cur.execute(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE').format(
                sql.SQL(',').join(sql.Identifier('public', m['table']) for m in proof['tables'])))
        for index, manifest in enumerate(proof['tables']):
            table = manifest['table']
            relation = sql.Identifier('public', table)
            where = sql.SQL(' WHERE {} < %s').format(sql.Identifier(TABLES[table])) if TABLES[table] else sql.SQL('')
            params = (manifest['before'],) if TABLES[table] else ()
            count = 0; digest = hashlib.sha256()
            with conn.cursor(name='verify_archive_' + str(index)) as cur:
                cur.itersize = 1000
                cur.execute(sql.SQL('SELECT row_to_json(t)::text FROM {} t').format(relation) + where
                            + sql.SQL(' ORDER BY {}').format(sql.Identifier(KEYS[table])), params)
                for row in cur:
                    digest.update(row[0].encode('utf8') + b'\n'); count += 1
            if count != manifest['rows'] or digest.hexdigest() != manifest.get('ordered_sha256', manifest['uncompressed_sha256']):
                raise ValueError('Cloud rows changed since archive; no history removed')
        removed = {}
        with conn.cursor() as cur:
            for manifest in proof['tables']:
                table = manifest['table']
                if TABLES[table]:
                    cur.execute(sql.SQL('DELETE FROM {} WHERE {} < %s').format(
                        sql.Identifier('public', table), sql.Identifier(TABLES[table])), (manifest['before'],))
                    if cur.rowcount != manifest['rows']:
                        raise ValueError('Removal receipt mismatch')
                else:
                    # Keep the old backup schema; no DROP/CASCADE is needed.
                    cur.execute(sql.SQL('TRUNCATE TABLE {}').format(sql.Identifier('public', table)))
                removed[table] = manifest['rows']
        conn.commit()
        return removed
    except BaseException:
        conn.rollback()
        raise


def main():
    import psycopg2
    envelope = json.loads(os.environ['SCOUT_ARCHIVE_PROOF'])
    proof = authenticate(envelope, Path(__file__).with_name('archive_public.pem'))
    conn = psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=20,
                           options='-c statement_timeout=120000')
    try:
        removed = prune(conn, proof)
        # Regular VACUUM does not reliably return the old front pages to disk.
        # FULL compacts only these verified, now much smaller history tables.
        conn.autocommit = True
        from psycopg2 import sql
        with conn.cursor() as cur:
            cur.execute("SET lock_timeout='15s'")
            for table, count in removed.items():
                if count and TABLES[table]:
                    cur.execute(sql.SQL('VACUUM (FULL, ANALYZE) {}').format(sql.Identifier('public', table)))
            cur.execute('SELECT pg_database_size(current_database())')
            size = cur.fetchone()[0]
        print(json.dumps({'removed_verified_rows': removed, 'database_bytes': size,
                          'drive_file_id': proof['drive_file_id']}))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
