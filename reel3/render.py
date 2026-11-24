"""Reel 3 full video (silent, text timed). `python3 render.py` -> reel3_silent.mp4 (1080x1920, 30 fps, H.264)."""
import os, subprocess, numpy as np
from PIL import Image
import board as B

FPS, DUR = 30, 31.0
OUT = os.path.join(B.HERE, "reel3_silent.mp4")
ease = lambda x: (lambda c: c * c * (3 - 2 * c))(min(max(x, 0.0), 1.0))
lerp = lambda a, b, k: a + (b - a) * k

W_MED, W_OFF, W_CRY, W_STI = B.room("meditate"), B.room("coatoff"), B.room("crayon"), B.room("stitch")
BOU, JEW, MIR, END = B.boutique(), B.jeweller(), B.mirror(), B.endcard()
GX, GY = B.GIRL[0], B.GIRL[1] - 660
# (start, end, text): cut-letter lines, popped in
LINES = [(0.4, 3.6, "Draw a box. Step in."), (3.8, 6.9, "Shut out the noise. Yours too."),
         (13.2, 16.0, "There's a child in there who never stopped playing."), (16.2, 19.0, "Hand her your problems and a crayon."),
         (19.3, 24.9, "She'll fix what your mind can't."), (25.3, 28.9, "There. I have just taught you how to meditate.")]
TXT = [B.r2.ransom(t, (173, 51, 97), size=76 if len(t) < 40 else 68, seed=100 + i, max_w=880) for i, (_, _, t) in enumerate(LINES)]


def zoom(img, k):  # slow push-in on a flat frame
    s = 1 + 0.06 * k; w, h = img.size
    cw, ch = w / s, h / s
    return img.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2))).resize((w, h), Image.BILINEAR)


def mix(a, b, k):
    return a if k <= 0 else b if k >= 1 else Image.blend(a, b, k)


def scene(t):
    if t < 11.0:  # close-up "Himalayas", then the pull-back into her room
        p = ease((t - 7.0) / 4.0)
        w = lerp(1000 - 40 * min(t / 7, 1), B.WW, p)
        fr = B.crop_frame(W_MED, lerp(GX, B.WW / 2, p), lerp(GY, B.WH / 2, p), w)
        return B.tilt_shift(fr, r=int(10 * (1 - p))) if p < 0.95 else fr
    if t < 13.2:  # zoom back in while the coat slides off
        p = ease((t - 11.0) / 1.4)
        a = B.crop_frame(W_MED, lerp(B.WW / 2, GX, p), lerp(B.WH / 2, 2900, p), lerp(B.WW, 1500, p))
        b = B.crop_frame(W_OFF, lerp(B.WW / 2, GX, p), lerp(B.WH / 2, 2900, p), lerp(B.WW, 1500, p))
        return mix(a, b, ease((t - 11.6) / 1.0))
    if t < 19.3:
        k = (t - 13.2) / 6.1
        cry = B.crop_frame(W_CRY, GX, 2960, 1500 - 80 * k)
        if t < 13.6:
            return mix(B.crop_frame(W_OFF, GX, 2900, 1500), cry, (t - 13.2) / 0.4)
        if t < 16.0:
            return cry
        return mix(cry, B.crop_frame(W_STI, GX, 2960, 1500 - 80 * k), (t - 16.0) / 0.4)
    if t < 22.0:
        return mix(B.crop_frame(W_STI, GX, 2960, 1420), zoom(BOU, (t - 19.3) / 2.7), (t - 19.3) / 0.4)
    if t < 25.3:
        return mix(zoom(BOU, 1), zoom(JEW, (t - 22.0) / 3.3), (t - 22.0) / 0.4)
    if t < 29.2:
        return mix(zoom(JEW, 1), zoom(MIR, (t - 25.3) / 3.9), (t - 25.3) / 0.4)
    return mix(zoom(MIR, 1), END, (t - 29.2) / 0.5)


def pop(u):
    u /= 0.22
    return 0.05 if u <= 0 else 1.0 if u >= 1 else 0.6 + 0.4 * np.sin(u * np.pi / 2) + 0.06 * np.sin(u * np.pi)


enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for n in range(int(DUR * FPS)):
    t = n / FPS
    fr = np.asarray(scene(t).convert("RGB")).astype(np.float32) / 255
    for (a, b, _), im in zip(LINES, TXT):
        if a <= t < b:
            y = 470 if a < 19 else 250
            fr = B.r2.paste_rgba(fr, im, 540, y, scale=max(pop(t - a), 0.05), alpha=min(1.0, (b - t) / 0.15))
    enc.stdin.write((np.clip(fr, 0, 1) * 255).astype(np.uint8).tobytes())
    if n % 150 == 0: print("t", round(t, 1), flush=True)
enc.stdin.close(); enc.wait(); print("done", OUT)
