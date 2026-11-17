"""Mix Della's voice with the violin score: the music steps back whenever she speaks and comes forward in her pauses.
python3 mix.py -> mix.wav (stereo 48 kHz, about -16.5 LUFS, true peak under -4 dBFS)"""
import subprocess, wave
import numpy as np

SR = 48000

def movavg(x, w):
    """centred moving average via cumulative sum (fast)"""
    c = np.cumsum(np.insert(x.astype(np.float64), 0, 0.0)); h = w // 2
    i = np.arange(len(x)); lo = np.clip(i - h, 0, len(x)); hi = np.clip(i + h + 1, 0, len(x))
    return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)

def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    return x.reshape(-1, ch) if ch > 1 else x

def lufs(x):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True).stderr.decode()
    return float(p.split("I:")[-1].split("LUFS")[0]), float(p.split("Peak:")[-1].split("dBFS")[0])

voice = load("voice.wav", 1); music = load("music.wav", 2)
n = int(84.0 * SR)
v = np.zeros(n, np.float32); v[:min(n, len(voice))] = voice[:n]
m = np.zeros((n, 2), np.float32); m[:min(n, len(music))] = music[:n]

# how loud is Della speaking right now? (100 Hz envelope, quick to duck, slow to come back)
w = int(0.12 * SR)
e = np.sqrt(movavg(v ** 2, w))
e100 = e[::SR // 100]
lvl = np.clip(e100 / (np.quantile(e100, 0.9) + 1e-9), 0, 1) ** 0.7
a_att, a_rel = np.exp(-0.01 / 0.04), np.exp(-0.01 / 0.5)
sm = np.zeros_like(lvl); c = 0.0
for i, x in enumerate(lvl):
    c = (a_att * c + (1 - a_att) * x) if x > c else (a_rel * c + (1 - a_rel) * x)
    sm[i] = c
env = np.interp(np.arange(n) / SR, np.arange(len(sm)) / 100, sm)
tt = np.arange(n) / SR
depth = np.where((tt >= 47.85) & (tt < 58.1), 0.28, 0.5)       # let the "pushing harder" crescendo stay audible
depth = movavg(depth, SR // 2)
gain = 1 - depth * env

# music sits about 7 LU under the voice on its own, then ducks a further 6 dB while she speaks
l_m, _ = lufs(m); l_v, _ = lufs(v[:, None])
g_music = 10 ** ((l_v - 7.0 - l_m) / 20)
mix = np.stack([v, v], 1) + m * (g_music * gain)[:, None]
# bring the whole thing to -16.5 LUFS, then catch any peak above -4 dBFS
l, _ = lufs(mix); mix *= 10 ** ((-16.5 - l) / 20)
ceil = 10 ** (-4.0 / 20)
for _ in range(3):
    pk = np.abs(mix).max()
    if pk <= ceil * 0.995: break
    mix = np.tanh(mix / ceil * 0.9) * ceil / np.tanh(0.9) if pk > ceil * 1.3 else mix * (ceil * 0.99 / pk)
l, pk = lufs(mix)
with wave.open("mix.wav", "w") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print(f"voice {l_v:.1f} LUFS | music alone {l_m:.1f} | mix {l:.1f} LUFS, true peak {pk:.1f} dBFS")
