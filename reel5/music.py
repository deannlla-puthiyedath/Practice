"""Reel 5 score (built on Reel 4's instruments). Original score for Reel 4 (Reverie: a day in the dress). D major, 104 bpm. Plucked strings, soft pad, light shaker.
Picture sync: 0 twirl (rising arpeggio) | 3.4 bakery (walking pluck) | 5.8 bell on the bag | 8.2 ride (faster, shaker)
13.8 house (door chime at 15.4) | 17.4 courtyard (slow, warm) | 23.6 reveal (swell) | 28.4 end chord.
python3 music.py -> music.wav"""
import wave
import numpy as np

SR = 48000; DUR = 55.0; BEAT = 60 / 84
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

_cache = {}
def P(m, dur=1.2, b=0.5):
    k = (m, dur, b)
    if k not in _cache: _cache[k] = pluck(m, dur, b)
    return _cache[k]

D, G, A, Bm = [50, 57, 62, 66], [43, 55, 59, 62], [45, 57, 61, 64], [47, 54, 59, 62]
prog = [D, G, Bm, A]


def bow(m, dur, g=1.0):
    """Synth violin, legato: sawtooth-ish with vibrato and slow bow swell."""
    t = np.arange(int(SR * dur)) / SR
    f = hz(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.4))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) / k for k in range(1, 7))
    env = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.4)
    return y * env * g * 0.3

D, G, A, Bm = [50, 57, 62, 66], [43, 55, 59, 62], [45, 57, 61, 64], [47, 54, 59, 62]
Em = [52, 55, 59, 64]
def pads(t0, t1, prog, g):
    t = t0; k = 0
    while t < t1:
        dur = min(BEAT * 8, t1 - t) + 0.8
        place(pad([c + 12 for c in prog[k % len(prog)][1:]], dur, 0.5), t, 0, g); t += BEAT * 8; k += 1

# 0-7 city at night: tender, slow (the kiss at 2.6: a held violin note)
pads(0, 11, [D, Bm, G, A], 0.33)
for i, m in enumerate([74, 78, 81, 78, 76, 74]): place(P(m, 1.6, 0.4), 0.2 + i * BEAT, -0.2, 0.38)
place(bow(81, 3.4), 2.4, 0.1, 0.5); place(bell(93), 2.7, 0, 0.12)
# 7-11 airport: the look back (8.6) gets one falling phrase
for i, m in enumerate([78, 76, 74, 71]): place(bow(m, 1.0), 7.4 + i * 0.9, 0, 0.42)
# 11-20 night flight: minor, hushed
pads(11, 20.4, [Bm, Em, G, A], 0.38)
for i, m in enumerate([71, 74, 76, 74, 71, 69, 71, 66]): place(P(m, 1.8, 0.35), 11.3 + i * BEAT * 1.4, 0.2, 0.32)
place(bow(66, 4.0), 15.8, -0.1, 0.4)
# 20-22 dawn through the window: swell
place(pad([62, 66, 69, 74, 78], 3.0, 1.0), 19.8, 0, 0.5); place(bow(78, 2.6), 20.0, 0, 0.5)
# 22-32 the ride through Fort Kochi: bright plucks + shaker
pads(22, 32, [D, G, A, D], 0.3)
mel = [78, 81, 83, 81, 78, 76, 74, 76, 78, 81, 86, 83]
i = 0; tt = 22.0
while tt < 31.8:
    place(P(mel[i % len(mel)], 0.7, 0.6), tt, 0.25, 0.32)
    place(shaker(), tt, -0.3, 0.55 if i % 2 else 0.25)
    if i % 4 == 0: place(P([D, G, A, D][(i // 16) % 4][0], 1.2, 0.3), tt, 0, 0.5)
    i += 1; tt += BEAT / 2
# 32-36 the house: door chime at 34
for i, m in enumerate([74, 71, 69, 74]): place(P(m, 1.4), 32.1 + i * BEAT, 0, 0.4)
place(bell(81), 34.0, -0.2, 0.2); place(bell(86), 34.25, 0.2, 0.16)
# 36-44 Dad's twirl: a waltz-like lift, rising arpeggios
pads(36, 44, [D, G, Bm, A], 0.36)
for r in range(5):
    for j, m in enumerate([62, 66, 69, 74, 78, 74]):
        tt = 37.9 + r * 1.2 + j * 0.2
        if tt < 43.6: place(P(m + (2 if r % 2 else 0), 0.9, 0.5), tt, (j % 2) * 0.5 - 0.25, 0.33)
place(bow(86, 2.6), 39.6, 0, 0.32)
# 44-50 Mum's hug: the theme, held long
for i, m in enumerate([74, 78, 76, 74]): place(bow(m, 1.6 if i < 3 else 3.0), 44.2 + i * 1.5, 0, 0.5)
place(pad([62, 66, 69, 74], 6.0, 0.8), 44.0, 0, 0.4)
# 50-55 end chord
place(pad([62, 66, 69, 74], 5.0, 0.6), 50.0, 0, 0.45)
for i, m in enumerate([62, 66, 69, 74]): place(P(m, 2.5, 0.4), 50.3 + i * 0.12, 0, 0.45)

out = out[: int(SR * DUR)]
fade = np.ones(len(out)); fade[-int(SR * 1.5):] = np.linspace(1, 0, int(SR * 1.5))
out *= fade[:, None]; out /= np.abs(out).max() * 1.12
with wave.open("music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("ok")
