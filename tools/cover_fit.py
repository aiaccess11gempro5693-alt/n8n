"""Подгонка обложек от gpt-image-2 под форматы сайта.

gpt-image-2 отдаёт 3:2 (1536×1024) и 2:3 (1024×1536):
  16:9 — кадрирование по высоте (сверху 35 % лишнего, снизу 65 %) → 1920×1080;
  9:16 — картинка во всю ширину, сверху и снизу — размытое продолжение фона → 1080×1920.

python3 tools/cover_fit.py scratch/img/cover_x_16x9.png out.jpg 16:9
"""
import sys

from PIL import Image, ImageFilter


def fit(src, dst, aspect):
    im = Image.open(src).convert("RGB")
    if aspect == "16:9":
        w, h = im.size
        th = int(w * 9 / 16)
        top = int((h - th) * 0.35)
        im.crop((0, top, w, top + th)).resize((1920, 1080), Image.LANCZOS).save(dst, quality=90)
        return
    W, H = 1080, 1920
    fg = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    bg = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(28))
    bg.paste(fg, (0, (H - fg.height) // 2))
    bg.save(dst, quality=90)


if __name__ == "__main__":
    fit(*sys.argv[1:4])
