#!/usr/bin/env python3
"""Debug: extract the exact selector pattern from the electronics page"""
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
    
    # Find the actual structure of the nav tree
    result = page.evaluate("""() => {
        const out = [];
        const leftCol = document.querySelector("#zg-left-col");
        if (!leftCol) return out;
        
        // Find all ul elements in left col
        const uls = leftCol.querySelectorAll("ul");
        uls.forEach((ul, i) => {
            const classes = ul.className;
            if (classes.includes("zg-nav-tree") || classes.includes("nav-tree")) {
                out.push({type: "ul", index: i, class: classes, html: ul.outerHTML.slice(0, 500)});
            }
        });
        
        // Find all li elements with browse items
        const lis = leftCol.querySelectorAll("li");
        lis.forEach((li, i) => {
            const classes = li.className;
            if (classes.includes("browse-item") || classes.includes("zg-browse")) {
                const a = li.querySelector("a");
                out.push({type: "li", index: i, class: classes, text: li.innerText.slice(0, 80), href: a ? a.href : "no-link"});
            }
        });
        return out;
    }""")
    
    print(f"Found {len(result)} relevant elements:")
    for r in result[:30]:
        print(f"  {r['type']} #{r['index']}: class={r.get('class', '')[:60]}")
        if 'text' in r:
            print(f"    text: {r['text']}")
        if 'href' in r:
            print(f"    href: {r['href']}")
    
    browser.close()