import os
import asyncio
import json
import requests
from playwright.async_api import async_playwright

JSON_FILE = "playlist.json"

# 🔒 Secrets (from GitHub Actions)
BASE_URL = os.getenv("STREAM_URL", "https://example.com/")
CHANNELS_URL = os.getenv("CHANNELS_JSON", "")


async def fetch_channel(ch):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        m3u8_url = None

        async def log_response(response):
            nonlocal m3u8_url
            url = response.url
            if ".m3u8" in url and "md5=" in url and "expires=" in url:
                m3u8_url = url

        page.on("response", log_response)
        await page.goto(f"{BASE_URL}{ch['code']}.php", timeout=60000)

        try:
            await page.wait_for_selector("video", timeout=5000)
            await page.evaluate("() => { const v=document.querySelector('video'); if(v)v.play(); }")
        except:
            pass

        await page.wait_for_timeout(5000)
        await browser.close()

        return {
            "name": ch["name"],
            "id": ch["code"],
            "logo": ch["tvg-logo"],
            "link": m3u8_url
        }


async def main():
    # 🌐 Fetch channel list directly from remote JSON link
    try:
        response = requests.get(CHANNELS_URL)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch or parse channels JSON: {e}")
        return

    tasks = [fetch_channel(ch) for ch in channels]
    result = await asyncio.gather(*tasks)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ playlist.json updated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
