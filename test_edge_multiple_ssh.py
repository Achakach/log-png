"""Test edge case: Multiple SSH sessions in one cell."""
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
        <!-- First SSH session -->
        <span class="prompt">&lt;TUC-TEST01&gt;</span> <span class="command">stelnet 10.0.0.1</span>
        <div class="output">Trying 10.0.0.1 ...</div>
        <div class="output">Connected to 10.0.0.1 ...</div>
        <div class="output">Please input the username: admin</div>
        <div class="output">Please input the password: ********</div>
        <span class="prompt">&lt;Remote-Device&gt;</span> <span class="command">display current-configuration</span>
        <div class="output">... configuration output ...</div>
        <!-- Second SSH session -->
        <span class="prompt">&lt;TUC-TEST01&gt;</span> <span class="command">stelnet 10.0.0.2</span>
        <div class="output">Trying 10.0.0.2 ...</div>
        <div class="output">Connected to 10.0.0.2 ...</div>
        <div class="output">Please input the username: admin2</div>
        <div class="output">Please input the password: ********</div>
        <span class="prompt">&lt;Remote-Device2&gt;</span> <span class="command">display device</span>
        <div class="output">... device info ...</div>
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
        
        base = "screenshots/TUC-TEST01 display current-configuration.png"
        await element.screenshot(path=base, type='png')
        print(f"Generated: {base}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(generate())
