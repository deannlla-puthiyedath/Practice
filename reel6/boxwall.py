"""Reel 6 box wall: the dress pattern opens into 35 boxes of the life she already has.
Builds 2 -> 3 -> 6 -> 9 -> 35 boxes (5x7), then pushes through the sun into the painting.
Sun boxes (yellow, orange) hold home and warmth; sea boxes (blue) hold water, time and freedom.

  python3 boxwall.py still 2.0        -> boxwall_still.jpg
  python3 boxwall.py video 6          -> boxwall.mp4 (silent, 30 fps)
  python3 boxwall.py zoom 3           -> boxwall_zoom.jpg (each box big, for checking)
"""
import math, os, subprocess, sys
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
COLS, ROWS, GAP = 5, 7, 12
CW, CH = (W - GAP * (COLS + 1)) // COLS, (H - GAP * (ROWS + 1)) // ROWS
SS = 2
BW = 720
BH = int(round(BW * CH / CW))
K = BW / 432
PAPER = (248, 246, 240)

# ------------------------------------------------------------------ palettes (all from the painting)
WARM = dict(cream=(252, 243, 218), lemon=(244, 226, 96), lime=(212, 222, 92), yel=(242, 196, 40),
            org=(234, 142, 52), deep=(206, 94, 32), rust=(160, 72, 32), out=(92, 48, 22), wash=(253, 247, 228))
BLUE = dict(white=(248, 250, 253), pale=(200, 224, 246), sky=(134, 186, 234), mid=(62, 132, 212),
            deep=(32, 84, 172), navy=(22, 50, 116), out=(20, 40, 92), wash=(244, 249, 255))
SKIN, HAIR, GOLDC = (176, 120, 88), (40, 26, 22), (214, 172, 60)
DADSHIRT, MUMKURTI = (170, 206, 236), (196, 64, 44)

# ------------------------------------------------------------------ painting crops
PAINT = Image.open(os.path.join(HERE, "sunset2.jpg")).convert("RGB")
XE = [0, 127, 272, 422, 577, 731, 874, 1017, 1162, 1305, 1390]
YE = [0, 97, 245, 400, 555, 700, 845, 995, 1083]

def crop_box(ci, ri):
    m = 12
    return PAINT.crop((XE[ci] + m, YE[ri] + m, XE[ci + 1] - m, YE[ri + 1] - m))

def bg_for(warm, k, still=False):
    r = np.random.default_rng(k)
    if warm: ci, ri = r.integers(0, 10), r.integers(0, 3)
    else: ci, ri = r.integers(0, 10), r.integers(3, 7)
    if ri == 0: ri = 1
    im = crop_box(ci, ri).resize((BW, BH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2 * K))
    a = np.asarray(im).astype(np.float32)
    wash = np.array((WARM if warm else BLUE)["wash"], np.float32)
    a = a * 0.85 + wash * 0.15
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")

# ------------------------------------------------------------------ drawing context (normalised coords 0..1)
class C:
    def __init__(self, img, pal):
        self.img, self.p = img, pal
        self.d = ImageDraw.Draw(img)
        self.o = pal["out"]
    def X(self, x): return x * BW
    def Y(self, y): return y * BH
    def pts(self, ps): return [(self.X(x), self.Y(y)) for x, y in ps]
    def P(self, ps, fill, w=4): self.d.polygon(self.pts(ps), fill=fill, outline=self.o if w else None, width=max(1, int(w * K)))
    def R(self, x0, y0, x1, y1, fill, w=4, r=0):
        b = (self.X(x0), self.Y(y0), self.X(x1), self.Y(y1))
        if r: self.d.rounded_rectangle(b, radius=r * SS * K, fill=fill, outline=self.o if w else None, width=max(1, int(w * K)))
        else: self.d.rectangle(b, fill=fill, outline=self.o if w else None, width=max(1, int(w * K)))
    def E(self, cx, cy, rx, ry, fill, w=4):
        self.d.ellipse((self.X(cx - rx), self.Y(cy - ry), self.X(cx + rx), self.Y(cy + ry)), fill=fill,
                       outline=self.o if w else None, width=max(1, int(w * K)))
    def O(self, cx, cy, r, fill, w=4):  # circle with radius in width units
        rr = r * BW
        self.d.ellipse((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), fill=fill,
                       outline=self.o if w else None, width=max(1, int(w * K)))
    def L(self, ps, col=None, w=4): self.d.line(self.pts(ps), fill=col or self.o, width=max(1, int(w * K)), joint="curve")
    def A(self, cx, cy, r, a0, a1, col=None, w=4):
        rr = r * BW
        self.d.arc((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), a0, a1, fill=col or self.o, width=max(1, int(w * K)))
    def S(self, name, cx, bottom, height, top_frac=1.0, flip=False, dy_crop=0.0):
        """Paste a cast sprite: `height` (box heights) is the shown part; top_frac keeps only the top of the figure."""
        im = SPRITE(name)
        if top_frac < 1: im = im.crop((0, 0, im.width, int(im.height * top_frac)))
        sc = height * BH / im.height
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        self.img.alpha_composite(im, (int(self.X(cx) - im.width / 2), int(self.Y(bottom) - im.height)))
    def PIE(self, cx, cy, r, a0, a1, fill, w=4):
        rr = r * BW
        self.d.pieslice((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), a0, a1, fill=fill,
                        outline=self.o if w else None, width=max(1, int(w * K)))

_SPR = {}
def SPRITE(name):
    if name not in _SPR: _SPR[name] = Image.open(os.path.join(HERE, "cast", name + ".png")).convert("RGBA")
    return _SPR[name]
DADSKIN = (228, 188, 156)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def fall(t, t0, y0, y1, dur=0.45):
    k = min(max((t - t0) / dur, 0), 1); return y0 + (y1 - y0) * k * k
def wob(t, f=1.0, a=1.0, ph=0.0): return a * math.sin(2 * math.pi * f * t + ph)

# ------------------------------------------------------------------ little people
def head(c, cx, cy, r, hair="bun", tilt=0.0, smile=True, hoops=False):
    if hair == "long":
        c.P([(cx - r * 1.15, cy - r * 0.3), (cx + r * 1.15, cy - r * 0.3), (cx + r * 1.25, cy + r * 3.2), (cx - r * 1.25, cy + r * 3.2)], HAIR)
    c.O(cx, cy, r, SKIN)
    if hair == "bun":
        c.O(cx, cy - r * 1.5 * BW / BH, r * 0.62, HAIR)
        c.PIE(cx, cy, r, 180, 360, HAIR)
    elif hair == "long":
        c.PIE(cx, cy, r, 180, 360, HAIR)
    elif hair == "short":
        c.PIE(cx, cy, r * 1.02, 190, 350, HAIR)
    elif hair == "dad":
        c.PIE(cx, cy, r * 1.02, 190, 350, HAIR)
        c.L([(cx - r * 0.45, cy + r * 0.32 * BW / BH), (cx + r * 0.45, cy + r * 0.32 * BW / BH)], HAIR, 7)
    ey = cy + r * 0.05 * BW / BH
    c.A(cx - r * 0.38, ey, r * 0.18, 20, 160, w=3); c.A(cx + r * 0.38, ey, r * 0.18, 20, 160, w=3)
    if smile: c.A(cx, cy + r * 0.25 * BW / BH, r * 0.3, 20, 160, (150, 50, 40), 3)
    if hoops: c.A(cx - r * 1.0, cy + r * 0.55 * BW / BH, r * 0.22, 0, 360, GOLDC, 4); c.A(cx + r * 1.0, cy + r * 0.55 * BW / BH, r * 0.22, 0, 360, GOLDC, 4)

def body(c, cx, top, wid, ht, col):
    c.P([(cx - wid * 0.42, top), (cx + wid * 0.42, top), (cx + wid * 0.5, top + ht), (cx - wid * 0.5, top + ht)], col)

# ================================================================== WARM boxes
def v_mum_drive(c, t):
    p = c.p
    c.R(0, 0, 1, 1, (200, 228, 250), 0)
    for i in range(6):  # palms rushing past
        x = (1.2 - ((t * 0.55 + i * 0.27) % 1.6))
        c.L([(x, 0.62), (x + 0.02, 0.18)], (110, 70, 40), 7)
        for a in (-1, 1): c.P([(x + 0.02, 0.18), (x + 0.02 + a * 0.16, 0.22), (x + 0.02 + a * 0.08, 0.16)], GREEN)
    bob = wob(t, 2.2, 0.004)
    c.S("mum", 0.3, 0.98 + bob, 0.8, top_frac=0.36)
    c.S("girl_open", 0.72, 0.98 - bob, 0.78, top_frac=0.34)
    c.P([(0, 0), (1, 0), (1, 0.1), (0, 0.1)], p["org"]); c.P([(0, 0.66), (1, 0.66), (1, 1), (0, 1)], p["org"])
    c.R(0, 0.1, 0.05, 0.66, p["org"]); c.R(0.95, 0.1, 1, 0.66, p["org"])
    c.A(0.24, 0.82, 0.16, 200, 340, (60, 50, 50), 10)   # steering wheel

