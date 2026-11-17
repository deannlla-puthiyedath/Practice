"""Reel 5: Love and Truth. A goodbye kiss in a big city, a night flight, a cab through Fort Kochi, home.
python3 render.py sheet t1 t2 ... -> sheet.jpg      python3 render.py full -> frames.mp4 (silent)"""
import os, sys, math, subprocess
from functools import lru_cache
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE); sys.path.insert(0, HERE)
import kochi as K
from kochi import (lib, W, H, FPS, ease, ramp, lerp, shp, rect, paste, building, bougain, fishing_net, palm, birds,
                   sky, ground_tiles, plate_house, house_live, plate_courtyard, courtyard_live, elder, boy,
                   OUT, WHITE, CREAM, GRN, LGRN, SAFF, YEL, SEA, TILE, WOOD, SKYB, MAG, PURP, RED, LATERITE)
DUR = 55.0
NIGHT = (40, 42, 96)                       # the painting's indigo, never black
SLATE = (96, 100, 116); LIT = (238, 226, 176)
INK = (36, 34, 112)
lib.TILE_BG[:] = [(252, 251, 247), (244, 239, 230), (196, 198, 202), (252, 251, 247)]

def q(x, s): return round(x / s) * s

@lru_cache(maxsize=512)
def girl(view, flare, spin, coat=None): return K.girl(view, flare, spin, coat)
@lru_cache(maxsize=8)
def BOY(w): return boy(w)
MUM = elder("mum"); DAD = elder("dad"); DAD_L = elder("dad", True); DAD_UP = elder("dad", True, True)

def heart(d, x, y, r, col=RED):
    d.ellipse((x - r, y - r * 0.7, x, y + r * 0.3), fill=col); d.ellipse((x, y - r * 0.7, x + r, y + r * 0.3), fill=col)
    d.polygon([(x - r, y - r * 0.1), (x + r, y - r * 0.1), (x, y + r * 1.2)], fill=col)

# ---------------------------------------------------------------- plates
def plate_city():
    im = Image.new("RGB", (W, H), NIGHT); d = ImageDraw.Draw(im)
    g = np.random.default_rng(3)
    for _ in range(70):
        x, y = g.uniform(0, W), g.uniform(0, 700); d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(230, 228, 240))
    d.ellipse((790, 170, 900, 280), fill=(246, 244, 236), outline=OUT, width=3)          # moon
    x = -40
    for w, h in [(210, 900), (160, 1150), (240, 760), (180, 1300), (220, 980), (200, 860)]:
        top = 1340 - h
        rect(d, x, top, x + w, 1340, SLATE)
        if h > 1200: d.line((x + w / 2, top, x + w / 2, top - 120), fill=OUT, width=6)    # antenna
        for yy in range(top + 40, 1300, 70):
            for xx in range(int(x) + 22, int(x + w) - 30, 46):
                d.rectangle((xx, yy, xx + 24, yy + 38), fill=LIT if g.random() > 0.35 else (70, 74, 96))
        x += w - 10
    d.rectangle((0, 1340, W, H), fill=(120, 118, 128))
    for y in range(1380, H, 70): d.line((0, y, W, y), fill=(100, 98, 108), width=2)
    for lx in (120, 960):                                                                   # street lamps
        d.line((lx, 1340, lx, 980), fill=OUT, width=8); d.ellipse((lx - 26, 950, lx + 26, 1000), fill=LIT, outline=OUT, width=3)
    return im

def plate_airport():
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
    rect(d, 60, 260, 1020, 1060, (150, 176, 206))                                         # big window
    d.rectangle((60, 820, 1020, 1060), fill=(120, 118, 128))                               # tarmac
    for x in range(60, 1020, 240): d.line((x, 260, x, 1060), fill=OUT, width=5)
    # plane
    shp(d, [(260, 700), (900, 690), (960, 740), (900, 790), (280, 790), (220, 750)], WHITE)
    shp(d, [(520, 760), (680, 760), (560, 900), (480, 900)], (210, 210, 216))
    shp(d, [(250, 700), (300, 700), (250, 590), (210, 590)], SKYB)
    for x in range(340, 880, 40): d.ellipse((x, 720, x + 18, 738), fill=(70, 74, 96))
    d.rectangle((0, 1060, W, H), fill=(196, 198, 202))
    for y in range(1100, H, 80): d.line((0, y, W, y), fill=(176, 178, 184), width=2)
    rect(d, 0, 1060, W, 1080, (120, 118, 128))
    return im

