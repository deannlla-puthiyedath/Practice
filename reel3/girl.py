"""The campaign girl, matched to the Reverie reel: tall fashion-illustration figure, thin dark outlines,
white sticker edge, sweetheart top on thin straps, full skirt with a wavy hem and seam lines.
Only change for Reel 3: hair is a straight bob just above the shoulders, ends curving in a little.

Units: figure height = 975 (Reverie measurement), x centred on 0, y from the top of the hair.
"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SPRING = Image.open(os.path.join(A, "spring_tee.jpg")).convert("RGB")         # front top
SKIRT = Image.open(os.path.join(A, "sunset_water.jpg")).convert("RGB")         # whole skirt: blue boxes
PLAIN = Image.open(os.path.join(A, "sunset_plainblue.jpg")).convert("RGB")     # back top: plain blue

SKIN = (172, 116, 86)
SKIN_SH = (150, 98, 72)
HAIR = (30, 22, 19)
HAIR_HI = (64, 48, 42)
LINE = (40, 28, 24)
GOLD = (214, 168, 52)
LIP = (196, 44, 46)
STICKER = (244, 236, 220)


class Fig:
    def __init__(self, cx, top, s):
        self.cx, self.top, self.s = cx, top, s

    def p(self, x, y):
        return (self.cx + x * self.s, self.top + y * self.s)

    def pl(self, pts):
        return [self.p(x, y) for x, y in pts]

    def w(self, v):
        return max(1, int(round(v * self.s)))


def _tex(layer, tex, poly):
    xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
    x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
    w, h = x1 - x0, y1 - y0
    s = max(w / tex.width, h / tex.height)
    t = tex.resize((int(tex.width * s) + 1, int(tex.height * s) + 1), Image.LANCZOS)
    t = t.crop(((t.width - w) // 2, (t.height - h) // 2, (t.width - w) // 2 + w, (t.height - h) // 2 + h)).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(a - x0, b - y0) for a, b in poly], fill=255)
    layer.paste(t, (x0, y0), m)


def _limb(d, pts, w, col, f):
    d.line(pts, fill=LINE, width=w + f.w(3), joint="curve")
    for q in pts:
        r = (w + f.w(3)) / 2; d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=LINE)
    d.line(pts, fill=col, width=w, joint="curve")
    for q in pts:
        r = w / 2; d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)


def _wavy_hem(y, half, n=4, amp=9):
    xs = np.linspace(half, -half, 80)
    return [(x, y + amp * np.cos((x + half) / (2 * half) * n * 2 * np.pi) - 6 * (1 - (x / half) ** 2)) for x in xs]


def _skirt_poly():
    right = [(37, 290), (62, 330), (98, 392), (136, 462), (166, 520), (182, 556)]
    return [(-37, 290)] + right + _wavy_hem(566, 182) + [(-x, y) for x, y in right[::-1]]


def _bob(d, f, back=False):
    """Straight bob: dome on top, straight sides, ends just above the shoulders turning in."""
    def side(sx, back):
        pts = [(sx * 30, 2), (sx * 48, 14), (sx * 57, 36), (sx * 58, 70), (sx * 57, 108), (sx * 55, 126), (sx * 50, 138),
               (sx * 42, 145), (sx * 32, 146), (sx * 24, 141), (sx * 22, 135)]
        if back:
            pts = pts[:-4] + [(sx * 44, 146), (sx * 30, 151), (sx * 14, 153)]
        return pts
    out = [(0, -2)] + side(1, back) + side(-1, back)[::-1]
    d.polygon(f.pl(out), fill=HAIR, outline=LINE, width=f.w(2))


def _hair_front(d, f):
    # side part at x=-14; two sections sweep over the forehead to the temples
    d.polygon(f.pl([(-14, 0), (-30, 4), (-50, 18), (-58, 44), (-56, 70), (-48, 64), (-44, 42), (-32, 28), (-16, 22)]), fill=HAIR)
    d.polygon(f.pl([(-14, 0), (14, -1), (40, 8), (56, 30), (59, 60), (54, 74), (48, 66), (46, 46), (30, 30), (8, 24), (-16, 22)]), fill=HAIR)
    d.line(f.pl([(-14, 2), (-16, 22)]), fill=HAIR_HI, width=f.w(2))
    d.arc([*f.p(-50, 8), *f.p(-8, 50)], 200, 280, fill=HAIR_HI, width=f.w(3))
    d.arc([*f.p(8, 6), *f.p(54, 52)], 260, 330, fill=HAIR_HI, width=f.w(3))
    # the in-curl at the ends
    for sx in (-1, 1):
        d.arc([*f.p(sx * 40 - 9, 128), *f.p(sx * 40 + 9, 148)], 20 if sx > 0 else 100, 160 if sx > 0 else 250, fill=HAIR_HI, width=f.w(2))


def draw(layer, cx, top, height, view="front", eyes="closed", necklace=None, earrings=True):
    """Draw the girl onto RGBA `layer` (with sticker edge). necklace: None | 'gold' | 'diamond'."""
    f = Fig(cx, top, height / 975)
    fig = Image.new("RGBA", layer.size, (0, 0, 0, 0)); d = ImageDraw.Draw(fig)
    _bob(d, f, back=(view == "back"))
    # legs + heels
    for sx in (-1, 1):
        _limb(d, [f.p(sx * 20, 560), f.p(sx * 19, 760), f.p(sx * 17, 950)], f.w(20), SKIN if view == "front" else SKIN_SH, f)
        d.line(f.pl([(sx * 17 - 9, 952), (sx * 17 + 9, 952)]), fill=LINE, width=f.w(3))
        d.line(f.pl([(sx * 17 + 6, 950), (sx * 17 + 10, 968)]), fill=LINE, width=f.w(3))
        d.line(f.pl([(sx * 17 - 8, 942), (sx * 17 + 9, 940)]), fill=GOLD, width=f.w(2))
    # skirt (front and back are the same print)
    sk = f.pl(_skirt_poly())
    _tex(fig, SKIRT, sk)
    d = ImageDraw.Draw(fig)
    for x in (-150, -95, -45, 0, 45, 95, 150):  # panel seams
        d.line([f.p(x * 0.2, 292), f.p(x, 566 - 6 * abs(np.cos(x / 20)))], fill=(255, 255, 255, 70), width=f.w(1.5))
    d.polygon(sk, outline=LINE, width=f.w(2.5))
    # neck + shoulders (angular, like Reverie)
    d.polygon(f.pl([(-14, 112), (14, 112), (15, 160), (-15, 160)]), fill=SKIN, outline=LINE, width=f.w(2))
    torso = [(-15, 156), (-58, 166), (-66, 178), (-64, 196), (-46, 214), (-40, 292), (40, 292), (46, 214), (64, 196), (66, 178), (58, 166), (15, 156)]
    d.polygon(f.pl(torso), fill=SKIN, outline=LINE, width=f.w(2))
    d.line(f.pl([(-15, 158), (15, 158)]), fill=SKIN, width=f.w(3))
    if view == "front":
        top_poly = [(-40, 292), (40, 292), (44, 200), (32, 186), (16, 186), (0, 200), (-16, 186), (-32, 186), (-44, 200)]
        _tex(fig, SPRING, f.pl(top_poly))
        d = ImageDraw.Draw(fig)
        d.polygon(f.pl(top_poly), outline=LINE, width=f.w(2.5))
        for sx in (-1, 1):
            d.line(f.pl([(sx * 34, 188), (sx * 44, 164)]), fill=LINE, width=f.w(2.5))  # thin straps
        if necklace == "gold":
            d.line(f.pl([(-24, 160), (0, 182), (24, 160)]), fill=GOLD, width=f.w(2))
        elif necklace == "diamond":
            for i, t in enumerate(np.linspace(0.15, 0.85, 13)):
                a = np.pi * t; x, y = -28 * np.cos(a), 160 + 22 * np.sin(a)
                r = 3.4 if i % 2 else 2.6
                d.ellipse([*f.p(x - r, y - r), *f.p(x + r, y + r)], fill=(240, 246, 255), outline=(150, 175, 210))
            d.polygon(f.pl([(0, 183), (6, 192), (0, 203), (-6, 192)]), fill=(236, 246, 255), outline=(140, 170, 210))
            for (sx_, sy_, rr) in ((12, 180, 9), (-22, 168, 6)):
                d.line(f.pl([(sx_ - rr, sy_), (sx_ + rr, sy_)]), fill=(255, 255, 255), width=f.w(1.5))
                d.line(f.pl([(sx_, sy_ - rr), (sx_, sy_ + rr)]), fill=(255, 255, 255), width=f.w(1.5))
        # face
        face = [(-46, 36), (-47, 72), (-41, 96), (-25, 112), (0, 120), (25, 112), (41, 96), (47, 72), (46, 36), (28, 20), (0, 16), (-28, 20)]
        d.polygon(f.pl(face), fill=SKIN, outline=LINE, width=f.w(2))
        if eyes == "closed":
            for sx in (-1, 1):
                d.arc([*f.p(sx * 21 - 11, 62), *f.p(sx * 21 + 11, 76)], 20, 160, fill=LINE, width=f.w(2))
        else:
            for sx in (-1, 1):
                d.ellipse([*f.p(sx * 21 - 9, 64), *f.p(sx * 21 + 9, 74)], fill=(246, 240, 232), outline=LINE, width=f.w(1.5))
                d.ellipse([*f.p(sx * 21 - 4, 64), *f.p(sx * 21 + 4, 73)], fill=(40, 24, 20))
        for sx in (-1, 1):
            d.line(f.pl([(sx * 31, 56), (sx * 11, 53)]), fill=LINE, width=f.w(2))
        d.line(f.pl([(3, 74), (-1, 92)]), fill=SKIN_SH, width=f.w(2))
        d.ellipse([*f.p(-9, 99), *f.p(9, 107)], fill=LIP)
        d.line(f.pl([(-7, 103), (7, 103)]), fill=(140, 30, 30), width=f.w(1))
        _hair_front(d, f)
        if earrings:
            for sx in (-1, 1):
                d.ellipse([*f.p(sx * 54 - 10, 112), *f.p(sx * 54 + 10, 132)], outline=GOLD, width=f.w(2.5))
    else:  # back: plain blue top, crossed straps
        top_poly = [(-40, 292), (40, 292), (44, 226), (-44, 226)]
        _tex(fig, PLAIN, f.pl(top_poly))
        d = ImageDraw.Draw(fig)
        d.polygon(f.pl(top_poly), outline=LINE, width=f.w(2.5))
        d.line(f.pl([(-36, 228), (44, 166)]), fill=LINE, width=f.w(2.5))
        d.line(f.pl([(36, 228), (-44, 166)]), fill=LINE, width=f.w(2.5))
        d.line(f.pl([(-6, 154), (-8, 160)]), fill=SKIN_SH, width=f.w(1.5))
        d2 = ImageDraw.Draw(fig)
        for sx in (-1, 1):
            d2.arc([*f.p(sx * 30 - 22, 112), *f.p(sx * 30 + 22, 150)], 30 if sx > 0 else 90, 150 if sx > 0 else 160, fill=HAIR_HI, width=f.w(3))
        d2.line(f.pl([(0, 4), (0, 60)]), fill=HAIR_HI, width=f.w(2))
    # arms (in front of the skirt edge)
    for sx in (-1, 1):
        _limb(d, [f.p(sx * 60, 176), f.p(sx * 66, 300), f.p(sx * 70, 420)], f.w(17), SKIN, f)
        d.ellipse([*f.p(sx * 70 - 9, 414), *f.p(sx * 70 + 9, 440)], fill=SKIN, outline=LINE, width=f.w(1.5))
    # sticker edge, like Reverie
    a = fig.split()[3]
    edge = a.filter(ImageFilter.MaxFilter(f.w(10) | 1))
    st = Image.new("RGBA", layer.size, STICKER + (0,)); st.putalpha(edge)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); sh.putalpha(edge.filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.25))
    layer.alpha_composite(sh, (6, 8)); layer.alpha_composite(st); layer.alpha_composite(fig)
    return layer
