"""Пакетная генерация картинок для роликов через CometAPI (запускается
внутри GitHub Actions — .github/workflows/call-brand-images.yml; у
песочницы Claude Code нет прямого доступа в интернет).

Для каждой картинки из jobs-файла:
  1. Nano Banana (gemini-2.5-flash-image) рисует по промпту; ВСЕГДА
     получает референсы стиля (брендбук docs/references/oleg-brand-board-*.jpg,
     плюс при необходимости фото аватара) — прямое требование пользователя
     23.09.2026: "обязательно отправлять в Gemini референс стиля".
  2. Gemini (gemini-3.5-flash) проверяет картинку: соответствие смыслу,
     стилю брендбука, отсутствие текста/артефактов. Вердикт — ГЕЙТ, не лог:
     если не OK, картинка перегенерируется с учётом замечания (до MAX_TRIES).

jobs-файл (JSON): {"style_refs": [...пути...], "jobs": [{"name", "prompt",
"meaning", "aspect", "kind": "icon"|"illustration", "extra_refs": [...]}]}
Результат: scratch/img/<name>.png + scratch/img/<name>.json (вердикты).
"""
import base64
import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.error
import urllib.request

API_KEY = os.environ["COMETAPI_KEY"]
BASE = "https://api.cometapi.com/v1beta/models"
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-3.5-flash")
OUT_DIR = "scratch/img"
MAX_TRIES = 3

STYLE = {
    "icon": (
        "Use the attached brand board images as the STRICT style reference (see the 'ИКОНКИ' "
        "section): a single simple rounded line icon drawn in deep blue #1E4FBF with small "
        "green #27AE60 accents, placed in the centre of a soft light-blue circle (#E8F0FD). "
        "Plain pure white background around the circle. Clean, modern, friendly, medical. "
        "No text, no letters, no numbers, no logos."
    ),
    "illustration": (
        "Use the attached brand board images as the STRICT style reference for palette and mood: "
        "modern clean semi-flat editorial illustration, soft rounded shapes, gentle soft shading, "
        "palette of deep blue #1E4FBF, sky blue #2F80ED, green #27AE60, light background #F5F8FC, "
        "white, warm natural skin tones. Calm, caring, professional pharmacy atmosphere. "
        "No text, no letters, no logos, no brand names anywhere in the image."
    ),
    # Макет страницы (лендинг и т.п.): стиль задаёт сам промпт, брендбук не нужен.
    "mockup": "",
}


STYLE_QA = {
    "icon": "простая линейная иконка синим цветом с зелёными акцентами в светло-голубом круге на белом фоне, как раздел 'ИКОНКИ' брендбука",
    "illustration": "современная полуплоская (semi-flat) редакционная иллюстрация в палитре брендбука (синий/голубой/зелёный/светлый фон), НЕ фото",
    "mockup": "макет веб-страницы (дизайн-концепт сайта), стиль описан в задании",
}


