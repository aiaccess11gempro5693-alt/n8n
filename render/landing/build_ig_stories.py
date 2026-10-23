"""Истории Instagram для «Актуального» (`iiavatar.video`) в стиле серии Reels
(render/landing/theme_brand.py): графит, оранжевый, Oswald + Montserrat.

Текстовые истории рисуются кодом (точный текст без ошибок), примеры — готовые
вертикальные ролики. Безопасная зона историй: сверху и снизу по 250 px под
интерфейс Instagram — там ничего важного.

Запуск:  python3 -m render.landing.build_ig_stories
Выход:   docs/landing/insta/stories/*.jpg
"""
import os

from PIL import Image, ImageDraw

from render.landing import theme_brand as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = f"{ROOT}/docs/landing/insta/stories"
TMP = f"{ROOT}/render/landing/_frames_stories"
W, H = 1080, 1920
SAFE_TOP, SAFE_BOTTOM = 260, 1660


def p(name):
    return f"{TMP}/{name}.png"


def paste(bg, png, x, y):
    im = Image.open(png).convert("RGBA")
    if x == "c":
        x = (W - im.width) // 2
    bg.alpha_composite(im, (int(x), int(y)))
    return y + im.height


def text_block(path, lines, w=960, size=54, color=T.WHITE, lh=1.3, font=None):
    f = T.font(font or T.F_BODY, size)
    out = list(lines)   # строки задаются вручную — без автопереноса
    h = int(len(out) * size * lh) + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    for line in out:
        d.text(((w - T.tw(line, f)) / 2, y), line, font=f, fill=color)
        y += int(size * lh)
    im.save(path)
    return path


def steps_card(path, items, w=960):
    """Нумерованные шаги 01–04 на тёмной карточке."""
    fn, ft = T.font(T.F_HEAD, 70), T.font(T.F_BODY, 46)
    row = 170
    h = 50 + len(items) * row
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=T.CARD, outline=(243, 83, 27, 120), width=3)
    y = 40
    for i, (title, sub) in enumerate(items):
        d.rounded_rectangle([36, y + 8, 146, y + 118], radius=24, fill=T.ORANGE)
        num = f"0{i + 1}"
        nb = T.tbox(num, fn)
        d.text((91 - (nb[2] - nb[0]) / 2 - nb[0], y + 63 - (nb[3] - nb[1]) / 2 - nb[1]), num, font=fn, fill=T.WHITE)
        d.text((180, y + 10), title, font=ft, fill=T.WHITE)
        d.text((180, y + 70), sub, font=T.font(T.F_BODY_S, 36), fill=T.GREY)
        y += row
    return T._save(T._shadow(im, blur=18, k=0.6), path)


def price_card(path, label, price, unit, w=960):
    """Карточка цены: подпись, крупная оранжевая цена, единица."""
    fl, fp, fu = T.font(T.F_BODY, 46), T.font(T.F_HEAD, 190), T.font(T.F_BODY, 46)
    h = 420
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=40, fill=T.CARD, outline=(243, 83, 27, 160), width=4)
    d.text(((w - T.tw(label, fl)) / 2, 40), label, font=fl, fill=T.GREY)
    bb = T.tbox(price, fp)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], 120 - bb[1]), price, font=fp, fill=T.ORANGE)
    d.text(((w - T.tw(unit, fu)) / 2, 120 + (bb[3] - bb[1]) + 40), unit, font=fu, fill=T.WHITE)
    return T._save(T._shadow(im, blur=18, k=0.6), path)


