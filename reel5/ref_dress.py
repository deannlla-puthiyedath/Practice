"""Fashion sketch: woman in an all-over Reverie print spaghetti-strap princess dress.
figure(view='front'|'back', flare=1.0, spin=0.0) -> RGBA PIL image 800x1500 (with paper border)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2
FW, FH = 800, 1500
SKIN = (176, 120, 88); SKIN_SH = (150, 98, 70)
HAIR = (34, 24, 22); GOLD = (214, 172, 60); LIP = (170, 50, 50); OUT = (28, 22, 20)
PAINT = Image.open(os.path.join(HERE, "reverie.jpg")).convert("RGB")
# keep the print free of the small flag mat: paint it over with the verandah purple
ImageDraw.Draw(PAINT).rectangle((392, 640, 482, 735), fill=(84, 52, 150))
PAINT = PAINT.filter(ImageFilter.SMOOTH)

def _print_tile(w, h, shift=0.0, scale=300):
    """All-over print: the painting tiled with mirrored copies, sliding by `shift` (twirl)."""
    p = PAINT.resize((scale, int(PAINT.height * scale / PAINT.width)), Image.LANCZOS)
    pm = p.transpose(Image.FLIP_LEFT_RIGHT)
    tw, th = p.width * 2, p.height
    tile = Image.new("RGB", (tw, th)); tile.paste(p, (0, 0)); tile.paste(pm, (p.width, 0))
    out = Image.new("RGB", (w + tw, h + th))
    for y in range(0, h + th, th):
        off = (y // th % 2) * p.width // 2
        for x in range(-tw, w + tw, tw): out.paste(tile, (x + off, y))
    dx = int(shift * tw) % tw
    return out.crop((dx, 0, dx + w, h))

def linen(img, k=0.16, seed=7):
    """Rough linen weave: uneven warp/weft threads plus slubs, like the canvas of the painting."""
    w, h = img.size; r = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32) / 255
    rows = r.normal(0, 1, (h, 1)); cols = r.normal(0, 1, (1, w))
    slub = np.asarray(Image.fromarray((r.random((h // 6, w // 40)) * 255).astype(np.uint8))
                      .resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    weave = 0.5 * rows + 0.5 * cols + 1.4 * (slub - 0.5) * (r.random((h, 1)) > 0.7)
    fine = (np.indices((h, w)).sum(0) % 4 < 2) * 0.5 - 0.25
    a = a * (1 + k * np.tanh(weave)[..., None] + 0.06 * fine[..., None])
    g = a.mean(2, keepdims=True); a = g + (a - g) * 0.88 + 0.03       # slightly chalky, washed colour
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def dilate(m, r):
    """Fast dilation: blur then threshold (MaxFilter is far too slow at this size)."""
    return m.filter(ImageFilter.BoxBlur(r)).point(lambda v: 255 if v > 8 else 0)

def _m():
    return Image.new("L", (FW * S, FH * S), 0)

def _poly(pts):
    m = _m(); ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in pts], fill=255); return m

def _ell(cx, cy, rx, ry):
    m = _m(); ImageDraw.Draw(m).ellipse(((cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S), fill=255); return m

def _limb(pts, w0, w1):
    """Tapered limb along a polyline."""
    pts = np.array(pts, float); n = len(pts)
    left, right = [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        d = b - a; d /= np.linalg.norm(d) + 1e-6; nrm = np.array([-d[1], d[0]])
        w = w0 + (w1 - w0) * i / (n - 1)
        left.append(pts[i] + nrm * w / 2); right.append(pts[i] - nrm * w / 2)
    return _poly([tuple(p) for p in left + right[::-1]])

def _union(*ms):
    a = np.maximum.reduce([np.asarray(m) for m in ms]); return Image.fromarray(a)

class Canvas:
    def __init__(self):
        self.rgb = Image.new("RGB", (FW * S, FH * S), (255, 255, 255))
        self.alpha = _m()
    def fill(self, mask, col, outline=True, ow=3):
        src = col if isinstance(col, Image.Image) else Image.new("RGB", self.rgb.size, col)
        if outline:
            big = dilate(mask, ow * S)
            self.rgb.paste(Image.new("RGB", self.rgb.size, OUT), (0, 0), big)
            self.alpha = _union(self.alpha, big)
        self.rgb.paste(src, (0, 0), mask)
        self.alpha = _union(self.alpha, mask)
    def line(self, pts, col, w):
        d = ImageDraw.Draw(self.rgb); d.line([(x * S, y * S) for x, y in pts], fill=col, width=int(w * S), joint="curve")
        ImageDraw.Draw(self.alpha).line([(x * S, y * S) for x, y in pts], fill=255, width=int(w * S))

def _skirt(flare, spin, cx=400, top=470, hem=840):
    """Flowy A-line skirt; flare widens and the hem ripples as it twirls."""
    hw_top = 52; hw_hem = 165 * flare
    pts = [(cx - hw_top, top), (cx + hw_top, top)]
    # right side curve
    for k in np.linspace(0, 1, 12)[1:]:
        y = top + (hem - top) * k; w = hw_top + (hw_hem - hw_top) * k ** 1.25
        pts.append((cx + w, y))
    n = 60; lift = 30 * (flare - 1)
    for i in range(n + 1):                                  # rippling hem
        u = 1 - i / n; x = cx - hw_hem + 2 * hw_hem * u
        y = hem + 22 * np.sin(u * np.pi * (5 + 2 * flare) + spin * 6.28) - lift * np.cos((u - 0.5) * np.pi)
        pts.append((x, y))
    for k in np.linspace(1, 0, 12)[1:]:
        y = top + (hem - top) * k; w = hw_top + (hw_hem - hw_top) * k ** 1.25
        pts.append((cx - w, y))
    return _poly(pts)

def _folds(c, flare, spin, cx=400, top=470, hem=840):
    for j in range(-3, 4):
        x0 = cx + j * 14; x1 = cx + j * 46 * flare + 10 * np.sin(spin * 6.28 + j)
        c.line([(x0, top + 40), ((x0 + x1) / 2, (top + hem) / 2 + 30), (x1, hem - 10)], (70, 60, 50), 1.0)

def _foliage_tile(w, h, sw=190 * S):
    """Below the waist and the whole back: the painting's black and yellow leaves, tiled."""
    from PIL import ImageEnhance
    src = ImageEnhance.Contrast(ImageEnhance.Color(PAINT).enhance(1.5)).enhance(1.2)
    strip = src.crop((800, 0, PAINT.width, 900)).resize((sw, int(900 * sw / (PAINT.width - 800))), Image.LANCZOS)
    tile = Image.new("RGB", (sw * 2, strip.height)); tile.paste(strip, (0, 0))
    tile.paste(strip.transpose(Image.FLIP_LEFT_RIGHT), (sw, 0))
    out = Image.new("RGB", (w + sw * 2, h))
    for y in range(0, h, strip.height):
        for x in range(0, w + sw * 2, sw * 2): out.paste(tile, (x, y))
    return out

