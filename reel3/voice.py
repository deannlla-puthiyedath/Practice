"""Della's narration: trim the long pauses (her words untouched), clean and level the voice,
and write the new timeline for every spoken phrase.
python3 voice.py -> voice.wav (48 kHz mono), cues.json"""
import json, re, subprocess, wave
import numpy as np

SR = 48000
RAW = "voice_raw.m4a"
CAP = 0.75            # longest pause kept anywhere
CAP_STILL = 1.5       # the breath before "We receive the grace of acceptance"
START = 1.42          # drop the tap before the first word (first word at 1.52 s)

# 1) decode
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", RAW, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768

# 2) find pauses (same settings as the check run: -38 dB, 0.35 s)
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", RAW, "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", log)]
en = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", log)]
sil = []
for s, e in zip(st, en):  # merge touching pieces
    if sil and s - sil[-1][1] < 0.01: sil[-1][1] = e
    else: sil.append([s, e])

words = json.load(open("voice_words.json"))
grace_t = next(s["start"] for s in words if s["text"].lower().startswith("we receive"))

# 3) remove the middle of every pause longer than its cap
cuts = [(0.0, START)]
for s, e in sil:
    if e <= START: continue
    s = max(s, START)
    cap = CAP_STILL if s < grace_t <= e + 0.3 else CAP
    if e - s > cap:
        cuts.append((s + cap * 0.55, e - cap * 0.45))
end_t = words[-1]["end"] + 0.6
cuts.append((end_t, len(x) / SR))

keep, t = [], 0.0
for a, b in cuts:
    if a > t: keep.append((t, a))
    t = max(t, b)

XF = int(0.02 * SR)
out = np.zeros(0, np.float32)
for a, b in keep:
    seg = x[int(a * SR):int(b * SR)].copy()
    if len(out) >= XF and len(seg) > XF:
        ramp = np.linspace(0, 1, XF, dtype=np.float32)
        out[-XF:] = out[-XF:] * (1 - ramp) + seg[:XF] * ramp
        seg = seg[XF:]
    out = np.concatenate([out, seg])

def new_time(t):
    """old recording time -> trimmed time"""
    acc = 0.0
    for a, b in keep:
        if t < a: return acc
        if t <= b: return acc + (t - a)
        acc += (b - a) - XF / SR
    return acc

with wave.open("voice_trim.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

# 4) clean + level: rumble cut, gentle denoise, light compression, warm presence, -18 LUFS
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "voice_trim.wav", "-af",
                "highpass=f=75,afftdn=nf=-48,acompressor=threshold=-26dB:ratio=3:attack=8:release=160:makeup=2,"
                "equalizer=f=3200:t=q:w=1.2:g=2,loudnorm=I=-18:TP=-4:LRA=9", "-ar", str(SR), "voice.wav"], check=True)

cues = [{"start": round(new_time(s["start"]), 3), "end": round(new_time(s["end"]), 3), "said": s["text"]} for s in words]
json.dump({"duration": round(len(out) / SR, 3), "cues": cues}, open("cues.json", "w"), indent=1)
print(f"{len(x)/SR:.1f}s -> {len(out)/SR:.1f}s")
for c in cues: print(f'{c["start"]:6.2f}-{c["end"]:6.2f}  {c["said"]}')
