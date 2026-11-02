"""Реальные картинки из интернета для монтажа (Wikimedia Commons) + вырезание фона.

Запуск — в GitHub Actions через call-brand-images.yml, jobs-файл с "mode": "web_images"
(у песочницы чата нет прямого доступа в интернет).

{
 "mode": "web_images",
 "set": "hist01",                                  # папка scratch/img/web/<set>/
 "search": [{"name": "onfim", "q": "Onfim birch bark", "n": 8}],   # поиск по Commons
 "files":  [{"name": "onfim_200", "title": "File:Onfim 200.jpg", "cutout": true}],  # точные файлы
 "cutout": [{"name": "rider", "src": "scratch/img/web/hist01/onfim_1.jpg"}]          # вырезать уже скачанное
}

Каждая картинка сохраняется как <name>[_i].jpg (ширина до 1600), вырезанная — <name>[_i]_cut.png
(прозрачный фон, rembg). В index.json — название файла, автор, лицензия и ссылка на источник:
берём только то, что можно использовать (общественное достояние / CC), лицензия пишется рядом.
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "iiavatar-montage/1.0 (https://iiavatar.ru; educational reels)"
OUT = "scratch/img/web"
OK_LICENSES = ("public domain", "pd", "cc0", "cc by", "cc-by", "cc by-sa", "cc-by-sa", "no restrictions")


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def info(titles):
    data = json.loads(get(API, {"action": "query", "format": "json", "prop": "imageinfo",
                                "titles": "|".join(titles), "iiprop": "url|extmetadata|size|mime",
                                "iiurlwidth": 1600}))
    out = []
    for p in data.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii:
            continue
        md = ii.get("extmetadata", {})
        val = lambda k: (md.get(k, {}).get("value") or "").strip()
        out.append({"title": p["title"], "url": ii.get("thumburl") or ii.get("url"),
                    "page": ii.get("descriptionurl"), "w": ii.get("width"), "h": ii.get("height"),
                    "mime": ii.get("mime"), "license": val("LicenseShortName"),
                    "artist": val("Artist")[:200], "desc": val("ImageDescription")[:300]})
    return out


def search(q, n):
    data = json.loads(get(API, {"action": "query", "format": "json", "list": "search", "srsearch": q,
                                "srnamespace": 6, "srlimit": min(50, n * 3)}))
    titles = [s["title"] for s in data.get("query", {}).get("search", [])
              if s["title"].lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"))]
    res = info(titles[:n * 2]) if titles else []
    return [r for r in res if licence_ok(r["license"])][:n]


def licence_ok(lic):
    l = (lic or "").lower()
    return any(k in l for k in OK_LICENSES) and "nc" not in l.split() and "-nc" not in l


def save(item, path):
    raw = get(item["url"])
    tmp = path + ".src"
    open(tmp, "wb").write(raw)
    from PIL import Image
    im = Image.open(tmp).convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)))
    im.save(path, quality=92)
    os.remove(tmp)


_rembg = None


def cutout(src, dst):
    global _rembg
    if _rembg is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rembg[cpu]", "pillow"], check=True)
        import importlib, site
        for d in [site.getusersitepackages()] + site.getsitepackages():
            if d not in sys.path:
                sys.path.append(d)
        importlib.invalidate_caches()
        from rembg import new_session, remove
        _rembg = (new_session("isnet-general-use"), remove)
    from PIL import Image
    sess, remove = _rembg
    im = Image.open(src).convert("RGB")
    remove(im, session=sess).save(dst)


def run(spec, only):
    d = f"{OUT}/{spec['set']}"
    os.makedirs(d, exist_ok=True)
    idx_path = f"{d}/index.json"
    index = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for s in spec.get("search", []):
        if only and s["name"] not in only:
            continue
        try:
            found = search(s["q"], s.get("n", 6))
        except Exception as e:
            print(f"{s['name']}: search failed {e}", flush=True)
            continue
        for i, it in enumerate(found, 1):
            key = f"{s['name']}_{i}"
            try:
                save(it, f"{d}/{key}.jpg")
                index[key] = it
                if s.get("cutout"):
                    cutout(f"{d}/{key}.jpg", f"{d}/{key}_cut.png")
                print(f"{key}: {it['title']} [{it['license']}]", flush=True)
            except Exception as e:
                print(f"{key}: failed {e}", flush=True)
    files = [f for f in spec.get("files", []) if not only or f["name"] in only]
    if files:
        got = {r["title"].replace("_", " "): r for r in info([f["title"] for f in files])}
        for f in files:
            it = got.get(f["title"].replace("_", " "))
            if not it:
                print(f"{f['name']}: not found {f['title']}", flush=True)
                continue
            if not licence_ok(it["license"]):
                print(f"{f['name']}: skipped, license {it['license']!r}", flush=True)
                continue
            try:
                save(it, f"{d}/{f['name']}.jpg")
                index[f["name"]] = it
                if f.get("cutout"):
                    cutout(f"{d}/{f['name']}.jpg", f"{d}/{f['name']}_cut.png")
                print(f"{f['name']}: ok [{it['license']}]", flush=True)
            except Exception as e:
                print(f"{f['name']}: failed {e}", flush=True)
    for c in spec.get("cutout", []):
        if only and c["name"] not in only:
            continue
        try:
            cutout(c["src"], f"{d}/{c['name']}_cut.png")
            print(f"{c['name']}: cut ok", flush=True)
        except Exception as e:
            print(f"{c['name']}: cut failed {e}", flush=True)
    json.dump(index, open(idx_path, "w"), ensure_ascii=False, indent=1)
