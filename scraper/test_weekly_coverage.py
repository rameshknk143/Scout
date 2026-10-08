import unittest
import os
import sys
import tempfile
import uuid
import threading
from pathlib import Path
from collections import Counter
from datetime import date,timedelta
from unittest.mock import patch
import weekly_coverage as weekly


class WeeklyCoverageTests(unittest.TestCase):
    def test_every_route_is_assigned_once_and_all_days_repeat(self):
        plan=weekly.manifest()
        self.assertEqual(len(plan['routes']),490)
        self.assertEqual(len({r['path'] for r in plan['routes']}),490)
        self.assertEqual({r['weekday'] for r in plan['routes']},set(range(7)))
        self.assertEqual(sum(len(day['categories']) for day in plan['days']),31)
        self.assertTrue(all(day['categories'] for day in plan['days']))
        for root in {r['top'] for r in plan['routes']}:
            self.assertEqual(len({r['weekday'] for r in plan['routes'] if r['top']==root}),1)
        self.assertEqual(weekly.digest(plan),weekly.digest(weekly.manifest()))

    def test_week_boundary_and_no_duplicate_tasks(self):
        self.assertEqual(weekly.monday(date(2027,1,3)),date(2026,12,28))
        plan=weekly.manifest();week=date(2026,10,5)
        tasks=weekly.list_tasks(plan,week)
        self.assertEqual(len(tasks),1960)
        self.assertEqual(len({t['task_id'] for t in tasks}),1960)
        self.assertEqual(set(Counter(t['path'] for t in tasks).values()),{4})
        later=weekly.list_tasks(plan,week+timedelta(days=7))
        self.assertFalse({t['task_id'] for t in tasks}&{t['task_id'] for t in later})
        self.assertEqual([t['payload'] for t in tasks],[t['payload'] for t in later])
        self.assertTrue(all('capture_at' not in t['payload'] for t in tasks))

    def test_zero_rows_does_not_mark_coverage_complete(self):
        import collector_optimized as collector
        task={'kind':'list','path':'Electronics','payload':{'slug':'electronics','list_type':'bestsellers','page':1,'capture_at':'2026-10-07T01:00:00Z'}}
        with patch.object(collector,'fetch_list_page',return_value='<html>blocked</html>'):
            with self.assertRaisesRegex(RuntimeError,'empty_or_blocked'):weekly.execute(task)

    def test_all_legacy_roots_are_included(self):
        from collector_optimized import CATEGORIES
        routes={r['slug'] for r in weekly.manifest()['routes']}
        self.assertFalse(set(CATEGORIES.values())-routes)

    def test_parallel_workers_respect_budget_and_circuit_break(self):
        class FakeLedger:
            def __init__(self):self.claimed=0;self.done=0;self.failed=0;self.lock=threading.Lock()
            def claim(self,today):
                with self.lock:self.claimed+=1;return {'id':self.claimed}
            def finish(self,*args):
                with self.lock:self.done+=1
            def fail(self,*args):
                with self.lock:self.failed+=1
        ledger=FakeLedger()
        with patch.object(weekly,'execute',return_value=({},[])):
            weekly.run_due(ledger,date(2026,10,7),minutes=1,max_tasks=5,workers=2)
        self.assertEqual(ledger.claimed,5);self.assertEqual(ledger.done,5)
        blocked=FakeLedger()
        with patch.object(weekly,'execute',side_effect=RuntimeError('blocked')):
            weekly.run_due(blocked,date(2026,10,7),minutes=1,max_tasks=100,workers=2)
        self.assertLessEqual(blocked.claimed,4);self.assertEqual(blocked.done,0)

    def test_detail_preserves_relevance_and_missing_statuses(self):
        import collector_optimized as collector
        import db
        from registry.observation_store import ObservationStore
        task={'kind':'detail','path':'Electronics','payload':{'asin':'B012345678','product_type':'laptop','capture_at':'2026-10-07T01:00:00Z'}}
        html='<input id="ASIN" value="B012345678"><span id="productTitle">Laptop</span><table id="productDetails_techSpec_section_1"><tr><th>RAM Size</th><td>8 GB</td></tr></table>'
        with patch.object(collector,'fetch_with_retry',return_value=html),patch.object(db,'insert_snapshot_rows'),patch.object(db,'get_conn'),patch.object(ObservationStore,'__init__',return_value=None),patch.object(ObservationStore,'acknowledge'),patch('registry.observation_store.deliver',return_value=[]):
            result,details=weekly.execute(task)
        self.assertEqual(result['field_statuses']['ram'],'COLLECTED')
        self.assertNotEqual(result['field_statuses']['unit_session_percentage'],'COLLECTED')
        self.assertEqual(len(result['field_statuses']),391)
        self.assertEqual(details,[])