def chips(path, words, w=960):
    """Строка тегов «что входит»."""
    f = T.font(T.F_BODY, 40)
    rows, cur, cw = [], [], 0
    for wd in words:
        ww = T.tw(wd, f) + 64
        if cur and cw + ww > w:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(wd)
        cw += ww + 16
    rows.append(cur)
    h = len(rows) * 96
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    for r in rows:
        tot = sum(T.tw(x, f) + 64 for x in r) + 16 * (len(r) - 1)
        x = (w - tot) / 2
        for wd in r:
            ww = T.tw(wd, f) + 64
            d.rounded_rectangle([x, y, x + ww, y + 76], radius=38, fill=(34, 36, 34, 245),
                                outline=(90, 92, 88, 255), width=2)
            d.text((x + 32, y + 16), wd, font=f, fill=T.WHITE)
            x += ww + 16
        y += 96
    im.save(path)
    return path


def canvas(variant="grid"):
    T.background(p(f"bg_{variant}"), W, H, variant)
    return Image.open(p(f"bg_{variant}")).convert("RGBA")


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/{name}.jpg"
    im.convert("RGB").save(path, quality=92)
    print(path)
    return path


def compose(name, variant, blocks):
    """Блоки (png, x, отступ сверху) стопкой, по центру безопасной зоны историй."""
    im = canvas(variant)
    hs = [Image.open(b[0]).height + b[2] for b in blocks]
    y = SAFE_TOP + max(0, (SAFE_BOTTOM - SAFE_TOP - sum(hs)) // 2)
    for (png, x, gap), h in zip(blocks, hs):
        paste(im, png, x, y + gap)
        y += h
    if y > SAFE_BOTTOM + 40:
        raise SystemExit(f"{name}: не помещается в безопасную зону ({y})")
    return save(im, name)


def main():
    os.makedirs(TMP, exist_ok=True)
    compose("prices-1", "grid", [
        (T.tag(p("t_price"), "Цены", 54), "c", 0),
        (T.headline(p("h_price"), [[("Ролик с", "w"), ("ИИ-ведущим", "box")]], 1000, size=96), 40, 20),
        (price_card(p("pc1"), "от", "1 000 ₽", "за минуту видео"), 40, 10),
        (chips(p("ch1"), ["сценарий", "ведущий", "живая озвучка", "монтаж", "субтитры", "музыка"]), 60, 30),
        (text_block(p("tb1"), ["Готово от 1 дня"], size=58, color=T.ORANGE, font=T.F_HEAD), 60, 30),
    ])
    compose("prices-2", "grid", [
        (T.tag(p("t_price2"), "Для компаний", 54), "c", 0),
        (T.headline(p("h_gen"), [[("Свой генератор", "w")], [("видео", "box"), ("под ключ", "w")]], 1000, size=96), 40, 20),
        (price_card(p("pc2"), "от", "100 000 ₽", "зависит от сложности"), 40, 10),
        (text_block(p("tb2"), ["Вы загружаете текст — система", "сама делает ролик с ведущим,", "озвучкой и монтажом.",
                               "Работаете за свои токены."], size=46), 60, 40),
    ])
    compose("order-1", "plain", [
        (T.tag(p("t_order"), "Как заказать", 54), "c", 0),
        (steps_card(p("steps"), [
            ("Пишете в директ", "тема, длина, формат"),
            ("Сценарий и ведущий", "напишем текст, подберём лицо"),
            ("Голос и монтаж", "озвучка, графика, субтитры"),
            ("Готовый ролик", "от 1 дня, одна правка бесплатно"),
        ]), 30, 30),
        (T.headline(p("h_cta"), [[("Напишите", "w"), ("«ВИДЕО»", "box")], [("в директ", "w")]], 1000, size=96), 40, 30),
    ])
    compose("langs-1", "grid", [
        (T.tag(p("t_lang"), "Языки", 54), "c", 0),
        (T.big_number(p("n30"), "30+", [[("языков", "w")], [("в одном ролике", "box")]], 1000, size=520), 40, 10),
        (text_block(p("tb3"), ["Тот же голос, та же мимика.", "Для филиалов, партнёров", "и зарубежных клиентов."],
                    size=46), 60, 20),
    ])


if __name__ == "__main__":
    main()