def v_dad_serve(c, t):
    p = c.p
    c.S("dad_laugh" if (t % 3) > 2.2 else "dad", 0.68, 0.98, 0.95, top_frac=0.42)
    c.R(0, 0.72, 1, 1, p["rust"])
    c.E(0.36, 0.8, 0.28, 0.06, (236, 238, 240))  # steel plate
    pile = min(t / 3.0, 1)
    c.E(0.36, 0.79 - 0.02 * pile, 0.05 + 0.13 * pile, 0.015 + 0.035 * pile, (252, 250, 244))
    if t > 3.2: c.E(0.52, 0.79, 0.06, 0.025, p["org"])
    lx, ly = 0.42, 0.58 + wob(t, 1.1, 0.02)
    c.L([(0.56, 0.62), (lx, ly)], DADSKIN, 14)
    c.L([(lx, ly), (lx - 0.06, ly + 0.05)], STEEL, 6); c.E(lx - 0.08, ly + 0.07, 0.05, 0.025, STEEL)
    if t < 3.0:
        for k in range(8):
            yy = ((t * 1.6 + k * 0.125) % 1) * 0.1 + ly + 0.09
            c.O(lx - 0.08 + 0.01 * math.sin(k * 3), yy, 0.008, (255, 255, 250), 0)
    for k in range(3):
        s_ = (t * 0.4 + k / 3) % 1
        c.L([(0.3 + k * 0.06 + wob(s_, 1, 0.02), 0.72 - s_ * 0.2), (0.3 + k * 0.06 + wob(s_, 1, 0.02, 2), 0.66 - s_ * 0.2)], p["cream"], 5)

def v_easel(c, t):
    p = c.p
    c.L([(0.3, 0.95), (0.5, 0.1)], p["rust"], 8); c.L([(0.7, 0.95), (0.5, 0.1)], p["rust"], 8)
    c.R(0.18, 0.18, 0.82, 0.68, p["wash"])
    k = ease(t / 4)
    for i in range(3):
        for j in range(3):
            if (i * 3 + j) / 9 < k * 1.2:
                c.R(0.22 + j * 0.2, 0.22 + i * 0.15, 0.38 + j * 0.2, 0.35 + i * 0.15, p["org"] if i == 0 else BLUE["sky"], 2)
    c.PIE(0.5, 0.3, 0.07, -90, -90 + 360 * k, p["yel"], 2)
    bx, by = 0.5 + 0.08 * math.cos(2 * math.pi * k - math.pi / 2), 0.3 + 0.06 * math.sin(2 * math.pi * k - math.pi / 2)
    c.L([(bx, by), (bx + 0.2, by + 0.25)], p["rust"], 7); c.O(bx, by, 0.015, p["yel"])
    c.E(0.8, 0.88, 0.14, 0.05, p["cream"])
    for i, col in enumerate((p["yel"], p["org"], BLUE["mid"])): c.O(0.72 + i * 0.07, 0.87, 0.02, col, 2)

def v_sadya(c, t):
    p = c.p
    leaf = [(0.02, 0.62), (0.2, 0.4), (0.6, 0.32), (0.98, 0.36), (0.98, 0.8), (0.6, 0.86), (0.2, 0.84)]
    c.P(leaf, (150, 186, 70))
    c.L([(0.02, 0.62), (0.98, 0.58)], (120, 150, 50), 5)
    for k in range(6): c.L([(0.15 + k * 0.14, 0.61), (0.22 + k * 0.14, 0.36)], (130, 166, 60), 2)
    items = [(0.45, 0.66, 0.11, 0.045, (252, 250, 244)), (0.25, 0.68, 0.05, 0.025, p["yel"]), (0.7, 0.55, 0.05, 0.025, p["org"]),
             (0.32, 0.56, 0.04, 0.02, (180, 200, 90)), (0.6, 0.72, 0.04, 0.02, p["deep"]), (0.8, 0.62, 0.07, 0.035, p["cream"])]
    for i, (x, y, rx, ry, col) in enumerate(items):
        t0 = 0.3 + i * 0.6
        if t < t0: continue
        yy = fall(t, t0, y - 0.5, y)
        c.E(x, yy, rx, ry, col, 3)
    if t > 4.0:  # banana and payasam last
        c.P([(0.12, 0.45), (0.24, 0.38), (0.27, 0.41), (0.15, 0.48)], p["lemon"], 3)

def v_fritters(c, t):
    p = c.p
    c.R(0, 0.78, 1, 1, p["rust"])
    c.E(0.38, 0.8, 0.3, 0.06, p["cream"])
    for i in range(4):
        t0 = 0.4 + i * 0.9
        if t < t0: continue
        x = 0.25 + i * 0.09
        c.E(x, fall(t, t0, 0.1, 0.74 - (i % 2) * 0.02), 0.09, 0.035, p["yel"], 3)
    c.R(0.72, 0.5, 0.88, 0.8, (226, 180, 130)); c.E(0.8, 0.5, 0.08, 0.015, (200, 150, 100))
    for k in range(3):
        s = (t * 0.5 + k / 3) % 1
        c.L([(0.77 + k * 0.03 + wob(s, 1.5, 0.015), 0.46 - s * 0.25), (0.77 + k * 0.03 + wob(s, 1.5, 0.015, 1.5), 0.4 - s * 0.25)], p["cream"], 4)

def v_chai(c, t):
    p = c.p
    h = 0.12 + 0.12 * (0.5 + 0.5 * math.sin(t * 1.6))
    c.R(0.12, 0.08 + h, 0.32, 0.3 + h, (230, 232, 236))  # upper tumbler
    c.R(0.6, 0.66, 0.84, 0.92, (230, 232, 236)); c.E(0.72, 0.66, 0.12, 0.025, (236, 214, 170))
    for k in range(14):
        s = k / 13
        x = 0.3 + (0.68 - 0.3) * s; y = 0.3 + h + (0.66 - 0.3 - h) * s ** 1.4
        c.O(x, y, 0.016, (210, 160, 100), 0)
    c.L([(0.22, 0.32 + h), (0.18, 0.5 + h)], SKIN, 12); c.L([(0.72, 0.92), (0.8, 0.98)], SKIN, 12)
    for k in range(3): c.O(0.66 + k * 0.05, 0.64 - wob(t + k, 1.3, 0.01), 0.018, p["cream"], 0)

def v_coconut_oil(c, t):
    p = c.p
    c.O(0.82, 0.13, 0.1, p["yel"])
    for k in range(8):
        a = t * 0.4 + k * math.pi / 4
        c.L([(0.82 + 0.13 * math.cos(a), 0.13 + 0.1 * math.sin(a)), (0.82 + 0.18 * math.cos(a), 0.13 + 0.14 * math.sin(a))], p["yel"], 4)
    c.P([(0.02, 0.5), (0.7, 0.42), (0.75, 0.6), (0.06, 0.68)], (214, 180, 120))
    for i in range(5):
        x = 0.1 + i * 0.13; y = 0.5 - i * 0.012
        c.PIE(x, y + 0.03, 0.055, 180, 360, p["rust"], 3); c.E(x, y + 0.03, 0.045, 0.012, p["cream"], 2)
    c.P([(0.68, 0.72), (0.86, 0.72), (0.88, 0.97), (0.66, 0.97)], (250, 246, 230))
    lvl = 0.94 - 0.18 * ease(t / 6)
    c.P([(0.67, lvl), (0.87, lvl), (0.88, 0.96), (0.67, 0.96)], (246, 226, 140), 0)
    d = (t * 1.2) % 1
    c.O(0.77, 0.6 + d * (lvl - 0.6), 0.012, (246, 226, 140), 2)
    c.L([(0.77, 0.52), (0.77, 0.6)], p["rust"], 3)

def v_jasmine(c, t):
    p = c.p
    sw = wob(t, 0.5, 0.01)
    c.S("girl_back", 0.5 + sw, 1.05, 1.0, top_frac=0.34)
    for k in range(9):                                                              # jasmine string pinned on her loose hair
        a = math.pi * (0.15 + 0.7 * k / 8)
        c.O(0.5 + sw + 0.2 * math.cos(a), 0.3 - 0.06 * math.sin(a), 0.026, (255, 255, 252), 2)
    for k in range(6):
        c.O(0.69 + sw * 1.5 + 0.004 * k, 0.32 + k * 0.06, 0.022, (255, 255, 252), 2)
    for k in range(3):
        s_ = (t * 0.25 + k / 3) % 1
        c.O(0.15 + k * 0.32 + wob(s_, 1, 0.05), 0.05 + s_ * 0.5, 0.013, (255, 255, 252), 2)