@unittest.skipUnless(os.environ.get('SCOUT_LOCAL_PG_TEST')=='1','Explicit isolated local PostgreSQL test only')
class LocalPostgresCoverageTests(unittest.TestCase):
    def test_leases_retry_rollover_fanout_and_atomic_ingest(self):
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import make_dsn
        from maxun_service_manager import stack_environment
        env=stack_environment();name='scoutveda_week_test_'+uuid.uuid4().hex[:10]
        params=dict(host='127.0.0.1',port=int(env.get('DB_PORT',5432)),user=env['DB_USER'],password=env['DB_PASSWORD'])
        admin=psycopg2.connect(dbname='postgres',**params);admin.autocommit=True
        api_db=None
        try:
            with admin.cursor() as cur:cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
            dsn=make_dsn(dbname=name,**params)
            import db
            with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'DATABASE_URL':dsn,'SCOUT_FIELD_STORE':str(Path(temp)/'fields.sqlite')}),patch.object(db,'DATABASE_URL',dsn):
                from registry.observation_store import SQL_PATH
                ledger=weekly.Ledger()
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute('''CREATE TABLE snapshots(id SERIAL PRIMARY KEY,asin TEXT,category TEXT,list_type TEXT,rank INTEGER,title TEXT,price REAL,rating REAL,review_count INTEGER,image_url TEXT,collected_at TIMESTAMPTZ,brand TEXT,size_tier_hint TEXT,product_type_hint TEXT,subcategory TEXT,product_type TEXT,source TEXT,UNIQUE(asin,category,list_type,collected_at))''')
                    cur.execute(SQL_PATH.read_text(encoding='utf-8'));cur.execute((weekly.HERE/'weekly_coverage.sql').read_text())
                ledger.preflight();plan=weekly.manifest();week=date(2026,10,5)
                ledger.seed(plan,week);ledger.seed(plan,week)
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM scrape_week_tasks');self.assertEqual(cur.fetchone()[0],1960)
                a=ledger.claim(date(2026,10,11));b=ledger.claim(date(2026,10,11))
                self.assertNotEqual(a['task_id'],b['task_id']);self.assertIn('capture_at',a['payload'])
                children=[{'asin':'B012345678','product_type':'laptop'},{'asin':'B012345679','product_type':'laptop'}]
                ledger.finish(a,{'rows_parsed':2},children)
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM scrape_week_tasks WHERE kind='detail'");self.assertEqual(cur.fetchone()[0],2)
                with self.assertRaises(RuntimeError):ledger.finish(a,{},children)
                with self.assertRaises(TypeError):ledger.finish(b,{},[{'asin':'B012345677','product_type':set()}])
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute('SELECT status FROM scrape_week_tasks WHERE task_id=%s',(b['task_id'],))
                    self.assertEqual(cur.fetchone()[0],'RUNNING')
                ledger.fail(b,'simulated_transient')
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute("SELECT status,next_attempt>NOW() FROM scrape_week_tasks WHERE task_id=%s",(b['task_id'],));self.assertEqual(cur.fetchone(),('RETRY',True))
                    cur.execute("UPDATE scrape_week_tasks SET due_date='2026-10-04',next_attempt=NOW()-INTERVAL '1 minute' WHERE task_id=%s",(b['task_id'],))
                again=ledger.claim(date(2026,10,11))
                self.assertEqual(again['task_id'],b['task_id']);self.assertNotEqual(again['payload']['capture_at'],b['payload']['capture_at'])
                self.assertNotEqual(again['lease_token'],b['lease_token'])
                with self.assertRaises(RuntimeError):ledger.finish(b,{},[])
                with ledger.connection() as conn,conn.cursor() as cur:
                    cur.execute("UPDATE scrape_week_tasks SET kind='detail' WHERE task_id=%s",(again['task_id'],))
                ledger.finish(again,{'field_counts':{'COLLECTED':2,'MISSING':3}},[])
                report=ledger.report(week,date(2026,10,11))
                self.assertEqual(report['status'],'INCOMPLETE');self.assertEqual(report['routes_total'],490)
                import json
                json.dumps(report)
                self.assertEqual(report['field_status_counts'],{'COLLECTED':2,'MISSING':3})
                with self.assertRaises(RuntimeError):ledger.seed({**plan,'version':2},week)
                ledger.seed(plan,date(2026,10,12))
                self.assertTrue(ledger.report(date(2026,10,12),date(2026,10,12))['all_weeks_due_unfinished'])
                import importlib.util
                with patch.object(sys,'path',[str(weekly.HERE.parent),*sys.path]):
                    spec=importlib.util.spec_from_file_location('weekly_test_api_db',weekly.HERE.parent/'api/db.py')
                    api_db=importlib.util.module_from_spec(spec);spec.loader.exec_module(api_db)
                    row=dict(asin='B012345678',category='Electronics',list_type='product-detail',rank=None,title='Laptop',price=1000,rating=4.2,review_count=3,image_url=None,collected_at='2026-10-07T01:00:00Z',source='integration',product_type='laptop',attribute_observations={'observations':[{'field_key':'ram','raw_value':'8 GB'}]})
                    self.assertEqual(api_db.insert_snapshot_rows([row]),1);self.assertEqual(api_db.insert_snapshot_rows([row]),0)
                    with ledger.connection() as conn,conn.cursor() as cur:
                        cur.execute("SELECT normalized_value FROM field_observations WHERE field_key='ram'");self.assertEqual(cur.fetchone()[0],8000000000)
                        cur.execute('ALTER TABLE field_observations RENAME TO field_observations_paused')
                    with self.assertRaises(RuntimeError):api_db.insert_snapshot_rows([{**row,'collected_at':'2026-10-07T02:00:00Z'}])
                    with ledger.connection() as conn,conn.cursor() as cur:
                        cur.execute('SELECT COUNT(*) FROM snapshots');self.assertEqual(cur.fetchone()[0],1)
        finally:
            if api_db is not None and api_db._pool is not None:api_db._pool.closeall()
            with admin.cursor() as cur:cur.execute(sql.SQL('DROP DATABASE IF EXISTS {}').format(sql.Identifier(name)))
            admin.close()


if __name__=='__main__':unittest.main()
