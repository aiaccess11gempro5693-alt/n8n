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
  click   — UI-клик касания (ролик 4)
  beep    — двухтоновый «бип» уведомления
  ding    — светлый «динь» (появление цены, успех)
  bass    — бас-удар (саб-дроп) на главном слове
  groove  — бодрый подклад: бочка, хэт, пульсирующий аккорд (ролик 4)
  pad     — тянущиеся аккорды + бас-пульс (ролик 5, ОТКЛОНЁН: «жутко, как в фильме ужасов»)
  piano   — светлый перебор пианино (ролик 5, ОТКЛОНЁН: «музыка для сна»)
  corporate — бодрый корпоративный подклад: перебор пианино шестнадцатыми,
            мягкая бочка, хлопок на 2 и 4, шейкер, 118 bpm (ролик 5)
  chime   — мягкий двойной колокольчик (переключение языка, ролик 5)

music_bed(path) — готовый трек (например из библиотеки HeyGen) вместо синтеза:
  возвращает функцию-подклад для mix(bed_fn=...).

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


def click(d=0.06):
    t = _t(d)
    x = np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 220) + 0.5 * np.sin(2 * np.pi * 1600 * t) * np.exp(-t * 160)
    return x * 0.6


def beep(d=0.32):
    t = _t(d)
    f = np.where(t < 0.13, 1318.5, 1760.0)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * ((t < 0.11) | (t > 0.15))
    return _lowpass(x, 6000) * _env(len(t), 0.004, 0.06) * 0.45


def ding(d=0.9):
    t = _t(d)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k)
            for f, a, k in ((1568, 1.0, 5), (2349, 0.5, 7), (3136, 0.25, 9)))
    return x / np.abs(x).max() * 0.5 * _env(len(t), 0.002, 0.1)


def bass(d=0.8):
    t = _t(d)
    f = 70 * np.exp(-t * 4) + 42
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5)
    x += _lowpass(np.random.default_rng(11).normal(0, 1, len(t)), 1800) * np.exp(-t * 60) * 0.3
    return x / np.abs(x).max() * 0.9


