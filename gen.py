#!/usr/bin/env python3
"""Generate the 21 November 2026 world-news front page (1024x1024 PNG).

Original vector-style broadsheet drawn from scratch with Pillow: no photos,
no downloads, no network, no randomness. Every story was checked against
news reported on Saturday 21 November 2026 (UTC).
Deterministic: same input -> same bytes.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (246, 241, 229)
INK = (20, 20, 20)
RED = (178, 34, 24)
DARKRED = (140, 20, 12)
BLUE = (29, 64, 175)
TEAL = (13, 110, 110)
GREEN = (28, 110, 44)
ORANGE = (190, 90, 10)
PURPLE = (110, 60, 150)
GREY = (90, 90, 88)
LIGHT = (232, 226, 210)
SEA = (196, 216, 228)
LAND = (238, 228, 200)
SAND = (226, 212, 172)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS_O = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"

_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def fit(path, text, maxw, start):
    size = start
    while size > 8 and F(path, size).getlength(text) > maxw:
        size -= 1
    return F(path, size)


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, text, font, maxw, fill=INK, leading=None, max_lines=None):
    lines = wrap(d, text, font, maxw)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading or int(font.size * 1.22)
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def rule(d, x, y, w, fill=INK, width=1):
    d.line([(x, y), (x + w, y)], fill=fill, width=width)


def tag(d, x, y, text, bg, fg=(255, 255, 255), font=None, pad=4):
    font = font or F(SANS_B, 9)
    w = int(d.textlength(text, font=font)) + pad * 2
    h = font.size + pad
    d.rectangle([x, y, x + w, y + h], fill=bg)
    d.text((x + pad, y + pad // 2), text, font=font, fill=fg)
    return w


def kicker(d, x, y, region, color, label, right=None):
    d.text((x, y), region, font=F(SANS_B, 10), fill=color)
    if right:
        rw = int(d.textlength(right, font=F(SANS_B, 9)))
        d.rectangle([x + 322 - rw - 8, y - 1, x + 322, y + 11], outline=color, width=1)
        d.text((x + 322 - rw - 4, y), right, font=F(SANS_B, 9), fill=color)
    return y + 13


# ---------------------------------------------------------------- maps
def project(x0, y0, w, h, lon, lat):
    return (x0 + (lon + 180.0) / 360.0 * w, y0 + (90.0 - lat) / 180.0 * h)


NA = [(-168, 66), (-140, 70), (-120, 72), (-95, 72), (-85, 70), (-80, 73),
      (-65, 60), (-55, 52), (-60, 45), (-75, 35), (-80, 25), (-85, 30),
      (-95, 20), (-100, 16), (-105, 20), (-110, 24), (-115, 30), (-125, 40), (-125, 50),
      (-140, 60), (-165, 60)]
SA = [(-80, 10), (-60, 5), (-50, 0), (-35, -5), (-40, -20), (-50, -30),
      (-60, -40), (-70, -50), (-75, -35), (-70, -20), (-80, -5)]
AF = [(-15, 35), (-5, 35), (10, 37), (20, 32), (30, 30), (35, 28),
      (40, 15), (50, 10), (40, 0), (40, -15), (35, -25), (25, -35),
      (15, -30), (10, -15), (5, 5), (-10, 5), (-15, 15)]
EU = [(-10, 37), (-5, 43), (-2, 48), (0, 50), (5, 55), (10, 57), (18, 55),
      (20, 60), (25, 65), (30, 70), (40, 68), (45, 60), (40, 50), (30, 45),
      (20, 40), (15, 38), (10, 37), (0, 36)]
AS = [(40, 68), (60, 70), (80, 73), (100, 75), (120, 73), (140, 72),
      (160, 70), (175, 65), (160, 60), (140, 50), (130, 40), (120, 35),
      (110, 25), (100, 15), (95, 10), (90, 20), (80, 10), (75, 5),
      (70, 20), (60, 25), (50, 30), (45, 40), (40, 45)]
AU = [(115, -20), (125, -15), (135, -12), (142, -10), (150, -20),
      (150, -35), (140, -38), (130, -32), (120, -35), (113, -25)]
CONTINENTS = [NA, SA, AF, EU, AS, AU]

PINS = [(50.5, 26.2), (-108.5, 25.6), (30.7, 36.9), (33.4, 47.9),
        (-74.0, 40.7), (24.5, 59.8), (-43.9, -19.9), (127.4, -7.7),
        (4.35, 50.85), (6.14, 46.2)]


def world_map(d, x, y, w, h, pins=True):
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 235), outline=INK, width=1)
    for poly in CONTINENTS:
        pts = [project(x, y, w, h, lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=(120, 110, 85))
    d.text((x + 6, y + 4), "ATLANTIC", font=F(SANS, 8), fill=(90, 120, 140))
    d.text((x + w - 52, y + h - 14), "PACIFIC", font=F(SANS, 8), fill=(90, 120, 140))
    if pins:
        drawn = []
        for i, (lon, lat) in enumerate(PINS, 1):
            px, py = project(x, y, w, h, lon, lat)
            for _ in range(2):
                if any((px - qx) ** 2 + (py - qy) ** 2 < 14 ** 2 for qx, qy in drawn):
                    px += 10
                    py -= 6
                else:
                    break
            drawn.append((px, py))
            ox, oy = project(x, y, w, h, lon, lat)
            if (px, py) != (ox, oy):
                d.line([(ox, oy), (px, py)], fill=RED, width=1)
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=RED,
                      outline=(255, 255, 255), width=1)
            d.text((px - 3, py - 6), str(i), font=F(SANS_B, 8), fill=(255, 255, 255))


# ---------------------------------------------------------------- illustrations
def ill_gulf(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    # Arabian peninsula (bottom) and Iran (top right)
    d.polygon([(x + 30, y + h), (x + 90, y + 58), (x + 150, y + 62),
               (x + 210, y + 78), (x + 250, y + h)], fill=LAND,
              outline=(120, 110, 85))
    d.polygon([(x + 120, y), (x + w, y), (x + w, y + 34), (x + 200, y + 44),
               (x + 130, y + 40)], fill=LAND, outline=(120, 110, 85))
    d.polygon([(x, y + 40), (x + 60, y + 30), (x + 95, y + 52),
               (x + 40, y + 66), (x, y + 62)], fill=LAND, outline=(120, 110, 85))
    d.text((x + 225, y + 6), "IRAN", font=F(SANS_B, 11), fill=INK)
    d.text((x + 8, y + h - 16), "SAUDI ARABIA", font=F(SANS_B, 9), fill=INK)
    d.text((x + 112, y + 80), "STRAIT OF HORMUZ", font=F(SANS_B, 8), fill=(60, 90, 110))
    # missile arc from Iran to Bahrain
    d.arc([x + 120, y - 6, x + 280, y + 78], start=200, end=340, fill=RED, width=2)
    # Bahrain
    bx, by = x + 118, y + 58
    d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=RED, outline=(255, 255, 255), width=2)
    d.text((bx - 26, by + 11), "BAHRAIN", font=F(SANS_B, 9), fill=RED)
    # tanker + flame
    tx, ty = x + 230, y + 66
    d.rectangle([tx, ty, tx + 52, ty + 10], fill=(40, 40, 40))
    d.rectangle([tx + 38, ty - 8, tx + 52, ty], fill=(40, 40, 40))
    d.polygon([(tx + 12, ty - 2), (tx + 18, ty - 14), (tx + 24, ty - 2)],
              fill=(255, 140, 0))
    d.polygon([(tx + 16, ty - 2), (tx + 20, ty - 10), (tx + 24, ty - 2)],
              fill=(255, 220, 0))
    d.text((tx - 6, ty + 13), "TANKER HIT", font=F(SANS_B, 8), fill=INK)


def ill_mexico(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    d.polygon([(x + 20, y + 8), (x + 130, y + 6), (x + 210, y + 18),
               (x + 300, y + 30), (x + 318, y + 52), (x + 260, y + 62),
               (x + 210, y + 78), (x + 170, y + h), (x + 120, y + h),
               (x + 110, y + 70), (x + 60, y + 55), (x + 15, y + 40)],
              fill=LAND, outline=(120, 110, 85))
    d.polygon([(x + 60, y + 55), (x + 110, y + 70), (x + 120, y + h),
               (x + 40, y + h), (x + 15, y + 70)], fill=(190, 205, 220))
    d.text((x + 150, y + 8), "MEXICO", font=F(SANS_B, 11), fill=INK)
    d.text((x + 12, y + h - 30), "GULF OF", font=F(SANS_B, 8), fill=(60, 90, 110))
    d.text((x + 12, y + h - 20), "CALIFORNIA", font=F(SANS_B, 8), fill=(60, 90, 110))
    gx, gy = x + 92, y + 52
    d.ellipse([gx - 10, gy - 10, gx + 10, gy + 10], fill=RED,
              outline=(255, 255, 255), width=2)
    d.text((gx - 24, gy + 12), "GUASAVE", font=F(SANS_B, 9), fill=RED)
    d.rectangle([x + w - 92, y + 6, x + w - 6, y + 26], fill=INK)
    d.text((x + w - 86, y + 10), "FBI TOP TEN", font=F(SANS_B, 10), fill=(255, 255, 255))
    d.rectangle([x + w - 92, y + h - 26, x + w - 6, y + h - 6], fill=RED)
    d.text((x + w - 84, y + h - 22), "CAPTURED", font=F(SANS_B, 10), fill=(255, 255, 255))


def ill_cop31(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    d.text((x + 10, y + 6), "ANTALYA  ·  NOVEMBER 2026", font=F(SANS_B, 10), fill=INK)
    cw, ch = 40, 30
    for i, day in enumerate([16, 17, 18, 19, 20, 21]):
        bx = x + 10 + i * (cw + 6)
        by = y + 26
        if day == 21:
            d.rectangle([bx, by, bx + cw, by + ch], fill=RED)
            d.text((bx + 8, by + 6), "21", font=F(SANS_B, 16), fill=(255, 255, 255))
            d.text((bx + 2, by + ch + 3), "SAT · DUE", font=F(SANS_B, 7), fill=RED)
        else:
            d.rectangle([bx, by, bx + cw, by + ch], outline=GREY, width=1)
            d.text((bx + 11, by + 6), str(day), font=F(SANS_B, 14), fill=INK)
    d.text((x + 10, y + 60), "DRAFT TEXT:", font=F(SANS_B, 10), fill=INK)
    d.text((x + 10, y + 74), "fossil fuels", font=F(SERIF_I, 13), fill=GREY)
    d.line([(x + 8, y + 81), (x + 88, y + 81)], fill=RED, width=2)
    d.text((x + 105, y + 76), "not mentioned", font=F(SANS_B, 11), fill=RED)
    d.rectangle([x + w - 118, y + h - 24, x + w - 8, y + h - 4], fill=INK)
    d.text((x + w - 106, y + h - 19), "NO DEAL YET", font=F(SANS_B, 11),
           fill=(255, 255, 255))


def ill_blast(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 38, 44), outline=INK, width=1)
    for bx, bw, bh in [(8, 26, 26), (40, 20, 38), (66, 30, 20), (102, 18, 32),
                       (126, 26, 24), (158, 20, 36), (184, 24, 18)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(70, 70, 78))
    cx, cy = x + w // 2, y + 26
    d.polygon([(cx, cy - 16), (cx + 5, cy - 5), (cx + 16, cy - 6), (cx + 8, cy + 3),
               (cx + 12, cy + 14), (cx, cy + 8), (cx - 12, cy + 14),
               (cx - 8, cy + 3), (cx - 16, cy - 6), (cx - 5, cy - 5)],
              fill=(255, 200, 0), outline=(255, 120, 0))
    d.text((x + 8, y + h - 16), "KRYVYI RIH · NIGHT", font=F(SANS_B, 8), fill=(255, 255, 255))


def ill_chart(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    pts = [(x + 8, y + 16), (x + 50, y + 20), (x + 90, y + 14), (x + 130, y + 24),
           (x + 170, y + 32), (x + 205, y + 36)]
    d.line(pts, fill=RED, width=3)
    d.text((x + 8, y + 2), "NASDAQ \u00b7 FRI", font=F(SANS_B, 8), fill=INK)
    d.text((x + w - 62, y + 2), "-5.3%", font=F(SANS_B, 13), fill=RED)


def ill_ship(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    d.rectangle([x + 30, y + 26, x + 180, y + 38], fill=(40, 40, 40))
    for cx, col in [(40, (200, 60, 40)), (80, (40, 90, 160)), (120, (200, 160, 40)),
                    (155, (60, 140, 90))]:
        d.rectangle([x + cx, y + 12, x + cx + 26, y + 26], fill=col)
    d.polygon([(x + 105, y + 12), (x + 112, y - 2), (x + 119, y + 12)],
              fill=(255, 140, 0))
    d.ellipse([x + 170, y + 2, x + 186, y + 14], fill=(120, 120, 120))
    d.ellipse([x + 178, y + 6, x + 196, y + 18], fill=(150, 150, 150))
    d.text((x + 6, y + 2), "SPARTA II", font=F(SANS_B, 8), fill=INK)


def ill_mosquito(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    d.ellipse([x + 60, y + 12, x + 150, y + 30], fill=(200, 220, 235),
              outline=(120, 140, 160))
    d.ellipse([x + 30, y + 20, x + 95, y + 32], fill=(60, 60, 60))
    for lx in (45, 60, 75):
        d.line([(x + lx, y + 30), (x + lx - 8, y + 40)], fill=INK, width=1)
        d.line([(x + lx, y + 30), (x + lx + 8, y + 40)], fill=INK, width=1)
    d.rectangle([x + 160, y + 10, x + 196, y + 30], fill=TEAL)
    d.text((x + 163, y + 13), "-69%", font=F(SANS_B, 12), fill=(255, 255, 255))
    d.text((x + 6, y + 2), "WOLBACHIA", font=F(SANS_B, 8), fill=INK)


def ill_quake(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    pts = [(x + 6, y + 26)]
    for i in range(1, 20):
        px = x + 6 + i * 10
        py = y + 26 + (9 if i % 4 == 1 else (-9 if i % 4 == 3 else 0))
        pts.append((px, py))
    d.line(pts, fill=RED, width=2)
    d.text((x + 8, y + 2), "M6.8 BANDA SEA \u00b7 M6.7 PERU", font=F(SANS_B, 9), fill=INK)


def ill_mercury(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 16, 28), outline=INK, width=1)
    d.ellipse([x + 30, y + 8, x + 90, y + 40], outline=(200, 200, 220), width=1)
    d.ellipse([x + 120, y + 6, x + 172, y + 38], fill=(180, 170, 150))
    for cx, cy, r in [(135, 18, 4), (150, 26, 5), (142, 32, 3), (160, 14, 3)]:
        d.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r], fill=(140, 130, 115))
    d.ellipse([x + 56, y + 20, x + 62, y + 26], fill=(255, 220, 0))
    d.rectangle([x + 4, y + h - 15, x + 122, y + h - 2], fill=(16, 16, 28))
    d.text((x + 8, y + h - 14), "BEPICOLOMBO \u00b7 8 YRS", font=F(SANS_B, 8), fill=(255, 255, 255))


def ill_trade(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    d.ellipse([x + 14, y + 6, x + 62, y + 38], fill=BLUE)
    for i in range(8):
        import math
        a = i * 3.14159 / 4
        d.ellipse([x + 38 + int(16 * math.cos(a)) - 2, y + 22 + int(12 * math.sin(a)) - 2,
                   x + 38 + int(16 * math.cos(a)) + 2, y + 22 + int(12 * math.sin(a)) + 2],
                  fill=(255, 220, 0))
    d.rectangle([x + 80, y + 4, x + 130, y + 20], fill=RED)
    d.rectangle([x + 80, y + 4, x + 130, y + 12], fill=(255, 255, 255))
    d.text((x + 140, y + 6), "98.5%", font=F(SANS_B, 15), fill=INK)
    d.text((x + 8, y + h - 11), "EU\u2013INDONESIA PACT", font=F(SANS_B, 8), fill=INK)


def ill_robot(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK, width=1)
    d.rectangle([x + 70, y + 6, x + 130, y + 36], fill=(120, 130, 145),
                outline=INK, width=1)
    d.ellipse([x + 84, y + 14, x + 96, y + 26], fill=(255, 220, 0))
    d.ellipse([x + 106, y + 14, x + 118, y + 26], fill=(255, 220, 0))
    d.line([(x + 78, y + 30), (x + 122, y + 30)], fill=INK, width=2)
    d.line([(x + 100, y + 6), (x + 100, y + 1)], fill=INK, width=2)
    d.text((x + 8, y + 2), "DRAFT BY", font=F(SANS_B, 9), fill=INK)
    d.text((x + 140, y + 12), "2028", font=F(SANS_B, 16), fill=INK)
    d.text((x + 8, y + h - 14), "GENEVA", font=F(SANS_B, 8), fill=INK)


# ---------------------------------------------------------------- content
LEADS = [
    dict(region="MIDDLE EAST", color=RED, status="CONFIRMED",
         head="Iran strikes Bahrain as tankers hit in Hormuz",
         body=("Bahrain says an Iranian attack set a civilian industrial site "
               "ablaze; no one hurt. The IRGC says it hit US positions at "
               "al-Riffa and Awali."),
         src="AL JAZEERA \u00b7 REUTERS \u00b7 AFP", ill="gulf"),
    dict(region="MEXICO \u00b7 SINALOA", color=GREEN, status="CONFIRMED",
         head="Mexico seizes \u2018El Chapo Isidro\u2019; 11 die",
         body=("Troops seize Fausto Isidro Meza Flores in Guasave: 4 soldiers "
               "and 7 gunmen killed. FBI Top Ten fugitive; $5m reward."),
         src="AP \u00b7 GUARDIAN \u00b7 REUTERS", ill="mexico"),
    dict(region="ANTALYA \u00b7 CLIMATE", color=TEAL, status="CONFIRMED",
         head="COP31 climate talks run into overtime",
         body=("Still split on fossil fuels and finance; closing session set "
               "for Sunday. The draft never names fossil fuels."),
         src="BBC \u00b7 AP \u00b7 FRANCE 24", ill="cop31"),
]

MEDIUM = [
    dict(n=4, region="EUROPE", color=BLUE, status="CONFIRMED",
         head="Russian missile hits Zelensky\u2019s hometown",
         body="2 killed, incl. a boy, 7; about 60 hurt.",
         src="AP \u00b7 BBC", ill="blast"),
    dict(n=5, region="AMERICAS", color=GREEN, status="CONFIRMED",
         head="AI sell-off drags US stocks into correction",
         body="S&P \u22123.7% Fri; Nasdaq erases 2026 gains.",
         src="BLOOMBERG \u00b7 REUTERS", ill="chart"),
    dict(n=6, region="EUROPE", color=BLUE, status="CONFIRMED",
         head="Drones set Russian cargo ship ablaze",
         body="Drifts into Finnish waters; crew safe.",
         src="BBC \u00b7 UPI", ill="ship"),
    dict(n=7, region="AMERICAS", color=GREEN, status="REPORTED",
         head="Trial: mosquitoes cut dengue 69%",
         body="5,757 children in Belo Horizonte trial.",
         src="AP \u00b7 STRAITS TIMES", ill="mosquito"),
    dict(n=8, region="ASIA", color=PURPLE, status="OFFICIAL",
         head="Deep quakes shake Peru and Timor",
         body="Deep, no tsunami threat; felt in Darwin.",
         src="USGS \u00b7 GFZ", ill="quake"),
    dict(n=9, region="GLOBAL", color=GREY, status="OFFICIAL",
         head="BepiColombo enters Mercury orbit",
         body="8 years, 10bn km; 2nd mission to orbit it.",
         src="ESA \u00b7 JAXA", ill="mercury"),
    dict(n=10, region="EUROPE", color=BLUE, status="OFFICIAL",
         head="EU and Indonesia sign trade pact",
         body="98.5% of EU tariffs gone; 730m people.",
         src="DW \u00b7 EURONEWS", ill="trade"),
    dict(n=11, region="GLOBAL", color=GREY, status="CONFIRMED",
         head="UN \u2018killer robot\u2019 talks end, no treaty",
         body="~100 states back rules by 2028; US opposed.",
         src="CBC \u00b7 NPR", ill="robot"),
]

BRIEFS = [
    ("Gaza", "Israeli strike kills 3 in food vehicle", "REUTERS"),
    ("Riyadh", "Coalition says it downed 3 Houthi missiles", "AL JAZEERA"),
    ("Paris", "6th Saturday of cost-of-living marches; 144 held", "FRANCE 24"),
    ("Copenhagen", "Denmark expels Russian attach\u00e9 over alleged plot", "BBC"),
    ("Brussels", "UK and EU sign three post-Brexit deals", "GUARDIAN"),
    ("Washington", "Trump threatens tax on firms building data centres abroad", "BBC"),
    ("Washington", "FBI crime database reportedly hacked", "BBC"),
    ("Virginia", "First US measles death of 2026, a child", "GUARDIAN"),
    ("Bras\u00edlia", "Bolsonaro in intensive care, bowel obstruction", "AL JAZEERA"),
    ("Bayelsa", "Funeral boat capsizes in Nigeria; 24 dead", "SKY NEWS"),
    ("Basra", "Fire at power station kills 4, injures 35", "REUTERS"),
    ("Dar es Salaam", "Tanzania convicts opposition leader Lissu", "BBC"),
    ("Kampala", "Uganda restricts gatherings over Ebola", "GUARDIAN"),
    ("Port-au-Prince", "Salvadoran troops fight gangs; 3 soldiers die", "GUARDIAN"),
    ("Tokyo", "Saudi Arabia, Japan agree oil stockpile deal", "JAPAN TODAY"),
    ("Buenos Aires", "Argentina bonds fall into distress", "BUENOS AIRES TIMES"),
    ("New York", "GTA VI earns $3.8bn on its first day", "BBC"),
    ("London", "England beat All Blacks 37\u201312 at Twickenham", "BBC"),
    ("Osaka", "BTS take five MAMA awards", "YONHAP"),
    ("Cardiff", "Australia beat Wales 29\u201326", "BBC"),
]

ILL = {"gulf": ill_gulf, "mexico": ill_mexico, "cop31": ill_cop31,
       "blast": ill_blast, "chart": ill_chart, "ship": ill_ship,
       "mosquito": ill_mosquito, "quake": ill_quake, "mercury": ill_mercury,
       "trade": ill_trade, "robot": ill_robot}


def draw():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0, x1 = 8, 1016
    # ---- top bar
    d.text((x0, 8), "THE WORLD IN ONE DAY", font=F(SANS_B, 11), fill=INK)
    d.text((x0 + 400, 8), "DAY 325 OF 2026", font=F(SANS_B, 11), fill=RED)
    d.text((x1 - 258, 8), "ALL TIMES UTC \u00b7 RANKED BY CONSEQUENCE",
           font=F(SANS_B, 11), fill=INK)
    rule(d, x0, 28, x1 - x0, width=2)
    # ---- masthead
    font = fit(SERIF_B, "Saturday 21 November 2026", 864, 66)
    d.text((x0, 32), "Saturday 21 November 2026", font=font, fill=INK)
    d.rectangle([888, 36, 1016, 94], fill=RED)
    d.text((906, 40), "SAT", font=F(SANS_B, 15), fill=(255, 255, 255))
    d.text((906, 58), "21 NOV", font=F(SANS_B, 15), fill=(255, 255, 255))
    rule(d, x0, 98, x1 - x0, width=1)
    # ---- subline (measured, centred, no overlap)
    p1 = "31 STORIES \u00b7 7 REGIONS \u00b7 12 FIELDS \u2014 EVERY ONE DATED "
    p2 = "SATURDAY 21 NOVEMBER 2026"
    fsub = F(SANS_B, 12)
    tw = d.textlength(p1, font=fsub) + d.textlength(p2, font=fsub)
    sx = (W - tw) // 2
    d.text((sx, 102), p1, font=fsub, fill=INK)
    d.text((sx + d.textlength(p1, font=fsub), 102), p2, font=fsub, fill=RED)
    rule(d, x0, 120, x1 - x0, width=1)
    # ---- ticker
    d.text((x0, 124), "Iran strikes Bahrain as tankers hit in Hormuz  \u25c6  Drones set "
           "Russian cargo ship ablaze  \u25c6  COP31 deadlocked over fossil fuels",
           font=F(SERIF_I, 14), fill=INK)
    rule(d, x0, 142, x1 - x0, width=1)
    # ---- timeline strip (auto-fit to the strip)
    d.rectangle([x0, 146, 128, 164], fill=INK)
    d.text((x0 + 6, 149), "THE DAY IN UTC", font=F(SANS_B, 10), fill=(255, 255, 255))
    tl = ("00:09 M6.7 Peru   |   06:50 Sparta II alarm   |   09:42 M6.8 Banda Sea   |   "
          "MIDDAY EU\u2013Indonesia pact   |   18:24 BepiColombo orbit   |   "
          "NIGHT Iran strikes Bahrain \u00b7 COP31 talks go on")
    ftl = fit(SANS, tl, x1 - 134, 10)
    d.text((134, 150), tl, font=ftl, fill=INK)
    rule(d, x0, 168, x1 - x0, width=1)
    # ---- numbers strip
    nums = [("2", "US Patriot radars Iran claims it hit"),
            ("11", "dead in the Sinaloa raid"),
            ("\u22125.3%", "Nasdaq on Friday"),
            ("$1.7tn", "China AI shares lost since June"),
            ("68.6%", "fewer dengue infections in trial")]
    nx, nw = x0, 198
    for i, (big, lab) in enumerate(nums):
        bx = nx + i * (nw + 5)
        d.rectangle([bx, 172, bx + nw, 216], outline=INK, width=1)
        d.text((bx + 6, 175), big, font=F(SERIF_B, 18), fill=RED)
        para(d, bx + 6, 196, lab, F(SANS, 9), nw - 12, leading=10, max_lines=2)
    # ---- region tabs
    tabs = [("EUROPE", 7, BLUE), ("MIDDLE EAST", 4, RED), ("AMERICAS", 10, GREEN),
            ("AFRICA", 3, ORANGE), ("ASIA", 3, PURPLE), ("OCEANIA", 1, TEAL),
            ("GLOBAL", 3, GREY)]
    tx = x0
    d.text((tx, 221), "STORIES BY REGION", font=F(SANS_B, 10), fill=INK)
    tx += 132
    for name, count, col in tabs:
        label = "%s %d" % (name, count)
        w = tag(d, tx, 219, label, col)
        tx += w + 6
    rule(d, x0, 236, x1 - x0, width=2)
    # ---- lead row
    ly, lh, lw = 240, 196, 328
    for i, s in enumerate(LEADS):
        bx = x0 + i * (lw + 12)
        ILL[s["ill"]](d, bx, ly, lw, 92)
        y = ly + 96
        d.text((bx, y), s["region"], font=F(SANS_B, 10), fill=s["color"])
        tag(d, bx + lw - 78, y - 1, s["status"], s["color"])
        y += 14
        y = para(d, bx, y, s["head"], F(SERIF_B, 22), lw, leading=23, max_lines=2)
        y = para(d, bx, y + 2, s["body"], F(SANS, 11), lw, leading=12, max_lines=2)
        d.text((bx, ly + lh - 11), s["src"], font=F(SANS, 8), fill=GREY)
    rule(d, x0, 440, x1 - x0, width=2)
    # ---- medium grid
    gy, gh, gw = 448, 118, 246
    for i, s in enumerate(MEDIUM):
        col, row = i % 4, i // 4
        bx = x0 + col * (gw + 8)
        by = gy + row * (gh + 8)
        ILL[s["ill"]](d, bx, by, gw, 42)
        y = by + 46
        d.text((bx, y), "%d  %s" % (s["n"], s["region"]), font=F(SANS_B, 9),
               fill=s["color"])
        d.text((bx + gw - 52, y), s["status"], font=F(SANS_B, 8), fill=s["color"])
        y += 13
        y = para(d, bx, y, s["head"], F(SERIF_B, 13), gw, leading=13, max_lines=2)
        y = para(d, bx, y + 2, s["body"], F(SANS, 10), gw, leading=11, max_lines=1)
        d.text((bx, by + gh - 10), s["src"], font=F(SANS, 8), fill=GREY)
    rule(d, x0, 696, x1 - x0, width=2)
    # ---- bottom: map + briefs
    by = 704
    d.text((x0, by), "WHERE IT HAPPENED", font=F(SANS_B, 12), fill=INK)
    d.text((x0, by + 15), "pins 1\u201310 are the drawn stories",
           font=F(SANS, 9), fill=GREY)
    world_map(d, x0, by + 30, 330, 190)
    d.text((x0, by + 226), "1 Bahrain  2 Mexico  3 Antalya  4 Kryvyi Rih  5 New York",
           font=F(SANS, 9), fill=INK)
    d.text((x0, by + 237), "6 Gulf of Finland  7 Belo Horizonte  8 Banda Sea  9 Brussels  10 Geneva",
           font=F(SANS, 9), fill=INK)
    d.text((x0, by + 248), "HOW SURE: CONFIRMED 2+ outlets \u00b7 OFFICIAL on the record \u00b7 REPORTED one outlet",
           font=F(SANS, 8), fill=GREY)
    bx = 354
    d.text((bx, by), "ALSO ON SATURDAY 21 NOVEMBER 2026 \u2014 20 MORE STORIES",
           font=F(SANS_B, 12), fill=INK)
    d.text((bx, by + 15), "in order of consequence", font=F(SANS, 9), fill=GREY)
    colw = 326
    for i, (place, head, src) in enumerate(BRIEFS):
        c = i // 10
        r = i % 10
        x = bx + c * (colw + 10)
        y = by + 30 + r * 23
        d.text((x, y), "%d" % (12 + i), font=F(SANS_B, 11), fill=RED)
        para(d, x + 22, y, "%s: %s  (%s)" % (place, head, src),
             F(SANS, 10), colw - 22, leading=11, max_lines=2)
    rule(d, x0, 968, x1 - x0, width=2)
    # ---- footer: date check (wrapped, inside the box)
    d.rectangle([x0, 974, x1, 1002], outline=RED, width=1)
    d.text((x0 + 6, 978), "DATE CHECK", font=F(SANS_B, 10), fill=RED)
    para(d, x0 + 84, 978,
         "Left out \u2014 they belong to another day: Fri 20 Nov: Russian missiles land in Poland.  "
         "Thu 19 Nov: ICJ finds Myanmar committed genocide \u00b7 Trump, Xi and Putin meet in Shenzhen.  "
         "Not yet: COP31\u2019s closing session (Sun 22 Nov).",
         F(SANS, 10), x1 - x0 - 96, leading=12, max_lines=2)
    d.text((x0, 1008),
           "Every story here happened or was first reported on Saturday 21 November 2026 (UTC), as the named "
           "outlets reported it. All maps and drawings are original vector work.",
           font=F(SANS, 9), fill=GREY)
    return img


def main():
    img = draw()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    img.save(path, format="PNG", optimize=True)
    os.chmod(path, 0o644)


if __name__ == "__main__":
    main()
