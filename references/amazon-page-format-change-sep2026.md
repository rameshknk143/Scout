# Amazon page-format change — Sept 18 2026

## What happened

On 2026-09-18 the nightly collector dropped from ~6,000 rows/run to ~3,500 rows/run — and has stayed there. Root cause: Amazon changed bestseller list pages from server-rendered HTML to client-side JavaScript rendering. Pages still return HTTP 200 (~320 KB), but zero `data-asin` attributes exist in the raw HTML.

## Before vs after

| Date | Page-1 ok/fail | Page-2 ok/fail | Total rows |
|---|---|---|---|
| 12 Sep | 107 ok / 17 failed | 101 ok / 0 failed | 6,315 |
| 13 Sep | 107 ok / 17 failed | 101 ok / 0 failed | 6,165 |
| 18 Sep | 54 ok / 70 failed | 57 ok / 0 failed | 3,278 |
| 19–22 Sep | ~55 ok / ~62 failed | similar | ~3,400–3,700 |

The same ~17 categories that were failing before (Apps & Games, Gift Cards, etc.) continue to fail — they were always the weak ones. The new failures are widespread: Health & Personal Care, Home Improvement, Industrial & Scientific, Jewellery, Shoes & Handbags, Video Games, Clothing & Accessories, Electronics Accessories, Beauty & Personal Care, Toys & Games, Garden & Outdoors, Pet Supplies, and most "most-wished-for" lists. The pages load and render in a browser, but `curl` on the VM gets a stub that contains navigation chrome but no product data.

## How it was diagnosed (transferable pattern)

1. **Compare row counts across consecutive runs** — a step-change is the signal. If runs before and after show different counts, pull logs for both and compare per-category ok/fail.
2. **Check the raw HTML from the fetch source** — SSH to the VM and run: `curl -sS -m 30 -H "User-Agent: Mozilla/5.0 ..." -H "Accept-Encoding: identity" "https://www.amazon.in/gp/bestsellers/electronics/3274516031" > /tmp/amz.html && grep -c "data-asin" /tmp/amz.html`. Before Sept 18 this returned 30; after it returns 0.
3. **Check for CAPTCHA/block signatures** — grep for `captcha`, `robot`, `verify you are not a robot`, `ap/signin` in the response. On Sept 18 the page title was `<title>Amazon.in Bestsellers: The most popular items in undefined</title>` — the `"undefined"` category name is a tell that Amazon returned a JS-rendering shell, not the full SSR page.
4. **Compare with local browser tool** — if the same URL works via the browser tool (chrome/selenium) but not via curl from the VM, it's a bot-detection or JS-rendering block, not a network outage.

## Why the tunnel didn't fix it

The phone tunnel provides a residential IP, which defeats IP-based blocks. But it does NOT provide JavaScript rendering — the tunnel is a SOCKS proxy at the TCP level. Amazon's change is rendering-based, not IP-based. A residential IP still sees the same empty HTML when it hits the JS-rendered endpoint.

## What fixing this requires

Plain HTTP scraping (`requests` / `curl`) cannot read these pages anymore. Options:

- **A. Use Maxun** — already deployed on the VM at port 9222 with a live worker. Maxun is a headless-browser automation platform. It can browse these pages, but extracting structured ASIN data from its output requires either (a) writing a Maxun recording that exports structured data, or (b) using its API to trigger a scrape and then pulling results. This is the path of least resistance since Maxun is already running.
- **B. Spin up Playwright/Trifle** on the VM — install a headless Chromium instance that can execute JS and then parse the resulting DOM. More infrastructure work but more control.
- **C. Accept the ~3,500-row floor** — the 55% coverage is still useful; skip the fix unless the missing 45% matters for a specific use case.

## Verbatim evidence (for future reference)

```
ssh -i <key> ubuntu@140.245.239.162 '
  curl -sS -m 30 -H "User-Agent: Mozilla/5.0 ..." \
       -H "Accept-Encoding: identity" \
       "https://www.amazon.in/gp/bestsellers/electronics/3274516031" \
    > /tmp/amz.html
  echo "Size: $(wc -c < /tmp/amz.html)"
  echo "ASIN matches: $(grep -c "data-asin" /tmp/amz.html)"
  grep -oE "<title>[^<]+</title>" /tmp/amz.html
'
```

Expected pre-Sept-18: `Size: ~2600000`, `ASIN matches: 30`, title contains the actual category name.
Post-Sept-18: `Size: ~320000`, `ASIN matches: 0`, title contains `undefined`.
