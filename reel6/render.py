"""Reel 6: "Nope. You are still not here."  A conversation in her head, then the life she already has.
Cut-paper, 1080x1920, 30 fps, about 57.5 s. Campaign cast (cast/), Fort Kochi plates (plates/), box wall (boxwall.py).

  A  0.0 - 8.0   she walks toward us down the Fort Kochi street; grey cloud of worries over her head
  B  8.0 - 22.0  at the church: the inner voice talks her back; the bell rings; she breathes
  C 22.0 - 28.0  the stop: no words, no music. She sees herself in a gold oval mirror and looks at the dress.
                 The camera goes into the dress, the boxes in the print come alive, then into the driving box.
  D 28.0 - 42.2  the box wall: 1 -> 2 -> 3 -> 6 -> 9 -> 35 boxes of what she already has
  E 42.2 - 51.4  Fort Kochi at sunset, the fishing nets: the realization
  F 51.4 - 54.4  the sun becomes the painting
  G 54.4 - 57.5  end card

Words: her dark thoughts in a GREY cloud with grey letters; the inner voice in a plain BLUE box with colourful letters;
her realization at the end in a light cloud with colourful letters (her thoughts, no longer dark).

  python3 render.py sheet t1 t2 ...  -> sheet.jpg        python3 render.py full -> frames.mp4 (silent)
"""
import math, os, subprocess, sys
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.join(HERE, "..", "reel2")
_cwd = os.getcwd(); os.chdir(R2); sys.path.insert(0, R2); import lib; LOGO = lib.logo_sticker(230); os.chdir(_cwd)
sys.path.insert(0, HERE)
import boxwall as BWALL

W, H, FPS = 1080, 1920, 30
T_A, T_B, T_C, T_D, T_E, T_F, T_G, DUR = 0.0, 8.0, 22.0, 28.0, 42.2, 51.4, 54.4, 57.5
NAVY = (30, 44, 120)
CX, CY = (W - 230) / 2 + 40, 360

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ramp(t, a, b): return ease((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k

def load(p): return Image.open(os.path.join(HERE, p)).convert("RGBA")
PL = {n: load(f"plates/{n}.png") for n in ("street",)}
ROUTE = load("plates/route.png")
CHURCH = ROUTE.crop((4700, 0, 5780, 1920))
SP = {n: load(f"cast/{n}.png") for n in ("girl_front", "girl_open", "girl_back")}

def sprite(base, name, cx, bottom, height, alpha=1.0, flip=False, tint=None):
    im = SP[name]; sc = height / im.height
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if tint is not None:
        a = np.asarray(im).astype(np.float32); a[..., :3] = a[..., :3] * 0.85 + np.array(tint, np.float32) * 0.15
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(bottom - im.height)))
    return (int(cx - im.width / 2), int(bottom - im.height), im.width, im.height)

def paste(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------------------------------------------------------------- words, in two kinds of bubble
GREY_TILES = [(238, 238, 238), (214, 214, 216), (196, 196, 200), (248, 248, 248)]
BRIGHT_TILES = [(246, 214, 80), (240, 150, 60), (160, 204, 240), (255, 255, 255), (252, 236, 170)]

def tiles(text, kind, seed):
    old = lib.TILE_BG
    lib.TILE_BG = GREY_TILES if kind == "dark" else BRIGHT_TILES
    im = lib.ransom(text, (44, 44, 48) if kind == "dark" else NAVY, size=70, seed=seed, max_w=580)
    lib.TILE_BG = old
    return im

def cloud_shape(w, h, fill, outline, tail=True):
    """a thought cloud around a w x h block, with a tail of little circles going down to her head"""
    pad = 46; W2, H2 = w + pad * 2, h + pad * 2 + (120 if tail else 0)
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = 20, 20, W2 - 20, h + pad * 2 - 20
    pts = []
    n = 14
    for i in range(n):
        u = i / n
        per = 2 * (bx1 - bx0) + 2 * (by1 - by0); s_ = u * per
        if s_ < bx1 - bx0: pts.append((bx0 + s_, by0))
        elif s_ < (bx1 - bx0) + (by1 - by0): pts.append((bx1, by0 + s_ - (bx1 - bx0)))
        elif s_ < 2 * (bx1 - bx0) + (by1 - by0): pts.append((bx1 - (s_ - (bx1 - bx0) - (by1 - by0)), by1))
        else: pts.append((bx0, by1 - (s_ - 2 * (bx1 - bx0) - (by1 - by0))))
    r = 40
    for (x, y) in pts: d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=5)
    tails = [(W2 * 0.32, by1 + 40, 22), (W2 * 0.27, by1 + 88, 14)] if tail else []
    for (x, y, rr) in tails: d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=fill, outline=outline, width=5)
    for (x, y) in pts: d.ellipse((x - r + 5, y - r + 5, x + r - 5, y + r - 5), fill=fill)
    d.rectangle((bx0, by0, bx1, by1), fill=fill)
    return im, pad

