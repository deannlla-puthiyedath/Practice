"""Clean Della's narration take: keep the speech, drop mouth noises, swallows, breaths and end taps,
and fill the gaps with her own room tone so nothing sounds gated. Timing is NOT changed.
python3 clean_voice.py take.m4a out_prefix
Segments (start, end) in seconds were set from voiced-speech detection plus a look at the spectrogram:
each one starts just before the first word (room for s / th / w onsets) and ends after the last (room for t / th).
Noises left out on purpose (take 2): breath 2.42-2.80, swallow/click series 6.15-6.55, click 10.18, breath 13.6,
clicks 22.09-22.14, thump 24.55, breath/air 37.05-37.9, clicks 42.57 / 42.99 / 43.66, tick 44.95, click 48.14, end taps 49.4+."""
import sys, subprocess, wave
import numpy as np

SR = 48000
SEGS = [(0.55, 2.50), (2.89, 4.72), (10.31, 12.25), (13.99, 15.69), (17.03, 18.61),
        (22.16, 24.55), (26.51, 28.25), (31.80, 33.31), (36.01, 37.05), (37.89, 39.16),
        (43.71, 44.94), (46.56, 48.13)]
TONE = (29.0, 31.0)          # a quiet, event-free stretch of this take
FADE = 0.025

src, prefix = sys.argv[1], sys.argv[2]
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
n = len(x)

# room tone, looped with 100 ms crossfades
t0, t1 = int(TONE[0] * SR), int(TONE[1] * SR)
tone = x[t0:t1].copy(); tone -= tone.mean()
xf = int(0.1 * SR); ramp = np.linspace(0, 1, xf, dtype=np.float32)
bed = tone.copy()
while len(bed) < n + SR:
    nxt = np.roll(tone, int(np.random.default_rng(len(bed)).integers(0, len(tone))))
    bed[-xf:] = bed[-xf:] * (1 - ramp) + nxt[:xf] * ramp
    bed = np.concatenate([bed, nxt[xf:]])
out = bed[:n].copy()

f = int(FADE * SR)
for a, b in SEGS:
    i, j = int(a * SR), int(b * SR)
    w = np.ones(j - i, np.float32)
    w[:f] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, f)); w[-f:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f))
    out[i:j] = bed[i:j] * (1 - w) + x[i:j] * w

end = int(48.9 * SR)          # the last word finishes at 48.13; leave a quiet tail
out = out[:end]
with wave.open(prefix + "_edit.wav", "w") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

# level like Reel 3: rumble cut, gentle denoise, light compression, -18 LUFS
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", prefix + "_edit.wav", "-af",
                "highpass=f=75,afftdn=nf=-48,acompressor=threshold=-26dB:ratio=3:attack=8:release=160:makeup=2,"
                "loudnorm=I=-18:TP=-4:LRA=9", "-ar", str(SR), prefix + ".wav"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", prefix + ".wav", "-c:a", "aac", "-b:a", "192k", prefix + ".m4a"], check=True)
print("done", len(out) / SR, "s")
