"""История России №2 «Часы» — новая обложка (02.11 первая была почти как у №1, пост удалён).

По правилу серии (docs/scenarios/history/README.md, п.9): главное — настоящая картинка темы
(фото Спасской башни с Wikimedia Commons), дедушки нет, раскладка и цвет заголовка другие, чем у №1
(там — дедушка крупно и белый заголовок по центру): здесь башня на весь кадр, заголовок внизу,
золотом на тёмно-синей подложке, сверху над часами — маленький «циферблат» из ролика.

python3 render/landing/build_hist02_cover2.py → docs/landing/insta/covers/hist02-cover-v2.jpg
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hist02 as C

ROOT = C.ROOT
W, H = 1080, 1920
SERIF = f"{ROOT}/render/fonts/PlayfairDisplay-Bold.ttf"
OUT = f"{ROOT}/docs/landing/insta/covers/hist02-cover-v2.jpg"
GOLD = (226, 184, 92)


def main():
    im = Image.open(f"{C.WEB}/tower_1.jpg").convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x0 = (im.width - W) // 2
    im = im.crop((x0, im.height - H, x0 + W, im.height)).convert("RGBA")
    # тёмно-синий градиент снизу под заголовок
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grad)
    for y in range(1050, H):
        a = min(235, int((y - 1050) / 420 * 235))
        g.line([(0, y), (W, y)], fill=(14, 22, 48, a))
    im.alpha_composite(grad)
    d = ImageDraw.Draw(im)
    f1, f2 = ImageFont.truetype(SERIF, 112), ImageFont.truetype(SERIF, 46)
    lines = ["ЧАСЫ, ГДЕ", "КРУТИЛСЯ", "ЦИФЕРБЛАТ"]
    y = 1235
    for ln in lines:
        d.text((W / 2 + 4, y + 5), ln, font=f1, fill=(0, 0, 0, 160), anchor="mm")
        d.text((W / 2, y), ln, font=f1, fill=GOLD, anchor="mm")
        y += 122
    d.line([(W / 2 - 170, y - 34), (W / 2 + 170, y - 34)], fill=GOLD, width=4)
    d.text((W / 2, y + 22), "Спасская башня · 1625 год", font=f2, fill=(240, 232, 214), anchor="mm")
    assert 240 <= 1235 - 60 and y + 50 <= 1680, "заголовок вне зоны 3:4 сетки профиля"
    im.convert("RGB").save(OUT, quality=92)
    print(OUT)


if __name__ == "__main__":
    main()
