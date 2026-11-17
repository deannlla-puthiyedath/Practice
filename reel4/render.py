"""Reel 4 'Reverie: a day in the dress'. A cut-paper fashion sketch girl spends a day in Fort Kochi
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
import dress
from dress import Canvas, _poly, _ell, _limb, _union, SKIN, HAIR, GOLD, OUT

W, H, FPS, DUR = 1080, 1920, 30, 32.0
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
def girl(view, flare, spin):
    return dress.figure(view, flare, spin)

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
    # legs and flat sandals, same construction as the girl
    for side, x_hip, x_ank in [(-1, 380, 374), (1, 420, 430)]:
        c.fill(_limb([(x_hip, 760), (x_hip + side * 6, 960), (x_ank, 1300)], 62, 22), SKIN)
        c.fill(_poly([(x_ank - 11, 1292), (x_ank + 11, 1292), (x_ank + 22, 1324), (x_ank - 10, 1324)]), SKIN, ow=2)
        c.line([(x_ank - 12, 1326), (x_ank + 24, 1326)], (110, 70, 40), 6)
    if mum:   # leggings over the legs
        c.fill(_union(_limb([(380, 760), (374, 960), (374, 1290)], 64, 26), _limb([(420, 760), (426, 960), (430, 1290)], 64, 26)), WHITE)
    # arms
    ax = 0 if mum else 18                                                                   # Dad is broader
    c.fill(_limb([(338 - ax / 2, 312), (322 - ax, 470), (304 - ax, 640)], 34 + ax / 2, 22 + ax / 3), SKIN); c.fill(_ell(302 - ax, 660, 16 + ax / 4, 24), SKIN)
    c.fill(_limb([(462 + ax / 2, 312), (478 + ax, 470), (496 + ax, 640)], 34 + ax / 2, 22 + ax / 3), SKIN); c.fill(_ell(498 + ax, 660, 16 + ax / 4, 24), SKIN)
    if mum:
        kurti = (214, 170, 52)
        c.fill(_union(_poly([(338, 296), (462, 296), (470, 560), (500, 960), (300, 960), (330, 560)]),
                      _limb([(340, 310), (326, 420)], 42, 34), _limb([(460, 310), (474, 420)], 42, 34)), kurti)
        c.line([(400, 300), (400, 380)], (150, 110, 30), 3)                                   # placket
        c.line([(306, 950), (494, 950)], RED, 6)                                              # hem border
        c.line([(330, 700), (318, 960)], OUT, 2); c.line([(470, 700), (482, 960)], OUT, 2)  # side slits
        c.fill(_poly([(356, 296), (392, 296), (470, 640), (446, 660)]), GRN)                  # dupatta
        for y in (612, 626): c.line([(292, y), (314, y)], GOLD, 5)                            # bangles
    else:
        lungi = Image.new("RGB", c.rgb.size, PURP); dl = ImageDraw.Draw(lungi)
        for x in range(0, c.rgb.size[0], 56): dl.rectangle((x, 0, x + 20, c.rgb.size[1]), fill=GRN)
        for y in range(0, c.rgb.size[1], 56): dl.rectangle((0, y, c.rgb.size[0], y + 14), fill=(232, 110, 40))
        c.fill(_poly([(318, 560), (482, 560), (490, 1260), (310, 1260)]), lungi)
        c.line([(400, 562), (412, 640)], OUT, 3)                                              # knot fold
        shirt = (176, 206, 226)
        c.fill(_union(_poly([(330, 296), (470, 296), (490, 450), (494, 540), (484, 612), (316, 612), (306, 540), (310, 450)]),
                      _limb([(334, 308), (310, 420)], 52, 42), _limb([(466, 308), (490, 420)], 52, 42)), shirt)
        c.line([(400, 300), (400, 608)], (120, 140, 160), 2)
        for y in range(340, 600, 50): c.fill(_ell(408, y, 4, 4), WHITE, outline=False)
        c.line([(504, 612), (526, 612)], (60, 50, 40), 7)                                     # watch
    c.fill(_poly([(384, 225), (416, 225), (420, 300), (380, 300)]), SKIN, outline=False)
    c.fill(_ell(400, 170, 52, 66), SKIN)
    if mum:   # bun like the girl's, a little grey at the temple
        c.fill(_poly([(344, 160), (352, 118), (400, 96), (448, 118), (456, 160), (430, 128), (370, 128)]), HAIR)
        c.fill(_ell(400, 100, 34, 28), HAIR)
        c.line([(356, 150), (370, 122)], (150, 146, 140), 4)
        c.fill(_ell(400, 140, 4, 4), RED, outline=False)
        for ex in (348, 452): c.fill(_ell(ex, 206, 5, 5), GOLD, outline=False)
    else:
        c.fill(_poly([(346, 156), (352, 114), (400, 100), (448, 114), (454, 156), (432, 126), (368, 126)]), HAIR)
        for ex in (350, 450): c.line([(ex, 128), (ex, 154)], (150, 146, 140), 6)             # greying temples
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

MUM = elder("mum"); DAD = elder("dad"); DAD_L = elder("dad", True)
BAG = bag(); BAG2 = bag(False)

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

STREET, BAKERY, SEAFRONT, HOUSE, COURT = plate_street(), plate_bakery(), plate_seafront(), plate_house(), plate_courtyard()

# Painting for the reveal
PAINT = Image.open("reverie.jpg").convert("RGB")

# ---------------------------------------------------------------- text
# every line copied word for word from the book, in story order
CARDS = [(0.3, 3.2, "we soar high into our imaginations", PURP), (3.6, 7.9, "We have sailed so far", PURP),
         (8.4, 13.7, "we want to run home,", RED), (14.1, 17.2, "wherever it may be.", PURP),
         (18.0, 23.3, "and then they all go home together.", PURP)]
os.chdir(R2)
CARD_IMG = [lib.ransom(s, ink, size=74, seed=i * 5 + 3, max_w=720) for i, (_, _, s, ink) in enumerate(CARDS)]
END_TXT = lib.ransom("Wear art, not a logo.", PURP, size=74, seed=41, max_w=720)
NAME = lib.ransom("Della Antony", PURP, size=88, seed=21, max_w=900)
os.chdir(HERE)
CX, CY = (W - 230) / 2 + 40, 340

def pop(t, t0):
    u = (t - t0) / 0.22
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.8 + 0.28 * math.sin(u * math.pi * 0.7) if u < 0.7 else lerp(1.06, 1.0, (u - 0.7) / 0.3)

def cards(img, t):
    for (a, b, _, _), im in zip(CARDS, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
            paste(img, im, CX, CY + im.height / 2 - 90, scale=pop(t, a), alpha=al)
    return img

# ---------------------------------------------------------------- shots
def q(x, s): return round(x / s) * s

def shot_street(t):                                   # 0 - 3.4 twirl
    img = STREET.copy(); d = ImageDraw.Draw(img)
    fishing_net(d, 470, 1040, 0.5 + 0.5 * math.sin(t * 1.4), 0.9)
    birds(d, t, 6, 1, 160)
    for i in range(6):                                # sea glints
        x = (i * 190 + t * 40) % W; d.line((x, 960 + i % 3 * 40, x + 50, 960 + i % 3 * 40), fill=WHITE, width=3)
    img = img.convert("RGBA")
    spin = q(t * 0.9, 1 / 24); flare = q(1.0 + 0.6 * ramp(t, 0.2, 1.4), 0.05)
    g = girl("front", flare, spin % 1)
    paste(img, g, 540, 1240 + 6 * math.sin(t * 6), scale=0.78)
    return img

def shot_bakery(t):                                   # 3.4 - 8.2
    u = t - 3.4
    img = BAKERY.copy(); d = ImageDraw.Draw(img)
    for i in range(3):                                # coffee steam
        x = 820 + 110 * (i % 2); y = 1390 - ((u * 40 + i * 30) % 120)
        d.arc((x - 12, y - 30, x + 12, y), 270, 90, fill=(250, 250, 250), width=3)
    birds(d, t, 3, 2, 80)
    img = img.convert("RGBA")
    flare = q(1.0 + 0.08 * math.sin(u * 3), 0.05)
    g = girl("front", flare, q(0.1 * math.sin(u), 1 / 24) % 1)
    x = lerp(300, 380, ramp(u, 0, 1.0))
    paste(img, g, x, 1300, scale=0.78)
    if u > 2.4:                                        # the bag appears in her hand
        paste(img, BAG, x - 190, 1430 + 8 * math.sin(u * 4), scale=0.62 * pop(t, 3.4 + 2.4))
    return img

def shot_ride(t):                                     # 8.2 - 13.8
    u = t - 8.2
    off = int(u * 420) % (STRIP_W - W)
    img = SEAFRONT.crop((off, 0, off + W, H)); d = ImageDraw.Draw(img)
    for x in range(-((int(u * 900)) % 200), W, 200): d.rectangle((x, 1590, x + 110, 1606), fill=WHITE)
    birds(d, t, 5, 3, 200)
    for k in range(3):                                # palms closer to camera, faster
        px = (k * 520 - u * 640) % 1600 - 200; palm(d, px, 1260, 520, math.sin(t * 2 + k))
    img = img.convert("RGBA")
    bob = 6 * math.sin(u * 9)
    g = girl("front", q(1.25 + 0.15 * math.sin(u * 5), 0.05), q(u * 0.3, 1 / 24) % 1)
    gc = g.crop((0, 0, g.width, int(g.height * 0.58)))
    paste(img, gc, 400, 1150 + bob, scale=0.62)
    sc = scooter(u)
    paste(img, sc, 560, 1420 + bob, scale=1.0)
    return img

def shot_house(t):                                    # 13.8 - 17.4
    u = t - 13.8
    img = HOUSE.copy()
    img = house_live(img, t, ramp(u, 1.6, 2.6)); d = ImageDraw.Draw(img)
    birds(d, t, 4, 5, 120)
    img = img.convert("RGBA")
    paste(img, scooter(0), 150, 1560, scale=0.45)
    k = ramp(u, 0.3, 3.4)
    g = girl("back", q(1.0 + 0.1 * math.sin(u * 7), 0.05), q(u * 0.15, 1 / 24) % 1)
    paste(img, g, lerp(620, 540, k), lerp(1500, 1180, k) + 8 * abs(math.sin(u * 7)), scale=lerp(0.7, 0.36, k))
    return img

def shot_court(t):                                    # 17.4 - 23.6
    u = t - 17.4
    img = courtyard_live(COURT.copy(), t).convert("RGBA")
    handed = u > 2.0; kiss = ramp(u, 2.8, 3.6) * (1 - ramp(u, 5.0, 5.8))
    paste(img, DAD_L if (u > 3.4 and int(u * 6) % 2) else DAD, 880, 1262, scale=0.67)
    paste(img, MUM, 670, 1300, scale=0.62)
    gx = lerp(150, 420, ramp(u, 0.0, 1.6)) + 40 * kiss
    g = girl("front", q(1.05 + 0.05 * math.sin(u * 4), 0.05), 0.0)
    paste(img, g, gx, 1300, scale=0.62, rot=-9 * kiss)
    if not handed:
        paste(img, BAG, gx - 160, 1420, scale=0.5)
    else:
        paste(img, BAG, 560, 1440, scale=0.5); paste(img, BAG2, 960, 1450, scale=0.42)
    if kiss > 0.5:                                    # a tiny heart
        d = ImageDraw.Draw(img); hx, hy = 560, 720 - 60 * (kiss - 0.5)
        d.ellipse((hx - 18, hy - 12, hx, hy + 6), fill=RED); d.ellipse((hx, hy - 12, hx + 18, hy + 6), fill=RED)
        d.polygon([(hx - 18, hy - 2), (hx + 18, hy - 2), (hx, hy + 22)], fill=RED)
    return img

def shot_reveal(t):                                   # 23.6 - 28.4: push into the kitchen door, it becomes the painting
    u = t - 23.6
    k = ramp(u, 0.0, 1.8)
    s = lerp(1.0, 3.0, k)
    base = courtyard_live(COURT.copy(), t)
    cx, cy = 540, 910
    vw, vh = W / s, H / s
    img = base.crop((int(cx - vw / 2), int(cy - vh / 2), int(cx + vw / 2), int(cy + vh / 2))).resize((W, H), Image.LANCZOS)
    paper = Image.fromarray((np.clip(lib.paper_bg(), 0, 1) * 255).astype(np.uint8))
    pw = 1000; ph = int(PAINT.height * pw / PAINT.width)
    pad = Image.new("RGB", (pw + 24, ph + 24), (252, 250, 244)); pad.paste(PAINT.resize((pw, ph), Image.LANCZOS), (12, 12))
    zoom = lerp(1.0, 1.06, ramp(u, 1.8, 4.8))
    pz = pad.resize((int(pad.width * zoom), int(pad.height * zoom)), Image.LANCZOS)
    paper.paste(pz, (W // 2 - pz.width // 2, 1060 - pz.height // 2))
    m = ramp(u, 1.3, 2.1)
    return Image.blend(img, paper, m).convert("RGBA")

def shot_end(t):
    img = Image.fromarray((np.clip(lib.paper_bg(), 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    p = pop(t, 28.7)
    if p: paste(img, LOGO, W / 2, 760, scale=p * 1.2)
    p = pop(t, 29.2)
    if p: paste(img, NAME, W / 2, 1030, scale=p)
    p = pop(t, 29.8)
    if p: paste(img, END_TXT, W / 2, 1200, scale=p)
    return img

SHOTS = [(0.0, shot_street), (3.4, shot_bakery), (8.2, shot_ride), (13.8, shot_house),
         (17.4, shot_court), (23.6, shot_reveal), (28.4, shot_end)]

def frame(t):
    i = max(j for j, (a, _) in enumerate(SHOTS) if t >= a)
    img = SHOTS[i][1](t)
    a = SHOTS[i][0]
    if i > 0 and t - a < 0.25 and i != 5:              # soft crossfade from the previous shot
        prev = SHOTS[i - 1][1](a - 0.001)
        img = Image.blend(prev, img, (t - a) / 0.25)
    img = cards(img, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    arr = arr * WEAVE[..., None]                       # canvas grain over everything
    return (np.clip(arr, 0, 1) * 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        ts = [float(x) for x in sys.argv[2:]]
        ims = [Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS) for t in ts]
        cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 370 + 10, rows * 650 + 10), (240, 236, 228))
        for k, im in enumerate(ims): sh.paste(im, (10 + k % cols * 370, 10 + k // cols * 650))
        sh.save("sheet.jpg", quality=88)
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "frames.mp4"], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, b in enumerate(pool.imap(job, range(n), chunksize=8)):
                p.stdin.write(b)
                if k % 90 == 0: print(k, flush=True)
        p.stdin.close(); p.wait()