def make_card(text, kind, seed):
    t = tiles(text, kind, seed)
    if kind == "voice":                                         # the inner voice: one plain blue box
        pad = 40
        im = Image.new("RGBA", (t.width + pad * 2, t.height + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((4, 4, im.width - 4, im.height - 4), radius=26, fill=(44, 96, 176), outline=(24, 56, 120), width=5)
        im.alpha_composite(t, (pad, pad))
    else:                                                       # her thoughts: a cloud (grey when dark, light at the end)
        fill, out = ((112, 112, 118), (64, 64, 70)) if kind == "dark" else ((255, 248, 232), (176, 120, 60))
        im, pad = cloud_shape(t.width, t.height, fill, out)
        im.alpha_composite(t, (pad + 20, pad + 20))
    sh = Image.new("RGBA", (im.width + 14, im.height + 14), (0, 0, 0, 0))
    a = im.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.3))
    sh.paste((0, 0, 0, 255), (10, 10), a); sh.alpha_composite(im, (0, 0))
    return sh

CARDS = [  # (start, end, text, kind)  kind: dark = her worry, voice = the inner voice, light = her, at peace
    (0.2, 2.2, "I don’t have a job.", "dark"),
    (2.2, 4.2, "I live with my parents.", "dark"),
    (4.2, 6.1, "What am I doing with my life?", "dark"),
    (6.1, 8.0, "Everyone is ahead of me.", "dark"),
    (8.2, 10.5, "Alright now, for real, come back.", "voice"),
    (10.5, 12.6, "Maybe I just need more discipline.", "dark"),
    (12.6, 14.8, "Nope. You are still not here.", "voice"),
    (14.8, 17.2, "Focus. on. this. bell.", "voice"),
    (17.2, 19.6, "So take a deep breath.", "voice"),
    (19.6, 22.0, "Like you’re not afraid to feel.", "voice"),
    (42.6, 44.8, "I don’t have the money.", "light"),
    (44.8, 47.0, "I have what it buys.", "light"),
    (47.0, 49.2, "I’m not behind.", "light"),
    (49.2, 51.4, "I’m already where they’re going.", "light"),
]
CARD_IMG = [make_card(s, k, i * 5 + 3) for i, (_, _, s, k) in enumerate(CARDS)]
NAME = lib.ransom("Della Antony", NAVY, size=88, seed=21, max_w=900)
TAG = lib.ransom("Wear art, not a logo.", NAVY, size=64, seed=9, max_w=760)

def pop(t, t0):
    u = (t - t0) / 0.22
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.8 + 0.28 * math.sin(u * math.pi * 0.7) if u < 0.7 else lerp(1.06, 1.0, (u - 0.7) / 0.3)

