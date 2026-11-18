#!/usr/bin/env python3
"""THE WORLD IN ONE PICTURE - Tuesday 17 November 2026.
Deterministic PIL broadsheet generator. Renders at 2x, downscales to 1024.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

S = 2
W = H = 1024

PAPER = (247, 243, 234)
INK = (20, 33, 61)
NAVY = (24, 40, 66)
RED = (193, 39, 45)
GOLD = (232, 163, 61)
SEA = (46, 90, 136)
SKY = (214, 231, 242)
STEEL = (90, 110, 130)
DARKGREY = (70, 80, 100)
WHITE = (255, 255, 255)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

_font_cache = {}


def get_font(size, bold=False):
    key = (round(size * 2) / 2.0, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(BOLD if bold else REG, int(round(size * S)))
    return _font_cache[key]


def sc(v):
    return int(round(v * S))


def _w(kw):
    if "width" in kw:
        kw["width"] = max(1, sc(kw["width"]))
    return kw


def rect(d, x, y, w, h, **kw):
    d.rectangle([sc(x), sc(y), sc(x + w), sc(y + h)], **_w(kw))


def rrect(d, x, y, w, h, r, **kw):
    d.rounded_rectangle([sc(x), sc(y), sc(x + w), sc(y + h)], radius=sc(r), **_w(kw))


def ell(d, cx, cy, rx, ry, **kw):
    d.ellipse([sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)], **_w(kw))


def line(d, pts, **kw):
    if "width" in kw:
        kw["width"] = sc(kw["width"])
    d.line([(sc(x), sc(y)) for x, y in pts], **kw)


def poly(d, pts, **kw):
    d.polygon([(sc(x), sc(y)) for x, y in pts], **_w(kw))


def lerp(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def gradient(img, x, y, w, h, top, bottom):
    d = ImageDraw.Draw(img)
    rows = sc(h)
    for i in range(rows + 1):
        t = i / max(1, rows)
        d.line([(sc(x), sc(y) + i), (sc(x + w), sc(y) + i)], fill=lerp(top, bottom, t))


def gradient_sub(img, w, h, top, bottom):
    gradient(img, 0, 0, w, h, top, bottom)


# ---------------- text helpers ----------------

def wrap_text(d, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if not cur or d.textlength(trial, font=font) / S <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit_text(d, text, max_w, max_h, start, minimum, bold=False, ls=1.16):
    size = float(start)
    while size >= minimum:
        f = get_font(size, bold)
        lines = wrap_text(d, text, f, max_w)
        if len(lines) * size * ls <= max_h + 0.5:
            return f, size, lines
        size -= 0.5
    f = get_font(minimum, bold)
    return f, float(minimum), wrap_text(d, text, f, max_w)


def draw_lines(d, x, y, lines, font, size, fill, ls=1.16):
    cy = y
    for ln in lines:
        d.text((sc(x), sc(cy)), ln, font=font, fill=fill)
        cy += size * ls
    return cy


def draw_centered(d, cx, y, text, font, fill):
    w = d.textlength(text, font=font) / S
    d.text((sc(cx - w / 2), sc(y)), text, font=font, fill=fill)
    return w


def text_block(d, x, y, w, kicker, headline, caption,
               head_start, head_box_h, cap_start, cap_box_h,
               kicker_size=13, cap_ls=1.22, head_ls=1.14):
    kf = get_font(kicker_size, True)
    d.text((sc(x), sc(y)), kicker, font=kf, fill=RED)
    y += kicker_size + 5
    hf, hs, hlines = fit_text(d, headline, w, head_box_h, head_start, 13, True, head_ls)
    y = draw_lines(d, x, y, hlines, hf, hs, INK, head_ls)
    y += 3
    cf, cs, clines = fit_text(d, caption, w, cap_box_h, cap_start, 10.5, False, cap_ls)
    y = draw_lines(d, x, y, clines, cf, cs, DARKGREY, cap_ls)
    return y


def panel(d, x, y, w, h):
    rrect(d, x + 3, y + 4, w, h, 5, fill=(203, 198, 188))
    rrect(d, x, y, w, h, 5, fill=WHITE, outline=(176, 182, 194), width=1)


def chip(d, x, y, text):
    f = get_font(12, True)
    tw = d.textlength(text, font=f) / S
    w = tw + 20
    rrect(d, x, y, w, 22, 11, fill=NAVY)
    d.text((sc(x + 10), sc(y + 4)), text, font=f, fill=WHITE)
    return w


def star_pts(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180.0 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def flame(d, cx, base_y, w, h, colors):
    for i, col in enumerate(colors):
        shrink = i * 0.22
        fw = w * (1 - shrink)
        fh = h * (1 - shrink * 0.9)
        by = base_y
        ell(d, cx, by - fh * 0.32, fw / 2, fh * 0.36, fill=col)
        poly(d, [(cx - fw / 2, by - fh * 0.30), (cx + fw / 2, by - fh * 0.30),
                 (cx, by - fh)], fill=col)


# ---------------- HERO: Crimea bridge ----------------

def hero_picture(pw, ph):
    img = Image.new("RGB", (sc(pw), sc(ph)), SKY)
    horizon = 112
    gradient_sub(img, pw, horizon, (198, 224, 242), (248, 216, 172))
    d = ImageDraw.Draw(img)
    ell(d, 884, 24, 14, 14, fill=(250, 205, 120))
    ell(d, 884, 24, 9, 9, fill=(252, 224, 160))
    gradient(img, 0, horizon, pw, ph - horizon, (56, 102, 144), (25, 53, 90))
    d = ImageDraw.Draw(img)
    line(d, [(0, horizon), (pw, horizon)], fill=(235, 242, 248), width=1)

    gap_l, gap_r = 388, 580
    deck_y, rail_y = 96, 109
    for px in range(18, int(pw), 76):
        if gap_l - 16 < px < gap_r:
            continue
        rect(d, px, rail_y + 5, 11, 44, fill=(58, 74, 96))
        rect(d, px - 4, rail_y + 5, 19, 4, fill=(58, 74, 96))
        ell(d, px + 5, 160, 12, 2.5, outline=(190, 215, 235), width=1)
    for ax0, ax1 in ((86, 314), (654, 882)):
        top_y = 42
        steps = 12
        prev = None
        for i in range(steps + 1):
            t = i / steps
            ax = ax0 + (ax1 - ax0) * t
            ay = deck_y - (deck_y - top_y) * (1 - (2 * t - 1) ** 2)
            if prev:
                line(d, [prev, (ax, ay)], fill=NAVY, width=4)
            if 0 < i < steps:
                line(d, [(ax, ay), (ax, deck_y)], fill=NAVY, width=1.5)
            prev = (ax, ay)
    for x0, x1 in ((0, gap_l), (gap_r, pw)):
        rect(d, x0, deck_y, x1 - x0, 8, fill=NAVY)
        rect(d, x0, rail_y, x1 - x0, 6, fill=STEEL)
        for mx in range(int(x0) + 10, int(x1) - 8, 26):
            rect(d, mx, deck_y + 3, 12, 1.6, fill=(240, 240, 235))
    poly(d, [(gap_l + 4, 100), (gap_r - 6, 120), (gap_r - 12, 132),
             (gap_l + 10, 114)], fill=NAVY)
    poly(d, [(gap_l + 10, 116), (gap_r - 14, 134), (gap_r - 16, 140),
             (gap_l + 14, 122)], fill=STEEL)
    line(d, [(gap_l + 34, 106), (gap_r - 40, 124)], fill=GOLD, width=3)
    for r_ in (26, 44, 64):
        ell(d, 484, 152, r_, r_ * 0.22, outline=(225, 240, 250), width=1.6)
    for sx in (428, 540):
        ell(d, sx, 146, 14, 3.2, outline=(225, 240, 250), width=1.4)
    poly(d, star_pts(484, 94, 40, 15, n=12, rot=-90), fill=GOLD)
    poly(d, star_pts(484, 94, 28, 10, n=12, rot=-75), fill=RED)
    ell(d, 484, 94, 7, 7, fill=(255, 236, 190))
    rng = random.Random(42)
    for _ in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r1 = rng.uniform(42, 56)
        sx, sy = 484 + r1 * math.cos(a), 94 + r1 * math.sin(a) * 0.8
        line(d, [(484 + 38 * math.cos(a), 94 + 30 * math.sin(a)), (sx, sy)],
             fill=GOLD, width=2)
    for sx, sy, s_ in ((104, 150, 1.0), (826, 156, 0.8)):
        poly(d, [(sx - 26 * s_, sy), (sx + 26 * s_, sy), (sx + 18 * s_, sy + 8 * s_),
                 (sx - 18 * s_, sy + 8 * s_)], fill=(30, 40, 58))
        rect(d, sx - 8 * s_, sy - 8 * s_, 18 * s_, 8 * s_, fill=(30, 40, 58))
        line(d, [(sx + 2 * s_, sy - 8 * s_), (sx + 2 * s_, sy - 18 * s_)],
             fill=(30, 40, 58), width=1.6)
    rng = random.Random(7)
    for _ in range(46):
        wx = rng.uniform(6, pw - 30)
        wy = rng.uniform(124, ph - 8)
        wl = rng.uniform(10, 26)
        line(d, [(wx, wy), (wx + wl * 0.4, wy - 1.6), (wx + wl, wy)],
             fill=(178, 208, 232), width=1.4)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    plume = [(484, 78, 30, 20, (52, 54, 60, 120)), (476, 56, 38, 25, (70, 72, 80, 105)),
             (460, 34, 47, 30, (95, 97, 105, 92)), (436, 16, 56, 34, (125, 127, 133, 78)),
             (500, 62, 26, 17, (80, 82, 90, 90)), (448, 46, 30, 20, (110, 112, 118, 70))]
    for cx, cy, rx, ry, col in plume:
        od.ellipse([sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)], fill=col)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    chip(d, 12, ph - 30, "KERCH BRIDGE \u2022 CRIMEA")
    return img


# ---------------- ROW 2 LEFT: Hormuz tanker ----------------

def tanker_picture(pw, ph):
    img = Image.new("RGB", (sc(pw), sc(ph)), SKY)
    horizon = 68
    gradient_sub(img, pw, horizon, (203, 226, 242), (246, 219, 178))
    gradient(img, 0, horizon, pw, ph - horizon, (54, 100, 142), (27, 56, 92))
    d = ImageDraw.Draw(img)
    line(d, [(0, horizon), (pw, horizon)], fill=(235, 242, 248), width=1)
    # distant escort ship silhouette
    poly(d, [(356, 62), (402, 62), (396, 67), (362, 67)], fill=(70, 88, 110))
    rect(d, 372, 55, 14, 7, fill=(70, 88, 110))
    # tanker hull (bow to the right)
    poly(d, [(52, 74), (398, 74), (434, 84), (420, 97), (66, 97), (52, 86)], fill=(27, 33, 46))
    poly(d, [(52, 90), (426, 90), (420, 97), (66, 97), (52, 93)], fill=RED)
    rect(d, 52, 70, 352, 4, fill=(16, 22, 34))
    # containers: two rows amidships
    cols = [RED, GOLD, (64, 128, 84), STEEL, (150, 70, 60), (70, 110, 150)]
    for row, (cy, ch) in enumerate(((54, 17), (36, 17))):
        n = 6 if row == 0 else 4
        for i in range(n):
            cx = 66 + i * 40
            col = cols[(i + row * 2) % len(cols)]
            rect(d, cx, cy, 37, ch, fill=col, outline=(30, 36, 48), width=1)
            line(d, [(cx + 12, cy + 2), (cx + 12, cy + ch - 2)], fill=(0, 0, 0), width=0.7)
            line(d, [(cx + 25, cy + 2), (cx + 25, cy + ch - 2)], fill=(0, 0, 0), width=0.7)
    # superstructure tower (stern, right of containers)
    rect(d, 322, 24, 46, 47, fill=(242, 244, 246), outline=(120, 130, 145), width=1)
    rect(d, 322, 33, 46, 9, fill=(28, 40, 60))
    for wx in range(327, 364, 9):
        rect(d, wx, 35.5, 5, 4, fill=(170, 205, 230))
    rect(d, 322, 48, 46, 3, fill=(200, 205, 212))
    rect(d, 330, 56, 30, 3, fill=(200, 205, 212))
    # funnel
    rect(d, 334, 8, 20, 17, fill=(30, 38, 52))
    rect(d, 334, 8, 20, 5, fill=RED)
    # mast at bow
    line(d, [(404, 74), (404, 50)], fill=(20, 26, 38), width=2)
    line(d, [(404, 52), (392, 60)], fill=(20, 26, 38), width=1.2)
    # flames amidships, above the container stack
    flame(d, 218, 40, 34, 40, [RED, (238, 110, 32), GOLD])
    flame(d, 248, 42, 24, 30, [RED, (238, 110, 32), (250, 205, 110)])
    flame(d, 192, 42, 20, 24, [(200, 60, 40), (238, 110, 32), GOLD])
    # wake behind stern (left)
    for i, wy in enumerate((88, 94, 100)):
        line(d, [(8 + i * 4, wy), (30, wy - 2), (50, wy)], fill=(210, 230, 245), width=1.5)
    # wave arcs
    rng = random.Random(21)
    for _ in range(26):
        wx = rng.uniform(6, pw - 26)
        wy = rng.uniform(102, ph - 6)
        wl = rng.uniform(9, 22)
        line(d, [(wx, wy), (wx + wl * 0.4, wy - 1.4), (wx + wl, wy)],
             fill=(178, 208, 232), width=1.3)
    # naval mines in the foreground water
    for mx, my, mr in ((398, 108, 11), (185, 111, 9)):
        for k in range(8):
            a = k * math.pi / 4
            line(d, [(mx + (mr - 1) * math.cos(a), my + (mr - 1) * math.sin(a)),
                     (mx + (mr + 6) * math.cos(a), my + (mr + 6) * math.sin(a))],
                 fill=(12, 15, 20), width=2)
            ell(d, mx + (mr + 6) * math.cos(a), my + (mr + 6) * math.sin(a), 1.8, 1.8,
                fill=(12, 15, 20))
        ell(d, mx, my, mr, mr, fill=(16, 19, 26))
        ell(d, mx - mr * 0.35, my - mr * 0.35, mr * 0.28, mr * 0.28, fill=(90, 100, 112))
    ell(d, 405, 101, 2.4, 2.4, fill=RED)
    ell(d, 406.5, 99.5, 1.1, 1.1, fill=WHITE)
    # smoke above flames and funnel
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    plume = [(224, 14, 30, 13, (60, 62, 70, 115)), (246, 6, 38, 15, (88, 90, 98, 95)),
             (206, 22, 22, 10, (80, 82, 90, 95)), (344, 2, 16, 7, (110, 112, 118, 70)),
             (262, 16, 24, 10, (105, 107, 113, 75))]
    for cx, cy, rx, ry, col in plume:
        od.ellipse([sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)], fill=col)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    chip(d, 10, ph - 28, "STRAIT OF HORMUZ")
    return img


# ---------------- ROW 2 RIGHT: Shenzhen summit ----------------

def flag_usa(d, x, y, w, h):
    stripe_h = h / 7.0
    for i in range(7):
        rect(d, x, y + i * stripe_h, w, stripe_h + 0.6,
             fill=RED if i % 2 == 0 else WHITE)
    cw, chh = w * 0.44, stripe_h * 4
    rect(d, x, y, cw, chh, fill=(38, 52, 110))
    for r_ in range(4):
        for c_ in range(5):
            ell(d, x + 5 + c_ * (cw - 9) / 4, y + 5 + r_ * (chh - 9) / 3, 1.7, 1.7, fill=WHITE)
    rrect(d, x, y, w, h, 1, outline=(90, 95, 105), width=1)


def flag_china(d, x, y, w, h):
    rect(d, x, y, w, h, fill=(206, 44, 40))
    poly(d, star_pts(x + 17, y + 15, 10, 4, 5), fill=GOLD)
    for sx, sy in ((36, 8), (41, 17), (41, 27), (35, 35)):
        poly(d, star_pts(x + sx, y + sy, 4.2, 1.7, 5), fill=GOLD)
    rrect(d, x, y, w, h, 1, outline=(120, 40, 38), width=1)


def flag_russia(d, x, y, w, h):
    third = h / 3.0
    rect(d, x, y, w, third + 0.6, fill=WHITE)
    rect(d, x, y + third, w, third + 0.6, fill=(43, 95, 170))
    rect(d, x, y + 2 * third, w, third + 0.6, fill=(206, 44, 40))
    rrect(d, x, y, w, h, 1, outline=(90, 95, 105), width=1)


def shenzhen_picture(pw, ph):
    img = Image.new("RGB", (sc(pw), sc(ph)), SKY)
    gradient_sub(img, pw, ph, (196, 222, 242), (236, 240, 244))
    d = ImageDraw.Draw(img)
    ground_y = 104
    # skyline towers
    rng = random.Random(11)
    towers = []
    tx = -6
    palette = [(90, 110, 130), (70, 95, 125), (110, 130, 155), (80, 102, 128)]
    ti = 0
    while tx < pw:
        tw = rng.uniform(26, 46)
        th = rng.uniform(42, 84)
        col = palette[ti % len(palette)]
        towers.append((tx, tw, th, col))
        tx += tw + rng.uniform(3, 8)
        ti += 1
    for tx, tw, th, col in towers:
        rect(d, tx, ground_y - th, tw, th, fill=col, outline=(52, 68, 90), width=1)
        rect(d, tx, ground_y - th, tw, 3, fill=(52, 68, 90))
        # lit windows
        wrng = random.Random(int(tx * 10) + 5)
        for wy in range(int(ground_y - th) + 7, ground_y - 6, 9):
            for wx in range(int(tx) + 4, int(tx + tw) - 4, 8):
                if wrng.random() < 0.42:
                    rect(d, wx, wy, 3.6, 4.6, fill=(250, 205, 115))
                elif wrng.random() < 0.5:
                    rect(d, wx, wy, 3.6, 4.6, fill=(168, 192, 214))
    # ground band
    rect(d, 0, ground_y, pw, ph - ground_y, fill=(52, 66, 84))
    rect(d, 0, ground_y, pw, 2.5, fill=(140, 155, 172))
    for gx in range(8, int(pw), 34):
        rect(d, gx, ground_y + 9, 16, 1.6, fill=(110, 126, 144))
    # three flagpoles with large flags
    flag_fns = (flag_usa, flag_china, flag_russia)
    for i, px in enumerate((64, 196, 328)):
        rrect(d, px + 3, 16, 100, 58, 1, fill=(160, 166, 174))  # flag shadow
        line(d, [(px, 10), (px, 112)], fill=(40, 48, 62), width=2.6)
        ell(d, px, 9, 3, 3, fill=GOLD)
        flag_fns[i](d, px + 3, 13, 100, 58)
        # subtle fold shading
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for fx in (px + 28, px + 62):
            od.rectangle([sc(fx), sc(13), sc(fx + 9), sc(71)], fill=(0, 0, 0, 22))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)
    chip(d, 10, ph - 28, "SHENZHEN \u2022 CHINA")
    return img


# ---------------- ROW 3 LEFT: Africa / Rwanda ----------------

AFRICA = [
    (38, 18), (56, 13), (78, 11), (100, 13), (118, 18), (128, 24),
    (131, 34), (140, 47), (141, 51), (130, 57), (124, 66), (121, 78),
    (119, 92), (114, 108), (106, 126), (96, 140), (84, 149), (72, 148),
    (62, 138), (54, 124), (48, 108), (43, 92), (48, 79), (40, 71),
    (26, 64), (19, 52), (20, 38), (27, 27), (32, 21),
]
MADAGASCAR = [(131, 100), (141, 106), (140, 124), (133, 142), (127, 128), (127, 109)]


def africa_picture(pw, ph):
    img = Image.new("RGB", (sc(pw), sc(ph)), (233, 239, 218))
    gradient_sub(img, pw, ph, (236, 242, 222), (219, 231, 198))
    d = ImageDraw.Draw(img)
    # faint graticule
    for gy in (36, 72, 108, 140):
        line(d, [(0, gy), (pw, gy)], fill=(205, 216, 188), width=1)
    for gx in (42, 84, 126):
        line(d, [(gx, 0), (gx, ph)], fill=(205, 216, 188), width=1)
    # continent + Madagascar
    poly(d, AFRICA, fill=(196, 168, 110), outline=INK, width=2)
    poly(d, MADAGASCAR, fill=(196, 168, 110), outline=INK, width=1.6)
    # Sahara shading (subtle)
    ell(d, 76, 34, 30, 13, fill=(205, 178, 118))
    # dashed arc Europe -> Rwanda (quadratic bezier, sampled)
    p0, p1, p2 = (13, 16), (30, 54), (101, 74)
    pts = []
    for i in range(41):
        t = i / 40.0
        bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((bx, by))
    for i in range(len(pts) - 1):
        if (i // 3) % 2 == 0:
            line(d, [pts[i], pts[i + 1]], fill=STEEL, width=1.8)
    ell(d, p0[0], p0[1], 2.4, 2.4, fill=STEEL)
    ef = get_font(10, True)
    d.text((sc(5), sc(2)), "EUROPE", font=ef, fill=INK)
    # Rwanda pin (east-central Africa)
    pin_x, pin_y = 104, 76
    poly(d, [(pin_x - 6, pin_y - 4), (pin_x + 6, pin_y - 4), (pin_x, pin_y + 10)], fill=RED)
    ell(d, pin_x, pin_y - 6, 7.5, 7.5, fill=RED, outline=WHITE, width=1.4)
    ell(d, pin_x, pin_y - 6, 2.8, 2.8, fill=WHITE)
    # label below the pin, with a short vertical leader from the pin tip
    lf = get_font(11.5, True)
    rtw = d.textlength("RWANDA", font=lf) / S
    line(d, [(pin_x, pin_y + 11), (pin_x, pin_y + 16)], fill=INK, width=1.2)
    d.text((sc(pin_x - rtw / 2 - 5), sc(pin_y + 17)), "RWANDA", font=lf, fill=INK)
    return img


# ---------------- ROW 3 RIGHT: AI chip ----------------

def octagon(d, cx, cy, r, **kw):
    pts = []
    for i in range(8):
        a = math.radians(22.5 + i * 45)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly(d, pts, **kw)


def chip_picture(pw, ph):
    img = Image.new("RGB", (sc(pw), sc(ph)), NAVY)
    gradient_sub(img, pw, ph, (30, 48, 76), (17, 29, 50))
    d = ImageDraw.Draw(img)
    cx0, cy0, cs = 47, 44, 72  # chip body box
    ccx, ccy = cx0 + cs / 2, cy0 + cs / 2
    trace_col = GOLD
    # circuit traces (orthogonal) running in from the edges, with pads
    traces = [
        [(0, 62), (30, 62), (30, 58), (cx0, 58)],
        [(0, 98), (24, 98), (24, 102), (cx0, 102)],
        [(66, 0), (66, 26), (70, 26), (70, cy0)],
        [(104, 0), (104, 22), (100, 22), (100, cy0)],
        [(cx0 + cs, 62), (140, 62), (140, 44), (pw, 44)],
        [(cx0 + cs, 96), (146, 96), (146, 122), (pw, 122)],
        [(70, cy0 + cs), (70, 138), (58, 138), (58, ph)],
        [(102, cy0 + cs), (102, 140), (116, 140), (116, ph)],
    ]
    for tr in traces:
        for i in range(len(tr) - 1):
            line(d, [tr[i], tr[i + 1]], fill=trace_col, width=2.4)
        ex, ey = tr[0]
        ell(d, ex if ex > 0 else 5, ey if ey < ph else ph - 5, 3.6, 3.6,
            outline=trace_col, width=1.8)
        ex, ey = tr[-1]
        if ex >= pw:
            ex = pw - 5
        if ey >= ph:
            ey = ph - 5
        ell(d, ex, ey, 3.2, 3.2, fill=trace_col)
    # extra decorative nodes
    for nx, ny in ((22, 30), (146, 140), (24, 134), (148, 18)):
        ell(d, nx, ny, 2.6, 2.6, outline=(150, 180, 210), width=1.4)
    # pins on all four sides
    for i in range(5):
        off = 10 + i * 13
        rect(d, cx0 + off, cy0 - 7, 5, 7, fill=trace_col)          # top
        rect(d, cx0 + off, cy0 + cs, 5, 7, fill=trace_col)        # bottom
        rect(d, cx0 - 7, cy0 + off, 7, 5, fill=trace_col)         # left
        rect(d, cx0 + cs, cy0 + off, 7, 5, fill=trace_col)        # right
    # chip body + inner die
    rrect(d, cx0, cy0, cs, cs, 6, fill=(36, 54, 82), outline=trace_col, width=2.6)
    rrect(d, cx0 + 13, cy0 + 13, cs - 26, cs - 26, 4, fill=(22, 36, 60),
          outline=(150, 180, 210), width=1.6)
    af = get_font(21, True)
    tw = d.textlength("AI", font=af) / S
    d.text((sc(ccx - tw / 2), sc(ccy - 13)), "AI", font=af, fill=WHITE)
    # blocked trace: red octagon stop sign on the right-hand trace
    octagon(d, 141, 30, 13, fill=RED, outline=WHITE, width=1.6)
    rect(d, 133.5, 28, 15, 4.4, fill=WHITE)
    line(d, [(119, 51), (132, 38)], fill=trace_col, width=2.4)
    return img


# ---------------- page assembly ----------------

M = 26
G = 14
PW_PAGE = W - 2 * M  # 972


def paste_pic(img, pic, x, y):
    img.paste(pic, (sc(x), sc(y)))


def build():
    random.seed(20261117)
    img = Image.new("RGB", (sc(W), sc(H)), PAPER)
    d = ImageDraw.Draw(img)

    # ---- MASTHEAD ----
    rect(d, M, 26, PW_PAGE, 120, fill=NAVY)
    rect(d, M, 26, PW_PAGE, 3, fill=GOLD)
    kf = get_font(21, True)
    kw = draw_centered(d, W / 2, 42, "T H E   W O R L D   I N   O N E   P I C T U R E", kf, GOLD)
    line(d, [(W / 2 - kw / 2 - 34, 53), (W / 2 - kw / 2 - 10, 53)], fill=GOLD, width=1.6)
    line(d, [(W / 2 + kw / 2 + 10, 53), (W / 2 + kw / 2 + 34, 53)], fill=GOLD, width=1.6)
    df = get_font(54, True)
    # shrink the date if it ever overflows the masthead
    while d.textlength("TUESDAY 17 NOVEMBER 2026", font=df) / S > PW_PAGE - 40:
        df = get_font(df.size / S - 2, True)
    draw_centered(d, W / 2, 74, "TUESDAY 17 NOVEMBER 2026", df, WHITE)
    sf = get_font(11.5, False)
    draw_centered(d, W / 2, 132 - 6, "", sf, WHITE)  # spacer (kept blank by design)
    rect(d, M, 146, PW_PAGE, 6, fill=RED)

    # ---- HERO ----
    hx, hy, hw, hh = M, 160, PW_PAGE, 318
    panel(d, hx, hy, hw, hh)
    hero_h = 188
    paste_pic(img, hero_picture(hw - 4, hero_h), hx + 2, hy + 2)
    d = ImageDraw.Draw(img)
    rrect(d, hx, hy, hw, hh, 5, outline=(176, 182, 194), width=1)
    text_block(d, hx + 16, hy + hero_h + 13, hw - 32,
               "CRIMEA \u2014 WAR IN UKRAINE",
               "UKRAINE DROPS CRIMEA BRIDGE ARCH",
               "A second strike in two days drops the road arch into the Kerch Strait "
               "and halts traffic on Russia's 19-km link to Crimea.",
               32, 38, 17, 46)

    # ---- ROW 2 ----
    r2y, r2h = 492, 236
    col_w = (PW_PAGE - G) / 2  # 479
    pic2_h = 126
    # left: tanker
    lx = M
    panel(d, lx, r2y, col_w, r2h)
    paste_pic(img, tanker_picture(col_w - 4, pic2_h), lx + 2, r2y + 2)
    d = ImageDraw.Draw(img)
    rrect(d, lx, r2y, col_w, r2h, 5, outline=(176, 182, 194), width=1)
    text_block(d, lx + 14, r2y + pic2_h + 12, col_w - 28,
               "THE GULF \u2014 ENERGY",
               "TANKERS HIT BY MINES OFF HORMUZ",
               "Iran says two oil tankers struck naval mines and caught fire; "
               "a third US carrier group arrives in the region.",
               22, 27, 15.5, 42, kicker_size=12)
    # right: Shenzhen
    rx = M + col_w + G
    panel(d, rx, r2y, col_w, r2h)
    paste_pic(img, shenzhen_picture(col_w - 4, pic2_h), rx + 2, r2y + 2)
    d = ImageDraw.Draw(img)
    rrect(d, rx, r2y, col_w, r2h, 5, outline=(176, 182, 194), width=1)
    text_block(d, rx + 14, r2y + pic2_h + 12, col_w - 28,
               "ASIA \u2014 DIPLOMACY",
               "XI, TRUMP, PUTIN TO MEET IN SHENZHEN",
               "China confirms the first three-way summit of the three leaders, "
               "set for Thursday on the APEC sidelines.",
               22, 27, 15.5, 42, kicker_size=12)

    # ---- ROW 3 ----
    r3y, r3h = 742, 164
    side_w = 168
    # left: Rwanda
    panel(d, lx, r3y, col_w, r3h)
    paste_pic(img, africa_picture(side_w, r3h - 4), lx + 2, r3y + 2)
    d = ImageDraw.Draw(img)
    rrect(d, lx, r3y, col_w, r3h, 5, outline=(176, 182, 194), width=1)
    tx = lx + side_w + 14
    text_block(d, tx, r3y + 14, lx + col_w - tx - 14,
               "EUROPE \u2014 MIGRATION",
               "EUROPE PLANS RWANDA RETURN HUB",
               "Five European nations plan a joint hub in Rwanda for people "
               "whose asylum claims were rejected.",
               19, 48, 14, 58, kicker_size=12)
    # right: AI chip
    panel(d, rx, r3y, col_w, r3h)
    paste_pic(img, chip_picture(side_w, r3h - 4), rx + 2, r3y + 2)
    d = ImageDraw.Draw(img)
    rrect(d, rx, r3y, col_w, r3h, 5, outline=(176, 182, 194), width=1)
    tx = rx + side_w + 14
    text_block(d, tx, r3y + 14, rx + col_w - tx - 14,
               "WASHINGTON \u2014 TECH",
               "US MOVES TO CLOSE AI-CHIP LOOPHOLE",
               "Washington moves to block China's remote access to advanced AI "
               "chips and tighten sales via Southeast Asia.",
               19, 48, 14, 58, kicker_size=12)

    # ---- FOOTER: IN BRIEF ----
    fy, fh = 920, 78
    rrect(d, M + 3, fy + 4, PW_PAGE, fh, 5, fill=(203, 198, 188))
    rrect(d, M, fy, PW_PAGE, fh, 5, fill=WHITE, outline=NAVY, width=1.6)
    rect(d, M, fy, 86, fh, fill=RED)
    rrect(d, M, fy, 86, fh, 5, fill=RED)
    rect(d, M + 40, fy, 46, fh, fill=RED)  # square off the tab's right edge
    ibf = get_font(16, True)
    draw_centered(d, M + 43, fy + 18, "IN", ibf, WHITE)
    draw_centered(d, M + 43, fy + 40, "BRIEF", ibf, WHITE)
    briefs = [
        ("PENTAGON FAILS AUDIT \u2014 9TH YEAR",
         "US defence books fail their financial audit for a ninth straight year."),
        ("SOUTH AFRICA SHOOTINGS KILL 17",
         "Two separate attacks leave 17 people dead."),
        ("JPMORGAN OUTAGE DISRUPTS ZELLE",
         "A technical issue at JPMorgan Chase disrupts online banking and Zelle."),
    ]
    col_x = M + 86
    colw = (PW_PAGE - 86) / 3
    for i, (head, sub) in enumerate(briefs):
        cx = col_x + i * colw + 13
        cw = colw - 24
        if i:
            line(d, [(col_x + i * colw, fy + 10), (col_x + i * colw, fy + fh - 10)],
                 fill=(205, 208, 216), width=1)
        hf, hs, hlines = fit_text(d, head, cw, 17, 14, 10.5, True, 1.12)
        draw_lines(d, cx, fy + 10, hlines, hf, hs, INK, 1.12)
        sf2, ss, slines = fit_text(d, sub, cw, 34, 12.5, 10, False, 1.2)
        draw_lines(d, cx, fy + 31, slines, sf2, ss, DARKGREY, 1.2)

    img = img.resize((W, H), Image.LANCZOS)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, format="PNG", optimize=True)
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    build()
