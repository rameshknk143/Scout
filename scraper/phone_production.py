"""Paginated official catalog client; scoped key, durable signed outbox, no Amazon secrets."""
import argparse
import json
import shutil
import sqlite3
import time
import urllib.request
import urllib.error
from pathlib import Path
from hourly_automation import Ledger
from urllib.parse import urlencode
from email.utils import parsedate_to_datetime
INTERVAL_SECONDS = 90
REQUESTS_PER_CYCLE = 5
MIN_REQUEST_GAP_SECONDS = 12
QUERY_COUNT = 32
MAX_PAGES = 50

BASE = Path('/opt/scout')
API = 'https://scout-api-3yvy.onrender.com'

def call(path, payload=None):
    key = (BASE / 'production.key').read_text().strip()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(API + path, data=data, headers={
        'X-Scout-Phone-Key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=110) as response:
        return json.load(response)

def retry_delay(error, minimum):
    raw = error.headers.get('Retry-After', '') if getattr(error, 'headers', None) else ''
    try:
        delay = float(raw)
    except (ValueError, TypeError):
        try:
            delay = parsedate_to_datetime(raw).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            delay = 300
    return max(minimum, delay)


def _tick(ledger,out,slot_override=None,delivery_only=False):
    out.execute('PRAGMA journal_mode=WAL')
    out.execute('CREATE TABLE IF NOT EXISTS captures(slot INTEGER PRIMARY KEY,payload TEXT NOT NULL,rows INTEGER NOT NULL,delivered_at REAL,receipt TEXT)')
    out.execute('CREATE TABLE IF NOT EXISTS cursor_state(id INTEGER PRIMARY KEY,query_index INTEGER,token TEXT,page INTEGER,not_before REAL,blocked TEXT)')
    out.execute("INSERT OR IGNORE INTO cursor_state VALUES(1,0,'',0,0,NULL)");out.commit()
    query_index,token,page,not_before,blocked=out.execute('SELECT query_index,token,page,not_before,blocked FROM cursor_state WHERE id=1').fetchone()
    if blocked:return 'authorization_blocked'
    if time.time()<not_before:return 'throttled_or_storage_pause'
    # Delivery is safe to retry: the server verifies its original signed batch,
    # and snapshots/field records use existing unique observation identities.
    for slot, raw, count in out.execute('SELECT slot,payload,rows FROM captures WHERE delivered_at IS NULL ORDER BY slot').fetchall():
        try:
            result = call('/phone/deliver', json.loads(raw))
            if result.get('ok') is not True or result.get('verified') != count:
                raise ValueError('delivery_receipt_mismatch')
            with out:
                out.execute('UPDATE captures SET delivered_at=?,receipt=? WHERE slot=?', (time.time(),json.dumps(result),slot))
            ledger.finish('phone-official-catalog',slot,'success',captured=count,delivered=count,result={**result,'production':True,'run_id':'moto-g85:'+str(slot),'source':'official-amazon-catalog'})
        except (OSError,ValueError,urllib.error.URLError) as error:
            code=getattr(error,'code',None)
            with out:
                if code in (400,401,403) or isinstance(error,ValueError):
                    out.execute("UPDATE cursor_state SET blocked='delivery_requires_review' WHERE id=1")
                else:
                    delay=retry_delay(error,60)
                    out.execute('UPDATE cursor_state SET not_before=? WHERE id=1',(time.time()+delay,))
            return 'delivery_pending'
    if delivery_only:
        return 'delivered'
    slot = slot_override if slot_override is not None else int(time.time() // INTERVAL_SECONDS) * INTERVAL_SECONDS
    if not ledger.claim('phone-official-catalog',slot):
        return 'already_recorded'
    temp = Path('/sys/class/power_supply/battery/temp')
    if (temp.exists() and int(temp.read_text()) >= 430) or shutil.disk_usage(BASE).free < 512*1024*1024:
        ledger.finish('phone-official-catalog',slot,'paused',attempts=0,error='thermal_or_disk_guard')
        return 'paused'
    try:
        data = call('/phone/catalog?'+urlencode({'query_index':query_index,'page_token':token}))
        rows = data['batch']['rows']
        if not isinstance(rows,list) or len(rows)>20 or not isinstance(data['proof'],str):
            raise ValueError('invalid_capture')
        next_token=data['batch'].get('next_token')
        if not isinstance(next_token,(str,type(None))):raise ValueError('invalid_cursor')
        if next_token and next_token!=token and page+1<MAX_PAGES:
            next_query,next_page=query_index,page+1
        else:
            next_query,next_token,next_page=(query_index+1)%QUERY_COUNT,'',0
        with out:
            out.execute('INSERT INTO captures(slot,payload,rows) VALUES(?,?,?)',(slot,json.dumps(data),len(rows)))
            out.execute('UPDATE cursor_state SET query_index=?,token=?,page=? WHERE id=1',(next_query,next_token or '',next_page))
        ledger.finish('phone-official-catalog',slot,'delivery_pending',captured=len(rows),result={
            'production':True,'source':'official-amazon-catalog','captured_at':data['batch']['captured_at'],
            'run_id':'moto-g85:'+str(slot),'price_available':any(r.get('price') is not None for r in rows),'priced_rows':sum(r.get('price') is not None for r in rows)})
        return 'captured'
    except (OSError,ValueError,KeyError,TypeError,urllib.error.URLError) as error:
        code = getattr(error,'code',None)
        with out:
            if code in (401,403):
                out.execute("UPDATE cursor_state SET blocked='authorization_denied' WHERE id=1")
            elif code in (429,503):
                delay=retry_delay(error,90)
                out.execute('UPDATE cursor_state SET not_before=? WHERE id=1',(time.time()+delay,))
            elif code==400 and token:
                out.execute("UPDATE cursor_state SET query_index=?,token='',page=0 WHERE id=1",((query_index+1)%QUERY_COUNT,))
        ledger.finish('phone-official-catalog',slot,'failed',error='capture_failed_no_blind_replay',result={'http_status':code})
        return 'failed'

def tick(slot_override=None,delivery_only=False):
    ledger=Ledger(BASE/'automation.sqlite')
    out=sqlite3.connect(BASE/'production-outbox.sqlite',timeout=15)
    try:
        return _tick(ledger,out,slot_override,delivery_only)
    finally:
        out.close()
        ledger.db.close()

def cycle():
    """Up to five signed pages; retain each page separately and rest 90s."""
    status=tick(delivery_only=True)
    if status!='delivered':
        return status
    control=sqlite3.connect(BASE/'production-outbox.sqlite',timeout=15)
    try:
        control.execute('CREATE TABLE IF NOT EXISTS batch_control(id INTEGER PRIMARY KEY,next_cycle REAL NOT NULL)')
        control.execute('INSERT OR IGNORE INTO batch_control VALUES(1,0)')
        control.commit()
        if time.time()<control.execute('SELECT next_cycle FROM batch_control WHERE id=1').fetchone()[0]:
            return 'batch_gap'
        base=int(time.time()//INTERVAL_SECONDS)*INTERVAL_SECONDS
        try:
            last_start=None
            for index in range(REQUESTS_PER_CYCLE):
                if last_start is not None:
                    time.sleep(max(0,MIN_REQUEST_GAP_SECONDS-(time.monotonic()-last_start)))
                last_start=time.monotonic()
                # Fail closed after an abrupt process death during a request.
                # Normal completion replaces this reservation with a 90s rest.
                with control:
                    control.execute('UPDATE batch_control SET next_cycle=? WHERE id=1',(time.time()+900,))
                status=tick(slot_override=base+index)
                if status!='captured':
                    return status
            return 'cycle_complete' if tick(delivery_only=True)=='delivered' else 'delivery_pending'
        finally:
            # Restarting the worker must not shorten the batch gap.
            with control:
                control.execute('UPDATE batch_control SET next_cycle=? WHERE id=1',(time.time()+INTERVAL_SECONDS,))
    finally:
        control.close()


def main(once=False):
    import fcntl
    lock=(BASE/'production.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Preserve uncertain old attempts without running them again.
    ledger=Ledger(BASE/'automation.sqlite')
    with ledger.db:
        ledger.db.execute("UPDATE jobs SET status='interrupted',finished=?,error='process_interruption_no_blind_replay' WHERE pipeline='phone-official-catalog' AND status='running'",(time.time(),))
    ledger.db.close()
    while True:
        try:
            status=cycle()
        except (OSError,sqlite3.Error,ValueError):
            status='local_error_data_retained'
        pending=BASE/'production-health.tmp'
        pending.write_text(json.dumps({'checked_at':time.time(),'status':status,'production_enabled':True,'source':'official-amazon-catalog','minimum_cycle_gap_seconds':INTERVAL_SECONDS,'requests_per_cycle':REQUESTS_PER_CYCLE,'minimum_request_gap_seconds':MIN_REQUEST_GAP_SECONDS,'maximum_rows_per_cycle':20*REQUESTS_PER_CYCLE,'query_count':QUERY_COUNT}))
        pending.replace(BASE/'production-health.json')
        if once:
            print(status)
            return
        time.sleep(15)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    main(parser.parse_args().once)

