"""Reel 2 frame renderer. `python3 render.py sheet` -> contact sheet; `python3 render.py full` -> frames.mp4 (silent)."""
import sys, subprocess, numpy as np
from multiprocessing import Pool
from PIL import Image, ImageFilter
import lib
from lib import *
from lib import _paint

FPS, DUR = 30, 35.5
PW, PH = _paint.shape[1], _paint.shape[0]
INK_M, INK_B = (173, 51, 97), (20, 20, 22)

# ---------- one-time prep (inherited by worker processes) ----------
def _u8(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
_M = np.asarray(_u8(lib.RING).filter(ImageFilter.MaxFilter(7))).astype(np.float32) / 255
_M = np.clip(_M * 2, 0, 1)
_keep = 1 - _M
_bl = lambda a: np.asarray(_u8(a).filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
_num = np.stack([_bl(PAINT[..., c] * _keep) for c in range(3)], -1)
_den = _bl(_keep)[..., None] + 1e-4
NORING_PIL = _u8(PAINT * _keep[..., None] + np.clip(_num / _den, 0, 1) * _M[..., None])
RING_PIL = Image.fromarray((lib.RING * 255).astype(np.uint8), "L")
PAINT_PIL = _u8(PAINT)
del _M, _keep, _num, _den
lib.PAINT = None  # free the float copy in children
PAPER = paper_bg()
_r = np.random.default_rng(9)
NOISE = np.asarray(Image.fromarray((_r.random((H // 24, W // 24)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255

def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def ramp(t, a, b): return ease((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k

def warp(pim, px, py, s, sx, sy, rot=0.0, sy_scale=1.0):
    """Map painting point (px,py) to screen (sx,sy); scale s; rotation rot deg clockwise; vertical squash."""
    a = np.deg2rad(rot); c, sn = np.cos(a), np.sin(a)
    A, B = c / s, sn / (s * sy_scale)
    D, E = -sn / s, c / (s * sy_scale)
    coeffs = (A, B, px - A * sx - B * sy, D, E, py - D * sx - E * sy)
    out = pim.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
    a_ = np.asarray(out).astype(np.float32) / 255
    return a_

# ---------- camera ----------
def camera(t):
    k = ramp(t, 0.0, 10.5)
    s = lerp(H / PH, 0.90, k) * (1 + 0.025 * ramp(t, 10.5, 21))
    px = lerp(PAD + PW / 2, SC[0], k); py = lerp(PAD + PH / 2, SC[1], k)
    sx, sy = 540, lerp(960, 820, k)
    sun = (sx + (SC[0] - px) * s, sy + (SC[1] - py) * s)
    return s, px, py, sx, sy, sun

# ---------- ring / halo ----------
def ring_state(t, s, sun):
    rot = 4.0 * max(0.0, t - 6.5)
    d = ramp(t, 19.0, 23.0)
    cx = lerp(sun[0], 540, d); cy = lerp(sun[1], 560, d)
    rw = lerp(SUN_R * s, 300, d); tilt = lerp(0, 72, d)
    if t < 11: col = INK
    elif t < 15: col = lerp(INK, ORANGE, ramp(t, 11, 15))
    elif t < 20: col = lerp(ORANGE, SUNLIGHT, ramp(t, 15, 19))
    else: col = lerp(SUNLIGHT, GOLD, ramp(t, 20, 23))
    glow_amt = 0.15 * ramp(t, 13, 19) + 0.85 * ramp(t, 19, 23)
    deco_amt = ramp(t, 22, 23.6)
    return cx, cy, rw, tilt, rot, col, glow_amt, deco_amt

def draw_ring(img, t, cx, cy, rw, tilt, rot, col, glow_amt, deco_amt):
    sq = np.cos(np.deg2rad(tilt))
    a = warp(RING_PIL, SC[0], SC[1], rw / SUN_R, cx, cy, rot, sq)
    thick = 1 + 1.6 * ramp(t, 19, 23)
    band = np.clip(np.maximum(a * 1.6, glow(a, 2.0) * 3 * (thick - 1)), 0, 1)
    if glow_amt > 0:
        light = glow(band, 16) * 1.8 + glow(band, 60) * 1.4
        img = screen(img, SUNLIGHT, np.clip(light, 0, 1) * 0.85 * glow_amt)
    img = over(img, col, band)
    if deco_amt > 0:
        _, _, deco = halo_layer(cx, cy, rw, tilt, t, GOLD)
        img = over(img, GOLD * 0.9, deco * 0.9 * deco_amt)
    return img

# ---------- wings (cached once fully grown) ----------
_WCACHE = {}
def wings(p):
    p = round(float(p), 3)
    if p >= 1 and "full" in _WCACHE: return _WCACHE["full"]
    l = wing_layer(-1, p); r = wing_layer(1, p)
    if p >= 1: _WCACHE["full"] = (l, r)
    return l, r

# ---------- text cards (from forced alignment of her voice note) ----------
CARDS = [
    (1.03, 4.35, "But I am not telling you the story of circles.", INK_M, 70),
    (4.45, 6.55, "Not today.", INK_M, 104),
    (6.65, 10.90, "I am telling you how to break the circle.", INK_M, 72),
    (11.45, 13.36, "How to find the close tangent", INK_M, 76),
    (13.39, 15.15, "and like a life boat", INK_M, 84),
    (15.25, 17.62, "sail away along the line to a new world.", INK_M, 72),
    (17.66, 18.62, "But you say,", INK_B, 116),
    (18.66, 20.30, "there is no way", INK_B, 92),
    (20.38, 24.60, "to escape the cycle of constant birth and death.", INK_B, 74),
    (24.62, 29.45, "You say, only few have mastered it.", INK_B, 74),
    (29.52, 32.85, "A select few.", INK_M, 108),
]
CARD_IMG = [ransom(txt, col, size=sz, seed=100 + i, max_w=800) for i, (_, _, txt, col, sz) in enumerate(CARDS)]
NAME_IMG = ransom("Della Antony", INK_M, size=96, seed=21, max_w=900)
LOGO_IMG = logo_sticker(260)
TEXT_CX, TEXT_BOTTOM = 425, 1430

def pop(t, t0):
    u = (t - t0) / 0.24
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.55 + 0.53 * np.sin(u * np.pi * 0.62) / np.sin(np.pi * 0.62) * (1 - 0.08 * u) if u < 0.75 else lerp(1.06, 1.0, (u - 0.75) / 0.25)

def draw_text(img, t):
    for (a, b, *_), im in zip(CARDS, CARD_IMG):
        if a - 0.01 <= t < b:
            sc = pop(t, a)
            al = min(1.0, (b - t) / 0.1)
            cy = TEXT_BOTTOM - im.height / 2
            img = paste_rgba(img, im, TEXT_CX, cy, scale=max(sc, 0.05), alpha=al)
    return img

# ---------- frame ----------
def frame(t):
    s, px, py, sx, sy, sun = camera(t)
    cx, cy, rw, tilt, rot, col, gl, dc = ring_state(t, s, sun)
    end_mix = ramp(t, 32.9, 33.5)
    img = None
    if t < 24.4 and end_mix < 1:
        # painting stage (ring removed; it is drawn on its own layer)
        dz = ramp(t, 20.5, 24.3)
        base = warp(NORING_PIL, px, py, s * (1 + 0.22 * dz), sx, sy)
        base = screen(base, YELLOW * 0.9 + 0.1, rays(sun[0], sun[1], SUN_R * s, t, ramp(t, 5.5, 9.0)))
        fa = ramp(t, 12.4, 13.2) * (1 - ramp(t, 19.0, 20.0))
        if fa > 0:
            wink = np.sin(np.pi * np.clip((t - 16.85) / 0.6, 0, 1)) ** 0.7
            frgb, fal = face_layer(sun[0], sun[1], SUN_R * s, wink)
            base = over(base, frgb, fal * fa)
        if dz > 0:  # reverse-disperse dissolve to paper: specks drift out and vanish
            key = 0.62 * NOISE + 0.38 * np.clip(np.hypot(*np.mgrid[:H, :W][::-1] - np.array([sun[0], sun[1]])[:, None, None]) / 1400, 0, 1)
            keep = np.clip((key - (dz * 1.3 - 0.15)) / 0.12, 0, 1)
            edge = np.clip(1 - np.abs(key - (dz * 1.3 - 0.15)) / 0.03, 0, 1) * (np.random.default_rng(int(t * 30)).random((H, W)) < 0.35)
            base = PAPER * (1 - keep[..., None]) + base * keep[..., None]
            base = over(base, SUNLIGHT, edge * 0.8)
        img = base
    else:
        img = PAPER.copy()
    # wings (behind halo)
    wp = ramp(t, 24.7, 28.5) if t < 28.5 else 1.0
    if t >= 24.7 and end_mix < 1:
        (lr, la), (rr, ra) = wings(wp if t < 28.5 else 1.0)
        breathe = 0.0
        img = over(img, lr, la); img = over(img, rr, ra)
        da = ramp(t, 25.5, 27.0)
        drgb, dal = doodles(t); img = over(img, drgb, dal * da)
    if end_mix < 1:
        img = draw_ring(img, t, cx, cy, rw, tilt, rot, col, gl, dc)
    # end card: full painting, logo, name
    if end_mix > 0:
        endc = warp(PAINT_PIL, PAD + PW / 2, PAD + PH / 2, H / PH, 540, 960)
        img = img * (1 - end_mix) + endc * end_mix
        lp = pop(t, 33.6)
        if lp > 0: img = paste_rgba(img, LOGO_IMG, 470, 640, scale=lp)
        npp = pop(t, 33.95)
        if npp > 0: img = paste_rgba(img, NAME_IMG, 470, 880, scale=npp)
    img = draw_text(img, t)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        ts = [1, 5, 8.5, 12, 14.5, 17.15, 19.5, 21.5, 23.0, 24.5, 26.5, 29, 31, 33.2, 34.8]
        with Pool(4) as p: fr = p.map(frame, ts)
        th = [Image.fromarray(f).resize((270, 480)) for f in fr]
        sheet = Image.new("RGB", (270 * 5, 480 * 3), "white")
        for k, im in enumerate(th): sheet.paste(im, ((k % 5) * 270, (k // 5) * 480))
        sheet.save("contact_sheet.jpg", quality=88)
        for t_, f in zip(ts, fr): Image.fromarray(f).save(f"/tmp/claude-0/-home-user-Practice/6b8363a1-55c5-5d6e-9fc0-4f4c21b30016/scratchpad/f_{t_}.jpg", quality=90)
    else:
        n = int(DUR * FPS)
        enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "frames.mp4"], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for k, b in enumerate(p.imap(job, range(n), chunksize=4)):
                enc.stdin.write(b)
                if k % 90 == 0: print(k, "/", n, flush=True)
        enc.stdin.close(); enc.wait()
