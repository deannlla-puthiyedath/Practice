# Campaign handoff: "A day in the dress" reel series (Reverie is Reel 4)

Paste the block under "Paste this into the new chat". Then attach the new painting, `Is It time to wake up 2.pages`, and the Reverie final video as reference.

## Paste this into the new chat

> Make my next reel in the same campaign as Reverie (Reel 4). Read `reel4/CAMPAIGN_TEMPLATE_HANDOFF.md` and `HANDOFF_next_reel.md` in the Practice repo first (the second is on branch `claude/vibrant-bardeen-intq1m`), and follow them. Reuse the code in `reel4/` (render.py, dress.py, music_violin.py) and keep the same two parents, the same girl, the same style and the same violin-only sound. Load my skills della-hyperframes-video, della-antony-instagram, della-master-advisor and della-creative-math. I'm attaching the new painting, the book file and the Reverie final video as reference. New subject: {{painting name}}. Ask me with pop-ups, show me the story and shot list, then make 4 or 5 key frames and stop for my approval before building. My voiceover goes in last.

## The campaign in one paragraph

Each reel is a drawn, cut-paper fashion story, about 32 s, 1080x1920. A girl wears a dress printed from ONE of Della's paintings and spends a happy day in Fort Kochi (street, bakery, scooter ride, heritage house). She ends in the courtyard with her parents. Last, the camera pushes into the painting and the full artwork is revealed. Words on screen are ONLY lines copied exactly from Della's book. Music is violin only. Rose logo and "Wear art, not a logo." end card. Della records her voiceover last.

## Fixed cast (final, approved. Do not change)

- **The girl.** Hair in a high bun, closed eyes with lashes, gold hoop earrings, fine gold necklace, gold clutch, gold bracelet, gold ankle straps and heels. Skin (176,120,88). Drawn as a flat cut-paper sketch with a black outline and a white paper border. Body and face built in `reel4/dress.py` (`figure(view, flare, spin)`).
- **Mum (about 50).** Simple red kurti (196,40,44), fitted at the waist and curvier at the hips, V neck, side slits. White pants, flat sandals, gold bangles, small gold studs, red bindi. Long straight black hair down over each shoulder to the waist, one soft grey strand. Neck and chest must stay visible in the middle (an earlier version looked like a burqa).
- **Dad (about 50).** Taller and chubby all over (round face with rosy cheeks, soft double chin, thick neck, broad rounded shoulders, full arms), fair skin (228,188,156). Pale blue half-sleeve shirt with buttons, checked kaili lungi (purple with green and saffron stripes), watch, black hair with grey temples, moustache. Laughs in the final courtyard beat.
- Both parents are built in `elder(kind)` in `reel4/render.py`. The approved look is the picture `reel4/parents.jpg`. Never redraw them.

## Dress rule (the template)

- Spaghetti-strap princess dress, flowy, above the knee, front and back.
- **Rough linen texture** like the painting's canvas (function `linen()` in dress.py).
- **Bodice = the "subject" of the painting** (for Reverie: the house seen through the door).
- **Skirt and the whole back = the painting's background pattern, tiled and mirrored** (for Reverie: the black and yellow-green leaves, colours boosted a little).
- Remove any small flag, sign or political symbol from the print.
- For a new painting: change `PAINT` (the crop), the bodice crop box in `_house_print()` and the strip crop in `_foliage_tile()`. Keep everything else.
- Dress shows as a design sketch. The caption must say it's a design/mockup. No AI label needed if everything is drawn in code.

## Fixed world (reused scenes, all in `reel4/render.py`)

| Seconds | Shot | Notes |
|---|---|---|
| 0 to 3.4 | Street twirl | Heritage buildings, striped awning, bougainvillea, birds, Chinese fishing net dipping |
| 3.4 to 8.2 | Bakery | Bread window, café table with steam, a paper bag with a French loaf appears |
| 8.2 to 13.8 | Scooter ride | Saffron scooter (generic Italian shape, no brand), seafront with palms, nets, rushing road lines |
| 13.8 to 17.4 | Heritage house | Looks like a FACE from the street: roof = hair, two blinking shuttered windows = eyes, carved door = mouth that opens. She walks in from behind |
| 17.4 to 23.6 | Courtyard (nalukettu) | Four sloping tiled roofs, open sky, wooden pillars, lotus pond, tulsi stand, brass lamp, butterflies. She hands bags to Mum and Dad, kisses Mum's cheek, a heart floats up |
| 23.6 to 28.4 | Reveal | Camera pushes through the kitchen door and it becomes the painting on cream paper |
| 28.4 to 32 | End card | Rose logo, "Della Antony", "Wear art, not a logo." |

Customize per reel: the **errand** (bread and scooter can change, e.g. flowers, fish, books), the **time of day**, the **colours** (all taken from the new painting), and the **text lines**. Keep the cast, the heritage house and the courtyard.

## Look rules

