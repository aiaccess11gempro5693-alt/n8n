"""Публикация в сообщество ВК через API (запуск — мост .github/workflows/vk-post.yml).

python3 tools/vk_post.py check                     — проверить ключи и права, ничего не публикуя
python3 tools/vk_post.py post docs/landing/vk/posts/001.json

Пост (JSON): {"text": "...", "images": ["путь.jpg"], "videos": [{"path": "x.mp4", "title": "...", "clip": true}],
              "publish_date": "2026-10-23T10:00:00+03:00" (необязательно — отложенный пост),
              "pin": false}
Ключи из окружения: VK_GROUP_TOKEN (ключ сообщества) и ключ администратора (нужен для видео):
VK_USER_TOKEN напрямую или VK_BRIDGE_KEY — тогда свежий ключ берётся с сайта
(VK_SITE_URL, по умолчанию https://iiavatar.ru, маршрут /api/vk?token=1; вход — /api/vk?login=1).
Результат пишется в scratch/vk/<имя>.result.json.
"""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.error
import urllib.request
import uuid

API = "https://api.vk.com/method/"
V = "5.199"
GROUP = os.environ.get("VK_GROUP_TOKEN", "").strip()
USER = os.environ.get("VK_USER_TOKEN", "").strip()
USER_ERROR = ""


def site_token():
    key = os.environ.get("VK_BRIDGE_KEY", "").strip()
    if not key:
        return "", ""
    site = os.environ.get("VK_SITE_URL", "").strip() or "https://iiavatar.ru"
    req = urllib.request.Request(site.rstrip("/") + "/api/vk?token=1", headers={"x-vk-bridge-key": key, "User-Agent": "Mozilla/5.0 (iiavatar-bridge)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["access_token"], ""
    except urllib.error.HTTPError as e:
        return "", f"сайт ответил {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return "", f"сайт недоступен: {e}"


if not USER:
    USER, USER_ERROR = site_token()


def call(method, token, **params):
    params.update(access_token=token, v=V)
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(API + method, data=data), timeout=120) as r:
        resp = json.loads(r.read().decode())
    if "error" in resp:
        e = resp["error"]
        raise RuntimeError(f"{method}: {e.get('error_code')} {e.get('error_msg')}")
    return resp["response"]


def upload(url, field, path):
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
            f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
    body += data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())


def group_id():
    if os.environ.get("VK_GROUP_ID"):
        return int(os.environ["VK_GROUP_ID"])
    r = call("groups.getById", GROUP)
    groups = r["groups"] if isinstance(r, dict) else r
    return int(groups[0]["id"])


def media_token():
    return USER or GROUP


def upload_photo(gid, path):
    if USER:
        server = call("photos.getWallUploadServer", USER, group_id=gid)["upload_url"]
        up = upload(server, "photo", path)
        saved = call("photos.saveWallPhoto", USER, group_id=gid, photo=up["photo"], server=up["server"],
                     hash=up["hash"])[0]
    else:
        # С ключом сообщества стена недоступна — грузим через сервер сообщений сообщества.
        server = call("photos.getMessagesUploadServer", GROUP, peer_id=0)["upload_url"]
        up = upload(server, "photo", path)
        saved = call("photos.saveMessagesPhoto", GROUP, photo=up["photo"], server=up["server"], hash=up["hash"])[0]
    key = f"_{saved['access_key']}" if saved.get("access_key") else ""
    return f"photo{saved['owner_id']}_{saved['id']}{key}"


def upload_video(gid, item):
    """Видео в сообщество (нужен VK_USER_TOKEN). clip=true — сначала пробуем как клип (shortVideo)."""
    if not USER:
        raise RuntimeError("Для загрузки видео нужен ключ администратора: " + (USER_ERROR or "нет VK_BRIDGE_KEY / VK_USER_TOKEN"))
    if item.get("clip"):
        try:
            meta = call("shortVideo.create", USER, group_id=gid, file_size=os.path.getsize(item["path"]),
                        description=item.get("description", ""))
            upload(meta["upload_url"], "file", item["path"])
            return f"video{meta['owner_id']}_{meta['video_id']}"
        except Exception as e:
            item["clip_error"] = str(e)
    meta = call("video.save", USER, group_id=gid, name=item.get("title", ""), description=item.get("description", ""),
                wallpost=0)
    upload(meta["upload_url"], "video_file", item["path"])
    return f"video{meta['owner_id']}_{meta['video_id']}"


