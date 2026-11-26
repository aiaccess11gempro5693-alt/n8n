"""Re-render the Apiksanta video with the client's corrections.

The original render is the base (same fonts, animation, timing, audio). Only the corrected elements are
replaced, each tracked frame by frame in the original so the replacement moves/fades/reveals exactly like
the element it replaces:
  * logo capsule      - all frames, fades in with the logo (first 0.7 s)
  * title scroll      - per-frame affine (scale-in / exit zoom) + opacity, difference patch
  * plaque texts      - left-to-right reveal measured per column on the original line, re-mapped to the new line
  * title footnotes   - old text unmixed out, new text set with the measured layer opacity
  * slide-3 footnotes - band lifted one line, new ОХЛП line with the measured opacity
  * slide-3 '**'      - follows the 2.5 mg label (slide-in + fade)
  * final approval code - fades in with 'Благодарим за внимание'
usage: render_video.py WORKDIR IN.mp4 OUT.mp4 [--frames f1,f2,...]  (debug: write PNGs only)
"""
import sys
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

S, SRC, DST = sys.argv[1], sys.argv[2], sys.argv[3]
DEBUG = None
if '--frames' in sys.argv:
    DEBUG = [int(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(',')]

rd = lambda p: cv2.imread(f'{S}/{p}').astype(np.float32)
O2, N2, CL2 = rd('orig/02.jpg'), rd('out/nocap-02.png'), rd('k2_notext.png')
O3, N3 = rd('orig/03.jpg'), rd('out/nocap-03.png')
O22, N22 = rd('orig/22.jpg'), rd('out/nocap-22.png')
gray = lambda x: cv2.cvtColor(x.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
hp = lambda g: g - cv2.GaussianBlur(g, (0, 0), 3)


def unmix(fr, cl, color):
    c = np.array(color, np.float32)[None, None]
    num = ((cl - fr) * (cl - c)).sum(2)
    den = ((cl - c) ** 2).sum(2) + 1e-3
    return np.clip(num / den, 0, 1)


# ------------------------------------------------------------------ tracking helpers
def track(frame, ref, box, search=60, smin=0.3, smax=1.08):
    """affine M (ref->frame) and opacity of the content of `box` (x0,y0,x1,y1 in ref coords)."""
    x0, y0, x1, y1 = box
    T = gray(ref[y0:y1, x0:x1])
    sx0, sy0 = max(0, x0 - search * 4), max(0, y0 - search * 3)
    sx1, sy1 = min(1920, x1 + search * 4), min(1080, y1 + search * 3)
    I = gray(frame[sy0:sy1, sx0:sx1])
    best = None
    for s in np.arange(smin, smax, 0.01):
        t = cv2.resize(T, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        if t.shape[0] < 10 or t.shape[0] >= I.shape[0] or t.shape[1] >= I.shape[1]:
            continue
        r = cv2.matchTemplate(I, t, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(r)
        if best is None or mv > best[0]:
            best = (mv, s, ml)
    if best is None or best[0] < 0.2:
        return None, 0.0
    _, s, (mx, my) = best
    W = np.array([[s, 0, mx], [0, s, my]], np.float32)
    try:
        _, W = cv2.findTransformECC(T, I, W, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5), None, 3)
    except cv2.error:
        pass
    A = W[:, :2]; b = W[:, 2] + np.array([sx0, sy0], np.float32) - A @ np.array([x0, y0], np.float32)
    M = np.hstack([A, b[:, None]]).astype(np.float32)
    return M, corr_opacity(frame, M, box, ref)


def opacity_fixed(frame, ref, box):
    x0, y0, x1, y1 = box
    g, h = hp(gray(frame[y0:y1, x0:x1])), hp(gray(ref[y0:y1, x0:x1]))
    return float(np.clip((g * h).sum() / (h * h).sum(), 0, 1.2))


def add_warped(out, D, M, o, mask=None):
    """out += o * warp(D) ; D is a full-frame float image (zeros outside the patch)."""
    if o <= 0.003:
        return out
    W = cv2.warpAffine(D, M, (1920, 1080), flags=cv2.INTER_LINEAR)
    return out + o * W


IDENT = np.array([[1, 0, 0], [0, 1, 0]], np.float32)

# ------------------------------------------------------------------ title (slide 2) patches
TITLE_F0, TITLE_F1 = 58, 196
D_scroll = np.zeros_like(O2)
ys, ye, xs, xe = 353, 429, 148, 888
D_scroll[ys:ye, xs:xe] = (N2 - O2)[ys:ye, xs:xe]
BOX_SCROLL = (238, 280, 808, 352)          # 'НОВАЯ ГЛАВА' line of the scroll (unchanged)

TXT = (130, 106, 83)
SC_CX = 487.0                      # intro: horizontal unroll about x=487 (measured)
EX_C = (980.0, 550.0)              # exit: uniform zoom about this point (measured)


def corr_opacity(frame, M, box, ref=None):
    """opacity = regression slope of the frame on the forward-warped reference, in frame space."""
    ref = O2 if ref is None else ref
    x0, y0, x1, y1 = box
    m = np.zeros((1080, 1920), np.float32); m[y0:y1, x0:x1] = 1
    wm = cv2.warpAffine(m, M, (1920, 1080), flags=cv2.INTER_NEAREST) > 0.5
    if wm.sum() < 200:
        return 0.0
    wr = cv2.warpAffine(ref, M, (1920, 1080), flags=cv2.INTER_AREA if M[0, 0] < 1 else cv2.INTER_LINEAR)
    ys, xs = np.nonzero(wm); ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    g = cv2.GaussianBlur(gray(frame[ya:yb, xa:xb]), (0, 0), 1.2)[wm[ya:yb, xa:xb]]
    h = cv2.GaussianBlur(gray(wr[ya:yb, xa:xb]), (0, 0), 1.2)[wm[ya:yb, xa:xb]]
    g = g - g.mean(); h = h - h.mean()
    return float(np.clip((g * h).sum() / ((h * h).sum() + 1e-6), 0, 1))


SC_STATE = {}
BOX_L2 = (160, 360, 885, 420)          # the old 'ТЕРАПИИ АПИКСАБАНА' line itself


def scroll_search(frame, cx_range, box=None):
    """2-param search (horizontal scale sx about centre cx) for the first intro frame."""
    x0, y0, x1, y1 = box or BOX_L2
    T = gray(O2[y0:y1, x0:x1]); G = gray(frame)
    best = (-2, 1.0, SC_CX)
    for cx in cx_range:
        for sx in np.arange(0.05, 1.0001, 0.01):
            w = int(round((x1 - x0) * sx))
            if w < 20:
                continue
            X = int(round(cx + sx * (x0 - cx)))
            if X < 0 or X + w > 1920:
                continue
            t = cv2.resize(T, (w, y1 - y0), interpolation=cv2.INTER_AREA)
            g = G[y0:y1, X:X + w]
            a = t - t.mean(); b = g - g.mean()
            c = float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))
            if c > best[0]:
                best = (c, sx, cx)
    return best


def ecc_refine(frame, M0, box, ref=None):
    ref = O2 if ref is None else ref
    x0, y0, x1, y1 = box
    T = gray(ref[y0:y1, x0:x1])
    # predicted location of the box in the frame
    pts = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]], np.float32)
    wp = pts @ M0[:, :2].T + M0[:, 2]
    pad = 40
    sx0 = int(max(0, wp[:, 0].min() - pad)); sx1 = int(min(1920, wp[:, 0].max() + pad))
    sy0 = int(max(0, wp[:, 1].min() - pad)); sy1 = int(min(1080, wp[:, 1].max() + pad))
    I = gray(frame[sy0:sy1, sx0:sx1])
    # crop-coord warp: p_in_crop = A (p_tpl + [x0,y0]) + b - [sx0,sy0]
    A = M0[:, :2]; b = M0[:, 2] + A @ np.array([x0, y0], np.float32) - np.array([sx0, sy0], np.float32)
    W = np.hstack([A, b[:, None]]).astype(np.float32)
    try:
        _, W = cv2.findTransformECC(T, I, W, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6), None, 3)
    except cv2.error:
        return None
    A = W[:, :2]; b = W[:, 2] + np.array([sx0, sy0], np.float32) - A @ np.array([x0, y0], np.float32)
    return np.hstack([A, b[:, None]]).astype(np.float32)