def cards(img, t):
    for (a, b, _, _), im in zip(CARDS, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
            paste(img, im, CX, CY + im.height / 2 - 120, scale=pop(t, a), alpha=al)
    return img

# ---------------------------------------------------------------- the worry cloud over her head (grey, not colourful)
def worry_cloud(t, scale, calm=0.0):
    S = 2; w, h = 520 * S, 360 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    OUT = (60, 60, 66); FILL = (150, 150, 156); jit = (1 - calm)
    for (x, y, r) in ((150, 190, 110), (260, 130, 130), (380, 180, 115), (300, 240, 110), (190, 250, 95), (410, 250, 85)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=FILL, outline=OUT, width=4 * S)
    for (x, y, r) in ((150, 190, 106), (260, 130, 126), (380, 180, 111), (300, 240, 106), (190, 250, 91), (410, 250, 81)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=FILL)
    def J(k): return (math.sin(t * 9 + k * 2.1) * 6 * jit * S, math.cos(t * 8 + k * 1.7) * 5 * jit * S)
    G1, G2, G3 = (236, 236, 238), (200, 200, 204), (90, 90, 96)
    dx, dy = J(1)
    d.rectangle((150 * S + dx, 130 * S + dy, 240 * S + dx, 220 * S + dy), fill=G1, outline=OUT, width=3 * S)
    d.rectangle((150 * S + dx, 130 * S + dy, 240 * S + dx, 152 * S + dy), fill=G3, outline=OUT, width=3 * S)
    for i in range(3):
        for j in range(3): d.rectangle(((160 + j * 26) * S + dx, (162 + i * 18) * S + dy, (176 + j * 26) * S + dx, (174 + i * 18) * S + dy), fill=G2)
    dx, dy = J(2)
    d.ellipse((270 * S + dx, 80 * S + dy, 340 * S + dx, 150 * S + dy), fill=G2, outline=OUT, width=3 * S)
    dx, dy = J(3)
    d.ellipse((360 * S + dx, 140 * S + dy, 440 * S + dx, 220 * S + dy), fill=G1, outline=OUT, width=3 * S)
    a = t * 4
    d.line((400 * S + dx, 180 * S + dy, (400 + 28 * math.cos(a)) * S + dx, (180 + 28 * math.sin(a)) * S + dy), fill=OUT, width=4 * S)
    dx, dy = J(4)
    d.rectangle((250 * S + dx, 210 * S + dy, 340 * S + dx, 270 * S + dy), fill=G3, outline=OUT, width=3 * S)
    dx, dy = J(5)
    d.line([(150 * S + dx, 240 * S + dy), (180 * S + dx, 255 * S + dy), (200 * S + dx, 245 * S + dy), (232 * S + dx, 285 * S + dy)], fill=G3, width=5 * S)
    for (x, y, r) in ((90, 330, 18), (60, 360, 11)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=FILL, outline=OUT, width=3 * S)
    im = im.resize((int(w / S * scale), int(h / S * scale)), Image.LANCZOS)
    if calm:
        a = im.split()[3].point(lambda v: int(v * (1 - 0.35 * calm))); im.putalpha(a)
    return im

def zoom_img(img, cx, cy, z):
    zw, zh = W / z, H / z
    return img.convert("RGB").transform((W, H), Image.EXTENT, (cx - zw / 2, cy - zh / 2, cx + zw / 2, cy + zh / 2), Image.BICUBIC).convert("RGBA")

# ---------------------------------------------------------------- A: she walks toward us
def shot_street(t):
    k = ease(t / 8.0)
    img = zoom_img(PL["street"], 540, 1000, 1.0 + 0.12 * k)        # the street comes toward us as she does
    h = lerp(600, 920, k); bottom = lerp(1430, 1800, k)
    bottom += 5 * math.sin(t * 2 * math.pi * 1.6)                    # gentle step rhythm, no hopping
    x = 470
    box = sprite(img, "girl_open", x, bottom, h)
    cl = worry_cloud(t, lerp(0.7, 1.15, k))
    paste(img, cl, x + 50, box[1] - cl.height / 2 + 30)
    return img

# ---------------------------------------------------------------- B: at the church
def shot_church(t):
    img = CHURCH.copy(); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((432, 300, 508, 410), fill=(60, 46, 40), outline=(28, 22, 20), width=3)
    tb = 15.1; sw = 0.0
    if t >= tb: sw = 22 * math.sin((t - tb) * 5.0) * math.exp(-(t - tb) / 2.0)
    bell = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); bd = ImageDraw.Draw(bell)
    bd.polygon([(20, 70), (70, 70), (62, 30), (45, 14), (28, 30)], fill=(214, 172, 60), outline=(28, 22, 20), width=3)
    bd.ellipse((39, 66, 51, 80), fill=(150, 110, 30))
    img.alpha_composite(bell.rotate(sw, center=(45, 10), resample=Image.BICUBIC), (425, 312))
    if tb <= t < tb + 3.2:
        for k in range(4):
            u = (t - tb) * 1.2 - k * 0.3
            if u <= 0: continue
            r = 40 + u * 260; a = max(0, 1 - u / 2.2)
            d.ellipse((470 - r, 350 - r, 470 + r, 350 + r), outline=(250, 250, 250, int(220 * a)), width=8)
    breath = ramp(t, 17.2, 21.4)
    if 17.2 <= t < 20.4:
        for k in range(4):
            u = ((t - 17.2) * 0.5 + k * 0.25) % 1
            y = 900 + k * 90; x0 = 100 + u * 900
            d.line([(x0, y), (x0 + 60, y - 10), (x0 + 120, y + 4)], fill=(255, 255, 255, int(200 * (1 - u))), width=5)
    x = 310
    stand = sprite(img, "girl_open" if t < 17.2 else "girl_front", x, 1790 + 5 * math.sin(t * 1.2) * breath, 930)
    wob = 10 * math.sin((t - 12.6) * 18) * (1 - (t - 12.6) / 1.4) if 12.6 <= t < 14.0 else 0.0
    cl = worry_cloud(t, lerp(1.15, 0.42, breath), calm=breath)
    paste(img, cl, x + 80 + wob, stand[1] - cl.height / 2 + 30)
    return img