- All colours come from the painting being featured. Reverie palette: black, yellow-green, saffron, purple, green, red, white, mosaic (blue, red, orange, white).
- No black backgrounds, no neon, no gradients, never pink-dominant.
- Text only in cut-letter tiles (`lib.ransom`), 64 px or larger, 8 words or fewer per screen, held 2 s or more, clear of the right 230 px, between y 230 and 1440.
- No text baked into images. Canvas grain overlay on every frame.
- Never name a real brand, character, film or other artist. Gentle for ages 10+. No rage bait.
- Never use the mom video (IMG_5597). The word "hallucination" is banned (say "vision").
- The painting appears ONLY at the end (as Della asked), with no words about it.

## Words on screen: rule and Reverie example

- Copy lines word for word from the book. Never invent or shorten mid-sentence. Show the WHOLE sentence across several screens.
- The book is "a story I wrote". No title, date or price. The girl in the book is Tamara.
- Reverie used this sentence (from the book): "What if I told you everything that you have built, all the kindness and love has made a place in a far away land to be matters of indivisible beauty, will you ever stop?" Split over 7 screens.
- How to extract the book text: unzip the `.pages` file into its own folder, snappy-decode `Index/Document.iwa` (small pure-Python decoder), pull long UTF-8 runs. Search the text for words that match the painting's theme, read passages in context.
- **Spare home mini-stories already found in the book** (all exact): the sailors ("So we set out sailing from the comfort island... Here is the joke - We have sailed so far to a new land only to build the same old house we had before and never leave the gates."); the farmer ("I am a farmer. I water the plants I have." / "he kept his world simple"); the tree ("I was a tree in it and on it. With roots and stuff."); "we want to run home, wherever it may be."; "but we know what doesn't take us home."; "they all go home together."; "the absolute truth is the home to ALL relative truths".

## Music (violin only, synthesized)

- File: `reel4/music_violin.py` (reuses Reel 3's violin synth: arco, spiccato, pizzicato). D major, 104 bpm.
- **Della's rules:** violin ONLY. No other instrument. **No plucked (pizzicato) sound** (she hated it, so the code turns every pluck into a soft bowed note and drops the low bass). **Nothing five-note (pentatonic)**: it sounded like traditional Chinese music. No accordion, no AI voice, no licensed songs.
- Sections (name and feeling): Waltz 0 to 8.2 s (joy, sway, 3/4, oom-pah-pah) / Moto perpetuo 8.2 to 13.8 s (breeze, freedom) / Ritardando 13.8 to 17.4 s (arriving) / Cantabile 17.4 to 23.6 s (warm, love, second violin a third below) / Crescendo 23.6 to 28.4 s (awe at the reveal) / Coda 28.4 to 32 s (rest).
- To customize: keep violin and the section names, change the notes and tempo to suit the new painting's mood. Offer Della a pool to pick from: waltz, café musette (no accordion), Carnatic violin in a bright raga (Kalyani), dreamy film score.
- Music is synthesized, so say honestly it won't sound like a live player.

## Build recipe

1. `python3 render.py sheet <times>` for a contact sheet. `python3 render.py full` makes `frames.mp4` (about 3 minutes on 4 CPUs). Speed trick already in place: `dress.dilate()` and a cached linen print.
2. `python3 music_violin.py` makes `music.wav`.
3. Mix and export (target about -16.5 LUFS, true peak under -4 dBFS):
   `ffmpeg -y -i frames.mp4 -i music.wav -filter_complex "[1:a]alimiter=limit=0.3:level=false,volume=1.6,loudnorm=I=-16.8:TP=-6:LRA=11,alimiter=limit=0.5:level=false[a]" -map 0:v -map "[a]" -c:v libx264 -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart reel.mp4`
4. Check one frame per scene before showing. File size under 30 MiB (Reverie was 7 MB).
5. **Voiceover last:** Della records about 30 s on her phone and may change words. Don't transcribe her. Mix her voice in with the violin ducked about 6 dB under it.
6. Pinterest pin: a 1000x1500 still from the courtyard scene (`ffmpeg -ss 20.6 ... crop=1080:1620:0:150,scale=1000:1500`).
7. Caption through `della-antony-instagram` (template in `reel4/CAPTION.md`), then `della-humanizer`. Della posts it herself. Never log in to Instagram.

## Order of work (approval gates, never skip)

1. Ask with pop-ups (painting meaning, errand, book lines, length, music style).
2. Show the story and shot list. **Stop for approval.**
3. Make 4 or 5 key frames. **Stop for approval.**
4. Build. Show Della the reel.
5. Della records the voiceover. Mix it in. Show again.
6. Caption, pin, schedule (she posts).

## Lessons from Reverie

- Della's first approval always wants changes to people: make the parents the same drawing style as the girl, never a different style.
- Show a close-up image of any character change, because small stills hide faces.
- Her words on screen must be complete and exact.
- Check peak level after every mix (the first mixes were over -4 dBFS).
- The first 7 seconds matter most for the music.

## Where things are

- Code and frames: Practice repo, branch `claude/eloquent-ritchie-b1p06r`, folder `reel4/` (also `reel3/` and `reel2/lib.py`, which holds the cut-letter and paper helpers).
- Video files are git-ignored. **Della should save the final mp4 from chat and attach it as reference in the new chat.** Also attach the Reverie painting and the character picture (`reel4/parents.jpg`) so the cast carries over.