def v_pookalam(c, t):
    p = c.p
    rings = [p["deep"], p["org"], p["yel"], (255, 255, 250), p["rust"], p["lemon"], p["org"]]
    k = t / 4.5
    for i in range(len(rings) - 1, -1, -1):
        if i / len(rings) > k: continue
        r = 0.08 + i * 0.055
        c.O(0.5, 0.5, r, rings[i], 3)
    for j in range(8):  # petal star in the middle
        a = j * math.pi / 4 + t * 0.2
        c.O(0.5 + 0.05 * math.cos(a), 0.5 + 0.04 * math.sin(a), 0.025, (255, 255, 250), 2)
    s = (t * 0.7) % 1
    c.O(0.85 - 0.2 * s, 0.05 + 0.3 * s, 0.02, p["yel"], 2)

def v_chenda(c, t):
    p = c.p
    hit = (t * 2.4) % 1
    for k in range(3):
        rr = 0.12 + ((hit + k / 3) % 1) * 0.35
        c.A(0.5, 0.36, rr, 200, 340, p["org"], 4)
    c.E(0.5, 0.38, 0.22, 0.05, p["cream"])
    c.R(0.28, 0.38, 0.72, 0.9, p["deep"], 4); c.E(0.5, 0.9, 0.22, 0.05, p["deep"])
    for k in range(5): c.L([(0.28 + k * 0.11, 0.4), (0.33 + k * 0.1, 0.9)], p["yel"], 3)
    l = 0.18 * abs(math.sin(math.pi * t * 2.4)); r = 0.18 * abs(math.cos(math.pi * t * 2.4))
    c.L([(0.2, 0.1 + l), (0.45, 0.36 - l * 0.2)], p["rust"], 8); c.L([(0.8, 0.1 + r), (0.55, 0.36 - r * 0.2)], p["rust"], 8)

def v_kathakali(c, t):
    p = c.p
    c.P([(0.18, 0.32), (0.82, 0.32), (0.92, 0.18), (0.5, 0.02), (0.08, 0.18)], GOLDC)
    for k in range(5): c.O(0.22 + k * 0.14, 0.2, 0.03, p["deep"], 2)
    c.E(0.5, 0.62, 0.36, 0.31, (255, 252, 242))   # white chutti frame
    c.E(0.5, 0.58, 0.26, 0.24, (150, 196, 70))    # pacha (green) face
    lift = 0.02 * abs(math.sin(t * 1.5))
    c.L([(0.28, 0.45), (0.36, 0.41 - lift), (0.45, 0.44)], p["out"], 6); c.L([(0.55, 0.44), (0.64, 0.41 - lift), (0.72, 0.45)], p["out"], 6)
    dx = 0.035 * math.sin(t * 2.2) if (t % 2) < 1.4 else 0.035 * math.sin(1.4 * 2.2)
    for x in (0.38, 0.62):
        c.E(x, 0.52, 0.07, 0.035, (255, 255, 255)); c.O(x + dx, 0.52, 0.022, p["out"], 0)
    c.PIE(0.5, 0.7, 0.08, 10, 170, (196, 50, 40), 3); c.L([(0.47, 0.55), (0.5, 0.64), (0.53, 0.55)], p["rust"], 3)

def v_three_faiths(c, t):
    p = c.p
    c.R(0, 0.8, 1, 1, p["rust"])
    c.R(0.04, 0.45, 0.3, 0.8, p["cream"]); c.P([(0.04, 0.45), (0.3, 0.45), (0.17, 0.2)], p["deep"])  # church
    c.L([(0.17, 0.2), (0.17, 0.08)], p["out"], 4); c.L([(0.13, 0.12), (0.21, 0.12)], p["out"], 4)
    c.R(0.12, 0.62, 0.22, 0.8, p["rust"])
    c.R(0.36, 0.5, 0.64, 0.8, p["cream"]); c.PIE(0.5, 0.5, 0.13, 180, 360, p["yel"])  # mosque
    c.R(0.6, 0.22, 0.65, 0.8, p["cream"]); c.PIE(0.625, 0.22, 0.035, 180, 360, p["yel"])
    c.A(0.5, 0.34, 0.03, 60, 300, p["out"], 4)
    c.R(0.7, 0.5, 0.96, 0.8, p["cream"]); c.P([(0.66, 0.52), (1.0, 0.52), (0.92, 0.4), (0.74, 0.4)], p["rust"])  # temple
    c.P([(0.72, 0.42), (0.94, 0.42), (0.88, 0.32), (0.78, 0.32)], p["rust"])
    c.L([(0.98, 0.8), (0.98, 0.15)], GOLDC, 5)
    for x in (0.17, 0.5, 0.83):
        f = 0.6 + 0.4 * abs(math.sin(t * 5 + x * 9))
        c.O(x, 0.74, 0.02 * f + 0.008, p["yel"], 0)
    for k in range(3):
        bx = ((t * 0.12 + k * 0.3) % 1.2) - 0.1
        c.L([(bx, 0.12 + k * 0.04), (bx + 0.025, 0.14 + k * 0.04), (bx + 0.05, 0.12 + k * 0.04)], p["out"], 3)

def v_sun(c, t):
    sun = PAINT.crop((735, 135, 885, 270)).resize((int(BW * 0.78), int(BW * 0.78 * 135 / 150)), Image.BICUBIC)
    sun = sun.rotate(-t * 9, resample=Image.BICUBIC, fillcolor=(250, 236, 180))
    m = Image.new("L", sun.size, 0); ImageDraw.Draw(m).ellipse((sun.width * 0.12, sun.height * 0.1, sun.width * 0.88, sun.height * 0.9), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10 * K))
    g = 1.0 + 0.08 * math.sin(t * 2)
    glow = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for k in range(6):
        r = BW * (0.3 + 0.06 * k) * g
        gd.ellipse((BW / 2 - r, BH / 2 - r, BW / 2 + r, BH / 2 + r), fill=(255, 214, 90, 26))
    c.img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16 * K)))
    c.img.paste(sun, (int(BW / 2 - sun.width / 2), int(BH / 2 - sun.height / 2)), m)

# ================================================================== BLUE boxes
def v_herbal_water(c, t):
    p = c.p
    c.P([(0.18, 0.2), (0.52, 0.2), (0.56, 0.86), (0.14, 0.86)], (250, 250, 252))
    c.P([(0.16, 0.38), (0.54, 0.38), (0.56, 0.84), (0.15, 0.84)], (240, 178, 140), 0)
    for k in range(6):
        a = t * 1.2 + k
        c.R(0.3 + 0.1 * math.cos(a), 0.6 + 0.12 * math.sin(a * 0.7), 0.33 + 0.1 * math.cos(a), 0.61 + 0.12 * math.sin(a * 0.7), (176, 70, 50), 0)
    c.A(0.6, 0.5, 0.1, -80, 80, p["out"], 6)
    c.R(0.66, 0.6, 0.86, 0.88, (230, 232, 236)); c.R(0.67, 0.68, 0.85, 0.87, (240, 178, 140), 0)
    c.L([(0.08, 0.94), (0.92, 0.94)], p["deep"], 6)

def v_swing(c, t):
    p = c.p
    c.L([(0.05, 0.06), (0.95, 0.06)], (110, 64, 34), 10)
    a = 0.3 * math.sin(t * 1.5)
    px, py, L = 0.5, 0.06, 0.66
    sx, sy = px + L * math.sin(a) * BH / BW * 0.5, py + L * math.cos(a)
    for o in (-0.16, 0.16): c.L([(px + o, py), (sx + o, sy)], (110, 64, 34), 3)
    c.S("girl_seat", sx, sy + 0.01, 0.36)
    c.R(sx - 0.24, sy, sx + 0.24, sy + 0.04, (150, 100, 60))

def v_ferry(c, t):
    p = c.p
    c.R(0, 0.55, 1, 1, p["mid"], 0)
    for k in range(5): c.A((k * 0.25 + t * 0.05) % 1.2, 0.68 + k % 2 * 0.12, 0.06, 200, 340, p["white"], 3)
    x = -0.4 + ((t * 0.18) % 1.8)
    c.P([(x, 0.5), (x + 0.5, 0.5), (x + 0.44, 0.62), (x + 0.06, 0.62)], p["white"])
    c.R(x + 0.1, 0.38, x + 0.38, 0.5, p["pale"]); c.R(x + 0.12, 0.31, x + 0.36, 0.38, p["deep"])
    for k in range(4): c.R(x + 0.13 + k * 0.06, 0.41, x + 0.17 + k * 0.06, 0.46, p["navy"], 0)
    for k in range(2):
        gx = ((t * 0.12 + k * 0.5) % 1.2) - 0.1
        c.L([(gx, 0.15 + k * 0.06), (gx + 0.03, 0.17 + k * 0.06 + wob(t, 2, 0.01)), (gx + 0.06, 0.15 + k * 0.06)], p["out"], 3)

