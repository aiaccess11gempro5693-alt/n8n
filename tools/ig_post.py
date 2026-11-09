"""Публикация в Instagram через официальный API с входом через Instagram (мост .github/workflows/ig-post.yml).

python3 tools/ig_post.py check                    — проверить ключ и аккаунт, ничего не публикуя
python3 tools/ig_post.py post docs/landing/insta/posts/001.json
python3 tools/ig_post.py stats                    — все публикации аккаунта со статистикой (scratch/ig/stats.result.json)

Пост (JSON): {"type": "reel", "video": "путь.mp4", "caption": "...", "cover_url": "https://...jpg" или "thumb_offset_ms": 1500 (кадр обложки, необязательно),
              "share_to_feed": true}
          или {"type": "image", "image_url": "https://...jpg", "caption": "..."}
          или {"type": "carousel", "image_urls": ["https://...", ...], "caption": "..."}
          или {"type": "story", "image_url": "https://...jpg"} / {"type": "story", "video_url": "https://...mp4"}
Instagram забирает картинки, обложки и видео по публичной ссылке ("video_url" — ролик на сайте).
Ключ — секрет IG_TOKEN (маркер из приложения Meta, живёт 60 дней). Результат — scratch/ig/<имя>.result.json.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

V = "v23.0"
API = f"https://graph.instagram.com/{V}/"
TOKEN = os.environ.get("IG_TOKEN", "").strip()


def req(method, path, data=None, headers=None, raw=None):
    url = path if path.startswith("http") else API + path
    params = dict(data or {})
    if raw is None:
        params["access_token"] = TOKEN
        body = urllib.parse.urlencode(params).encode()
        if method == "GET":
            url += ("&" if "?" in url else "?") + body.decode()
            body = None
    else:
        body = raw
    r = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{path.split('?')[0]}: {e.code} {e.read().decode()[:500]}")


def me():
    return req("GET", "me", {"fields": "user_id,username,name,account_type,media_count"})


def wait_ready(container):
    for _ in range(60):
        st = req("GET", container, {"fields": "status_code,status"})
        if st.get("status_code") == "FINISHED":
            return st
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"контейнер {container}: {st}")
        time.sleep(10)
    raise RuntimeError(f"контейнер {container} не обработался за 10 минут")


def post(path):
    data = json.load(open(path))
    if isinstance(data, list):   # пачка — по порядку (истории для «Актуального» и т.п.)
        out = []
        for it in data:
            try:
                out.append(post_item(it))
            except Exception as e:
                out.append({"error": str(e), "item": it.get("name")})
                break
        return out
    return post_item(data)


def post_item(item):
    uid = me()["user_id"]
    kind = item.get("type", "reel")
    caption = item.get("caption", "")
    if kind == "reel":
        params = {"media_type": "REELS", "caption": caption,
                  "share_to_feed": str(item.get("share_to_feed", True)).lower()}
        if item.get("cover_url"):
            params["cover_url"] = item["cover_url"]
        elif item.get("thumb_offset_ms") is not None:
            params["thumb_offset"] = str(item["thumb_offset_ms"])
        if item.get("video_url"):
            # API с входом через Instagram принимает видео по публичной ссылке
            params["video_url"] = item["video_url"]
            c = req("POST", f"{uid}/media", params)
            up = None
        else:
            params["upload_type"] = "resumable"
            c = req("POST", f"{uid}/media", params)
            size = os.path.getsize(item["video"])
            with open(item["video"], "rb") as f:
                up = req("POST", c["uri"], raw=f.read(), headers={
                    "Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
        container = c["id"]
    elif kind == "story":
        params = {"media_type": "STORIES"}
        if item.get("video_url"):
            params["video_url"] = item["video_url"]
        else:
            params["image_url"] = item["image_url"]
        container = req("POST", f"{uid}/media", params)["id"]
        up = None
    elif kind == "image":
        container = req("POST", f"{uid}/media", {"image_url": item["image_url"], "caption": caption})["id"]
        up = None
    elif kind == "carousel":
        children = [req("POST", f"{uid}/media", {"image_url": u, "is_carousel_item": "true"})["id"]
                    for u in item["image_urls"]]
        for ch in children:
            wait_ready(ch)
        container = req("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                                 "caption": caption})["id"]
        up = None
    else:
        raise ValueError(f"неизвестный type: {kind}")
    wait_ready(container)
    pub = req("POST", f"{uid}/media_publish", {"creation_id": container})
    link = req("GET", pub["id"], {"fields": "permalink"}).get("permalink")
    return {"name": item.get("name"), "container": container, "upload": up, "media_id": pub["id"], "permalink": link}


def check():
    if not TOKEN:
        return {"error": "Нет секрета IG_TOKEN"}
    out = {}
    try:
        out["account"] = me()
    except Exception as e:
        out["account_error"] = str(e)
        return out
    try:
        out["publishing_limit"] = req("GET", f"{out['account']['user_id']}/content_publishing_limit",
                                      {"fields": "quota_usage,config"})
    except Exception as e:
        out["publishing_limit_error"] = str(e)
    return out


REEL_METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
                "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]
POST_METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions"]


def insights(mid, metrics):
    """Метрики по одной: если какая-то недоступна для этого вида публикации, остальные не теряются."""
    out = {}
    for m in metrics:
        try:
            r = req("GET", f"{mid}/insights", {"metric": m})
            vals = r.get("data", [{}])[0].get("values", [{}])
            out[m] = vals[0].get("value") if vals else r.get("data", [{}])[0].get("total_value", {}).get("value")
        except Exception as e:
            out[m] = None
            out.setdefault("_errors", {})[m] = str(e)[:160]
    return out


def stats():
    acc = me()
    items, url = [], f"{acc['user_id']}/media"
    params = {"fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count",
              "limit": 50}
    while url:
        r = req("GET", url, params)
        items += r.get("data", [])
        url = r.get("paging", {}).get("next")
        params = None if url else params
    for it in items:
        reel = it.get("media_product_type") == "REELS"
        it["insights"] = insights(it["id"], REEL_METRICS if reel else POST_METRICS)
        it["caption"] = (it.get("caption") or "")[:300]
    try:
        acc_ins = req("GET", f"{acc['user_id']}/insights",
                      {"metric": "follower_count,reach", "period": "day"})
    except Exception as e:
        acc_ins = {"error": str(e)[:300]}
    return {"account": acc, "account_insights": acc_ins, "media": items}


if __name__ == "__main__":
    mode = sys.argv[1]
    os.makedirs("scratch/ig", exist_ok=True)
    name = mode if mode in ("check", "stats") else os.path.splitext(os.path.basename(sys.argv[2]))[0]
    try:
        result = check() if mode == "check" else stats() if mode == "stats" else post(sys.argv[2])
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, ensure_ascii=False, indent=1))
    json.dump(result, open(f"scratch/ig/{name}.result.json", "w"), ensure_ascii=False, indent=1)
