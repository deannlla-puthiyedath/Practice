"""Reel 6 score (synth from Reel 4): violin only (arco, spiccato, pizzicato), synthesized. D major, 104 bpm.
Sync: 0 twirl rise | 3.4 bakery walk | 5.8 pluck on the bag | 8.2 ride, quick spiccato | 13.8 house, door chime
17.4 courtyard, warm legato | 23.6 reveal swell | 28.4 end. python3 music_violin.py -> music.wav"""
import wave
import numpy as np
from numpy.fft import rfft, irfft

SR = 48000
DUR = 58.5
BEAT = 60 / 66
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


# ---------------------------------------------------------------- Reel 6 score ----
# Violin only (bowed, no plucks, never five-note). Dreamy film score. Plus three sounds from the scene:
# the church bell, sea wind, faint street voices. They carry the silence at the stop (24 - 29 s).
def pizz(m, vel=0.6, ring=1.0): return arco(m, 0.55 * ring, vel * 0.8, 0.8, rel=0.35)
amb = np.zeros_like(out)
def amb_place(sig, t, pan=0.0, g=1.0):
    i = int(t * SR); j = min(i + len(sig), len(amb))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    amb[i:j, 0] += sig[:j - i] * g * l; amb[i:j, 1] += sig[:j - i] * g * r

