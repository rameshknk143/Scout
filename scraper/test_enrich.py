#!/usr/bin/env python3
"""Test Phase 1b enrichment against a few known ASINs."""
import os
import sys
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgres://dummy:dummy@localhost:5432/dummy'

# Patch get_conn to avoid actual DB call during test
import enrich_top_asins
enrich_top_asins.get_conn = lambda: None

from enrich_top_asins import fetch_product_page, parse_product_page

# Test with 3 real ASINs from recent collector output
test_asins = [
    "B0DDHM6D3L",  # Portronics earphones (rank 1 electronics)
    "B0D2R2MXXJ",  # Samsung charger
    "B098NS6PVG",  # Ambrane cable
]

print("=== Testing enrichment parser ===\n")
for asin in test_asins:
    print(f"--- {asin} ---")
    html = fetch_product_page(asin)
    if not html:
        print("  FAIL: page unreachable")
        continue
    data = parse_product_page(html, asin)
    print(f"  title:   {data.get('title_enriched', 'N/A')[:80]}")
    print(f"  brand:   {data.get('brand', 'N/A')}")
    print(f"  price:   ₹{data.get('price')}")
    print(f"  rating:  {data.get('rating')}")
    print(f"  reviews: {data.get('review_count')}")
    print(f"  bsr:     #{data.get('bsr_rank')} in {data.get('bsr_category')}")
    print(f"  stock:   {'in stock' if data.get('in_stock') else 'unknown'}")
    print(f"  seller:  {data.get('seller', 'N/A')[:40]}")
    print(f"  dims:    {data.get('dimensions', 'N/A')}")
    print(f"  weight:  {data.get('weight', 'N/A')}")
    print(f"  material:{data.get('material', 'N/A')}")
    print(f"  warranty:{data.get('warranty', 'N/A')}")
    print()
