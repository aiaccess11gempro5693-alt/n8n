import json, subprocess, os

R = os.path.dirname(os.path.abspath(__file__))
SCENES = "/tmp/final-scenes"
ICONS = "/home/user/n8n/scratch"
FONT = f"{R}/fonts/Inter-Bold.otf"
CKEY = "colorkey=0xE91E8F:0.35:0.12"

def dur(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",path],
                          capture_output=True, text=True).stdout.strip()
    return float(out)

def clamp(x, lo, hi):
    return max(lo, min(x, hi))

# each icon: png, x, y, sz, start, label, pill_png, pill_w, pill_h, pill_margin, layout('below'|'beside')
def build_scene(scene_n, icons, pill_start_gap=0.15, slide_icon=40, slide_pill=30):
    IN = f"{SCENES}/scene-{scene_n}.mp4"
    OUT = f"{R}/scene-{scene_n}.mp4"
    D = dur(IN)

    inputs = ["-i", IN]
    for ic in icons:
        inputs += ["-i", ic["png"]]
    for ic in icons:
        inputs += ["-i", ic["pill_png"]]
    n = len(icons)
    # extra transparent lavfi canvas for caption_filter.py's crop-mask karaoke text
    canvas_idx = 1 + 2*n
    inputs += ["-f", "lavfi", "-i", f"color=c=black@0.0:s=1920x1080:r=25:d={D}"]

    fc = []
    for i, ic in enumerate(icons):
        idx = i+1
        inp = f"{idx}:v"
        fc.append(f"[{inp}]scale={ic['sz']}:{ic['sz']},{CKEY},eq=saturation=1.4:contrast=1.1:brightness=0.03,format=rgba,split=2[icon{idx}clean_a][icon{idx}clean_b]")
        fc.append(f"[icon{idx}clean_a]alphaextract,split=2[mask{idx}_a][mask{idx}_b]")
        fc.append(f"[mask{idx}_a]" + ",".join(["dilation"]*7) + f"[mask{idx}_outline]")
        fc.append(f"[mask{idx}_b]" + ",".join(["dilation"]*10) + f",gblur=sigma=6[mask{idx}_shadow]")
        fc.append(f"color=0xFFFFFF:s={ic['sz']}x{ic['sz']}[white{idx}]")
        fc.append(f"[white{idx}][mask{idx}_outline]alphamerge[outline{idx}]")
        fc.append(f"color=0x000000:s={ic['sz']}x{ic['sz']}[black{idx}]")
        fc.append(f"[black{idx}][mask{idx}_shadow]alphamerge,colorchannelmixer=aa=0.45[shadow{idx}]")

    fc.append("[0:v]scale=1920:1080[base]")
    prev = "base"
    for i, ic in enumerate(icons):
        idx = i+1
        X, Y, ST = ic["x"], ic["y"], ic["start"]
        ease = f"max(0,1-(t-{ST})/0.35)"
        nxt = f"s{idx}a"
        fc.append(f"[{prev}][shadow{idx}]overlay=x={X}+10:y='{Y}+14-{slide_icon}*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt
        nxt = f"s{idx}b"
        fc.append(f"[{prev}][outline{idx}]overlay=x={X}:y='{Y}-{slide_icon}*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt
        nxt = f"s{idx}c"
        fc.append(f"[{prev}][icon{idx}clean_b]overlay=x={X}:y='{Y}-{slide_icon}*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt

    for i, ic in enumerate(icons):
        idx = i+1
        pin = f"{n+idx}:v"
        PST = round(ic["start"] + pill_start_gap, 3)
        pease = f"max(0,1-(t-{PST})/0.3)"
        BX, BY, PW, PH = ic["pill_bx"], ic["pill_by"], ic["pill_w"], ic["pill_h"]
        MARGIN = ic["pill_margin"]
        OX, OY = BX - MARGIN, BY - MARGIN
        nxt = f"p{idx}a"
        fc.append(f"[{prev}][{pin}]overlay=x={OX}:y='{OY}-{slide_pill}*{pease}':enable='gte(t,{PST})'[{nxt}]")
        prev = nxt
        nxt = f"p{idx}b"
        label_esc = ic["label"].replace("'", r"\'").replace(":", r"\:")
        fc.append(
            f"[{prev}]drawtext=fontfile={FONT}:fontcolor=white:fontsize={ic['fs']}:text='{label_esc}':"
            f"shadowcolor=black@0.35:shadowx=1:shadowy=1:"
            f"x={BX}+({PW}-text_w)/2:y='{BY}+({PH}-text_h)/2-{slide_pill}*{pease}':"
            f"enable='gte(t,{PST})':alpha='min((t-{PST})/0.25\\,1)'[{nxt}]"
        )
        prev = nxt

    # karaoke subtitle panel — same crop-mask technique / same font (Inter-Bold)
    # as everything else, via the shared caption_filter.py
    cap_out = subprocess.run(
        ["python3", f"{R}/caption_filter.py", str(scene_n), prev, "vout", str(canvas_idx)],
        capture_output=True, text=True
    )
    if cap_out.returncode != 0:
        print("caption_filter.py STDERR:\n", cap_out.stderr[-4000:])
        raise SystemExit(f"caption_filter failed for scene {scene_n}")
    fc.append(cap_out.stdout.strip())

    filter_complex = ";\n".join(fc)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "0:a", "-t", str(D),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "160k",
        OUT
    ]
    print(f"=== rendering scene {scene_n} ({len(icons)} icons), duration {D}s ===")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG STDERR TAIL:\n", r.stderr[-4000:])
        raise SystemExit(f"scene {scene_n} failed")
    print(f"scene {scene_n} OK -> {OUT}")

TEAL = "0x216E71"
CORAL = "0xE05D42"

with open(f"{R}/pills/pill_info.json") as f:
    info = json.load(f)
with open(f"{R}/pills/pill_info5.json") as f:
    info5 = json.load(f)

def below_pos(icon_x, icon_sz, pill_w, gap=30):
    center = icon_x + icon_sz/2
    bx = clamp(center - pill_w/2, 20, 1920-20-pill_w)
    return round(bx)

def beside_pos(icon_x, icon_y, icon_sz, pill_h, gap=30):
    bx = icon_x + icon_sz + gap
    by = round(icon_y + (icon_sz - pill_h)/2)
    return bx, by

# ---- scene 2 ----
m = info["scene2-pill1"]
X, Y, SZ = 1350, 180, 520
bx = below_pos(X, SZ, m["pill_w"])
by = Y + SZ + 30
scene2_icons = [dict(png=f"{ICONS}/scene2-icon1.png", x=X, y=Y, sz=SZ, start=8.3,
                      label="Добраться до сути", pill_png=f"{R}/pills/scene2-pill1.png",
                      pill_w=m["pill_w"], pill_h=m["pill_h"], pill_margin=m["margin"],
                      pill_bx=bx, pill_by=by, fs=34)]

# ---- scene 3 ----
SZ3 = 330; XL, XR, Y0, Y1 = 60, 1540, 60, 460
defs3 = [
    ("scene3-icon1.png", XL, Y0, 7.15, "Болеет каждую осень", "scene3-pill1"),
    ("scene3-icon2.png", XR, Y0, 12.13, "Слабость после ОРВИ", "scene3-pill2"),
    ("scene3-icon3.png", XL, Y1, 15.56, "Просто устал", "scene3-pill3"),
    ("scene3-icon4.png", XR, Y1, 20.81, "Уже принимает БАДы", "scene3-pill4"),
]
scene3_icons = []
for png, x, y, st, label, pillname in defs3:
    m = info[pillname]
    bx = below_pos(x, SZ3, m["pill_w"])
    by = y + SZ3 + 30
    scene3_icons.append(dict(png=f"{ICONS}/{png}", x=x, y=y, sz=SZ3, start=st, label=label,
                              pill_png=f"{R}/pills/{pillname}.png", pill_w=m["pill_w"], pill_h=m["pill_h"],
                              pill_margin=m["margin"], pill_bx=bx, pill_by=by, fs=34))

# ---- scene 5 ---- (icon shifted left from old x=1430 since sticker style has no
# bulky white card anymore, and beside-labels now need much more horizontal room)
SZ5 = 110; ICX = 1300
rows5 = [50, 220, 390, 560]
defs5 = [
    (rows5[0], 2.92, "Что именно беспокоит?", "scene5-pill1", "scene5-icon1.png"),
    (rows5[1], 11.28, "Длительность симптомов", "scene5-pill2", "scene5-icon2.png"),
    (rows5[2], 14.26, "Приём других препаратов", "scene5-pill3", "scene5-icon3.png"),
    (rows5[3], 19.86, "Хронические заболевания", "scene5-pill4", "scene5-icon4.png"),
]
scene5_icons = []
for y, st, label, pillname, png in defs5:
    m = info5[pillname]
    bx, by = beside_pos(ICX, y, SZ5, m["pill_h"])
    scene5_icons.append(dict(png=f"{ICONS}/{png}", x=ICX, y=y, sz=SZ5, start=st, label=label,
                              pill_png=f"{R}/pills/{pillname}.png", pill_w=m["pill_w"], pill_h=m["pill_h"],
                              pill_margin=m["margin"], pill_bx=bx, pill_by=by, fs=28))

# ---- scene 6 ----
SZ6 = 470
defs6 = [
    ("scene6-icon1.png", 80, 120, 13.79, "Излишняя стимуляция", "scene6-pill1", 472, 89),
    ("scene6-icon2.png", 1400, 120, 17.2, "Восстановительная поддержка", "scene6-pill2", 627, 89),
]
scene6_icons = []
for png, x, y, st, label, pillname, pw, ph in defs6:
    bx = below_pos(x, SZ6, pw)
    by = 620
    scene6_icons.append(dict(png=f"{ICONS}/{png}", x=x, y=y, sz=SZ6, start=st, label=label,
                              pill_png=f"{R}/pills/{pillname}.png", pill_w=pw, pill_h=ph,
                              pill_margin=40, pill_bx=bx, pill_by=by, fs=34))

for scene_n, icons in [(2, scene2_icons), (3, scene3_icons), (5, scene5_icons), (6, scene6_icons)]:
    build_scene(scene_n, icons)

print("ALL ICON SCENES DONE")