def scroll_M(f, frame):
    if 92 < f < 176:
        return IDENT, 1.0
    prev = sorted(k for k in SC_STATE if 0 < f - k <= 3)
    if f < 176:
        c, sx, cx = scroll_search(frame, np.arange(440, 540, 2))
        if c < 0.25:
            return None, 0.0
        M0 = np.array([[sx, 0, cx * (1 - sx)], [0, 1, 0]], np.float32)
        prev = []
    elif prev:
        p1 = prev[-1]
        if len(prev) >= 2:
            p0 = prev[-2]; M0 = SC_STATE[p1] + (SC_STATE[p1] - SC_STATE[p0]) * (f - p1) / (p1 - p0)
        else:
            M0 = SC_STATE[p1]
    else:
        M0 = IDENT.copy()
    M0 = M0.astype(np.float32)
    M = ecc_refine(frame, M0, BOX_L2)
    ok = M is not None and abs(M[0, 1]) < 0.01 and abs(M[1, 0]) < 0.01
    if ok and f < 176:
        ok = abs(M[1, 1] - 1) < 0.01 and abs(M[1, 2]) < 3
    if ok and f >= 176:
        ok = abs(M[0, 0] - M[1, 1]) < 0.008
    if ok and np.abs(M - M0).max() > (25 if not prev else 8):
        ok = False
    M = M if ok else M0
    o = corr_opacity(frame, M, BOX_L2)
    if o < 0.04:
        return None, 0.0
    SC_STATE[f] = M
    return M, o


