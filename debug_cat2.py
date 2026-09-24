#!/usr/bin/env python3
"""Debug: full page structure of electronics bestseller page"""
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
    
    # Get all elements with "zg" in id or class
    zg_elements = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[id*="zg"], [class*="zg"]').forEach(el => {
            out.push({
                tag: el.tagName,
                id: el.id,
                class: el.className,
                text: el.innerText.slice(0, 100)
            });
        });
        return out;
    }""")
    print(f"=== ZG elements found: {len(zg_elements)} ===")
    for el in zg_elements[:20]:
        print(f"  {el['tag']:10s} id={el['id'] or '(none)'} class={str(el['class'])[:60]} text={el['text'][:50]}")
    
    # Also check sidebar-like structures
    sidebar = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('aside, nav, [role="navigation"], .a-column, .a-span, [id*="sidebar"], [class*="sidebar"]').forEach(el => {
            out.push({
                tag: el.tagName,
                id: el.id,
                class: el.className,
                children: el.querySelectorAll("a").length
            });
        });
        return out;
    }""")
    print(f"\n=== Sidebar-like elements: {len(sidebar)} ===")
    for el in sidebar[:10]:
        print(f"  {el['tag']:10s} id={el['id'] or '(none)'} class={str(el['class'])[:60]} links={el['children']}")
    
    browser.close()