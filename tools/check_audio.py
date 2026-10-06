"""Прослушивание озвучки через Gemini (CometAPI): ударения, ошибки чтения,
плоская интонация. Запускается внутри GitHub Actions тем же мостом, что и
картинки (call-brand-images.yml → tools/gen_brand_images.py), если в
jobs-файле "mode": "audio_check" — отдельный воркфлоу в main не нужен.

jobs-файл: {"mode": "audio_check", "jobs": [{"name", "audio", "text",
"model" (необязательно)}]}. Результат: scratch/img/<name>.json.

Whisper ударения не слышит (он пишет слово правильно при любом ударении),
поэтому ударения проверяет модель, слушающая аудио целиком.
"""
import base64
import json
import os
import urllib.error
import urllib.request

API_KEY = os.environ["COMETAPI_KEY"]
BASE = "https://api.cometapi.com/v1beta/models"
OUT_DIR = "scratch/img"

PROMPT = """Ты — строгий редактор русской дикторской озвучки и эксперт по орфоэпии.
Прослушай аудио ЦЕЛИКОМ и сравни с текстом сценария (теги в [скобках] — указания интонации,
их не читают). Найди:
1) stress_errors — КАЖДОЕ слово, где ударение поставлено не по нормам русского литературного
   языка (например «звОнит» вместо «звонИт», «сЕрвис» и т.п.). Для каждого: word (как в тексте),
   heard (как прозвучало, ударную гласную — заглавной), expected (правильно, ударная — заглавной),
   time (примерная секунда).
2) misread — пропущенные, лишние или искажённые слова/буквы (word, heard, time).
3) flat_spots — места, где подача плоская, монотонная, без нужного акцента для серьёзной темы
   (phrase, time, advice — что усилить).
4) overall — 1–2 предложения об общей подаче (уверенность, драматизм, темп).
Если ударения везде верные — stress_errors пустой; не придумывай ошибок.
Ответ — ТОЛЬКО JSON: {"stress_errors": [...], "misread": [...], "flat_spots": [...], "overall": "..."}

Текст сценария:
"""


def call(model, body):
    req = urllib.request.Request(
        f"{BASE}/{model}:generateContent", data=json.dumps(body).encode(), method="POST",
        headers={"x-goog-api-key": API_KEY, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {model}: {e.read().decode(errors='replace')[:500]}")


def check(job):
    with open(job["audio"], "rb") as f:
        audio = base64.b64encode(f.read()).decode()
    model = job.get("model", "gemini-3.5-flash")
    body = {"contents": [{"role": "user", "parts": [
        {"text": PROMPT + job["text"]},
        {"inline_data": {"mime_type": "audio/mpeg", "data": audio}}]}],
        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}}
    resp = call(model, body)
    parts = (resp.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    txt = "".join(p.get("text", "") for p in parts).strip()
    try:
        res = json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
    except Exception:
        res = {"raw": txt}
    res["model"] = model
    res["audio"] = job["audio"]
    return res


def run(spec, only=()):
    os.makedirs(OUT_DIR, exist_ok=True)
    for job in spec["jobs"]:
        if only and job["name"] not in only:
            continue
        try:
            res = check(job)
        except Exception as e:
            res = {"error": str(e)}
        print(job["name"], json.dumps(res, ensure_ascii=False, indent=1))
        with open(f"{OUT_DIR}/{job['name']}.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