def text_T(ref, box, thr=0.03):
    x0, y0, x1, y1 = box
    A = unmix(ref[y0:y1, x0:x1], CL2[y0:y1, x0:x1], TXT)
    m = cv2.dilate((A > thr).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    T = np.zeros_like(O2)
    T[y0:y1, x0:x1] = (ref[y0:y1, x0:x1] - CL2[y0:y1, x0:x1]) * m[..., None]
    return T, A


PL1 = (140, 530, 665, 573)
T1o, A1o = text_T(O2, PL1)
T1n, A1n = text_T(N2, PL1)
PL3a = (15, 834, 668, 881)                 # plaque 3 line 1
PL3b = (15, 881, 668, 922)                 # plaque 3 line 2
T3ao, A3ao = text_T(O2, PL3a); T3an, A3an = text_T(N2, PL3a)
T3bo, A3bo = text_T(O2, PL3b); T3bn, A3bn = text_T(N2, PL3b)
BOX_PL1 = (240, 575, 642, 610)             # 'ДЖЕНЕРИК АПИКСАБАНА**' (unchanged) for exit tracking
BOX_PL3 = (40, 884, 430, 920)              # 'В СООТВЕТСТВИИ СО' (unchanged)


def extent(A):
    cols = np.nonzero((A > 0.2).any(0))[0]
    return cols.min(), cols.max()


def reveal_profile(frame, Told, box):
    """measured visibility of the original line per column (0..1), smoothed."""
    x0, y0, x1, y1 = box
    fr = frame[y0:y1, x0:x1]
    t = Told[y0:y1, x0:x1]
    diff = fr - CL2[y0:y1, x0:x1]
    num = (diff * t).sum((0, 2)); den = (t * t).sum((0, 2))
    v = np.where(den > 50, num / np.maximum(den, 1e-3), np.nan)
    idx = np.arange(len(v)); ok = ~np.isnan(v)
    v = np.interp(idx, idx[ok], v[ok])
    v = np.convolve(v, np.ones(9) / 9, mode='same')
    return np.clip(v, 0, 1)


PRES_ROWS = {PL1: (613, 628), PL3a: (924, 938), PL3b: (924, 938)}


def presence(frame, box):
    x0, y0, x1, y1 = box
    r0, r1 = PRES_ROWS[box]
    d = np.abs(frame[r0:r1, x0:x1] - CL2[r0:r1, x0:x1]).mean((0, 2))
    p = np.clip(1 - (d - 6) / 10, 0, 1)
    p = np.minimum.reduce([np.roll(p, k) for k in range(-6, 7)])
    return p


def remap(v_old, A_old, A_new):
    lo, ro = extent(A_old); ln, rn = extent(A_new)
    xs_ = np.arange(len(v_old))
    u = (xs_ - ln) / max(1, rn - ln)
    src = lo + np.clip(u, 0, 1) * (ro - lo)
    return np.interp(src, xs_, v_old)


# title footnotes: unmix old text out, set new text
FN_Y0 = 948
FNC = (238, 236, 234)
A_fn_old = unmix(O2[FN_Y0:], CL2[FN_Y0:], FNC); A_fn_old[A_fn_old < 0.06] = 0
A_fn_new = unmix(N2[FN_Y0:], CL2[FN_Y0:], FNC); A_fn_new[A_fn_new < 0.06] = 0
BOX_FN2 = (60, 990, 1900, 1068)


def patch_footnotes(out, o):
    if o <= 0.003:
        return out
    reg = out[FN_Y0:]
    c = np.array(FNC, np.float32)[None, None]
    va = (o * A_fn_old)[..., None]
    under = (reg - c * va) / np.clip(1 - va, 0.15, 1)
    hard = (o * A_fn_old) > 0.6
    if hard.any():
        inp = cv2.inpaint(reg.clip(0, 255).astype(np.uint8),
                          cv2.dilate(hard.astype(np.uint8), np.ones((3, 3), np.uint8)) * 255, 2, cv2.INPAINT_TELEA)
        under[hard] = inp[hard]
    na = (o * A_fn_new)[..., None]
    out[FN_Y0:] = under * (1 - na) + c * na
    return out


# ------------------------------------------------------------------ slide 3
_K3 = None


def clean_rows(block, y0=1049):
    """remove the old footnote line from a strip of the real frame (keeps the band shading).
    Mask = exact text alpha from the storyboard frame vs the text-free PSD (static layer) + local contrast."""
    global _K3
    if _K3 is None:
        o3 = cv2.imread(f'{S}/orig/03.jpg').astype(np.float32)
        k3 = cv2.imread(f'{S}/k3_notext.png').astype(np.float32)
        c = np.array([250, 250, 250], np.float32)[None, None]
        num = ((k3 - o3) * (k3 - c)).sum(2); den = ((k3 - c) ** 2).sum(2) + 1e-3
        _K3 = np.clip(num / den, 0, 1)
    b = block.clip(0, 255).astype(np.uint8)
    L = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bgL = cv2.medianBlur(L.astype(np.uint8), 9).astype(np.float32)
    m = (((L - bgL) > 18) | (_K3[y0:y0 + block.shape[0]] > 0.12)).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8)) * 255
    return cv2.inpaint(b, m, 4, cv2.INPAINT_TELEA).astype(np.float32)


