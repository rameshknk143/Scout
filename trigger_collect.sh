#!/bin/bash
# Trigger the nightly collector NOW via workflow_dispatch (page-2 depth debut run).
ENV="D:/Ram Claude Desk/projects/Amazon Reseller/categories/tools-research/scout-cloud/.env"
TOKEN="$(grep -E '^GITHUB_TOKEN=|^GH_TOKEN=|^GITHUB_PAT=' "$ENV" | head -1 | cut -d= -f2- | tr -d '\r"' | tr -d "'")"
REPO="rameshknk143/Scout"

curl -s -m 30 -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/$REPO/actions/workflows/nightly-collect.yml/dispatches" \
  -d '{"ref":"main"}' \
  -w "\nHTTP %{http_code}\n"