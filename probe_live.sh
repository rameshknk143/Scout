#!/bin/bash
# Live scraper + tunnel status, flattened to readable lines. Key from .env, never echoed.
ENV="D:/Ram Claude Desk/projects/Amazon Reseller/categories/tools-research/scout-cloud/.env"
API="https://scout-api-3yvy.onrender.com"
KEY="$(grep -E '^API_KEY=' "$ENV" | head -1 | cut -d= -f2- | tr -d '\r"' | tr -d "'")"

OUT="$LOCALAPPDATA/Temp/scout_status.json"
curl -s -m 40 "$API/ops/status" -H "X-Scout-Key: $KEY" > "$OUT"

python3 - "$OUT" <<'PY'
import json, sys
raw = open(sys.argv[1]).read()
data = json.loads(raw)
hb = data.get('heartbeats', [])
print("=== LIVE HEARTBEATS ===")
for h in hb:
    d = h.get('detail', {}).get('detail', {})
    print(f"{h['component']:14} {h['status']:3}  {h.get('last_seen_ist','')}  -> {d.get('summary') or d.get('message','')}")
print()
vm = hb[0]['detail']['detail'] if hb else {}
print("=== TUNNEL (the phone) ===")
print("listener :", vm.get('tunnel_listener'))
print("exit_ip  :", vm.get('tunnel_exit_ip'))
print("uptime   :", vm.get('tunnel_uptime_samples'))
th = vm.get('tunnel_history', [])
print("--- last 10 hours of tunnel up% (UTC) ---")
for t in th[-10:]:
    print(f"  {t['hour']}  up={t['up_pct']:5}%  n={t['samples']}")
print()
print("=== VM SCRAPE (watchlist) ===")
sc = [h for h in hb if h['component']=='vm-scrape']
if sc:
    dd = sc[0]['detail']['detail']
    print("last:", sc[0]['last_seen_ist'])
    print("result:", dd.get('message'), "| attempted", dd.get('attempted'), "landed", dd.get('landed'))
print()
print("=== RECENT ERROR EVENTS ===")
for e in data.get('recent_events', []):
    print(f"{e['severity']:5} {e['component']:12} {e['created_at_ist']}  {e['message'][:110]}")
PY