def plate_cabin():
    im = Image.new("RGB", (W, H), (226, 222, 212)); d = ImageDraw.Draw(im)
    for y in range(0, H, 160): d.line((0, y, W, y), fill=(210, 206, 196), width=3)
    return im

WIN = (560, 640, 1000, 1300)                                                              # oval window box
def window_view(t, dawn):
    """What she sees: the night sky with drifting clouds, opening to morning over the Kerala coast."""
    x0, y0, x1, y1 = WIN; w, h = x1 - x0, y1 - y0
    v = Image.new("RGB", (w, h), NIGHT if dawn < 0.5 else (224, 232, 222)); d = ImageDraw.Draw(v)
    if dawn < 0.5:
        g = np.random.default_rng(9)
        for _ in range(30):
            x, y = g.uniform(0, w), g.uniform(0, h * 0.6); d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(230, 228, 240))
    else:
        d.rectangle((0, h * 0.55, w, h), fill=SEA)
        d.polygon([(0, h * 0.62), (w * 0.55, h * 0.58), (w, h * 0.7), (w, h), (0, h)], fill=GRN)
        for k in range(8):
            px = (k * 70 + 20) % w; d.line((px, h * 0.72, px, h * 0.66), fill=WOOD, width=3)
            d.ellipse((px - 18, h * 0.62, px + 18, h * 0.67), fill=LGRN)
    cl = (150, 150, 176) if dawn < 0.5 else (248, 246, 240)
    for k in range(4):
        cx = (k * 260 - t * 60) % (w + 400) - 200; cy = 140 + k * 140
        part = 0 if dawn < 0.5 else (dawn - 0.5) * 2 * 500 * (1 if k % 2 else -1)
        d.ellipse((cx - 160 + part, cy - 40, cx + 160 + part, cy + 40), fill=cl)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 200, fill=255)
    return v, m

def plate_route():
    """One long Fort Kochi strip for the cab: sea wall and Chinese fishing nets, Dutch houses, bougainvillea,
    the church spire, rain trees, then the lane home."""
    SW = 7600
    im = Image.new("RGB", (SW, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SW, 1260), fill=(224, 232, 222))
    for i in range(14): d.ellipse((i * 560 + 60, 220 + (i % 3) * 120, i * 560 + 320, 270 + (i % 3) * 120), fill=(244, 240, 228))
    # 0-2400: the sea and the nets
    d.rectangle((0, 820, 2600, 1180), fill=SEA)
    for x in (300, 1200, 2050): fishing_net(d, x, 1060, 0.5, 1.15)
    d.rectangle((0, 1180, 2600, 1260), fill=(200, 190, 160))
    for x in range(0, 2600, 60): d.line((x, 1180, x, 1260), fill=(160, 150, 120), width=2)
    # 2400-4600: Dutch-era houses in a row, bougainvillea
    cols = [(SAFF, "house"), (YEL, "shop"), (SKYB, "house"), (CREAM, "cafe"), (LGRN, "house"), (WHITE, "shop")]
    x = 2600
    for (c, kind) in cols:
        building(d, x, 360, 1260, 640, c, kind, shutter=GRN if c != LGRN else PURP); x += 360
    for bx in (2700, 3300, 3900, 4500): bougain(d, bx, 700, 120, bx)
    # 4800-5600: the church, white with a spire
    rect(d, 4900, 620, 5440, 1260, WHITE)
    shp(d, [(4860, 620), (5480, 620), (5170, 430)], TILE)
    rect(d, 5100, 260, 5240, 620, WHITE); shp(d, [(5080, 260), (5260, 260), (5170, 80)], TILE)
    d.line((5170, 80, 5170, 20), fill=OUT, width=6); d.line((5145, 45, 5195, 45), fill=OUT, width=6)
    d.pieslice((5110, 900, 5230, 1020), 180, 360, fill=WOOD, outline=OUT, width=3); rect(d, 5110, 960, 5230, 1260, WOOD)
    for wx in (4980, 5320): d.pieslice((wx - 40, 720, wx + 40, 800), 180, 360, fill=SKYB, outline=OUT, width=3); rect(d, wx - 40, 760, wx + 40, 900, SKYB)
    # 5600-7600: rain trees and the laterite lane home
    for tx in (5750, 6300, 6900, 7400):
        d.line((tx, 1260, tx, 700), fill=WOOD, width=34)
        d.ellipse((tx - 300, 380, tx + 300, 760), fill=GRN, outline=OUT, width=3)
        d.ellipse((tx - 200, 330, tx + 160, 600), fill=LGRN, outline=OUT, width=3)
    d.rectangle((0, 1260, SW, H), fill=(90, 84, 80))
    return im, SW

