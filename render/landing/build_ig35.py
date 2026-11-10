"""Reels №35 «Тетрис: игра, за которую автор не получил ни копейки».

Тот же формат и движок, что у №32 «Прайм Москвы» (`build_ig32.py`): неоновая моушн-графика кодом поверх
ночного пиксельного города, рамка «▶ PLAY / дата», неоновые заголовки, крупные субтитры по 2–3 слова.
Свои сцены: падающие тетромино, экран «Электроники-60» со скобками, ряд собирается и исчезает,
«ТЕТРА + ТЕННИС = ТЕТРИС», дискеты разлетаются, маршрут стран, штамп «ПРАВА — ГОСУДАРСТВУ», Game Boy,
счётчик 35 000 000, «0 $», 1996 / 12 лет, башня из фигур. Музыка — чиптюн из библиотеки HeyGen.

python3 render/landing/build_ig35.py [--preview t1,t2]  →  render/landing/ig35-9x16.mp4
"""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig32 as M  # noqa: E402
import sfx as SFX  # noqa: E402

ROOT = M.ROOT
M.SCEN = f"{ROOT}/docs/scenarios/insta-35-tetris.md"
M.AUDIO = f"{ROOT}/scratch/ig35/voice.mp3"
M.WHISPER = f"{ROOT}/scratch/ig35-whisper-final.json"
M.OUT = f"{ROOT}/render/landing/ig35-9x16.mp4"
M.TMP = f"{ROOT}/render/landing/.ig35"
MUSIC = f"{ROOT}/scratch/music/ig35-music.mp3"
MUSIC_GAIN = 0.55
W, H = M.W, M.H
PINK, CYAN, GOLD, RED, GREEN, WHITE = M.PINK, M.CYAN, M.GOLD, M.RED, M.GREEN, M.WHITE
PURPLE, ORANGE = (170, 90, 255), (255, 150, 40)
TERM = (90, 255, 140)
neon_text, plain_text, pill, bubble, place, appear, ease = (M.neon_text, M.plain_text, M.pill, M.bubble, M.place,
                                                            M.appear, M.ease)

SHAPES = {   # тетромино: клетки (x, y)
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)], "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)], "L": [(0, 0), (0, 1), (0, 2), (1, 2)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)], "Z": [(0, 0), (1, 0), (1, 1), (2, 1)], "J": [(1, 0), (1, 1), (1, 2), (0, 2)],
}
SCOL = {"I": CYAN, "O": GOLD, "T": PURPLE, "L": ORANGE, "S": GREEN, "Z": RED, "J": PINK}


