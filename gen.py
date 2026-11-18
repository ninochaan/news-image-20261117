#!/usr/bin/env python3
"""Generate entry.png for make.fun news-image-20261117.

Deterministic PIL drawing of a newspaper front page summing up the
world news of Tuesday 17 November 2026. No network, no timestamps,
fixed seed, fixed fonts.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SEED = 20261117
W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (20, 33, 61)
RED = (193, 39, 45)
GOLD = (232, 163, 61)
SKY = (214, 231, 242)
SEA = (46, 90, 136)
STEEL = (90, 110, 130)
DARK = (24, 40, 66)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, fnt, cx, y, fill, spacing=4):
    for line in lines:
        w = draw.textlength(line, font=fnt)
        draw.text((cx - w / 2, y), line, font=fnt, fill=fill)
        y += fnt.size + spacing
    return y


def starburst(draw, cx, cy, r_out, r_in, points, fill):
    pts = []
    for i in range(points * 2):
        ang = 3.14159265 * i / points - 3.14159265 / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * __import__("math").cos(ang),
                    cy + r * __import__("math").sin(ang)))
    draw.polygon(pts, fill=fill)


def panel(draw, x0, y0, x1, y1, headline, caption, hsize, csize, pic,
          pic_frac=0.62):
    """One story panel: pictogram band on top, headline + caption below."""
    draw.rectangle([x0, y0, x1, y1], outline=INK, width=2)
    pic_h = int((y1 - y0) * pic_frac)
    pic(draw, x0 + 2, y0 + 2, x1 - 2, y0 + pic_h)
    draw.line([x0, y0 + pic_h, x1, y0 + pic_h], fill=INK, width=2)
    cf = font(FONT_REG, csize)
    avail = (y1 - y0) - pic_h - 12
    # auto-fit: shrink the headline until headline + caption fit the panel
    while hsize > 12:
        hf = font(FONT_BOLD, hsize)
        lines = wrap(draw, headline, hf, (x1 - x0) - 24)
        cap = wrap(draw, caption, cf, (x1 - x0) - 28)
        need = len(lines) * (hsize + 2) + 2 + len(cap) * (csize + 2)
        if need <= avail:
            break
        hsize -= 1
    hf = font(FONT_BOLD, hsize)
    lines = wrap(draw, headline, hf, (x1 - x0) - 24)
    cap = wrap(draw, caption, cf, (x1 - x0) - 28)
    cx = (x0 + x1) / 2
    ty = y0 + pic_h + 10
    ty = draw_lines(draw, lines, hf, cx, ty, INK, spacing=2)
    draw_lines(draw, cap, cf, cx, ty + 2, (70, 80, 100), spacing=2)


# ---------------------------------------------------------------- pictograms

def pic_bridge(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=SKY)
    w, h = x1 - x0, y1 - y0
    sea_y = y0 + int(h * 0.72)
    draw.rectangle([x0, sea_y, x1, y1], fill=SEA)
    # waves
    for i in range(6):
        wx = x0 + i * (w // 6) + 8
        draw.arc([wx, sea_y + 8, wx + 34, sea_y + 26], 180, 360,
                 fill=(255, 255, 255), width=3)
    deck_y = y0 + int(h * 0.52)
    gap_cx = x0 + w // 2
    gap = 46
    # deck segments, broken in the middle
    draw.rectangle([x0 + 14, deck_y, gap_cx - gap, deck_y + 12], fill=DARK)
    draw.rectangle([gap_cx + gap, deck_y, x1 - 14, deck_y + 12], fill=DARK)
    # tilted broken slab falling into the gap
    draw.polygon([(gap_cx - gap, deck_y + 12), (gap_cx - 8, deck_y + 12),
                  (gap_cx + 26, deck_y + 44), (gap_cx - 6, deck_y + 40)],
                 fill=STEEL)
    # pillars
    for px in (x0 + int(w * 0.22), x1 - int(w * 0.22)):
        draw.rectangle([px - 8, deck_y + 12, px + 8, sea_y + 6], fill=DARK)
    # support towers
    for px in (x0 + int(w * 0.30), x1 - int(w * 0.30)):
        draw.rectangle([px - 5, y0 + int(h * 0.18), px + 5, deck_y], fill=DARK)
    # blast at the gap
    starburst(draw, gap_cx, deck_y - 6, 52, 22, 10, GOLD)
    starburst(draw, gap_cx, deck_y - 6, 34, 14, 10, RED)
    starburst(draw, gap_cx, deck_y - 6, 18, 8, 8, (255, 240, 180))
    # smoke
    for sx, sy, sr in ((gap_cx - 58, deck_y - 52, 16),
                       (gap_cx - 30, deck_y - 74, 20),
                       (gap_cx + 44, deck_y - 60, 17)):
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                     fill=(120, 125, 130))


def pic_tanker(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=SKY)
    w, h = x1 - x0, y1 - y0
    sea_y = y0 + int(h * 0.62)
    draw.rectangle([x0, sea_y, x1, y1], fill=SEA)
    hull_y = y0 + int(h * 0.34)
    # hull
    draw.polygon([(x0 + 20, hull_y), (x1 - 20, hull_y),
                  (x1 - 44, hull_y + 34), (x0 + 44, hull_y + 34)], fill=DARK)
    draw.rectangle([x0 + 20, hull_y - 6, x1 - 20, hull_y], fill=RED)
    # containers
    cols = [RED, GOLD, (70, 130, 90), STEEL]
    cw = (w - 90) // 4
    for i, c in enumerate(cols):
        draw.rectangle([x0 + 34 + i * cw, hull_y - 34,
                        x0 + 34 + (i + 1) * cw - 6, hull_y - 6], fill=c)
    # bridge tower
    draw.rectangle([x1 - 74, hull_y - 62, x1 - 34, hull_y - 6], fill=(240, 240, 235))
    draw.rectangle([x1 - 74, hull_y - 62, x1 - 34, hull_y - 50], fill=INK)
    # flames amidships
    fx = x0 + w // 2 - 20
    for (dx, fh, col) in ((0, 52, RED), (14, 66, (240, 110, 30)),
                          (30, 44, GOLD)):
        draw.polygon([(fx + dx, hull_y - 6), (fx + dx + 12, hull_y - 6 - fh),
                      (fx + dx + 26, hull_y - 6)], fill=col)
    # smoke
    for sx, sy, sr in ((fx + 8, hull_y - 78, 13), (fx + 30, hull_y - 96, 16),
                       (fx + 52, hull_y - 76, 12)):
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                     fill=(120, 125, 130))
    # waves
    for i in range(5):
        wx = x0 + i * (w // 5) + 6
        draw.arc([wx, sea_y + 10, wx + 30, sea_y + 26], 180, 360,
                 fill=(255, 255, 255), width=3)


def pic_summit(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=SKY)
    w, h = x1 - x0, y1 - y0
    base = y1 - 8
    # Shenzhen skyline
    heights = [0.42, 0.60, 0.34, 0.72, 0.48, 0.66, 0.38]
    bw = w // len(heights)
    for i, frac in enumerate(heights):
        bh = int(h * frac)
        draw.rectangle([x0 + 6 + i * bw, base - bh,
                        x0 + 6 + (i + 1) * bw - 6, base], fill=STEEL)
        # lit windows
        for wy in range(base - bh + 8, base - 6, 14):
            draw.rectangle([x0 + 12 + i * bw, wy,
                            x0 + 18 + i * bw, wy + 6], fill=GOLD)
    # three flags
    pole_y0 = y0 + int(h * 0.16)
    pole_y1 = base - int(h * 0.30)
    fx = [x0 + int(w * 0.20), x0 + int(w * 0.50), x0 + int(w * 0.80)]
    flags = ["us", "cn", "ru"]
    for px, kind in zip(fx, flags):
        draw.rectangle([px - 2, pole_y0, px + 2, pole_y1], fill=INK)
        fw, fh = 52, 32
        if kind == "us":
            for s in range(7):
                col = RED if s % 2 == 0 else (255, 255, 255)
                draw.rectangle([px + 2, pole_y0 + s * (fh // 7),
                                px + 2 + fw, pole_y0 + (s + 1) * (fh // 7)],
                               fill=col)
            draw.rectangle([px + 2, pole_y0, px + 2 + 22, pole_y0 + 15],
                           fill=INK)
        elif kind == "cn":
            draw.rectangle([px + 2, pole_y0, px + 2 + fw, pole_y0 + fh],
                           fill=RED)
            starburst(draw, px + 12, pole_y0 + 10, 7, 3, 5, GOLD)
        else:
            for s, col in enumerate([(255, 255, 255), (40, 90, 180), RED]):
                draw.rectangle([px + 2, pole_y0 + s * (fh // 3),
                                px + 2 + fw, pole_y0 + (s + 1) * (fh // 3)],
                               fill=col)
    draw.rectangle([x0, base, x1, y1], fill=(70, 90, 70))


def pic_africa(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(232, 238, 226))
    w, h = x1 - x0, y1 - y0
    # Africa drawn inside a centred box so it is not squashed flat
    bx0, bx1 = x0 + int(w * 0.24), x0 + int(w * 0.76)
    by0, by1 = y0 + 4, y1 - 4
    bw, bh = bx1 - bx0, by1 - by0
    # rough Africa outline (normalised coords)
    pts_n = [(0.30, 0.10), (0.52, 0.06), (0.74, 0.12), (0.86, 0.24),
             (0.82, 0.40), (0.66, 0.50), (0.60, 0.62), (0.56, 0.82),
             (0.50, 0.94), (0.44, 0.72), (0.38, 0.56), (0.22, 0.48),
             (0.14, 0.32), (0.18, 0.16)]
    pts = [(bx0 + px * bw, by0 + py * bh) for px, py in pts_n]
    draw.polygon(pts, fill=(196, 168, 110), outline=INK, width=2)
    # map pin over east-central Africa
    pin_x = bx0 + int(bw * 0.62)
    pin_y = by0 + int(bh * 0.42)
    draw.polygon([(pin_x - 13, pin_y + 4), (pin_x + 13, pin_y + 4),
                  (pin_x, pin_y + 30)], fill=RED)
    draw.ellipse([pin_x - 14, pin_y - 22, pin_x + 14, pin_y + 6], fill=RED)
    draw.ellipse([pin_x - 6, pin_y - 14, pin_x + 6, pin_y - 2], fill=PAPER)
    # dashed route line from Europe (top-left corner) toward the pin
    for i in range(5):
        dx = x0 + 12 + i * 9
        dy = y0 + 10 + i * 5
        draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=INK)


def pic_chip(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=DARK)
    w, h = x1 - x0, y1 - y0
    cx, cy = x0 + w // 2, y0 + h // 2
    side = int(min(w, h) * 0.52)
    # pins
    for i in range(4):
        off = -side // 2 + i * (side // 3) + side // 6
        draw.rectangle([cx + off - 3, cy - side // 2 - 14,
                        cx + off + 3, cy - side // 2], fill=GOLD)
        draw.rectangle([cx + off - 3, cy + side // 2,
                        cx + off + 3, cy + side // 2 + 14], fill=GOLD)
        draw.rectangle([cx - side // 2 - 14, cy + off - 3,
                        cx - side // 2, cy + off + 3], fill=GOLD)
        draw.rectangle([cx + side // 2, cy + off - 3,
                        cx + side // 2 + 14, cy + off + 3], fill=GOLD)
    draw.rectangle([cx - side // 2, cy - side // 2,
                    cx + side // 2, cy + side // 2],
                   fill=(40, 56, 84), outline=GOLD, width=3)
    inner = side // 2
    draw.rectangle([cx - inner // 2, cy - inner // 2,
                    cx + inner // 2, cy + inner // 2], fill=INK)
    tf = font(FONT_BOLD, 20)
    t = "AI"
    tw = draw.textlength(t, font=tf)
    draw.text((cx - tw / 2, cy - 11), t, font=tf, fill=(255, 255, 255))
    # circuit traces
    for (sx, sy, ex, ey) in ((x0 + 8, y0 + 10, cx - side // 2, cy - side // 2),
                             (x1 - 8, y0 + 12, cx + side // 2, cy - side // 2),
                             (x0 + 10, y1 - 10, cx - side // 2, cy + side // 2),
                             (x1 - 10, y1 - 12, cx + side // 2, cy + side // 2)):
        draw.line([sx, sy, ex, ey], fill=GOLD, width=2)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=GOLD)


# ---------------------------------------------------------------- main

def main():
    random.seed(SEED)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M, G = 28, 16

    # masthead
    d.rectangle([M, M, W - M, 148], fill=INK)
    sub = font(FONT_BOLD, 22)
    t = "T H E   W O R L D   I N   O N E   P I C T U R E"
    tw = d.textlength(t, font=sub)
    d.text(((W - tw) / 2, 40), t, font=sub, fill=GOLD)
    big = font(FONT_BOLD, 56)
    t = "TUESDAY 17 NOVEMBER 2026"
    tw = d.textlength(t, font=big)
    d.text(((W - tw) / 2, 74), t, font=big, fill=(255, 255, 255))
    d.line([M, 148, W - M, 148], fill=RED, width=6)

    # hero: Crimea bridge
    panel(d, M, 164, W - M, 452,
          "UKRAINE HITS CRIMEA BRIDGE AGAIN",
          "Second strike in under 24 hours; road traffic suspended.",
          30, 17, pic_bridge)

    # row 2: Hormuz tankers / Shenzhen summit
    half = (W - 2 * M - G) // 2
    panel(d, M, 468, M + half, 700,
          "TANKERS HIT BY MINES OFF HORMUZ",
          "Mines hit tankers off Hormuz; a third US carrier arrived.",
          23, 15, pic_tanker)
    panel(d, M + half + G, 468, W - M, 700,
          "XI, TRUMP, PUTIN TO MEET IN SHENZHEN",
          "First three-way talks set for Thursday in Shenzhen.",
          23, 15, pic_summit)

    # row 3: Rwanda hub / AI-chip loophole
    panel(d, M, 716, M + half, 868,
          "EUROPE PLANS RWANDA RETURN HUB",
          "Five nations plan a joint hub for rejected asylum seekers.",
          20, 14, pic_africa, pic_frac=0.50)
    panel(d, M + half + G, 716, W - M, 868,
          "US MOVES TO CLOSE AI-CHIP LOOPHOLE",
          "Washington tightens processor sales to Southeast Asia.",
          20, 14, pic_chip, pic_frac=0.50)

    # footer: ALSO strip
    fy0, fy1 = 884, 996
    d.rectangle([M, fy0, W - M, fy1], outline=INK, width=2)
    d.rectangle([M, fy0, M + 96, fy1], fill=RED)
    af = font(FONT_BOLD, 20)
    t = "ALSO:"
    tw = d.textlength(t, font=af)
    d.text((M + (96 - tw) / 2, fy0 + (fy1 - fy0 - 20) / 2), t,
           font=af, fill=(255, 255, 255))
    ff = font(FONT_REG, 15)
    items = ("Pentagon fails its financial audit for the ninth year in a row  |  "
             "17 people killed in two separate shootings in South Africa  |  "
             "A technical issue at JPMorgan Chase disrupted online banking and Zelle.")
    lines = wrap(d, items, ff, (W - M) - (M + 96) - 24)
    y = fy0 + 12
    for line in lines:
        d.text((M + 96 + 12, y), line, font=ff, fill=INK)
        y += 15 + 5

    out = Path(__file__).resolve().parent / "entry.png"
    img.save(out, "PNG")
    print(f"wrote {out} {img.size}")


if __name__ == "__main__":
    main()
