"""Original score for Reel 4 (Reverie: a day in the dress). D major, 104 bpm. Plucked strings, soft pad, light shaker.
Picture sync: 0 twirl (rising arpeggio) | 3.4 bakery (walking pluck) | 5.8 bell on the bag | 8.2 ride (faster, shaker)
13.8 house (door chime at 15.4) | 17.4 courtyard (slow, warm) | 23.6 reveal (swell) | 28.4 end chord.
python3 music.py -> music.wav"""
import wave
import numpy as np

SR = 48000; DUR = 32.0; BEAT = 60 / 104
rng = np.random.default_rng(4)
out = np.zeros((int(SR * (DUR + 2)), 2))

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def place(sig, t, pan=0.0, g=1.0):
    i = int(t * SR); j = min(i + len(sig), len(out))
    if i >= len(out): return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:j, 0] += sig[:j - i] * g * l; out[i:j, 1] += sig[:j - i] * g * r

def pluck(m, dur=1.2, bright=0.5):
    """Karplus-Strong plucked string."""
    n = int(SR * dur); p = int(SR / hz(m))
    buf = rng.uniform(-1, 1, p); y = np.zeros(n)
    for i in range(n):
        y[i] = buf[i % p]
        buf[i % p] = 0.996 * (bright * buf[i % p] + (1 - bright) * buf[(i + 1) % p])
    return y * np.exp(-np.arange(n) / (SR * dur * 0.5))

def pad(ms, dur, g=1.0):
    t = np.arange(int(SR * dur)) / SR
    y = sum(np.sin(2 * np.pi * hz(m) * t * (1 + d)) for m in ms for d in (-0.002, 0.002))
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8)
    return y * env * g / (2 * len(ms))

def bell(m):
    t = np.arange(int(SR * 2.5)) / SR
    return (np.sin(2 * np.pi * hz(m) * t) + 0.4 * np.sin(2 * np.pi * hz(m) * 2.76 * t)) * np.exp(-t * 2.2)

def shaker():
    n = int(SR * 0.08); return rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * 0.015)) * 0.25

# ---- Indian instruments for the opening (0 - 7 s): sitar, tabla, tanpura drone
def sitar(m, dur=1.4):
    """Bright plucked string with a buzzing jawari bridge and a small upward meend (slide)."""
    y = pluck(m, dur, 0.9)
    y = np.tanh(3.0 * y) * 0.6 + 0.4 * y                       # jawari buzz
    t = np.arange(len(y)) / SR
    sym = sum(np.sin(2 * np.pi * hz(m + k) * t) * np.exp(-t * 2.5) for k in (12, 19)) * 0.08   # sympathetic strings
    return y + sym

def tabla(kind):
    t = np.arange(int(SR * 0.6)) / SR
    if kind == "ge":                                            # low bayan, pitch bends down
        f = 95 + 60 * np.exp(-t * 18)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * 0.9
    if kind == "na":                                            # ringing dayan
        return (np.sin(2 * np.pi * 587 * t) + 0.5 * np.sin(2 * np.pi * 587 * 2.1 * t)) * np.exp(-t * 14) * 0.5
    return rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.35  # "te": dry slap

def tanpura(dur):
    """Drone on A, D, D, low D, each string fading in turn."""
    out_ = np.zeros(int(SR * dur)); t = np.arange(len(out_)) / SR
    for k, m in enumerate([45, 50, 50, 38] * int(dur / 2.4 + 1)):
        t0 = k * 0.6
        if t0 >= dur: break
        tt = np.clip(t - t0, 0, None)
        out_ += sum(np.sin(2 * np.pi * hz(m) * h * tt) / h ** 1.2 for h in range(1, 9)) * np.exp(-tt * 0.9) * (t >= t0) * 0.12
    env = np.minimum(1, t / 0.3) * np.clip((dur - t) / 1.0, 0, 1)
    return out_ * env

INDIAN_END = 7.0

_cache = {}
def P(m, dur=1.2, b=0.5):
    k = (m, dur, b)
    if k not in _cache: _cache[k] = pluck(m, dur, b)
    return _cache[k]

