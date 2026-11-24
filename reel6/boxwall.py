"""Reel 6 box wall: the dress pattern opens into 35 boxes of the life she already has.
5 x 7 grid on 1080x1920. Each box = a real crop of Sunset (2) washed light, with a small cut-paper scene that keeps moving.
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
BW, BH = CW * SS, CH * SS
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
    im = crop_box(ci, ri).resize((BW, BH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    a = np.asarray(im).astype(np.float32)
    wash = np.array((WARM if warm else BLUE)["wash"], np.float32)
    a = a * 0.42 + wash * 0.58
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
    def P(self, ps, fill, w=4): self.d.polygon(self.pts(ps), fill=fill, outline=self.o if w else None, width=w)
    def R(self, x0, y0, x1, y1, fill, w=4, r=0):
        b = (self.X(x0), self.Y(y0), self.X(x1), self.Y(y1))
        if r: self.d.rounded_rectangle(b, radius=r * SS, fill=fill, outline=self.o if w else None, width=w)
        else: self.d.rectangle(b, fill=fill, outline=self.o if w else None, width=w)
    def E(self, cx, cy, rx, ry, fill, w=4):
        self.d.ellipse((self.X(cx - rx), self.Y(cy - ry), self.X(cx + rx), self.Y(cy + ry)), fill=fill,
                       outline=self.o if w else None, width=w)
    def O(self, cx, cy, r, fill, w=4):  # circle with radius in width units
        rr = r * BW
        self.d.ellipse((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), fill=fill,
                       outline=self.o if w else None, width=w)
    def L(self, ps, col=None, w=4): self.d.line(self.pts(ps), fill=col or self.o, width=w, joint="curve")
    def A(self, cx, cy, r, a0, a1, col=None, w=4):
        rr = r * BW
        self.d.arc((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), a0, a1, fill=col or self.o, width=w)
    def PIE(self, cx, cy, r, a0, a1, fill, w=4):
        rr = r * BW
        self.d.pieslice((self.X(cx) - rr, self.Y(cy) - rr, self.X(cx) + rr, self.Y(cy) + rr), a0, a1, fill=fill,
                        outline=self.o if w else None, width=w)

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
    for i in range(6):  # palms rushing past
        x = (1.2 - ((t * 0.55 + i * 0.27) % 1.6))
        c.L([(x, 0.62), (x + 0.02, 0.18)], p["rust"], 7)
        for a in (-1, 1):
            c.P([(x + 0.02, 0.18), (x + 0.02 + a * 0.16, 0.22), (x + 0.02 + a * 0.08, 0.16)], p["lime"])
    c.P([(0, 0), (1, 0), (1, 0.1), (0, 0.1)], p["org"]); c.P([(0, 0.62), (1, 0.62), (1, 1), (0, 1)], p["org"])
    c.R(0, 0.1, 0.05, 0.62, p["org"]); c.R(0.95, 0.1, 1, 0.62, p["org"])
    bob = wob(t, 2.2, 0.006)
    body(c, 0.3, 0.52 + bob, 0.26, 0.4, MUMKURTI); head(c, 0.3, 0.42 + bob, 0.085, "long")
    body(c, 0.7, 0.54 - bob, 0.24, 0.4, p["yel"]); head(c, 0.7, 0.44 - bob, 0.08, "bun", hoops=True)
    c.A(0.18, 0.74, 0.12, 200, 340, p["out"], 8)   # steering wheel

def v_dad_serve(c, t):
    p = c.p
    c.R(0, 0.72, 1, 1, p["rust"])
    c.E(0.42, 0.78, 0.3, 0.06, (236, 238, 240))  # steel plate
    pile = min(t / 3.0, 1)
    c.E(0.42, 0.77 - 0.02 * pile, 0.05 + 0.13 * pile, 0.015 + 0.035 * pile, (252, 250, 244))
    if t > 3.2: c.E(0.58, 0.77, 0.06, 0.025, p["org"])
    body(c, 0.72, 0.3, 0.4, 0.45, DADSHIRT); head(c, 0.72, 0.2, 0.1, "dad")
    lx, ly = 0.5, 0.52 + wob(t, 1.1, 0.02)
    c.L([(0.62, 0.42), (lx, ly)], SKIN, 12)
    c.L([(lx, ly), (lx - 0.06, ly + 0.05)], (200, 200, 205), 6); c.E(lx - 0.08, ly + 0.07, 0.05, 0.025, (220, 222, 226))
    if t < 3.0:
        for k in range(8):
            yy = ((t * 1.6 + k * 0.125) % 1) * 0.14 + ly + 0.09
            c.O(lx - 0.08 + 0.01 * math.sin(k * 3), yy, 0.008, (255, 255, 250), 0)
    for k in range(3):
        s = (t * 0.4 + k / 3) % 1
        c.L([(0.36 + k * 0.06 + wob(s, 1, 0.02), 0.7 - s * 0.25), (0.36 + k * 0.06 + wob(s, 1, 0.02, 2), 0.64 - s * 0.25)], p["cream"], 5)

def v_alarm_off(c, t):
    p = c.p
    br = wob(t, 0.35, 0.012)
    c.O(0.5, 0.44, 0.27, p["yel"]); c.O(0.5, 0.44, 0.21, p["cream"])
    for s in (-1, 1):  # muffled bells, tied with cloth
        c.O(0.5 + s * 0.2, 0.25, 0.09, p["deep"])
        c.L([(0.5 + s * 0.27, 0.2), (0.5 + s * 0.12, 0.3)], p["cream"], 9)
    c.A(0.42, 0.44, 0.04, 20, 160, w=4); c.A(0.58, 0.44, 0.04, 20, 160, w=4)  # sleeping eyes
    c.P([(0.08, 0.52 - br), (0.92, 0.52 - br), (0.98, 0.9), (0.02, 0.9)], p["org"])  # blanket breathing
    for k in range(4): c.L([(0.1 + k * 0.22, 0.56 - br), (0.06 + k * 0.24, 0.88)], p["deep"], 3)
    for k in range(3):  # sleep bubbles drifting up, no letters
        s = (t * 0.3 + k / 3) % 1
        c.O(0.72 + 0.1 * s, 0.32 - 0.3 * s, 0.02 + 0.03 * s, p["wash"], 3)

def v_house(c, t):
    p = c.p
    c.R(0.12, 0.42, 0.88, 0.95, p["cream"])
    c.P([(0.02, 0.44), (0.98, 0.44), (0.78, 0.18), (0.22, 0.18)], p["rust"])
    for k in range(5): c.L([(0.1 + k * 0.2, 0.43), (0.25 + k * 0.125, 0.2)], p["deep"], 3)
    c.R(0.36, 0.55, 0.64, 0.95, (255, 214, 120))  # warm light inside
    op = ease((t - 0.8) / 2.5) * 0.12
    c.R(0.36, 0.55, 0.5 - op, 0.95, p["deep"]); c.R(0.5 + op, 0.55, 0.64, 0.95, p["deep"])
    for x in (0.4 - op * 0.3, 0.55 + op * 0.7): c.O(x + 0.02, 0.75, 0.012, GOLDC, 0)
    c.R(0.18, 0.55, 0.28, 0.75, p["rust"]); c.R(0.72, 0.55, 0.82, 0.75, p["rust"])

def v_room(c, t):
    p = c.p
    c.R(0.55, 0.08, 0.92, 0.45, (255, 236, 170))
    c.L([(0.735, 0.08), (0.735, 0.45)], p["out"], 4); c.L([(0.55, 0.265), (0.92, 0.265)], p["out"], 4)
    sw = wob(t, 0.4, 0.03)
    c.P([(0.5, 0.06), (0.6 + sw, 0.06), (0.56 + sw * 1.5, 0.5), (0.5, 0.5)], p["org"])
    beam = 0.15 + 0.25 * ease(t / 6)
    c.d.polygon(c.pts([(0.55, 0.45), (0.92, 0.45), (0.6 + beam, 0.78), (0.2 + beam, 0.78)]), fill=(255, 240, 160, 150))
    c.R(0.06, 0.62, 0.94, 0.86, p["yel"]); c.R(0.06, 0.56, 0.18, 0.92, p["rust"]); c.R(0.86, 0.66, 0.94, 0.92, p["rust"])
    c.E(0.3, 0.6, 0.12, 0.04, p["cream"]); c.P([(0.42, 0.62), (0.86, 0.62), (0.86, 0.72), (0.42, 0.72)], p["org"])

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
    sw = wob(t, 0.5, 0.015)
    c.P([(0.12, 1.0), (0.2, 0.74), (0.8, 0.74), (0.88, 1.0)], p["yel"])          # shoulders, from behind
    c.R(0.42, 0.6, 0.58, 0.78, SKIN, 3)                                           # neck
    c.O(0.5, 0.46, 0.25, HAIR, 0)                                                 # back of head
    c.O(0.5 + sw, 0.2, 0.13, HAIR, 0)                                             # bun
    for k in range(12):                                                           # jasmine ring round the bun
        a = 2 * math.pi * k / 12 + t * 0.15
        c.O(0.5 + sw + 0.15 * math.cos(a), 0.2 + 0.1 * math.sin(a), 0.028, (255, 255, 252), 2)
    for k in range(6):                                                            # string falling to the shoulder
        c.O(0.66 + sw * 2 + 0.01 * k, 0.3 + k * 0.07, 0.024, (255, 255, 252), 2)
    for k in range(3):
        s_ = (t * 0.25 + k / 3) % 1
        c.O(0.15 + k * 0.32 + wob(s_, 1, 0.05), 0.05 + s_ * 0.6, 0.013, (255, 255, 252), 2)

def v_mango(c, t):
    p = c.p
    c.L([(0, 0.18), (1, 0.12)], p["rust"], 10)
    for i in range(6): c.E(0.08 + i * 0.17, 0.2 + 0.03 * (i % 2), 0.08, 0.03, (150, 186, 70), 3)
    c.P([(0.25, 0.7), (0.75, 0.7), (0.7, 0.95), (0.3, 0.95)], (214, 170, 100))
    for k in range(3): c.L([(0.27 + k * 0.01, 0.76 + k * 0.06), (0.73 - k * 0.01, 0.76 + k * 0.06)], p["rust"], 2)
    for i, t0 in enumerate((0.8, 3.0)):
        x = 0.42 + i * 0.16
        y = 0.3 if t < t0 else fall(t, t0, 0.3, 0.68 - i * 0.02, 0.6)
        col = tuple(int(a + (b - a) * min(t / max(t0, 0.1), 1)) for a, b in zip((170, 196, 80), p["yel"]))
        c.E(x, y, 0.06, 0.04, col, 3)

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
    m = m.filter(ImageFilter.GaussianBlur(10))
    g = 1.0 + 0.08 * math.sin(t * 2)
    glow = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for k in range(6):
        r = BW * (0.3 + 0.06 * k) * g
        gd.ellipse((BW / 2 - r, BH / 2 - r, BW / 2 + r, BH / 2 + r), fill=(255, 214, 90, 26))
    c.img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
    c.img.paste(sun, (int(BW / 2 - sun.width / 2), int(BH / 2 - sun.height / 2)), m)

# ================================================================== BLUE boxes
def v_tender_coconut(c, t):
    p = c.p
    c.O(0.5, 0.56, 0.32, (170, 196, 80))
    c.P([(0.36, 0.3), (0.64, 0.3), (0.58, 0.22), (0.42, 0.22)], (220, 226, 130))
    c.O(0.5, 0.26, 0.07, p["white"], 3)
    c.L([(0.52, 0.26), (0.68, -0.02)], p["white"], 10); c.L([(0.52, 0.26), (0.68, -0.02)], p["mid"], 3)
    for k in range(4):
        s = (t * 0.6 + k / 4) % 1
        c.O(0.6 + 0.02 * k, 0.2 - s * 0.18, 0.012, p["white"], 2)
    c.L([(0.25, 0.92), (0.75, 0.92)], p["deep"], 6)

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

def v_well(c, t):
    p = c.p
    c.R(0.15, 0.62, 0.85, 0.96, p["pale"]); c.E(0.5, 0.62, 0.35, 0.05, p["navy"])
    for k in range(3): c.L([(0.15, 0.7 + k * 0.08), (0.85, 0.7 + k * 0.08)], p["sky"], 2)
    c.L([(0.18, 0.62), (0.18, 0.12)], p["out"], 8); c.L([(0.82, 0.62), (0.82, 0.12)], p["out"], 8); c.L([(0.14, 0.12), (0.86, 0.12)], p["out"], 8)
    c.O(0.5, 0.16, 0.05, p["mid"])
    y = 0.36 + 0.22 * (0.5 + 0.5 * math.cos(t * 1.1))
    c.L([(0.5, 0.2), (0.5, y)], p["out"], 3)
    c.P([(0.43, y), (0.57, y), (0.55, y + 0.1), (0.45, y + 0.1)], p["mid"])
    if y < 0.45:
        for k in range(3): c.O(0.45 + k * 0.05, y + 0.12 + ((t * 2 + k * 0.3) % 1) * 0.15, 0.012, p["sky"], 0)

def v_lotus(c, t):
    p = c.p
    for k in range(4):
        s = (t * 0.35 + k / 4) % 1
        c.d.ellipse(
            (c.X(0.5 - 0.08 - 0.45 * s), c.Y(0.66 - 0.03 - 0.12 * s), c.X(0.5 + 0.08 + 0.45 * s), c.Y(0.66 + 0.03 + 0.12 * s)),
            outline=p["white"], width=3)
    c.E(0.25, 0.8, 0.14, 0.04, p["mid"]); c.E(0.78, 0.5, 0.12, 0.035, p["mid"])
    op = ease(t / 4)
    for j in range(5):
        a = math.pi * (0.15 + 0.7 * j / 4)
        spread = 0.05 + 0.09 * op
        cx, cy = 0.5 + spread * math.cos(a) * -1, 0.6 - 0.12 * math.sin(a) * (0.6 + 0.4 * op)
        c.P([(0.5, 0.64), (cx - 0.04, cy + 0.02), (cx, cy - 0.06), (cx + 0.04, cy + 0.02)], p["white"], 3)
    c.O(0.5, 0.6, 0.03, (244, 222, 100), 2)

def v_swing(c, t):
    p = c.p
    c.L([(0.05, 0.06), (0.95, 0.06)], p["out"], 10)
    a = 0.35 * math.sin(t * 1.5)
    px, py, L = 0.5, 0.06, 0.58
    sx, sy = px + L * math.sin(a) * BH / BW, py + L * math.cos(a)
    for o in (-0.12, 0.12):
        c.L([(px + o, py), (sx + o, sy)], p["out"], 3)
    c.R(sx - 0.2, sy, sx + 0.2, sy + 0.04, p["mid"])
    body(c, sx, sy - 0.2, 0.18, 0.2, (244, 214, 90)); head(c, sx, sy - 0.25, 0.07, "bun")
    c.R(sx - 0.07, sy - 0.12, sx + 0.07, sy - 0.07, p["white"], 3)

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

def v_bus(c, t):
    p = c.p
    for i in range(5):
        x = 1.1 - ((t * 0.7 + i * 0.3) % 1.5)
        c.L([(x, 0.7), (x + 0.02, 0.25)], p["navy"], 6)
        for a in (-1, 1): c.P([(x + 0.02, 0.25), (x + 0.02 + a * 0.14, 0.3), (x + 0.02 + a * 0.06, 0.22)], p["deep"], 2)
    c.R(0, 0.7, 1, 1, p["sky"], 0)
    c.R(0, 0, 1, 0.12, p["deep"]); c.R(0, 0.62, 1, 1, p["deep"]); c.R(0, 0, 0.06, 1, p["deep"]); c.R(0.94, 0, 1, 1, p["deep"])
    c.L([(0.06, 0.6), (0.94, 0.6)], p["white"], 8)
    c.L([(0.06, 0.58), (0.45, 0.58)], SKIN, 16); c.E(0.47, 0.58, 0.05, 0.022, SKIN)
    c.L([(0.3, 0.6), (0.3, 0.62)], GOLDC, 6)
    w = wob(t, 1.8, 0.03)
    c.L([(0.7, 0.9), (0.76 + w, 0.75), (0.8 - w, 0.7)], HAIR, 10)

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

def v_street_art(c, t):
    p = c.p
    c.R(0.02, 0.1, 0.98, 0.9, p["pale"])
    for i in range(6): c.L([(0.02, 0.1 + i * 0.13), (0.98, 0.1 + i * 0.13)], p["sky"], 2)
    k = ease(t / 4.5)
    mural = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); md = C(mural, c.p)
    md.E(0.5, 0.5, 0.3, 0.16, p["deep"]); md.P([(0.78, 0.5), (0.95, 0.36), (0.95, 0.64)], p["deep"])
    md.O(0.32, 0.46, 0.03, p["white"]); md.O(0.32, 0.46, 0.012, p["navy"], 0)
    for j in range(4): md.A(0.5 + j * 0.06, 0.5, 0.06, 300, 60, p["white"], 3)
    md.O(0.2, 0.25, 0.05, (244, 214, 90))
    m = Image.new("L", (BW, BH), 0); ImageDraw.Draw(m).rectangle((0, 0, int(BW * k), BH), fill=255)
    c.img.paste(mural, (0, 0), Image.composite(mural.split()[3], Image.new("L", (BW, BH), 0), m))
    x = k
    c.L([(x, 0.45), (x + 0.08, 0.7)], p["out"], 8)

def v_cycle(c, t):
    p = c.p
    for i in range(3):
        x0 = 0.02 + i * 0.33
        c.R(x0, 0.3, x0 + 0.3, 0.75, (p["white"], p["pale"], p["sky"])[i])
        c.P([(x0, 0.3), (x0 + 0.3, 0.3), (x0 + 0.24, 0.2), (x0 + 0.2, 0.2), (x0 + 0.15, 0.1), (x0 + 0.1, 0.2), (x0 + 0.06, 0.2)], (p["deep"], p["mid"], p["deep"])[i])
        c.R(x0 + 0.1, 0.5, x0 + 0.2, 0.75, p["navy"]); c.R(x0 + 0.04, 0.36, x0 + 0.11, 0.44, p["navy"], 2); c.R(x0 + 0.19, 0.36, x0 + 0.26, 0.44, p["navy"], 2)
    c.R(0, 0.75, 1, 1, p["pale"], 0)
    x = -0.3 + ((t * 0.22) % 1.6)
    for wx in (x, x + 0.22):
        c.O(wx, 0.86, 0.075, p["wash"], 4)
        a = t * 8
        c.L([(wx - 0.06 * math.cos(a), 0.86 - 0.05 * math.sin(a)), (wx + 0.06 * math.cos(a), 0.86 + 0.05 * math.sin(a))], p["out"], 2)
    c.L([(x, 0.86), (x + 0.1, 0.76), (x + 0.22, 0.86)], p["out"], 4)
    body(c, x + 0.1, 0.58, 0.14, 0.18, (244, 214, 90)); head(c, x + 0.11, 0.53, 0.055, "bun")

def v_canoe(c, t):
    p = c.p
    c.R(0, 0.5, 1, 1, p["sky"], 0)
    for x in (0.1, 0.85):
        c.L([(x, 0.5), (x + 0.06, 0.12)], p["navy"], 6); c.L([(x, 0.52), (x + 0.06, 0.88)], p["mid"], 6)
        for a in (-1, 1): c.P([(x + 0.06, 0.12), (x + 0.06 + a * 0.16, 0.18), (x + 0.06 + a * 0.07, 0.1)], p["deep"], 2)
    x = -0.3 + ((t * 0.13) % 1.6)
    c.P([(x, 0.6), (x + 0.4, 0.6), (x + 0.34, 0.66), (x + 0.06, 0.66)], p["navy"])
    body(c, x + 0.26, 0.42, 0.1, 0.18, p["white"]); head(c, x + 0.26, 0.38, 0.045, "short")
    c.L([(x + 0.36, 0.3), (x + 0.2, 0.72)], p["out"], 4)
    for k in range(3): c.A(x - 0.05 - k * 0.08, 0.66, 0.04, 200, 340, p["white"], 2)

def v_fishing_net(c, t):
    p = c.p
    c.O(0.75, 0.42, 0.09, (244, 160, 70))
    c.R(0, 0.5, 1, 1, p["mid"], 0)
    for k in range(4): c.A(0.2 + k * 0.22, 0.6 + (k % 2) * 0.12, 0.05, 200, 340, p["white"], 3)
    a = 0.22 + 0.18 * math.sin(t * 0.8)
    pivot = (0.25, 0.52)
    tip = (pivot[0] + 0.62 * math.cos(-a), pivot[1] + 0.62 * math.sin(-a) * BW / BH * -1 + 0.0)
    tipy = 0.52 - 0.35 * math.sin(a)
    tx = 0.25 + 0.55 * math.cos(a)
    c.L([(0.25, 0.52), (tx, tipy)], p["out"], 6)
    c.L([(0.25, 0.52), (0.05, 0.3)], p["out"], 5)
    for o in (-0.12, 0.12): c.L([(tx, tipy), (tx + o, tipy + 0.2 + 0.25 * (0.4 - a))], p["out"], 2)
    ny = tipy + 0.2 + 0.25 * (0.4 - a)
    c.A(tx, ny, 0.12, 0, 180, p["white"], 3)
    c.R(0.05, 0.52, 0.32, 0.6, p["navy"])

def v_school(c, t):
    p = c.p
    c.R(0, 0.82, 1, 1, p["pale"], 0)
    c.R(0.08, 0.36, 0.92, 0.82, p["white"]); c.P([(0.02, 0.38), (0.98, 0.38), (0.5, 0.14)], p["deep"])
    for i in range(5): c.R(0.13 + i * 0.16, 0.48, 0.23 + i * 0.16, 0.6, p["sky"], 2)
    c.R(0.42, 0.64, 0.58, 0.82, p["navy"])
    ring = abs(math.sin(t * 3)) * 15
    c.O(0.5, 0.26, 0.04, (244, 214, 90)); c.L([(0.5, 0.22), (0.5 + ring / 400, 0.3)], p["out"], 3)
    for k in range(3):
        x = 1.1 - ((t * 0.15 + k * 0.18) % 0.75)
        body(c, x, 0.78, 0.06, 0.08, p["mid"]); head(c, x, 0.76, 0.025, "short", smile=False)
        c.R(x + 0.02, 0.79, x + 0.05, 0.83, (244, 214, 90), 2)

def v_friends(c, t):
    p = c.p
    c.R(0, 0, 1, 0.5, p["pale"], 0); c.R(0, 0.5, 1, 0.66, p["mid"], 0)
    c.R(0, 0.66, 1, 1, p["navy"])
    for i, (x, hair) in enumerate(((0.35, "bun"), (0.65, "long"))):
        bob = abs(math.sin(t * 3 + i)) * 0.015 if (t % 2.5) < 1.2 else 0
        body(c, x, 0.48 - bob, 0.18, 0.2, ((244, 214, 90), p["white"])[i]); head(c, x, 0.43 - bob, 0.06, hair)
        sw = wob(t, 0.9, 0.04, i)
        c.L([(x - 0.04, 0.68), (x - 0.05 + sw, 0.86)], SKIN, 8); c.L([(x + 0.04, 0.68), (x + 0.05 - sw, 0.86)], SKIN, 8)

def v_backyard(c, t):
    p = c.p
    c.R(0, 0.78, 1, 1, p["deep"])
    for k in range(4): c.L([(0.05 + k * 0.25, 0.8), (0.2 + k * 0.25, 0.98)], p["navy"], 3)
    g = ease(t / 3.5)
    c.L([(0.14, 0.8), (0.14, 0.2)], p["white"], 10)  # banana plant
    for a in (-1, 1): c.P([(0.14, 0.25), (0.14 + a * 0.18, 0.1 + wob(t, 0.5, 0.02)), (0.14 + a * 0.2, 0.2), (0.14, 0.32)], p["pale"], 3)
    for k, x in enumerate((0.42, 0.62, 0.84)):  # rows of veg, growing
        h = 0.08 + 0.18 * g
        c.L([(x, 0.8), (x, 0.8 - h)], p["white"], 4)
        for j in range(3):
            y = 0.8 - h * (0.3 + j * 0.3)
            c.E(x + 0.04 * (1 if j % 2 else -1), y, 0.04, 0.015, p["pale"], 2)
        if g > 0.6:
            col = ((176, 70, 50), (170, 196, 80), (244, 214, 90))[k]
            c.E(x + 0.03, 0.8 - h * 0.5, 0.018 + 0.02 * (g - 0.6), 0.03, col, 2)
    c.P([(0.6, 0.1), (0.78, 0.1), (0.82, 0.24), (0.58, 0.24)], p["mid"])  # watering can
    c.L([(0.82, 0.16), (0.92, 0.08)], p["out"], 5)
    for k in range(4):
        s = (t * 1.5 + k / 4) % 1
        c.O(0.92 - s * 0.05, 0.1 + s * 0.5, 0.01, p["white"], 0)

def v_herbs(c, t):
    p = c.p
    c.R(0.3, 0.62, 0.7, 0.95, p["white"]); c.R(0.26, 0.57, 0.74, 0.64, p["pale"])     # tulsi thara
    c.R(0.42, 0.72, 0.58, 0.84, p["pale"], 2)
    c.L([(0.5, 0.58), (0.5, 0.3)], p["deep"], 5)
    for i in range(26):                                                            # bushy tulsi
        a = i * 2.4; rr = 0.04 + 0.16 * ((i * 37) % 26) / 26
        x = 0.5 + rr * math.cos(a) + wob(t, 0.5, 0.008, i); y = 0.36 + rr * 0.9 * math.sin(a) * BW / BH
        c.E(x, y, 0.035, 0.018, (p["mid"], p["sky"], p["deep"])[i % 3], 2)
    for x in (0.1, 0.9):                                                           # aloe
        for k in range(4): c.P([(x - 0.03, 0.95), (x + 0.03, 0.95), (x + (k - 1.5) * 0.06, 0.62 + (k % 2) * 0.05)], p["mid"], 2)
    s_ = (t * 0.25) % 1
    c.E(0.78 - s_ * 0.2, 0.2 + s_ * 0.7, 0.025, 0.012, p["sky"], 2)

def v_stars(c, t):
    p = c.p
    c.R(0, 0, 1, 1, p["navy"], 0)
    for k in range(12):
        tw = 0.5 + 0.5 * math.sin(t * 3 + k * 1.7)
        c.O((k * 0.37) % 1, (k * 0.23) % 0.4, 0.006 + 0.006 * tw, p["white"], 0)
    c.R(0.05, 0.58, 0.45, 1, p["deep"]); c.P([(0.0, 0.6), (0.5, 0.6), (0.25, 0.44)], p["mid"])
    c.R(0.55, 0.64, 0.95, 1, p["deep"]); c.P([(0.5, 0.66), (1.0, 0.66), (0.75, 0.5)], p["mid"])
    for cx, cy in ((0.25, 0.3), (0.75, 0.36)):
        sw = wob(t, 0.6, 8, cx * 5)
        c.L([(cx, 0.44 if cx < 0.5 else 0.5), (cx, cy)], p["white"], 2)
        R = 0.09; pts = []
        for i in range(10):
            a = math.radians(-90 + sw + i * 36); r = R if i % 2 == 0 else R * 0.45
            pts.append((cx + r * math.cos(a), cy + 0.05 + r * math.sin(a) * BW / BH))
        c.P(pts, (248, 224, 110), 3)

def v_neighbours(c, t):
    p = c.p
    c.R(0.44, 0.45, 0.56, 1, p["pale"])
    for k in range(5): c.L([(0.44, 0.45 + k * 0.11), (0.56, 0.45 + k * 0.11)], p["sky"], 2)
    body(c, 0.2, 0.55, 0.22, 0.45, (244, 214, 90)); head(c, 0.2, 0.5, 0.07, "bun")
    body(c, 0.8, 0.55, 0.24, 0.45, p["white"]); head(c, 0.8, 0.5, 0.07, "short")
    k = 0.5 - 0.5 * math.cos(t * 1.2)
    x = 0.28 + 0.44 * k; y = 0.5 - 0.22 * math.sin(math.pi * k)
    c.R(x - 0.05, y - 0.08, x + 0.05, y + 0.06, (230, 232, 236)); c.L([(x - 0.05, y - 0.03), (x + 0.05, y - 0.03)], p["out"], 2)
    c.A(x, y - 0.08, 0.04, 180, 360, p["out"], 3)
    c.L([(0.27, 0.6), (x - 0.04, y + 0.04)], SKIN, 8) if k < 0.55 else c.L([(0.73, 0.6), (x + 0.04, y + 0.04)], SKIN, 8)

# ------------------------------------------------------------------ layout
WARM_LIST = [v_mum_drive, v_dad_serve, v_alarm_off, v_house, v_room, v_easel, v_sadya, v_fritters, v_chai,
             v_coconut_oil, v_jasmine, v_mango, v_pookalam, v_chenda, v_kathakali, v_three_faiths, v_sun]
BLUE_LIST = [v_tender_coconut, v_herbal_water, v_well, v_lotus, v_swing, v_ferry, v_bus, v_hospital, v_street_art,
             v_cycle, v_canoe, v_fishing_net, v_school, v_friends, v_backyard, v_herbs, v_stars, v_neighbours]
SUN_CELL = (0, 4)

def layout():
    warm_cells = [(c, r) for r in range(ROWS) for c in range(2)] + [(2, r) for r in range(3)]
    blue_cells = [(2, r) for r in range(3, ROWS)] + [(c, r) for r in range(ROWS) for c in (3, 4)]
    warm_cells.remove(SUN_CELL)
    out = {SUN_CELL: (v_sun, True)}
    order_w = [v for v in WARM_LIST if v is not v_sun]
    for cell, v in zip(warm_cells, order_w): out[cell] = (v, True)
    for cell, v in zip(blue_cells, BLUE_LIST): out[cell] = (v, False)
    return out

LAYOUT = layout()
BGS = {}

def cell_img(cell, t):
    v, warm = LAYOUT[cell]
    key = cell
    if key not in BGS: BGS[key] = bg_for(warm, hash(cell) % 997 + 3)
    img = BGS[key].copy()
    c = C(img, WARM if warm else BLUE)
    v(c, t + (cell[0] * 0.37 + cell[1] * 0.21) % 0.8)
    return img.resize((CW, CH), Image.LANCZOS)

WEAVE = None
def linen_overlay():
    r = np.random.default_rng(11)
    rows = r.normal(0, 1, (H, 1)); cols = r.normal(0, 1, (1, W))
    fine = (np.indices((H, W)).sum(0) % 4 < 2) * 0.5 - 0.25
    return (1 + 0.05 * np.tanh(0.5 * rows + 0.5 * cols) + 0.012 * fine)[..., None].astype(np.float32)

def frame(t):
    global WEAVE
    if WEAVE is None: WEAVE = linen_overlay()
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    rng = np.random.default_rng(5)
    for (ci, ri) in LAYOUT:
        x = GAP + ci * (CW + GAP); y = GAP + ri * (CH + GAP)
        dx = 3 * math.sin(t * 0.5 + ci + ri * 2); dy = 3 * math.cos(t * 0.4 + ri + ci)  # boxes drift slowly
        base.alpha_composite(cell_img((ci, ri), t), (int(x + dx), int(y + dy)))
    z = 1.0 + 0.035 * (t / 6)                       # slow push in
    if z > 1.0:
        zw, zh = int(W / z), int(H / z)
        base = base.crop(((W - zw) // 2, (H - zh) // 2, (W - zw) // 2 + zw, (H - zh) // 2 + zh)).resize((W, H), Image.LANCZOS)
    a = np.asarray(base.convert("RGB")).astype(np.float32) * WEAVE
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "still"
    if mode == "still":
        frame(float(sys.argv[2]) if len(sys.argv) > 2 else 2.0).save(os.path.join(HERE, "boxwall_still.jpg"), quality=92)
    elif mode == "zoom":
        t = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
        cells = sorted(LAYOUT); sheet = Image.new("RGB", (7 * BW // 2 + 8 * 6, 5 * BH // 2 + 6 * 6), PAPER)
        for k, cell in enumerate(cells):
            v, warm = LAYOUT[cell]
            if cell not in BGS: BGS[cell] = bg_for(warm, hash(cell) % 997 + 3)
            im = BGS[cell].copy(); v(C(im, WARM if warm else BLUE), t)
            im = im.resize((BW // 2, BH // 2), Image.LANCZOS)
            sheet.paste(im.convert("RGB"), (6 + (k % 7) * (BW // 2 + 6), 6 + (k // 7) * (BH // 2 + 6)))
        sheet.save(os.path.join(HERE, "boxwall_zoom.jpg"), quality=90)
    elif mode == "video":
        secs = float(sys.argv[2]) if len(sys.argv) > 2 else 6
        n = int(secs * FPS)
        out = os.path.join(HERE, "boxwall.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                             stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for b in pool.imap(job, range(n), chunksize=4): p.stdin.write(b)
        p.stdin.close(); p.wait()
        print("wrote", out)