# A 0 - 9: her worries. Restless short bows in B minor (with C# and G, so never pentatonic), climbing.
pat = [71, 73, 74, 78, 76, 74, 73, 74]
tt, i = 0.25, 0
while tt < 8.9:
    m = pat[i % 8] + (2 if i >= 32 else 0)
    place(arco(m, 0.16, .32 + 0.1 * (tt / 9), 0.3, rel=.1), tt, 0.3 * np.sin(i))
    if i % 8 == 0: place(arco([59, 55, 57, 54][(i // 8) % 4], 2.0, .3, 0.6, rel=.5), tt, -0.35)
    i += 1; tt += 0.27
# B 9 - 24: the inner voice. Long, calm, two violins.
for t0, m1, m2, d in ((9.0, 78, 74, 2.4), (11.4, 76, 73, 2.2), (13.6, 74, 71, 2.4), (16.0, 73, 69, 2.6)):
    place(arco(m1, d, .42, 1.0, rel=.6), t0, 0.15); place(arco(m2, d, .26, 0.8, rel=.6), t0 + 0.05, -0.25)
place(arco(81, 4.8, .45, 1.0, harmonic_flute=0.3, rel=1.4), 18.6, 0.1)             # the breath: one long held note
place(arco(74, 4.8, .22, 0.8, rel=1.4), 18.7, -0.3)
# the bell (16.3), and a softer one (17.7)
def bell(f0, dur=6.0, g=1.0):
    n = int(SR * dur); t = np.arange(n) / SR; s = np.zeros(n)
    for ratio, a, dec in ((0.5, .5, 4.5), (1.0, 1.0, 2.6), (1.19, .55, 1.8), (1.5, .4, 1.6), (2.0, .6, 1.3), (2.51, .3, .9), (3.0, .25, .7)):
        s += a * np.sin(2 * np.pi * f0 * ratio * t + ratio) * np.exp(-t / dec)
    s[:60] *= np.linspace(0, 1, 60)
    return s / np.abs(s).max() * g
amb_place(bell(523.0), 16.3, 0.2, 0.32); amb_place(bell(523.0, 5.0), 17.7, 0.2, 0.18); amb_place(bell(523.0, 6.0), 24.3, 0.3, 0.18)
# sea wind and street voices under everything, up at the stop
nA = len(amb); tA = np.arange(nA) / SR
wind = band_noise(nA, 150, 900) * (0.55 + 0.45 * np.sin(2 * np.pi * tA / 6.5) ** 2)
voices = band_noise(nA, 300, 1600) * (0.5 + 0.5 * np.clip(np.sin(2 * np.pi * tA * 1.7) * np.sin(2 * np.pi * tA * 0.37), 0, 1))
lvl = 0.05 + 0.22 * np.clip((tA - 23.6) / 0.8, 0, 1) * np.clip((29.6 - tA) / 1.0, 0, 1)
amb[:, 0] += (wind * 0.7 + voices * 0.35) * lvl; amb[:, 1] += (wind * 0.6 + voices * 0.4) * lvl * 0.95
# D 29 - 42.4: the boxes. Warm, rising cantabile, a small lift at each new set of boxes.
mel = [(74, 2), (76, 1), (78, 2), (81, 1), (79, 2), (78, 1), (76, 3), (78, 2), (81, 1), (83, 2), (85, 1), (86, 3), (85, 2), (83, 1), (81, 3)]
t0 = 29.3
for m, nb in mel:
    if t0 > 42.2: break
    place(arco(m, nb * BEAT * 0.5 - 0.04, .48, 1.0, rel=.5), t0, 0.15)
    place(arco(m - 4 if m - 4 not in (70, 75) else m - 3, nb * BEAT * 0.5 - 0.04, .27, 0.8, rel=.5), t0 + 0.03, -0.3)
    t0 += nb * BEAT * 0.5
for ts in (29.0, 31.6, 33.9, 36.6, 39.3):
    place(arco(62, 2.2, .3, 0.6, rel=.8), ts, -0.4); place(arco(69, 2.2, .2, 0.6, rel=.8), ts + 0.05, 0.4)
# E 42.4 - 51.8: home. Slow, warm chords; the line comes down and rests.
for i, (m1, m2, m3) in enumerate(((78, 74, 69), (76, 73, 69), (74, 71, 67), (73, 69, 64))):
    t0 = 42.6 + i * 2.25
    place(arco(m1, 2.1, .44, 1.0, rel=.8), t0, 0.15); place(arco(m2, 2.1, .3, .8, rel=.8), t0 + .04, -0.2); place(arco(m3 - 12, 2.1, .26, .6, rel=.8), t0 + .08, -0.45)
# F 51.8 - 55: the reveal swell
place(arco(74, 3.3, .55, 1.0, rel=1.2), 51.8, 0.1); place(arco(81, 3.3, .4, 1.0, rel=1.2), 51.9, -0.2); place(arco(86, 2.6, .35, 1.0, rel=1.2), 52.5, 0.3)
# G 55 - 58.5: coda
place(arco(86, 3.0, .4, 0.8, harmonic_flute=0.5, rel=1.2), 55.1, 0.1); place(arco(78, 3.0, .25, 0.7, rel=1.2), 55.15, -0.3)
# music rests at the stop
gate = np.ones(len(out)); ta = np.arange(len(out)) / SR
gate *= np.clip((23.6 - ta) / 0.8 + 1, 0, 1) * 0 + np.where(ta < 23.6, 1.0, np.where(ta < 24.4, (24.4 - ta) / 0.8, np.where(ta < 28.8, 0.0, np.clip((ta - 28.8) / 0.6, 0, 1))))
out *= gate[:, None]
# ------------------------------------------------------------ room + out ---
ir_len = int(SR * 2.0)
ir = rng.standard_normal((2, ir_len)) * np.exp(-np.arange(ir_len) / SR * 2.6) * 0.022
ir[:, 0] = 1.0
nfft = 1 << int(np.ceil(np.log2(len(out) + ir_len)))
wet = np.stack([irfft(rfft(out[:, c], nfft) * rfft(ir[c], nfft), nfft)[:len(out)] for c in range(2)], 1)
mix = wet[:int(SR * DUR)] + amb[:int(SR * DUR)] * (np.abs(wet).max() / 0.8)
fi = int(SR * 0.15); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(SR * 1.1); mix[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
mix /= np.abs(mix).max() / 0.8
with wave.open("music.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("music.wav", len(mix) / SR, "s")
