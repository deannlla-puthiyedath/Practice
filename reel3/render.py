"""Reel 3 renderer: Sunset (2) comes alive to Della's narration.
python3 render.py sheet -> contact_sheet.jpg (+ check frames)
python3 render.py full  -> frames.mp4 (silent)"""
import os, sys, json, subprocess
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
import stills                      # calm field, sticker, ripples, sea tiles, cut-letter cards (also loads Reel 2 lib)
from stills import lib, W, H, CUT, SUIT, SEA_INK, calm_field, ripples, sea_tiles

FPS, DUR = 30, 84.0
P = stills.P                        # painting, float 0..1, 1083 x 1390
PH, PW = P.shape[:2]
PAPER = lib.paper_bg()

# ---------------- grid geometry ----------------
VX = [125, 270, 425, 578, 735, 878, 1020, 1165, 1310]          # vertical lines
HY = [95, 245, 408, 555, 700, 848, 990]                         # horizontal lines (sky + sea)
XS = [0] + VX + [PW]
SEA_Y = [408, 555, 700, 848, 990, PH]
BOXES = [(r, c) for r in range(5) for c in range(10)]          # sea boxes
STILL = (2, 5)                                                  # box 26 (row 3, col 6 in 1-based)
def box_rect(r, c, inset=0):
    return XS[c] + inset, SEA_Y[r] + inset, XS[c + 1] - inset, SEA_Y[r + 1] - inset
B26 = box_rect(*STILL)
B26_C = ((B26[0] + B26[2]) / 2, (B26[1] + B26[3]) / 2)

