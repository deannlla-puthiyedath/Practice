"""Trial variant of Reel 1 ("circles"): line 1 on frame 0, sun orbit from 0.0, silent head removed.
Built from the finished Reel 1 file + Reel 2's cut-letter renderer. Segment = new frames 0..N-1; rest is spliced in by ffmpeg."""
import subprocess, sys, numpy as np
from PIL import Image, ImageFilter
import lib

R1 = "/root/.claude/uploads/6b8363a1-55c5-5d6e-9fc0-4f4c21b30016/2fcbe14c-della_antony_reel_final.mp4"
W, H, FPS = 1080, 1920, 30
T0 = 0.80                      # silent head removed: new t = orig t - 0.80
LINE_START, LINE_END = 2.55, 6.20   # baked line-1 span in the finished Reel 1 (orig time)
SUN_START = 2.50               # baked sun takes over here
N = int(round((LINE_END - T0) * FPS))   # 162 frames patched
PERIOD = 2.9
RX0, RY0, RX1, RY1 = 150, 204, 950, 470   # patch rect covering the baked tiles + shadow

# ---- sun path measured from Reel 1 (orig time, px) ----
CP = [(2.5,1005,820),(2.6,1001,881),(2.7,985,939),(2.8,959,994),(2.9,903,1042),(3.0,760,1117),(3.1,677,1139),(3.2,590,1156),
      (3.3,499,1155),(3.4,418,1144),(3.5,342,1047),(3.9,335,830),(4.3,345,640),(4.5,389,580),(4.6,431,579),(4.7,530,580),
      (4.8,651,574),(4.9,736,579),(5.0,887,609),(5.1,946,635),(5.2,981,683),(5.3,996,741),(5.4,1005,820)]
cp = np.array(CP); tt = np.linspace(2.5, 5.4, 291, endpoint=False)
px = np.interp(tt, cp[:,0], cp[:,1]); py = np.interp(tt, cp[:,0], cp[:,2])
k = np.ones(11)/11
px = np.convolve(np.r_[px[-5:], px, px[:5]], k, "valid"); py = np.convolve(np.r_[py[-5:], py, py[:5]], k, "valid")
def sun_pos(o):
    ph = ((o - 2.5) % PERIOD) / PERIOD * len(px)
    i = int(ph) % len(px); j = (i + 1) % len(px); f = ph - int(ph)
    return px[i]*(1-f)+px[j]*f, py[i]*(1-f)+py[j]*f

SUN = Image.open("sun_sprite.png").convert("RGBA")

# ---- line 1 in Reel-1 tile style (mixed inks), drawn with Reel 2's cut-letter renderer ----
INKS = [(173,51,97),(20,20,22),(36,70,127),(173,51,97),(20,20,22)]
TXT = lib.ransom("My mission is about circles.", lambda r: INKS[r.integers(len(INKS))], size=62, seed=7, max_w=790)
print("text size", TXT.size, flush=True)
TX, TY = 548, 335

def paste(base, im, cx, cy):
    x, y = int(round(cx - im.width/2)), int(round(cy - im.height/2))
    x0,y0,x1,y1 = max(x,0),max(y,0),min(x+im.width,W),min(y+im.height,H)
    if x1<=x0 or y1<=y0: return
    a = np.asarray(im).astype(np.float32)/255
    sub = a[y0-y:y1-y, x0-x:x1-x]
    al = sub[...,3:4]
    base[y0:y1,x0:x1] = base[y0:y1,x0:x1]*(1-al) + sub[...,:3]*255*al

def readframes(args, n):
    p = subprocess.Popen(["ffmpeg","-loglevel","error"]+args+["-f","rawvideo","-pix_fmt","rgb24","-"], stdout=subprocess.PIPE)
    sz = W*H*3 if "-vf" not in args else None
    return p

# clean plate: region of frames just before the baked text appears (orig 1.0-2.5, no text yet), looped
pl = subprocess.run(["ffmpeg","-loglevel","error","-ss","1.0","-t","1.5","-i",R1,"-vf",f"fps=30,crop={RX1-RX0}:{RY1-RY0}:{RX0}:{RY0}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
pw, ph_ = RX1-RX0, RY1-RY0
PLATE = np.frombuffer(pl, np.uint8).reshape(-1, ph_, pw, 3).astype(np.float32)
print("plate frames", len(PLATE), flush=True)
fm = np.zeros((ph_, pw), np.float32); fm[16:-16, 16:-16] = 1
FEATH = (np.asarray(Image.fromarray((fm*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))).astype(np.float32)/255)[...,None]

dec = subprocess.Popen(["ffmpeg","-loglevel","error","-ss",str(T0),"-i",R1,"-frames:v",str(N),"-f","rawvideo","-pix_fmt","rgb24","-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","-",
                        "-c:v","libx264","-crf","14","-preset","fast","-pix_fmt","yuv420p","seg.mp4"], stdin=subprocess.PIPE)
for n in range(N):
    buf = dec.stdout.read(W*H*3)
    if len(buf) < W*H*3: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    o = T0 + n/FPS
    if o >= LINE_START - 0.02:      # erase the baked tiles
        reg = f[RY0:RY1, RX0:RX1]
        f[RY0:RY1, RX0:RX1] = reg*(1-FEATH) + PLATE[n % len(PLATE)]*FEATH
    paste(f, TXT, TX, TY)           # line 1: fully on screen from frame 0
    if o < SUN_START:               # sun orbit starts at t=0, hands over to the baked sun at the same spot
        sx, sy = sun_pos(o)
        sp = SUN.rotate(-50*(n/FPS), resample=Image.BICUBIC)
        paste(f, sp, sx, sy)
    enc.stdin.write(np.clip(f,0,255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("segment done", n+1)
