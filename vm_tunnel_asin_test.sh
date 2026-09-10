#!/bin/bash
KEY="D:/Ram Claude Desk/projects/Amazon Reseller/categories/tools-research/oracle-keys/maxun-server"
VM="ubuntu@140.245.239.162"
ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=20 "$VM" '
echo "=== fetching B0757631XR (a previously-failed ASIN) through the PHONE TUNNEL ==="
curl -s -o /dev/null -m 90 --socks5-hostname 127.0.0.1:1080 \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
  -H "Accept-Language: en-IN" \
  -w "HTTP %{http_code} | %{size_download} bytes | %{time_total}s\n" \
  "https://www.amazon.in/dp/B0757631XR"
echo "=== and B0FWRLQND8 ==="
curl -s -o /dev/null -m 90 --socks5-hostname 127.0.0.1:1080 \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
  -H "Accept-Language: en-IN" \
  -w "HTTP %{http_code} | %{size_download} bytes | %{time_total}s\n" \
  "https://www.amazon.in/dp/B0FWRLQND8"
'