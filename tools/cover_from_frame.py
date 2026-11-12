"""Обложка Reels кодом — без нейросети (экономия CometAPI).

Кадр из готового ролика (или любая картинка) + заголовок крупными буквами.
Заголовок кладётся в зону сетки профиля 3:4 (y 240–1680 из 1920), чтобы не обрезался.

  python3 tools/cover_from_frame.py VIDEO_OR_IMAGE OUT.jpg --t 3.0 \
      --lines "МОЛЧАНИЕ —" "САМЫЙ СИЛЬНЫЙ" "ОТВЕТ" --hot 1 --pos top

--hot   номер строки (с 0), выделенной цветом акцента (можно несколько через запятую)
--pos   top | bottom — где заголовок
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
GRID_TOP, GRID_BOT = 240, 1680
FONT = os.path.join(os.path.dirname(__file__), "..", "render", "fonts", "Montserrat-ExtraBold.ttf")


def load_frame(src, t):
    if src.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return Image.open(src).convert("RGB")
    tmp = tempfile.mktemp(suffix=".png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", tmp], check=True)
    return Image.open(tmp).convert("RGB")


def cover_fill(im):
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def fit_font(draw, lines, maxw, start=150):
    size = start
    while size > 40:
        f = ImageFont.truetype(FONT, size)
        if all(draw.textlength(l, font=f) <= maxw for l in lines):
            return f
        size -= 4
    return ImageFont.truetype(FONT, 40)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--t", type=float, default=2.0)
    ap.add_argument("--lines", nargs="+", required=True)
    ap.add_argument("--hot", default="")
    ap.add_argument("--pos", default="top")
    ap.add_argument("--accent", default="#FFC93C")
    a = ap.parse_args()

    img = cover_fill(load_frame(a.src, a.t))
    hot = {int(x) for x in a.hot.split(",") if x != ""}
    d = ImageDraw.Draw(img)
    f = fit_font(d, a.lines, W - 120)
    lh = int(f.size * 1.12)
    block = lh * len(a.lines)
    y0 = GRID_TOP + 90 if a.pos == "top" else GRID_BOT - 120 - block

    # затемнение под текстом — мягкий градиент, не рамка
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    pad = 160
    top, bot = max(0, y0 - pad), min(H, y0 + block + pad)
    for yy in range(top, bot):
        edge = min(yy - top, bot - yy)
        sd.line([(0, yy), (W, yy)], fill=int(170 * min(1, edge / pad)))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(dark, img, shade)

    # тень текста
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdd = ImageDraw.Draw(sh)
    for i, line in enumerate(a.lines):
        tw = sdd.textlength(line, font=f)
        sdd.text(((W - tw) / 2 + 4, y0 + i * lh + 6), line, font=f, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img.convert("RGBA"), sh)

    d = ImageDraw.Draw(img)
    for i, line in enumerate(a.lines):
        tw = d.textlength(line, font=f)
        d.text(((W - tw) / 2, y0 + i * lh), line, font=f, fill=a.accent if i in hot else "#FFFFFF")
    img.convert("RGB").save(a.out, quality=92)
    # превью сетки 3:4
    img.convert("RGB").crop((0, GRID_TOP, W, GRID_BOT)).resize((360, 480)).save(
        os.path.join(tempfile.gettempdir(), os.path.basename(os.path.splitext(a.out)[0]) + "-grid.jpg"))
    print(a.out)


if __name__ == "__main__":
    main()
