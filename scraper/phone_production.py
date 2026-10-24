"""Hourly official catalog client; scoped key, durable signed outbox, no Amazon secrets."""
import argparse
import json
import shutil
import sqlite3
import time
import urllib.request
import urllib.error
from pathlib import Path
from hourly_automation import Ledger, hour_slot

BASE = Path('/opt/scout')
API = 'https://scout-api-3yvy.onrender.com'

def call(path, payload=None):
    key = (BASE / 'production.key').read_text().strip()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(API + path, data=data, headers={
        'X-Scout-Phone-Key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=110) as response:
        return json.load(response)

def _tick(ledger,out):
    out.execute('PRAGMA journal_mode=WAL')
    out.execute('CREATE TABLE IF NOT EXISTS captures(slot INTEGER PRIMARY KEY,payload TEXT NOT NULL,rows INTEGER NOT NULL,delivered_at REAL,receipt TEXT)')
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
        except (OSError,ValueError,urllib.error.URLError):
            return 'delivery_pending'
    slot = hour_slot(time.time())
    if not ledger.claim('phone-official-catalog',slot):
        return 'already_recorded'
    temp = Path('/sys/class/power_supply/battery/temp')
    if (temp.exists() and int(temp.read_text()) >= 430) or shutil.disk_usage(BASE).free < 512*1024*1024:
        ledger.finish('phone-official-catalog',slot,'paused',attempts=0,error='thermal_or_disk_guard')
        return 'paused'
    try:
        data = call('/phone/catalog')
        rows = data['batch']['rows']
        if not isinstance(rows,list) or len(rows)>20 or not isinstance(data['proof'],str):
            raise ValueError('invalid_capture')
        with out:
            out.execute('INSERT INTO captures(slot,payload,rows) VALUES(?,?,?)',(slot,json.dumps(data),len(rows)))
        ledger.finish('phone-official-catalog',slot,'delivery_pending',captured=len(rows),result={
            'production':True,'source':'official-amazon-catalog','captured_at':data['batch']['captured_at'],
            'run_id':'moto-g85:'+str(slot),'price_available':False})
        return 'captured'
    except (OSError,ValueError,KeyError,TypeError,urllib.error.URLError) as error:
        code = getattr(error,'code',None)
        ledger.finish('phone-official-catalog',slot,'failed',error='capture_failed_no_blind_replay',result={'http_status':code})
        return 'failed'

def tick():
    ledger=Ledger(BASE/'automation.sqlite')
    out=sqlite3.connect(BASE/'production-outbox.sqlite',timeout=15)
    try:
        return _tick(ledger,out)
    finally:
        out.close()
        ledger.db.close()

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
            status=tick()
        except (OSError,sqlite3.Error,ValueError):
            status='local_error_data_retained'
        (BASE/'production-health.json').write_text(json.dumps({'checked_at':time.time(),'status':status,'production_enabled':True,'source':'official-amazon-catalog','maximum_items_per_hour':20}))
        if once:
            print(status)
            return
        time.sleep(60)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    main(parser.parse_args().once)