def groove(d, bpm=112):
    """Бодрый подклад: бочка на долю, хэт на восьмые, мягкий аккорд-пульс
    (до-мажорная гармония A–F–C–G по такту)."""
    t = _t(d)
    beat = 60 / bpm
    x = np.zeros_like(t)
    kick_t = _t(0.3)
    kick = np.sin(2 * np.pi * (110 * np.exp(-kick_t * 25) + 45) * kick_t) * np.exp(-kick_t * 9)
    hat_t = _t(0.05)
    hat = np.random.default_rng(2).normal(0, 1, len(hat_t)) * np.exp(-hat_t * 90)
    hat = hat - _lowpass(hat, 7000)
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 261.6, 329.6), (196.0, 246.9, 293.7)]
    n = int(d / beat)
    for k in range(n):
        s = int(SR * k * beat)
        e = min(len(kick), len(x) - s)
        if e > 0:
            x[s:s + e] += kick[:e] * 0.9
        for half in (0.0, 0.5):
            s2 = int(SR * (k + half) * beat)
            e2 = min(len(hat), len(x) - s2)
            if e2 > 0:
                x[s2:s2 + e2] += hat[:e2] * (0.18 if half else 0.1)
        if k % 2 == 1:   # аккорд-«стаб» на слабую долю
            ct = _t(beat * 0.9)
            ch = chords[(k // 4) % 4]
            stab = sum(np.sin(2 * np.pi * f * ct) + 0.3 * np.sin(2 * np.pi * 2 * f * ct) for f in ch)
            stab *= np.exp(-ct * 6) * 0.12
            e3 = min(len(stab), len(x) - s)
            if e3 > 0:
                x[s:s + e3] += stab[:e3]
    x *= _env(len(t), 0.3, 1.2)
    return x / np.abs(x).max() * 0.5


def chime(d=1.2):
    """Мягкий двойной колокольчик: две ноты (ля → ми) с долгим хвостом."""
    t = _t(d)
    x = np.zeros_like(t)
    for off, f in ((0.0, 880.0), (0.12, 1318.5)):
        s = int(SR * off)
        tt = t[: len(t) - s]
        n = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 4.5)
        x[s:] += n
    return x / np.abs(x).max() * 0.45 * _env(len(t), 0.003, 0.2)


def pad(d, bpm=76):
    """Спокойный подклад: тянущиеся аккорды (ре-мажорная гармония D–Bm–G–A, мягкая
    атака, лёгкое вибрато) + приглушённый пульс баса на сильную долю."""
    t = _t(d)
    beat = 60 / bpm
    bar = beat * 4
    chords = [(146.8, 185.0, 220.0, 293.7), (123.5, 185.0, 246.9, 293.7),
              (98.0, 196.0, 246.9, 293.7), (110.0, 220.0, 277.2, 329.6)]
    x = np.zeros_like(t)
    n = int(d / bar) + 1
    for k in range(n):
        s = int(SR * k * bar)
        if s >= len(x):
            break
        ct = _t(bar * 1.15)
        ch = chords[k % 4]
        vib = 1 + 0.002 * np.sin(2 * np.pi * 5 * ct)
        tone = sum(np.sin(2 * np.pi * f * vib * ct) + 0.25 * np.sin(2 * np.pi * 2 * f * vib * ct) for f in ch)
        tone *= _env(len(ct), 0.6, 0.6) * 0.12
        e = min(len(tone), len(x) - s)
        x[s:s + e] += tone[:e]
        for b in range(4):   # мягкий бас-пульс
            sb = int(SR * (k * bar + b * beat))
            bt = _t(0.4)
            p = np.sin(2 * np.pi * ch[0] / 2 * bt) * np.exp(-bt * 7) * (0.5 if b == 0 else 0.25)
            e2 = min(len(p), len(x) - sb)
            if e2 > 0:
                x[sb:sb + e2] += p[:e2]
    x = _lowpass(x, 3500)
    x *= _env(len(t), 1.0, 1.2)
    return x / np.abs(x).max() * 0.5


def piano(d, bpm=100):
    """Светлый корпоративный подклад: мажорные аккорды D–A–G–D переборами
    восьмыми в среднем/высоком регистре (тон «пианино»: синус + обертоны с
    быстрым затуханием), лёгкий бас на первую долю такта. Без тянущихся
    низких тонов и вибрато — они звучат тревожно."""
    t = _t(d)
    x = np.zeros_like(t)
    e8 = 60 / bpm / 2
    # аккорды (бас, арпеджио вверх-вниз)
    prog = [(146.8, (293.7, 370.0, 440.0, 587.3)), (110.0, (277.2, 329.6, 440.0, 554.4)),
            (98.0, (293.7, 392.0, 493.9, 587.3)), (146.8, (293.7, 370.0, 440.0, 587.3))]
    order = [0, 1, 2, 3, 2, 1, 2, 3]

    def note(f, dur, amp):
        nt = _t(dur)
        v = (np.sin(2 * np.pi * f * nt) + 0.4 * np.sin(2 * np.pi * 2 * f * nt) * np.exp(-nt * 3)
             + 0.15 * np.sin(2 * np.pi * 3 * f * nt) * np.exp(-nt * 5))
        return v * np.exp(-nt * 2.6) * _env(len(nt), 0.004, 0.05) * amp

    k = 0
    while k * e8 < d:
        bar, step = divmod(k, 8)
        bass, arp = prog[bar % 4]
        s = int(SR * k * e8)
        n = note(arp[order[step]], 1.4, 0.32)
        if step == 0:
            n = n + note(bass, 2.0, 0.28)[: len(n)] if len(note(bass, 2.0, 0.28)) >= len(n) else n
        e = min(len(n), len(x) - s)
        if e > 0:
            x[s:s + e] += n[:e]
        k += 1
    x *= _env(len(t), 0.8, 1.5)
    return x / np.abs(x).max() * 0.5


def corporate(d, bpm=118):
    """Бодрый корпоративный подклад (вдохновляющая реклама): мажор D–A–Bm–G,
    перебор «пианино» шестнадцатыми, мягкая бочка на каждую долю, хлопок на
    2 и 4, шейкер на восьмые, басовая нота на долю."""
    t = _t(d)
    x = np.zeros_like(t)
    beat = 60 / bpm
    s16 = beat / 4
    prog = [(73.4, (293.7, 370.0, 440.0, 587.3)), (110.0, (277.2, 329.6, 440.0, 554.4)),
            (123.5, (246.9, 293.7, 370.0, 493.9)), (98.0, (293.7, 392.0, 493.9, 587.3))]
    pat = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 2, 3, 2, 1]

    def pluck(f, dur, amp):
        nt = _t(dur)
        v = (np.sin(2 * np.pi * f * nt) + 0.45 * np.sin(2 * np.pi * 2 * f * nt) * np.exp(-nt * 6)
             + 0.2 * np.sin(2 * np.pi * 3 * f * nt) * np.exp(-nt * 9))
        return v * np.exp(-nt * 7) * _env(len(nt), 0.003, 0.03) * amp

    def add(sig, at):
        st = int(SR * at)
        e = min(len(sig), len(x) - st)
        if e > 0:
            x[st:st + e] += sig[:e]

    kt = _t(0.25)
    kick = np.sin(2 * np.pi * (95 * np.exp(-kt * 30) + 50) * kt) * np.exp(-kt * 14)
    ct = _t(0.18)
    rng = np.random.default_rng(5)
    clap = rng.normal(0, 1, len(ct)) * np.exp(-ct * 30)
    clap = clap - _lowpass(clap, 1200)
    sh_t = _t(0.06)
    shaker = rng.normal(0, 1, len(sh_t)) * np.exp(-sh_t * 70)
    shaker = shaker - _lowpass(shaker, 6000)
    n16 = int(d / s16) + 1
    for k in range(n16):
        at = k * s16
        bar, step = divmod(k, 16)
        bass, arp = prog[bar % 4]
        add(pluck(arp[pat[step]], 0.5, 0.22), at)
        if step % 4 == 0:   # доля
            add(kick * 0.55, at)
            add(pluck(bass, 0.45, 0.35), at)
            if step in (4, 12):
                add(clap * 0.35, at)
        if step % 2 == 0:
            add(shaker * (0.10 if step % 4 else 0.06), at)
    x *= _env(len(t), 0.3, 1.2)
    return x / np.abs(x).max() * 0.5


