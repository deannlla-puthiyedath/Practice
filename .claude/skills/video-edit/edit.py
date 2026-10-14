#!/usr/bin/env python3
"""ffmpeg wrapper for the video-edit skill. Run with -h for usage."""
import argparse, json, re, shutil, subprocess, sys, tempfile, os


def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr or ''}")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path], capture=True)
    return json.loads(r.stdout)


def cmd_probe(a):
    d = probe(a.input)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in d["streams"])
    print(f"duration: {float(d['format']['duration']):.1f}s")
    if v:
        print(f"size:     {v['width']}x{v['height']}")
        print(f"fps:      {v.get('r_frame_rate')}")
    print(f"audio:    {'yes' if has_audio else 'no'}")
    print(f"bytes:    {d['format'].get('size')}")


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart"]


def cmd_trim(a):
    cmd = ["ffmpeg", "-y", "-i", a.input, "-ss", str(a.start)]
    if a.end is not None:
        cmd += ["-to", str(a.end)]
    run(cmd + ENC + [a.output], capture=True)
    print("wrote", a.output)


def cmd_silence(a):
    dur = float(probe(a.input)["format"]["duration"])
    r = run(["ffmpeg", "-i", a.input, "-af",
             f"silencedetect=noise={a.db}dB:d={a.min}", "-f", "null", "-"], capture=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    keep, pos = [], 0.0
    for s, e in zip(starts, ends):
        s += a.pad
        e -= a.pad
        if e > s:
            if s > pos:
                keep.append((pos, s))
            pos = e
    if len(starts) > len(ends):  # trailing silence
        keep.append((pos, starts[-1] + a.pad))
    else:
        keep.append((pos, dur))
    keep = [(s, e) for s, e in keep if e - s > 0.05]
    if not keep or not starts:
        shutil.copy(a.input, a.output)
        print("no silences found; copied unchanged")
        return
    parts, labels = [], ""
    for i, (s, e) in enumerate(keep):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}]")
        labels += f"[v{i}][a{i}]"
    fc = ";".join(parts) + f";{labels}concat=n={len(keep)}:v=1:a=1[v][a]"
    run(["ffmpeg", "-y", "-i", a.input, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]"] + ENC + [a.output], capture=True)
    saved = dur - sum(e - s for s, e in keep)
    print(f"removed {len(starts)} pauses, {saved:.1f}s saved -> {a.output}")


def cmd_vertical(a):
    if a.blur:
        vf = ("split[a][b];[a]scale=1080:1920,boxblur=30:5[bg];"
              "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2")
    else:
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    run(["ffmpeg", "-y", "-i", a.input, "-vf", vf] + ENC + [a.output], capture=True)
    print("wrote", a.output)


def cmd_captions(a):
    style = ("FontName=Arial,FontSize=14,Bold=1,PrimaryColour=&HFFFFFF&,"
             "OutlineColour=&H000000&,BorderStyle=1,Outline=2,Alignment=2,MarginV=90")
    srt = a.srt.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    run(["ffmpeg", "-y", "-i", a.input, "-vf",
         f"subtitles='{srt}':force_style='{style}'"] + ENC + [a.output], capture=True)
    print("wrote", a.output)


def cmd_join(a):
    # normalise every clip first so concat never trips on mismatched streams
    tmp = tempfile.mkdtemp()
    norm = []
    for i, c in enumerate(a.inputs):
        p = os.path.join(tmp, f"{i}.mp4")
        run(["ffmpeg", "-y", "-i", c, "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
             "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1",
             "-ar", "48000", "-ac", "2"] + ENC + [p], capture=True)
        norm.append(p)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in norm)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.output], capture=True)
    shutil.rmtree(tmp)
    print(f"joined {len(norm)} clips -> {a.output}")


def cmd_export(a):
    run(["ffmpeg", "-y", "-i", a.input, "-r", "30"] + ENC + [a.output], capture=True)
    d = probe(a.output)
    print(f"{a.output}: {float(d['format']['duration']):.1f}s, "
          f"{int(d['format']['size'])/1e6:.1f} MB")


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install it first.")
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="c", required=True)

    def add(name, fn, *args):
        s = sp.add_parser(name)
        for n, kw in args:
            s.add_argument(n, **kw)
        s.set_defaults(fn=fn)

    io = [("input", {}), ("output", {})]
    add("probe", cmd_probe, ("input", {}))
    add("trim", cmd_trim, *io, ("--start", {"type": float, "default": 0}), ("--end", {"type": float}))
    add("silence", cmd_silence, *io, ("--db", {"type": float, "default": -30}),
        ("--min", {"type": float, "default": 0.5}), ("--pad", {"type": float, "default": 0.1}))
    add("vertical", cmd_vertical, *io, ("--blur", {"action": "store_true"}))
    add("captions", cmd_captions, *io, ("srt", {}))
    add("join", cmd_join, ("output", {}), ("inputs", {"nargs": "+"}))
    add("export", cmd_export, *io)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
