---
name: video-edit
description: >-
  Edit video with ffmpeg - trim, cut dead air and silences, reframe to 9:16,
  burn in captions, join clips, and export an Instagram-ready file. Use when
  the user has a video file and says "edit this", "cut the pauses", "trim",
  "make it vertical", "add captions", "stitch these clips", "compress for
  Instagram", or wants a raw recording turned into something postable.
---

# video-edit

Turns a raw recording into a clean, postable file. One helper, `edit.py`,
wraps ffmpeg so the commands are the same every time.

```bash
python3 edit.py probe in.mp4                       # duration, size, fps, audio
python3 edit.py trim in.mp4 out.mp4 --start 2.5 --end 31
python3 edit.py silence in.mp4 out.mp4             # cut dead air (--db -30 --min 0.5)
python3 edit.py vertical in.mp4 out.mp4            # 1080x1920, center crop (--blur to letterbox)
python3 edit.py captions in.mp4 out.mp4 subs.srt   # burn captions in
python3 edit.py join out.mp4 a.mp4 b.mp4 c.mp4     # concat, re-encoded so it never breaks
python3 edit.py export in.mp4 out.mp4              # Instagram preset: H.264, AAC, 30fps, faststart
```

## Order of work

Always in this order, each step feeding the next, so nothing is re-encoded
more than it has to be:

1. `probe` first. Know the length, orientation and whether there is audio.
2. `trim` the head and tail (most raw takes start with "okay, so...").
3. `silence` to remove pauses. Then listen: if breaths are gone and it sounds
   rushed, rerun with a gentler `--min 0.8`.
4. `vertical` if the source is not 9:16. Use `--blur` when cropping would cut
   off the speaker or on-screen text.
5. `captions` last, after the cuts, so the timing matches. If there is no
   .srt, transcribe first (whisper if installed) and ask the user to check names.
6. `export` for the final file. Report the size and length back.

## Rules

- Never overwrite the original. Outputs go to a new file; name them `_cut`,
  `_vertical`, `_final`.
- Reels run up to 90 seconds but most finish under 30. If the cut is longer
  than the user's goal, say so and offer the trims, don't silently chop.
- Tell the user what changed in one line each: "removed 11 pauses, 14s saved".
- If ffmpeg is missing, say so and stop; do not fake an output.
- For a hook rewrite or script, hand off to `ig-reel`; for the caption text, `ig-caption`.
