"""Универсальная "плашка" — фон/карточка на освободившемся месте, когда
аватар уехал в угол (23.09.2026, прямое ТЗ с созвона). Рисуется через
PIL как PNG (та же техника, что в render/visual/components.py), потом
накладывается ffmpeg-оверлеем поверх фона в build_scenario5.py.

Набор "инструментов" — то, чем можно заполнить плашку (буллиты,
цитата-акцент, крупная цифра). Прямое указание Олега: "не все обязательно
задействовать... в одном ролике 3 каких-то одних инструмента, в другом —
3 других, чтобы не намешивать всё сразу". Этот файл даёт строительные
блоки; какие из них использовать в конкретном ролике — решает сценарий
верхнего уровня (build_scenario5.py и его аналоги для будущих роликов),
не сам этот модуль.
"""
import os
from PIL import Image, ImageDraw

from . import brand_style as S
from . import geometry as G

CARD_RADIUS = 28
CARD_PAD = 40


def _new_canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def render_bullet_card(title, bullets, width=None, out_path=None):
    """Карточка: киккер-заголовок (синий, uppercase) + список буллитов с
    зелёным маркером-точкой. width по умолчанию — вся ширина PLASHKA_ZONE."""
    width = width or (G.PLASHKA_ZONE["x1"] - G.PLASHKA_ZONE["x0"])
    font_title = S.font(S.F_SEMIBOLD, S.SIZE_LABEL)
    font_body = S.font(S.F_MEDIUM, S.SIZE_BODY)

    line_h = S.SIZE_BODY + 22
    height = CARD_PAD * 2 + S.SIZE_LABEL + 24 + line_h * len(bullets)

    img = _new_canvas(width, height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width, height], radius=CARD_RADIUS, fill=S.WHITE)

    tx, ty = CARD_PAD, CARD_PAD
    draw.text((tx, ty), title.upper(), font=font_title, fill=S.BLUE)
    draw.rectangle([tx, ty + S.SIZE_LABEL + 10, tx + 60, ty + S.SIZE_LABEL + 14], fill=S.GREEN)

    by = ty + S.SIZE_LABEL + 34
    for b in bullets:
        cx, cy = tx + 8, by + S.SIZE_BODY // 2 - 4
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=S.GREEN)
        draw.text((tx + 32, by), b, font=font_body, fill=S.TEXT_DARK)
        by += line_h

    if out_path:
        img.save(out_path)
    return img, width, height


def render_quote_card(quote, width=None, out_path=None):
    """Карточка-акцент: одна короткая фраза крупным шрифтом, синяя
    акцентная плашка слева (та же визуальная грамматика, что у буллит-
    карточки, для единообразия внутри ролика)."""
    width = width or (G.PLASHKA_ZONE["x1"] - G.PLASHKA_ZONE["x0"]) // 2
    font_q = S.font(S.F_HEADLINE, S.SIZE_TITLE)

    # простой перенос по словам под ширину карточки
    words = quote.split()
    lines, cur = [], []
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    max_w = width - CARD_PAD * 2 - 24
    for w in words:
        trial = " ".join(cur + [w])
        tw, _ = _text_size(d, trial, font_q)
        if tw <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))

    line_h = S.SIZE_TITLE + 14
    height = CARD_PAD * 2 + line_h * len(lines)
    img = _new_canvas(width, height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width, height], radius=CARD_RADIUS, fill=S.WHITE)
    draw.rectangle([0, 0, 10, height], fill=S.BLUE)

    ty = CARD_PAD
    for line in lines:
        draw.text((CARD_PAD + 24, ty), line, font=font_q, fill=S.TEXT_DARK)
        ty += line_h

    if out_path:
        img.save(out_path)
    return img, width, height