def block_sprite(col, cell=56):
    key = ("blk", col, cell)
    if key in M.CACHE:
        return M.CACHE[key]
    pad = 20
    im = Image.new("RGBA", (cell + pad * 2, cell + pad * 2), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rectangle((pad, pad, pad + cell - 4, pad + cell - 4), fill=col + (200,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rectangle((pad, pad, pad + cell - 4, pad + cell - 4), fill=tuple(int(c * 0.55) for c in col) + (255,),
                outline=col + (255,), width=4)
    d.rectangle((pad + 8, pad + 8, pad + cell - 20, pad + 16), fill=(255, 255, 255, 120))
    M.CACHE[key] = im
    return im


def draw_piece(cv, kind, cx, cy, cell=56, alpha=1.0, rot=0):
    pts = SHAPES[kind]
    for _ in range(rot % 4):
        pts = [(-y, x) for x, y in pts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ox, oy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    b = block_sprite(SCOL[kind], cell)
    for x, y in pts:
        place(cv, b, cx + (x - ox + 0.5) * cell, cy + (y - oy + 0.5) * cell, alpha)


def rain(cv, lt, seed=1, n=9, alpha=0.55, y0=300, y1=1250):
    """Фон-дождь из фигур, медленно падают."""
    kinds = list(SHAPES)
    for i in range(n):
        k = kinds[(i * 3 + seed) % 7]
        x = 120 + ((i * 397 + seed * 131) % 840)
        sp = 70 + (i * 37) % 60
        y = y0 + ((lt * sp + i * 173 + seed * 50) % (y1 - y0))
        draw_piece(cv, k, x, y, cell=34, alpha=alpha, rot=i)


def terminal(lt):
    w, h = 820, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w - 20, h - 60), 26, fill=(196, 188, 170, 255), outline=(240, 236, 220, 255), width=5)
    d.rounded_rectangle((60, 60, w - 60, h - 110), 18, fill=(8, 22, 12, 255))
    d.rectangle((w / 2 - 70, h - 60, w / 2 + 70, h - 30), fill=(150, 144, 130, 255))
    f = M.font("DejaVuSansMono-Bold.ttf", 34) if os.path.exists(f"{M.FD}/DejaVuSansMono-Bold.ttf") else \
        M.font("Montserrat-ExtraBold.ttf", 30)
    rows = 9
    fall = int(lt * 3) % rows
    for r in range(rows):
        y = 80 + r * 38
        line = "<!" + " . " * 8 + "!>"
        if r == rows - 1:
            line = "<!" + "[][][][][][][][]"[:24].ljust(24) + "!>"
        d.text((90, y), line, font=f, fill=TERM + (220,))
    d.text((90 + 4 * 30, 80 + fall * 38), "[][][]", font=f, fill=TERM + (255,))
    g = im.filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(im)
    return out


def well(lt, clear_t):
    """Стакан: внизу почти полный ряд, падает I и закрывает его; ряд вспыхивает и исчезает."""
    cw, ch, cell = 10, 12, 52
    w, h = cw * cell + 40, ch * cell + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((14, 14, w - 14, h - 14), outline=CYAN + (220,), width=4)
    base = [(x, ch - 1) for x in range(cw) if x not in (3, 4, 5, 6)] + [(x, ch - 2) for x in (0, 1, 7, 8, 9)]
    cols = [CYAN, GOLD, PURPLE, ORANGE, GREEN, RED, PINK]
    flash = clear_t <= lt < clear_t + 0.5
    gone = lt >= clear_t + 0.5
    for i, (x, y) in enumerate(base):
        if gone and y == ch - 1:
            continue
        yy = y + (1 if gone else 0)
        c = WHITE if (flash and y == ch - 1) else cols[i % 7]
        b = block_sprite(c, cell)
        im.alpha_composite(b, (int(20 + x * cell - 20), int(20 + yy * cell - 20)))
    if not gone:
        fy = min(ch - 1, (lt / max(clear_t, 0.1)) * (ch - 1))
        for x in (3, 4, 5, 6):
            b = block_sprite(CYAN, cell)
            im.alpha_composite(b, (int(20 + x * cell - 20), int(20 + fy * cell - 20)))
    return im


def floppy(col):
    key = ("flop", col)
    if key in M.CACHE:
        return M.CACHE[key]
    w = 150
    im = Image.new("RGBA", (w + 40, w + 40), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rectangle((20, 20, 20 + w, 20 + w), fill=col + (160,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.polygon(((20, 20), (20 + w - 24, 20), (20 + w, 44), (20 + w, 20 + w), (20, 20 + w)), fill=(28, 24, 46, 255),
              outline=col + (255,))
    d.rectangle((50, 20, 20 + w - 40, 70), fill=(190, 190, 205, 255))
    d.rectangle((90, 28, 108, 62), fill=(28, 24, 46, 255))
    d.rectangle((40, 100, 20 + w - 20, 20 + w - 8), fill=(235, 232, 220, 255))
    d.line((50, 120, 150, 120), fill=col + (255,), width=4)
    M.CACHE[key] = im
    return im


def gameboy(lt):
    w, h = 520, 820
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((30, 30, w - 30, h - 30), 40, fill=PINK + (120,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, w - 30, h - 30), 40, fill=(200, 200, 194, 255), outline=(235, 235, 230, 255), width=5)
    d.rounded_rectangle((70, 80, w - 70, 420), 22, fill=(90, 90, 110, 255))
    sx0, sy0, sx1, sy1 = 120, 120, w - 120, 380
    d.rectangle((sx0, sy0, sx1, sy1), fill=(150, 172, 60, 255))
    cell = 26
    for x in range(int((sx1 - sx0) / cell)):
        if x % 5 != 2:
            d.rectangle((sx0 + x * cell + 2, sy1 - cell, sx0 + (x + 1) * cell - 2, sy1 - 2), fill=(40, 60, 20, 255))
    fy = sy0 + ((lt * 90) % (sy1 - sy0 - 2 * cell))
    for dx in range(3):
        d.rectangle((sx0 + (3 + dx) * cell + 2, fy, sx0 + (4 + dx) * cell - 2, fy + cell - 4), fill=(40, 60, 20, 255))
    d.rectangle((sx0 + 4 * cell + 2, fy + cell, sx0 + 5 * cell - 2, fy + 2 * cell - 4), fill=(40, 60, 20, 255))
    cx, cy = 140, 560
    d.rectangle((cx - 60, cy - 20, cx + 60, cy + 20), fill=(30, 30, 40, 255))
    d.rectangle((cx - 20, cy - 60, cx + 20, cy + 60), fill=(30, 30, 40, 255))
    for bx, by in ((w - 170, 580), (w - 100, 530)):
        d.ellipse((bx - 34, by - 34, bx + 34, by + 34), fill=(150, 30, 80, 255))
    for i in range(2):
        d.rounded_rectangle((180 + i * 100, 680, 250 + i * 100, 700), 10, fill=(120, 120, 128, 255))
    return im


def stamp_sprite(text, col):
    key = ("stamp", text, col)
    if key in M.CACHE:
        return M.CACHE[key]
    f = M.font("Unbounded-Black.ttf", 56)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d0.textlength(text, font=f)
    w, h = int(tw + 90), 150
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, w - 10, h - 10), 18, outline=col + (255,), width=10)
    d.text((w / 2, h / 2), text, font=f, fill=col + (255,), anchor="mm")
    im = im.rotate(-8, expand=True, resample=Image.BICUBIC)
    M.CACHE[key] = im
    return im


def tower(lt):
    """Башня из фигур растёт снизу."""
    w, h = 700, 820
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    seq = [("I", 350, 780, 0), ("O", 230, 700, 0), ("T", 470, 700, 2), ("L", 330, 620, 1), ("S", 470, 600, 0),
           ("J", 220, 560, 0), ("Z", 380, 500, 0), ("I", 350, 420, 0), ("T", 260, 340, 0), ("O", 450, 330, 0)]
    for i, (k, x, y, r) in enumerate(seq):
        a = ease((lt - i * 0.25) / 0.3)
        if a > 0:
            draw_piece(im, k, x, y - (1 - a) * 120, cell=44, alpha=a, rot=r)
    return im


def build_acts():
    at = M.at
    T = {"hook": 0.0}
    T["y1984"] = at("Москва")
    T["comp"] = at("Алексей")
    T["game"] = at("И он придумывает")
    T["row"] = at("Собери")
    T["name"] = at("Тетра")
    T["copy"] = at("Коллеги")
    T["world"] = at("Потом")
    T["rights"] = at("Но все права")
    T["gb"] = at("Nintendo", T["rights"]) if any(M.norm(w) == "nintendo" for w, _, _ in M.WORDS) else at("выпускает")
    T["y1989"] = T["gb"] - 1.6
    T["box"] = at("кладёт")
    T["count"] = at("Больше тридцати")
    T["zero"] = at("А Пажитнов")
    T["y1996"] = at("Только в")
    T["legend"] = at("Сегодня")
    T["next"] = at("Какую игру")
    T["write"] = at("Пиши")
    T["empty"] = T["prime"] = 1e9
    T["england"] = at("Англия")
    T["usa"] = at("Америка")
    return T


ACTS = ["hook", "y1984", "comp", "game", "name", "copy", "world", "rights", "y1989", "count", "zero", "y1996",
        "legend", "next"]
DATES = {"hook": "1984", "y1984": "1984", "comp": "1984", "game": "06.1984", "name": "1984", "copy": "1985",
         "world": "1986 – 1988", "rights": "1988", "y1989": "1989", "count": "1989 →", "zero": "1989", "y1996": "1996",
         "legend": "20XX", "next": "20XX"}


def draw_act(cv, name, lt, T, t):
    st = T[name]
    if name == "hook":
        rain(cv, lt, seed=1, n=11, alpha=0.5)
        appear(cv, neon_text("ТЕТРИС", 150, CYAN), 540, 520, lt, 0.0, kind="flicker")
        appear(cv, neon_text("ИГРАЛ ВЕСЬ МИР", 64, PINK), 545, 660, lt, 0.3, kind="flicker")
        appear(cv, pill("АВТОР ПОЛУЧИЛ: 0 ₽", GOLD, 38), 540, 820, lt, max(0.6, M.at("советский") - st), kind="pop")
    elif name == "y1984":
        appear(cv, pill("ВЦ АКАДЕМИИ НАУК СССР", CYAN, 32), 540, 500, lt, 0.0, kind="pop")
        k = ease(lt / 0.7)
        appear(cv, neon_text(str(int(round(1970 + 14 * k))), 220, GOLD, skew=0), 540, 720, lt, 0.05, kind="fade")
        appear(cv, plain_text("МОСКВА", 50, WHITE), 540, 900, lt, 0.5, kind="rise")
    elif name == "comp":
        appear(cv, pill("«ЭЛЕКТРОНИКА-60»", GOLD, 34), 540, 420, lt, 0.0, kind="pop")
        place(cv, terminal(lt), 540, 780, min(1, lt / 0.3), 0.92 + 0.08 * ease(lt / 0.5))
        appear(cv, plain_text("ни цвета · ни графики", 40, (200, 190, 220), "Montserrat-Bold.ttf"), 540, 1110, lt,
               M.at("Ни цвета") - st, kind="rise")
    elif name == "game":
        appear(cv, neon_text("ФИГУРЫ ИЗ 4 КВАДРАТОВ", 54, PINK), 540, 410, lt, 0.0, kind="flicker")
        place(cv, well(lt, T["row"] - st + 1.4), 540, 830, min(1, lt / 0.3))
        if T["row"] - st + 1.4 <= lt:
            appear(cv, pill("РЯД СОБРАН!", GREEN, 34), 540, 520, lt, T["row"] - st + 1.4, kind="pop")
    elif name == "name":
        rain(cv, lt, seed=3, n=7, alpha=0.35)
        appear(cv, neon_text("ТЕТРА", 96, CYAN), 540, 480, lt, 0.0, kind="flicker")
        appear(cv, plain_text("= четыре", 44, WHITE), 540, 570, lt, 0.4, kind="rise")
        appear(cv, neon_text("+ ТЕННИС", 96, GOLD), 540, 700, lt, M.at("Плюс теннис") - st, kind="flicker")
        appear(cv, neon_text("ТЕТРИС", 140, PINK), 540, 900, lt, M.at("Тетрис", T["name"] + 1) - st, kind="pop")
    elif name == "copy":
        appear(cv, pill("КОПИЯ НА ДИСКЕТУ", CYAN, 34), 540, 420, lt, 0.0, kind="pop")
        n = min(9, 1 + int(lt * 2.2))
        cols = [CYAN, PINK, GOLD, GREEN, PURPLE]
        for i in range(n):
            ang = i / 9 * 2 * math.pi + 0.4
            r = 0 if i == 0 else 260 * ease((lt - i / 2.2) / 0.5)
            place(cv, floppy(cols[i % 5]), 540 + r * math.cos(ang), 820 + r * 0.8 * math.sin(ang), 1.0, 0.9)
        appear(cv, neon_text("ПО ВСЕМУ СОЮЗУ", 60, PINK), 540, 1180, lt, M.at("и она") - st, kind="flicker")
    elif name == "world":
        rain(cv, lt, seed=5, n=6, alpha=0.3)
        steps = [("СССР", CYAN, 0.0), ("ВЕНГРИЯ", GREEN, 0.3), ("АНГЛИЯ", GOLD, T["england"] - st),
                 ("США", PINK, T["usa"] - st)]
        for i, (txt, col, t0) in enumerate(steps):
            y = 470 + i * 170
            appear(cv, bubble(txt, col), 540, y, lt, t0, kind="pop")
            if i and lt > t0:
                appear(cv, plain_text("↓", 46, WHITE, "DejaVuSans-Bold.ttf" if os.path.exists(
                    f"{M.FD}/DejaVuSans-Bold.ttf") else "Montserrat-ExtraBold.ttf"), 540, y - 85, lt, t0, kind="fade")
    elif name == "rights":
        cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
        appear(cv, neon_text("ВСЕ ПРАВА", 96, WHITE, glow=0.4), 540, 560, lt, 0.0, kind="flicker")
        appear(cv, stamp_sprite("ГОСУДАРСТВУ", RED), 540, 800, lt, M.at("государству") - st, kind="pop")
        f = lt - (M.at("государству") - st)
        if 0 < f < 0.25:
            cv.alpha_composite(Image.new("RGBA", (W, H), RED + (int(80 * (1 - f / 0.25)),)))
    elif name == "y1989":
        appear(cv, pill("NINTENDO · США", RED, 34, WHITE), 540, 410, lt, 0.0, kind="pop")
        appear(cv, neon_text("1989", 120, GOLD, skew=0), 540, 530, lt, 0.1, kind="pop")
        place(cv, gameboy(lt), 540, 930, min(1, lt / 0.3), 0.75 + 0.1 * ease(lt / 0.6))
        if t >= T["box"]:
            appear(cv, pill("ТЕТРИС — В КАЖДОЙ КОРОБКЕ", GOLD, 32), 540, 1250, lt, T["box"] - st, kind="pop")
    elif name == "count":
        rain(cv, lt, seed=7, n=12, alpha=0.6)
        k = ease(lt / 1.4)
        v = int(35_000_000 * k)
        s = f"{v:,}".replace(",", " ")
        appear(cv, neon_text(s, 96, GOLD, skew=0), 540, 680, lt, 0.0, kind="fade")
        appear(cv, plain_text("КОПИЙ", 60, WHITE), 540, 820, lt, 0.3, kind="rise")
    elif name == "zero":
        cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 110)))
        appear(cv, plain_text("А ПАЖИТНОВ?", 64, (210, 200, 230)), 540, 500, lt, 0.0, kind="rise")
        appear(cv, neon_text("0", 300, RED, skew=0), 540, 760, lt, M.at("Ноль") - st, kind="pop")
        appear(cv, plain_text("ни рубля · ни доллара", 44, WHITE, "Montserrat-Bold.ttf"), 540, 980, lt,
               M.at("Ни рубля") - st, kind="rise")
    elif name == "y1996":
        appear(cv, neon_text("1996", 170, GOLD, skew=0), 540, 560, lt, 0.0, kind="pop")
        appear(cv, pill("ПРАВА ВЕРНУЛИСЬ К АВТОРУ", GREEN, 34), 540, 740, lt, M.at("вернул") - st, kind="pop")
        appear(cv, neon_text("12 ЛЕТ СПУСТЯ", 70, CYAN), 540, 900, lt, M.at("Через") - st, kind="flicker")
    elif name == "legend":
        place(cv, tower(lt), 540, 940, 1.0)
        appear(cv, neon_text("ОДНА ИЗ САМЫХ", 62, CYAN), 540, 420, lt, 0.0, kind="flicker")
        appear(cv, neon_text("ПРОДАВАЕМЫХ ИГР", 62, PINK), 545, 510, lt, 0.2, kind="flicker")
    elif name == "next":
        rain(cv, lt, seed=9, n=8, alpha=0.4)
        appear(cv, neon_text("КАКУЮ ИГРУ", 96, PINK), 540, 500, lt, 0.0, kind="flicker")
        appear(cv, neon_text("СЛЕДУЮЩЕЙ?", 80, CYAN), 545, 610, lt, 0.2, kind="flicker")
        appear(cv, bubble("ДЕНДИ?", GOLD), 360, 800, lt, 0.7, kind="pop")
        appear(cv, bubble("ТАМАГОЧИ?", GREEN), 730, 800, lt, 1.1, kind="pop")
        appear(cv, pill("ПИШИ В КОММЕНТАРИЯХ", GOLD, 34), 540, 1000, lt, T["write"] - st, kind="pop")


