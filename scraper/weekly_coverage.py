"""Seven-day category coverage with durable tasks and truthful completion.

The manifest covers registered browse routes and bounded list pages, not every
Amazon catalog ASIN. Public fields are observed; unavailable/private sources
remain explicit statuses. All discovered ASIN/path pairs get detail tasks.
"""
import argparse
import hashlib
import json
import os
import re
import time
import uuid
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from registry.amazon_schema import AmazonSchema

HERE = Path(__file__).parent
IST = ZoneInfo('Asia/Kolkata')
DAYS = ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
_sessions = threading.local()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def monday(day):
    return day-timedelta(days=day.weekday())


def manifest():
    schema=AmazonSchema()
    roots={p['label']:p['slug'] for p in schema.data['top_routes']}
    groups={top:[{'path':top,'slug':slug}] for top,slug in roots.items()}
    for row in schema.data['taxonomy']:
        if row['top'] not in groups:raise ValueError('Unassigned taxonomy root')
        groups[row['top']].append({'path':row['label'],'slug':row['slug']})
    # Stable, balanced by route count, at most four roots per day for 28 roots.
    bins=[[] for _ in DAYS];loads=[0]*7
    root_limit=(len(groups)+6)//7
    for top in sorted(groups,key=lambda k:(-len(groups[k]),k)):
        target=min((i for i in range(7) if len(bins[i])<root_limit),key=lambda i:(loads[i],i))
        bins[target].append(top);loads[target]+=len(groups[top])
    assignments={top:i for i,items in enumerate(bins) for top in items}
    routes=[{**route,'top':top,'weekday':assignments[top]} for top in sorted(groups) for route in groups[top]]
    labels=[r['path'] for r in routes]
    if len(labels)!=len(set(labels)):raise ValueError('Duplicate category path')
    return {'version':1,'schema_version':schema.data['schema_version'],'timezone':'Asia/Kolkata',
            'lists':['bestsellers','new-releases'],'pages':[1,2],
            'routes':routes,'days':[{'day':DAYS[i],'categories':bins[i],'routes':loads[i]} for i in range(7)],
            'scope':'Registered top routes and verified immediate children; all ASIN/path pairs discovered on configured list pages receive detail tasks.'}


def list_tasks(plan,week):
    tasks=[]
    for route in plan['routes']:
        for kind in plan['lists']:
            for page in plan['pages']:
                payload={**route,'list_type':kind,'page':page}
                tasks.append({'task_id':digest([week.isoformat(),'list',route['path'],kind,page]),
                              'due_date':week+timedelta(days=route['weekday']),'kind':'list','path':route['path'],'payload':payload})
    return tasks


