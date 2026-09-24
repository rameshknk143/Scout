
import requests, re

UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept-Language":"en-IN,en;q=0.9"}

# compound slug = topslug/node
tests = [
    ("electronics","1388867031"),
    ("electronics","92071051031"),
    ("sports","3403617031"),
    ("books","1318064031"),
    ("music","1375706031"),
]

for top,node in tests:
    url = f"https://www.amazon.in/gp/bestsellers/{top}/{node}/"
    try:
        r = requests.get(url, headers=UA, timeout=25)
        html = r.text
        asins = re.findall(r'data-asin="([A-Z0-9]{10})"', html)
        botwall = "(MEOW)" in html or "automated access" in html.lower()
        print(f"{top}/{node}  status={r.status_code}  size={len(html):>8}  asins={len(asins):>3}  botwall={'YES' if botwall else 'no'}")
    except Exception as e:
        print(f"{top}/{node}  ERROR {str(e)[:60]}")
