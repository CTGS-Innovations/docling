#!/usr/bin/env python3
import os
import re
import asyncio
import requests
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

BASE_DIR = Path("/home/corey/projects/docling/cli/data_web")

CATEGORIES = {
    "html": [
        "https://www.bbc.com",
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://www.gnu.org/licenses/gpl-3.0.en.html",
    ],
    "js": [
        "https://twitter.com",
        "https://www.reddit.com",
        "https://www.netflix.com",
    ],
    "hybrid": [
        "https://medium.com",
        "https://www.shopify.com/blog",
    ],
    "amp": [
        "https://www.theguardian.com/amp",
        "https://www.cnn.com/ampstories/world",
    ],
    "infinite_scroll": [
        "https://news.ycombinator.com",
        "https://www.instagram.com",
    ],
    "wasm": [
        "https://editor.construct.net",
        "https://play.figma.com",
    ],
}

def safe_filename(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc
    # clean any unwanted chars
    domain = re.sub(r"[^a-zA-Z0-9.-]", "_", domain)
    return domain + ".html"

def save_raw(content: str, path: Path):
    path.write_text(content, encoding="utf-8")

def download_html(url: str, out_dir: Path):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out_file = out_dir / safe_filename(url)
        save_raw(r.text, out_file)
        print(f"[HTML] Saved {url} -> {out_file}")
    except Exception as e:
        print(f"[ERROR] Failed {url}: {e}")

async def download_js(url: str, out_dir: Path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=20000)
            content = await page.content()
            out_file = out_dir / safe_filename(url)
            save_raw(content, out_file)
            print(f"[JS] Saved {url} -> {out_file}")
        except Exception as e:
            print(f"[ERROR] JS {url}: {e}")
        finally:
            await browser.close()

async def main():
    for cat, urls in CATEGORIES.items():
        out_dir = BASE_DIR / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        for url in urls:
            if cat == "js" or cat in ["hybrid", "infinite_scroll", "wasm"]:
                await download_js(url, out_dir)
            else:
                download_html(url, out_dir)

if __name__ == "__main__":
    asyncio.run(main())

