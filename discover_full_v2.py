#!/usr/bin/env python3
"""
Full sub-category discovery: visits each top-level category page,
extracts sub-category links from the left sidebar (zg-left-col > ul._p13n-zg-nav-tree-all_),
recurses deeper. Outputs a complete browse-node tree.
"""
import json, re, time, sys
from playwright.sync_api import sync_playwright

ROOT = "https://www.amazon.in/gp/bestsellers"
OUT = "/home/ubuntu/browse_tree_full.json"
EXE = "/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"

# Our 31 known top-level category slugs (from collector.py)
TOP_SLUGS = [
    "electronics", "kitchen", "beauty", "sports", "toys", "office",
    "pet-supplies", "automotive", "garden", "baby", "watches",
    "apparel", "boost", "amazon-renewed", "mobile-apps", "luggage",
    "books", "computers", "gift-cards", "grocery", "hpc",
    "home-improvement", "industrial", "jewelry", "digital-text",
    "dvd", "music", "musical-instruments", "shoes", "software", "videogames"
]

NODE_RE = re.compile(r"[?&]node=(\d+)")
SLUG_RE = re.compile(r"/gp/bestsellers/([^/?]+)(?:/(\d+))?")

seen_nodes = set()
tree = {"name": "root", "slug": "", "node": None, "children": []}

def extract_subcats(page):
    """Extract sub-category links from the left sidebar using the correct selector."""
    links = page.evaluate("""() => {
        const out = [];
        // Find the navigation tree in zg-left-col
        const navTree = document.querySelector("#zg-left-col ul._p13n-zg-nav-tree-all_");
        if (!navTree) return out;
        navTree.querySelectorAll("li._p13n-zg-nav-tree-all_style_zg-browse-item__1rdKf a").forEach(a => {
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

def crawl_category_page(slug, parent_node=None, depth=0, max_depth=2):
    """Visit a category page (by slug), extract its sub-categories."""
    if depth > max_depth:
        return []
    url = f"https://www.amazon.in/gp/bestsellers/{slug}"
    indent = "  " * depth
    print(f"{indent}-> {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EXE, headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            locale="en-IN", timezone_id="Asia/Kolkata",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"    ERROR loading {url}: {e}")
            browser.close()
            return []
        subcats = extract_subcats(page)
        browser.close()
    
    children = []
    for name, link in subcats:
        nid = node_id_from_url(link)
        if not nid or nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        sub_slug = slug_from_url(link)
        subindent = "  " * (depth + 1)
        print(f"{subindent}ok {name}  node={nid}  slug={sub_slug}")
        child = {
            "name": name,
            "slug": sub_slug,
            "node": nid,
            "url": link,
            "children": crawl_category_page(sub_slug, nid, depth+1, max_depth)
        }
        children.append(child)
        time.sleep(1.5)
    return children

print(f"Starting full sub-category discovery from {len(TOP_SLUGS)} top-level categories...")
for slug in TOP_SLUGS:
    child = {
        "name": slug.replace("-", " ").title(),
        "slug": slug,
        "node": None,
        "url": f"https://www.amazon.in/gp/bestsellers/{slug}",
        "children": crawl_category_page(slug, None, max_depth=2)
    }
    tree["children"].append(child)
    time.sleep(2)

with open(OUT, "w") as f:
    json.dump(tree, f, indent=2)
print(f"\nDone. {len(seen_nodes)} unique sub-category nodes written to {OUT}")