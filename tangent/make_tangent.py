"""Tangent shot for the 15 s Reel 1 cut: a straight line touches the painted sun at exactly one point; a paper boat sails along it into the blue.
Built on the real painting. Silent 8 s clip, 1080x1920 @30."""
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
os.chdir("/home/user/Practice/reel2"); sys.path.insert(0, ".")
import lib
from lib import W, H, SC, SUN_R, rays, YELLOW, SUNLIGHT
OUT = "/home/user/Practice/tangent/"
FPS, DUR = 30, 8.0
PAINT_PIL = Image.fromarray((np.clip(lib.PAINT, 0, 1) * 255).astype(np.uint8))
rng = np.random.default_rng(5)
GRAIN = rng.random((H, W)).astype(np.float32)

def ease(x): x = float(np.clip(x, 0, 1)); return x * x * (3 - 2 * x)

# --- camera: sun left of centre so the blue field is on screen; slow push-in ---
SUNX, SUNY = 210, 600
def cam(t): return 0.70 + 0.04 * ease(t / DUR)
def to_screen(px, py, s): return SUNX + (px - SC[0]) * s, SUNY + (py - SC[1]) * s
def warp(s):
    A = 1 / s
    coeffs = (A, 0, SC[0] - A * SUNX, 0, A, SC[1] - A * SUNY)
    return np.asarray(PAINT_PIL.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)).astype(np.float32) / 255

# --- paper boat in painting magenta (flat folded-paper facets) ---
def make_boat(w=250):
    k = 4; bw, bh = 260 * k, 135 * k
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda pts: [(x * k, y * k) for x, y in pts]
    d.polygon(P([(130, 4), (48, 72), (130, 72)]), fill=(196, 78, 124, 255))     # sail left, lit
    d.polygon(P([(130, 4), (130, 72), (212, 72)]), fill=(150, 40, 88, 255))     # sail right, shade
    d.polygon(P([(22, 72), (130, 72), (130, 128), (62, 128)]), fill=(173, 51, 97, 255))   # hull left
    d.polygon(P([(130, 72), (238, 72), (198, 128), (130, 128)]), fill=(136, 34, 78, 255))  # hull right
    d.line(P([(130, 4), (130, 128)]), fill=(214, 120, 158, 255), width=2 * k)   # centre fold highlight
    d.line(P([(22, 72), (238, 72)]), fill=(120, 28, 70, 255), width=1 * k)
    a = np.asarray(im).astype(np.float32); n = (rng.random(a.shape[:2]) - 0.5) * 16   # paper grain
    a[..., :3] = np.clip(a[..., :3] + n[..., None], 0, 255)
    im = Image.fromarray(a.astype(np.uint8), "RGBA").resize((w, int(w * bh / bw)), Image.LANCZOS)
    return im
BOAT = make_boat(230)
BW, BH = BOAT.size

def paste(base, im, x, y_base, rot=0.0, shadow=True):
    """paste RGBA im with its bottom-centre at (x, y_base)"""
    im2 = im.rotate(rot, resample=Image.BICUBIC, expand=True, center=(im.width / 2, im.height))
    px, py = int(x - im2.width / 2), int(y_base - im.height - (im2.height - im.height) / 2 * 0 - (im2.height - im.height))
    al = np.asarray(im2).astype(np.float32) / 255
    if shadow:
        sh = Image.new("L", im2.size, 0); sh.putalpha(0)
        sa = Image.fromarray((al[..., 3] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7))
        sa = np.asarray(sa).astype(np.float32) / 255 * 0.35
        blend(base, np.zeros((*sa.shape, 3), np.float32), sa, px + 7, py + 12)
    blend(base, al[..., :3], al[..., 3], px, py)

def blend(base, rgb, a, x, y):
    h, w = a.shape; x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x][..., None]; sr = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - sa) + sr * sa

def draw_line(base, y, xa, xb, width=10):
    if xb - xa < 2: return
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line([(xa, y), (xb, y)], fill=255, width=width)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(0.9))).astype(np.float32) / 255
    a = a * np.where(GRAIN > 0.16, 1.0, 0.45)           # crayon grain, line itself stays dead straight
    base[:] = base * (1 - a[..., None]) + np.array([0.07, 0.07, 0.085], np.float32) * a[..., None]

def frame(t):
    s = cam(t)
    f = warp(s)
    sx, sy = to_screen(SC[0], SC[1], s)
    f = lib.screen(f, YELLOW * 0.9 + 0.1, rays(sx, sy, SUN_R * s, t + 1.0, 0.75))
    ty = SC[1] + SUN_R                                   # bottom of the circle = the one touching point
    _, line_y = to_screen(SC[0], ty, s); line_y = int(round(line_y)); tx = int(round(sx))
    p = ease((t - 0.6) / 1.6)
    draw_line(f, line_y, tx - p * (tx + 20), tx + p * (W + 20 - tx))
    # contact sparkle: small golden ring at the single touching point
    q = (t - 2.0) / 0.9
    if 0 < q < 1:
        r = 14 + 40 * q; m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse((tx - r, line_y - r, tx + r, line_y + r), outline=255, width=4)
        a = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255 * (1 - q)
        f = lib.screen(f, SUNLIGHT, a)
    # boat: appears left of the contact point, then sails right along the line, over the touching point and into the blue
    if t > 2.4:
        pop = ease((t - 2.4) / 0.35)
        sail = ease((t - 3.2) / (7.6 - 3.2))
        x_start = tx - 190
        _, _ = 0, 0
        x_end_px, _ = to_screen(lib.PAD + 1540, ty, s)
        bx = x_start + (x_end_px - x_start) * sail
        bob = np.sin(t * 2.2) * 2.2 * (0.4 + sail)
        im = BOAT.resize((max(1, int(BW * pop)), max(1, int(BH * pop))), Image.LANCZOS) if pop < 1 else BOAT
        paste(f, im, bx, line_y + 3 + np.sin(t * 3.1) * 1.5 * sail, rot=bob)
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "stills":
        for t in (1.2, 2.6, 4.5, 7.4): Image.fromarray(frame(t)).save(f"/tmp/claude-0/-home-user-Practice/6b8363a1-55c5-5d6e-9fc0-4f4c21b30016/scratchpad/tg_{t}.png")
    else:
        enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT + "tangent_clip.mp4"], stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)):
            enc.stdin.write(frame(i / FPS).tobytes())
        enc.stdin.close(); enc.wait(); print("done")