def v_hospital(c, t):
    p = c.p
    c.R(0, 0.86, 1, 1, p["pale"], 0)
    c.R(0.12, 0.18, 0.88, 0.86, p["white"])
    for i in range(4):
        for j in range(4):
            c.R(0.18 + j * 0.17, 0.3 + i * 0.1, 0.3 + j * 0.17, 0.37 + i * 0.1, p["sky"], 2)
    c.O(0.5, 0.12, 0.07, p["white"]); c.R(0.485, 0.07, 0.515, 0.17, p["mid"], 0); c.R(0.45, 0.105, 0.55, 0.135, p["mid"], 0)
    op = 0.06 * (0.5 + 0.5 * math.sin(t * 1.3))
    c.R(0.38, 0.72, 0.62, 0.86, p["navy"]); c.R(0.38, 0.72, 0.5 - op, 0.86, p["sky"], 2); c.R(0.5 + op, 0.72, 0.62, 0.86, p["sky"], 2)
    for x in (0.05, 0.95):
        c.L([(x, 0.86), (x, 0.66)], p["out"], 5); c.O(x, 0.6, 0.08, p["mid"])

def v_cycle(c, t):
    p = c.p
    cols = [((250, 236, 190), TERRA), ((246, 246, 240), (60, 110, 180)), ((240, 200, 150), TERRA)]
    for i in range(3):
        x0 = 0.02 + i * 0.33; wall_, roof_ = cols[i]
        c.R(x0, 0.3, x0 + 0.3, 0.75, wall_)
        c.P([(x0, 0.3), (x0 + 0.3, 0.3), (x0 + 0.24, 0.2), (x0 + 0.2, 0.2), (x0 + 0.15, 0.1), (x0 + 0.1, 0.2), (x0 + 0.06, 0.2)], roof_)
        c.R(x0 + 0.1, 0.5, x0 + 0.2, 0.75, (110, 64, 34)); c.R(x0 + 0.04, 0.36, x0 + 0.11, 0.44, (60, 120, 70), 2); c.R(x0 + 0.19, 0.36, x0 + 0.26, 0.44, (60, 120, 70), 2)
    c.R(0, 0.75, 1, 1, (200, 196, 186), 0)
    x = -0.3 + ((t * 0.18) % 1.6)
    c.S("girl_open", x + 0.02, 0.96, 0.62)                                          # walking her bicycle
    for wx in (x + 0.08, x + 0.32):
        c.d.ellipse((c.X(wx) - 0.075 * BW, c.Y(0.88) - 0.075 * BW, c.X(wx) + 0.075 * BW, c.Y(0.88) + 0.075 * BW), outline=(40, 40, 40), width=int(5 * K))
        a = t * 6
        c.L([(wx - 0.06 * math.cos(a), 0.88 - 0.05 * math.sin(a)), (wx + 0.06 * math.cos(a), 0.88 + 0.05 * math.sin(a))], p["out"], 2)
    c.L([(x + 0.08, 0.88), (x + 0.18, 0.8), (x + 0.32, 0.88)], (60, 110, 180), 5); c.L([(x + 0.18, 0.8), (x + 0.3, 0.78)], (60, 110, 180), 5)

def v_canoe(c, t):
    p = c.p
    c.R(0, 0.5, 1, 1, (120, 176, 226), 0)
    for x in (0.1, 0.85):
        c.L([(x, 0.5), (x + 0.06, 0.12)], (110, 70, 40), 6); c.L([(x, 0.52), (x + 0.06, 0.88)], (90, 150, 200), 6)
        for a in (-1, 1): c.P([(x + 0.06, 0.12), (x + 0.06 + a * 0.16, 0.18), (x + 0.06 + a * 0.07, 0.1)], GREEN, 2)
    x = -0.3 + ((t * 0.12) % 1.6)
    c.S("dad", x + 0.22, 0.63, 0.34)                                                # Dad poling the canoe
    c.L([(x + 0.36, 0.26), (x + 0.16, 0.74)], (110, 64, 34), 4)
    c.P([(x, 0.6), (x + 0.42, 0.6), (x + 0.36, 0.67), (x + 0.06, 0.67)], (110, 64, 34))
    for k in range(3): c.A(x - 0.05 - k * 0.08, 0.67, 0.04, 200, 340, (240, 248, 255), 2)

def v_school(c, t):
    p = c.p
    c.R(0, 0.82, 1, 1, (200, 196, 186), 0)
    c.O(0.08, 0.6, 0.12, GREEN); c.L([(0.08, 0.82), (0.08, 0.66)], (110, 64, 34), 6)
    c.R(0.16, 0.36, 0.92, 0.82, (250, 236, 190)); c.P([(0.1, 0.38), (0.98, 0.38), (0.54, 0.14)], TERRA)
    for i in range(4): c.R(0.21 + i * 0.18, 0.48, 0.31 + i * 0.18, 0.6, (90, 150, 200), 2)
    c.R(0.46, 0.64, 0.62, 0.82, (110, 64, 34))
    ring = math.sin(t * 6) * 0.03
    c.O(0.54, 0.27, 0.04, GOLDC); c.L([(0.54, 0.23), (0.54 + ring, 0.31)], p["out"], 3)
    for k in range(2):
        r = 0.07 + ((t * 0.8 + k * 0.5) % 1) * 0.12
        c.A(0.54, 0.27, r, 200, 340, (250, 250, 250), 2)

def v_stars(c, t):
    p = c.p
    c.R(0, 0, 1, 1, (78, 122, 196), 0)
    for k in range(12):
        tw = 0.5 + 0.5 * math.sin(t * 3 + k * 1.7)
        c.O((k * 0.37) % 1, (k * 0.23) % 0.4, 0.006 + 0.006 * tw, p["white"], 0)
    c.R(0.05, 0.58, 0.45, 1, (246, 240, 226)); c.P([(0.0, 0.6), (0.5, 0.6), (0.25, 0.44)], TERRA)
    c.R(0.55, 0.64, 0.95, 1, (250, 230, 170)); c.P([(0.5, 0.66), (1.0, 0.66), (0.75, 0.5)], TERRA)
    for x in (0.18, 0.3, 0.68, 0.82): c.R(x - 0.04, 0.72, x + 0.04, 0.82, (255, 226, 120), 3)
    for cx, cy in ((0.25, 0.3), (0.75, 0.36)):
        sw = wob(t, 0.6, 8, cx * 5)
        c.L([(cx, 0.44 if cx < 0.5 else 0.5), (cx, cy)], p["white"], 2)
        R = 0.09; pts = []
        for i in range(10):
            a = math.radians(-90 + sw + i * 36); r = R if i % 2 == 0 else R * 0.45
            pts.append((cx + r * math.cos(a), cy + 0.05 + r * math.sin(a) * BW / BH))
        c.P(pts, (248, 224, 110), 3)

# ================================================================== natural-colour boxes (v2)
GREEN, LGREEN, DGREEN = (70, 150, 60), (140, 196, 80), (36, 100, 48)
SOIL, LAT, TERRA = (120, 72, 40), (190, 96, 60), (178, 80, 42)
WATER, STONE, STEEL = (84, 152, 212), (176, 174, 168), (206, 208, 214)
LPINK, PINKTIP = (252, 238, 240), (232, 140, 168)

def v_alarm_off(c, t):
    p = c.p
    k = ease((t - 1.2) / 0.5)
    sh = wob(t, 11, 0.012) if t < 1.2 else 0
    if t < 1.2:
        for s in (-1, 1):
            for j in range(2): c.A(0.5 + sh, 0.42, 0.33 + j * 0.07, 200 if s < 0 else -20, 250 if s < 0 else 30, p["deep"], 4)
    c.L([(0.32 + sh, 0.62), (0.26 + sh, 0.7)], p["out"], 6); c.L([(0.68 + sh, 0.62), (0.74 + sh, 0.7)], p["out"], 6)
    for s in (-1, 1): c.O(0.5 + s * 0.19 + sh, 0.2, 0.09, p["deep"])
    c.O(0.5 + sh, 0.42, 0.26, p["yel"]); c.O(0.5 + sh, 0.42, 0.2, p["cream"])
    c.L([(0.5 + sh, 0.42), (0.5 + sh, 0.3)], p["out"], 5); c.L([(0.5 + sh, 0.42), (0.6 + sh, 0.45)], p["out"], 5)
    if k > 0: c.L([(0.18, 0.14), (0.18 + 0.64 * k, 0.14 + 0.56 * k)], (200, 52, 40), 16)
    k2 = ease((t - 1.8) / 0.4)
    col = tuple(int(a + (b - a) * k2) for a, b in zip((96, 186, 96), (176, 176, 176)))
    c.R(0.3, 0.8, 0.7, 0.9, col, 4, r=40)
    c.O(0.62 - 0.24 * k2, 0.85, 0.075, (255, 255, 255))
    if t > 2.5:
        for j in range(3):
            s_ = ((t - 2.5) * 0.35 + j / 3) % 1
            c.O(0.78 + 0.08 * s_, 0.3 - 0.25 * s_, 0.02 + 0.025 * s_, p["wash"], 3)

