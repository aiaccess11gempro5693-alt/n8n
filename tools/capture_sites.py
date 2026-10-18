"""Снимки сайтов конкурентов (запускается в GitHub Actions через
call-brand-images.yml, jobs-файл с "mode": "site_capture").

Для каждого сайта: первый экран 1440x900, вся страница (JPEG, обрезано по
высоте), мобильный первый экран, видимый текст; плюс до 2 страниц цен/услуг,
найденных по ссылкам. Результат — scratch/img/competitors/<name>/.
"""
import json
import os
import re
import subprocess
import sys

OUT = "scratch/img/competitors"
PRICE_RE = re.compile(r"цен|прайс|стоимост|тариф|price|pricing|услуг", re.I)
MAX_H = 12000


def ensure_playwright():
    try:
        import playwright  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright", "pillow"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], check=True)


def shoot(page, url, d, tag, log):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        # прокрутка — чтобы подгрузились ленивые блоки
        h = page.evaluate("document.body.scrollHeight")
        for y in range(0, min(h, MAX_H), 800):
            page.evaluate(f"window.scrollTo(0,{y})"); page.wait_for_timeout(150)
        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(800)
        page.screenshot(path=f"{d}/{tag}-screen.jpg", type="jpeg", quality=80)
        page.screenshot(path=f"{d}/{tag}-full.png", full_page=True)
        from PIL import Image
        im = Image.open(f"{d}/{tag}-full.png").convert("RGB")
        if im.height > MAX_H:
            im = im.crop((0, 0, im.width, MAX_H))
        im.save(f"{d}/{tag}-full.jpg", quality=70); os.remove(f"{d}/{tag}-full.png")
        text = page.evaluate("document.body.innerText")
        meta = page.evaluate("""() => ({title: document.title,
            description: (document.querySelector('meta[name=description]')||{}).content||''})""")
        with open(f"{d}/{tag}.txt", "w", encoding="utf-8") as f:
            f.write(f"URL: {page.url}\nTITLE: {meta['title']}\nDESCRIPTION: {meta['description']}\n\n{text}")
        links = page.evaluate("""() => [...document.querySelectorAll('a[href]')].map(a => [a.href, (a.innerText||'').trim()])""")
        log.append({"tag": tag, "url": page.url, "ok": True})
        return links
    except Exception as e:
        log.append({"tag": tag, "url": url, "ok": False, "error": str(e)[:300]})
        return []


def run(spec, only):
    ensure_playwright()
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        for site in spec["sites"]:
            if only and site["name"] not in only:
                continue
            d = f"{OUT}/{site['name']}"; os.makedirs(d, exist_ok=True)
            log = []
            ctx = br.new_context(viewport={"width": 1440, "height": 900}, locale="ru-RU")
            page = ctx.new_page()
            links = shoot(page, site["url"], d, "home", log)
            host = re.sub(r"^https?://", "", site["url"]).split("/")[0]
            extra = list(site.get("extra", []))
            for href, txt in links:
                if len(extra) >= 2 + len(site.get("extra", [])):
                    break
                if host in href and href.split("#")[0] != site["url"].split("#")[0] and PRICE_RE.search(href + " " + txt) and href not in extra:
                    extra.append(href)
            for i, u in enumerate(extra):
                shoot(page, u, d, f"page{i+1}", log)
            ctx.close()
            m = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ru-RU", is_mobile=True)
            mp = m.new_page()
            try:
                mp.goto(site["url"], wait_until="domcontentloaded", timeout=45000); mp.wait_for_timeout(4000)
                mp.screenshot(path=f"{d}/mobile-screen.jpg", type="jpeg", quality=80)
            except Exception as e:
                log.append({"tag": "mobile", "ok": False, "error": str(e)[:200]})
            m.close()
            json.dump(log, open(f"{d}/log.json", "w"), ensure_ascii=False, indent=1)
            print(site["name"], json.dumps(log, ensure_ascii=False), flush=True)
        br.close()