def call(model, body):
    req = urllib.request.Request(
        f"{BASE}/{model}:generateContent", data=json.dumps(body).encode(), method="POST",
        headers={"x-goog-api-key": API_KEY, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {model}: {e.read().decode(errors='replace')[:500]}")


def img_part(path):
    mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    with open(path, "rb") as f:
        return {"inline_data": {"mime_type": mime, "data": base64.b64encode(f.read()).decode()}}


def text_of(resp):
    parts = (resp.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def generate(job, refs, fix_note):
    parts = [img_part(p) for p in refs + job.get("extra_refs", [])]
    if job["kind"] == "mockup":
        prompt = job["prompt"]
    else:
        prompt = STYLE[job["kind"]] + " Do not copy the reference's layout or subject, only its visual style.\n\nSubject: " + job["prompt"]
    if job.get("extra_refs"):
        prompt += "\nThe pharmacist in the image must look like the woman in the attached photo (same face, hair, white coat)."
    if fix_note:
        prompt += f"\n\nIMPORTANT — a previous attempt was rejected for this reason, fix it: {fix_note}"
    parts.append({"text": prompt})
    body = {"contents": [{"parts": parts}], "generationConfig": {
        "responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": job.get("aspect", "1:1")}}}
    # job["model"] — предпочтительная модель (например Nano Banana Pro); при ошибке — IMAGE_MODEL.
    try:
        resp = call(job.get("model") or IMAGE_MODEL, body)
    except RuntimeError as e:
        if not job.get("model"):
            raise
        print(f"{job['name']}: {job['model']} failed, fallback to {IMAGE_MODEL}: {e}", flush=True)
        resp = call(IMAGE_MODEL, body)
    cand = (resp.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    p = next((x for x in cand if x.get("inlineData", {}).get("data")), None)
    if not p:
        raise RuntimeError("no image: " + json.dumps(resp)[:300])
    return p["inlineData"]["data"], p["inlineData"].get("mimeType", "image/png")


def qa(job, b64, mime, refs):
    if job["kind"] == "mockup":
        q = (
            "Ты — арт-директор. Это сгенерированный дизайн-концепт веб-страницы.\n"
            f"Задумано: «{job['meaning']}».\n"
            "Проверь только: 1) это цельный правдоподобный макет страницы сайта, а не коллаж/набор "
            "разрозненных картинок; 2) стиль соответствует задуманному; 3) нет грубых артефактов "
            "(искажённые лица, сломанная вёрстка, наложение блоков друг на друга); 4) крупный текст, "
            "если есть, читается и не превращается в бессмысленные символы (мелкий текст-заглушка допустим).\n"
            "Ответь СТРОГО JSON без markdown: {\"ok\": true|false, \"issue\": \"коротко по-английски, "
            "что исправить, или пусто\"}"
        )
        parts = [{"text": q}, {"inline_data": {"mime_type": mime, "data": b64}}]
        t = text_of(call(TEXT_MODEL, {"contents": [{"parts": parts}]}))
        try:
            return json.loads(re.sub(r"^```(json)?|```$", "", t.strip(), flags=re.M).strip())
        except Exception:
            return {"ok": False, "issue": f"unparsable QA answer: {t[:200]}"}
    q = (
        "Ты — строгий арт-директор обучающего видео для фармацевтов. Первые изображения — брендбук "
        "(референс стиля), последнее — сгенерированная картинка.\n"
        f"Картинка должна визуализировать: «{job['meaning']}».\n"
        f"Задуманный стиль (он утверждён, НЕ требуй другого — например фотореализма): {STYLE_QA[job['kind']]}\n"
        "Проверь: 1) по смыслу картинка понятно передаёт эту мысль (не требуй буквальности, достаточно "
        "ясной ассоциации); 2) стиль соответствует задуманному, палитра — брендбуку; 3) нет читаемого или "
        "псевдо-текста, букв, логотипов, вывесок с надписями; 4) нет артефактов (лишние/сросшиеся пальцы, "
        "искажённые лица, дублированные персонажи, криво обрезанные объекты).\nОтветь СТРОГО JSON без "
        "markdown: {\"ok\": true|false, \"issue\": \"коротко, что исправить (по-английски, одной фразой), "
        "или пусто\"}"
    )
    parts = [img_part(r) for r in refs] + [{"text": q}, {"inline_data": {"mime_type": mime, "data": b64}}]
    t = text_of(call(TEXT_MODEL, {"contents": [{"parts": parts}]}))
    try:
        return json.loads(re.sub(r"^```(json)?|```$", "", t.strip(), flags=re.M).strip())
    except Exception:
        return {"ok": False, "issue": f"unparsable QA answer: {t[:200]}"}


def run_job(job, refs):
    log, fix = [], None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            b64, mime = generate(job, refs, fix)
            verdict = qa(job, b64, mime, refs)
        except Exception as e:
            log.append({"attempt": attempt, "error": str(e)})
            continue
        log.append({"attempt": attempt, **verdict})
        with open(f"{OUT_DIR}/{job['name']}.png", "wb") as f:
            f.write(base64.b64decode(b64))
        if verdict.get("ok"):
            break
        fix = verdict.get("issue")
    status = "ok" if log and log[-1].get("ok") else "rejected"
    with open(f"{OUT_DIR}/{job['name']}.json", "w") as f:
        json.dump({"job": job, "status": status, "attempts": log}, f, ensure_ascii=False, indent=2)
    print(f"[{status}] {job['name']}: {json.dumps(log, ensure_ascii=False)}", flush=True)
    return status


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    only = set(filter(None, (os.environ.get("ONLY") or "").split(",")))
    jobs = [j for j in spec["jobs"] if not only or j["name"] in only]
    os.makedirs(OUT_DIR, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda j: run_job(j, spec["style_refs"]), jobs))
    print(f"done: {results.count('ok')} ok, {results.count('rejected')} rejected")


if __name__ == "__main__":
    main()
