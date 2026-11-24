"""Reel 6: "Nope. You are still not here."  A conversation in her head, then the life she already has.
Cut-paper, 1080x1920, 30 fps, about 58.5 s. Campaign cast (cast/), Fort Kochi plates (plates/), box wall (boxwall.py).

  A  0.0 - 9.0   street, walking fast, a paper cloud of worries over her head (her lines, rust ink)
  B  9.0 - 24.0  at the church: the inner voice (navy ink) talks her back; the bell rings; she breathes
  C 24.0 - 29.0  the stop: no words, no music. Her reflection in a shop window. Zoom into the dress.
  D 29.0 - 42.4  the box wall: 2 -> 3 -> 6 -> 9 -> 35 boxes of what she already has
  E 42.4 - 51.8  home, the courtyard, Mum and Dad: the realization
  F 51.8 - 55.0  into her dress, the painting is revealed
  G 55.0 - 58.5  end card

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
DUR = 58.5
INNER = (30, 44, 120)       # the inner voice
HERS = (176, 52, 40)        # her own worried voice
CX, CY = (W - 230) / 2 + 40, 330

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ramp(t, a, b): return ease((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k

def load(p): return Image.open(os.path.join(HERE, p)).convert("RGBA")
PL = {n: load(f"plates/{n}.png") for n in ("street", "courtyard")}
ROUTE = load("plates/route.png").crop((4700, 0, 5780, 1920))
SP = {n: load(f"cast/{n}.png") for n in ("girl_front", "girl_open", "girl_back", "mum", "dad", "dad_laugh")}
PRINT = None

def sprite(base, name, cx, bottom, height, rot=0.0, alpha=1.0, flip=False, tint=None):
    im = SP[name]; sc = height / im.height
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if tint is not None:
        a = np.asarray(im).astype(np.float32); a[..., :3] = a[..., :3] * 0.6 + np.array(tint, np.float32) * 0.4
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(bottom - im.height)))
    return (int(cx - im.width / 2), int(bottom - im.height), im.width, im.height)

def paste(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------------------------------------------------------------- words on screen
CARDS = [  # (start, end, text, who)
    (0.2, 2.4, "I don’t have a job.", HERS),
    (2.4, 4.6, "I live with my parents.", HERS),
    (4.6, 6.8, "What am I doing with my life?", HERS),
    (6.8, 9.0, "Everyone is ahead of me.", HERS),
    (9.2, 11.4, "Alright now, for real, come back.", INNER),
    (11.4, 13.6, "Maybe I just need more discipline.", HERS),
    (13.6, 16.0, "Nope. You are still not here.", INNER),
    (16.0, 18.6, "Focus. on. this. bell.", INNER),
    (18.6, 21.2, "So take a deep breath.", INNER),
    (21.2, 23.8, "Like you’re not afraid to feel.", INNER),
    (42.8, 45.0, "I don’t have the money.", HERS),
    (45.0, 47.2, "I have what it buys.", HERS),
    (47.2, 49.4, "I’m not behind.", HERS),
    (49.4, 51.8, "I’m already where they’re going.", HERS),
]
CARD_IMG = [lib.ransom(s, ink, size=74, seed=i * 5 + 3, max_w=720) for i, (_, _, s, ink) in enumerate(CARDS)]
NAME = lib.ransom("Della Antony", INNER, size=88, seed=21, max_w=900)
TAG = lib.ransom("Wear art, not a logo.", HERS, size=64, seed=9, max_w=760)

def pop(t, t0):
    u = (t - t0) / 0.22
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.8 + 0.28 * math.sin(u * math.pi * 0.7) if u < 0.7 else lerp(1.06, 1.0, (u - 0.7) / 0.3)

def cards(img, t):
    for (a, b, _, _), im in zip(CARDS, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
            paste(img, im, CX, CY + im.height / 2 - 60, scale=pop(t, a), alpha=al)
    return img

# ---------------------------------------------------------------- the worry cloud
def worry_cloud(t, scale, calm=0.0):
    """Paper thought-cloud stuffed with worries: a calendar, a coin, a clock, a briefcase, a falling graph."""
    S = 2; w, h = 520 * S, 360 * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    OUT = (40, 30, 30); jit = (1 - calm) * 1.0
    for (x, y, r) in ((150, 190, 110), (260, 130, 130), (380, 180, 115), (300, 240, 110), (190, 250, 95), (410, 250, 85)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=(250, 248, 242), outline=OUT, width=4 * S)
    for (x, y, r) in ((150, 190, 106), (260, 130, 126), (380, 180, 111), (300, 240, 106), (190, 250, 91), (410, 250, 81)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=(250, 248, 242))
    def J(k): return (math.sin(t * 9 + k * 2.1) * 6 * jit * S, math.cos(t * 8 + k * 1.7) * 5 * jit * S)
    dx, dy = J(1)   # calendar
    d.rectangle((150 * S + dx, 130 * S + dy, 240 * S + dx, 220 * S + dy), fill=(255, 255, 255), outline=OUT, width=3 * S)
    d.rectangle((150 * S + dx, 130 * S + dy, 240 * S + dx, 152 * S + dy), fill=(200, 50, 44), outline=OUT, width=3 * S)
    for i in range(3):
        for j in range(3): d.rectangle(((160 + j * 26) * S + dx, (162 + i * 18) * S + dy, (176 + j * 26) * S + dx, (174 + i * 18) * S + dy), fill=(220, 220, 226))
    dx, dy = J(2)   # coin
    d.ellipse((270 * S + dx, 80 * S + dy, 340 * S + dx, 150 * S + dy), fill=(236, 190, 60), outline=OUT, width=3 * S)
    d.ellipse((284 * S + dx, 94 * S + dy, 326 * S + dx, 136 * S + dy), outline=(190, 140, 30), width=3 * S)
    dx, dy = J(3)   # clock
    d.ellipse((360 * S + dx, 140 * S + dy, 440 * S + dx, 220 * S + dy), fill=(255, 255, 255), outline=OUT, width=3 * S)
    a = t * 4
    d.line((400 * S + dx, 180 * S + dy, (400 + 28 * math.cos(a)) * S + dx, (180 + 28 * math.sin(a)) * S + dy), fill=OUT, width=4 * S)
    d.line((400 * S + dx, 180 * S + dy, 400 * S + dx, 158 * S + dy), fill=OUT, width=4 * S)
    dx, dy = J(4)   # briefcase
    d.rectangle((250 * S + dx, 210 * S + dy, 340 * S + dx, 270 * S + dy), fill=(120, 72, 40), outline=OUT, width=3 * S)
    d.rectangle((280 * S + dx, 196 * S + dy, 310 * S + dx, 212 * S + dy), outline=OUT, width=3 * S)
    dx, dy = J(5)   # falling graph
    d.line([(150 * S + dx, 240 * S + dy), (180 * S + dx, 255 * S + dy), (200 * S + dx, 245 * S + dy), (232 * S + dx, 285 * S + dy)], fill=(200, 50, 44), width=5 * S)
    for (x, y, r) in ((90, 330, 18), (60, 360, 11)):
        d.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=(250, 248, 242), outline=OUT, width=3 * S)
    im = im.resize((int(w / S * scale), int(h / S * scale)), Image.LANCZOS)
    if calm:
        a = im.split()[3].point(lambda v: int(v * (1 - 0.35 * calm))); im.putalpha(a)
    return im

def girl_walk(img, t, x, bottom, h, name="girl_front"):
    bob = abs(math.sin(t * 6.0)) * 12; rot = 2.2 * math.sin(t * 6.0)
    return sprite(img, name, x, bottom - bob, h, rot=rot)

# ---------------------------------------------------------------- shots
def shot_street(t):                                     # A: walking fast, the cloud grows
    k = t / 9.0
    z = 1.06; pan = lerp(-30, 30, k)
    bg = PL["street"].resize((int(W * z), int(H * z)), Image.LANCZOS).crop((int((W * z - W) / 2 + pan), int((H * z - H) / 2), int((W * z - W) / 2 + pan) + W, int((H * z - H) / 2) + H))
    img = bg.copy()
    x = lerp(240, 600, k)
    girl_walk(img, t, x, 1760, 900, "girl_open")
    cl = worry_cloud(t, lerp(0.75, 1.2, ease(k)))
    paste(img, cl, x + 60, 1760 - 900 - cl.height / 2 + 30)
    return img

def bell_rings(d, t):
    if 16.3 <= t < 19.5:
        for k in range(4):
            u = (t - 16.3) * 1.2 - k * 0.3
            if u <= 0: continue
            r = 40 + u * 260; a = max(0, 1 - u / 2.2)
            d.ellipse((470 - r, 350 - r, 470 + r, 350 + r), outline=(250, 250, 250, int(220 * a)), width=8)

def shot_church(t):                                     # B: the inner voice, the bell, the breath
    img = ROUTE.copy(); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((432, 300, 508, 410), fill=(60, 46, 40), outline=(28, 22, 20), width=3)          # belfry
    sw = 0.0
    if t >= 16.2: sw = 22 * math.sin((t - 16.2) * 5.0) * math.exp(-(t - 16.2) / 2.0)
    bell = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); bd = ImageDraw.Draw(bell)
    bd.polygon([(20, 70), (70, 70), (62, 30), (45, 14), (28, 30)], fill=(214, 172, 60), outline=(28, 22, 20), width=3)
    bd.ellipse((39, 66, 51, 80), fill=(150, 110, 30))
    bell = bell.rotate(sw, center=(45, 10), resample=Image.BICUBIC)
    img.alpha_composite(bell, (425, 312))
    bell_rings(d, t)
    breath = ramp(t, 18.6, 23.0)
    if 18.6 <= t < 22.0:                                # wind lines: the breath going out into the street
        for k in range(4):
            u = ((t - 18.6) * 0.5 + k * 0.25) % 1
            y = 900 + k * 90; x0 = 100 + u * 900
            d.line([(x0, y), (x0 + 60, y - 10), (x0 + 120, y + 4)], fill=(255, 255, 255, int(200 * (1 - u))), width=5)
    x = 300
    stand = sprite(img, "girl_open" if t < 18.6 else "girl_front", x, 1780 + 6 * math.sin(t * 1.2) * breath, 920)
    wob = 0.0
    if 13.6 <= t < 15.0: wob = 10 * math.sin((t - 13.6) * 18) * (1 - (t - 13.6) / 1.4)
    cl = worry_cloud(t, lerp(1.2, 0.42, breath), calm=breath)
    paste(img, cl, x + 80 + wob, stand[1] - cl.height / 2 + 30)
    return img

def window_scene(t):
    img = PL["street"].copy(); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((90, 380, 990, 1560), fill=(110, 72, 40), outline=(28, 22, 20), width=4)          # shop front
    d.rectangle((130, 420, 950, 1500), fill=(196, 222, 236), outline=(28, 22, 20), width=4)      # big glass window
    sprite(img, "girl_front", 540, 1430, 860, alpha=0.55, flip=True, tint=(170, 205, 230))       # her reflection
    for k in range(3):                                                                           # glass shine
        x0 = 200 + k * 260
        d.polygon([(x0, 420), (x0 + 70, 420), (x0 - 80, 1500), (x0 - 150, 1500)], fill=(255, 255, 255, 40))
    d.rectangle((90, 1560, 990, 1600), fill=(110, 72, 40))
    return img

def shot_window(t):                                     # C: the stop
    img = window_scene(t)
    sprite(img, "girl_back", 520, 1980, 1180)           # her, from behind, looking in
    if t < 26.4: return img
    k = ease((t - 26.4) / 2.4)
    z = 1 + 9 * k ** 1.7
    cx, cy = lerp(540, 520, k), lerp(960, 1380, k)    # into the print on her dress
    zw, zh = W / z, H / z
    img = img.convert("RGB").transform((W, H), Image.EXTENT, (cx - zw / 2, cy - zh / 2, cx + zw / 2, cy + zh / 2), Image.BICUBIC).convert("RGBA")
    if t > 28.2:
        img = Image.blend(img, print_full(), ease((t - 28.2) / 0.8))
    return img

def print_full():
    global PRINT
    if PRINT is None:
        sys.path.insert(0, HERE)
        p = Image.open(os.path.join(HERE, "sunset2.jpg")).convert("RGB").rotate(90, expand=True).crop((0, 0, 810, 1390))
        PRINT = p.resize((W, int(W * p.height / p.width)), Image.LANCZOS).crop((0, 0, W, H)).convert("RGBA") if W * p.height / p.width >= H \
            else p.resize((int(H * p.width / p.height), H), Image.LANCZOS).convert("RGBA")
        if PRINT.size != (W, H): PRINT = PRINT.crop(((PRINT.width - W) // 2, 0, (PRINT.width - W) // 2 + W, H))
    return PRINT

def shot_wall(t):                                       # D: the box wall (its own clock starts at 29.0)
    u = t - 29.0
    img = BWALL.wall(min(u, 13.4))
    if u < 0.6: img = Image.blend(print_full(), img, ease(u / 0.6))
    return img

def shot_home(t):                                       # E: the courtyard, Mum and Dad, the realization
    img = PL["courtyard"].copy(); d = ImageDraw.Draw(img, "RGBA")
    for j in range(3):
        bx = 200 + 700 * ((t * 0.08 + j * 0.33) % 1); by = 700 + 60 * math.sin(t * 2 + j)
        fl = abs(math.sin(t * 9 + j)) * 18 + 6
        d.ellipse((bx - 22, by - fl, bx, by + 4), fill=(244, 200, 60), outline=(28, 22, 20), width=2)
        d.ellipse((bx, by - fl, bx + 22, by + 4), fill=(244, 200, 60), outline=(28, 22, 20), width=2)
    sprite(img, "mum", 250, 1800, 900)
    sprite(img, "dad_laugh" if (t > 47.2 and (t * 2) % 2 < 1.2) else "dad", 830, 1810, 940)
    sprite(img, "girl_front", 540, 1820, 900)
    return img

def painting_card(t, t0, t1):
    base = Image.new("RGBA", (W, H), (248, 246, 240, 255))
    k = ease((t - t0) / (t1 - t0)); z = 1.3 - 0.3 * k
    p = BWALL.PAINT
    pw = int(W * 0.94 * z); ph = int(pw * p.height / p.width)
    base.alpha_composite(p.resize((pw, ph), Image.LANCZOS).convert("RGBA"), ((W - pw) // 2, (H - ph) // 2 - 60))
    return base

def shot_reveal(t):                                     # F: into her dress, the painting
    img = shot_home(51.8)
    k = ease((t - 51.8) / 1.6)
    z = 1 + 7 * k ** 1.6
    cx, cy = lerp(540, 525, k), lerp(960, 1330, k)
    zw, zh = W / z, H / z
    img = img.convert("RGB").transform((W, H), Image.EXTENT, (cx - zw / 2, cy - zh / 2, cx + zw / 2, cy + zh / 2), Image.BICUBIC).convert("RGBA")
    if t > 53.0: img = Image.blend(img, painting_card(t, 53.0, 55.0), ease((t - 53.0) / 0.7))
    return img

def shot_end(t):                                        # G
    img = Image.new("RGBA", (W, H), (248, 246, 240, 255))
    p = pop(t, 55.3)
    if p: paste(img, LOGO, W / 2, 760, scale=p * 1.25)
    p = pop(t, 55.8)
    if p: paste(img, NAME, W / 2, 1040, scale=p)
    p = pop(t, 56.4)
    if p: paste(img, TAG, W / 2, 1200, scale=p)
    return img

SHOTS = [(0.0, shot_street), (9.0, shot_church), (24.0, shot_window), (29.0, shot_wall), (42.4, shot_home),
         (51.8, shot_reveal), (55.0, shot_end)]
WEAVE = None

def frame(t):
    global WEAVE
    if WEAVE is None: WEAVE = BWALL.linen_overlay()
    i = max(j for j, (a, _) in enumerate(SHOTS) if t >= a)
    img = SHOTS[i][1](t)
    a = SHOTS[i][0]
    if i > 0 and t - a < 0.35 and SHOTS[i][1] not in (shot_wall, shot_reveal):
        img = Image.blend(SHOTS[i - 1][1](a - 0.001), img, (t - a) / 0.35)
    if i == 3 and t > 42.0:                             # wall dissolves into home
        img = Image.blend(img, shot_home(42.4), ease((t - 42.0) / 0.4))
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
