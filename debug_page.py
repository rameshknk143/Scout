#!/usr/bin/env python3
"""Debug: what does the bestsellers root page actually contain?"""
import re
from playwright.sync_api import sync_playwright

ROOT = "https://www.amazon.in/gp/bestsellers"
EXE = "/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"

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
    page.goto(ROOT, timeout=60000)
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    # Check what category links exist
    links = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href;
            const text = a.innerText.trim();
            if (text && href && href.includes("bestsellers")) {
                out.push([text, href]);
            }
        });
        return out;
    }""")
    print(f"Total bestseller links: {len(links)}")
    for name, url in links[:30]:
        print(f"  {name[:50]:50s} -> {url}")

    # Also check for the left nav structure
    nav_html = page.evaluate("""() => {
        const nav = document.querySelector("#zg_browseRoot") || document.querySelector(".zg_browseRoot") || document.querySelector("[role=navigation]") || document.body;
        return nav.outerHTML.slice(0, 5000);
    }""")
    print("\n--- nav snippet ---")
    print(nav_html[:2000])

    browser.close()