#!/usr/bin/env python3
"""
Discover all Amazon.in bestseller browse-node IDs.
Starts from root bestsellers page, follows every category link,
recurses into sub-categories, extracts node IDs from URLs.
"""
import json, re, time, sys
from playwright.sync_api import sync_playwright

ROOT = "https://www.amazon.in/gp/bestsellers"
OUT = "/home/ubuntu/browse_tree.json"

NODE_RE = re.compile(r"[?&]node=(\d+)")
SLUG_RE = re.compile(r"/gp/bestsellers/([^/?]+)(?:/(\d+))?")

seen_nodes = set()
tree = {"name": "root", "slug": "", "node": None, "children": []}

def extract_links(page):
    """Return list of (name, url) for all category links on current page."""
    links = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('a[href*="/gp/bestsellers/"]').forEach(a => {
            const href = a.href;
            const text = a.innerText.trim();
            if (text && href && !href.includes("ref=")) {
                out.push([text, href]);
            }
        });
        return out;
    }""")
    uniq = {}
    for name, url in links:
        if url not in uniq:
            uniq[url] = name
    return [(n, u) for u, n in uniq.items()]

def node_id_from_url(url):
    m = NODE_RE.search(url)
    if m: return m.group(1)
    m2 = SLUG_RE.search(url)
    if m2 and m2.group(2): return m2.group(2)
    return None

def slug_from_url(url):
    m = SLUG_RE.search(url)
    return m.group(1) if m else ""

def crawl(url, parent_node, depth=0, max_depth=4):
    if depth > max_depth:
        return []
    indent = "  " * depth
    print(f"{indent}-> {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
            headless=True, args=["--no-sandbox","--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(locale="en-IN", timezone_id="Asia/Kolkata",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"    ERROR loading {url}: {e}")
            browser.close()
            return []
        links = extract_links(page)
        browser.close()
    children = []
    for name, link in links:
        nid = node_id_from_url(link)
        if not nid or nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        slug = slug_from_url(link)
        subindent = "  " * (depth + 1)
        print(f"{subindent}ok {name}  node={nid}  slug={slug}")
        child = {
            "name": name,
            "slug": slug,
            "node": nid,
            "url": link,
            "children": crawl(link, nid, depth+1, max_depth)
        }
        children.append(child)
        time.sleep(1.5)
    return children

print(f"Starting discovery from {ROOT}")
tree["children"] = crawl(ROOT, None, max_depth=3)
with open(OUT, "w") as f:
    json.dump(tree, f, indent=2)
print(f"\nDone. {len(seen_nodes)} unique nodes written to {OUT}")