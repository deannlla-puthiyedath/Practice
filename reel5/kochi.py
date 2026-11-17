"""Reel 5 scene kit, taken from Reel 4 (claude/eloquent-ritchie-b1p06r).
Original: Reel 4 'Reverie: a day in the dress'. A cut-paper fashion sketch girl spends a day in Fort Kochi
in the Reverie print dress, rides home and finds her parents in a courtyard house; the print is revealed as the painting.
python3 render.py sheet t1 t2 ...  -> sheet.jpg      python3 render.py full -> frames.mp4 (silent)"""
import os, sys, math, subprocess
from functools import lru_cache
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.join(HERE, "..", "reel2")
os.chdir(R2); sys.path.insert(0, R2); sys.path.insert(0, HERE)
import lib
LOGO = lib.logo_sticker(230)
os.chdir(HERE)
import dress5 as dress
from dress5 import Canvas, _poly, _ell, _limb, _union, SKIN, HAIR, GOLD, OUT

W, H, FPS = 1080, 1920, 30
WEAVE = (lib.WEAVE ** 0.5).astype(np.float32)

# palette, all from Reverie
SAFF = (232, 110, 40); PURP = (84, 52, 150); GRN = (62, 128, 60); LGRN = (120, 170, 70)
RED = (178, 54, 46); YEL = (226, 214, 80); SKYB = (96, 160, 214); WHITE = (246, 242, 232)
CREAM = (238, 226, 196); TILE = (176, 74, 46); WOOD = (92, 52, 32); SEA = (70, 140, 190)
LATERITE = (170, 92, 62); MAG = (190, 60, 120); KRAFT = (196, 158, 108); BREAD = (214, 160, 84)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ramp(t, a, b): return ease((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k

def shp(d, pts, fill, w=3):
    d.polygon(pts, fill=fill, outline=OUT, width=w)

def rect(d, x0, y0, x1, y1, fill, w=3):
    d.rectangle((x0, y0, x1, y1), fill=fill, outline=OUT, width=w)

def paste(base, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
    return base

# ---------------------------------------------------------------- city pieces
def window(d, x, y, w, h, shutter=GRN, arch=True, open_k=1.0):
    rect(d, x, y, x + w, y + h, (40, 34, 40))
    if arch: d.pieslice((x, y - w / 2, x + w, y + w / 2), 180, 360, fill=CREAM, outline=OUT, width=3)
    sw = w / 2 * open_k
    rect(d, x - sw, y, x, y + h, shutter); rect(d, x + w, y, x + w + sw, y + h, shutter)
    for k in range(1, 5):
        yy = y + h * k / 5
        d.line((x - sw, yy, x, yy), fill=OUT, width=1); d.line((x + w, yy, x + w + sw, yy), fill=OUT, width=1)
    d.line((x + w / 2, y, x + w / 2, y + h), fill=OUT, width=2)

def roof(d, x0, x1, y, h, over=24):
    shp(d, [(x0 - over, y), (x1 + over, y), (x1 - h * 0.4, y - h), (x0 + h * 0.4, y - h)], TILE)
    for k in range(1, 6):
        yy = y - h * k / 6; d.line((x0 - over + h * 0.4 * k / 6 + 8, yy, x1 + over - h * 0.4 * k / 6 - 8, yy), fill=(140, 52, 34), width=2)

def building(d, x, w, ground, h, wall, kind="house", shutter=GRN):
    top = ground - h
    rect(d, x, top, x + w, ground, wall)
    roof(d, x, x + w, top, 70)
    nw = max(1, int(w // 150))
    for i in range(nw):                                   # upper floor windows
        cx = x + (i + 0.5) * w / nw
        window(d, cx - 26, top + 80, 52, 100, shutter)
    d.line((x, top + 230, x + w, top + 230), fill=OUT, width=3)
    if kind == "cafe":                                    # striped awning, open front, tables
        aw = [(x + 10, ground - 300), (x + w - 10, ground - 300), (x + w + 20, ground - 220), (x - 20, ground - 220)]
        shp(d, aw, WHITE)
        for k in range(0, 10, 2):
            a = x - 20 + (w + 40) * k / 10; b = x - 20 + (w + 40) * (k + 1) / 10
            d.polygon([(lerp(x + 10, x + w - 10, k / 10), ground - 300), (lerp(x + 10, x + w - 10, (k + 1) / 10), ground - 300),
                       (b, ground - 220), (a, ground - 220)], fill=SAFF)
        d.polygon(aw, outline=OUT, width=3)
        rect(d, x + 30, ground - 210, x + w - 30, ground, (60, 40, 34))
        for i in range(3):
            rect(d, x + 50 + i * (w - 100) / 3, ground - 120, x + 40 + (i + 1) * (w - 100) / 3, ground - 112, WOOD, 2)
    elif kind == "shop":
        d.arc((x + w / 2 - 70, ground - 280, x + w / 2 + 70, ground - 140), 180, 360, fill=OUT, width=3)
        rect(d, x + w / 2 - 70, ground - 210, x + w / 2 + 70, ground, (64, 40, 30))
        window(d, x + 30, ground - 190, 50, 120, shutter, arch=False)
    else:
        d.pieslice((x + w / 2 - 55, ground - 260, x + w / 2 + 55, ground - 150), 180, 360, fill=WOOD, outline=OUT, width=3)
        rect(d, x + w / 2 - 55, ground - 205, x + w / 2 + 55, ground, WOOD)
        d.line((x + w / 2, ground - 205, x + w / 2, ground), fill=OUT, width=2)

def bougain(d, x, y, r, seed):
    g = np.random.default_rng(seed)
    for _ in range(40):
        a = g.uniform(0, 6.28); rr = g.uniform(0, r)
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr * 0.6
        d.ellipse((px - 9, py - 9, px + 9, py + 9), fill=MAG if g.random() > 0.35 else GRN)

def fishing_net(d, base_x, base_y, k, s=1.0, flip=False):
    """Chinese fishing net: a cantilever frame that dips with k (0..1)."""
    sg = -1 if flip else 1
    ang = math.radians(-35 + 20 * k)
    tip = (base_x + sg * 330 * s * math.cos(ang), base_y + 330 * s * math.sin(ang))
    d.line((base_x, base_y, tip[0], tip[1]), fill=WOOD, width=int(7 * s))
    d.line((base_x, base_y, base_x - sg * 120 * s, base_y - 150 * s), fill=WOOD, width=int(6 * s))
    for f in (-1, 1):
        ex = (tip[0] + f * 90 * s, tip[1] + 140 * s)
        d.line((tip[0], tip[1], ex[0], ex[1]), fill=WOOD, width=int(4 * s))
    net = [(tip[0] - 90 * s, tip[1] + 140 * s), (tip[0] + 90 * s, tip[1] + 140 * s), (tip[0], tip[1] + 190 * s)]
    d.polygon(net, outline=OUT, width=2)
    for j in range(1, 6):
        d.line((lerp(net[0][0], net[2][0], j / 6), lerp(net[0][1], net[2][1], j / 6),
                lerp(net[1][0], net[2][0], j / 6), lerp(net[1][1], net[2][1], j / 6)), fill=OUT, width=1)
    for j in range(5): d.ellipse((base_x - sg * 120 * s - 12 + j * 3, base_y - 150 * s + j * 18, base_x - sg * 120 * s + 12 + j * 3, base_y - 150 * s + j * 18 + 18), fill=(150, 150, 140), outline=OUT)

def palm(d, x, ground, h, sway):
    top = (x + 30 + sway * 18, ground - h)
    d.line((x, ground, top[0], top[1]), fill=WOOD, width=16)
    for a in range(0, 360, 45):
        ang = math.radians(a + sway * 10)
        ex = top[0] + 150 * math.cos(ang); ey = top[1] + 70 * math.sin(ang) + 40
        d.polygon([top, (ex, ey), ((top[0] + ex) / 2 + 10, (top[1] + ey) / 2 + 22)], fill=GRN, outline=OUT)

def birds(d, t, n=5, seed=1, y0=260):
    g = np.random.default_rng(seed)
    for i in range(n):
        x = (g.uniform(-200, 1100) + t * g.uniform(60, 120)) % 1400 - 160
        y = y0 + g.uniform(0, 260) + 14 * math.sin(t * 2 + i)
        f = 10 * math.sin(t * 9 + i * 2)
        d.line((x - 18, y + f, x, y, x + 18, y + f), fill=OUT, width=3)

def sky(d, top=0, bottom=900):
    d.rectangle((0, top, W, bottom), fill=(224, 232, 222))
    for i, y in enumerate(range(top + 120, bottom, 160)):
        d.ellipse((60 + i * 210 % 900, y, 300 + i * 210 % 900, y + 50), fill=(244, 240, 228))

def ground_tiles(d, y0, col=LATERITE):
    d.rectangle((0, y0, W, H), fill=col)
    for y in range(y0 + 30, H, 60):
        off = (y // 60 % 2) * 45
        for x in range(-90 + off, W, 90): d.rectangle((x, y, x + 86, y + 56), outline=(140, 72, 48), width=2)

# ---------------------------------------------------------------- people and props
@lru_cache(maxsize=256)
def girl(view, flare, spin, coat=None):
    return dress.figure(view, flare, spin, coat)

def bag(bread=True):
    im = Image.new("RGBA", (200, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if bread:
        d.rounded_rectangle((70, 4, 112, 200), 20, fill=BREAD, outline=OUT, width=3)
        for y in (40, 80, 120): d.line((80, y, 102, y - 14), fill=(150, 100, 50), width=3)
    shp(d, [(20, 140), (180, 140), (170, 326), (30, 326)], KRAFT)
    d.arc((60, 100, 140, 180), 180, 360, fill=OUT, width=4)
    return im

def elder(kind, laugh=False):
    """Parents, about 50, drawn exactly like the girl (same body, face and outline).
    Mum: a mustard cotton kurti, off-white leggings, green dupatta, gold bangles.
    Dad: a half-sleeve shirt and a checked kaili lungi, a watch."""
    c = Canvas()
    mum = kind == "mum"
    sk = SKIN if mum else (228, 188, 156)                                                     # Dad: fair skin
    if mum:   # long straight hair falls behind her back, past the waist
        c.fill(_poly([(338, 150), (352, 108), (400, 96), (448, 108), (462, 150), (484, 600), (452, 640), (348, 640), (316, 600)]), HAIR)
    # legs and flat sandals, same construction as the girl
    for side, x_hip, x_ank in [(-1, 380, 374), (1, 420, 430)]:
        c.fill(_limb([(x_hip, 760), (x_hip + side * 6, 960), (x_ank, 1300)], 62 if mum else 80, 22 if mum else 32), sk)
        c.fill(_poly([(x_ank - 11, 1292), (x_ank + 11, 1292), (x_ank + 22, 1324), (x_ank - 10, 1324)]), sk, ow=2)
        c.line([(x_ank - 12, 1326), (x_ank + 24, 1326)], (110, 70, 40), 6)
    if mum:   # leggings over the legs
        c.fill(_union(_limb([(380, 760), (374, 960), (374, 1290)], 64, 26), _limb([(420, 760), (426, 960), (430, 1290)], 64, 26)), WHITE)
    # arms
    ax = 0 if mum else 34                                                                   # Dad is broader
    c.fill(_limb([(338 - ax / 2, 312), (322 - ax, 470), (304 - ax, 640)], 34 + ax * 0.8, 22 + ax * 0.6), sk); c.fill(_ell(302 - ax, 660, 16 + ax / 3, 24 + ax / 4), sk)
    c.fill(_limb([(462 + ax / 2, 312), (478 + ax, 470), (496 + ax, 640)], 34 + ax * 0.8, 22 + ax * 0.6), sk); c.fill(_ell(498 + ax, 660, 16 + ax / 3, 24 + ax / 4), sk)
    if mum:
        kurti = (196, 40, 44)                                                                 # simple red kurti
        c.fill(_union(_poly([(334, 296), (466, 296), (474, 380), (452, 480), (482, 640), (492, 960), (308, 960), (318, 640), (348, 480), (326, 380)]),
                      _limb([(338, 310), (324, 440)], 42, 34), _limb([(462, 310), (476, 440)], 42, 34)), kurti)
        c.line([(380, 300), (400, 340), (420, 300)], (120, 20, 24), 3)                        # V neck
        c.line([(320, 760), (310, 960)], OUT, 2); c.line([(480, 760), (490, 960)], OUT, 2)  # side slits
        for y in (612, 626): c.line([(292, y), (314, y)], GOLD, 5)                            # bangles
    else:
        lungi = Image.new("RGB", c.rgb.size, PURP); dl = ImageDraw.Draw(lungi)
        for x in range(0, c.rgb.size[0], 56): dl.rectangle((x, 0, x + 20, c.rgb.size[1]), fill=GRN)
        for y in range(0, c.rgb.size[1], 56): dl.rectangle((0, y, c.rgb.size[0], y + 14), fill=(232, 110, 40))
        c.fill(_poly([(290, 580), (510, 580), (514, 1260), (286, 1260)]), lungi)
        c.line([(400, 562), (412, 640)], OUT, 3)                                              # knot fold
        shirt = (176, 206, 226)
        c.fill(_union(_poly([(310, 290), (490, 290), (508, 400), (518, 640), (282, 640), (292, 400)]),
                      _ell(318, 316, 30, 30), _ell(482, 316, 30, 30),
                      _limb([(322, 310), (294, 430)], 70, 58), _limb([(478, 310), (506, 430)], 70, 58)), shirt)   # soft, broad, evenly chubby
        c.line([(400, 300), (400, 626)], (120, 140, 160), 2)
        for y in range(340, 600, 50): c.fill(_ell(408, y, 4, 4), WHITE, outline=False)
        c.line([(516, 612), (540, 612)], (60, 50, 40), 7)                                     # watch
    c.fill(_poly([(384, 225), (416, 225), (420, 300), (380, 300)]), sk, outline=False)
    if mum:   # straight hair down to the shoulders, one soft grey strand
        c.fill(_ell(400, 170, 52, 66), sk)
        c.fill(_poly([(346, 166), (354, 116), (400, 102), (446, 116), (454, 166), (430, 122), (400, 116)]), HAIR)
        c.line([(440, 124), (452, 200)], (150, 146, 140), 3)
        c.fill(_ell(400, 140, 4, 4), RED, outline=False)
        for sd in (-1, 1):    # long strands over the front of each shoulder, down to the waist
            x0 = 400 + sd * 50
            c.fill(_poly([(x0, 130), (x0 + sd * 14, 200), (x0 + sd * 30, 300), (x0 + sd * 36, 520), (x0 + sd * 10, 540), (x0 + sd * 2, 300), (x0 - sd * 6, 210)]), HAIR)
        for ex in (348, 452): c.fill(_ell(ex, 206, 5, 5), GOLD, outline=False)
    else:     # rounder, cuter face with soft cheeks
        c.fill(_poly([(352, 220), (448, 220), (456, 300), (344, 300)]), sk, outline=False)   # thick neck
        c.fill(_ell(400, 180, 80, 78), sk)
        c.line([(370, 238), (400, 246), (430, 238)], dress.SKIN_SH, 3)                       # soft double chin
        for ex in (352, 448): c.fill(_ell(ex, 202, 16, 10), (204, 112, 92), outline=False)
        c.fill(_poly([(334, 158), (344, 112), (400, 98), (456, 112), (466, 158), (436, 124), (364, 124)]), HAIR)
        for ex in (338, 462): c.line([(ex, 128), (ex, 154)], (150, 146, 140), 6)             # greying temples
        c.line([(378, 200), (400, 195), (422, 200)], HAIR, 7)                                 # moustache
    for ex in (380, 420):                                                                     # same eyes as the girl
        c.line([(ex - 12, 172), (ex, 178), (ex + 12, 172)], OUT, 2.4)
        c.line([(ex - 13, 156), (ex + 12, 154)], HAIR, 3)
    c.line([(400, 182), (396, 200), (402, 202)], dress.SKIN_SH, 2)
    if laugh: c.fill(_ell(400, 218, 13, 9), (90, 30, 30))
    else: c.line([(388, 216), (400, 221), (412, 216)], (120, 40, 40), 3)
    rgb = c.rgb.resize((800, 1500), Image.LANCZOS); a = c.alpha.resize((800, 1500), Image.LANCZOS)
    fig = rgb.convert("RGBA"); fig.putalpha(a)
    pad = Image.new("RGBA", (830, 1530), (0, 0, 0, 0))
    pad.paste(Image.new("RGBA", (800, 1500), (252, 250, 244, 255)), (15, 15), dress.dilate(a, 8))
    pad.alpha_composite(fig, (15, 15))
    return pad.crop(pad.getbbox())


def scooter(t, k_basket=True):
    im = Image.new("RGBA", (760, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for wx in (150, 590):
        d.ellipse((wx - 78, 360, wx + 78, 516), fill=(30, 28, 28), outline=OUT, width=3)
        d.ellipse((wx - 42, 396, wx + 42, 480), fill=(200, 196, 186), outline=OUT, width=3)
        for s in range(4):
            a = t * 9 + s * math.pi / 4
            d.line((wx - 40 * math.cos(a), 438 - 40 * math.sin(a), wx + 40 * math.cos(a), 438 + 40 * math.sin(a)), fill=OUT, width=3)
    shp(d, [(60, 400), (90, 300), (220, 250), (330, 260), (360, 400)], SAFF)          # rear cowl
    shp(d, [(330, 360), (520, 360), (540, 400), (330, 410)], (200, 92, 34))            # floorboard
    shp(d, [(500, 380), (520, 180), (580, 150), (600, 200), (570, 400)], SAFF)         # leg shield
    shp(d, [(540, 400), (650, 360), (680, 420), (520, 440)], SAFF)                     # front fender
    d.line((585, 160, 610, 60), fill=OUT, width=10)
    d.line((560, 60, 670, 52), fill=OUT, width=9)
    d.ellipse((610, 70, 660, 116), fill=YEL, outline=OUT, width=3)                     # headlamp
    shp(d, [(110, 250), (330, 240), (340, 270), (120, 280)], (60, 40, 34))             # seat
    if k_basket:
        shp(d, [(640, 120), (740, 120), (730, 200), (650, 200)], KRAFT)
        for x in range(650, 740, 18): d.line((x, 122, x - 4, 198), fill=(140, 100, 60), width=2)
        d.rounded_rectangle((676, 30, 710, 140), 15, fill=BREAD, outline=OUT, width=3)
    return im

# ---------------------------------------------------------------- scenes (static plates)
def plate_street():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    sky(d, 0, 1200)
    d.rectangle((0, 900, W, 1100), fill=SEA)
    cols = [(SAFF, "house"), (CREAM, "cafe"), (LGRN, "shop"), (YEL, "house"), (SKYB, "cafe")]
    x = -60
    for i, (w, (col, kind)) in enumerate(zip([280, 300, 0, 0, 0], cols)):
        if i < 2:
            building(d, x, w, 1240, 560 + i * 40, col, kind); x += w
    building(d, 760, 380, 1240, 600, YEL, "shop", shutter=PURP)
    d.rectangle((0, 1240, W, H), fill=LATERITE); ground_tiles(d, 1240)
    bougain(d, 120, 700, 110, 3); bougain(d, 880, 650, 120, 4)
    return im

def plate_bakery():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    sky(d, 0, 500)
    rect(d, -10, 300, W + 10, 1320, CREAM)
    roof(d, 0, W, 300, 80)
    for cx in (240, 540, 840): window(d, cx - 40, 380, 80, 150, GRN)
    building(d, -10, 0, 0, 0, CREAM) if False else None
    # awning
    for k in range(12):
        x0 = -20 + k * 95; d.polygon([(x0, 640), (x0 + 95, 640), (x0 + 110, 760), (x0 - 10, 760)], fill=SAFF if k % 2 else WHITE)
    d.line((-20, 640, W + 20, 640), fill=OUT, width=4); d.line((-20, 760, W + 20, 760), fill=OUT, width=4)
    # shop window with breads
    rect(d, 120, 790, 960, 1180, (70, 46, 36))
    for sy in (900, 1010, 1120):
        d.line((140, sy, 940, sy), fill=WOOD, width=8)
        for bx in range(160, 920, 130):
            d.rounded_rectangle((bx, sy - 34, bx + 110, sy - 6), 14, fill=BREAD, outline=OUT, width=2)
    d.rectangle((0, 1320, W, H), fill=LATERITE); ground_tiles(d, 1320)
    # outdoor cafe table
    d.ellipse((760, 1420, 1000, 1470), fill=WHITE, outline=OUT, width=3)
    d.line((880, 1450, 880, 1620), fill=OUT, width=6)
    for cx in (820, 930): rect(d, cx - 18, 1400, cx + 18, 1440, WHITE, 2)
    bougain(d, 60, 620, 120, 7)
    return im

STRIP_W = 3600
def plate_seafront():
    im = Image.new("RGB", (STRIP_W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, STRIP_W, 1000), fill=(224, 232, 222))
    d.rectangle((0, 780, STRIP_W, 1180), fill=SEA)
    for x in range(0, STRIP_W, 1100): fishing_net(d, x + 300, 1050, 0.5, 1.2)
    d.rectangle((0, 1180, STRIP_W, 1260), fill=(200, 190, 160))                         # promenade wall
    for x in range(0, STRIP_W, 60): d.line((x, 1180, x, 1260), fill=(160, 150, 120), width=2)
    d.rectangle((0, 1260, STRIP_W, H), fill=(90, 84, 80))                                # road
    return im

def plate_house():
    """Heritage house that looks like a face from the street: tiled roof hair, two shuttered window eyes,
    a carved door mouth, a gable nose. Opens into a courtyard."""
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    sky(d, 0, 900)
    building(d, -200, 260, 1300, 520, SKYB, "shop")
    building(d, 960, 300, 1300, 520, SAFF, "house")
    rect(d, 90, 560, 990, 1300, WHITE)
    shp(d, [(40, 560), (1040, 560), (860, 330), (220, 330)], TILE)                      # roof hair
    for k in range(1, 7): d.line((40 + 30 * k, 560 - 38 * k, 1040 - 30 * k, 560 - 38 * k), fill=(140, 52, 34), width=3)
    shp(d, [(440, 330), (640, 330), (540, 210)], WOOD)                                    # gable
    d.ellipse((520, 260, 560, 300), fill=YEL, outline=OUT, width=3)
    shp(d, [(500, 560), (580, 560), (560, 760), (520, 760)], CREAM)                       # pillar nose
    d.rectangle((90, 1240, 990, 1300), fill=(200, 196, 186), outline=OUT, width=3)        # plinth
    for x in range(330, 760, 70): rect(d, x, 1300, x + 70, 1340 + (x - 330) // 70 * 0, (180, 176, 168), 2)
    d.rectangle((0, 1340, W, H), fill=LATERITE); ground_tiles(d, 1340)
    # potted plants either side
    for px in (200, 880):
        shp(d, [(px - 50, 1200), (px + 50, 1200), (px + 36, 1290), (px - 36, 1290)], TILE)
        bougain(d, px, 1150, 70, px)
    return im

def house_live(img, t, open_k):
    d = ImageDraw.Draw(img)
    blink = 0.08 if (t % 2.6) < 0.18 else 1.0                                           # window eyes blink
    for cx in (290, 790): window(d, cx - 60, 640, 120, 200, PURP, True, blink)
    # door mouth: carved, with brass studs; opens
    x0, x1, y0, y1 = 420, 660, 920, 1240
    rect(d, x0 - 16, y0 - 16, x1 + 16, y1, WOOD)
    if open_k > 0:
        d.rectangle((x0, y0, x1, y1), fill=(232, 216, 170))                                # sunlit courtyard beyond
        d.rectangle((x0 + 40, y0 + 80, x1 - 40, y1), fill=LGRN)
    lw = (x1 - x0) / 2 * (1 - open_k)
    for side in (0, 1):
        a = x0 if side == 0 else x1 - lw
        if lw > 2:
            rect(d, a, y0, a + lw, y1, (120, 70, 40))
            for yy in range(int(y0 + 30), y1, 60):
                for xx in np.linspace(a + 14, a + lw - 14, 3): d.ellipse((xx - 5, yy - 5, xx + 5, yy + 5), fill=GOLD)
    return img

def plate_courtyard():
    """Nalukettu courtyard: tiled roofs slope inward on four sides, open sky in the middle, wooden pillars,
    a small lotus pond and a tulsi stand. Traditional, but clean and new."""
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, H), fill=WHITE)
    d.rectangle((300, 0, 780, 300), fill=(200, 222, 236))                                 # open sky square
    shp(d, [(-20, 0), (300, 0), (300, 300), (-20, 460)], TILE)
    shp(d, [(780, 0), (1100, 0), (1100, 460), (780, 300)], TILE)
    shp(d, [(-20, 460), (300, 300), (780, 300), (1100, 460)], TILE)
    for k in range(1, 6):
        d.line((300 - 60 * k, 300 + 32 * k, 780 + 60 * k, 300 + 32 * k), fill=(140, 52, 34), width=3)
    d.rectangle((0, 460, W, 1250), fill=WHITE, outline=OUT)                               # back wall
    rect(d, 440, 640, 640, 1180, (60, 40, 34))                                            # kitchen door, bright view beyond
    d.rectangle((456, 656, 624, 1180), fill=(232, 216, 170))
    d.rectangle((456, 900, 624, 1180), fill=PURP); d.rectangle((456, 820, 624, 900), fill=GRN)
    for x in (110, 970):                                                                  # wooden pillars
        rect(d, x - 22, 440, x + 22, 1300, WOOD)
        rect(d, x - 40, 1270, x + 40, 1310, (200, 196, 186))
    d.rectangle((0, 1300, W, H), fill=(184, 98, 64))                                     # oxide red floor
    for y in range(1340, H, 80): d.line((0, y, W, y), fill=(160, 84, 54), width=2)
    rect(d, 330, 1420, 750, 1600, (90, 150, 180))                                         # lotus pond
    rect(d, 120, 1150, 210, 1300, CREAM)                                                  # tulsi stand
    d.ellipse((120, 1060, 210, 1160), fill=GRN, outline=OUT, width=3)
    for x in (690, 760): d.line((x, 560, x, 640), fill=OUT, width=2)                     # brass lamp
    d.polygon([(650, 640), (800, 640), (760, 690), (690, 690)], fill=GOLD, outline=OUT)
    return im

def courtyard_live(img, t):
    d = ImageDraw.Draw(img)
    for i in range(4):                                                                    # ripples, lotus
        r = (t * 30 + i * 30) % 120
        d.ellipse((540 - r, 1510 - r * 0.3, 540 + r, 1510 + r * 0.3), outline=(200, 230, 240), width=2)
    for lx, ly in [(420, 1480), (650, 1540)]:
        d.ellipse((lx - 34, ly - 14, lx + 34, ly + 14), fill=GRN, outline=OUT, width=2)
        d.polygon([(lx - 14, ly - 6), (lx, ly - 34), (lx + 14, ly - 6)], fill=MAG, outline=OUT)
    fl = 8 + 4 * math.sin(t * 13)                                                          # lamp flame
    d.ellipse((718, 600 - fl, 732, 620), fill=SAFF)
    for i in range(2):                                                                    # butterflies
        x = 380 + 200 * math.sin(t * 0.7 + i * 2); y = 200 + 60 * math.cos(t * 1.1 + i)
        f = 14 * abs(math.sin(t * 12 + i))
        d.polygon([(x, y), (x - f, y - 12), (x - f, y + 10)], fill=YEL, outline=OUT)
        d.polygon([(x, y), (x + f, y - 12), (x + f, y + 10)], fill=YEL, outline=OUT)
    return img


def boy(wave=0.0):
    """Her boyfriend, drawn like the others: slate shirt, indigo trousers, short hair. wave 0..1 raises his right arm."""
    c = Canvas()
    PANT = (40, 42, 96); SHIRT = (120, 124, 136)
    for side, x_hip, x_ank in [(-1, 380, 376), (1, 420, 428)]:
        c.fill(_poly([(x_ank - 12, 1292), (x_ank + 14, 1292), (x_ank + 26, 1328), (x_ank - 12, 1328)]), (40, 30, 26), ow=2)
    c.fill(_union(_limb([(378, 600), (374, 960), (376, 1296)], 74, 34), _limb([(422, 600), (426, 960), (428, 1296)], 74, 34)), PANT)
    c.fill(_limb([(332, 310), (316, 470), (300, 640)], 44, 34), SHIRT); c.fill(_ell(300, 660, 18, 24), SKIN)
    ang = math.radians(lerp(0, 150, wave))
    ex, ey = 470 + 150 * math.sin(ang * 0.6), 312 + 150 * math.cos(ang * 0.6)
    hx, hy = ex + 150 * math.sin(ang), ey + 150 * math.cos(ang)
    c.fill(_limb([(466, 310), (ex, ey), (hx, hy)], 44, 34), SHIRT); c.fill(_ell(hx, hy + 14 * math.cos(ang), 18, 22), SKIN)
    c.fill(_poly([(326, 296), (474, 296), (480, 450), (472, 612), (328, 612), (320, 450)]), SHIRT)
    c.line([(400, 300), (400, 608)], (90, 94, 106), 2)
    c.fill(_poly([(384, 225), (416, 225), (420, 300), (380, 300)]), SKIN, outline=False)
    c.fill(_poly([(374, 296), (400, 330), (426, 296)]), (236, 232, 222))                  # collar
    c.fill(_ell(400, 170, 54, 68), SKIN)
    c.fill(_poly([(344, 150), (350, 110), (400, 94), (450, 110), (456, 150), (436, 120), (364, 120)]), HAIR)
    for ex_ in (380, 420):
        c.line([(ex_ - 12, 172), (ex_, 178), (ex_ + 12, 172)], OUT, 2.4)
        c.line([(ex_ - 13, 156), (ex_ + 12, 154)], HAIR, 4)
    c.line([(400, 182), (396, 200), (402, 202)], dress.SKIN_SH, 2)
    c.line([(388, 216), (400, 221), (412, 216)], (120, 40, 40), 3)
    rgb = c.rgb.resize((800, 1500), Image.LANCZOS); a = c.alpha.resize((800, 1500), Image.LANCZOS)
    fig = rgb.convert("RGBA"); fig.putalpha(a)
    pad = Image.new("RGBA", (830, 1530), (0, 0, 0, 0))
    pad.paste(Image.new("RGBA", (800, 1500), (252, 250, 244, 255)), (15, 15), dress.dilate(a, 8))
    pad.alpha_composite(fig, (15, 15))
    return pad.crop(pad.getbbox())