def lift(fr):
    out = fr.copy()
    y0, y1, LH = 1008, 1066, 17
    out[y0 - LH:y1 - LH] = fr[y0:y1]
    out[y1 - LH:y1] = clean_rows(fr[y1 - LH:y1])
    for k in range(8):
        w = (k + 1) / 9; yy = y0 - LH - 8 + k
        out[yy] = fr[yy] * (1 - w) + fr[yy + LH] * w
    return out


L3 = lift(O3)
D3 = N3 - L3
D3_line4 = np.zeros_like(O3); D3_line4[1030:1072] = D3[1030:1072]
D3_star = np.zeros_like(O3); D3_star[580:620, 1352:1400] = D3[580:620, 1352:1400]
BOX_FN3 = (60, 1010, 900, 1066)
BOX_LAB = (1200, 568, 1356, 616)
LAB_STATE = {}


def label_M(f, frame):
    prev = sorted(k for k in LAB_STATE if 0 < f - k <= 2)
    M0 = None
    if prev:
        M0 = LAB_STATE[prev[-1]]
    else:
        x0, y0, x1, y1 = BOX_LAB
        T = gray(O3[y0:y1, x0:x1]); G = gray(frame[:900])
        best = None
        for sc in np.arange(0.9, 2.0, 0.02):
            t = cv2.resize(T, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
            r = cv2.matchTemplate(G, t, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
            if best is None or mv > best[0]:
                best = (mv, sc, ml)
        if best[0] < 0.69:
            return None, 0.0
        sc, (mx, my) = best[1], best[2]
        M0 = np.array([[sc, 0, mx - sc * x0], [0, sc, my - sc * y0]], np.float32)
    M = ecc_refine(frame, M0, BOX_LAB, O3)
    if M is None or abs(M[0, 1]) > 0.02 or abs(M[0, 0] - M[1, 1]) > 0.03 or np.abs(M - M0).max() > 40:
        M = M0
    o = corr_opacity(frame, M, BOX_LAB, O3)
    if (not prev and o < 0.6) or o < 0.15:
        LAB_STATE.pop(f, None)
        return None, 0.0
    LAB_STATE[f] = M
    return M, o
S3_F0, S3_F1 = 196, 1050

# ------------------------------------------------------------------ slide 22
D22 = np.zeros_like(O22); D22[860:925, 70:520] = (N22 - O22)[860:925, 70:520]
BOX_THX = (350, 460, 1570, 600)
S22_F0 = 7000

# ------------------------------------------------------------------ capsule
LOGO = Image.open(f'{S}/logo_layer.png').convert('RGBA')
LX0, LY0 = 1743, 74
cap = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
bx0, by0, bx1, by1 = LX0 - 26, LY0 - 14, LX0 + LOGO.width + 26, LY0 + LOGO.height + 14
r_ = (by1 - by0) // 2
sh = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((bx0, by0 + 4, bx1, by1 + 4), radius=r_, fill=(20, 40, 60, 60))
cap = Image.alpha_composite(cap, sh.filter(ImageFilter.GaussianBlur(8)))
pill = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
ImageDraw.Draw(pill).rounded_rectangle((bx0, by0, bx1, by1), radius=r_, fill=(255, 255, 255, 255))
cap = Image.alpha_composite(cap, pill)
cap.alpha_composite(LOGO, (LX0, LY0))
CAP = cv2.cvtColor(np.asarray(cap), cv2.COLOR_RGBA2BGRA).astype(np.float32)
CY0, CY1, CX0, CX1 = by0 - 12, by1 + 24, bx0 - 20, min(1920, bx1 + 20)
CAPc = CAP[CY0:CY1, CX0:CX1, :3]; CAPa = CAP[CY0:CY1, CX0:CX1, 3:] / 255.0
logo_op = np.load(f'{S}/logo_op.npy')


def capsule(out, f):
    o = float(np.clip(logo_op[min(f, len(logo_op) - 1)] / 0.95, 0, 1))
    if o <= 0:
        return out
    a = CAPa * o
    reg = out[CY0:CY1, CX0:CX1]
    out[CY0:CY1, CX0:CX1] = reg * (1 - a) + CAPc * a
    return out


# ------------------------------------------------------------------ per-frame processing
state = {}


def process(f, fr):
    out = fr.astype(np.float32)
    if TITLE_F0 <= f <= TITLE_F1:
        # scroll
        Ms, os_ = scroll_M(f, fr.astype(np.float32))
        if Ms is not None and os_ > 0.02:
            out = add_warped(out, D_scroll, Ms, os_)
        # footnotes (static layer, fades)
        ofn = min(1.0, opacity_fixed(fr.astype(np.float32), O2, BOX_FN2) / 0.99)
        out = patch_footnotes(out, ofn)
        # plaques
        if f <= 177:
            for (Told, Tnew, Aold, Anew, box) in [(T1o, T1n, A1o, A1n, PL1), (T3ao, T3an, A3ao, A3an, PL3a),
                                                   (T3bo, T3bn, A3bo, A3bn, PL3b)]:
                x0, y0, x1, y1 = box
                pres = presence(fr.astype(np.float32), box)
                vo = reveal_profile(fr.astype(np.float32), Told, box) * pres
                if vo.max() < 0.04:
                    continue
                vn = remap(vo, Aold[:, :], Anew[:, :]) if Told is T1o else vo
                if Told is T3ao:
                    vn = remap(vo, Aold, Anew)
                vn = vn * pres
                mo = cv2.dilate((Aold > 0.02).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
                mo = cv2.GaussianBlur(mo, (0, 0), 1.0) * pres[None, :]
                reg = out[y0:y1, x0:x1]
                reg = reg * (1 - mo[..., None]) + CL2[y0:y1, x0:x1] * mo[..., None]
                out[y0:y1, x0:x1] = reg + Tnew[y0:y1, x0:x1] * vn[None, :, None]
        else:
            for (To, Tn, box) in [(T1o, T1n, BOX_PL1), (T3ao + T3bo, T3an + T3bn, BOX_PL3)]:
                M, o = track(fr.astype(np.float32), O2, box, search=30, smin=0.95, smax=1.08)
                if M is not None and o > 0.05:
                    out = add_warped(out, Tn - To, M, o)
    if S3_F0 <= f <= S3_F1:
        o3 = min(1.0, opacity_fixed(fr.astype(np.float32), O3, BOX_FN3) / 0.92)
        if o3 > 0.01:
            out = lift(out)
            out = out + o3 * D3_line4
        if f >= 300:
            M, o = label_M(f, fr.astype(np.float32))
            if M is not None and o > 0.15:
                out = add_warped(out, D3_star, M, min(1.0, o / 0.97))
    if f >= S22_F0:
        o22 = min(1.0, opacity_fixed(fr.astype(np.float32), O22, BOX_THX) / 0.97)
        out = out + o22 * D22
    out = capsule(out, f)
    return out.clip(0, 255).astype(np.uint8)


capv = cv2.VideoCapture(SRC)
n = int(capv.get(cv2.CAP_PROP_FRAME_COUNT))
if DEBUG:
    for f in DEBUG:
        capv.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, fr = capv.read()
        cv2.imwrite(f'{DST}/dbg-{f:05d}.png', process(f, fr))
        cv2.imwrite(f'{DST}/src-{f:05d}.png', fr)
    sys.exit(0)

enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1920x1080',
                        '-r', '24', '-i', '-', '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:a', 'copy',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', DST], stdin=subprocess.PIPE)
f = 0
while True:
    ok, fr = capv.read()
    if not ok:
        break
    enc.stdin.write(process(f, fr).tobytes())
    if f % 500 == 0:
        print('frame', f, '/', n, flush=True)
    f += 1
enc.stdin.close(); enc.wait()
print('done', f, 'frames')