def music_bed(path, fade=1.5):
    """Подклад из готового трека: декодирует файл в моно 48 кГц, обрезает под
    длину ролика (при нехватке — повторяет), плавное начало и конец; пик 0.5,
    как у синтезированных подкладов — громкость задаёт bed_gain в mix()."""
    def fn(d):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).astype(float)
        n = int(SR * d)
        while len(x) < n:
            x = np.concatenate([x, x])
        x = x[:n] * _env(n, 0.4, fade)
        return x / max(np.abs(x).max(), 1e-6) * 0.5
    return fn


GEN = {"whoosh": whoosh, "hit": hit, "stamp": stamp, "pop": pop, "ring": ring, "tick": tick,
       "riser": riser, "glitch": glitch, "click": click, "beep": beep, "ding": ding, "bass": bass,
       "chime": chime}


def render_all(folder):
    os.makedirs(folder, exist_ok=True)
    out = {}
    for name, fn in GEN.items():
        out[name] = _save(f"{folder}/{name}.wav", fn())
    return out


def mix(voice, events, out, folder, bed_gain=0.22, total=None, bed_fn=None):
    """voice — mp3 озвучки; events — [(время, имя, громкость)]; подклад
    приглушается под голос (sidechaincompress), эффекты — поверх."""
    files = render_all(folder)
    if total is None:
        total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                      "csv=p=0", voice], capture_output=True, text=True).stdout)
    bed_path = _save(f"{folder}/bed.wav", (bed_fn or bed)(total + 0.5))
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
