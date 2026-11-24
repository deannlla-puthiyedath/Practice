"""Reel 3 storyboard: low-res frames for every beat. `python3 board.py` -> board/*.jpg + contact sheet.

Story: she sits cross-legged in a black long coat with orange fur, wind in her bob, snowy peaks behind her.
The camera pulls back: the peaks are a white cloth heaped on a low table, the rocks are thread spools,
the alpine flowers are pin heads, the wind is a table fan. She takes the coat off (the dress is underneath),
plays, finishes the coat, sells it at a boutique, and admires a diamond necklace in a mirror.
"""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REEL2 = os.path.join(HERE, "..", "reel2")
sys.path.insert(0, REEL2)
_cwd = os.getcwd(); os.chdir(REEL2)
import lib as r2  # cut-letter text + logo sticker from Reel 2 (keeps the series consistent)
os.chdir(_cwd)

A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "board"); os.makedirs(OUT, exist_ok=True)
FW, FH = 1080, 1920          # frame size before the low-res export
LOW = (540, 960)             # storyboard export size

# ---------------- textures ----------------
SPRING = Image.open(os.path.join(A, "spring_banner.jpg")).convert("RGB")
SPRING_T = Image.open(os.path.join(A, "spring_tee.jpg")).convert("RGB")
BOXES = Image.open(os.path.join(A, "blue_boxes.jpg")).convert("RGB")
WATER = Image.open(os.path.join(A, "blue_water.jpg")).convert("RGB")