D, G, A, Bm = [50, 57, 62, 66], [43, 55, 59, 62], [45, 57, 61, 64], [47, 54, 59, 62]
prog = [D, G, Bm, A]

# pad underneath, chord per 2 bars
t = BEAT * 8 * 2; k = 2
while t < 28.4:
    ch = prog[k % 4]; place(pad([c + 12 for c in ch[1:]], BEAT * 8 + 0.8, 0.5), t, 0, 0.35); t += BEAT * 8; k += 1
place(pad([62, 66, 69, 74], 4.5, 0.6), 28.2, 0, 0.45)                 # end chord

# 0 - 3.4 twirl: rising arpeggio
place(tanpura(INDIAN_END + 1.0), 0.0, 0, 0.55)
for i, m in enumerate([62, 66, 69, 74, 78, 81, 86]): place(sitar(m), 0.15 + i * BEAT / 2, (i % 2) * 0.4 - 0.2, 0.45)
# tabla theka under the opening: dha dhin dhin dha | dha dhin dhin dha
for b in range(int(INDIAN_END / (BEAT / 2))):
    tt = 0.15 + b * BEAT / 2
    if tt > INDIAN_END - 0.2: break
    pat = b % 8
    if pat in (0, 3, 4, 7): place(tabla("ge"), tt, -0.15, 0.6)
    place(tabla("na" if pat in (0, 1, 2, 3, 4, 7) else "te"), tt, 0.2, 0.45)
# 3.4 - 8.2 walk: gentle melody in eighths
mel = [74, 76, 78, 76, 74, 71, 69, 71, 74, 76, 78, 81, 78, 76, 74, 76]
for i, m in enumerate(mel):
    tt = 3.4 + i * BEAT / 2
    if tt < INDIAN_END: place(sitar(m, 1.0), tt, -0.25, 0.4)
    elif tt < 8.2: place(P(m, 0.9), tt, -0.25, 0.42)
place(bell(86), 5.8, 0.3, 0.25)                                         # the bag
# 8.2 - 13.8 ride: faster sixteenths, shaker
mel2 = [78, 81, 83, 81, 78, 76, 74, 76]
i = 0; tt = 8.2
while tt < 13.8:
    place(P(mel2[i % 8], 0.6, 0.6), tt, 0.25, 0.32)
    place(shaker(), tt, -0.3, 0.6 if i % 2 else 0.3)
    if i % 4 == 0: place(P(prog[(i // 16) % 4][0], 1.2, 0.3), tt, 0, 0.5)
    i += 1; tt += BEAT / 4
# 13.8 - 17.4 house: slowing, door chime
for i, m in enumerate([74, 71, 69, 66, 69]): place(P(m, 1.4), 13.9 + i * BEAT, 0, 0.4)
place(bell(81), 15.4, -0.2, 0.2); place(bell(86), 15.65, 0.2, 0.16)
# 17.4 - 23.6 courtyard: warm, slow quarter notes, heart chime at the kiss
mel3 = [66, 69, 74, 73, 71, 69, 66, 64, 66, 69, 71, 74]
for i, m in enumerate(mel3):
    tt = 17.5 + i * BEAT
    if tt < 23.5: place(P(m, 1.6, 0.4), tt, -0.1, 0.42); place(P(m - 12, 1.6, 0.3), tt, 0.1, 0.2)
place(bell(90), 20.9, 0, 0.18)
# 23.6 - 28.4 reveal: swell and slow arpeggio
place(pad([62, 66, 69, 74, 78], 5.0, 1.0), 23.6, 0, 0.45)
for i, m in enumerate([62, 69, 74, 78, 81, 78, 74, 69]): place(P(m, 1.8, 0.45), 24.2 + i * BEAT * 0.75, (i % 2) * 0.5 - 0.25, 0.4)
for i, m in enumerate([62, 66, 69, 74]): place(P(m, 2.5, 0.4), 28.5 + i * 0.12, 0, 0.45)

out = out[: int(SR * DUR)]
fade = np.ones(len(out)); fade[-int(SR * 1.2):] = np.linspace(1, 0, int(SR * 1.2))
out *= fade[:, None]; out /= np.abs(out).max() * 1.12
with wave.open("music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("ok")