class Ledger:
    def __init__(self):
        import db
        self.connection=db.get_conn
        self.task_kind=None

    def preflight(self):
        with self.connection() as conn,conn.cursor() as cur:
            for table in ('scrape_week_plans','scrape_week_tasks','field_observations','snapshots'):
                cur.execute('SELECT to_regclass(%s)',('public.'+table,))
                if cur.fetchone()[0] is None:raise RuntimeError('Required migration missing: '+table)
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='snapshots'")
            required={'asin','category','list_type','rank','title','price','rating','review_count','image_url','collected_at','brand','size_tier_hint','product_type_hint','subcategory','product_type','source'}
            missing=required-{r[0] for r in cur.fetchall()}
            if missing:raise RuntimeError('Snapshot schema missing columns: '+','.join(sorted(missing)))
            cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='snapshots'")
            if not any('UNIQUE' in r[0] and all(k in r[0] for k in ('asin','category','list_type','collected_at')) for r in cur.fetchall()):
                raise RuntimeError('Snapshot replay unique index is required')

    def seed(self,plan,week):
        from psycopg2.extras import Json,execute_values
        fingerprint=digest(plan)
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute('INSERT INTO scrape_week_plans(week_start,plan_hash,manifest) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(week,fingerprint,Json(plan)))
            cur.execute('SELECT plan_hash FROM scrape_week_plans WHERE week_start=%s',(week,))
            if cur.fetchone()[0]!=fingerprint:raise RuntimeError('Active week manifest changed; review/version the next week instead')
            tasks=list_tasks(plan,week)
            execute_values(cur,'INSERT INTO scrape_week_tasks(task_id,week_start,due_date,kind,path,payload) VALUES %s ON CONFLICT DO NOTHING',[(t['task_id'],week,t['due_date'],t['kind'],t['path'],Json(t['payload'])) for t in tasks])

    def recover(self):
        """Re-probe exhausted work daily without resetting the attempt history."""
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute("""UPDATE scrape_week_tasks SET status='RETRY',next_attempt=NOW(),lease_token=NULL,lease_until=NULL
                WHERE status='EXHAUSTED' AND next_attempt<=NOW()-INTERVAL '24 hours'""")

    def storage_guard(self):
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute('SELECT pg_database_size(current_database())')
            size=cur.fetchone()[0]
        if size>=int(os.environ.get('SCOUT_DATABASE_MAX_BYTES',460*1024*1024)):
            raise RuntimeError('database_capacity_guard: archive or expand storage before collection resumes')

    def heartbeat(self,status,detail):
        from psycopg2.extras import Json
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute("""INSERT INTO scrape_worker_health(component,status,detail) VALUES('weekly-coverage',%s,%s)
                ON CONFLICT(component) DO UPDATE SET checked_at=NOW(),status=EXCLUDED.status,detail=EXCLUDED.detail""",(status,Json(detail)))

    def claim(self,today):
        from psycopg2.extras import RealDictCursor
        token=uuid.uuid4().hex
        with self.connection() as conn,conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""WITH candidate AS (
              SELECT task_id FROM scrape_week_tasks WHERE due_date<=%s
              AND (%s::text IS NULL OR kind=%s)
              AND ((status IN ('PENDING','RETRY') AND next_attempt<=NOW()) OR (status='RUNNING' AND attempts<5 AND lease_until<NOW()))
              ORDER BY due_date,CASE WHEN kind='list' THEN 0 ELSE 1 END,task_id
              FOR UPDATE SKIP LOCKED LIMIT 1)
              UPDATE scrape_week_tasks t SET status='RUNNING',attempts=attempts+1,lease_token=%s,lease_until=NOW()+INTERVAL '15 minutes',
              payload=payload || jsonb_build_object('capture_at',NOW())
              FROM candidate c WHERE t.task_id=c.task_id RETURNING t.*""",(today,self.task_kind,self.task_kind,token))
            # A worker dying on its fifth attempt must not leave RUNNING forever.
            row=cur.fetchone()
            cur.execute("UPDATE scrape_week_tasks SET status='EXHAUSTED',last_error='lease_expired_after_final_attempt' WHERE status='RUNNING' AND attempts>=5 AND lease_until<NOW()")
            return dict(row) if row else None

    def finish(self,task,result,details=()):
        from psycopg2.extras import Json,execute_values
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute("UPDATE scrape_week_tasks SET status='DONE',result=%s,completed_at=NOW(),lease_until=NULL WHERE task_id=%s AND lease_token=%s AND status='RUNNING' RETURNING task_id",(Json(result),task['task_id'],task['lease_token']))
            if not cur.fetchone():raise RuntimeError('Task lease lost; completion rejected')
            if details:
                execute_values(cur,'INSERT INTO scrape_week_tasks(task_id,week_start,due_date,kind,path,payload) VALUES %s ON CONFLICT DO NOTHING',[
                    (digest([str(task['week_start']),'detail',task['path'],r['asin']]),task['week_start'],task['due_date'],'detail',task['path'],Json({'asin':r['asin'],'path':task['path'],'top':task['payload']['top'],'product_type':r.get('product_type')})) for r in details])

    def fail(self,task,code):
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute("""UPDATE scrape_week_tasks SET status=CASE WHEN attempts>=5 THEN 'EXHAUSTED' ELSE 'RETRY' END,
              last_error=%s,next_attempt=NOW()+%s*INTERVAL '1 minute',lease_until=NULL
              WHERE task_id=%s AND lease_token=%s AND status='RUNNING'""",(code,min(360,15*2**min(5,task['attempts']-1)),task['task_id'],task['lease_token']))

    def report(self,week,today):
        with self.connection() as conn,conn.cursor() as cur:
            cur.execute('SELECT manifest FROM scrape_week_plans WHERE week_start=%s',(week,))
            row=cur.fetchone()
            if not row:return {'week_start':str(week),'status':'NOT_SEEDED'}
            plan=row[0]
            cur.execute('SELECT path,kind,status,due_date,COUNT(*) FROM scrape_week_tasks WHERE week_start=%s GROUP BY path,kind,status,due_date',(week,))
            records=cur.fetchall()
            cur.execute("SELECT path,COUNT(*) FROM scrape_week_tasks WHERE week_start=%s AND kind='list' AND status='DONE' AND result->>'verified_empty'='true' GROUP BY path",(week,))
            empty_pages=dict(cur.fetchall())
            cur.execute("SELECT status,COUNT(*) FROM scrape_week_tasks WHERE due_date<=%s AND status<>'DONE' GROUP BY status",(today,))
            global_due=dict(cur.fetchall())
            cur.execute("""SELECT item.key,SUM(item.value::bigint) FROM scrape_week_tasks t,
                LATERAL jsonb_each_text(COALESCE(t.result->'field_counts','{}'::jsonb)) item
                WHERE t.week_start=%s AND t.kind='detail' AND t.status='DONE' GROUP BY item.key""",(week,))
            field_counts={key:int(value) for key,value in cur.fetchall()}
            cur.execute("SELECT pg_database_size(current_database())")
            database_bytes=cur.fetchone()[0]
        coverage=[]
        for route in plan['routes']:
            counts=Counter();due=week+timedelta(days=route['weekday'])
            for path,kind,status,_,count in records:
                if path==route['path']:counts[kind+':'+status]+=count
            expected=len(plan['lists'])*len(plan['pages'])
            complete=counts['list:DONE']==expected and not any(v for k,v in counts.items() if k.startswith('detail:') and k!='detail:DONE') and (counts['detail:DONE']>0 or empty_pages.get(route['path'],0)==expected)
            coverage.append({'path':route['path'],'day':DAYS[route['weekday']],'due_date':str(due),'complete':complete,'counts':dict(counts)})
        overdue=[r for r in coverage if not r['complete'] and date.fromisoformat(r['due_date'])<=today]
        return {'week_start':str(week),'status':'COMPLETE' if all(r['complete'] for r in coverage) else 'INCOMPLETE',
                'routes_total':len(coverage),'routes_complete':sum(r['complete'] for r in coverage),'due_incomplete':len(overdue),
                'all_weeks_due_unfinished':global_due,'field_status_counts':field_counts,
                'database_bytes':database_bytes,'coverage':coverage}


def execute(task):
    import collector_optimized as collector
    import db
    from product_detail import parse_detail
    from registry.observation_store import ObservationStore,snapshot_records,deliver
    payload=task['payload']
    if not hasattr(_sessions,'opener'):_sessions.opener=collector._build_opener()
    if task['kind']=='list':
        html=collector.fetch_list_page(task['path'],payload['slug'],payload['list_type'],payload['page'],session=_sessions.opener)
        if not html:raise RuntimeError('fetch_failed')
        matches=list(collector.ASIN_RE.finditer(html));rows=[]
        for i,match in enumerate(matches):
            card=html[match.start():matches[i+1].start() if i+1<len(matches) else len(html)]
            rank=collector.RANK_RE.search(card)
            row=collector.parse_product_card(card,int(rank.group(1)) if rank else None,task['path'],payload['list_type'])
            if row and row.get('title'):rows.append({**row,'collected_at':payload['capture_at']})
        if not rows:
            # An empty catalogue category is different from a bot wall. Require
            # matching full category shells on independent HTTP/browser reads.
            if empty_category_shell(html,payload):
                path=collector.LIST_TYPES[payload['list_type']]
                url=collector.BASE_URL.format(path=path,slug=payload['slug'])
                if payload['page']>1:url+='?pg='+str(payload['page'])
                rendered=browser_html(url)
                if empty_category_shell(rendered,payload):
                    return {'rows_parsed':0,'verified_empty':True,'document_hashes':[digest(html),digest(rendered)]},[]
            raise RuntimeError('empty_or_blocked_list')
        db.insert_snapshot_rows(rows)
        return {'rows_parsed':len(rows)},rows
    html=collector.fetch_with_retry('https://www.amazon.in/dp/'+payload['asin'],session=_sessions.opener)
    if not html:html=browser_html('https://www.amazon.in/dp/'+payload['asin'])
    if not html:raise RuntimeError('detail_fetch_failed')
    product_type='ebook' if payload.get('top')=='Kindle Store' else payload.get('product_type')
    try:
        row=parse_detail(html,payload['asin'],schema_category=task['path'],schema_product_type=product_type)
    except ValueError as exc:
        if str(exc)!='No product title: blocked or unsupported page':raise
        html=browser_html('https://www.amazon.in/dp/'+payload['asin'])
        row=parse_detail(html,payload['asin'],schema_category=task['path'],schema_product_type=product_type)
    row.update(category=task['path'],rank=None,list_type='product-detail',source='weekly-product-detail',collected_at=payload['capture_at'])
    for k in ('price','rating','review_count','image_url'):row.setdefault(k,None)
    records=snapshot_records(row)
    plan=AmazonSchema().plan(task['path'],product_type=row.get('product_type'))
    statuses={key:f['initial_status'] for key,f in plan['fields'].items()}
    for record in records:
        if record['field_key'] in statuses:statuses[record['field_key']]=record['status']
    # Persist complete relevance/missing/private-source statuses as well as actual values.
    db.insert_snapshot_rows([row])
    store=ObservationStore()
    with db.get_conn() as conn,conn.cursor() as cur:accepted=deliver(cur,records)
    store.acknowledge(accepted)
    return {'field_statuses':statuses,'field_counts':dict(Counter(statuses.values())),
            'observed_fields':len(records),'collected_fields':sum(r['status']=='COLLECTED' for r in records)},[]


def browser_html(url):
    """Normal rendered-page fallback; browser resources close on every outcome."""
    from playwright.sync_api import sync_playwright
    from urllib.parse import unquote
    import collector_optimized as collector
    collector._rate_limiter.wait()
    proxy=None
    if collector.PROXY_URL:
        parsed=urlparse(collector.PROXY_URL)
        proxy={'server':f'{parsed.scheme}://{parsed.hostname}:{parsed.port}'}
        if parsed.username:proxy['username']=unquote(parsed.username)
        if parsed.password:proxy['password']=unquote(parsed.password)
    with sync_playwright() as runtime:
        settings={'headless':True}
        if proxy:settings['proxy']=proxy
        if os.environ.get('SCOUT_BROWSER_EXECUTABLE'):settings['executable_path']=os.environ['SCOUT_BROWSER_EXECUTABLE']
        browser=runtime.chromium.launch(**settings)
        try:
            page=browser.new_page(locale='en-IN')
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_timeout(2000)
            return page.content()
        finally:browser.close()


def empty_category_shell(html,payload):
    from bs4 import BeautifulSoup
    if len(html)<20000 or re.search(r'/dp/[A-Z0-9]{10}|data-asin="[A-Z0-9]{10}"',html):return False
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    heading=' '.join(h.get_text(' ',strip=True) for h in soup.select('h1,h2'))
    normalize=lambda value:re.sub(r'[^a-z0-9]','',value.lower())
    expected=normalize(payload['path'].split(' > ')[-1])
    marker='bestsellers' if payload['list_type']=='bestsellers' else 'newreleases'
    blocked=any(word in html.lower() for word in ('validatecaptcha','robot check','automated access'))
    return bool(expected and not blocked and 'Amazon.in' in title and marker in normalize(title) and expected in normalize(title) and expected in normalize(heading))


def run_due(ledger,today,*,minutes,max_tasks,workers):
    deadline=time.monotonic()+minutes*60
    stopped=threading.Event();lock=threading.Lock();state={'claimed':0,'consecutive_failures':0,'succeeded':0,'failed':0}
    def worker():
        while not stopped.is_set() and time.monotonic()<deadline:
            with lock:
                if state['claimed']>=max_tasks:return
                state['claimed']+=1
            task=ledger.claim(today)
            if not task:return
            try:
                if hasattr(ledger,'storage_guard'):ledger.storage_guard()
                result,details=execute(task);ledger.finish(task,result,details)
                with lock:state['consecutive_failures']=0;state['succeeded']+=1
            except Exception as exc:
                safe_messages={'fetch_failed','empty_or_blocked_list','detail_fetch_failed',
                    'No product title: blocked or unsupported page','Product page ASIN differs from requested ASIN',
                    'Canonical product differs from requested ASIN','Blank ASIN input requires a matching canonical product URL'}
                code=str(exc) if isinstance(exc,(RuntimeError,ValueError)) and str(exc) in safe_messages else type(exc).__name__
                ledger.fail(task,code)
                with lock:
                    state['consecutive_failures']+=1
                    state['failed']+=1
                    if state['consecutive_failures']>=3:stopped.set()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(worker) for _ in range(workers)]
        for future in futures:future.result()
    return state


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',action='store_true');parser.add_argument('--migrate',action='store_true')
    parser.add_argument('--report',action='store_true');parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--date',type=date.fromisoformat)
    parser.add_argument('--max-tasks',type=int,default=1000);parser.add_argument('--minutes',type=int,default=100)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--details-only',action='store_true',help='Bounded detail-delivery canary')
    args=parser.parse_args(argv)
    if args.max_tasks<1 or args.minutes<1:parser.error('Budgets must be positive')
    if not 1<=args.workers<=4:parser.error('Workers must be between 1 and 4')
    today=args.date or datetime.now(IST).date();week=monday(today);plan=manifest()
    if args.plan:
        print(json.dumps({**plan,'weekly_list_tasks':len(list_tasks(plan,week))},indent=2));return 0
    ledger=Ledger()
    if args.details_only:ledger.task_kind='detail'
    if args.migrate:
        from registry.observation_store import SQL_PATH
        with ledger.connection() as conn,conn.cursor() as cur:
            cur.execute(SQL_PATH.read_text(encoding='utf-8'));cur.execute((HERE/'weekly_coverage.sql').read_text(encoding='utf-8'))
        return 0
    ledger.preflight()
    if args.preflight:
        print('Required tables, snapshot columns and replay index verified');return 0
    if not args.report:
        ledger.storage_guard()
        ledger.seed(plan,week)
        ledger.recover()
        ledger.heartbeat('RUNNING',{'week_start':str(week)})
        tick=run_due(ledger,today,minutes=args.minutes,max_tasks=args.max_tasks,workers=args.workers)
        ledger.heartbeat('DEGRADED' if tick['failed'] else 'OK',tick)
    report=ledger.report(week,today)
    Path('weekly-coverage-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='coverage'}))
    if not args.report and tick['failed']:return 3
    return 2 if report.get('due_incomplete',0)>0 or report.get('all_weeks_due_unfinished') or report['status']=='NOT_SEEDED' else 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        try:Ledger().heartbeat('ERROR',{'error_type':type(exc).__name__})
        except Exception:pass
        raise
