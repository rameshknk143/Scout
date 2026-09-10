#!/bin/bash
ENV="D:/Ram Claude Desk/projects/Amazon Reseller/categories/tools-research/scout-cloud/.env"
API="https://scout-api-3yvy.onrender.com"
KEY="$(grep -E '^API_KEY=' "$ENV" | head -1 | cut -d= -f2- | tr -d '\r"' | tr -d "'")"
OUT="$LOCALAPPDATA/Temp/scout_status.json"
curl -s -m 40 "$API/ops/status" -H "X-Scout-Key: $KEY" > "$OUT"

python3 - "$OUT" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1]).read())
hb = data.get('heartbeats', [])
# full raw dump of vm-scrape + any error-state component
for h in hb:
    if h['component'] in ('vm-scrape',) or h['status'] != 'ok':
        print("==== RAW:", h['component'], "status", h['status'], "====")
        print(json.dumps(h, indent=2, default=str))
        print()
print("==== recent_events (last 10) ====")
for e in data.get('recent_events', [])[:10]:
    print(json.dumps(e, default=str)[:400])
    print()
PY