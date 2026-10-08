"""Durable canonical-field outbox plus append-only PostgreSQL delivery.

Snapshot insert receipts keep their existing meaning. Field delivery is tracked
separately; a missing migration never silently discards parsed specifications.
"""
import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .amazon_schema import AmazonSchema

SQL_PATH = Path(__file__).with_name('field_observations.sql')
DEFAULT_PATH = Path(__file__).parent.parent/'.field_observations.sqlite'

@lru_cache(maxsize=1)
def schema():return AmazonSchema()

@lru_cache(maxsize=512)
def _plan(category, subcategory, product_type):
    return schema().plan(category,subcategory,product_type)

def timestamp(value):
    dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Observation requires a timezone-aware capture timestamp')
    return dt.astimezone(timezone.utc).isoformat()

def snapshot_records(row):
    """Represent observed values only. List position is never substituted for BSR."""
    asin=row.get('asin','')
    if not re.fullmatch(r'[A-Z0-9]{10}',asin):raise ValueError('Invalid observation ASIN')
    observed=timestamp(row['collected_at'])
    category=str(row.get('category') or 'Unknown')
    plan=_plan(category,row.get('subcategory'),row.get('product_type'))
    url=f'https://www.amazon.in/dp/{asin}'
    source=str(row.get('source') or row.get('list_type') or 'collector')
    aliases={'seller':'seller_name','availability_text':'availability_text'}
    public={'asin','title','brand','manufacturer','price','rating','review_count','image_url',
            'category','subcategory','product_type','seller','availability_text'}
    observations=[]
    for old in sorted(public & row.keys()):
        raw=row[old]
        if raw is None:continue
        key=aliases.get(old,old);f=plan['fields'][key]
        status=f['initial_status'];value=None
        if f['applicability_status']=='APPLICABLE':
            try:value=schema().normalize(f,[raw] if key=='subcategory' and isinstance(raw,str) else raw);status='COLLECTED'
            except (ValueError,TypeError,ArithmeticError):status='FAILED'
        if status=='COLLECTED' and ((source=='collector' and old in {'brand','subcategory','product_type'}) or
            ((row.get('attribute_observations') or {}).get('classification_evidence') and old in {'subcategory','product_type'})):
            status='INFERRED'
        observations.append({'field_key':key,'raw_value':raw,'normalized_value':value,
                             'status':status,'scope':f['scope'],'unit':f['unit'],
                             'source_url':url,'observed_at':observed,'schema_version':plan['schema_version']})
    bundle=row.get('attribute_observations') or {}
    if len(bundle.get('observations',[]))>500 or len(bundle.get('unmapped',[]))>500:
        raise ValueError('Too many field observations in one product')
    for incoming in bundle.get('observations',[]):
        key=incoming['field_key']
        if key not in plan['fields']:raise ValueError('Unknown canonical field')
        f=plan['fields'][key];record=dict(incoming)
        record['normalized_value']=None
        record['status']=f['initial_status']
        record['scope']=f['scope'];record['unit']=f['unit']
        record['source_url']=url;record['schema_version']=plan['schema_version']
        if f['source'] not in {'product_page','technical_specs'}:
            record['status']='WRONG_COLLECTION_SOURCE'
        elif f['applicability_status']=='APPLICABLE':
            try:
                record['normalized_value']=schema().normalize(f,record.get('raw_value'),record.get('source_unit'))
                record['status']='COLLECTED'
            except (ValueError,TypeError,ArithmeticError):record['status']='FAILED'
        observations.append(record)
    # Preserve unknown labels and original structured source values for a later
    # reviewed schema extension, without declaring them canonical collected fields.
    for record in bundle.get('unmapped',[]):
        observations.append({'field_key':'unreviewed:'+record['label'],'raw_value':record.get('raw_value'),
                             'normalized_value':None,'status':'UNREVIEWED_ATTRIBUTE','scope':'variant',
                             'unit':None,'source_url':url,'observed_at':observed,
                             'schema_version':bundle.get('schema_version',plan['schema_version'])})
    records=[]
    for observation in observations:
        o=dict(observation)
        # All values from one page use the actual page capture time, not a later
        # normalization/delivery time; callers cannot overwrite immutable history.
        o.update({'asin':asin,'marketplace':'amazon.in','category':category,
                  'product_type':row.get('product_type'),'source':source,'observed_at':observed})
        o['context']={'list_type':row.get('list_type'),'list_rank':row.get('rank'),
                      'count_kind':'source_label_unspecified' if o['field_key']=='review_count' else None,
                      'seller_id':row.get('seller_id'),'schema_category_status':plan['category']['status']}
        payload=json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
        o['observation_id']=hashlib.sha256(payload.encode('utf-8')).hexdigest()
        records.append(o)
    return records

