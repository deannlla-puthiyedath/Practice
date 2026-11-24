"""Soft original pad under the narration: slow chords, gentle pluck on each scene cut. -> score.wav (32 s)."""
import numpy as np, wave
SR, DUR = 44100, 32.0
t = np.arange(int(SR * DUR)) / SR
out = np.zeros_like(t)
chords = [(0, [146.8, 220.0, 277.2, 370.0]), (8, [123.5, 185.0, 246.9, 293.7]), (16, [164.8, 246.9, 329.6, 415.3]), (24, [146.8, 220.0, 293.7, 370.0])]
for i, (st, fr) in enumerate(chords):
    en = chords[i + 1][0] if i + 1 < len(chords) else DUR
    env = np.clip((t - st) / 2.0, 0, 1) * np.clip((en + 1.5 - t) / 2.0, 0, 1)
    for f in fr:
        out += env * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.003 * f * t)) * 0.06
for cut in (7.0, 11.0, 13.2, 16.0, 19.3, 22.0, 25.3, 30.1):  # pluck on each cut
    m = t >= cut; tt = t[m] - cut
    out[m] += 0.12 * np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 5)
out *= np.clip(t / 1.0, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1)
out = (out / np.abs(out).max() * 0.5 * 32767).astype(np.int16)
with wave.open("score.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
