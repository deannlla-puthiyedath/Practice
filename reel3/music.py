"""Original violin score for Reel 3 (synthesized violin: arco, spiccato, pizzicato). D major, 96.8 bpm.
Picture sync:   0.4 hook "dun dun dun dun" | 10.3 dream, legato | 15.2/16.9 tape peel runs | 18.4 pops (one note per box)
                28.0 wave, crescendo | 35.7 calm, held notes | 47.85 push harder, staccato crescendo | 58.1 smooth ending
python3 music.py -> music.wav (stereo, 48 kHz)"""
import wave
import numpy as np
from numpy.fft import rfft, irfft

SR = 48000
DUR = 84.0
BEAT = 0.62
rng = np.random.default_rng(5)
out = np.zeros((int(SR * (DUR + 4)), 2))

def hz(m): return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)
def sstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def place(sig, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= len(out): return
    j = min(i + len(sig), len(out))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:j, 0] += sig[:j - i] * g * l; out[i:j, 1] += sig[:j - i] * g * r

def body(f):
    """violin body: air/wood resonances near 290 and 450 Hz, a broad bridge hill near 2.8 kHz, soft roll-off above"""
    f = np.asarray(f, float)
    r = 1 + 1.5 * np.exp(-((f - 290) / 110) ** 2) + 0.9 * np.exp(-((f - 450) / 140) ** 2) \
        + 1.1 * np.exp(-((f - 2800) / 750) ** 2) + 0.5 * np.exp(-((f - 1300) / 450) ** 2)
    return r / (1 + (f / 7000) ** 4)

def band_noise(n, lo=1500, hi=7000):
    x = rng.standard_normal(n)
    X = rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    X *= ((fr > lo) & (fr < hi)) * 1.0
    y = irfft(X, n); return y / (np.abs(y).max() + 1e-9)

def additive(f_t, harmonics, amp_fn, phases):
    """sum of harmonics of a (possibly gliding) fundamental"""
    ph = 2 * np.pi * np.cumsum(f_t) / SR
    s = np.zeros(len(f_t))
    for k in range(1, harmonics + 1):
        fk = f_t[0] * k
        if fk > 11000: break
        s += amp_fn(k, fk) * np.sin(k * ph + phases[k])
    return s

def arco(m, dur, vel=0.6, vib=1.0, scoop=0.0, harmonic_flute=0.0, rel=0.22):
    """bowed, legato, with delayed vibrato. m = midi note, dur seconds held."""
    n = int(SR * (dur + rel)); t = np.arange(n) / SR; f0 = float(hz(m))
    sig = np.zeros(n)
    for det in (-2.5, 2.5):                                    # two voices a hair apart = bow shimmer
        vr = 5.3 + 0.25 * np.sin(0.7 * t + det)
        vd = vib * 11 * sstep((t - 0.28) / 0.55)                # cents, grows in after the note speaks
        cents = vd * np.sin(2 * np.pi * vr * t) + det - scoop * 100 * np.exp(-t / 0.09)
        f_t = f0 * 2 ** (cents / 1200)
        ph = rng.uniform(0, 6.28, 40)
        flute = harmonic_flute
        amp = lambda k, fk: (k ** -1.05) * body(fk) * (1 if k < 6 else (1 - 0.8 * flute)) * (0.2 if (flute and k > 5) else 1)
        sig += additive(f_t, 28, amp, ph)
    a = 0.055 + 0.07 * (1 - vel)
    env = sstep(t / a) * np.where(t < dur, 1.0, np.exp(-(t - dur) / (rel / 3.2)))
    env *= 1 + 0.06 * np.sin(2 * np.pi * 0.35 * t)             # slow bow-pressure breath
    sig = sig * env
    sc = band_noise(n) * 0.045 * np.exp(-t / 0.12) + band_noise(n, 800, 3500) * 0.012 * env   # bow bite + hiss
    sig += sc * (np.abs(sig).max() + 1e-9)
    return sig / (np.abs(sig).max() + 1e-9) * vel * 0.5

def spiccato(m, vel=0.6, dur=0.17):
    """short bounced bow: crisp bite, quick decay (the 'dun')"""
    n = int(SR * (dur + 0.16)); t = np.arange(n) / SR; f0 = float(hz(m))
    cents = -28 * np.exp(-t / 0.012)                           # tiny pitch scoop on the bite
    f_t = f0 * 2 ** (cents / 1200)
    ph = rng.uniform(0, 6.28, 40)
    amp = lambda k, fk: (k ** -0.85) * body(fk) * np.exp(-t[0] * 0)
    s = additive(f_t, 30, amp, ph)
    env = sstep(t / 0.006) * (0.55 * np.exp(-t / 0.045) + 0.45 * np.exp(-t / 0.11))
    s = s * env + band_noise(n, 2000, 8000) * 0.10 * np.exp(-t / 0.012) * np.abs(s).max()
    return s / (np.abs(s).max() + 1e-9) * vel * 0.55