def car(t, head=None):
    """A plain cream hatchback cab, side view. Her head shows in the back window."""
    im = Image.new("RGBA", (900, 460), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    shp(d, [(40, 300), (60, 220), (230, 200), (330, 90), (640, 90), (760, 200), (860, 230), (870, 330), (40, 340)], (238, 230, 206))
    shp(d, [(250, 200), (345, 108), (470, 108), (470, 200)], (150, 176, 206))            # front window
    shp(d, [(490, 108), (630, 108), (730, 200), (490, 200)], (150, 176, 206))            # back window
    if head is not None:
        hm = Image.new("L", im.size, 0); ImageDraw.Draw(hm).polygon([(490, 108), (630, 108), (730, 200), (490, 200)], fill=255)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0)); layer.alpha_composite(head, (560 - head.width // 2, 96))
        im.paste(layer, (0, 0), Image.fromarray(np.minimum(np.asarray(hm), np.asarray(layer.split()[3]))))
    d = ImageDraw.Draw(im)
    d.line((480, 108, 480, 330), fill=OUT, width=3); d.line((60, 250, 860, 250), fill=(200, 190, 160), width=2)
    for wx in (210, 700):
        d.ellipse((wx - 70, 270, wx + 70, 410), fill=(30, 28, 28), outline=OUT, width=3)
        d.ellipse((wx - 34, 306, wx + 34, 374), fill=(200, 196, 186), outline=OUT, width=3)
        for s in range(3):
            a = t * 14 + s * math.pi / 3
            d.line((wx - 32 * math.cos(a), 340 - 32 * math.sin(a), wx + 32 * math.cos(a), 340 + 32 * math.sin(a)), fill=OUT, width=3)
    d.ellipse((830, 236, 866, 262), fill=YEL, outline=OUT, width=2)
    return im

CITY, AIR, CABIN = plate_city(), plate_airport(), plate_cabin()
ROUTE, RW = plate_route()
HOUSE, COURT = plate_house(), plate_courtyard()

# ---------------------------------------------------------------- text: the book, word for word
CARDS = [(0.4, 3.6, "It's about a boy who loved Love"), (3.7, 6.9, "so much he became the Truth."),
         (11.4, 14.2, "In a world filled with darkness,"), (14.3, 17.1, "no one believes in Love."),
         (17.2, 19.9, "She is invisible."),
         (22.6, 26.8, "Only Truth and those who love him"), (26.9, 31.6, "sees her for who she is."),
         (32.4, 35.8, "Love is the truth."),
         (36.6, 43.6, "Without Truth, the world can't see Love."),
         (44.3, 46.9, "When they love the other,"), (47.0, 49.9, "they love themselves more.")]
os.chdir(K.R2)
CARD_IMG = [lib.ransom(s, INK, size=74, seed=i * 5 + 3, max_w=720) for i, (_, _, s) in enumerate(CARDS)]
NAME = lib.ransom("Della Antony", INK, size=88, seed=21, max_w=900)
os.chdir(HERE)
LOGO = K.LOGO
CX, CY = (W - 230) / 2 + 40, 340

def pop(t, t0):
    u = (t - t0) / 0.22
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.8 + 0.28 * math.sin(u * math.pi * 0.7) if u < 0.7 else lerp(1.06, 1.0, (u - 0.7) / 0.3)

def cards(img, t):
    for (a, b, _), im in zip(CARDS, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
            paste(img, im, CX, CY + im.height / 2 - 90, scale=pop(t, a), alpha=al)
    return img

# ---------------------------------------------------------------- shots
def shot_city(t):                                     # 0 - 7: goodbye kiss
    img = CITY.copy().convert("RGBA")
    k = ramp(t, 1.4, 2.6) * (1 - ramp(t, 5.4, 6.4))   # lean in
    g = girl("front", 0.62, 0.0, "open")
    paste(img, BOY(0.0), lerp(700, 610, k), 1300, scale=0.66, rot=lerp(0, 9, k))
    paste(img, g, lerp(380, 468, k), 1330, scale=0.62, rot=lerp(0, -9, k))
    if k > 0.9:
        d = ImageDraw.Draw(img)
        for i in range(3):
            u = (t - 2.6 - i * 0.6)
            if u > 0: heart(d, 540 + 40 * math.sin(u * 3 + i), 760 - u * 120, 16 + 4 * i)
    return img

def shot_airport(t):                                  # 7 - 11: he waves, she looks back once
    u = t - 7.0
    img = AIR.copy().convert("RGBA")
    paste(img, BOY(q(0.5 + 0.5 * math.sin(u * 7), 0.25)), 860, 1420, scale=0.6)
    look = 1.6 < u < 2.7
    k = ramp(u, 0.2, 4.0)
    g = girl("front" if look else "back", 0.62, 0.0, "open")
    paste(img, g, lerp(560, 330, k), lerp(1460, 1240, k) + (0 if look else 6 * abs(math.sin(u * 7))), scale=lerp(0.6, 0.42, k))
    return img

def shot_plane(t):                                    # 11 - 22: wrapped in the coat, at the window; dawn opens
    u = t - 11.0
    dawn = ramp(u, 8.6, 9.6)
    push = ramp(u, 9.0, 11.0)
    img = CABIN.copy().convert("RGBA")
    v, m = window_view(t, dawn)
    x0, y0, x1, y1 = WIN
    frame = Image.new("RGBA", (x1 - x0 + 60, y1 - y0 + 60), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), 230, fill=(244, 240, 230), outline=OUT, width=4)
    img.alpha_composite(frame, (x0 - 30, y0 - 30))
    img.paste(v, (x0, y0), m)
    ImageDraw.Draw(img).rounded_rectangle(WIN, 200, outline=OUT, width=4)
    g = girl("front", 0.62, 0.0, "wrap")
    top = g.crop((0, 0, g.width, int(g.height * 0.5)))
    sway = 2 * math.sin(u * 1.2)
    paste(img, top, 330, 1420, scale=1.7, rot=-6 + sway)              # leaning toward the window
    # seat back
    shp(ImageDraw.Draw(img), [(0, 1640), (600, 1600), (640, H), (0, H)], (70, 74, 110))
    if push > 0:                                      # into the window, the morning fills the frame
        s = lerp(1.0, 2.8, push)
        vw, vh = W / s, H / s
        cx, cy = min(780, W - vw / 2), 970
        img = img.crop((int(cx - vw / 2), int(cy - vh / 2), int(cx + vw / 2), int(cy + vh / 2))).resize((W, H), Image.LANCZOS)
    return img

def shot_ride(t):                                     # 22 - 32: the scenic route through Fort Kochi
    u = t - 22.0
    off = int(lerp(0, RW - W, ease(u / 10.0) * 0.15 + u / 10.0 * 0.85))
    img = ROUTE.crop((off, 0, off + W, H)); d = ImageDraw.Draw(img)
    for x in range(-((int(u * 900)) % 200), W, 200): d.rectangle((x, 1590, x + 110, 1606), fill=WHITE)
    birds(d, t, 5, 3, 200)
    for k in range(3):
        px = (k * 520 - u * 900) % 1600 - 200; palm(d, px, 1300, 380, math.sin(t * 2 + k))
    img = img.convert("RGBA")
    g = girl("front", 0.62, 0.0, "open")
    head = g.crop((0, 0, g.width, int(g.height * 0.24))).resize((int(g.width * 0.42), int(g.height * 0.24 * 0.42)), Image.LANCZOS)
    paste(img, car(u, head), 540, 1420 + 4 * math.sin(u * 11))
    return img

def shot_house(t):                                    # 32 - 36: out of the cab, coat over her arm
    u = t - 32.0
    img = house_live(HOUSE.copy(), t, ramp(u, 2.0, 3.0)).convert("RGBA")
    birds(ImageDraw.Draw(img), t, 4, 5, 120)
    paste(img, car(0), 150, 1560, scale=0.6)
    k = ramp(u, 0.4, 3.8)
    view = "front" if u < 1.2 else "back"
    g = girl(view, 1.0, 0.0, "arm" if view == "front" else None)
    paste(img, g, lerp(380, 540, k), lerp(1500, 1190, k) + 8 * abs(math.sin(u * 8)), scale=lerp(0.66, 0.38, k))
    return img

def _dad_back():
    """Dad seen from behind: the approved figure with the back of his head (hair) and no buttons."""
    im = DAD_UP.copy(); d = ImageDraw.Draw(im)
    d.ellipse((57, 8, 231, 206), fill=(34, 24, 22), outline=OUT, width=3)
    d.rectangle((138, 262, 172, 640), fill=(176, 206, 226))
    return im
DAD_BACK = _dad_back()

@lru_cache(maxsize=64)
def lifted(step):
    """Dad holding her up by the waist; step 0..23 is one full 360 turn.
    Near side: her back to us, Dad's laughing face beside her. Far side: her face, Dad's back."""
    ang = step / 24 * 2 * math.pi
    near = math.cos(ang) >= 0
    g = girl("back" if near else "front", 1.4, (step / 24) % 1)
    grp = Image.new("RGBA", (1100, 2100), (0, 0, 0, 0))
    dx0, dy0 = 600, 760                                            # Dad's cut-out (292 x 1249) in the group
    P_ = lambda x, y: (dx0 + x, dy0 + y)
    gs = g.resize((int(g.width * 0.86), int(g.height * 0.86)), Image.LANCZOS).rotate(6 if near else -6, expand=True, resample=Image.BICUBIC)
    wx, wy = P_(-20, 0)                                            # her waist, up beside his head
    if near:                                                       # Dad behind, she is nearer to us
        grp.alpha_composite(DAD_UP, (dx0, dy0))
        grp.alpha_composite(gs, (int(wx - gs.width / 2), int(wy - gs.height * 0.31)))
    else:
        grp.alpha_composite(gs, (int(wx - gs.width / 2), int(wy - gs.height * 0.31)))
        grp.alpha_composite(DAD_BACK, (dx0, dy0))
    d = ImageDraw.Draw(grp); SK = (228, 188, 156)
    for pts in ([P_(62, 250), P_(-60, 200), P_(-95, 40)], [P_(230, 250), P_(100, 250), P_(55, 50)]):
        if near: pts = [pts[-1]]                                  # her body hides his arms; only his hands show at her waist
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d.line((x0, y0, x1, y1), fill=OUT, width=50)
        for x, y in pts[1:-1]: d.ellipse((x - 25, y - 25, x + 25, y + 25), fill=OUT)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d.line((x0, y0, x1, y1), fill=SK, width=42)
        for x, y in pts[1:-1]: d.ellipse((x - 21, y - 21, x + 21, y + 21), fill=SK)
        hx, hy = pts[-1]
        d.ellipse((hx - 25, hy - 29, hx + 25, hy + 29), fill=SK, outline=OUT, width=4)
    sx = max(0.25, abs(math.cos(ang)))
    out = grp.resize((max(1, int(grp.width * sx)), grp.height), Image.LANCZOS)
    if not near: out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out

def shot_court(t):                                    # 36 - 44: she runs to Dad; he picks her up and twirls her
    u = t - 36.0
    img = courtyard_live(COURT.copy(), t).convert("RGBA")
    paste(img, MUM, 930, 1300, scale=0.62)
    if u < 1.5 or u > 7.2:                            # run in / set down
        k = ramp(u, 0.0, 1.4)
        paste(img, DAD_L if u > 7.2 else DAD, 600, 1290, scale=0.66)
        g = girl("front", 1.0, 0.0)
        paste(img, g, lerp(80, 400, k) if u < 1.5 else 400, 1300, scale=0.6)
        return img
    lift = ramp(u, 1.5, 2.2) * (1 - ramp(u, 6.6, 7.2))
    step = int(round(ramp(u, 2.6, 5.8) * 24)) % 24                # one full 360
    grp = lifted(step)
    paste(img, grp, 560, 1230 - 60 * lift + 6 * math.sin(u * 6), scale=0.66)
    return img

def shot_hug(t):                                      # 44 - 50: Mum hugs her tight. Just the two of them.
    u = t - 44.0
    img = courtyard_live(COURT.copy(), t).convert("RGBA")
    k = ramp(u, 0.0, 1.2)
    sq = 1 + 0.025 * max(0.0, math.sin(u * 3.2)) * k  # squeezing
    g = girl("front", 1.0, 0.0)
    paste(img, MUM, lerp(800, 600, k), 1300, scale=0.62 * sq, rot=lerp(0, 8, k))
    paste(img, g, lerp(320, 470, k), 1310, scale=0.6 * sq, rot=lerp(0, -8, k))
    if k > 0.95:
        d = ImageDraw.Draw(img)
        for i in range(2):
            v = u - 1.6 - i * 1.4
            if v > 0: heart(d, 535 + 30 * math.sin(v * 2 + i), 760 - v * 90, 18)
    return img

def shot_end(t):
    img = Image.fromarray((np.clip(lib.paper_bg(), 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    p = pop(t, 50.4)
    if p: paste(img, LOGO, W / 2, 800, scale=p * 1.25)
    p = pop(t, 50.9)
    if p: paste(img, NAME, W / 2, 1070, scale=p)
    return img

SHOTS = [(0.0, shot_city), (7.0, shot_airport), (11.0, shot_plane), (22.0, shot_ride), (32.0, shot_house),
         (36.0, shot_court), (44.0, shot_hug), (50.0, shot_end)]

def frame(t):
    i = max(j for j, (a, _) in enumerate(SHOTS) if t >= a)
    img = SHOTS[i][1](t)
    a = SHOTS[i][0]
    if i > 0 and t - a < 0.3:
        prev = SHOTS[i - 1][1](a - 0.001)
        img = Image.blend(prev, img, (t - a) / 0.3)
    img = cards(img, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    arr = arr * K.WEAVE[..., None]
    return (np.clip(arr, 0, 1) * 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        ts = [float(x) for x in sys.argv[2:]]
        with Pool(4) as p: fr = p.map(frame, ts)
        ims = [Image.fromarray(f).resize((360, 640), Image.LANCZOS) for f in fr]
        for t_, f in zip(ts, fr): Image.fromarray(f).save(f"check_{t_:05.1f}.jpg", quality=88)
        cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 370 + 10, rows * 650 + 10), (240, 236, 228))
        for k, im in enumerate(ims): sh.paste(im, (10 + k % cols * 370, 10 + k // cols * 650))
        sh.save("sheet.jpg", quality=88)
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "frames.mp4"], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, b in enumerate(pool.imap(job, range(n), chunksize=8)):
                p.stdin.write(b)
                if k % 150 == 0: print(k, "/", n, flush=True)
        p.stdin.close(); p.wait()
        print("frames.mp4 done")
