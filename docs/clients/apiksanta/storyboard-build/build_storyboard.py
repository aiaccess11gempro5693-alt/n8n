"""Build the corrected storyboard frames (1:1 with the original, only the client's corrections applied)."""
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = sys.argv[1]          # work dir (orig/, scroll_new.png, k2_notext.png, k3_notext.png, logo_layer.png)
FONTS = sys.argv[2]
OUT = sys.argv[3]
MONT = f'{FONTS}/Montserrat[wght].ttf'


def mont(size, weight=500):
    f = ImageFont.truetype(MONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def load(i):
    return cv2.imread(f'{S}/orig/{i:02d}.jpg').astype(np.float32)


def unmix(fr, cl, color):
    """alpha of solid-colour text over a known clean background."""
    c = np.array(color, np.float32)[None, None]
    num = ((cl - fr) * (cl - c)).sum(2)
    den = ((cl - c) ** 2).sum(2) + 1e-3
    return np.clip(num / den, 0, 1)


def paste_alpha(img, alpha, color, x, y):
    h, w = alpha.shape
    reg = img[y:y + h, x:x + w]
    c = np.array(color, np.float32)[None, None]
    img[y:y + h, x:x + w] = reg * (1 - alpha[..., None]) + c * alpha[..., None]


# ---------------------------------------------------------------- logo capsule (all frames)
LOGO = Image.open(f'{S}/logo_layer.png').convert('RGBA')
LX0, LY0 = 1743, 74


def capsule(bgr):
    F = Image.fromarray(cv2.cvtColor(bgr.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert('RGBA')
    x1, y1 = LX0 + LOGO.width, LY0 + LOGO.height
    bx0, by0, bx1, by1 = LX0 - 26, LY0 - 14, x1 + 26, y1 + 14
    r = (by1 - by0) // 2
    sh = Image.new('RGBA', F.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((bx0, by0 + 4, bx1, by1 + 4), radius=r, fill=(20, 40, 60, 60))
    F = Image.alpha_composite(F, sh.filter(ImageFilter.GaussianBlur(8)))
    cap = Image.new('RGBA', F.size, (0, 0, 0, 0))
    ImageDraw.Draw(cap).rounded_rectangle((bx0, by0, bx1, by1), radius=r, fill=(255, 255, 255, 255))
    F = Image.alpha_composite(F, cap)
    F.alpha_composite(LOGO, (LX0, LY0))
    return F.convert('RGB')


def draw_text_bgr(img, xy, text, font, rgb, anchor='la'):
    pil = Image.fromarray(cv2.cvtColor(img.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB))
    ImageDraw.Draw(pil).text(xy, text, font=font, fill=rgb, anchor=anchor)
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR).astype(np.float32)


# ---------------------------------------------------------------- slide 2 (title)
def slide2():
    fr = load(2)
    cl = cv2.imread(f'{S}/k2_notext.png').astype(np.float32)
    out = fr.copy()
    # 2a. scroll: line 2 rebuilt ('ТЕРАПИИ АПИКСАБАНОМ'); paste only the edited band
    sc = cv2.imread(f'{S}/scroll_new.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
    SX, SY = 88, 249
    y0, y1, x0, x1 = 106, 178, 62, 798
    band = sc[y0:y1, x0:x1, :3]
    feather = np.ones((y1 - y0, x1 - x0), np.float32)
    for k in range(6):
        feather[k] *= (k + 1) / 7; feather[-1 - k] *= (k + 1) / 7
    for k in range(12):
        feather[:, k] *= (k + 1) / 13; feather[:, -1 - k] *= (k + 1) / 13
    reg = out[SY + y0:SY + y1, SX + x0:SX + x1]
    out[SY + y0:SY + y1, SX + x0:SX + x1] = reg * (1 - feather[..., None]) + band * feather[..., None]

    # 2b. plaque 1: 'ПЕРВЫЙ ЕВРОПЕЙСКИЙ' -> 'ПЕРВЫЙ В РФ ЕВРОПЕЙСКИЙ'
    TXT = (130, 106, 83)                               # BGR plaque text colour
    a1 = unmix(fr, cl, TXT)
    ly0, ly1 = 533, 571                                # line 1 rows (incl. breve)
    w_perv = a1[ly0:ly1, 296:424].copy()
    w_evr = a1[ly0:ly1, 432:642].copy()
    # 'В РФ' from slide-3 title (same family, bold), scaled to plaque cap height
    fr3 = load(3); cl3 = cv2.imread(f'{S}/k3_notext.png').astype(np.float32)
    a3 = unmix(fr3, cl3, (77, 53, 6))
    sx, sy = 18 / 30, 24 / 38
    def grab(xa, xb):
        g = a3[76:122, xa:xb]
        return cv2.resize(g, (int(round(g.shape[1] * sx)), int(round(g.shape[0] * sy))), interpolation=cv2.INTER_AREA)
    gV = grab(624, 657); gRF = grab(671, 752)
    # vertical placement: title cap top 81 -> plaque cap top 543
    def put(dst, g, x):
        top = 543 - ly0 - int(round((81 - 76) * sy))
        h = min(g.shape[0], dst.shape[0] - top)
        dst[top:top + h, x:x + g.shape[1]] = np.maximum(dst[top:top + h, x:x + g.shape[1]], g[:h])
    SP = 13
    width = w_perv.shape[1] + SP + gV.shape[1] + SP + gRF.shape[1] + SP + w_evr.shape[1]
    line = np.zeros((ly1 - ly0, width), np.float32)
    x = 0
    line[:, x:x + w_perv.shape[1]] = w_perv; x += w_perv.shape[1] + SP
    put(line, gV, x); x += gV.shape[1] + SP
    put(line, gRF, x); x += gRF.shape[1] + SP
    line[:, x:x + w_evr.shape[1]] = np.maximum(line[:, x:x + w_evr.shape[1]], w_evr)
    right = 642
    lx = right - width
    out[ly0:ly1, 150:660] = cl[ly0:ly1, 150:660]       # wipe old line 1
    paste_alpha(out, line, TXT, lx, ly0)

    # 2c. plaque 3: 'ПРОИЗВОДСТВО' + '¹', 'GMP¹' -> 'GMP²'
    a = unmix(fr, cl, TXT)
    m = a[880:918, 560:660] > 0.25
    # locate the superscript '1' at the far right of line 2 (above the cap middle)
    cols = np.nonzero(m.any(0))[0]
    segs = []; s = cols[0]; p = cols[0]
    for c in cols[1:]:
        if c - p > 1: segs.append((s, p)); s = c
        p = c
    segs.append((s, p))
    sup_x0, sup_x1 = segs[-1][0] + 560, segs[-1][1] + 560
    sup_rows = np.nonzero((a[870:925, sup_x0:sup_x1 + 1] > 0.25).any(1))[0]
    sy0, sy1 = 870 + sup_rows.min(), 870 + sup_rows.max()
    sup1 = a[sy0 - 1:sy1 + 2, sup_x0 - 1:sup_x1 + 2].copy()
    # line 1 of plaque 3
    l1 = a[838:878, 20:660]
    rows1 = np.nonzero((l1 > 0.25).any(1))[0]; cols1 = np.nonzero((l1 > 0.25).any(0))[0]
    l1x0, l1x1 = 20 + cols1.min(), 20 + cols1.max()
    l1y0, l1y1 = 838 + rows1.min(), 838 + rows1.max()
    word = a[l1y0 - 2:l1y1 + 3, l1x0 - 2:l1x1 + 3].copy()
    gap = max(2, sup_x0 - (segs[-2][1] + 560) - 4)
    new_w = word.shape[1] + gap + sup1.shape[1]
    out[l1y0 - 2:l1y1 + 3, 20:660] = cl[l1y0 - 2:l1y1 + 3, 20:660]
    nx = (sup_x1 + 1) - new_w + 2                        # keep right alignment with line 2
    paste_alpha(out, word, TXT, nx, l1y0 - 2)
    sup_top_rel = (sy0 - 1) - (870 + 10)                 # superscript sits at cap top of its line
    cap_top_l2 = 882 + np.nonzero((a[882:925, 450:sup_x0 - 3] > 0.25).any(1))[0].min()
    sup_y = l1y0 + (sy0 - 1 - cap_top_l2)
    paste_alpha(out, sup1, TXT, nx + word.shape[1] + gap, sup_y)
    # '¹' -> '²' on line 2: wipe and draw a '2' of the same height/weight
    out[sy0 - 2:sy1 + 3, sup_x0 - 2:sup_x1 + 4] = cl[sy0 - 2:sy1 + 3, sup_x0 - 2:sup_x1 + 4]
    h = sy1 - sy0 + 1
    for size in range(6, 40):
        f = mont(size, 600)
        bb = f.getbbox('2')
        if bb[3] - bb[1] >= h:
            break
    rgb = (TXT[2], TXT[1], TXT[0])
    out = draw_text_bgr(out, (sup_x0 - bb[0], sy0 - bb[1]), '2', f, rgb)

    # 2d. footnotes: clean band and set the new text in the same style (Montserrat Medium, caps, white)
    fy0 = 980
    out[fy0:1080] = cl[fy0:1080]
    fn = ("ОХЛП Апиксанта. ЛП-№(010414)-(РГ-RU). Сайт уполномоченного органа (экспертной организации) "
          "https://lk.regmed.ru/Register/EAEU_SmPC. Дата доступа 10.11.2026 "
          "*Формулировка не содержит утверждений о новых данных по эффективности или безопасности и не подразумевает "
          "расширения терапевтических возможностей. Под «новой главой» понимается появление нового препарата в классе "
          "средств с МНН апиксабан. "
          "**По состоянию на 10.11.2026 Апиксанта является первым дженериком апиксабана, введённым в гражданский оборот. "
          "По сведениям о лекарственных средствах, вводимых в гражданский оборот в РФ, опубликованных на сайте Росздравнадзора "
          "***По данным реестра предельных отпускных цен, актуальным на 10.11.2026, зарегистрированная цена на препарат "
          "Апиксанта в среднем на 22% ниже оригинального препарата. "
          "https://grls.rosminzdrav.ru/PriceLims.aspx?PageSize=&TradeName=%d0%90%d0%bf%d0%b8%d0%ba%d1%81%d0%b0%d0%bd%d1%82%d0%b0"
          "&INN=&OrgName=&RegNumber=&OrderNumber=&OuterState=60&token=05824fba-43c0-46f2-bb3e-b62a7ba70e34&OrderBy=pklimprice&OrderType=desc "
          "****Согласно ОХЛП препарата Апиксанта терапию препаратом по показанию \"Профилактика инсульта и системной "
          "тромбоэмболии у взрослых пациентов с неклапанной фибрилляцией предсердий, имеющих один или несколько факторов "
          "риска ТЭО (полную информацию см. в ОХЛП Апиксанта)\" следует принимать длительно при условии, что польза от "
          "профилактики инсульта и системной тромбоэмболии превышает риск кровотечения "
          "ОХЛП Апиксанта. ЛП-№(010414)-(РГ-RU). Сайт уполномоченного органа (экспертной организации) "
          "https://lk.regmed.ru/Register/EAEU_SmPC. Дата доступа 10.11.2026 "
          "1. Государственный реестр лекарственных средств "
          "https://grls.rosminzdrav.ru/Grls_View_v2.aspx?routingGuid=4a415c7d-bc64-409e-855c-7bc3373e6025. Дата доступа 10.11.2026 "
          "2. Сведения из базы данных о сертификатах GMP Министерства промышленности и торговли России, "
          "номер сертификата GMP/EAEU/RU/02647-2026").upper()
    FX0, FX1 = 68, 1902
    size = 13
    while True:
        f = mont(size, 500)
        lines = wrap(fn, f, FX1 - FX0)
        lh = round(size * 1.06)
        if len(lines) * lh <= 1076 - 982 or size <= 9:
            break
        size -= 0.5
    pil = Image.fromarray(cv2.cvtColor(out.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    ytop = 1076 - len(lines) * lh
    for k, ln in enumerate(lines):
        d.text((FX0, ytop + k * lh), ln, font=f, fill=(234, 236, 238))
    print('slide2 footnotes:', len(lines), 'lines, size', size, 'top y', ytop)
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR).astype(np.float32)


def wrap(text, font, width):
    """greedy wrap; long tokens (URLs) are split by characters to fill the current line."""
    words = text.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = (cur + ' ' + w) if cur else w
        if font.getlength(cand) <= width:
            cur = cand
            continue
        if len(w) > 30:
            while True:
                pre = (cur + ' ') if cur else ''
                k = len(w)
                while k > 0 and font.getlength(pre + w[:k]) > width:
                    k -= 1
                if k == len(w):
                    cur = pre + w; break
                lines.append(pre + w[:k]); cur = ''; w = w[k:]
            continue
        lines.append(cur)
        cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- slide 3
def slide3():
    fr = load(3)
    cl = cv2.imread(f'{S}/k3_notext.png').astype(np.float32)
    out = fr.copy()
    # 3a. footnotes: lift the existing three lines by one line and add the ОХЛП reference as line 4
    WHITE = (250, 250, 250)
    y0, y1 = 1008, 1066
    reg = fr[y0:y1]
    bg = cv2.medianBlur(reg.clip(0, 255).astype(np.uint8), 7).astype(np.float32)
    a = unmix(reg, bg, WHITE)          # used only for measuring line 1
    LH = 17
    # lift the whole band (text + background) by one line; columns are vertical so the shift is invisible
    out[y0 - LH:y1 - LH] = fr[y0:y1]
    out[y1 - LH:y1] = fr[1080 - LH:1080]
    for k in range(8):                 # feather the upper seam
        w = (k + 1) / 9
        yy = y0 - LH - 8 + k
        out[yy] = fr[yy] * (1 - w) + fr[yy + LH] * w
    # line 4: same size as the existing lines (match the measured width of line 1)
    l1 = 'ТЭЛА - тромбоэмболия легочной артерии'
    rows = np.nonzero((a[:, 60:360] > 0.4).any(1))[0]
    r0 = rows.min()
    cols = np.nonzero((a[r0:r0 + 12, 40:420] > 0.4).any(0))[0] + 40
    target = cols.max() - cols.min() + 1
    print('line1 cols', cols.min(), cols.max())
    size = 8.0
    while mont(size + 0.25, 500).getlength(l1) <= target:
        size += 0.25
    f = mont(size, 500)
    bb = f.getbbox('Т')
    base_y = y0 - LH + r0 + 3 * LH
    ref = ("ОХЛП Апиксанта. ЛП-№(010414)-(РГ-RU). Сайт уполномоченного органа (экспертной организации) "
           "https://lk.regmed.ru/Register/EAEU_SmPC. Дата доступа 10.11.2026")
    out = draw_text_bgr(out, (cols.min(), base_y - bb[1]), ref, f, (250, 250, 250))
    # 3b. '**' after 'АПИКСАНТА 2,5мг, 20 и 60 таблеток' (where the client placed it)
    lab = unmix(fr, cl, (247, 247, 245))[592:614, 1240:1362]
    m = lab > 0.35
    cols = np.nonzero(m.any(0))[0]; rows = np.nonzero(m.any(1))[0]
    end_x = 1240 + cols.max(); top_y = 592 + rows.min()
    f2 = mont(14, 700)
    b2 = f2.getbbox('**')
    out = draw_text_bgr(out, (end_x + 2 - b2[0], top_y - b2[1] - 1), '**', f2, (245, 247, 247))
    print('slide3: footnote font', size, 'line4 y', base_y, '; ** at x', end_x + 2)
    return out


# ---------------------------------------------------------------- slide 22
def slide22():
    out = load(22)
    f = mont(22, 600)
    out = draw_text_bgr(out, (89, 892), 'APIX-RU-00148-DOC-11.2026', f, (6, 53, 77), anchor='lm')
    return out


frames = {}
for i in range(1, 23):
    if i == 2:
        img = slide2()
    elif i == 3:
        img = slide3()
    elif i == 22:
        img = slide22()
    else:
        img = load(i)
    if i in (2, 3, 22):
        cv2.imwrite(f"{OUT}/nocap-{i:02d}.png", img.clip(0, 255).astype(np.uint8))
    frames[i] = capsule(img)
    frames[i].save(f'{OUT}/frame-{i:02d}.png')
pages = [frames[i] for i in range(1, 23)]
pages[0].save(f'{OUT}/storyboard.pdf', save_all=True, append_images=pages[1:], resolution=96, quality=92)
print('done')
