"""Звуковой слой роликов-примеров: синтез эффектов кодом (numpy) и сведение
с озвучкой через ffmpeg.

Эффекты — короткие WAV 48 кГц моно:
  whoosh  — вжух на смене сцены (фильтрованный шум со сдвигом частоты)
  hit     — тяжёлый удар/«бум» (низкий синус с падением тона + щелчок)
  stamp   — штамп: глухой удар + шлепок
  pop     — короткий «поп» появления элемента
  ring    — двойная трель телефонного звонка
  tick    — тиканье часов (для «спешки»)
  riser   — нарастающий тон перед кульминацией
  glitch  — цифровой сбой (для «тревожных» моментов)
  bed     — тревожный подклад: низкий гул + пульс, бесшовный на всю длину

mix(voice, events, bed, out): озвучка + подклад (с приглушением под голос)
+ эффекты в заданные моменты, нормализация громкости.
"""
import os
import subprocess
import wave

import numpy as np

SR = 48000


def _save(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return path


def _t(d):
    return np.arange(int(SR * d)) / SR


def _env(n, a, r):
    e = np.ones(n)
    ai, ri = int(SR * a), int(SR * r)
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if ri:
        e[-ri:] *= np.linspace(1, 0, ri) ** 2
    return e


def _lowpass(x, cutoff):
    """Однополюсный ФНЧ; cutoff — число или массив (переменная частота)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def whoosh(d=0.45, seed=1):
    rng = np.random.default_rng(seed)
    n = int(SR * d)
    noise = rng.normal(0, 1, n)
    t = np.linspace(0, 1, n)
    sweep = 300 + 5000 * np.sin(np.pi * t) ** 2
    x = _lowpass(noise, sweep) - _lowpass(noise, sweep * 0.25)
    x *= np.sin(np.pi * t) ** 1.5
    return x / (np.abs(x).max() + 1e-9) * 0.7


def hit(d=0.9):
    t = _t(d)
    f = 95 * np.exp(-t * 6) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    click = np.random.default_rng(3).normal(0, 1, len(t)) * np.exp(-t * 90) * 0.5
    x = body + _lowpass(click, 2500)
    return x / np.abs(x).max() * 0.9


def stamp(d=0.45):
    t = _t(d)
    thud = np.sin(2 * np.pi * (70 * np.exp(-t * 10) + 55) * t) * np.exp(-t * 14)
    slap = _lowpass(np.random.default_rng(5).normal(0, 1, len(t)), 3500) * np.exp(-t * 45)
    x = thud + 1.6 * slap
    return x / np.abs(x).max() * 0.9


def pop(d=0.14):
    t = _t(d)
    x = np.sin(2 * np.pi * (900 * np.exp(-t * 30) + 300) * t) * np.exp(-t * 35)
    return x * 0.5


def ring(d=1.6):
    """Классическая трель: 2 посылки по 0.4 с, тон 440+480 Гц с модуляцией 20 Гц."""
    t = _t(d)
    tone = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * 0.5
    trill = (np.sign(np.sin(2 * np.pi * 20 * t)) + 1) / 2
    gate = ((t % 0.8) < 0.4).astype(float)
    x = tone * (0.35 + 0.65 * trill) * gate
    x = _lowpass(x, 3000)
    return x * _env(len(t), 0.005, 0.05) * 0.45


def tick(n=6, gap=0.5):
    out = np.zeros(int(SR * n * gap))
    for i in range(n):
        s = int(SR * i * gap)
        tt = _t(0.04)
        c = np.sin(2 * np.pi * (2400 if i % 2 else 1900) * tt) * np.exp(-tt * 160)
        out[s:s + len(c)] += c * 0.6
    return out


def riser(d=1.2):
    t = _t(d)
    f = 120 + 900 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    noise = _lowpass(np.random.default_rng(7).normal(0, 1, len(t)), 200 + 6000 * t / d) * 0.3
    x = (tone + noise) * (t / d) ** 2
    return x / np.abs(x).max() * 0.6


def glitch(d=0.35, seed=9):
    rng = np.random.default_rng(seed)
    n = int(SR * d)
    x = np.zeros(n)
    i = 0
    while i < n:
        seg = rng.integers(int(SR * 0.01), int(SR * 0.04))
        kind = rng.integers(0, 3)
        tt = np.arange(min(seg, n - i)) / SR
        if kind == 0:
            x[i:i + len(tt)] = np.sign(np.sin(2 * np.pi * rng.integers(200, 1600) * tt)) * 0.3
        elif kind == 1:
            x[i:i + len(tt)] = rng.normal(0, 0.35, len(tt))
        i += seg
    return x * _env(n, 0.002, 0.05)


def bed(d, bpm=92):
    """Тревожный подклад: гул 55 Гц + квинта, тихий «пульс сердца» в темп."""
    t = _t(d)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t)
             + 0.25 * np.sin(2 * np.pi * 110 * t + 0.4 * np.sin(2 * np.pi * 0.2 * t)))
    drone *= 0.18 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t))
    beat = 60 / bpm
    pulse = np.zeros_like(t)
    for k in range(int(d / beat)):
        for off, amp in ((0.0, 1.0), (0.22, 0.6)):   # «тук-тук»
            s = int(SR * (k * beat + off))
            tt = _t(0.25)
            p = np.sin(2 * np.pi * (60 * np.exp(-tt * 12) + 40) * tt) * np.exp(-tt * 18) * amp
            e = min(len(p), len(pulse) - s)
            if e > 0:
                pulse[s:s + e] += p[:e]
    x = drone + 0.35 * pulse
    x *= _env(len(t), 1.0, 1.5)
    return x / np.abs(x).max() * 0.5


GEN = {"whoosh": whoosh, "hit": hit, "stamp": stamp, "pop": pop, "ring": ring, "tick": tick,
       "riser": riser, "glitch": glitch}


def render_all(folder):
    os.makedirs(folder, exist_ok=True)
    out = {}
    for name, fn in GEN.items():
        out[name] = _save(f"{folder}/{name}.wav", fn())
    return out


def mix(voice, events, out, folder, bed_gain=0.22, total=None):
    """voice — mp3 озвучки; events — [(время, имя, громкость)]; подклад
    приглушается под голос (sidechaincompress), эффекты — поверх."""
    files = render_all(folder)
    if total is None:
        total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                      "csv=p=0", voice], capture_output=True, text=True).stdout)
    bed_path = _save(f"{folder}/bed.wav", bed(total + 0.5))
    inputs = ["-i", voice, "-i", bed_path]
    fc = ["[0:a]aformat=sample_rates=48000:channel_layouts=mono,asplit=2[v][sc]",
          f"[1:a]volume={bed_gain}[b0]",
          "[b0][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[bed]"]
    labels = ["[v]", "[bed]"]
    for i, (tm, name, gain) in enumerate(events):
        inputs += ["-i", files[name]]
        ms = max(0, int(tm * 1000))
        fc.append(f"[{i + 2}:a]volume={gain},adelay={ms}|{ms}[e{i}]")
        labels.append(f"[e{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,"
              "alimiter=limit=0.95,loudnorm=I=-15:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[a]",
                    "-t", f"{total}", "-ar", "48000", "-c:a", "pcm_s16le", out], check=True)
    return out