def _u8(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
def _f(im): return np.asarray(im).astype(np.float32) / 255

# soft interior mask + per-box id for the churn
yy, xx = np.mgrid[:PH, :PW].astype(np.float32)
BOX_ID = np.full((PH, PW), -1, np.int16)
INNER = np.zeros((PH, PW), np.float32)
for k, (r, c) in enumerate(BOXES):
    x0, y0, x1, y1 = box_rect(r, c, 13)
    BOX_ID[y0:y1, x0:x1] = k
    if (r, c) != STILL:
        INNER[y0:y1, x0:x1] = 1
INNER = _f(_u8(INNER).filter(ImageFilter.GaussianBlur(5)))
rng = np.random.default_rng(26)
PH1, PH2 = rng.uniform(0, 2 * np.pi, (2, len(BOXES))).astype(np.float32)
SPD = rng.uniform(0.75, 1.35, len(BOXES)).astype(np.float32)
_bid = np.where(BOX_ID < 0, 0, BOX_ID)
PH1_MAP, PH2_MAP, SPD_MAP = PH1[_bid], PH2[_bid], SPD[_bid]

# painting with the grid lines filled in (the "one open ocean" under the tape):
# each gap is rebuilt by blending the paint mirrored from both sides, so it reads as continuous brushwork
def _mirror_fill(img):
    out = img.copy()
    for x in VX:
        x0, x1 = max(1, x - 14), min(PW - 1, x + 14); w = x1 - x0
        for i in range(w):
            k = (i + 0.5) / w
            left = img[:, max(0, x0 - 1 - i)]; right = img[:, min(PW - 1, x1 + i)]
            out[:, x0 + i] = left * (1 - k) + right * k
    for y in HY:
        y0, y1 = max(1, y - 13), min(PH - 1, y + 13); h = y1 - y0
        for i in range(h):
            k = (i + 0.5) / h
            up = out[max(0, y0 - 1 - i)]; dn = out[min(PH - 1, y1 + i)]
            out[y0 + i] = up * (1 - k) + dn * k
    return out
NOGRID = _mirror_fill(P)
NOGRID = np.asarray(_u8(NOGRID).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255
# each line as a strip of tape (rgb + feathered alpha), so it can lift and drop back
LINES = []
for i, x in enumerate(VX):
    x0, x1 = max(0, x - 14), min(PW, x + 14)
    a = np.zeros((PH, x1 - x0), np.float32); a[:, 3:-3] = 1
    LINES.append(("v", x0, 0, P[:, x0:x1].copy(), _f(_u8(a).filter(ImageFilter.GaussianBlur(2)))))
for y in HY:
    y0, y1 = max(0, y - 13), min(PH, y + 13)
    a = np.zeros((y1 - y0, PW), np.float32); a[3:-3, :] = 1
    LINES.append(("h", 0, y0, P[y0:y1].copy(), _f(_u8(a).filter(ImageFilter.GaussianBlur(2)))))
LINE_ORDER = rng.permutation(len(LINES))

# box 26 outline glow
_o = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(_o).rectangle([B26[0] + 9, B26[1] + 9, B26[2] - 9, B26[3] - 9], outline=255, width=5)
OUTLINE = _f(_o.filter(ImageFilter.GaussianBlur(4))) * 1.6

# ---------------- timing helpers ----------------
def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def ramp(t, a, b): return float(ease((t - a) / (b - a)))
def lerp(a, b, k): return a + (b - a) * k
def bump(x, w=0.8): return float(np.exp(-(x * x) / w))

# camera keyframes: t, scale, painting centre x, y, screen centre y
KEYS = [(0.0, 1.80, 806, 541, 960), (2.7, 1.80, 806, 541, 960), (5.8, 2.60, 806, 690, 960),
        (10.6, 2.75, 806, 700, 960), (13.0, 2.10, 790, 300, 960), (13.6, 2.10, 790, 300, 960),
        (15.2, 0.777, 695, 541, 1010), (35.7, 0.80, 695, 541, 1010), (42.0, 9.0, *B26_C, 960),
        (47.85, 9.2, *B26_C, 960), (50.6, 0.80, 695, 541, 1010), (60.4, 0.80, 695, 541, 1010),
        (63.2, 9.0, *B26_C, 960), (DUR, 9.0, *B26_C, 960)]
def camera(t):
    for (t0, s0, x0, y0, q0), (t1, s1, x1, y1, q1) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            k = ease((t - t0) / max(t1 - t0, 1e-6))
            s = float(np.exp(lerp(np.log(s0), np.log(s1), k)))
            # when zooming, keep the target point steady on screen (feels like sinking in, not sliding)
            kp = k if s1 <= s0 else ease(np.clip((np.log(s) - np.log(s0)) / (np.log(s1) - np.log(s0) + 1e-9), 0, 1))
            return s, lerp(x0, x1, kp), lerp(y0, y1, kp), lerp(q0, q1, kp)
    return KEYS[-1][1:]

def churn_amp(t):
    if t < 13.6: return 1.0
    if t < 18.2: return 0.35
    if t < 27.9: return 0.6
    if t < 35.7: return 0.3
    if t < 47.85: return 0.3 * (1 - ramp(t, 35.7, 38))
    if t < 58.1: return 1.35 * ramp(t, 47.85, 49)
    return 1.35 * (1 - ramp(t, 58.1, 59.2))

# ---------------- painting-space frame ----------------
def tape_layer(t):
    """Grid lines peel off (15.2-16.4), open ocean (to 16.9), drop back and seal (16.9-18.2)."""
    if not (15.2 <= t < 18.3): return None
    img = NOGRID.copy()
    n = len(LINES)
    for rank, idx in enumerate(LINE_ORDER):
        kind, x0, y0, rgb, a = LINES[idx]
        up = ramp(t, 15.2 + rank * 0.04, 15.2 + rank * 0.04 + 0.4)
        down = ramp(t, 16.9 + rank * 0.07, 16.9 + rank * 0.07 + 0.35)
        u = up * (1 - down)                       # 0 = sealed, 1 = lifted away
        if u > 0.98: continue
        off = int(-60 * u)                         # lifts up / sideways
        al = a * (1 - u)
        hgt, wid = a.shape
        X0, Y0 = (x0 + off, y0) if kind == "v" else (x0, y0 + off)
        sx0, sy0 = max(0, -X0), max(0, -Y0)
        X1, Y1 = min(PW, X0 + wid), min(PH, Y0 + hgt)
        if X1 <= max(X0, 0) or Y1 <= max(Y0, 0): continue
        sub_a = al[sy0:sy0 + Y1 - max(Y0, 0), sx0:sx0 + X1 - max(X0, 0)][..., None]
        sub_c = rgb[sy0:sy0 + Y1 - max(Y0, 0), sx0:sx0 + X1 - max(X0, 0)]
        reg = img[max(Y0, 0):Y1, max(X0, 0):X1]
        img[max(Y0, 0):Y1, max(X0, 0):X1] = reg * (1 - sub_a * 0.25 * u) * (1 - sub_a) + sub_c * sub_a  # faint shadow while lifted
    return img

def bilinear(img, x, y):
    x = np.clip(x, 0, PW - 1.001); y = np.clip(y, 0, PH - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]; c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def lift_boxes(img, t):
    """Pops (secrets, 18.2-27.9) and the travelling wave (oceans, 27.9-35.7). Box 26 never moves."""
    lifts = []
    if 18.2 <= t < 28.6:
        order = POP_ORDER
        for j, k in enumerate(order):
            t0 = 18.4 + j * 0.31
            u = (t - t0) / 0.9
            if 0 < u < 1: lifts.append((k, np.sin(np.pi * u), POP_ROT[k]))
    if 27.9 <= t < 35.9:
        w = (t - 28.2) * 2.4
        fade = ramp(t, 27.9, 28.4) * (1 - ramp(t, 35.2, 35.9))
        for k, (r, c) in enumerate(BOXES):
            e = max(bump((w % 14) - c - 0.4 * r, 1.0), bump(((w + 7) % 14) - c - 0.4 * r, 1.0) * 0.0) * fade
            if e > 0.03: lifts.append((k, e, 0.0))
    if not lifts: return img
    im = _u8(img).convert("RGBA")
    for k, e, rot in lifts:
        if BOXES[k] == STILL: continue
        x0, y0, x1, y1 = box_rect(*BOXES[k], 9)
        tile = im.crop((x0, y0, x1, y1))
        sc = 1 + 0.13 * e
        tile = tile.resize((int(tile.width * sc), int(tile.height * sc)), Image.BICUBIC)
        bd = Image.new("RGBA", (tile.width + 8, tile.height + 8), (250, 249, 244, 255)); bd.paste(tile, (4, 4))
        bd = bd.rotate(rot * e, expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", bd.size, (10, 35, 80, 0)); sh.putalpha(bd.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.45 * e))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        im.alpha_composite(sh, (int(cx - bd.width / 2 + 6 * e), int(cy - bd.height / 2 + 9 * e)))
        im.alpha_composite(bd, (int(cx - bd.width / 2), int(cy - bd.height / 2)))
    return _f(im.convert("RGB"))

POP_ORDER = [k for k in rng.permutation(len(BOXES)) if BOXES[k] != STILL][:31]
POP_ROT = rng.uniform(-8, 8, len(BOXES))

def painting_at(t):
    base = tape_layer(t)
    if base is None: base = P
    A = churn_amp(t) * 4.2
    if A > 0.01:
        tt = np.float32(t)
        dx = A * INNER * np.sin(2 * np.pi * 0.5 * SPD_MAP * tt + PH1_MAP + yy * 0.055)
        dy = 0.75 * A * INNER * np.cos(2 * np.pi * 0.42 * SPD_MAP * tt + PH2_MAP + xx * 0.045)
        img = bilinear(base, xx + dx, yy + dy)
        img = img * (1 + 0.035 * churn_amp(t) * INNER * np.sin(2 * np.pi * 0.3 * tt + PH2_MAP))[..., None]
    else:
        img = base.copy()
    img = lift_boxes(img, t)
    g = ramp(t, 3.0, 4.2) * (1 - ramp(t, 10.6, 11.6)) + 0.6 * ramp(t, 51, 52) * (1 - ramp(t, 60.4, 61.5))
    if g > 0:
        img = lib.screen(img, np.array([1.0, 0.98, 0.9]), np.clip(OUTLINE * g, 0, 1))
    return np.clip(img, 0, 1)

# ---------------- screen-space ----------------
COVER = Image.new("L", (PW, PH), 255)
def warp(img_f, s, cx, cy, sy):
    a, d = 1 / s, 1 / s
    coeffs = (a, 0, cx - a * W / 2, 0, d, cy - d * sy)
    pim = _u8(img_f).transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
    cov = COVER.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
    return _f(pim), _f(cov)

def painting_view(t):
    s, cx, cy, sy = camera(t)
    calm = ramp(np.log(s), np.log(3.5), np.log(7.5))
    if calm >= 1: return calm_field(t * 0.35), s
    pimg, cov = warp(painting_at(t), s, cx, cy, sy)
    sh = _f(_u8(cov).filter(ImageFilter.GaussianBlur(14)))
    sh = np.roll(np.roll(sh, 10, 0), 6, 1)
    bg = PAPER * (1 - 0.28 * sh * (1 - cov))[..., None]
    img = bg * (1 - cov[..., None]) + pimg * cov[..., None]
    if calm > 0: img = img * (1 - calm) + calm_field(t * 0.35) * calm
    return img, s

# ---------------- cards ----------------
CARDS = [(0.0, 2.65, "Stop fixing yourself."), (2.65, 5.8, "Watch what this box does."),
         (5.8, 8.85, "Every box of sea is moving."), (8.85, 10.65, "Only one is still."),
         (10.65, 13.6, "It began as a dream of the sea."), (13.6, 18.2, "So I kept the colours in boxes."),
         (18.2, 21.75, "We bury secrets in us"), (21.75, 27.9, "and believe we all hold the same ones."),
         (27.9, 31.45, "From a story I wrote."), (31.45, 35.75, "You can't drown the oceans."),
         (35.75, 38.7, "We receive the grace of acceptance."), (38.7, 42.85, "With acceptance, comes a calm."),
         (42.85, 47.85, "Change comes through being, not resisting."), (47.85, 58.1, "Stop fixing yourself."),
         (58.1, 68.2, "The grace of acceptance."), (68.2, 73.3, "Change comes through being, not resisting."),
         (73.3, 79.0, "We listen with a stillness.")]
CARD_IMG = [lib.ransom(txt, SEA_INK, size=68, seed=i * 7 + 3, max_w=760) for i, (_, _, txt) in enumerate(CARDS)]
CARD_X, CARD_Y = (W - 230) / 2 + 40, 340

def pop(t, t0):
    u = (t - t0) / 0.22
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 0.8 + 0.28 * np.sin(u * np.pi * 0.7) if u < 0.7 else lerp(1.06, 1.0, (u - 0.7) / 0.3)

def draw_cards(img, t):
    for (a, b, _), im in zip(CARDS, CARD_IMG):
        if a <= t < b:
            al = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
            img = lib.paste_rgba(img, im, CARD_X, CARD_Y + im.height / 2 - 90, scale=pop(t, a), alpha=al)
    return img

# ---------------- swimsuit + tiles + end card ----------------
SUIT_L = SUIT.resize((int(SUIT.width * 1.15), int(SUIT.height * 1.15)), Image.LANCZOS)
SUIT_A = np.asarray(SUIT_L).astype(np.float32) / 255
TILES = sea_tiles(); np.random.default_rng(11).shuffle(TILES)
_r = np.random.default_rng(11)
SLOTS = [(x, y) for y in range(140, H, 210) for x in range(90, W, 225)
         if not (230 < x < 850 and 470 < y < 1700) and not (190 < y < 480)]
TILE_IMG = []
for (x, y), t_ in zip(SLOTS, TILES):
    t_ = t_.resize((190, 182)).rotate(_r.uniform(-6, 6), expand=True, resample=Image.BICUBIC)
    pad = Image.new("RGBA", (t_.width + 14, t_.height + 14), (0, 0, 0, 0))
    wm = t_.split()[3].filter(ImageFilter.MaxFilter(13))
    pad.paste(Image.new("RGBA", wm.size, (252, 250, 244, 255)), (7, 7), wm); pad.alpha_composite(t_, (7, 7))
    TILE_IMG.append((x + int(_r.integers(-12, 12)), y + int(_r.integers(-10, 10)), pad, _r.uniform(0, 6.28)))
WATER_Y = 1390
LOGO = stills.LOGO
NAME = lib.ransom("Della Antony", SEA_INK, size=88, seed=21, max_w=900)

def swimsuit_layer(img, t):
    if t < 63.4: return img
    rise = ramp(t, 63.6, 66.8); settle = ramp(t, 68.2, 70.2)
    h = SUIT_L.height
    frac = lerp(0.62 * rise + 0.008 * np.sin(t * 2.2) * ramp(t, 66.0, 67.0), 1.0, settle)
    top_rise = WATER_Y - frac * h
    cy_rise = top_rise + h / 2
    cy = lerp(cy_rise, 1260, settle)
    a = SUIT_A.copy()
    under = np.clip((np.arange(h)[:, None] + (cy - h / 2) - WATER_Y) / 60.0, 0, 1) * (1 - settle)
    a[..., 3] *= (1 - 0.9 * under)
    if rise <= 0: return img
    a[..., 3] *= min(1.0, rise * 4)
    img = lib.paste_rgba(img, _u8(a), W / 2, cy)
    rp = (1 - settle) * min(1.0, rise * 3)
    if rp > 0.01:
        img = img * (1 - rp) + ripples(img, W / 2, WATER_Y, t=(t - 63.6) * 0.8) * rp
    return img

def tiles_layer(img, t):
    if t < 68.4: return img
    come = ramp(t, 68.4, 70.8); drift = 1 - ramp(t, 73.3, 74.4)
    for i, (x, y, im, ph) in enumerate(TILE_IMG):
        k = ramp(t, 68.4 + i * 0.05, 69.6 + i * 0.05)
        ox = (x - W / 2) * 0.6 * (1 - k); oy = 420 * (1 - k)          # float in from the water
        fx = 14 * np.sin(t * 1.1 + ph) * drift * come; fy = 10 * np.cos(t * 0.9 + ph) * drift * come
        if k > 0: img = lib.paste_rgba(img, im, x + ox + fx, y + oy + fy, alpha=k)
    return img

def end_card(t):
    img = PAPER.copy()
    lp = pop(t, 79.4)
    if lp > 0: img = lib.paste_rgba(img, LOGO, W / 2, 800, scale=lp * 1.25)
    npp = pop(t, 79.9)
    if npp > 0: img = lib.paste_rgba(img, NAME, W / 2, 1070, scale=npp)
    return img

def frame(t):
    img, s = painting_view(t)
    img = swimsuit_layer(img, t)
    img = tiles_layer(img, t)
    img = draw_cards(img, t)
    e = ramp(t, 78.9, 79.5)
    if e > 0: img = img * (1 - e) + end_card(t) * e
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def job(i): return frame(i / FPS).tobytes()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sheet"
    if mode == "sheet":
        ts = [float(v) for v in sys.argv[2:]] or [0.5, 4.5, 9.5, 12.5, 15.0, 16.6, 20.5, 30.5,
                                                   37.0, 40.0, 45.0, 54.0, 59.5, 65.5, 71.5, 77.0, 82.0]
        with Pool(4) as p: fr = p.map(frame, ts)
        cols = 6; rows = (len(ts) + cols - 1) // cols
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