def pizz(m, vel=0.6, ring=1.0):
    """plucked string: bright burst, harmonics die away fastest at the top"""
    f0 = float(hz(m)); n = int(SR * (0.25 + ring)); t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 16):
        fk = f0 * k * (1 + 0.0002 * k * k)
        if fk > 9000: break
        d = 2.6 + 2.2 * k * (f0 / 440) ** 0.25
        s += (k ** -1.1) * abs(np.sin(k * np.pi * 0.17) + 0.15) * body(fk) ** 0.6 * np.sin(2 * np.pi * fk * t + k) * np.exp(-t * d / ring ** 0.5)
    s[:24] *= np.linspace(0, 1, 24)
    return s / (np.abs(s).max() + 1e-9) * vel * 0.5

SC = [74, 76, 78, 79, 81, 83, 85, 86, 88, 90]               # D major from D5

# ---------------------------------------------------------------- score ----
def eighth(g0, bar, e): return g0 + bar * 4 * BEAT + e * BEAT / 2
G0 = 0.42

# A  0.4 - 10.3   hook: quiet staccato "dun dun dun dun-dun" over a plucked bass
A = {0: ([74, 74, 74, 78, 76], .42), 1: ([81, 81, 81, 78, 79], .46), 2: ([74, 74, 74, 78, 76], .50), 3: ([83, 81, 78, 76, 74], .56)}
for bar, (notes, v) in A.items():
    for i, (e, m) in enumerate(zip([0, 2, 4, 6, 7], notes)):
        place(spiccato(m, v * (1.2 if i == 0 else 1)), eighth(G0, bar, e), 0.2 * (-1) ** i, 1.0)
    place(pizz([62, 57, 62, 57][bar], .5, 0.9), eighth(G0, bar, 0), -0.45)
    place(pizz([69, 66, 69, 55][bar], .38, 0.7), eighth(G0, bar, 4), -0.35)

# B  10.3 - 18.4  dream of the sea: smooth, singing, a little slower to speak
bt = lambda bar, b: G0 + (bar * 4 + b) * BEAT
B = [(4, 0, 78, 2), (4, 2, 76, 1), (4, 3, 74, 1), (5, 0, 73, 2), (5, 2, 74, 2), (6, 0, 76, 2), (6, 2, 78, 1), (6, 3, 81, 1)]
for bar, b, m, nb in B:
    place(arco(m, nb * BEAT - 0.05, .52, 1.0), bt(bar, b), 0.15, 1.0)
for bar, m in [(4, 62), (5, 59), (6, 55)]:
    place(pizz(m, .42, 1.1), bt(bar, 0), -0.4)
    place(pizz(m + 12, .3, 0.7), bt(bar, 2), -0.3)
# tape peel: a quick plucked run up as the lines lift, back down as they seal
for i, m in enumerate([69, 73, 74, 78, 81, 85]): place(pizz(m, .42, 0.8), 15.2 + i * 0.085, -0.5 + i * 0.2)
for i, m in enumerate([86, 83, 81, 78, 74, 69]): place(pizz(m, .40, 0.8), 16.95 + i * 0.1, 0.5 - i * 0.18)
for i, m in enumerate([74, 78, 81, 86]): place(pizz(m, .45 + i * .03, 0.7), 17.78 + i * 0.155, -0.2 + i * 0.15)   # pick-up into the pops

