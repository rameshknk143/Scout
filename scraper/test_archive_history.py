import gzip
import hashlib
import tempfile
import unittest
import os
import uuid
from pathlib import Path
from archive_history import verify


@unittest.skipUnless(os.environ.get('SCOUT_LOCAL_PG_TEST') == '1', 'Explicit isolated local database only')
class ArchivePostgresTests(unittest.TestCase):
    def test_export_restore_and_atomic_prune_refuses_changed_rows(self):
        import json
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extras import Json
        from datetime import datetime, timezone
        from archive_history import export
        from archive_prune import prune
        if os.environ.get('SCOUT_ARCHIVE_TEST_DSN'):
            from psycopg2.extensions import parse_dsn
            params = parse_dsn(os.environ['SCOUT_ARCHIVE_TEST_DSN'])
            if params.pop('dbname', 'postgres') != 'postgres' or params.get('host') != '127.0.0.1':
                raise ValueError('Isolated loopback test database required')
        else:
            from maxun_service_manager import stack_environment
            env = stack_environment()
            params = dict(host='127.0.0.1', port=int(env.get('DB_PORT',5432)), user=env['DB_USER'], password=env['DB_PASSWORD'])
        name = 'scout_archive_test_' + uuid.uuid4().hex[:12]
        admin = psycopg2.connect(dbname='postgres', **params); admin.autocommit = True
        conn = None
        try:
            with admin.cursor() as cur:
                cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
            conn = psycopg2.connect(dbname=name, **params)
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE snapshots (id integer primary key, title text, collected_at timestamptz, specs jsonb)")
                cur.execute("INSERT INTO snapshots VALUES (1,'Original ✓','2026-09-01',%s),(2,'Recent','2026-10-11',null)", (Json({'ram':'8 GB'}),))
            conn.commit()
            with tempfile.TemporaryDirectory() as temp:
                path, receipt, manifest = export(conn, 'snapshots', temp, datetime(2026,10,1,tzinfo=timezone.utc))
                self.assertEqual(manifest['rows'], 1)
                verify(path, 1, manifest['uncompressed_sha256'])
                conn.set_session(readonly=False)
                with conn.cursor() as cur:
                    cur.execute("UPDATE snapshots SET title='Changed' WHERE id=1")
                conn.commit()
                with self.assertRaisesRegex(ValueError, 'changed'):
                    prune(conn, {'tables':[manifest]})
                with conn.cursor() as cur:
                    cur.execute('SELECT count(*) FROM snapshots'); self.assertEqual(cur.fetchone()[0],2)
                    cur.execute("UPDATE snapshots SET title='Original ✓' WHERE id=1")
                conn.commit()
                self.assertEqual(prune(conn, {'tables':[manifest]}), {'snapshots':1})
                with gzip.open(path, 'rt', encoding='utf8') as stream:
                    row = json.loads(stream.readline())
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO snapshots SELECT * FROM jsonb_populate_record(null::snapshots,%s)", (Json(row),))
                    cur.execute("SELECT title,specs FROM snapshots WHERE id=1")
                    self.assertEqual(cur.fetchone(), ('Original ✓', {'ram':'8 GB'}))
                conn.commit()
        finally:
            if conn: conn.close()
            with admin.cursor() as cur:
                cur.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
            admin.close()


class ArchiveTests(unittest.TestCase):
    def test_encryption_roundtrip_and_truncation_fail_closed(self):
        from archive_transport import encrypt, decrypt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private = folder/'private.pem'; public = folder/'public.pem'
            private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
            source = folder/'source'; source.write_bytes(b'original data' * 100000)
            encrypted = folder/'encrypted'; restored = folder/'restored'
            encrypt(source, encrypted, public)
            decrypt(encrypted, restored, private)
            self.assertEqual(source.read_bytes(), restored.read_bytes())
            restored.unlink()
            encrypted.write_bytes(encrypted.read_bytes()[:-20])
            with self.assertRaises(Exception):
                decrypt(encrypted, restored, private)
            self.assertFalse(restored.exists())
            self.assertFalse(Path(str(restored)+'.partial').exists())

    def test_verified_and_corrupt_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'archive.gz'
            content = b'{"id":1,"title":"Original"}\n{"id":2,"price":null}\n'
            with gzip.open(path, 'wb') as out:
                out.write(content)
            checksum = hashlib.sha256(content).hexdigest()
            self.assertEqual(verify(path, 2, checksum), checksum)
            for count, digest in [(3, checksum), (2, 'wrong')]:
                with self.assertRaises(ValueError):
                    verify(path, count, digest)
            with gzip.open(path, 'wb') as out:
                out.write(b'not JSON\n')
            with self.assertRaises(ValueError):
                verify(path, 1)
