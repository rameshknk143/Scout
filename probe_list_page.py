#!/usr/bin/env python3
"""Probe list page to discover what EXTRA fields we can parse beyond the 10 we already scrape."""
import requests, re, sys

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

url = "https://www.amazon.in/gp/bestsellers/electronics/"
try:
    r = requests.get(url, headers=UA, timeout=25)
    h = r.text
    print(f"Page size: {len(h):,} chars")
    print()

    # Find first product card block
    idx = h.find('data-asin="')
    if idx >= 0:
        card = h[idx:idx+3000]
        print("=== FIRST CARD HTML BLOCK ===")
        print(card[:1500])
        print("...\n")

    # Try extracting brand (common patterns)
    brands = re.findall(r'data-brand[^>]*>', h)
    print(f"brand attributes found: {len(brands)}")
    for b in brands[:3]:
        print(f"  {b[:200]}")

    # Try extracting seller info
    sellers = re.findall(r'_sold_by[^\"]*"[^"]*"', h)
    print(f"\nseller mentions: {len(sellers)}")

    # Try extracting item weight / dimensions
    weights = re.findall(r'(\d+(?:\.\d+)?)\s*(g|kg|lb|oz)', h, re.I)
    print(f"\nweight mentions: {len(weights)}")

    # Look at the exact class pattern around product cards
    asins = re.findall(r'data-asin="([A-Z0-9]{10})"', h)
    print(f"\ntotal ASINs on page: {len(asins)}")

    # Check what comes AFTER data-asin in each card
    for i, asin in enumerate(asins[:3]):
        pos = h.find(f'data-asin="{asin}"')
        context = h[pos:pos+800]
        print(f"\n=== CARD {i+1} for {asin} ===")
        print(context[:600])
        print("...")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
