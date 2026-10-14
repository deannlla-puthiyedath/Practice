"""Original score for Reel 2: marimba, harp, soft bells. Ab major, ~92 bpm (same key/tempo feel as Reel 1).
Verse -> build/swell at the halo -> short silence -> whimsical return -> bell ring-out on the end card."""
import numpy as np, wave

SR = 44100
DUR = 35.5
BEAT = 0.65
rng = np.random.default_rng(2)
out = np.zeros((int(SR * DUR) + SR * 3, 2))

def hz(n): return 440.0 * 2 ** ((n - 69) / 12)  # midi -> Hz

def add(sig, t, pan=0.0, g=1.0):
    i = int(t * SR); j = min(i + len(sig), len(out))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:j, 0] += sig[:j - i] * g * l; out[i:j, 1] += sig[:j - i] * g * r

def marimba(n, dur=0.9):
    t = np.arange(int(SR * dur)) / SR; f = hz(n)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 22) \
        + 0.12 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 60)
    s[:40] *= np.linspace(0, 1, 40)
    return s

def harp(n, dur=2.2):
    t = np.arange(int(SR * dur)) / SR; f = hz(n)
    s = sum((1 / k ** 1.3) * np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (1.0 + 0.9 * k)) for k in range(1, 9) if f * k < 9000)
    s[:30] *= np.linspace(0, 1, 30)
    return s


def bell(n, dur=3.5):
    t = np.arange(int(SR * dur)) / SR; f = hz(n)
    parts = [(1, 1, 1.4), (2.76, 0.45, 2.5), (5.4, 0.22, 4.5), (8.93, 0.1, 7)]
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * d) for k, a, d in parts)
    s[:60] *= np.linspace(0, 1, 60)
    return s

# Ab major: Ab4=68. chords (midi roots): Ab, Fm, Db, Eb
CH = {"Ab": [56, 60, 63], "Fm": [53, 56, 60], "Db": [49, 53, 56], "Eb": [51, 55, 58]}
PROG = ["Ab", "Fm", "Db", "Eb"]
BAR = 4 * BEAT

# --- verse 0 - 19.0 ---
t = 0.35
mel = [75, 72, 70, 72, 68, 70, 72, 75, 77, 75, 72, 70, 68, 67, 68, 70]  # bell tune, Ab pentatonic-ish
k = 0
while t < 19.0:
    for c in PROG:
        if t >= 19.0: break
        notes = CH[c]
        harp_g = 0.5 * min(1, t / 3)
        add(harp(notes[0] - 12), t, -0.3, harp_g); add(harp(notes[0] - 5), t + 2 * BEAT, -0.3, harp_g * 0.7)
        patt = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24, notes[2] + 12, notes[1] + 12]
        for i, n in enumerate(patt):
            tt = t + i * BEAT / 2
            if tt < 19.0: add(marimba(n), tt, 0.25 if i % 2 else -0.1, 0.28 * min(1, t / 2 + 0.3))
        if t > 5.5:  # bells come in with the sun rays
            for j in range(2):
                add(bell(mel[k % len(mel)] + 12), t + j * 2 * BEAT, 0.4, 0.07); k += 1
        t += BAR

# --- build / swell 19.0 - 24.25 (ring lifts into halo) ---
t = 19.0
for bi, c in enumerate(["Db", "Eb", "Fm"]):
    notes = CH[c]
    for i in range(16):
        tt = t + i * BEAT / 4
        if tt >= 24.2: break
        g = 0.16 + 0.22 * (tt - 19) / 5.2
        add(marimba(notes[i % 3] + 12 + 12 * (i // 8)), tt, (-1) ** i * 0.3, g)
    add(harp(notes[0] - 12), t, -0.2, 0.7)
    add(bell(notes[2] + 24), t, 0.3, 0.06 + 0.04 * bi)
    t += BAR * 0.5 + 0.0
# harp glissando up into the swell
g_notes = [56, 58, 60, 61, 63, 65, 67, 68, 70, 72, 73, 75, 77, 79, 80]
for i, n in enumerate(g_notes):
    add(harp(n, 1.6), 23.15 + i * 0.065, -0.5 + i / len(g_notes), 0.45)
for n in (68, 72, 75, 80):
    add(bell(n + 12, 2.0), 23.95, 0.0, 0.09)
# hard stop for the short silence 24.25 - 24.65
cut0, cut1 = int(24.25 * SR), int(24.65 * SR)
fade = int(0.06 * SR)
out[cut0 - fade:cut0] *= np.linspace(1, 0, fade)[:, None]
out[cut0:] = 0

# --- whimsical return 24.65 - 33.0 (wings) ---
t = 24.65
motif = [80, 0, 77, 79, 80, 0, 84, 0, 82, 80, 77, 0, 79, 0, 75, 0]  # playful staccato, higher register
while t < 33.0:
    for c in ["Ab", "Db", "Eb", "Ab"]:
        if t >= 33.0: break
        notes = CH[c]
        add(harp(notes[0] - 12, 1.2), t, -0.4, 0.55); add(harp(notes[2], 0.6), t + BEAT, 0.4, 0.35)
        add(harp(notes[1] + 12, 0.6), t + 2.5 * BEAT, 0.4, 0.3)
        for i in range(8):
            n = motif[(i + int(t * 10)) % len(motif)]
            if n and t + i * BEAT / 2 < 33.0:
                add(marimba(n - 12, 0.5), t + i * BEAT / 2, 0.3 * (-1) ** i, 0.24)
        add(bell(notes[2] + 24, 2.5), t + 3 * BEAT, -0.3, 0.05)
        t += BAR

# --- end card: bell chord + harp roll ring-out ---
for i, n in enumerate([56, 63, 68, 72, 75, 80]):
    add(harp(n, 3.0), 33.05 + i * 0.07, -0.4 + i * 0.15, 0.4)
for n in (68, 72, 75):
    add(bell(n + 12, 3.0), 33.5, 0.0, 0.08)

# simple room reverb
ir_len = int(SR * 1.6)
ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 3.2) * 0.03
ir[0] = 1.0
from numpy.fft import rfft, irfft
nfft = 1 << int(np.ceil(np.log2(len(out) + ir_len)))
IR = rfft(ir, nfft)
wet = np.stack([irfft(rfft(out[:, c], nfft) * IR, nfft)[:len(out)] for c in range(2)], 1)
# keep the silence silent (reverb tail shortened there)
env = np.ones(len(out)); env[cut0 - fade:cut0] = np.linspace(1, 0, fade); env[cut0:cut1] = 0
wet *= env[:, None]
mix = wet[:int(SR * DUR)]
fo = int(SR * 1.2); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix /= np.abs(mix).max() / 0.8
with wave.open("music.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("music.wav", len(mix) / SR, "s")
