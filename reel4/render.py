"""Reel 4 renderer: The Mediterranean Sea at Night. The glyph sea talks; the moon box goes silent.
python3 render.py sheet [times] -> contact_sheet.jpg + check_*.jpg
python3 render.py full          -> frames.mp4 (silent)"""
import os, sys, subprocess
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REEL2 = os.path.join(HERE, "..", "reel2")
os.chdir(REEL2); sys.path.insert(0, REEL2)
import lib
LOGO = lib.logo_sticker(200)
os.chdir(HERE)
# tile papers only from this painting: chalk white, canvas cream, slate grey
lib.TILE_BG[:] = [(252, 251, 247), (244, 239, 230), (196, 198, 202), (252, 251, 247)]
W, H = lib.W, lib.H
FPS, DUR = 30, 32.0
INK = (36, 34, 112)                         # the painting's indigo
PAPER = lib.paper_bg()

# ---------------- painting + the drawn-in missing pieces ----------------
SRC = np.asarray(Image.open("painting.png").convert("RGB")).astype(np.float32) / 255
G = SRC.shape[1] / 7.0                      # 7 x 7 grid of boxes, about 152 px
def box(img, r, c):
    return img[int(r * G):int((r + 1) * G), int(c * G):int((c + 1) * G)]
# two extra sea rows below: the photo is cropped, so the sea is continued from its own boxes,
# shuffled and mirrored so no box sits next to its twin
rng = np.random.default_rng(4)
n0 = SRC.shape[0]
def make_row(r0, r1):
    row = []
    for c in range(7):
        r = int(rng.integers(r0, r1)); cc = int(rng.integers(0, 7))
        while (r, cc) == (1, 3):            # never copy the moon: there is only one
            r = int(rng.integers(r0, r1)); cc = int(rng.integers(0, 7))
        b = box(SRC, r, cc)[:int(G), :int(G)]
        if rng.random() < 0.5: b = b[:, ::-1]
        if rng.random() < 0.5: b = b[::-1]
        row.append(b)
    w = min(x.shape[1] for x in row); h = min(x.shape[0] for x in row)
    return np.concatenate([x[:h, :w] for x in row], 1)