M.ACTS, M.DATES, M.draw_act, M.build_acts = ACTS, DATES, draw_act, build_acts
M.HOTWORDS = {"тетрис", "весь", "мир", "копейки", "академии", "пажитнов", "электроника60", "скобки", "четырёх",
              "четырех", "ряд", "исчезнет", "тетра", "четыре", "теннис", "дискеты", "союзу", "венгрия", "англия",
              "америка", "государству", "nintendo", "game", "boy", "коробку", "миллионов", "копий", "ноль",
              "доллара", "права", "двенадцать", "истории", "детства", "комментариях", "восемьдесят", "девяносто"}
M.REDWORDS = {"копейки", "государству", "ноль", "доллара"}


def main():
    os.makedirs(M.TMP, exist_ok=True)
    M.WORDS, _ = M.timed()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                           "csv=p=0", M.AUDIO]).decode()) + 0.4
    T = build_acts()
    order = [T[a] for a in ACTS]
    assert order == sorted(order), ("сцены не по порядку", {a: round(T[a], 2) for a in ACTS})
    for a, b in zip(ACTS, ACTS[1:]):
        assert T[b] - T[a] >= 1.8, ("сцена мелькает", a, T[b] - T[a])
    subs = M.sub_chunks()
    json.dump({"T": T, "subs": subs}, open(f"{M.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)
    bg, wins = M.build_background()
    wl = M.window_layers(wins)
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        for tt in sys.argv[2].split(","):
            M.render_frame(float(tt), T, total, bg, wl, subs).save(f"{M.TMP}/prev-{float(tt):05.1f}.jpg", quality=88)
        return
    audio = f"{M.TMP}/mix.wav"
    ev = [(T[a], "whoosh", 0.3) for a in ACTS[1:]]
    ev += [(T["row"] + 1.4, "ding", 0.5), (M.at("Тетрис", T["name"] + 1), "hit", 0.5),
           (M.at("государству"), "stamp", 0.6), (T["box"], "pop", 0.45), (T["count"], "riser", 0.35),
           (M.at("Ноль"), "hit", 0.6), (M.at("вернул"), "chime", 0.45)]
    pad = f"{M.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", M.AUDIO, "-af", "apad=pad_dur=0.4", "-ar", "48000", pad],
                   check=True)
    SFX.mix(pad, ev, audio, f"{M.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))
    n = int(total * M.FPS)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                          str(M.FPS), "-i", "-", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                          "-preset", "medium", "-crf", "19", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt",
                          "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", M.OUT],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(M.render_frame(i / M.FPS, T, total, bg, wl, subs).tobytes())
        if i % 300 == 0:
            print(f"{i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print(M.OUT, f"{total:.1f} c")


if __name__ == "__main__":
    main()
