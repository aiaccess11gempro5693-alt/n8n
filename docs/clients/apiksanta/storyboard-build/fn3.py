"""Slide-3 footnotes: deterministic, flicker-free rebuild.

The footnote block is static white text whose lines fade in/out (staggered).  The exact text alpha is
measured once from the video itself (per pixel, at the frame where the background under it is darkest),
so every frame is un-mixed analytically with per-line opacity:
    bg = (F - 255*a*o_line) / (1 - a*o_line)
and the same alpha shifted up by one line (+ the new ОХЛП line rendered with a font calibrated to the
video's own letters) is composited back over that background.  Only the letters move; the underlay
stays in place; no per-frame thresholds -> no flicker.
"""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

Y0, Y1 = 996, 1080
LINE4 = ("ОХЛП Апиксанта. ЛП-№(010414)-(РГ-RU). Сайт уполномоченного органа (экспертной организации) "
         "https://lk.regmed.ru/Register/EAEU_SmPC. Дата доступа 10.11.2026")
L1TXT = 'ТЭЛА - тромбоэмболия легочной артерии'


def _groups(rows):
    out, s, p = [], rows[0], rows[0]
    for r in rows[1:]:
        if r - p > 1:
            out.append((s, p)); s = r
        p = r
    out.append((s, p))
    return out


class Footnotes3:
    def __init__(self, S, fonts):
        A = np.load(f'{S}/A_vid3.npy')
        rows = np.nonzero((A > 0.3).sum(1) > 3)[0]
        g = [x for x in _groups(rows) if x[1] - x[0] >= 6][:3]
        self.lines = g
        (l1a, l1b), (l2a, l2b), (l3a, l3b) = g
        self.pitch = int(round((l3a - l1a) / 2))
        # per-line masks (split overlap rows at the midpoint between lines)
        cuts = [Y0, (l1b + l2a) // 2 + 1, (l2b + l3a) // 2 + 1, Y1]
        self.line_masks = []
        for k in range(3):
            m = np.zeros_like(A); m[cuts[k]:cuts[k + 1]] = 1
            self.line_masks.append(m)
        self.A_old = A
        self.A_lines = [A * m for m in self.line_masks]
        sh = lambda X: np.vstack([X[self.pitch:], np.zeros((self.pitch, X.shape[1]), X.dtype)])
        self.A_new_lines = [sh(a) for a in self.A_lines]
        self.A_line4 = self._line4(A, fonts, (l1a, l1b), (l3a, l3b))
        self.cores = cv2.dilate((A > 0.6).astype(np.uint8), np.ones((2, 2), np.uint8))[Y0:Y1] * 255
        self.prev = None
        om = cv2.dilate((A > 0.04).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
        self.oldmask = cv2.GaussianBlur(om, (0, 0), 0.8)[Y0:Y1]

    def _font(self, size, wght, fonts):
        f = ImageFont.truetype(f'{fonts}/Montserrat[wght].ttf', 10).font_variant(size=size)
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
        return f

    def _render(self, text, size, wght, fonts):
        f = self._font(size, wght, fonts)
        bb = f.getbbox(text)
        im = Image.new('L', (bb[2] + 8, bb[3] + 8), 0)
        ImageDraw.Draw(im).text((4, 4), text, font=f, fill=255)
        a = np.asarray(im).astype(np.float32) / 255
        ys, xs = np.nonzero(a > 0.3)
        return a, xs.min(), ys.min(), xs.max()

    def _line4(self, A, fonts, l1, l3):
        reg = A[l1[0] - 2:l1[1] + 1, :700]
        cols = np.nonzero((reg > 0.3).any(0))[0]
        tw = cols.max() - cols.min() + 1
        ink = reg.sum()
        best = None
        for size in np.arange(12.0, 16.01, 0.05):
            a, x0, y0, x1 = self._render(L1TXT, float(size), 500, fonts)
            if best is None or abs((x1 - x0 + 1) - tw) < best[0]:
                best = (abs((x1 - x0 + 1) - tw), float(size))
        size = best[1]
        wb = None
        for w in range(380, 700, 10):
            a, *_ = self._render(L1TXT, size, w, fonts)
            if wb is None or abs(a.sum() - ink) < wb[0]:
                wb = (abs(a.sum() - ink), w)
        self.size4, self.wght4 = size, 500
        top1 = l1[0] + np.nonzero((A[l1[0]:l1[1] + 1, cols.min():cols.min() + 20] > 0.3).any(1))[0].min()
        a4, bx, by, _ = self._render(LINE4, size, self.wght4, fonts)
        out = np.zeros_like(A)
        X = cols.min() - bx
        Yt = top1 + 2 * self.pitch - by                 # old line-3 slot (after the lift)
        h, w = a4.shape
        w = min(w, 1920 - X)
        out[Yt:Yt + h, X:X + w] = a4[:, :w]
        return out

    def _profiles(self, F):
        g = cv2.cvtColor(F.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        hp = g - cv2.GaussianBlur(g, (0, 0), 2)
        out = []
        for k in range(3):
            v = (hp * self.A_lines[k]).sum(0)
            out.append(cv2.GaussianBlur(v[None, :], (0, 0), 14)[0])
        return np.array(out)

    def set_reference(self, F_settled):
        self.ref = self._profiles(F_settled)
        self.ink = np.array([cv2.GaussianBlur(self.A_lines[k].sum(0)[None, :], (0, 0), 14)[0] for k in range(3)])

    def opacity(self, F, f, settled=(216, 1024)):
        """per-line, per-column opacity o[k, x] (lines reveal left-to-right)."""
        if settled[0] <= f <= settled[1]:
            return np.ones((3, 1920), np.float32)
        P = self._profiles(F)
        o = np.ones((3, 1920), np.float32)
        for k in range(3):
            ok = self.ink[k] > 0.4 * self.ink[k].max() * 0.05
            r = np.where(ok, P[k] / np.where(np.abs(self.ref[k]) > 1e-3, self.ref[k], 1e-3), np.nan)
            ok = ok & (np.abs(self.ref[k]) > 0.15 * np.abs(self.ref[k]).max())
            xs = np.arange(1920)
            if ok.sum() < 10:
                o[k] = 0; continue
            o[k] = np.clip(np.interp(xs, xs[ok], np.nan_to_num(r[ok])), 0, 1)
            if f > settled[1]:                 # fade-out is uniform: use a robust scalar
                o[k] = float(np.clip(np.sum(P[k][ok]) / np.sum(self.ref[k][ok]), 0, 1))
        return o

    def apply(self, F, os_):
        """No removal: the three original lines stay untouched; the ОХЛП line is added below line 3."""
        o3 = np.asarray(os_)[2]
        if np.max(o3) <= 0.01:
            return F
        A4 = np.vstack([np.zeros((self.pitch, 1920), np.float32), self.A_line4[:-self.pitch]])
        an = (A4[Y0:Y1] * (o3[None, :] if np.ndim(o3) else o3) * 0.9)[..., None]
        out = F.copy()
        out[Y0:Y1] = F[Y0:Y1] * (1 - an) + 245.0 * an
        return out
