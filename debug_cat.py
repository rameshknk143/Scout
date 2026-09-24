#!/usr/bin/env python3
"""Debug: what's on the electronics bestseller page?"""
import re
from playwright.sync_api import sync_playwright

URL = "https://www.amazon.in/gp/bestsellers/electronics"
EXE = "/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EXE, headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
    ctx = browser.new_context(locale="en-IN", timezone_id="Asia/Kolkata", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = ctx.new_page()
    page.goto(URL, timeout=60000)
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    
    # Check for zg_browseRoot
    zg_html = page.evaluate("""() => {
        const el = document.querySelector("#zg_browseRoot");
        return el ? el.outerHTML.slice(0, 3000) : "NOT FOUND";
    }""")
    print("=== zg_browseRoot ===")
    print(zg_html[:2000])
    
    # Check all links in zg_browseRoot
    links = page.evaluate("""() => {
        const root = document.querySelector("#zg_browseRoot");
        if (!root) return [];
        const out = [];
        root.querySelectorAll("a").forEach(a => {
            const href = a.href;
            const text = a.innerText.trim();
            if (text && href) out.push([text, href]);
        });
        return out;
    }""")
    print(f"\n=== Links in zg_browseRoot: {len(links)} ===")
    for text, href in links[:20]:
        print(f"  {text[:40]:40s} -> {href}")
    
    browser.close()