def janaki_standin(w=640, h=420, seed=3):
    """STAND-IN for Colours of Janaki (the real file isn't here yet): a simple sky with a sun, wrinkled paper."""
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None]
    top, mid, bot = np.array([96, 150, 206]), np.array([214, 214, 210]), np.array([242, 178, 132])
    k1 = np.clip(y / 0.6, 0, 1); k2 = np.clip((y - 0.6) / 0.4, 0, 1)
    sky = (top * (1 - k1) + mid * k1) * (1 - k2) + bot * k2
    img = np.repeat(sky[:, None, :], w, 1).reshape(h, w, 3).astype(np.float32)
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    d = np.hypot(xx - w * 0.62, yy - h * 0.58)
    sun = np.clip(1 - (d - 62) / 6, 0, 1)[..., None]
    halo = np.clip(1 - d / 170, 0, 1)[..., None] ** 2
    img = img * (1 - halo * 0.35) + np.array([252, 214, 120]) * halo * 0.35
    img = img * (1 - sun) + np.array([244, 150, 46]) * sun
    wr = Image.fromarray((rng.random((h // 18, w // 18)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    wr = np.asarray(wr.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    img = img * (1 - 0.35 * wr[..., None])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


import girl as G2  # the campaign girl, matched to Reverie
JANAKI = G2.JANAKI      # Colours of Janaki: coat lining
SUNBELT = G2.SUNBELT    # its sun: the belt

# ---------------- palette ----------------
SKIN, SKIN_D = (150, 98, 70), (124, 78, 54)
HAIR = (24, 20, 22)
BLACK = (22, 20, 24)
FUR, FUR_L = (232, 122, 40), (250, 168, 82)
LIP = (178, 82, 92)


# ---------------- drawing helpers ----------------
def tex_fill(img, tex, poly, rot=0):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    t = tex.rotate(rot, expand=True) if rot else tex
    s = max(w / t.width, h / t.height)
    t = t.resize((max(1, int(t.width * s) + 1), max(1, int(t.height * s) + 1)), Image.LANCZOS)
    t = t.crop(((t.width - w) // 2, (t.height - h) // 2, (t.width - w) // 2 + w, (t.height - h) // 2 + h))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(px - x0, py - y0) for px, py in poly], fill=255)
    img.paste(t, (x0, y0), m)


def shade(img, poly, col, a):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon(poly, fill=col + (int(255 * a),))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"))


def limb(d, pts, w, col):
    d.line(pts, fill=col, width=int(w), joint="curve")
    for p in pts:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)


def fur_chain(d, pts, r, seed=0):
    rng = np.random.default_rng(seed)
    pts = np.array(pts, float)
    seg = np.concatenate([np.linspace(pts[i], pts[i + 1], 8, endpoint=False) for i in range(len(pts) - 1)] + [pts[-1:]])
    for p in seg:
        rr = r * rng.uniform(0.8, 1.15); j = rng.normal(0, r * 0.15, 2)
        d.ellipse([p[0] + j[0] - rr, p[1] + j[1] - rr, p[0] + j[0] + rr, p[1] + j[1] + rr], fill=FUR)
    for p in seg[::2]:
        rr = r * 0.45
        d.ellipse([p[0] - rr * 0.6, p[1] - rr * 1.1, p[0] + rr * 0.9, p[1] + rr * 0.2], fill=FUR_L)


def arc_pts(cx, cy, rx, ry, a0, a1, n=24):
    t = np.linspace(np.deg2rad(a0), np.deg2rad(a1), n)
    return [(cx + rx * np.cos(v), cy + ry * np.sin(v)) for v in t]


# ---------------- the girl ----------------
class G:
    def __init__(self, cx, by, s):
        self.cx, self.by, self.s = cx, by, s

    def P(self, x, y):
        return (self.cx + x * self.s, self.by + y * self.s)

    def poly(self, pts):
        return [self.P(x, y) for x, y in pts]


def head(img, g, yo, eyes="closed", wind=0.0, back=False):
    """yo: y of the chin line. Bob: straight, above the shoulders, ends curving in."""
    d = ImageDraw.Draw(img); s = g.s
    hy = yo  # chin
    wx = wind * 26
    # back hair (bob)
    back_hair = [(-104 + wx * 0.3, hy - 120), (-98, hy - 190), (-60, hy - 222), (0, hy - 232), (60, hy - 222), (98, hy - 190),
                 (106 + wx * 0.3, hy - 120), (108 + wx, hy - 40), (100 + wx * 1.4, hy + 18), (74 + wx * 1.2, hy + 30), (58 + wx, hy + 12),
                 (-58 + wx, hy + 12), (-74 + wx * 1.2, hy + 30), (-100 + wx * 1.4, hy + 18), (-108 + wx, hy - 40)]
    d.polygon(g.poly(back_hair), fill=HAIR)
    if back:
        # nape shading only: viewer sees the back of the head
        d.line(g.poly([(-60 + wx, hy + 10), (0, hy - 10), (60 + wx, hy + 10)]), fill=(48, 40, 44), width=max(1, int(3 * s)))
        for k in (-40, 0, 40):
            d.line(g.poly([(k * 0.6, hy - 210), (k + wx, hy + 5)]), fill=(46, 40, 44), width=max(1, int(3 * s)))
        return
    # face
    d.ellipse([*g.P(-74, hy - 205), *g.P(74, hy)], fill=SKIN)
    d.ellipse([*g.P(-52, hy - 70), *g.P(-26, hy - 54)], fill=(176, 104, 84))
    d.ellipse([*g.P(26, hy - 70), *g.P(52, hy - 54)], fill=(176, 104, 84))
    ey = hy - 98
    for sx in (-1, 1):
        ex = sx * 32
        if eyes == "closed":
            d.arc([*g.P(ex - 18, ey - 12), *g.P(ex + 18, ey + 10)], 15, 165, fill=(40, 26, 24), width=max(1, int(4 * s)))
            for k in (-10, 0, 10):
                d.line([g.P(ex + k, ey + 9), g.P(ex + k * 1.3, ey + 17)], fill=(40, 26, 24), width=max(1, int(2 * s)))
        else:
            d.ellipse([*g.P(ex - 16, ey - 9), *g.P(ex + 16, ey + 9)], fill=(246, 240, 232))
            d.ellipse([*g.P(ex - 8, ey - 9), *g.P(ex + 8, ey + 8)], fill=(46, 28, 22))
            d.ellipse([*g.P(ex - 1, ey - 6), *g.P(ex + 4, ey - 1)], fill=(255, 255, 255))
            d.arc([*g.P(ex - 18, ey - 12), *g.P(ex + 18, ey + 12)], 190, 350, fill=(30, 20, 20), width=max(1, int(4 * s)))
        d.line([g.P(ex - 18, ey - 28), g.P(ex + 16, ey - 31)], fill=(36, 26, 24), width=max(1, int(5 * s)))
    d.line([g.P(2, hy - 86), g.P(-6, hy - 54), g.P(6, hy - 50)], fill=SKIN_D, width=max(1, int(3 * s)))
    d.ellipse([*g.P(-20, hy - 34), *g.P(20, hy - 18)], fill=LIP)
    # front hair: side part, locks framing the face, ends curling in
    d.polygon(g.poly([(-84, hy - 120), (-80, hy - 180), (-40, hy - 222), (20, hy - 228), (70, hy - 200), (86, hy - 140),
                      (70, hy - 168), (30, hy - 188), (-20, hy - 176), (-60, hy - 150)]), fill=HAIR)
    d.polygon(g.poly([(-84, hy - 150), (-64, hy - 110), (-68, hy - 30), (-62 + wx, hy + 8), (-86 + wx, hy + 20), (-104 + wx, hy - 30), (-102, hy - 120)]), fill=HAIR)
    d.polygon(g.poly([(84, hy - 150), (66, hy - 110), (70, hy - 30), (62 + wx, hy + 8), (86 + wx, hy + 20), (104 + wx, hy - 30), (102, hy - 120)]), fill=HAIR)
    if abs(wind) > 0:
        for k, yy in enumerate((hy - 60, hy - 10, hy + 15)):
            d.line(g.poly([(sx_ * 100, yy) for sx_ in ()]) or [g.P(np.sign(wind) * 100, yy), g.P(np.sign(wind) * (140 + 30 * k), yy - 10 + 8 * k), g.P(np.sign(wind) * (175 + 30 * k), yy + 4)],
                   fill=HAIR, width=max(1, int(5 * s)), joint="curve")


def seated(img, g, coat="on", eyes="closed", hands="knees", wind=0.0, necklace=False):
    d = ImageDraw.Draw(img)
    # coat back (behind everything)
    if coat == "on":
        d.polygon(g.poly([(-165, -612), (165, -612), (270, -300), (395, -34), (-395, -34), (-270, -300)]), fill=BLACK)
    elif coat == "slip":
        d.polygon(g.poly([(-200, -470), (200, -470), (300, -260), (420, -30), (-420, -30), (-300, -260)]), fill=BLACK)
        tex_fill(img, JANAKI, g.poly([(-190, -470), (-120, -430), (-150, -60), (-390, -40), (-290, -280)]))
        tex_fill(img, JANAKI, g.poly([(190, -470), (120, -430), (150, -60), (390, -40), (290, -280)]))
    # shins crossed (visible under the hem)
    limb(d, [g.P(-250, -52), g.P(160, -18)], 58 * g.s, SKIN)
    limb(d, [g.P(250, -52), g.P(-160, -18)], 58 * g.s, SKIN_D)
    d.ellipse([*g.P(150, -44), *g.P(205, 0)], fill=(120, 40, 60))
    d.ellipse([*g.P(-205, -44), *g.P(-150, 0)], fill=(120, 40, 60))
    # skirt: blue boxes from the Sunset painting's water
    hem = arc_pts(0, -70, 345, 40, 0, 180, 20)
    tex_fill(img, BOXES, g.poly([(-105, -332), (105, -332), (262, -182), (345, -70)] + [(x, y) for x, y in hem] + [(-262, -182)]))
    shade(img, g.poly([(-105, -332), (105, -332), (60, -250), (-60, -250)]), (20, 30, 70), 0.18)
    # shoulders / chest skin
    d.polygon(g.poly([(-160, -560), (-158, -606), (-120, -632), (-38, -646), (38, -646), (120, -632), (158, -606), (160, -560), (112, -420), (-112, -420)]), fill=SKIN)
    d.rectangle([*g.P(-30, -720), *g.P(30, -630)], fill=SKIN)
    d.polygon(g.poly([(-30, -660), (30, -660), (0, -636)]), fill=SKIN_D)
    # bodice / corset: Spring in the Himalayas
    tex_fill(img, SPRING_T, g.poly([(-100, -332), (100, -332), (114, -560), (62, -588), (0, -566), (-62, -588), (-114, -560)]))
    for x in (-50, 0, 50):  # corset seams
        d.line([g.P(x, -340), g.P(x * 1.1, -570 + abs(x) * 0.2)], fill=(150, 30, 40), width=max(1, int(3 * g.s)))
    if necklace:
        draw_necklace(img, g, -640)
    head(img, g, -700, eyes=eyes, wind=wind)
    # arms
    if hands == "knees":
        L = [g.P(-150, -592), g.P(-212, -420), g.P(-280, -150)]; R = [g.P(150, -592), g.P(212, -420), g.P(280, -150)]
    elif hands == "crayon":
        L = [g.P(-150, -592), g.P(-200, -420), g.P(-120, -150)]; R = [g.P(150, -592), g.P(205, -400), g.P(70, -170)]
    else:  # stitch
        L = [g.P(-150, -592), g.P(-205, -410), g.P(-70, -250)]; R = [g.P(150, -592), g.P(205, -410), g.P(60, -270)]
    if coat == "on":
        limb(d, L, 86 * g.s, BLACK); limb(d, R, 86 * g.s, BLACK)
    elif coat == "slip":
        limb(d, L[:2], 46 * g.s, SKIN); limb(d, R[:2], 46 * g.s, SKIN)
        limb(d, L[1:], 86 * g.s, BLACK); limb(d, R[1:], 86 * g.s, BLACK)
    else:
        limb(d, L, 46 * g.s, SKIN); limb(d, R, 46 * g.s, SKIN)
    for H_ in (L[-1], R[-1]):
        d.ellipse([H_[0] - 30 * g.s, H_[1] - 26 * g.s, H_[0] + 30 * g.s, H_[1] + 30 * g.s], fill=SKIN)
    if coat in ("on", "slip"):
        fur_chain(d, [L[-1], (L[-1][0] + 1, L[-1][1] - 1)], 26 * g.s, 5)
        fur_chain(d, [R[-1], (R[-1][0] + 1, R[-1][1] - 1)], 26 * g.s, 6)
        # put hands back on top of the cuffs
        for H_ in (L[-1], R[-1]):
            d.ellipse([H_[0] - 26 * g.s, H_[1] + 6 * g.s, H_[0] + 26 * g.s, H_[1] + 44 * g.s], fill=SKIN)
    if coat == "on":
        # front panels, closed below the belt, a V at the chest that shows the corset
        lp = [(-162, -602), (-46, -642), (-18, -440), (-8, -332), (-10, -36), (-392, -34), (-280, -300)]
        d.polygon(g.poly(lp), fill=BLACK); d.polygon(g.poly([(-x, y) for x, y in lp]), fill=BLACK)
        tex_fill(img, JANAKI, g.poly([(-8, -300), (-8, -36), (-110, -36)]))  # lining flash at the hem
        fur_chain(d, g.poly([(-150, -600), (-60, -650), (-30, -520), (-14, -440)]), 30 * g.s, 1)
        fur_chain(d, g.poly([(150, -600), (60, -650), (30, -520), (14, -440)]), 30 * g.s, 2)
        tex_fill(img, SUNBELT, g.poly([(-262, -372), (262, -372), (268, -318), (-268, -318)]))  # sun belt
        d.ellipse([*g.P(-30, -372), *g.P(30, -312)], fill=(236, 146, 46))
        limb(d, [g.P(-12, -320), g.P(-34, -230)], 20 * g.s, (236, 146, 46)); limb(d, [g.P(12, -320), g.P(40, -236)], 20 * g.s, (236, 146, 46))
    elif coat == "slip":
        fur_chain(d, g.poly([(-210, -470), (-170, -400), (-150, -300)]), 28 * g.s, 3)
        fur_chain(d, g.poly([(210, -470), (170, -400), (150, -300)]), 28 * g.s, 4)


def draw_necklace(img, g, y0):
    d = ImageDraw.Draw(img)
    pts = arc_pts(0, y0 - 18, 72, 52, 15, 165, 22)
    for i, (x, y) in enumerate(pts):
        r = 7.5 if i % 2 else 6
        d.ellipse([*g.P(x - r, y - r), *g.P(x + r, y + r)], fill=(236, 242, 252), outline=(150, 170, 200))
    px, py = 0, y0 + 46
    d.polygon(g.poly([(px, py - 14), (px + 13, py + 4), (px, py + 26), (px - 13, py + 4)]), fill=(232, 244, 255), outline=(140, 170, 210))
    for (sx, sy, rr) in ((px + 18, py - 14, 22), (-46, y0 + 14, 14), (52, y0 + 6, 12)):
        d.line([g.P(sx - rr, sy), g.P(sx + rr, sy)], fill=(255, 255, 255), width=max(1, int(3 * g.s)))
        d.line([g.P(sx, sy - rr), g.P(sx, sy + rr)], fill=(255, 255, 255), width=max(1, int(3 * g.s)))


def standing(img, g, view="front", arm="necklace", necklace=True, eyes="open"):
    d = ImageDraw.Draw(img)
    for sx in (-1, 1):  # legs + flats
        limb(d, [g.P(sx * 48, -650), g.P(sx * 46, -330), g.P(sx * 52, -40)], 60 * g.s, SKIN if sx < 0 else SKIN_D if view == "back" else SKIN)
        d.ellipse([*g.P(sx * 52 - 38, -46), *g.P(sx * 52 + 38, 6)], fill=(120, 40, 60))
    hem = arc_pts(0, -640, 312, 46, 0, 180, 22)
    tex_fill(img, BOXES, g.poly([(-96, -1000), (96, -1000), (230, -820), (312, -640)] + hem + [(-230, -820)]))
    d.polygon(g.poly([(-160, -1250), (-158, -1300), (-120, -1326), (-38, -1340), (38, -1340), (120, -1326), (158, -1300), (160, -1250), (110, -1100), (-110, -1100)]), fill=SKIN)
    d.rectangle([*g.P(-30, -1412), *g.P(30, -1322)], fill=SKIN)
    top = [(-96, -1000), (96, -1000), (112, -1250), (62, -1278), (0, -1256), (-62, -1278), (-112, -1250)]
    if view == "front":
        tex_fill(img, SPRING_T, g.poly(top))
        for x in (-50, 0, 50):
            d.line([g.P(x, -1008), g.P(x * 1.1, -1262 + abs(x) * 0.2)], fill=(150, 30, 40), width=max(1, int(3 * g.s)))
        if necklace:
            draw_necklace(img, g, -1332)
        head(img, g, -1392, eyes=eyes)
    else:  # back: plain blue water, no boxes
        tex_fill(img, WATER, g.poly([(-96, -1000), (96, -1000), (114, -1262), (-114, -1262)]))
        head(img, g, -1392, back=True)
    L = [g.P(-152, -1290), g.P(-188, -1040), g.P(-200, -800)]
    R = [g.P(152, -1290), g.P(208, -1080), g.P(58, -1236)] if arm == "necklace" else [g.P(152, -1290), g.P(188, -1040), g.P(200, -800)]
    limb(d, L, 46 * g.s, SKIN); limb(d, R, 46 * g.s, SKIN)
    for H_ in (L[-1], R[-1]):
        d.ellipse([H_[0] - 28 * g.s, H_[1] - 24 * g.s, H_[0] + 28 * g.s, H_[1] + 28 * g.s], fill=SKIN)


# ---------------- the room (one world; the close-up of it reads as the Himalayas) ----------------
WW, WH = 2160, 3840
GIRL = (1080, 3330, 1.0)   # cx, floor contact, scale in world px


def room(state="meditate"):
    rng = np.random.default_rng(11)
    y = np.linspace(0, 1, WH)[:, None, None]
    wall = np.array([168, 200, 232]) * (1 - y) + np.array([226, 236, 244]) * y
    img = Image.fromarray(np.broadcast_to(wall, (WH, WW, 3)).astype(np.uint8).copy())
    d = ImageDraw.Draw(img)
    # floor
    d.rectangle([0, 2990, WW, WH], fill=(176, 128, 88))
    for k in range(10):
        d.line([0, 3000 + k * 92, WW, 3000 + k * 92], fill=(150, 106, 72), width=4)
    # window with curtain (left)
    d.rectangle([110, 900, 520, 1820], fill=(236, 240, 236)); d.rectangle([140, 930, 490, 1790], fill=(206, 228, 214))
    d.line([315, 930, 315, 1790], fill=(236, 240, 236), width=18); d.line([140, 1360, 490, 1360], fill=(236, 240, 236), width=18)
    d.polygon([(90, 860), (240, 860), (200, 1880), (70, 1880)], fill=(232, 200, 150))
    # side desk + sewing machine (left)
    d.rectangle([60, 2580, 500, 2620], fill=(120, 84, 56)); d.rectangle([80, 2620, 110, 2990], fill=(110, 76, 50)); d.rectangle([450, 2620, 480, 2990], fill=(110, 76, 50))
    d.rounded_rectangle([130, 2380, 440, 2580], 26, fill=(236, 232, 224)); d.rounded_rectangle([130, 2380, 230, 2580], 20, fill=(210, 206, 200))
    d.rectangle([220, 2440, 440, 2470], fill=(236, 232, 224)); d.line([330, 2470, 330, 2540], fill=(120, 120, 128), width=8)
    # grey felt rug: reads as stony ground up close
    d.polygon([(300, 2930), (1860, 2930), (2050, 3760), (110, 3760)], fill=(150, 150, 156))
    tex = Image.fromarray((rng.random((60, 60)) * 255).astype(np.uint8)).resize((1960, 840), Image.BICUBIC)
    shade_m = Image.new("L", img.size, 0); shade_m.paste(tex.point(lambda v: v * 0.25), (110, 2930))
    m2 = Image.new("L", img.size, 0); ImageDraw.Draw(m2).polygon([(300, 2930), (1860, 2930), (2050, 3760), (110, 3760)], fill=255)
    from PIL import ImageChops
    img.paste((110, 110, 118), (0, 0), ImageChops.multiply(shade_m, m2))
    # low table (one leg peeks out) with a white cloth heaped and draped: the mountains
    d.rectangle([1632, 2560, 1666, 2950], fill=(120, 84, 56))
    base = 2560
    peaks = [(520, base), (560, 2380), (660, 2240), (760, 2330), (880, 2060), (990, 1990), (1090, 2120), (1190, 2010),
             (1300, 1960), (1410, 2140), (1500, 2230), (1580, 2360), (1640, base)]
    d.polygon(peaks, fill=(244, 246, 250))
    faces = [[(660, 2240), (760, 2330), (700, base)], [(990, 1990), (1090, 2120), (1030, base)], [(1300, 1960), (1410, 2140), (1350, base)],
             [(880, 2060), (990, 1990), (930, base), (840, base)], [(1500, 2230), (1580, 2360), (1560, base)]]
    for f in faces:
        shade(img, f, (120, 140, 176), 0.32)
    d = ImageDraw.Draw(img)
    for x0 in (600, 820, 1000, 1180, 1330, 1480):  # cloth creases
        d.line([(x0, base - 40), (x0 + 30, base - 220)], fill=(214, 220, 232), width=6)
    drape = [(500, base - 10), (1660, base - 10), (1690, 2950), (470, 2950)]
    d.polygon(drape, fill=(238, 240, 246))
    for (xa, xb, xc) in ((560, 700, 640), (820, 980, 860), (1120, 1250, 1180), (1400, 1560, 1500)):  # soft snow-slope folds
        shade(img, [(xa, base), (xb, base), (xc, 2950), (xc - 90, 2950)], (150, 165, 195), 0.14)
    d = ImageDraw.Draw(img)
    shade(img, [(470, 2900), (1690, 2900), (1690, 2950), (470, 2950)], (90, 100, 120), 0.25)
    d = ImageDraw.Draw(img)
    # table fan (right), blowing left
    d.rectangle([1960, 2700, 2000, 2990], fill=(80, 80, 88)); d.ellipse([1900, 2960, 2060, 3010], fill=(80, 80, 88))
    d.ellipse([1820, 2380, 2140, 2700], outline=(90, 90, 98), width=10, fill=(226, 230, 236))
    for a in range(0, 360, 120):
        t = np.deg2rad(a)
        d.ellipse([1980 + 90 * np.cos(t) - 60, 2540 + 90 * np.sin(t) - 40, 1980 + 90 * np.cos(t) + 60, 2540 + 90 * np.sin(t) + 40], fill=(170, 200, 226))
    for k in range(10):
        d.line([1820, 2420 + k * 28, 2140, 2420 + k * 28], fill=(150, 150, 160), width=3)
    d.ellipse([1955, 2515, 2005, 2565], fill=(90, 90, 98))
    # blue crayon box drawn on the rug around her ("Draw a box. Step in.")
    if state in ("meditate", "coatoff", "crayon", "stitch"):
        box = [(560, 3150), (1600, 3150), (1700, 3700), (460, 3700)]
        for j in range(4):
            jj = rng.normal(0, 5, (5, 2))
            d.line([tuple(np.array(p) + jj[i]) for i, p in enumerate(box + box[:1])], fill=(36, 84, 196), width=9, joint="curve")
    # papers with crayon sketches when she plays
    if state in ("crayon", "stitch"):
        for (px, py, rot) in ((620, 3480, -8), (1380, 3520, 10), (1500, 3300, -4)):
            sheet = Image.new("RGBA", (260, 200), (252, 250, 244, 255)); sd = ImageDraw.Draw(sheet)
            sd.polygon([(70, 30), (190, 30), (220, 180), (40, 180)], outline=(20, 20, 24), width=5)  # coat sketch
            sd.ellipse([105, 90, 155, 140], outline=(236, 140, 40), width=8)  # sun belt
            sd.line([(70, 30), (130, 110), (190, 30)], fill=(232, 122, 40), width=7)
            sheet = sheet.rotate(rot, expand=True)
            img.paste(sheet, (px - sheet.width // 2, py - sheet.height // 2), sheet)
        d = ImageDraw.Draw(img)
        for k, c in enumerate([(220, 40, 60), (36, 84, 196), (240, 170, 30), (40, 150, 80)]):
            d.rounded_rectangle([760 + k * 40, 3600, 784 + k * 40, 3690], 8, fill=c)
    # the girl (seated, cross-legged)
    GH, GT = 2040, 2420
    lay = img.convert("RGBA")
    if state == "meditate":
        G2.draw(lay, 1080, GT, GH, pose="seat", arms="knees", coat="on", eyes="closed", wind=-1.0)
    elif state == "coatoff":
        G2.draw(lay, 1080, GT, GH, pose="seat", arms="knees", coat="slip", eyes="open", wind=-0.5)
    elif state == "crayon":
        f = G2.draw(lay, 1080, GT, GH, pose="seat", arms="crayon", eyes="open")
        d = ImageDraw.Draw(lay); h = f.p(40, 396)
        d.rounded_rectangle([h[0] - 8, h[1] - 60, h[0] + 12, h[1] + 10], 6, fill=(36, 84, 196))
        # the coat lies folded beside her, lining up
        d.polygon([(1480, 3380), (1800, 3400), (1840, 3580), (1460, 3580)], fill=BLACK)
        fur_chain(ImageDraw.Draw(lay), [(1480, 3380), (1800, 3400)], 22, 9)
        G2._tex_stretch(lay, JANAKI, [(1450, 3470), (1850, 3476), (1852, 3506), (1448, 3500)])
    elif state == "stitch":
        f = G2.draw(lay, 1080, GT, GH, pose="seat", arms="stitch", eyes="open")
        d = ImageDraw.Draw(lay)
        lap = f.pl([(-150, 312), (150, 312), (196, 404), (-196, 404)])
        d.polygon(lap, fill=BLACK, outline=G2.LINE, width=3)
        G2._tex_stretch(lay, JANAKI, f.pl([(-180, 360), (180, 360), (184, 378), (-184, 378)]))
        fur_chain(ImageDraw.Draw(lay), f.pl([(-150, 312), (150, 312)]), 22, 7)
        d = ImageDraw.Draw(lay)
        for hx, hy in ((-32, 336), (30, 330)):
            q = f.p(hx, hy); d.ellipse([q[0] - 19, q[1] - 19, q[0] + 19, q[1] + 31], fill=G2.SKIN, outline=G2.LINE, width=3)
        n0 = f.p(30, 326)
        d.line([n0, (n0[0] + 160, n0[1] - 300), (n0[0] + 220, n0[1] - 360)], fill=(232, 122, 40), width=4)
        d.line([n0, (n0[0] + 14, n0[1] - 60)], fill=(200, 205, 215), width=6)
    img = lay.convert("RGB")
    # cotton fluff in the fan's wind: snow up close
    if state in ("meditate", "coatoff"):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        for _ in range(240):
            x, yv, r = rng.uniform(300, 1900), rng.uniform(1700, 3400), rng.uniform(4, 13)
            ld.ellipse([x - r, yv - r * 0.8, x + r, yv + r * 0.8], fill=(255, 255, 255, int(rng.uniform(140, 230))))
        lay = lay.filter(ImageFilter.GaussianBlur(1.5))
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    # spools (rocks up close) and pin-head "flowers" in front of her
    d = ImageDraw.Draw(img)
    for (x, yv, s, c) in ((640, 3560, 1.0, (120, 120, 126)), (760, 3640, 0.8, (140, 136, 130)), (1420, 3580, 1.1, (112, 112, 120)),
                          (1580, 3520, 0.8, (132, 128, 124)), (1300, 3680, 0.7, (126, 126, 132))):
        w, h = 90 * s, 110 * s
        d.rounded_rectangle([x - w, yv - h, x + w, yv + h], int(40 * s), fill=c)
        for k in range(6):
            d.line([x - w + 6, yv - h + 30 * s + k * 26 * s, x + w - 6, yv - h + 34 * s + k * 26 * s], fill=tuple(v - 22 for v in c), width=4)
        d.ellipse([x - w - 8, yv - h - 26 * s, x + w + 8, yv - h + 20 * s], fill=(170, 130, 90))
    for (cx, cy) in ((540, 3420), (1640, 3400), (1200, 3620)):
        d.ellipse([cx - 80, cy - 40, cx + 80, cy + 50], fill=(70, 126, 70))
        for k in range(9):
            a = rng.uniform(np.pi * 1.1, np.pi * 1.9); L = rng.uniform(50, 110)
            ex, ey = cx + np.cos(a) * L * 0.8, cy + np.sin(a) * L
            d.line([cx + rng.normal(0, 30), cy, ex, ey], fill=(190, 196, 204), width=4)
            col = [(240, 120, 160), (250, 220, 90), (255, 255, 255), (200, 120, 230)][k % 4]
            d.ellipse([ex - 15, ey - 15, ex + 15, ey + 15], fill=col)
    return img


def tilt_shift(fr, top=0.16, bot=0.74, r=10):
    bl = fr.filter(ImageFilter.GaussianBlur(r))
    y = np.linspace(0, 1, fr.height)
    m = np.clip((top - y) / top, 0, 1) + np.clip((y - bot) / (1 - bot), 0, 1)
    mask = Image.fromarray((np.clip(m, 0, 1)[:, None] * np.ones((1, fr.width)) * 255).astype(np.uint8))
    return Image.composite(bl, fr, mask)


def crop_frame(world, cx, cy, w):
    h = w * FH / FW
    cx = min(max(cx, w / 2), world.width - w / 2); cy = min(max(cy, h / 2), world.height - h / 2)
    return world.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((FW, FH), Image.LANCZOS)


# ---------------- boutique + mirror ----------------
def boutique():
    img = Image.new("RGB", (FW, FH), (238, 224, 210)); d = ImageDraw.Draw(img)
    d.rectangle([0, 1500, FW, FH], fill=(150, 104, 70))
    d.rectangle([60, 220, 1020, 236], fill=(170, 130, 60))  # rail
    for k, c in enumerate([(206, 160, 170), (120, 150, 190), (230, 200, 120), (90, 110, 90)]):
        x = 140 + k * 120
        d.line([x, 236, x, 270], fill=(80, 80, 80), width=4)
        d.polygon([(x - 50, 270), (x + 50, 270), (x + 60, 560), (x - 60, 560)], fill=c)
    # dress form wearing the wrap coat, closed: fur collar + the Janaki tie are the details
    mx, my = 760, 520
    d.line([mx, my + 900, mx, my + 1040], fill=(60, 50, 40), width=14); d.ellipse([mx - 90, my + 1020, mx + 90, my + 1060], fill=(60, 50, 40))
    d.ellipse([mx - 40, my - 60, mx + 40, my + 10], fill=(214, 200, 180))
    for sx in (-1, 1):  # sleeves hanging straight
        d.polygon([(mx + sx * 128, my + 40), (mx + sx * 170, my + 70), (mx + sx * 178, my + 610), (mx + sx * 122, my + 610)], fill=BLACK, outline=G2.LINE)
        fur_chain(d, [(mx + sx * 128, my + 612), (mx + sx * 176, my + 612)], 22, 5 + sx)
    body = [(mx - 132, my + 40), (mx + 132, my + 40), (mx + 118, my + 200), (mx + 104, my + 330), (mx + 124, my + 520), (mx + 140, my + 880),
            (mx - 140, my + 880), (mx - 124, my + 520), (mx - 104, my + 330), (mx - 118, my + 200)]
    d.polygon(body, fill=BLACK, outline=G2.LINE, width=3)
    d.polygon([(mx - 40, my + 30), (mx + 40, my + 30), (mx, my + 200)], fill=(214, 200, 180))
    d.line([(mx + 14, my + 360), (mx + 40, my + 620), (mx + 60, my + 880)], fill=(70, 66, 74), width=3)
    for sx in (-1, 1):
        fur_chain(d, [(mx + sx * 128, my + 40), (mx + sx * 46, my + 34), (mx + sx * 20, my + 180), (mx - sx * 6, my + 320)], 24, 1 + sx)
    G2._tex_stretch(img, JANAKI, [(mx - 110, my + 318), (mx + 110, my + 318), (mx + 112, my + 362), (mx - 112, my + 362)])
    for end in ([(mx - 40, my + 350), (mx - 14, my + 350), (mx - 34, my + 520), (mx - 62, my + 514)],
                [(mx - 20, my + 352), (mx + 4, my + 354), (mx + 18, my + 540), (mx - 8, my + 544)]):
        G2._tex_stretch(img, JANAKI.rotate(90, expand=True), end)
    d = ImageDraw.Draw(img)
    d.rectangle([mx - 112, my + 318, mx + 112, my + 362], outline=G2.LINE, width=2)
    d.ellipse([mx - 46, my + 322, mx - 6, my + 360], outline=G2.LINE, width=2)
    tag = r2.ransom("SOLD", (173, 51, 97), size=62, seed=41, max_w=400)
    img.paste(tag, (mx - tag.width // 2, my + 940), tag)
    d.line([mx, my + 900, mx, my + 950], fill=(120, 90, 60), width=3)
    lay = img.convert("RGBA"); G2.draw(lay, 300, 610, 1150, view="front", eyes="open"); return lay.convert("RGB")


def mirror():
    img = Image.new("RGB", (FW, FH), (200, 222, 240)); d = ImageDraw.Draw(img)
    d.rectangle([0, 1560, FW, FH], fill=(176, 128, 88))
    # standing oval mirror (right) with her front reflection
    m = [540, 260, 1010, 1620]
    d.ellipse([m[0] - 22, m[1] - 22, m[2] + 22, m[3] + 22], fill=(170, 130, 60))
    refl = Image.new("RGB", (FW, FH), (214, 230, 242)); rd = ImageDraw.Draw(refl)
    rd.rectangle([0, 1500, FW, FH], fill=(166, 122, 86))
    rl = refl.convert("RGBA"); G2.draw(rl, 775, 400, 1290, arms="down", necklace="diamond", eyes="open"); refl = rl.convert("RGB")
    mk = Image.new("L", (FW, FH), 0); ImageDraw.Draw(mk).ellipse(m, fill=255)
    img.paste(refl, (0, 0), mk)
    shade(img, [(560, 300), (680, 300), (600, 1500), (560, 1400)], (255, 255, 255), 0.12)
    d = ImageDraw.Draw(img)
    d.line([620, 1640, 560, 1800], fill=(150, 110, 50), width=14); d.line([930, 1640, 990, 1800], fill=(150, 110, 50), width=14)
    # her, seen from behind, mid-turn: the back top is the plain blue water
    lay = img.convert("RGBA"); G2.draw(lay, 300, 480, 1400, view="back", arms="down"); return lay.convert("RGB")


def jeweller():
    """She pays with the coat money; the jeweller hands over the diamond necklace."""
    img = Image.new("RGB", (FW, FH), (60, 46, 58)); d = ImageDraw.Draw(img)
    for k in range(5):  # warm shop lights
        d.ellipse([90 + k * 220, 160, 150 + k * 220, 220], fill=(250, 214, 150))
    d.rectangle([0, 300, FW, 1230], fill=(222, 206, 190))
    for k in range(3):  # wall display cases
        x = 90 + k * 320; d.rectangle([x, 380, x + 240, 640], fill=(70, 52, 64), outline=(196, 160, 80), width=6)
        for j in range(3):
            d.arc([x + 40 + j * 60, 450, x + 90 + j * 60, 540], 200, 340, fill=(236, 230, 214), width=4)
    lay = img.convert("RGBA")
    G2.draw(lay, 380, 520, 1500, arms="pay", eyes="open")
    f = G2.Fig(380, 520, 1500 / 975)
    d = ImageDraw.Draw(lay)
    hx, hy = f.p(176, 290)
    for k, c in enumerate([(206, 228, 196), (230, 214, 236), (206, 228, 196)]):  # folded notes
        d.polygon([(hx - 10 + k * 8, hy - 40 - k * 10), (hx + 110 + k * 8, hy - 60 - k * 10), (hx + 118 + k * 8, hy - 8 - k * 10), (hx - 2 + k * 8, hy + 12 - k * 10)], fill=c, outline=(90, 110, 90))
    # jeweller's arm from the right, holding the open box
    d.polygon([(FW, 820), (820, 860), (812, 930), (FW, 930)], fill=(40, 70, 60))
    d.ellipse([776, 848, 836, 920], fill=(196, 140, 110))
    bx, by = 600, 760
    d.rectangle([bx, by, bx + 220, by + 130], fill=(30, 40, 90), outline=(196, 160, 80), width=4)
    d.polygon([(bx, by), (bx + 220, by), (bx + 200, by - 110), (bx + 20, by - 110)], fill=(36, 48, 104), outline=(196, 160, 80))
    d.rectangle([bx + 16, by + 14, bx + 204, by + 116], fill=(236, 232, 240))
    for i, t in enumerate(np.linspace(0.1, 0.9, 13)):
        a = np.pi * t; x, y = bx + 110 - 70 * np.cos(a), by + 30 + 50 * np.sin(a)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(245, 248, 255), outline=(140, 170, 210))
    d.polygon([(bx + 110, by + 82), (bx + 122, by + 98), (bx + 110, by + 116), (bx + 98, by + 98)], fill=(240, 248, 255), outline=(130, 160, 210))
    for (sx, sy, r) in ((bx + 150, by + 50, 22), (bx + 60, by + 70, 14)):
        d.line([sx - r, sy, sx + r, sy], fill=(255, 255, 255), width=4); d.line([sx, sy - r, sx, sy + r], fill=(255, 255, 255), width=4)
    # glass counter in front (covers her lower half)
    d.rectangle([0, 1230, FW, 1920], fill=(70, 52, 64))
    d.rectangle([0, 1200, FW, 1240], fill=(196, 160, 80))
    d.rectangle([60, 1290, 1020, 1600], fill=(150, 176, 196), outline=(196, 160, 80), width=6)
    for k in range(4):
        x = 140 + k * 230; d.arc([x, 1380, x + 120, 1480], 200, 340, fill=(236, 230, 214), width=5)
    return lay.convert("RGB")


def endcard():
    base = r2.paper_bg()
    os.chdir(REEL2); st = r2.logo_sticker(260); os.chdir(HERE)
    base = r2.paste_rgba(base, st, 540, 700)
    base = r2.paste_rgba(base, r2.ransom("Wear art, not a logo.", (173, 51, 97), size=84, seed=22, max_w=900), 540, 990)
    base = r2.paste_rgba(base, r2.ransom("Della Antony", (20, 20, 22), size=70, seed=21, max_w=900), 540, 1160)
    return Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))


def add_text(fr, text, seed, y=520, size=76):
    arr = np.asarray(fr).astype(np.float32) / 255
    INK = (173, 51, 97)
    arr = r2.paste_rgba(arr, r2.ransom(text, INK, size=size, seed=seed, max_w=880), FW // 2, y)
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))


# ---------------- beats ----------------
COPY = {
    "01": "Draw a box. Step in.",
    "02": "Shut out the noise. Yours too.",
    "05": "There's a child in there who never stopped playing.",
    "06": "Hand her your problems and a crayon.",
    "07": "She'll fix what your mind couldn't.",
    "07b": "She'll fix what your mind couldn't.",
    "08": "There. I have just taught you how to meditate.",
}


def main():
    frames = []
    w_med = room("meditate")
    gx, gy = GIRL[0], GIRL[1] - 520
    f1 = tilt_shift(crop_frame(w_med, gx, gy - 140, 980))
    frames.append(("01", "0-4 s  'Himalayas': snow peaks, rocks, flowers, wind", f1))
    f2 = tilt_shift(crop_frame(w_med, gx, gy - 140, 980), r=10)
    frames.append(("02", "4-7 s  same shot, the box line lands", f2))
    f3 = crop_frame(w_med, gx, 2600, 1700)
    frames.append(("03", "7-9 s  pull-back starts: a table leg, the fan", f3))
    f4 = crop_frame(w_med, WW / 2, WH / 2, WW)
    frames.append(("04", "9-11 s  her room: cloth heap, spools, pins, fan", f4))
    w_off = room("coatoff")
    frames.append(("04b", "11-13 s  eyes open, coat slides off: the dress", crop_frame(w_off, gx, 2900, 1500)))
    frames.append(("05", "13-16 s  the child plays: crayon sketches", crop_frame(room("crayon"), gx, 2960, 1500)))
    frames.append(("06", "16-19 s  she stitches the coat (the Janaki tie)", crop_frame(room("stitch"), gx, 2960, 1500)))
    frames.append(("07", "19-22 s  boutique: the coat sells", boutique()))
    frames.append(("07b", "22-25 s  jeweller: she pays, takes the necklace", jeweller()))
    frames.append(("08", "25-29 s  mirror: she wears it with the dress, turns", mirror()))
    frames.append(("09", "29-31 s  end card", endcard()))

    sheet_items = []
    for key, label, fr in frames:
        k = key[:2]
        if key in COPY:
            fr = add_text(fr, COPY[key], seed=100 + int(k), y=470 if key not in ("07", "07b", "08") else 250, size=76 if key != "08" else 68)
        low = fr.resize(LOW, Image.LANCZOS)
        low.save(os.path.join(OUT, f"frame_{key}.jpg"), quality=86)
        sheet_items.append((key, label, low))
    # contact sheet, 5 x 2
    tw, th = 270, 480
    cols = 6; rows = (len(sheet_items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 16) + 16, rows * (th + 70) + 16), (246, 242, 236)); sd = ImageDraw.Draw(sheet)
    for i, (key, label, low) in enumerate(sheet_items):
        x, y = 16 + (i % cols) * (tw + 16), 16 + (i // cols) * (th + 70)
        sheet.paste(low.resize((tw, th), Image.LANCZOS), (x, y))
        sd.text((x, y + th + 6), key + "  " + label[:40], fill=(40, 30, 30))
        sd.text((x, y + th + 24), label[40:80], fill=(40, 30, 30))
    sheet.save(os.path.join(OUT, "contact_sheet.jpg"), quality=88)
    print("ok", len(frames))


if __name__ == "__main__":
    main()
