#!/usr/bin/env python3
"""Test: can we extract brand from URL slug on Amazon.in list pages?"""
import requests, re, sys

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Test with a few different categories
test_urls = [
    "https://www.amazon.in/gp/bestsellers/electronics/",
    "https://www.amazon.in/gp/bestsellers/kitchen/",
    "https://www.amazon.in/gp/bestsellers/books/",
]

patterns = [
    # Brand appears BEFORE the first hyphen-separated word cluster in URL
    r'/([^/]+?)-[^/]*dp/',  # Brand-word before /dp/
    r'/([A-Z][a-z]+(?:-[A-Z][a-z]+)*)-[\w\-]+dp/',  # CamelCase brand
]

for url in test_urls:
    print(f"\n=== {url.split('/')[-3].title()} ===")
    try:
        r = requests.get(url, headers=UA, timeout=25)
        h = r.text
        asins = re.findall(r'data-asin="([A-Z0-9]{10})"', h)
        
        for asin in asins[:5]:
            pos = h.find(f'data-asin="{asin}"')
            block = h[pos:pos+2500]
            
            # Try to find brand in href
            href_match = re.search(r'href="(/[^"]+/dp/' + asin + r'/[^"]+)"', block)
            if href_match:
                slug = href_match.group(1)
                # Extract brand part (first segment before -dp- or before hyphen cluster)
                parts = slug.split('/')
                for p in parts:
                    if p == 'dp' or p == asin:
                        break
                    # Try to identify brand: words starting with capital, 2+ chars
                    words = p.split('-')
                    potential_brand = []
                    for w in words:
                        if len(w) >= 2 and w[0].isupper() and w.isalpha():
                            potential_brand.append(w)
                    if potential_brand:
                        print(f"  {asin}: brand_candidates={potential_brand}, slug_part={p}")
                        break
    except Exception as e:
        print(f"ERROR: {e}")
