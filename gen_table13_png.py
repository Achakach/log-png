"""Generate Table 13 test PNG with error + username combined tag."""
import asyncio
from playwright.async_api import async_playwright
import os
import shutil

HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background-color: transparent; margin: 0; padding: 20px; }
        #capture-area { background-color: #000000; padding: 20px; width: 1000px; 
                        font-family: 'Fira Code', 'Courier New', monospace;
                        font-size: 12px; line-height: 1.3; color: #ffffff; }
        .prompt { color: #ffffff; }
        .command { color: #ffffff; }
        .output { color: #ffffff; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div id="capture-area">
        <span class="prompt">&lt;TUC-TEST01&gt;</span> <span class="command">display current-configutation</span>
        <div class="output">Error: Do not have permission to run this command.</div>
        <span class="prompt">&lt;TUC-TEST01&gt;</span> <span class="command">username xxuser</span>
        <div class="output">This command will set the current user name.</div>
    </div>
</body>
</html>
"""

async def generate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1200, 'height': 900})
        await page.set_content(HTML)
        element = await page.wait_for_selector('#capture-area')
        
        base = "screenshots/TUC-TEST01 display current-configutation username xxuser [error].png"
        await element.screenshot(path=base, type='png')
        print(f"Generated: {base}")
        await browser.close()
    
    # Copy for TUC-TEST02 and TUC-TEST03
    for dev in ['TUC-TEST02', 'TUC-TEST03']:
        dst = f"screenshots/{dev} display current-configutation username xxuser [error].png"
        shutil.copy2(base, dst)
        print(f"Copied to: {dst}")

if __name__ == "__main__":
    asyncio.run(generate())
