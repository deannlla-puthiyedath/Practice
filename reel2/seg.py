import subprocess
from multiprocessing import Pool
import render
A, B = 372, 601
def job(i): return render.frame(i / 30).tobytes()
if __name__ == "__main__":
    enc = subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r","30","-i","-","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","seg.mp4"],stdin=subprocess.PIPE)
    with Pool(4) as p:
        for b in p.imap(job, range(A, B), chunksize=4): enc.stdin.write(b)
    enc.stdin.close(); enc.wait()