def video_test(path="scratch/vk/test-video.mp4"):
    """Пробуем загрузить видео ключом сообщества разными способами; удачную загрузку сразу удаляем."""
    gid = group_id()
    out = {"group_id": gid}
    tries = {
        "video.save group_id private": lambda: call("video.save", GROUP, group_id=gid, name="test", is_private=1),
        "video.save group_id": lambda: call("video.save", GROUP, group_id=gid, name="test", wallpost=0),
        "video.save no group_id private": lambda: call("video.save", GROUP, name="test", is_private=1),
        "shortVideo.create": lambda: call("shortVideo.create", GROUP, group_id=gid, file_size=os.path.getsize(path)),
        "docs.getMessagesUploadServer": lambda: call("docs.getMessagesUploadServer", GROUP, peer_id=0, type="doc"),
    }
    for name, fn in tries.items():
        if name == "video.save group_id" and "upload" in out.get("video.save group_id private", {}):
            continue  # закрытая загрузка уже прошла — открытую (видна в группе) не пробуем
        try:
            meta = fn()
            res = {"meta": {k: v for k, v in meta.items() if k != "upload_url"}}
            field = "file" if name in ("shortVideo.create", "docs.getMessagesUploadServer") else "video_file"
            res["upload"] = upload(meta["upload_url"], field, path)
            if name.startswith("docs"):
                res["saved"] = call("docs.save", GROUP, file=res["upload"]["file"], title="test")
            vid, owner = meta.get("video_id"), meta.get("owner_id")
            if vid and owner:
                try:
                    res["deleted"] = call("video.delete", GROUP, video_id=vid, owner_id=owner)
                except Exception as e:
                    res["delete_error"] = str(e)
            out[name] = res
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


def check():
    out = {"group_token": bool(GROUP), "user_token": bool(USER)}
    if USER_ERROR:
        out["user_token_error"] = USER_ERROR
    if not GROUP and not USER:
        out["error"] = "Нет ни VK_GROUP_TOKEN, ни VK_USER_TOKEN в секретах репозитория"
        return out
    try:
        gid = group_id()
        out["group_id"] = gid
        g = call("groups.getById", GROUP or USER, group_id=gid)
        g = (g["groups"] if isinstance(g, dict) else g)[0]
        out["group"] = {"name": g.get("name"), "screen_name": g.get("screen_name")}
    except Exception as e:
        out["group_error"] = str(e)
        return out
    if GROUP:
        try:
            out["group_token_permissions"] = [p["name"] for p in call("groups.getTokenPermissions", GROUP)["permissions"]]
        except Exception as e:
            out["group_token_permissions_error"] = str(e)
    for name, tok in (("group", GROUP), ("user", USER)):
        if not tok:
            continue
        try:
            call("photos.getWallUploadServer", tok, group_id=gid)
            out[f"{name}_can_upload_photo"] = True
        except Exception as e:
            out[f"{name}_can_upload_photo"] = str(e)
    if USER:
        try:
            u = call("users.get", USER)[0]
            out["user"] = f"{u.get('first_name')} {u.get('last_name')}"
            g = call("groups.get", USER, filter="admin,editor")
            out["user_is_admin_of_group"] = gid in g.get("items", [])
        except Exception as e:
            out["user_error"] = str(e)
    try:
        out["test_photo_upload"] = upload_photo(gid, os.environ.get("VK_TEST_IMAGE", "docs/landing/vk/vk-avatar.jpg"))
    except Exception as e:
        out["test_photo_upload"] = str(e)
    return out


def post(path):
    spec = json.load(open(path))
    gid = group_id()
    att = [upload_photo(gid, p) for p in spec.get("images", [])]
    att += [upload_video(gid, v) for v in spec.get("videos", [])]
    params = {"owner_id": -gid, "from_group": 1, "message": spec.get("text", "")}
    if att:
        params["attachments"] = ",".join(att)
    if spec.get("publish_date"):
        params["publish_date"] = int(datetime.datetime.fromisoformat(spec["publish_date"]).timestamp())
    r = call("wall.post", GROUP or USER, **params)
    out = {"post_id": r["post_id"], "url": f"https://vk.com/wall-{gid}_{r['post_id']}", "attachments": att,
           "clip_errors": [v["clip_error"] for v in spec.get("videos", []) if v.get("clip_error")]}
    if spec.get("pin") and not spec.get("publish_date"):
        call("wall.pin", USER or GROUP, owner_id=-gid, post_id=r["post_id"])
        out["pinned"] = True
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    os.makedirs("scratch/vk", exist_ok=True)
    name = mode if mode in ("check", "video_test") else os.path.splitext(os.path.basename(sys.argv[2]))[0]
    try:
        result = check() if mode == "check" else video_test() if mode == "video_test" else post(sys.argv[2])
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, ensure_ascii=False, indent=1))
    json.dump(result, open(f"scratch/vk/{name}.result.json", "w"), ensure_ascii=False, indent=1)
