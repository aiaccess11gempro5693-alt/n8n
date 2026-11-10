"""Обложка Reels №35 «Тетрис» — неон на ночном городе, рисуется кодом.
Заголовок в зоне 3:4 сетки профиля (y 240–1680).

python3 render/landing/build_ig35_cover.py → docs/landing/insta/covers/ig35-cover.jpg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig35 as T  # noqa: E402

M = T.M
OUT = f"{M.ROOT}/docs/landing/insta/covers/ig35-cover.jpg"


def main():
    bg, wins = M.build_background()
    cv = bg.copy()
    cv.alpha_composite(M.window_layers(wins, 1)[0])
    for kind, x, y, rot in (("I", 110, 1150, 0), ("T", 920, 380, 0), ("L", 110, 900, 2), ("S", 960, 950, 1),
                            ("O", 170, 1330, 0), ("Z", 900, 1420, 0)):
        T.draw_piece(cv, kind, x, y, cell=48, alpha=0.75, rot=rot)
    M.place(cv, M.neon_text("ТЕТРИС", 170, M.CYAN), 540, 470)
    M.place(cv, M.neon_text("ИГРАЛ ВЕСЬ МИР", 74, M.PINK), 545, 630)
    M.place(cv, T.gameboy(5.0), 540, 1060, scale=0.68)
    M.place(cv, M.neon_text("АВТОРУ — 0", 96, M.GOLD, skew=0), 540, 1480)
    cv.alpha_composite(M.frame_ui("1984"))
    cv.convert("RGB").save(OUT, quality=92)
    print(OUT)


if __name__ == "__main__":
    main()