_HOUSE = None
def _house_print():
    """Bodice: the house, the colour blocks seen through the door."""
    global _HOUSE
    if _HOUSE is None:
        img = Image.new("RGB", (FW * S, FH * S), (20, 18, 16))
        h = PAINT.crop((330, 90, 700, 650)).resize((130 * S, 150 * S), Image.LANCZOS)
        img.paste(h, (335 * S, 335 * S))
        _HOUSE = linen(img)
    return _HOUSE

_BIG = None
def _linen_print(spin):
    """Linen-textured print, built once, then slid sideways for the twirl."""
    global _BIG
    if _BIG is None:
        _BIG = linen(_foliage_tile(FW * S * 2, FH * S))
    tw = 2 * 190 * S
    dx = int((spin % 1) * tw)
    return _BIG.crop((dx, 0, dx + FW * S, FH * S))

def figure(view="front", flare=1.0, spin=0.0):
    c = Canvas()
    pr = _linen_print(spin)
    back = view == "back"
    # legs and heels
    for side, x_hip, x_ank in [(-1, 380, 372), (1, 420, 440)]:
        c.fill(_limb([(x_hip, 760), (x_hip + side * 6, 960), (x_ank, 1300)], 62, 22), SKIN)
        c.fill(_poly([(x_ank - 11, 1290), (x_ank + 11, 1290), (x_ank + 20, 1330), (x_ank + 4, 1340), (x_ank - 9, 1318)]), SKIN, ow=2)  # foot
        c.line([(x_ank - 6, 1322), (x_ank + 18, 1334)], OUT, 4)                  # sole
        c.line([(x_ank + (-14 if back else 18), 1316), (x_ank + (-14 if back else 18), 1352)], OUT, 5)  # heel
        c.line([(x_ank - 14, 1292), (x_ank + 14, 1292)], GOLD, 4)                # ankle strap
    # arms
    c.fill(_limb([(338, 312), (322, 470), (300, 640)], 34, 22), SKIN)
    c.fill(_ell(298, 660, 16, 24), SKIN)
    if back:
        c.fill(_limb([(462, 312), (478, 470), (500, 640)], 34, 22), SKIN)
        c.fill(_ell(502, 660, 16, 24), SKIN)
    else:
        c.fill(_limb([(462, 312), (492, 440), (440, 520)], 34, 22), SKIN)       # hand on waist
        c.fill(_ell(438, 520, 18, 16), SKIN)
    # neck, shoulders, upper chest
    c.fill(_poly([(384, 225), (416, 225), (420, 290), (380, 290)]), SKIN, outline=False)
    c.fill(_union(_poly([(344, 300), (456, 300), (462, 330), (452, 380), (348, 380), (338, 330)]),
                  _ell(344, 318, 20, 22), _ell(456, 318, 20, 22)), SKIN)
    # dress: bodice + skirt, all-over print
    bod = _poly([(350, 358), (372, 350), (400, 364), (428, 350), (450, 358),
                 (446, 470), (354, 470)] if not back else [(348, 372), (452, 372), (446, 470), (354, 470)])
    sk = _skirt(flare, spin)
    c.fill(sk, pr)
    c.fill(bod, pr if back else _house_print())
    _folds(c, flare, spin)
    c.line([(354, 470), (446, 470)], OUT, 3)                                      # waist seam
    # spaghetti straps
    if back:
        c.line([(352, 374), (446, 300)], OUT, 3); c.line([(448, 374), (354, 300)], OUT, 3)   # crossed back
    else:
        c.line([(356, 356), (350, 298)], OUT, 3); c.line([(444, 356), (450, 298)], OUT, 3)
    # head and hair
    if back:
        c.fill(_ell(400, 168, 56, 70), HAIR)
        c.fill(_ell(400, 108, 42, 38), HAIR)
        c.line([(370, 102), (430, 102)], GOLD, 4)                                 # hair clip
    else:
        c.fill(_ell(400, 170, 52, 66), SKIN)
        c.fill(_poly([(344, 160), (352, 118), (400, 96), (448, 118), (456, 160), (430, 128), (370, 128)]), HAIR)
        c.fill(_ell(400, 96, 40, 34), HAIR)                                      # high bun
        for ex in (380, 420):                                                     # closed eyes, lashes
            c.line([(ex - 12, 172), (ex, 178), (ex + 12, 172)], OUT, 2.4)
            c.line([(ex - 13, 156), (ex + 12, 154)], HAIR, 3)
        c.line([(400, 182), (396, 200), (402, 202)], SKIN_SH, 2)
        c.fill(_ell(400, 214, 12, 6), LIP, outline=False)
        c.line([(388, 214), (412, 214)], (120, 30, 30), 1.5)
        for ex in (346, 454):                                                     # gold hoops
            m = _m(); ImageDraw.Draw(m).ellipse(((ex - 13) * S, 196 * S, (ex + 13) * S, 226 * S), outline=255, width=4 * S)
            c.rgb.paste(Image.new("RGB", c.rgb.size, GOLD), (0, 0), m); c.alpha = _union(c.alpha, m)
        c.line([(372, 292), (400, 318), (428, 292)], GOLD, 2.5)                    # fine necklace
        c.fill(_poly([(468, 560), (548, 552), (552, 604), (472, 612)]), GOLD)     # clutch
        c.line([(478, 572), (544, 566)], OUT, 2)
    c.line([(290, 628), (310, 628)], GOLD, 5)                                     # bracelet
    # shrink and add a paper border
    rgb = c.rgb.resize((FW, FH), Image.LANCZOS); a = c.alpha.resize((FW, FH), Image.LANCZOS)
    fig = rgb.convert("RGBA"); fig.putalpha(a)
    pad = Image.new("RGBA", (FW + 30, FH + 30), (0, 0, 0, 0))
    pad.paste(Image.new("RGBA", (FW, FH), (252, 250, 244, 255)), (15, 15), dilate(a, 8))
    pad.alpha_composite(fig, (15, 15))
    return pad.crop(pad.getbbox())

if __name__ == "__main__":
    ims = [figure("front"), figure("front", 1.6, 0.35), figure("back", 1.2, 0.7)]
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 80, max(i.height for i in ims) + 40), (246, 240, 228))
    x = 20
    for im in ims: sheet.paste(im, (x, 20), im); x += im.width + 20
    sheet.save(os.path.join(HERE, "dress_test.jpg"), quality=88)
