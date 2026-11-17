# Handoff: the next painting reel (same tone as Reel 3)

Use this to start a new session for the next video. Della attaches the painting; everything else is below.

## Paste this into the new session

> Make my next Instagram reel (also for Pinterest) from the painting I'm attaching, in the same tone and method as Reel 3. Read `HANDOFF_next_reel.md` in the Practice repo first and follow it. Load my skills `della-hyperframes-video`, `della-ig-viral`, `della-creative-math` and `della-antony-instagram`. I'll attach the book file (`Is It time to wake up 2.pages`) and the painting's own story if I have one. Ask me with pop-ups, then show me the story and shot list and stop for my approval before building.

## What Reel 3 was (the model to follow)

- **Painting:** Sunset (2) – Finding Meaning in the Now. 50 sea boxes. One box (26, under the sun) is flat and calm.
- **Bait / hook:** the meaning of that one box goes against self-help and agrees with spiritual teaching. Hook: "Stop fixing yourself. Watch what this box does." It scored 81 (STRONG) on `hookscore.py`.
- **Story arc:** hook on a detail in the painting, then the painting's origin (her own words), then 3–4 book lines, then the turn (her own meaning), then the product rising out of the painting, then the end card (rose logo + "Della Antony").
- **Files:** `reel3/` holds `STORY.md`, `narration.txt`, `book_quotes.md`, and the pipeline (`voice.py`, `render.py`, `music.py`, `mix.py`, `stills.py`, `cutout.py`).

## Order of work (her approval gates; never skip)

1. **Find the painting's meaning.** Search Google Drive for the painting's name and its write-up (Reel 3's came from a product write-up doc). Ask Della for the meaning of any detail you want to build on; never invent it.
2. **Find the hidden detail.** Look closely at the painting for one thing that is different from the rest (Reel 3: the one still box). That detail is usually the hook.
3. **Pick book lines.** The book is `Is It time to wake up 2.pages` (a zip). Unzip it into its own folder, decompress `Index/Document.iwa` (raw snappy chunks; the script used is in Reel 3's session notes: a small pure-Python snappy decoder, then pull long UTF-8 runs). Search the text for words that match the painting's theme, read the passages in context, and copy lines word for word. `reel3/book_quotes.md` has spare water and stillness lines already pulled.
4. **Ask with pop-ups (AskUserQuestion):** the hook detail's meaning, the opening (painting moving vs Della moving), which product photos to use, and length.
5. **Write the story, hook options and shot list.** Score hooks with `.claude/skills/ig-reel/hookscore.py`. Under 50 means no hook yet. Contrarian, true, gentle hooks did best. **Stop for approval.**
6. **Make 1–2 approval stills** of the product moment before building (Reel 3: `still_rise.jpg`, `still_settled.jpg`).
7. **Della records her narration** on her phone. She changes words as she goes. Don't transcribe her: put the matching line from the approved narration on screen while she says that part.
8. **Build:** voice, then frames, then music, then mix (below). Check one frame per scene from the final file. **Show Della before anything is posted.** She posts it herself.
9. **Caption** through `della-antony-instagram`, after she approves the reel.

## Her rules (from her and from `della-hyperframes-video`)

- **Look:**
  - Colours come only from the painting.
  - No black backgrounds, no neon, no gradients, never pink-dominant.
  - No text baked into images. Text lives only in cut-letter tiles: 64 px or larger, 8 words or fewer, held 2 s or more, clear of the right 230 px and between y 230 and 1440.
- **People:**
  - No person ever rises out of the painting. Products appear as the garment alone, cut from the photo, on a white paper border.
  - Never use the mom video (IMG_5597).
  - If anything on screen is AI-made, the caption says so.
- **Sound:**
  - Her own voice or an original score. No AI voice, no licensed songs, no accordion.
- **Book:**
  - It's "a story I wrote", with no title, date or price on screen. The girl is Tamara.
  - Book lines are copied exactly. Never invent a line.
- **Tone:**
  - Gentle for ages 10+.
  - Hooks are true. No rage bait.
  - Never write "hallucination"; say "vision".
- **Pace:**
  - Ask before building, then stop for approval at the story and again at the finished reel.

## Technical recipe (copy `reel3/` to `reel4/` and adapt)

- **Voice (`voice.py`):**
  - Get the word timings with faster-whisper `small.en` in a scratch virtualenv, used only for timing. Load the WAV as a numpy array, because the `av` version clashes.
  - Cut the opening tap and cap pauses at 0.75 s. Keep a longer breath before the key line.
  - Clean and level the voice: highpass, `afftdn`, a light compressor, loudnorm at -18 LUFS.
- **Frames (`render.py`):**
  - Work in painting space, then apply camera keyframes (scale, centre, screen y).
  - Effects: churn displacement per box, a still box, tape-peel grid lines, box pops and a wave, a dive into a calm colour field, the product rising from the water, tiles drifting in, the end card.
  - Wide shots at scale about 1.1, so the boxes read big. Scale 0.78 left too much empty cream.
  - Run `python3 render.py sheet <times>` for a contact sheet before the full render. The full render takes about 12 minutes on 4 CPUs.
- **Music (`music.py`):**
  - Synthesized violin: arco legato, spiccato staccato, pizzicato.
  - Sync notes to the picture: one staccato note per box pop, held notes at the stillness, a crescendo before the turn, a smooth ending.
  - No sampled violin is available in the container (apt has no fluidsynth). Say so honestly.
- **Mix (`mix.py`):**
  - The music sits about 7 LU under the voice and ducks about 6 dB while she speaks.
  - Targets: about -16.5 to -17 LUFS, true peak under -4 dBFS.
  - Use the cumsum moving average. `np.convolve` on full-length audio hangs.
- **Export:**
  - 1080x1920, H.264 CRF 22, AAC 192k, `+faststart`. That gave 24.7 MB for 84 s, under the 30 MiB limit.
- **Getting it to her iPad:**
  - The chat file card can't preview large videos.
  - Publish an Artifact page with the video as a file (15 MB per file limit, so make a copy of about 13 MB) and a Save button using the `downloads` capability. Plain download links don't work in artifacts.
  - Reel 3's page: https://claude.ai/artifact/6mWCtSCFh645e3dRy6ij6R

## Lessons from Reel 3

- Check the box grid and index against the photo before rendering. A one-column slip put the glow on the wrong box.
- Her recording ran 107 s (82 s after trimming), much longer than the 30 s plan. Ask about length before she records, or plan a 30–35 s cut from the start.
- The transcriber heard "can drown the oceans", but the book says "can't". Check any line that matters with her.
- Thin repairs (filling the gaps where a hand covered the garment) are fine in motion but show on stills. Mention them.
- Media files are git-ignored (`reel3/*.mp4|*.wav|*.m4a`). Commit the scripts and docs; deliver the video through chat and the Artifact page.