def v_courtyard(c, t):
    p = c.p
    x0, x1, y0, y1 = 0.04, 0.96, 0.15, 0.85
    ix0, ix1, iy0, iy1 = 0.3, 0.7, 0.35, 0.65
    for (cx, cy) in ((0.02, 0.06), (0.98, 0.06), (0.02, 0.94), (0.98, 0.94)): c.O(cx, cy, 0.12, GREEN)
    c.R(ix0, iy0, ix1, iy1, (232, 214, 186))                                        # open courtyard floor
    sx = ix0 + 0.04 + 0.2 * (0.5 + 0.5 * math.sin(t * 0.4))
    c.d.polygon(c.pts([(sx, iy0), (sx + 0.16, iy0), (sx + 0.1, iy1), (sx - 0.06, iy1)]), fill=(255, 244, 200, 140))
    c.R(0.46, 0.46, 0.54, 0.54, (250, 250, 246)); c.O(0.5, 0.5, 0.035, GREEN, 3)     # tulsi thara
    c.E(0.36, 0.6, 0.035, 0.02, WATER, 3)
    roofs = [[(x0, y0), (x1, y0), (ix1, iy0), (ix0, iy0)], [(x1, y0), (x1, y1), (ix1, iy1), (ix1, iy0)],
             [(x1, y1), (x0, y1), (ix0, iy1), (ix1, iy1)], [(x0, y1), (x0, y0), (ix0, iy0), (ix0, iy1)]]
    for i, r in enumerate(roofs):
        c.P(r, (TERRA, (196, 98, 54), TERRA, (160, 70, 36))[i])
    for k in range(1, 8):
        f = k / 8
        c.L([(x0 + (x1 - x0) * f, y0), (ix0 + (ix1 - ix0) * f, iy0)], (130, 56, 30), 2)
        c.L([(x0 + (x1 - x0) * f, y1), (ix0 + (ix1 - ix0) * f, iy1)], (130, 56, 30), 2)
        c.L([(x0, y0 + (y1 - y0) * f), (ix0, iy0 + (iy1 - iy0) * f)], (130, 56, 30), 2)
        c.L([(x1, y0 + (y1 - y0) * f), (ix1, iy0 + (iy1 - iy0) * f)], (130, 56, 30), 2)
    a = t * 0.7                                                                      # Mum walking round the tulsi
    mx, my = 0.5 + 0.13 * math.cos(a), 0.5 + 0.1 * math.sin(a)
    c.E(mx, my, 0.05, 0.03, MUMKURTI); c.O(mx, my, 0.025, HAIR)
    bx = -0.1 + ((t * 0.2) % 1.3)
    c.L([(bx, 0.3), (bx + 0.04, 0.28 + wob(t, 3, 0.01)), (bx + 0.08, 0.3)], (60, 50, 50), 4)

def v_verandah(c, t):
    p = c.p
    c.R(0, 0.74, 1, 1, (176, 52, 40))                                                # red-oxide floor
    c.R(0.04, 0.0, 0.12, 0.74, (120, 72, 40))                                       # pillar
    c.O(0.88, 0.7, 0.07, LAT)
    for j in range(5): c.E(0.88 + 0.06 * math.cos(j * 1.3 + wob(t, 0.4, 0.2)), 0.6 - 0.05 * abs(math.sin(j)), 0.05, 0.02, GREEN, 2)
    c.L([(0.22, 0.9), (0.36, 0.5)], (110, 60, 30), 8); c.L([(0.76, 0.9), (0.62, 0.48)], (110, 60, 30), 8)
    c.P([(0.3, 0.52), (0.66, 0.5), (0.72, 0.84), (0.28, 0.86)], (234, 176, 64))       # cloth sling
    for j in range(4): c.L([(0.33 + j * 0.1, 0.52), (0.31 + j * 0.12, 0.85)], (200, 80, 40), 3)
    c.S("girl_seat", 0.5, 0.86 + wob(t, 0.3, 0.004), 0.55)
    c.L([(0.24, 0.62), (0.76, 0.6)], (110, 60, 30), 8)                                # chair arms
    c.R(0.16, 0.86, 0.24, 0.94, (236, 236, 236), 3)
    for j in range(2):
        s_ = (t * 0.5 + j / 2) % 1
        c.L([(0.19 + j * 0.03 + wob(s_, 1.4, 0.01), 0.84 - s_ * 0.15), (0.19 + j * 0.03, 0.8 - s_ * 0.15)], (250, 250, 250), 3)

def v_mango(c, t):
    p = c.p
    c.L([(0, 0.14), (1, 0.08)], (110, 64, 34), 10)
    for i in range(6): c.E(0.08 + i * 0.17, 0.16 + 0.03 * (i % 2), 0.08, 0.03, GREEN, 3)
    c.P([(0.05, 0.62), (0.45, 0.62), (0.41, 0.82), (0.09, 0.82)], (214, 170, 100))
    for k in range(3): c.L([(0.07, 0.67 + k * 0.05), (0.43, 0.67 + k * 0.05)], (150, 100, 50), 2)
    y = 0.25 if t < 0.6 else fall(t, 0.6, 0.25, 0.6, 0.6)
    c.E(0.25, y, 0.07, 0.045, (246, 186, 40), 3)
    if t > 2.0:
        sx = 0.7 + 0.5 * (1 - ease((t - 2.0) / 0.6))
        c.E(sx, 0.86, 0.26, 0.06, (250, 250, 250))
        c.E(sx, 0.76, 0.18, 0.12, (246, 160, 30))                                    # sliced cheek, cubes
        for i in range(-2, 3):
            for j in range(-1, 2):
                c.R(sx + i * 0.06 - 0.025, 0.76 + j * 0.06 - 0.022, sx + i * 0.06 + 0.025, 0.76 + j * 0.06 + 0.022, (252, 196, 50), 2)

def _petal(c, bx, by, ang, ln, wd, fill, tip):
    ca, sa = math.cos(ang), math.sin(ang)
    asp = BW / BH
    pt = lambda u, v: (bx + (u * sa + v * ca) * 1.0, by - (u * ca - v * sa) * asp)
    c.P([pt(0, 0), pt(ln * 0.45, -wd), pt(ln, 0), pt(ln * 0.45, wd)], fill, 3)
    c.P([pt(ln * 0.7, -wd * 0.45), pt(ln, 0), pt(ln * 0.7, wd * 0.45)], tip, 0)

def v_lotus(c, t):
    p = c.p
    c.R(0, 0.45, 1, 1, (120, 176, 226), 0)
    for k in range(3):
        s_ = (t * 0.3 + k / 3) % 1
        c.A(0.5, 0.74, 0.12 + 0.4 * s_, 200, 340, (230, 242, 252), 3)
    for (x, y, r, a0) in ((0.2, 0.86, 0.16, 30), (0.82, 0.7, 0.13, 200), (0.75, 0.93, 0.1, 120)):
        yb = y + wob(t, 0.4, 0.006, x * 9)
        c.d.pieslice((c.X(x - r), c.Y(yb - r * 0.45 * BW / BH), c.X(x + r), c.Y(yb + r * 0.45 * BW / BH)), a0 + 25, a0 + 360, fill=GREEN, outline=c.o, width=int(3 * K))
    c.L([(0.5, 0.74), (0.5, 0.95)], DGREEN, 6)
    op = 0.35 + 0.45 * ease(t / 3.5)
    base = (0.5, 0.7)
    for j, a in enumerate((-1.5, -0.9, 0.9, 1.5)):                                  # back petals
        _petal(c, base[0], base[1], a * op, 0.2, 0.06, LPINK, PINKTIP)
    for j, a in enumerate((-0.55, 0.0, 0.55)):                                      # front petals
        _petal(c, base[0], base[1] + 0.01, a * op, 0.24, 0.07, (255, 246, 248), PINKTIP)
    c.E(0.5, 0.6 - 0.05 * op, 0.05, 0.02, (240, 210, 70), 3)
    bx = 0.82; c.L([(bx, 0.68), (bx - 0.02, 0.4)], DGREEN, 5)                        # a bud
    _petal(c, bx - 0.02, 0.42, 0.0, 0.14, 0.05, (250, 226, 232), PINKTIP)

