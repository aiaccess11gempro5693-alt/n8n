"""
Статичное превью presentation-слоя — БЕЗ полного рендера видео (design-
system.md, "14. После реализации... сначала preview"). Берёт один кадр
аватара из уже готового /tmp/final-scenes/scene-N.mp4, накладывает ВСЕ
слои сцены разом (игнорируя тайминг — это geometry-проверка, не финальная
анимация) и сохраняет PNG для визуальной проверки.
"""
import os
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from presentation.compose_scene import compose_scene  # noqa: E402

OUT_DIR = "/tmp/presentation-preview"
FINAL_SCENES = "/tmp/final-scenes"
FRAME_AT = {1: 3.0, 2: 5.0, 3: 21.5, 5: 20.5, 6: 18.0}  # момент, когда видно максимум слоёв сцены


def grab_frame(scene_n, t, out_path):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(t), "-i", f"{FINAL_SCENES}/scene-{scene_n}.mp4",
         "-frames:v", "1", out_path, "-loglevel", "error"],
        check=True,
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for scene_n, t in FRAME_AT.items():
        frame_path = f"{OUT_DIR}/scene{scene_n}-raw.png"
        grab_frame(scene_n, t, frame_path)
        base = Image.open(frame_path).convert("RGBA")

        layout, layers = compose_scene(scene_n)
        print(f"scene {scene_n}: layout={layout}, layers={len(layers)}")
        for l in layers:
            base.alpha_composite(l.image, (l.x, l.y))
            print(f"  - {l.image.width}x{l.image.height} at ({l.x},{l.y}) start={l.start} end={l.end}")

        out_path = f"{OUT_DIR}/scene{scene_n}-preview.png"
        base.convert("RGB").save(out_path)
        print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
