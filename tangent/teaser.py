"""Teaser for non-followers: tangent clip + Della's voice line + Reel 2 score + her exact words as cut letters from frame 0."""
import os, sys, subprocess, numpy as np
os.chdir("/home/user/Practice/reel2"); sys.path.insert(0, ".")
import lib
from lib import W, H, ransom, paste_rgba
OUT = "/home/user/Practice/tangent/"
FPS, N = 30, 240
VOICE_T0 = 11.43      # voice note offset: "How to find..." starts ~0.1 s into the teaser
M = (173, 51, 97)
# her exact words, timed to the forced alignment of the voice note (minus VOICE_T0)
CARDS = [(0.00, 1.95, "How to find the close tangent", 82),
         (1.97, 3.88, "and like a life boat", 90),
         (3.92, 6.55, "sail away along the line to a new world.", 76)]
IMGS = [ransom(t, M, size=sz, seed=300 + i, max_w=790) for i, (_, _, t, sz) in enumerate(CARDS)]
NAME = ransom("Della Antony", M, size=84, seed=21, max_w=800)
TX, TCY = 425, 1270
def pop(t, t0, first=False):
    if first: return 1.0
    u = (t - t0) / 0.22
    return 0.0 if u <= 0 else (1.0 if u >= 1 else 0.6 + 0.4 * np.sin(u * np.pi / 2) + 0.06 * np.sin(u * np.pi))
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", OUT + "tangent_clip.mp4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", OUT + "teaser_video.mp4"], stdin=subprocess.PIPE)
for n in range(N):
    f = np.frombuffer(dec.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    t = n / FPS
    for i, ((a, b, _, _), im) in enumerate(zip(CARDS, IMGS)):
        if a <= t < b:
            al = min(1.0, (b - t) / 0.1)
            f = paste_rgba(f, im, TX, TCY, scale=max(pop(t, a, first=(i == 0)), 0.05), alpha=al)
    if t >= 6.6:
        f = paste_rgba(f, NAME, TX, TCY, scale=max(pop(t, 6.6), 0.05))
    enc.stdin.write((np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("video ok")
