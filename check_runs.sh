#!/bin/bash
# Check the collector run status on GitHub Actions.
ENV="D:/Ram Claude Desk/projects/Amazon Reseller/categories/tools-research/scout-cloud/.env"
TOKEN="$(grep -E '^GITHUB_TOKEN=|^GH_TOKEN=|^GITHUB_PAT=' "$ENV" | head -1 | cut -d= -f2- | tr -d '\r"' | tr -d "'")"

curl -s -m 30 -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/rameshknk143/Scout/actions/runs?per_page=3" | \
python3 -c "
import json, sys
d = json.load(sys.stdin)
for r in d.get('workflow_runs', [])[:3]:
    print(f\"{r['name'][:28]:28} | {r['status']:10} | {r.get('conclusion') or '-':8} | {r['created_at']} | run {r['id']}\")"