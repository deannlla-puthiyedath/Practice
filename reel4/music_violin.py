"""Reel 4 score: violin only (arco, spiccato, pizzicato), synthesized. D major, 104 bpm.
Sync: 0 twirl rise | 3.4 bakery walk | 5.8 pluck on the bag | 8.2 ride, quick spiccato | 13.8 house, door chime
17.4 courtyard, warm legato | 23.6 reveal swell | 28.4 end. python3 music_violin.py -> music.wav"""
import wave
import numpy as np
from numpy.fft import rfft, irfft

SR = 48000
DUR = 32.0
BEAT = 60 / 104
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
# Della: only a bowed violin. No plucked strings anywhere (the pizzicato is gone), no bass plucks.
def pizz(m, vel=0.6, ring=1.0):
    if m < 60: return np.zeros(1)                     # drop the low plucked bass entirely
    return arco(m, 0.55 * ring, vel * 0.8, 0.8, rel=0.35)
def spiccato(m, vel=0.6, dur=0.17):
    return arco(m, max(dur * 2.2, 0.3), vel * 0.85, 0.6, rel=0.18)
H = BEAT / 2
# 0 - 3.4 twirl: a light pizzicato rise into a held note
for i, m in enumerate([62, 66, 69, 74, 78, 81]): place(pizz(m, .5, 0.9), 0.15 + i * H, 0.3 * (-1) ** i)
place(arco(86, 1.6, .5, 1.0, scoop=0.3, rel=.6), 0.15 + 6 * H, 0.1)
# 3.4 - 8.2 bakery: walking spiccato tune over plucked bass
mel = [74, 76, 78, 76, 74, 71, 69, 71, 74, 76, 78, 81, 78, 76, 74, 76]
for i, m in enumerate(mel):
    tt = 3.4 + i * H
    if tt < 8.1: place(spiccato(m, .5), tt, 0.2 * (-1) ** i)
    if i % 4 == 0 and tt < 8.1: place(pizz([50, 55, 47, 57][(i // 4) % 4], .5, 0.9), tt, -0.4)
place(pizz(90, .45, 1.2), 5.8, 0.4)                                    # the bag appears
# 8.2 - 13.8 ride: quick sixteenth spiccato, the sea going by
mel2 = [78, 81, 83, 81, 78, 76, 74, 76]
i = 0; tt = 8.2
while tt < 13.75:
    place(spiccato(mel2[i % 8], .42 + 0.05 * (i % 4 == 0), 0.12), tt, 0.35 * np.sin(i * 0.9))
    if i % 8 == 0: place(pizz([50, 55, 47, 57][(i // 8) % 4], .55, 0.9), tt, -0.4)
    i += 1; tt += BEAT / 4
# 13.8 - 17.4 house: slowing legato, two plucks as the door opens
for k, (m, nb) in enumerate([(74, 1), (71, 1), (69, 1), (66, 2)]):
    place(arco(m, nb * BEAT - 0.05, .45, 1.0), 13.9 + sum(n for _, n in [(74, 1), (71, 1), (69, 1), (66, 2)][:k]) * BEAT, 0.1)
place(pizz(81, .4, 1.4), 15.4, -0.2); place(pizz(86, .35, 1.4), 15.65, 0.2)
# 17.4 - 23.6 courtyard: warm singing line, a second violin a third below
mel3 = [(66, 1), (69, 1), (74, 2), (73, 1), (71, 1), (69, 2), (66, 1), (71, 1)]
t0 = 17.5
for m, nb in mel3:
    if t0 > 23.4: break
    place(arco(m + 12, nb * BEAT - 0.04, .5, 1.0, rel=.5), t0, 0.15)
    place(arco(m + 8, nb * BEAT - 0.04, .28, 0.8, rel=.5), t0 + 0.03, -0.3)
    t0 += nb * BEAT
place(pizz(93, .3, 1.4), 20.9, 0.3)                                    # the kiss
# 23.6 - 28.4 reveal: long swell and a slow pizzicato arpeggio
place(arco(74, 4.4, .55, 1.0, rel=1.0), 23.6, 0.1); place(arco(81, 4.4, .35, 0.9, rel=1.0), 23.65, -0.2)
for i, m in enumerate([62, 69, 74, 78, 81, 78, 74, 69]): place(pizz(m, .38, 1.2), 24.2 + i * BEAT * 0.75, 0.3 * (-1) ** i)
# 28.4 - 32 end: soft held D, last plucks
place(arco(86, 3.0, .45, 0.8, harmonic_flute=0.5, rel=1.2), 28.5, 0.1)
for i, m in enumerate([62, 66, 69, 74]): place(pizz(m, .4, 1.5), 28.5 + i * 0.12, -0.3 + i * 0.2)

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