# ---------------------------------------------------------------- C: the mirror, the dress, the boxes inside it
MIR = (560, 300, 1000, 1620)                   # gold oval mirror on the pavement outside a shop
REFL = (780, 1470, 880)                        # reflection: centre x, feet y, height

def mirror_scene(t):
    img = PL["street"].copy(); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = MIR
    d.line((x0 + 80, y1 - 20, x0 + 20, y1 + 140), fill=(160, 120, 40), width=12); d.line((x1 - 80, y1 - 20, x1 - 20, y1 + 140), fill=(160, 120, 40), width=12)
    d.ellipse((x0 - 22, y0 - 22, x1 + 22, y1 + 22), fill=(214, 172, 60), outline=(120, 86, 30), width=5)
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    refl_bg = PL["street"].transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(refl_bg).astype(np.float32); a[..., :3] = a[..., :3] * 0.8 + np.array((205, 225, 238), np.float32) * 0.2
    glass.alpha_composite(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    sprite(glass, "girl_front", REFL[0], REFL[1], REFL[2], tint=(205, 225, 238))            # her reflection, clear
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse(MIR, fill=255)
    img.paste(glass, (0, 0), m)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.polygon([(x0 + 90, y0 + 60), (x0 + 150, y0 + 40), (x0 + 60, y1 - 200), (x0 + 20, y1 - 300)], fill=(255, 255, 255, 50))
    img.alpha_composite(sh)
    return img

def print_rects():
    """screen rects of the painting's boxes in the full-screen dress print"""
    s = 1920 / 1390; off = (810 * s - W) / 2
    cols = [0, 97, 245, 400, 555, 700, 810]; rows = [0, 85, 228, 373, 516, 659, 813, 968, 1118, 1263, 1390]
    out = []
    for i in range(len(cols) - 1):
        for j in range(len(rows) - 1):
            out.append((cols[i] * s - off, rows[j] * s, cols[i + 1] * s - off, rows[j + 1] * s))
    return out
PRECTS = print_rects()
DRIVE_RECT = (245 * 1920 / 1390 - (810 * 1920 / 1390 - W) / 2, 659 * 1920 / 1390, 400 * 1920 / 1390 - (810 * 1920 / 1390 - W) / 2, 813 * 1920 / 1390)
LIVE = [(r, c) for r, c in zip([r for r in PRECTS if r != DRIVE_RECT][3:40:3], BWALL.ORDER[1:14])]

PRINT = None
def print_full():
    global PRINT
    if PRINT is None:
        art = os.path.join(HERE, "artwork.jpg")
        p = Image.open(art if os.path.exists(art) else os.path.join(HERE, "sunset2.jpg")).convert("RGB")
        if p.width > p.height: p = p.rotate(90, expand=True)
        p = p.crop((0, 0, int(p.width * 810 / 1083), p.height))
        s = 1920 / p.height
        p = p.resize((int(p.width * s), 1920), Image.LANCZOS)
        PRINT = p.crop(((p.width - W) // 2, 0, (p.width - W) // 2 + W, H)).convert("RGBA")
    return PRINT

def fit_box(r, aspect=BWALL.CW / BWALL.CH, m=0.1):
    x0, y0, x1, y1 = r; w_, h_ = (x1 - x0) * (1 - m), (y1 - y0) * (1 - m)
    if w_ / h_ > aspect: w_ = h_ * aspect
    else: h_ = w_ / aspect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - w_ / 2, cy - h_ / 2, w_, h_

def live_print(t, k_in, skip_drive=False):
    """the dress print with the boxes coming alive: little moving scenes inside the painted boxes"""
    img = print_full().copy()
    items = LIVE if skip_drive else LIVE + [(DRIVE_RECT, BWALL.ORDER[0])]
    for n, (r, cell) in enumerate(items):
        a = ease(k_in * 1.6 - n * 0.05)
        if a <= 0: continue
        x, y, w_, h_ = fit_box(r)
        im = BWALL.cell_img(cell, t, (w_, h_))
        if a < 1: im.putalpha(im.split()[3].point(lambda v, a=a: int(v * a)))
        img.alpha_composite(im, (int(x), int(y)))
    return img

def shot_mirror(t):
    if t < 25.6:                                               # she looks at herself, at the dress
        img = mirror_scene(t)
        lean = ramp(t, 22.4, 24.0) * 14
        sprite(img, "girl_back", 330 + lean, 1990, 1220)
        if t > 23.6:
            k = ease((t - 23.6) / 1.6)
            img = zoom_img(img, lerp(540, REFL[0], k), lerp(960, REFL[1] - REFL[2] * 0.66, k), 1 + 2.6 * k ** 1.4)
        if t > 24.7: img = Image.blend(img, live_print(t, 0.0), ease((t - 24.7) / 0.8))
        return img
    if t < 27.0:                                               # the boxes in the dress come alive
        return live_print(t, (t - 25.6) / 1.2)
    # into the driving box; it becomes the first box of the wall
    k = ease((t - 27.0) / 0.8)
    x, y, w_, h_ = fit_box(DRIVE_RECT)
    tx, ty, tw, th = BWALL.stage_rect(1, (1, 1), BWALL.ORDER[0])
    z = lerp(1.0, th / h_, k)
    bcx, bcy = x + w_ / 2, y + h_ / 2
    ncx, ncy = lerp(bcx, tx + tw / 2, k), lerp(bcy, ty + th / 2, k)
    base = live_print(t, 1.0, skip_drive=True).convert("RGB")
    # screen = (p - (bcx,bcy)) * z + (ncx,ncy)  ->  source extent for the transform
    sx0, sy0 = bcx - ncx / z, bcy - ncy / z
    base = base.transform((W, H), Image.EXTENT, (sx0, sy0, sx0 + W / z, sy0 + H / z), Image.BICUBIC).convert("RGBA")
    pw, ph = w_ * z, h_ * z
    base.alpha_composite(BWALL.cell_img(BWALL.ORDER[0], t, (pw, ph)), (int(ncx - pw / 2), int(ncy - ph / 2)))
    if t > 27.8: base = Image.blend(base, BWALL.wall(0.0), ease((t - 27.8) / 0.2))
    return base

# ---------------------------------------------------------------- D: the wall
def shot_wall(t):
    return BWALL.wall(min(t - T_D, 14.2))

# ---------------------------------------------------------------- E: Fort Kochi at sunset, the nets
SUNSET = None
def sunset_plate():
    global SUNSET
    if SUNSET is None:
        p = ROUTE.crop((0, 0, W, H)).convert("RGB")
        a = np.asarray(p).astype(np.int32)
        sky = (np.abs(a - np.array((224, 232, 222))).sum(2) < 12); cld = (np.abs(a - np.array((244, 240, 228))).sum(2) < 12)
        sea = (np.abs(a - np.array((70, 140, 190))).sum(2) < 12)
        a[sky] = (250, 210, 156); a[cld] = (252, 230, 196); a[sea] = (60, 108, 170)
        img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
        sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sun).ellipse((640, 690, 840, 890), fill=(240, 140, 50, 255))
        m = Image.fromarray((sky | cld).astype(np.uint8) * 255)
        img.paste(sun, (0, 0), Image.fromarray(np.minimum(np.asarray(sun.split()[3]), np.asarray(m))))
        SUNSET = img
    return SUNSET

def shot_sunset(t):
    img = sunset_plate().copy(); d = ImageDraw.Draw(img, "RGBA")
    for k in range(7):                                         # light on the water
        y = 850 + k * 46; w_ = 90 - k * 8 + 14 * math.sin(t * 2 + k)
        d.line((740 - w_, y, 740 + w_, y), fill=(250, 190, 90, 200), width=6)
    sprite(img, "girl_back", 360, 1930, 1000)
    return img

def painting_card(t, t0, t1):
    base = Image.new("RGBA", (W, H), (248, 246, 240, 255))
    k = ease((t - t0) / (t1 - t0)); z = 1.3 - 0.3 * k
    p = BWALL.PAINT
    pw = int(W * 0.94 * z); ph = int(pw * p.height / p.width)
    base.alpha_composite(p.resize((pw, ph), Image.LANCZOS).convert("RGBA"), ((W - pw) // 2, (H - ph) // 2 - 60))
    return base

def shot_reveal(t):                                     # F: the sun becomes the painting
    k = ease((t - T_F) / 1.6)
    img = zoom_img(shot_sunset(t), lerp(540, 740, k), lerp(960, 790, k), 1 + 3 * k ** 1.5)
    if t > T_F + 1.1: img = Image.blend(img, painting_card(t, T_F + 1.1, T_G), ease((t - T_F - 1.1) / 0.8))
    return img

def shot_end(t):
    img = Image.new("RGBA", (W, H), (248, 246, 240, 255))
    p = pop(t, T_G + 0.3)
    if p: paste(img, LOGO, W / 2, 760, scale=p * 1.25)
    p = pop(t, T_G + 0.8)
    if p: paste(img, NAME, W / 2, 1040, scale=p)
    p = pop(t, T_G + 1.4)
    if p: paste(img, TAG, W / 2, 1200, scale=p)
    return img

SHOTS = [(T_A, shot_street), (T_B, shot_church), (T_C, shot_mirror), (T_D, shot_wall), (T_E, shot_sunset), (T_F, shot_reveal), (T_G, shot_end)]
WEAVE = None

def frame(t):
    global WEAVE
    if WEAVE is None: WEAVE = BWALL.linen_overlay()
    i = max(j for j, (a, _) in enumerate(SHOTS) if t >= a)
    img = SHOTS[i][1](t)
    a = SHOTS[i][0]
    if i > 0 and t - a < 0.35 and SHOTS[i][1] not in (shot_wall, shot_reveal):
        img = Image.blend(SHOTS[i - 1][1](a - 0.001), img, (t - a) / 0.35)
    if SHOTS[i][1] is shot_wall and t > T_E - 0.4:
        img = Image.blend(img, shot_sunset(T_E), ease((t - (T_E - 0.4)) / 0.4))
    img = cards(img, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32) * WEAVE
    return arr.clip(0, 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        ts = [float(x) for x in sys.argv[2:]]
        with Pool(4) as p: fr = p.map(frame, ts)
        ims = [Image.fromarray(f).resize((270, 480), Image.LANCZOS) for f in fr]
        cols = min(8, len(ims)); rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 278 + 8, rows * 488 + 8), (240, 236, 228))
        for k, im in enumerate(ims): sh.paste(im, (8 + k % cols * 278, 8 + k // cols * 488))
        sh.save(os.path.join(HERE, "sheet.jpg"), quality=88)
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", os.path.join(HERE, "frames.mp4")], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, b in enumerate(pool.imap(job, range(n), chunksize=4)):
                p.stdin.write(b)
                if k % 300 == 0: print(k, "/", n, flush=True)
        p.stdin.close(); p.wait()
        print("frames.mp4 done")