def v_paddy(c, t):
    p = c.p
    c.R(0, 0.0, 1, 0.3, (190, 220, 246), 0)
    for i in range(6):
        x = 0.05 + i * 0.18
        c.L([(x, 0.34), (x + 0.02, 0.12)], (90, 70, 50), 4)
        for a in (-1, 1): c.P([(x + 0.02, 0.12), (x + 0.02 + a * 0.1, 0.16), (x + 0.02 + a * 0.04, 0.1)], DGREEN, 2)
    c.R(0, 0.3, 1, 1, (150, 200, 230), 0)
    for r in range(7):
        y = 0.34 + r * 0.1 * (1 + r * 0.12)
        n = 9 + r * 2
        for i in range(n):
            x = (i + 0.5) / n
            sw = wob(t, 0.5, 0.01 + 0.004 * r, x * 6 + r)
            hgt = 0.03 + 0.012 * r
            for d in (-1, 0, 1):
                c.L([(x + d * 0.008, y), (x + d * 0.012 + sw, y - hgt)], (GREEN, LGREEN, DGREEN)[(i + r + d) % 3], 3 + r // 2)
    ex = 0.65 - 0.06 * t if t < 3 else 0.47 - (t - 3) * 0.1
    ey = 0.56 if t < 3 else 0.56 - (t - 3) * 0.12
    c.E(ex, ey, 0.05, 0.025, (255, 255, 255), 3); c.L([(ex - 0.04, ey - 0.01), (ex - 0.07, ey - 0.06)], (255, 255, 255), 5)
    c.O(ex - 0.075, ey - 0.065, 0.015, (255, 255, 255), 2); c.L([(ex - 0.085, ey - 0.06), (ex - 0.12, ey - 0.055)], (240, 200, 60), 3)
    if t >= 3:
        f = wob(t, 3, 0.04)
        c.P([(ex, ey), (ex + 0.1, ey - 0.06 + f), (ex + 0.05, ey)], (255, 255, 255), 2)
    else:
        c.L([(ex, ey + 0.02), (ex + 0.01, ey + 0.08)], (240, 200, 60), 3)

def v_tender_coconut(c, t):
    p = c.p
    c.L([(0.18, 0.95), (0.18, 0.16)], (110, 64, 34), 6)                              # umbrella
    for i in range(6):
        a0, a1 = math.pi + i * math.pi / 6, math.pi + (i + 1) * math.pi / 6
        c.P([(0.18, 0.08), (0.18 + 0.32 * math.cos(a0), 0.2 + 0.1 * math.sin(a0) * 0.2), (0.18 + 0.32 * math.cos(a1), 0.2 + 0.1 * math.sin(a1) * 0.2)],
            ((234, 110, 40), (250, 246, 236))[i % 2], 3)
    c.R(0.05, 0.72, 0.62, 0.8, (130, 80, 40))
    for i in range(5): c.O(0.1 + i * 0.12, 0.66 - (i % 2) * 0.03, 0.07, (120, 176, 60))
    cx, cy = 0.72, 0.62
    c.O(cx, cy, 0.17, (140, 190, 70))
    cut = t > 0.9
    if cut:
        c.E(cx, cy - 0.09, 0.08, 0.025, (250, 248, 230))
        fx = cx + 0.05 + min(t - 0.9, 0.6) * 0.3; fy = cy - 0.14 - min(t - 0.9, 0.6) * 0.2 + max(t - 1.2, 0) ** 2 * 0.6
        if fy < 1.1: c.E(fx, fy, 0.06, 0.03, (140, 190, 70))
    else:
        c.P([(cx - 0.07, cy - 0.12), (cx + 0.07, cy - 0.12), (cx, cy - 0.2)], (160, 200, 90))
    ang = 0.0 if t < 0.6 else min((t - 0.6) / 0.3, 1.0)
    hx, hy = 0.98, 0.18 + 0.12 * ang
    c.L([(1.05, 0.3), (hx, hy)], SKIN, 14)
    c.P([(hx - 0.02, hy - 0.02), (hx - 0.26, hy + 0.02 + 0.08 * ang), (hx - 0.24, hy + 0.06 + 0.08 * ang), (hx, hy + 0.03)], STEEL)
    if t > 1.6:
        sy = fall(t, 1.6, 0.0, 0.32)
        c.L([(cx + 0.02, sy + 0.18), (cx + 0.08, sy)], (250, 250, 250), 10); c.L([(cx + 0.02, sy + 0.18), (cx + 0.08, sy)], (230, 70, 50), 3)

def v_backyard(c, t):
    p = c.p
    c.R(0, 0.0, 1, 0.42, (196, 224, 246), 0)
    c.L([(0.86, 0.42), (0.88, 0.05)], (120, 80, 40), 8)                             # coconut palm
    for a in (-2.6, -2.0, -1.2, -0.5): c.P([(0.88, 0.05), (0.88 + 0.2 * math.cos(a), 0.05 - 0.08 * math.sin(a) + 0.1), (0.88 + 0.12 * math.cos(a + 0.2), 0.05 - 0.04 * math.sin(a))], GREEN, 2)
    c.O(0.12, 0.2, 0.14, DGREEN); c.O(0.26, 0.24, 0.1, GREEN); c.L([(0.16, 0.42), (0.16, 0.28)], (110, 64, 34), 8)
    c.L([(0.32, 0.24), (0.72, 0.24)], (130, 90, 50), 4)                               # pandal (trellis)
    for x in (0.32, 0.52, 0.72): c.L([(x, 0.24), (x, 0.42)], (130, 90, 50), 3)
    for i in range(4):
        gx = 0.38 + i * 0.1; gl = 0.06 + 0.06 * ease((t - i * 0.3) / 2)
        c.E(gx, 0.27 + gl, 0.018, gl, (110, 170, 60), 2)
    c.R(0, 0.42, 1, 1, (150, 96, 54), 0)
    for r in range(3):
        y = 0.52 + r * 0.16
        c.R(0.02, y + 0.06, 0.98, y + 0.1, SOIL, 2)
        for i in range(5):
            x = 0.1 + i * 0.2; h = 0.04 + 0.06 * ease((t - r * 0.4 - i * 0.1) / 2.5)
            c.L([(x, y + 0.06), (x + wob(t, 0.5, 0.006, i), y + 0.06 - h)], DGREEN, 4)
            for s in (-1, 1): c.E(x + s * 0.03, y + 0.06 - h * 0.6, 0.03, 0.012, (GREEN, LGREEN)[i % 2], 2)
            if h > 0.08: c.O(x + 0.015, y + 0.06 - h * 0.4, 0.016, ((214, 50, 40), (230, 120, 30), (100, 170, 50))[r], 2)
    hx = 0.9; hy = 0.5 + wob(t, 0.6, 0.01)
    c.L([(1.05, 0.62), (hx, hy + 0.04)], SKIN, 12)
    c.P([(hx - 0.2, hy), (hx - 0.02, hy), (hx, hy + 0.1), (hx - 0.18, hy + 0.1)], (70, 140, 200))
    c.L([(hx - 0.2, hy + 0.03), (hx - 0.3, hy - 0.02)], (70, 140, 200), 6)
    for k in range(5):
        s_ = (t * 1.6 + k / 5) % 1
        c.O(hx - 0.31 - s_ * 0.04 + 0.01 * k, hy + s_ * 0.2, 0.008, (210, 236, 252), 0)

def v_herbs(c, t):
    p = c.p
    c.R(0, 0.78, 1, 1, SOIL, 0)
    c.R(0.3, 0.62, 0.7, 0.95, (250, 250, 246)); c.R(0.26, 0.57, 0.74, 0.64, (236, 232, 222))
    c.L([(0.5, 0.58), (0.5, 0.3)], (110, 64, 34), 5)
    for i in range(30):
        a = i * 2.4; rr = 0.04 + 0.16 * ((i * 37) % 30) / 30
        x = 0.5 + rr * math.cos(a) + wob(t, 0.5, 0.008, i); y = 0.36 + rr * 0.9 * math.sin(a) * BW / BH
        c.E(x, y, 0.035, 0.018, (GREEN, LGREEN, DGREEN)[i % 3], 2)
    for x in (0.1, 0.9):
        for k in range(4): c.P([(x - 0.03, 0.95), (x + 0.03, 0.95), (x + (k - 1.5) * 0.06, 0.62 + (k % 2) * 0.05)], (90, 160, 90), 2)
    s_ = (t * 0.25) % 1
    c.E(0.78 - s_ * 0.2, 0.2 + s_ * 0.6, 0.025, 0.012, LGREEN, 2)

def v_well(c, t):
    p = c.p
    c.R(0, 0.9, 1, 1, (150, 96, 54), 0)
    c.R(0.15, 0.62, 0.85, 0.96, LAT); c.E(0.5, 0.62, 0.35, 0.05, (40, 70, 120))
    for k in range(3): c.L([(0.15, 0.7 + k * 0.08), (0.85, 0.7 + k * 0.08)], (150, 70, 40), 3)
    for k in range(4):
        for r in range(3): c.L([(0.25 + k * 0.17 + (r % 2) * 0.08, 0.62 + r * 0.08), (0.25 + k * 0.17 + (r % 2) * 0.08, 0.7 + r * 0.08)], (150, 70, 40), 3)
    c.L([(0.18, 0.62), (0.18, 0.12)], (110, 64, 34), 9); c.L([(0.82, 0.62), (0.82, 0.12)], (110, 64, 34), 9); c.L([(0.14, 0.12), (0.86, 0.12)], (110, 64, 34), 9)
    c.O(0.5, 0.16, 0.05, (150, 100, 60))
    y = 0.36 + 0.22 * (0.5 + 0.5 * math.cos(t * 1.1))
    c.L([(0.5, 0.2), (0.5, y)], (90, 60, 40), 3)
    c.P([(0.43, y), (0.57, y), (0.55, y + 0.1), (0.45, y + 0.1)], STEEL)
    if y < 0.45:
        for k in range(3): c.O(0.45 + k * 0.05, y + 0.12 + ((t * 2 + k * 0.3) % 1) * 0.15, 0.012, (150, 200, 240), 0)

def v_friends(c, t):
    p = c.p
    c.R(0, 0, 1, 0.5, (200, 226, 248), 0); c.R(0, 0.5, 1, 0.75, WATER, 0)
    for k in range(4): c.A(0.15 + k * 0.25, 0.58, 0.04, 200, 340, (240, 248, 255), 3)
    for i, (x, name) in enumerate(((0.3, "girl_open"), (0.7, "friend"))):
        bob = abs(math.sin(t * 3 + i)) * 0.012 if (t % 2.5) < 1.2 else 0
        c.S(name, x, 0.78 - bob, 0.62, top_frac=0.45)
    c.R(0, 0.74, 1, 1, STONE)
    for r in range(3):
        for k in range(5): c.R(k * 0.22 - (r % 2) * 0.11, 0.74 + r * 0.087, k * 0.22 - (r % 2) * 0.11 + 0.22, 0.74 + (r + 1) * 0.087, STONE, 2)

def v_bus(c, t):
    p = c.p
    c.R(0, 0, 1, 1, (200, 228, 250), 0)
    for i in range(5):
        x = 1.1 - ((t * 0.7 + i * 0.3) % 1.5)
        if i % 2:
            c.R(x, 0.36, x + 0.16, 0.6, ((250, 236, 190), (240, 200, 150))[i % 2]); c.P([(x - 0.02, 0.36), (x + 0.18, 0.36), (x + 0.08, 0.28)], TERRA)
        else:
            c.L([(x, 0.62), (x + 0.02, 0.2)], (110, 70, 40), 6)
            for a in (-1, 1): c.P([(x + 0.02, 0.2), (x + 0.02 + a * 0.14, 0.26), (x + 0.02 + a * 0.06, 0.18)], GREEN, 2)
    c.R(0, 0.6, 1, 0.66, (120, 120, 120), 0)
    c.R(0, 0, 1, 0.12, (236, 180, 40)); c.R(0, 0.62, 1, 1, (236, 180, 40)); c.R(0, 0, 0.06, 1, (236, 180, 40)); c.R(0.94, 0, 1, 1, (236, 180, 40))
    c.R(0, 0.7, 1, 0.75, (200, 50, 40), 0)
    c.L([(0.06, 0.6), (0.94, 0.6)], STEEL, 8)
    c.L([(0.06, 0.58), (0.45, 0.58)], SKIN, 16); c.E(0.47, 0.58, 0.05, 0.022, SKIN)
    w = wob(t, 1.8, 0.03)
    c.L([(0.7, 0.9), (0.76 + w, 0.75), (0.8 - w, 0.7)], HAIR, 10)

def v_neighbours(c, t):
    p = c.p
    c.S("mum", 0.24, 0.78, 0.7, top_frac=0.42)
    c.S("friend", 0.76, 0.78, 0.68, top_frac=0.45)
    k = 0.5 - 0.5 * math.cos(t * 1.2)
    x = 0.32 + 0.36 * k; y = 0.42 - 0.14 * math.sin(math.pi * k)
    c.L([(0.3, 0.52), (x - 0.04, y + 0.03)], SKIN, 9) if k < 0.55 else c.L([(0.7, 0.52), (x + 0.04, y + 0.03)], SKIN, 9)
    c.R(x - 0.06, y - 0.08, x + 0.06, y + 0.06, STEEL); c.L([(x - 0.06, y - 0.03), (x + 0.06, y - 0.03)], p["out"], 2)
    c.A(x, y - 0.08, 0.04, 180, 360, p["out"], 3)
    c.R(0, 0.6, 1, 1, LAT)                                                           # low laterite wall
    for r in range(4):
        for j in range(6): c.R(j * 0.2 - (r % 2) * 0.1, 0.6 + r * 0.1, j * 0.2 - (r % 2) * 0.1 + 0.2, 0.7 + r * 0.1, LAT, 2)
    c.R(0, 0.58, 1, 0.62, (220, 210, 196))

def v_fishing_net(c, t):
    p = c.p
    c.R(0, 0, 1, 0.6, (250, 220, 160), 0)
    c.O(0.18, 0.34, 0.07, (244, 150, 60))
    c.R(0, 0.6, 1, 1, WATER, 0)
    for k in range(4): c.A(0.15 + k * 0.24, 0.72 + (k % 2) * 0.1, 0.05, 200, 340, (230, 244, 255), 3)
    c.R(0.0, 0.56, 0.34, 0.62, (130, 84, 46))                                        # jetty
    for x in (0.04, 0.16, 0.28): c.L([(x, 0.62), (x, 0.85)], (110, 64, 34), 5)
    dip = 0.5 + 0.5 * math.sin(t * 0.7)                                             # 0 = up, 1 = in the water
    a = math.radians(38 - 30 * dip)
    px, py = 0.26, 0.56
    L = 0.5
    tx, ty = px + L * math.cos(a), py - L * math.sin(a) * BW / BH
    bx, by = px - 0.22 * math.cos(a), py + 0.22 * math.sin(a) * BW / BH
    c.L([(px, py), (px + 0.05, 0.12)], (110, 64, 34), 5)                              # king post and stay
    c.L([(px + 0.05, 0.12), (tx, ty)], (90, 60, 40), 2); c.L([(px + 0.05, 0.12), (bx, by)], (90, 60, 40), 2)
    c.L([(bx, by), (tx, ty)], (110, 64, 34), 8)                                       # main beam
    for j in range(3):                                                              # counterweight stones
        c.L([(bx + j * 0.03, by), (bx + j * 0.03, by + 0.1)], (90, 60, 40), 2); c.O(bx + j * 0.03, by + 0.11, 0.02, STONE, 2)
    span = 0.3
    ends = [(tx - span, ty + 0.12), (tx + span * 0.9, ty + 0.1), (tx - span * 0.5, ty + 0.2), (tx + span * 0.45, ty + 0.2)]
    for ex, ey in ends: c.L([(tx, ty), (ex, ey)], (110, 64, 34), 4)                  # four bamboo arms
    sag = 0.1
    for k in range(9):                                                              # net mesh hanging between the arms
        f = k / 8
        x0 = ends[0][0] + (ends[1][0] - ends[0][0]) * f; y0 = ends[0][1] + (ends[1][1] - ends[0][1]) * f
        c.L([(x0, y0), (tx + (x0 - tx) * 0.5, y0 + sag + 0.06 * math.sin(math.pi * f))], (250, 250, 250), 2)
    c.A(tx - 0.02, ends[0][1] + 0.02, span * 0.95, 15, 165, (250, 250, 250), 3)

# ------------------------------------------------------------------ layout: final 5x7 wall
# warm (sun) cells: cols 0-1 and col 2 rows 0-2.  blue (sea) cells: the rest.  The first 9 sit in the centre 3x3.
def is_warm(cell): return cell[0] <= 1 or (cell[0] == 2 and cell[1] <= 2)

FIRST = [((1, 2), v_mum_drive), ((2, 2), v_dad_serve),                      # 2 on screen
         ((1, 3), v_alarm_off),                                             # 3
         ((2, 3), v_courtyard), ((3, 2), v_fishing_net), ((3, 3), v_cycle),  # 6
         ((1, 4), v_easel), ((2, 4), v_backyard), ((3, 4), v_three_faiths)]  # 9
SUN_CELL = (0, 4)
REST_WARM = [v_verandah, v_sadya, v_fritters, v_chai, v_coconut_oil, v_jasmine, v_mango, v_pookalam, v_chenda,
             v_kathakali, v_tender_coconut, v_herbal_water]
REST_BLUE = [v_well, v_lotus, v_swing, v_ferry, v_bus, v_hospital, v_paddy, v_canoe, v_school, v_friends, v_herbs,
             v_stars, v_neighbours]

def build_layout():
    out = {cell: v for cell, v in FIRST}
    out[SUN_CELL] = v_sun
    free = [(c_, r_) for r_ in range(ROWS) for c_ in range(COLS) if (c_, r_) not in out]
    fw = [c_ for c_ in free if is_warm(c_)]; fb = [c_ for c_ in free if not is_warm(c_)]
    assert len(fw) == len(REST_WARM) and len(fb) == len(REST_BLUE), (len(fw), len(fb))
    for c_, v in zip(fw, REST_WARM): out[c_] = v
    for c_, v in zip(fb, REST_BLUE): out[c_] = v
    return out

LAYOUT = build_layout()
ORDER = [cell for cell, _ in FIRST] + sorted([c_ for c_ in LAYOUT if c_ not in dict(FIRST)], key=lambda c_: (c_[1] * 7 + c_[0] * 3) % 35)

# ------------------------------------------------------------------ timing (seconds)
STAGES = [(2, (1, 2)), (3, (1, 3)), (6, (2, 3)), (9, (3, 3)), (35, (COLS, ROWS))]
T_STAGE = [0.0, 2.6, 4.9, 7.6, 10.3]
TR = 0.7                      # transition length
T_PUSH, T_REVEAL, T_END = 13.4, 15.0, 17.0
STAGE_POS = {                 # slot (col,row) of each box in the smaller grids
    2: {(1, 2): (0, 0), (2, 2): (0, 1)},
    3: {(1, 2): (0, 0), (2, 2): (0, 1), (1, 3): (0, 2)},
    6: {(1, 2): (0, 0), (2, 2): (1, 0), (1, 3): (0, 1), (2, 3): (1, 1), (3, 2): (0, 2), (3, 3): (1, 2)},
    9: {cell: (cell[0] - 1, cell[1] - 2) for cell, _ in FIRST},
}

def final_rect(cell):
    ci, ri = cell
    return (GAP + ci * (CW + GAP), GAP + ri * (CH + GAP), CW, CH)

def stage_rect(n, grid, cell):
    if n == 35: return final_rect(cell)
    cols, rows = grid; M = 40; g = 28
    sw, sh = (W - 2 * M) / cols, (H - 2 * M) / rows
    a = CW / CH
    bw = min(sw - g, (sh - g) * a); bh = bw / a
    sc, sr = STAGE_POS[n][cell]
    return (M + sc * sw + (sw - bw) / 2, M + sr * sh + (sh - bh) / 2, bw, bh)

def appear_time(cell):
    k = ORDER.index(cell)
    for s, (n, _) in enumerate(STAGES):
        if k < n:
            base = T_STAGE[s]
            if s == 4: return base + 0.035 * (k - 9)
            return base
    return 0

def lerp_rect(a, b, k): return tuple(x + (y - x) * k for x, y in zip(a, b))

def box_state(cell, t):
    """rect (x,y,w,h) and alpha for one box at time t, or None if not on screen yet."""
    ta = appear_time(cell)
    if t < ta: return None
    s = max(i for i, ts in enumerate(T_STAGE) if ts <= t)
    n, grid = STAGES[s]
    k = ORDER.index(cell)
    target = stage_rect(n, grid, cell)
    first_stage = next(i for i, (nn, _) in enumerate(STAGES) if k < nn)
    if s == first_stage:            # sliding in like a scroll from below
        dur = TR if s < 4 else 0.45
        e = ease((t - ta) / dur)
        x, y, w_, h_ = target
        return (x, y + (1 - e) * 260, w_, h_), e
    prev = stage_rect(STAGES[s - 1][0], STAGES[s - 1][1], cell)
    e = ease((t - T_STAGE[s]) / TR)
    return lerp_rect(prev, target, e), 1.0

BGS = {}
def cell_img(cell, t, size):
    v = LAYOUT[cell]; warm = is_warm(cell)
    if cell not in BGS: BGS[cell] = bg_for(warm, (cell[0] * 31 + cell[1] * 7) % 997 + 3)
    img = BGS[cell].copy()
    pal = {**(BLUE if warm else WARM), **(WARM if warm else BLUE)}
    v(C(img, pal), max(t, 0.0))
    return img.resize((max(1, int(size[0])), max(1, int(size[1]))), Image.LANCZOS)

WEAVE = None
def linen_overlay():
    r = np.random.default_rng(11)
    rows = r.normal(0, 1, (H, 1)); cols = r.normal(0, 1, (1, W))
    fine = (np.indices((H, W)).sum(0) % 4 < 2) * 0.5 - 0.25
    return (1 + 0.05 * np.tanh(0.5 * rows + 0.5 * cols) + 0.012 * fine)[..., None].astype(np.float32)

def wall(t):
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    for cell in ORDER:
        st = box_state(cell, t)
        if st is None: continue
        (x, y, w_, h_), al = st
        if t >= T_STAGE[4] + 1.5:
            x += 3 * math.sin(t * 0.5 + cell[0] + cell[1] * 2); y += 3 * math.cos(t * 0.4 + cell[1] + cell[0])
        im = cell_img(cell, t - appear_time(cell), (w_, h_))
        if al < 1:
            a_ = im.split()[3].point(lambda v_: int(v_ * al)); im.putalpha(a_)
        base.alpha_composite(im, (int(x), int(y)))
    return base

def painting_card(t):
    base = Image.new("RGB", (W, H), PAPER)
    k = ease((t - T_REVEAL) / (T_END - T_REVEAL))
    z = 1.25 - 0.25 * k
    pw = int(W * 0.94 * z); ph = int(pw * PAINT.height / PAINT.width)
    im = PAINT.resize((pw, ph), Image.LANCZOS)
    base.paste(im, ((W - pw) // 2, (H - ph) // 2 - 60))
    return base

def frame(t):
    global WEAVE
    if WEAVE is None: WEAVE = linen_overlay()
    if t < T_PUSH:
        img = wall(t).convert("RGB")
    else:
        img = wall(T_PUSH + 0.0 * (t - T_PUSH) + (t - T_PUSH) * 0.5).convert("RGB")
        x, y, w_, h_ = final_rect(SUN_CELL)
        cx, cy = x + w_ / 2, y + h_ / 2
        k = ease((t - T_PUSH) / (T_REVEAL - T_PUSH))
        z = 1 + (H / h_ - 1) * k ** 1.6
        fx = W / 2 + (cx - W / 2) * min(1, k * 1.4); fy = H / 2 + (cy - H / 2) * min(1, k * 1.4)
        zw, zh = W / z, H / z
        box = (fx - zw / 2, fy - zh / 2, fx + zw / 2, fy + zh / 2)
        img = img.transform((W, H), Image.EXTENT, box, Image.BICUBIC)
        if t > T_REVEAL - 0.5:
            img = Image.blend(img, painting_card(t), ease((t - (T_REVEAL - 0.5)) / 0.8))
    a = np.asarray(img).astype(np.float32) * WEAVE
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def job(i): return frame(i / FPS).tobytes()

def sheet(times, name="sheet.jpg"):
    ims = [frame(t).resize((270, 480), Image.LANCZOS) for t in times]
    out = Image.new("RGB", (270 * len(ims) + 8 * (len(ims) + 1), 496), PAPER)
    for i, im in enumerate(ims): out.paste(im, (8 + i * 278, 8))
    out.save(os.path.join(HERE, name), quality=90)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "still"
    if mode == "still":
        frame(float(sys.argv[2]) if len(sys.argv) > 2 else 12.5).save(os.path.join(HERE, "boxwall_still.jpg"), quality=92)
    elif mode == "sheet":
        sheet([float(x) for x in sys.argv[2:]])
    elif mode == "zoom":
        t = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
        cells = ORDER
        sw_, sh_ = BW // 3, BH // 3
        out = Image.new("RGB", (7 * sw_ + 8 * 6, 5 * sh_ + 6 * 6), PAPER)
        for k, cell in enumerate(cells):
            im = cell_img(cell, t, (sw_, sh_))
            out.paste(im.convert("RGB"), (6 + (k % 7) * (sw_ + 6), 6 + (k // 7) * (sh_ + 6)))
        out.save(os.path.join(HERE, "boxwall_zoom.jpg"), quality=90)
    elif mode == "video":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else T_END
        n = int(secs * FPS)
        outp = os.path.join(HERE, "boxwall.mp4")
        pr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", outp],
                              stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for b in pool.imap(job, range(n), chunksize=2): pr.stdin.write(b)
        pr.stdin.close(); pr.wait()
        print("wrote", outp)