top = [make_row(0, 3) for _ in range(2)]      # sky continued above (white glyphs on charcoal)
bot = [make_row(3, 7) for _ in range(2)]      # sea continued below
ew = min(e.shape[1] for e in top + bot + [SRC])
P = np.concatenate([e[:, :ew] for e in top] + [SRC[:, :ew]] + [e[:, :ew] for e in bot], 0)
G = P.shape[0] / 11.0
P = np.asarray(Image.fromarray((P * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
PH, PW = P.shape[:2]

MOON = (3, 3)                               # column 4, row 2 (the white circle)
MC = ((MOON[0] + 0.5) * G, (MOON[1] + 0.5) * G)
yy, xx = np.mgrid[:PH, :PW].astype(np.float32)
BR, BC = np.minimum((yy // G).astype(int), 10), np.minimum((xx // G).astype(int), 6)
BID = BR * 7 + BC
fx, fy = (xx % G) / G, (yy % G) / G
INNER = np.clip(np.minimum.reduce([fx, 1 - fx, fy, 1 - fy]) / 0.12, 0, 1)
ISMOON = (BR == MOON[1]) & (BC == MOON[0])
INNER[ISMOON] = 0
PH1 = rng.uniform(0, 6.28, 77).astype(np.float32)[BID]
SPD = rng.uniform(0.8, 1.4, 77).astype(np.float32)[BID]
MOONGLOW = np.exp(-(((xx - MC[0]) ** 2 + (yy - MC[1]) ** 2) / (2 * 70.0 ** 2))).astype(np.float32)
GREY = np.array([0.30, 0.30, 0.34], np.float32)

def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def ramp(t, a, b): return float(ease((t - a) / (b - a)))
def lerp(a, b, k): return a + (b - a) * k

# ---------------- timeline ----------------
WIDE = (1.12, PW / 2, PH / 2, 960)
SEA_C = (PW / 2, 7.0 * G)
CUTS = [(5.0, (1, 6)), (6.5, (5, 7)), (8.0, (2, 8)), (9.5, (5, 4)), (11.0, (1, 7)), (12.5, (4, 6))]  # (t, (col,row))
def box_c(c, r): return ((c + 0.5) * G, (r + 0.5) * G)

def camera(t):
    if t < 2.4:                                            # hook: close on the churning sea, scanning
        return 1.9, SEA_C[0] - 120 + 100 * t, SEA_C[1], 960
    if t < 5.0:                                            # pull out to the whole painting
        k = ramp(t, 2.4, 4.4); s0, cx0, cy0 = 1.9, SEA_C[0] + 120, SEA_C[1]
        return lerp(s0, WIDE[0], k), lerp(cx0, WIDE[1], k), lerp(cy0, WIDE[2], k), 960
    if t < 14.0:                                           # jump cuts box to box, each with a small punch-in
        i = max(j for j, (a, _) in enumerate(CUTS) if t >= a)
        a, (c, r) = CUTS[i]; u = t - a
        s = 3.0 * (1.08 - 0.08 * ease(u / 0.4)) + 0.12 * u
        cx, cy = box_c(c, r)
        return s, cx + 10 * u, cy, 1050
    if t < 26.0:                                           # glide to the moon, then hold and push slowly
        a = box_c(4, 6); k = ramp(t, 14.0, 17.5)
        s = lerp(3.12, 2.5, k) + 0.06 * max(0, t - 17.5)
        return s, lerp(a[0], MC[0], k), lerp(a[1], MC[1], k), lerp(1050, 1180, k)
    k = ramp(t, 26.0, 28.6)                                # pull back to the calm whole
    s1 = 2.5 + 0.06 * 8.5
    return lerp(s1, WIDE[0], k), lerp(MC[0], WIDE[1], k), lerp(MC[1], WIDE[2], k), lerp(1180, 960, k)

def churn(t):   # how much the glyphs move
    return 1.0 - 0.75 * ramp(t, 13.6, 15.5) - 0.25 * ramp(t, 15.5, 17.0)
def silence(t): # everything but the moon dims
    return ramp(t, 14.2, 17.0) * (1 - 0.7 * ramp(t, 25.8, 28.6))
def glow(t):
    return ramp(t, 14.8, 17.8) * (1 - 0.6 * ramp(t, 26.0, 28.6))

TEXT = [(0.15, 2.4, "STOP READING THE GLYPHS"),
        (2.45, 4.9, "FIND THE BOX WITH NO WORDS"),
        (5.3, 9.0, "A SEA PAINTED AS A LANGUAGE"),
        (9.4, 13.4, "EVERY BOX IS TRYING TO SPEAK"),
        (20.0, 25.4, "LOVE IS THE TRUTH")]
CARD_IMG = [lib.ransom(s, INK, size=74, seed=7 + i, max_w=720) for i, (_, _, s) in enumerate(TEXT)]
CARD_X, CARD_Y = (W - 230) / 2 + 40, 330
NAME = lib.ransom("Della Antony", INK, size=88, seed=21, max_w=900)

def pop(t, t0):
    u = (t - t0) / 0.35
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return float(1 + 0.12 * np.sin(np.pi * u) - (1 - ease(u)) * 0.6)

def view(t):
    s, cx, cy, sy = camera(t)
    oy, ox = np.mgrid[:H, :W].astype(np.float32)
    px = (ox - W / 2) / s + cx
    py = (oy - sy) / s + cy
    inside = (px >= 0) & (px < PW - 1) & (py >= 0) & (py < PH - 1)
    pxc, pyc = np.clip(px, 0, PW - 2), np.clip(py, 0, PH - 2)
    xi, yi = pxc.astype(int), pyc.astype(int)
    a = churn(t)
    if a > 0.01:
        inn, ph, sp = INNER[yi, xi], PH1[yi, xi], SPD[yi, xi]
        amp = 7.0 * a * inn
        dx = amp * np.sin(2.4 * t * sp + ph + pyc * 0.045)
        dy = amp * np.cos(2.0 * t * sp + ph * 1.3 + pxc * 0.045)
        pxc, pyc = np.clip(pxc + dx, 0, PW - 2), np.clip(pyc + dy, 0, PH - 2)
        xi, yi = pxc.astype(int), pyc.astype(int)
    fx, fy = (pxc - xi)[..., None], (pyc - yi)[..., None]
    img = (P[yi, xi] * (1 - fx) * (1 - fy) + P[yi, xi + 1] * fx * (1 - fy)
           + P[yi + 1, xi] * (1 - fx) * fy + P[yi + 1, xi + 1] * fx * fy)
    sl = silence(t)
    if sl > 0:
        m = (~ISMOON[yi, xi])[..., None].astype(np.float32) * sl
        lum = img.mean(2, keepdims=True)
        img = img * (1 - 0.72 * m) + (GREY * 0.6 + lum * 0.4) * 0.72 * m
    g = glow(t)
    if g > 0:
        mg = MOONGLOW[yi, xi][..., None] * g * (0.85 + 0.15 * np.sin(t * 1.6))
        img = img + (1 - img) * mg * 0.45
    out = np.where(inside[..., None], img, PAPER)
    # soft shadow edge so the canvas sits on paper
    return out

def frame(t):
    img = view(t)
    for (a, b, _), im in zip(TEXT, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.15)
            img = lib.paste_rgba(img, im, CARD_X, CARD_Y + im.height / 2 - 60, scale=pop(t, a), alpha=al)
    e = ramp(t, 29.2, 29.9)
    if e > 0:
        card = PAPER.copy()
        lp = pop(t, 29.8)
        if lp > 0: card = lib.paste_rgba(card, LOGO, W / 2, 800, scale=lp * 1.25)
        np_ = pop(t, 30.3)
        if np_ > 0: card = lib.paste_rgba(card, NAME, W / 2, 1070, scale=np_)
        img = img * (1 - e) + card * e
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sheet"
    if mode == "sheet":
        ts = [float(v) for v in sys.argv[2:]] or [0.5, 2.0, 3.6, 5.5, 8.2, 11.2, 14.5, 16.0, 18.0, 21.0, 24.0, 27.0, 29.0, 31.5]
        with Pool(4) as p: fr = p.map(frame, ts)
        cols = 7; rows = (len(ts) + cols - 1) // cols
        sheet = Image.new("RGB", (270 * cols, 480 * rows), (244, 239, 230))
        for k, f in enumerate(fr):
            sheet.paste(Image.fromarray(f).resize((270, 480)), ((k % cols) * 270, (k // cols) * 480))
            Image.fromarray(f).save(f"check_{ts[k]:05.1f}.jpg", quality=88)
        sheet.save("contact_sheet.jpg", quality=88)
        print("sheet ok")
    else:
        n = int(DUR * FPS)
        enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                                "-pix_fmt", "yuv420p", "frames.mp4"], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for k, b in enumerate(p.imap(job, range(n), chunksize=4)):
                enc.stdin.write(b)
                if k % 150 == 0: print(k, "/", n, flush=True)
        enc.stdin.close(); enc.wait()
        print("frames.mp4 done")