# C  18.4 - 27.7  the boxes pop: one staccato note per box (31 pops, 0.31 s apart)
cyc = [0, 2, 4, 2, 1, 3, 5, 3]
roots = [62, 59, 55, 57]
for j in range(31):
    m = SC[min(cyc[j % 8] + j // 8, len(SC) - 1)]
    v = 0.46 + 0.34 * j / 30 + (0.1 if j % 4 == 0 else 0)
    tt = 18.4 + 0.31 * j
    place(spiccato(m, v), tt, 0.35 * np.sin(j * 1.3), 1.0)
    if j % 4 == 0: place(pizz(roots[(j // 4) % 4], .5, 0.9), tt, -0.4)
    if j % 8 == 4: place(pizz(roots[(j // 4) % 4] + 12, .3, 0.6), tt, 0.4)

# D  28.0 - 35.4  the wave: rolling arpeggios, crescendo
chords = [[74, 78, 81, 86], [74, 78, 83, 86], [79, 83, 86, 88], [76, 81, 85, 88]]
shape = [0, 1, 2, 3, 2, 1, 2, 3]
for m_i in range(24):
    ch = chords[(m_i // 6) % 4]
    m = ch[shape[m_i % 8]]
    v = 0.52 + 0.44 * (m_i / 23) ** 1.3
    place(spiccato(m, v), 28.01 + 0.31 * m_i, 0.4 * np.sin(m_i * 0.9), 1.0)
    if m_i % 4 == 0: place(pizz(roots[(m_i // 4) % 4], .52, 0.9), 28.01 + 0.31 * m_i, -0.4)
place(arco(86, 1.9, .7, 1.0, rel=.8), 35.45, 0.1)          # swell that lets go into the calm

# E  35.7 - 47.85  the calm: held, pure notes (the still box)
E = [(35.7, 74, 3.4), (38.9, 69, 3.5), (42.3, 78, 4.1), (46.2, 76, 1.7)]
for t0, m, d in E:
    place(arco(m, d, .36, 0.7, harmonic_flute=0.55, rel=.9), t0, 0.1)
place(pizz(62, .35, 1.8), 35.8, -0.4); place(pizz(57, .28, 1.8), 42.4, -0.3)
for i, m in enumerate([86, 90, 88]): place(pizz(m, .16, 1.6), 38.3 + i * 1.7, 0.45)     # light on water

# F  47.85 - 58.1  pushing harder and harder: staccato "dun" that builds and builds
F0 = 47.85
for n, m in enumerate([69, 74, 69, 74, 69, 74, 76, 74]):
    place(spiccato(m, 0.38 + 0.017 * n), F0 + n * BEAT, 0.2 * (-1) ** n)
    if n % 2 == 0: place(pizz(62 if n < 4 else 57, .5, 0.8), F0 + n * BEAT, -0.4)
for n, m in enumerate([74, 76, 78, 76, 78, 81, 78, 81]):
    place(spiccato(m, 0.55 + 0.02 * n), 52.81 + n * BEAT / 2, 0.3 * (-1) ** n)
for n, m in enumerate([74, 76, 78, 79, 81, 83, 85, 86, 85, 83, 81, 86, 88, 86, 88, 90]):
    place(spiccato(m, 0.7 + 0.018 * n, 0.12), 55.29 + n * BEAT / 4, 0.4 * (-1) ** n)
for m in (74, 86, 90): place(spiccato(m, 1.0, 0.2), 57.77, 0)       # the last big "dun", then the air clears
for m in (50 + 12, 57): place(pizz(m, .7, 0.5), 57.77, -0.4)

# G  58.3 - 84  smooth ending: warm legato violins, a second violin a third below, plucked bass
S0 = 58.3; SEG = 4 * BEAT
G = [(0, 0, 69, 2), (0, 2, 74, 2), (1, 0, 73, 1), (1, 1, 74, 1), (1, 2, 76, 2), (2, 0, 78, 3), (2, 3, 76, 1),
     (3, 0, 74, 2), (3, 2, 81, 2), (4, 0, 79, 1), (4, 1, 78, 1), (4, 2, 76, 1), (4, 3, 74, 1), (5, 0, 73, 2), (5, 2, 74, 2),
     (6, 0, 78, 2), (6, 2, 81, 2), (7, 0, 86, 4), (8, 0, 83, 2), (8, 2, 81, 2), (9, 0, 78, 2), (9, 2, 74, 4.2)]
for seg, b, m, nb in G:
    t0 = S0 + seg * SEG + b * BEAT
    sc = 1.2 if (seg, b) == (2, 0) else 0.0                          # slides up into the swimsuit's rise
    v = 0.5 + 0.05 * min(seg, 7) - (0.08 if seg >= 8 else 0)
    place(arco(m, nb * BEAT - 0.04, v, 1.0, scoop=sc, rel=.5 if seg < 9 else 1.2), t0, 0.15, 1.0)
    if seg >= 1 and nb >= 2:
        low = m - 4 if (m - 2) % 12 in (2, 7, 9) else m - 3
        place(arco(low, nb * BEAT - 0.04, v * 0.55, 0.8, rel=.5 if seg < 9 else 1.2), t0 + 0.03, -0.3, 1.0)
BASS = [62, 57, 59, 55, 62, 55, 57, 62, 55, 57]
for seg in range(10):
    t0 = S0 + seg * SEG
    place(pizz(BASS[seg], .46, 1.4), t0, -0.45)
    if seg < 9: place(pizz(BASS[seg] + 12, .28, 0.9), t0 + 2 * BEAT, -0.3)
for i, m in enumerate([74, 78, 81, 86]):                              # a little plucked sparkle as the end card lands
    place(pizz(m, .3, 1.4), 79.5 + i * 0.12, 0.3 + i * 0.1)

# ------------------------------------------------------------ room + out ---
ir_len = int(SR * 2.0)
ir = rng.standard_normal((2, ir_len)) * np.exp(-np.arange(ir_len) / SR * 2.6) * 0.022
ir[:, 0] = 1.0
nfft = 1 << int(np.ceil(np.log2(len(out) + ir_len)))
wet = np.stack([irfft(rfft(out[:, c], nfft) * rfft(ir[c], nfft), nfft)[:len(out)] for c in range(2)], 1)
mix = wet[:int(SR * DUR)]
fi = int(SR * 0.15); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(SR * 1.1); mix[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
mix /= np.abs(mix).max() / 0.8
with wave.open("music.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("music.wav", len(mix) / SR, "s")