class ObservationStore:
    def __init__(self,path=None):
        self.path=Path(path or os.environ.get('SCOUT_FIELD_STORE',DEFAULT_PATH))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.executescript('''PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS observations(
                  observation_id TEXT PRIMARY KEY, asin TEXT NOT NULL,
                  field_key TEXT NOT NULL, observed_at TEXT NOT NULL,
                  payload TEXT NOT NULL, delivered_at TEXT);
                CREATE INDEX IF NOT EXISTS field_history ON observations(asin,field_key,observed_at);
                CREATE INDEX IF NOT EXISTS pending_fields ON observations(delivered_at,observed_at);''')

    @contextmanager
    def connect(self):
        conn=sqlite3.connect(self.path,timeout=30)
        try:
            with conn:yield conn
        finally:conn.close()

    def enqueue(self,rows):
        records=[r for row in rows for r in snapshot_records(row)]
        return self.enqueue_records(records)

    def enqueue_records(self,records):
        with self.connect() as conn:
            before=conn.total_changes
            conn.executemany('INSERT OR IGNORE INTO observations(observation_id,asin,field_key,observed_at,payload) VALUES(?,?,?,?,?)',
                [(r['observation_id'],r['asin'],r['field_key'],r['observed_at'],json.dumps(r,ensure_ascii=False,allow_nan=False)) for r in records])
            return conn.total_changes-before

    def pending(self,limit=2000):
        with self.connect() as conn:
            return [json.loads(row[0]) for row in conn.execute('SELECT payload FROM observations WHERE delivered_at IS NULL ORDER BY observed_at,observation_id LIMIT ?',(limit,))]

    def acknowledge(self,observation_ids):
        with self.connect() as conn:
            conn.executemany('UPDATE observations SET delivered_at=? WHERE observation_id=?',
                             [(datetime.now(timezone.utc).isoformat(),key) for key in observation_ids])

    def status(self):
        with self.connect() as conn:
            total,pending=conn.execute('SELECT COUNT(*),COALESCE(SUM(delivered_at IS NULL),0) FROM observations').fetchone()
        return {'total_observations':total,'pending_delivery':pending,'path':str(self.path)}

def deliver(cursor,records):
    """Return IDs accepted by an existing migrated table; caller commits before ack."""
    from psycopg2.extras import Json, execute_values
    if not records:return []
    cursor.execute("SELECT to_regclass('public.field_observations')")
    if cursor.fetchone()[0] is None:return []
    execute_values(cursor,'''INSERT INTO field_observations
      (observation_id,marketplace,asin,field_key,scope,source,source_url,observed_at,schema_version,status,unit,raw_value,normalized_value,context)
      VALUES %s ON CONFLICT (observation_id) DO NOTHING''',
      [(r['observation_id'],r['marketplace'],r['asin'],r['field_key'],r['scope'],r['source'],
        r['source_url'],r['observed_at'],r['schema_version'],r['status'],r.get('unit'),
        Json(r.get('raw_value')),Json(r.get('normalized_value')),Json(r.get('context',{}))) for r in records])
    # ON CONFLICT is a valid replay acknowledgement after the surrounding commit.
    return [r['observation_id'] for r in records]

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--flush',action='store_true')
    parser.add_argument('--migrate',action='store_true');args=parser.parse_args()
    store=ObservationStore()
    if args.flush or args.migrate:
        import psycopg2
        with psycopg2.connect(os.environ['DATABASE_URL']) as conn:
            with conn.cursor() as cursor:
                if args.migrate:cursor.execute(SQL_PATH.read_text(encoding='utf-8'))
                accepted=deliver(cursor,store.pending()) if args.flush else []
        store.acknowledge(accepted)
    print(json.dumps(store.status()))
