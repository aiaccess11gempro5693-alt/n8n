"""Rebuild line 2 of the title scroll: 'ТЕРАПИИ АПИКСАБАНА' -> 'ТЕРАПИИ АПИКСАБАНОМ'.
Original letters are reused pixel-for-pixel; 'О' is taken from line 1 ('НОВАЯ') and scaled,
'М' is rendered from the Forum font (closest free Trajan-like Cyrillic) with a synthesized
V-cut engraving matched to the original strokes."""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = sys.argv[1]
FONT = sys.argv[2]
sc = cv2.imread(f'{S}/scroll.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
rgb = sc[..., :3]
L = rgb.mean(2)

B0, B1 = 112, 172          # line-2 band rows
X0, X1 = 62, 798           # scroll interior columns
# ---- 1. clean parchment under line 2: vertical blend of parchment rows above/below + grain
top_rows = rgb[104:110].mean(0); bot_rows = rgb[176:182].mean(0)
clean = rgb.copy()
rng = np.random.default_rng(7)
grain_src = cv2.GaussianBlur(rng.normal(0, 5, (14, rgb.shape[1], 1)).astype(np.float32).repeat(3, 2), (0, 0), 1.2)
grain_src = grain_src * np.array([0.6, 0.85, 1.0], np.float32)
for y in range(B0, B1):
    w = (y - B0) / (B1 - B0 - 1)
    row = top_rows * (1 - w) + bot_rows * w
    row = cv2.GaussianBlur(row[None], (0, 0), 6)[0]
    clean[y, X0:X1] = row[X0:X1] + grain_src[(y - B0) % grain_src.shape[0], X0:X1] * 0.9
# feather the band edges into the original
for k_ in range(4):
    a_ = (k_ + 1) / 5
    clean[B0 - 4 + k_, X0:X1] = rgb[B0 - 4 + k_, X0:X1] * (1 - a_) + clean[B0, X0:X1] * a_
    clean[B1 + 3 - k_, X0:X1] = rgb[B1 + 3 - k_, X0:X1] * (1 - a_) + clean[B1 - 1, X0:X1] * a_
bgL = cv2.medianBlur(np.clip(L, 0, 255).astype(np.uint8), 31).astype(np.float32)


def glyph(x0, x1, y0=B0, y1=B1, src=rgb):
    """Return (rgb, alpha) patch of an original engraved glyph (alpha relative to parchment)."""
    patch = src[y0:y1, x0 - 2:x1 + 2].copy()
    l = patch.mean(2)
    a = np.clip((bgL[y0:y1, x0 - 2:x1 + 2] - l - 6) / 28.0, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.6)
    a[:, :3] = 0; a[:, -3:] = 0          # no seams at patch borders
    return patch, a


segs2 = [(80, 115), (121, 145), (152, 217), (220, 260), (267, 307), (314, 355),
         (373, 413), (417, 456), (464, 504), (512, 584), (586, 626), (630, 658),
         (660, 699), (703, 744), (746, 787)]
# Т Е РА П И И | А П И КС А Б А Н [А dropped]
pieces = []
for i, (a, b) in enumerate(segs2[:-1]):
    gap_before = 0 if i == 0 else (segs2[i][0] - segs2[i - 1][1])
    pieces.append((gap_before, *glyph(a, b)))
gap = int(np.median([segs2[i][0] - segs2[i - 1][1] for i in range(1, len(segs2)) if segs2[i][0] - segs2[i - 1][1] < 12]))

# ---- 2. 'О' from line 1, scaled to line-2 cap height
def cap_rows(y0, y1, x0, x1):
    m = (L[y0:y1, x0:x1] < 120).any(1)
    ys = np.nonzero(m)[0]
    return y0 + ys.min(), y0 + ys.max()

l2t, l2b = cap_rows(116, 168, 703, 744)       # Н on line 2
l1t, l1b = cap_rows(30, 104, 160, 216)        # Н on line 1
k = (l2b - l2t + 1) / (l1b - l1t + 1)
o_rgb, o_a = glyph(223, 280, l1t - 8, l1b + 8)
n, lab, st, _ = cv2.connectedComponentsWithStats((o_a > 0.05).astype(np.uint8), 8)
keep = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
o_a = o_a * cv2.dilate((lab == keep).astype(np.uint8), np.ones((3, 3), np.uint8))
nh = int(round(o_rgb.shape[0] * k)); nw = int(round(o_rgb.shape[1] * k))
o_rgb = cv2.resize(o_rgb, (nw, nh), interpolation=cv2.INTER_AREA)
o_a = cv2.resize(o_a, (nw, nh), interpolation=cv2.INTER_AREA)
# pad into band coordinates (align cap top)
top = (l2t - B0) - int(round(8 * k))
O = np.zeros((B1 - B0, nw, 3), np.float32) + clean[B0:B1, 400:401]
Oa = np.zeros((B1 - B0, nw), np.float32)
ys, ye = max(0, top), min(B1 - B0, top + nh)
O[ys:ye] = o_rgb[ys - top:ye - top]; Oa[ys:ye] = o_a[ys - top:ye - top]
pieces.append((gap, O, Oa))

# ---- 3. 'М' rendered from Forum with synthetic V-cut engraving
cap_h = l2b - l2t + 1
SS = 6
font = None
for size in range(20, 120):
    f = ImageFont.truetype(FONT, size * SS)
    bb = f.getbbox('Н')
    if (bb[3] - bb[1]) >= cap_h * SS:
        font = f
        break
bb = font.getbbox('М')
W = bb[2] - bb[0] + 8 * SS; H = (B1 - B0) * SS
im = Image.new('L', (W, H), 0)
hb = font.getbbox('Н')
ImageDraw.Draw(im).text((4 * SS - bb[0], (l2t - B0) * SS - hb[1]), 'М', font=font, fill=255)
m = np.asarray(im).astype(np.uint8)
m = cv2.dilate(m, np.ones((int(SS * 2.2), int(SS * 2.2)), np.uint8))          # original strokes are heavier
dist = cv2.distanceTransform((m > 127).astype(np.uint8), cv2.DIST_L2, 5)
# local half-width ~ max distance in neighbourhood
hw = cv2.dilate(dist, np.ones((5 * SS, 5 * SS), np.uint8)) + 1e-3
t = np.clip(dist / hw, 0, 1)                                      # 0 at edge, 1 at stroke centre
dark = np.array([34, 86, 127], np.float32)    # BGR of the deep cut
mid = np.array([70, 118, 158], np.float32)    # BGR of the groove centre
col = dark[None, None] + (mid - dark)[None, None] * (t ** 2.2)[..., None]
# light catches the lower-right lip
hl = cv2.GaussianBlur(((m > 127).astype(np.float32)), (0, 0), SS * 0.8)
shift = np.roll(np.roll(hl, SS, 0), SS, 1) - hl
col_small = cv2.resize(col, (W // SS, H // SS), interpolation=cv2.INTER_AREA)
a_small = cv2.resize((m / 255.0).astype(np.float32), (W // SS, H // SS), interpolation=cv2.INTER_AREA)
lip = np.clip(cv2.resize(shift, (W // SS, H // SS), interpolation=cv2.INTER_AREA), 0, 1)
M_rgb = col_small
M_bg = np.zeros_like(M_rgb) + clean[B0:B1, 400:401]
M_rgb = M_rgb * a_small[..., None] + (M_bg + lip[..., None] * 25) * (1 - a_small[..., None])
M_a = np.clip(a_small + lip * 0.6, 0, 1)
pieces.append((gap, M_rgb.astype(np.float32), M_a))

# ---- 4. assemble the new line on a strip, then fit into the scroll interior
total = sum(g + p.shape[1] for g, p, _ in pieces)
strip = np.zeros((B1 - B0, total, 3), np.float32)
strip_a = np.zeros((B1 - B0, total), np.float32)
x = 0
for g, p, a in pieces:
    x += g
    w = p.shape[1]
    strip[:, x:x + w] = strip[:, x:x + w] * (1 - a[..., None]) + p * a[..., None]
    strip_a[:, x:x + w] = np.maximum(strip_a[:, x:x + w], a)
    x += w
avail = (X1 - 14) - (X0 + 14)
s = min(1.0, avail / total)
nw = int(round(total * s)); nh = int(round((B1 - B0) * s))
strip = cv2.resize(strip, (nw, nh), interpolation=cv2.INTER_AREA)
strip_a = cv2.resize(strip_a, (nw, nh), interpolation=cv2.INTER_AREA)
cx = (80 + 787) / 2                     # keep original line centre
cy = (l2t + l2b) / 2                    # keep original line vertical centre
ox = int(round(cx - nw / 2)); oy = int(round(cy - (((l2t + l2b) / 2 - B0) * s)))
ox = max(X0 + 6, min(ox, X1 - 6 - nw))
out = rgb.copy()
out[B0 - 4:B1 + 4, X0:X1] = clean[B0 - 4:B1 + 4, X0:X1]
reg = out[oy:oy + nh, ox:ox + nw]
out[oy:oy + nh, ox:ox + nw] = reg * (1 - strip_a[..., None]) + strip * strip_a[..., None]
res = np.dstack([out, sc[..., 3]]).clip(0, 255).astype(np.uint8)
cv2.imwrite(f'{S}/scroll_new.png', res)
print('scale', round(s, 3), 'line width', nw, 'at', ox, oy)
