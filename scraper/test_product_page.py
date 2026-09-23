"""Quick test: can we fetch product pages from local IP?"""
import requests, re, sys

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "en-IN,en;q=0.9"}

test_asins = ["B0DDHM6D3L", "B0D2R2MXXJ", "B098NS6PVG"]
for asin in test_asins:
    url = f"https://www.amazon.in/dp/{asin}"
    try:
        r = requests.get(url, headers=UA, timeout=25)
        h = r.text
        size = len(h)
        botwall = "(MEOW)" in h or "automated access" in h.lower()
        brand_m = re.search(r'"brand"\s*:\s*"([^"]+)"', h)
        title_m = re.search(r'id="productTitle"[^>]*value="([^"]+)"', h)
        print(f"{asin}: size={size:>8}  botwall={'YES' if botwall else 'no'}  brand={brand_m.group(1) if brand_m else 'N/A'}  title={title_m.group(1)[:50] if title_m else 'N/A'}")
    except Exception as e:
        print(f"{asin}: ERR {str(e)[:60]}")
