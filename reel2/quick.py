"""Quick ~10 s cut of Reel 2: same frames, faster timeline, no text cards, silent (like the tangent clip)."""
import subprocess, numpy as np
from multiprocessing import Pool
import render
render.CARDS[:] = []; render.CARD_IMG[:] = []
# new time u -> original time t (piecewise linear)
U = [0.0, 2.0, 4.0, 6.5, 9.0, 10.0]
T = [0.0, 10.5, 19.0, 24.4, 29.0, 31.0]
def job(i): return render.frame(float(np.interp(i / 30, U, T))).tobytes()
if __name__ == "__main__":
    enc = subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r","30","-i","-",
        "-c:v","libx264","-crf","18","-preset","slow","-pix_fmt","yuv420p","-movflags","+faststart","reel2_quick.mp4"], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for b in p.imap(job, range(300), chunksize=4): enc.stdin.write(b)
    enc.stdin.close(); enc.wait()
