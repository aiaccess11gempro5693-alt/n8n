"""Обложка Reels №32 «Прайм Москвы» — в стиле самого ролика (неон на ночном городе), рисуется кодом.
Заголовок в зоне 3:4 сетки профиля (y 240–1680).

python3 render/landing/build_ig32_cover.py → docs/landing/insta/covers/ig32-cover.jpg
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig32 as M  # noqa: E402

OUT = f"{M.ROOT}/docs/landing/insta/covers/ig32-cover.jpg"


def main():
    bg, wins = M.build_background()
    cv = bg.copy()
    cv.alpha_composite(M.window_layers(wins, 1)[0])
    M.place(cv, M.towers(1.0), 540, 1290, 0.9)
    M.place(cv, M.neon_text("МОСКВА", 150, M.PINK), 540, 430)
    M.place(cv, M.neon_text("НИКОГДА НЕ СПАЛА", 72, M.CYAN), 545, 570)
    M.place(cv, M.neon_text("2007", 260, M.GOLD, skew=0), 540, 790)
    M.place(cv, M.pill("ПРАЙМ МОСКВЫ · 1998 – 2008", M.GOLD, 40), 540, 1530)
    cv.alpha_composite(M.frame_ui("2007"))
    cv.convert("RGB").save(OUT, quality=92)
    print(OUT)


if __name__ == "__main__":
    main()
