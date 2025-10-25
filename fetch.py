import os
import asyncio
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright

CHANNELS_FILE = "channels.json"
JSON_FILE = "playlist.json"
M3U_FILE = "playlist.m3u"

# মূল পেজের URL (Environment variable বা সরাসরি সেট করতে পারো)
BASE_URL = os.getenv("STREAM_URL", "https://example.com/")

# ডিফল্ট referer/origin
DEFAULT_REFERER = "https://profamouslife.com/"
DEFAULT_ORIGIN = "https://profamouslife.com"


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
            "link": m3u8_url,
            "referer": DEFAULT_REFERER,
            "origin": DEFAULT_ORIGIN
        }


async def main():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)

    tasks = [fetch_channel(ch) for ch in channels]
    result = await asyncio.gather(*tasks)

    # 🎯 JSON save (new structure)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # 🎯 M3U save (new format)
    m3u_content = "#EXTM3U\n"
    for ch in result:
        if ch.get("link"):
            m3u_content += (
                f'#EXTINF:-1 tvg-logo="{ch["logo"]}",{ch["name"]}\n'
                f'#EXTVLCOPT:http-referrer={ch["referer"]}\n'
                f'#EXTVLCOPT:http-origin={ch["origin"]}\n'
                f'{ch["link"]}\n'
            )

    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("✅ JSON and M3U updated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
