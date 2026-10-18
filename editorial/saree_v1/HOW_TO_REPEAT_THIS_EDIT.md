# How to repeat the Della editorial edit in another chat

Paste the block below into a new Claude Code (or Cowork) chat, attach the photo, and attach or point to the `scripts/` folder (it holds SKILL.md and the five scripts that made the saree edit).

---
## Prompt to paste

You are a senior photo editor and retoucher for Vogue India and Vanitha editorials. Edit the attached photo of me (Della) so it looks like a fashion-magazine editorial image, using only classic edits on a copy.

Use the skill file `scripts/SKILL.md` as the rulebook, and `scripts/*.py` as a working starting point (adapt the coordinates to the new photo; they are tuned to the saree photo).

HARD LIMITS
- Never change my face, expression, body, skin tone or skin texture. No smoothing, slimming, lightening or darkening of skin. Keep my own hair pixels exactly as shot (no recolouring, no smoothing, no trimming).
- No AI generation or face-swap. Only crop, mask, small inpainting, compositing, light, colour.
- No text, logos or watermarks. Upscale at most 2x. Work on copies only.

PIPELINE (save each stage as a file, say "done" + path after each)
1. Show me a 5-line diagnosis of what looks homemade and STOP for my OK.
2. 01_crop: 4:5 crop, cut ceiling/fan/empty floor, hero on a third.
3. 02_clean: inpaint small distractions (frames, switches, fittings) with tight masks; recolour any visible bra/tank strap to a blouse tone matching the garment and tell me.
4. Cut-out (rembg isnet-general-use with alpha matting). Keep only the largest component, remove leftover background bits with colour-aware masks (not hard rectangles).
5. 03_bg: two looks. Heritage = keep the real setting, darken and lightly desaturate it, vignette. Studio = seamless backdrop with a radial gradient (deep teal #1F3B3A for red/gold silk; bone #F0EBE2 or taupe #8C7B6B for others).
6. 04_light: one soft directional key light, gently lift face shadows.
7. 05_grade: deeper richer garment colour (not neon), warm the zari/jewellery only in the border area, gentle S-curve, 0.7% grain on non-skin only. Skin is protected: lightness within +-3 and colour within +-2 of the original, and the skin mask must be multiplied by the subject alpha.
8. Restore my original hair pixels from the cleaned crop (mask = dark pixels inside the subject alpha).
9. Check: before/after side-by-side and a face-crop comparison; print the face dL/da/db (must stay under about 1.5 L*). Look for halos, ghost bits, mismatched light.
10. Export: full-res 2x JPG q95, a version under 2 MB, and 1080x1350, named della_[hero]_[mood]_v1.jpg.

Ask before installing anything beyond Pillow, opencv-python, numpy, rembg, onnxruntime, ffmpeg, and before writing outside the output folder.
In the final message list what changed (5 bullets per version) and what could not be fixed.
---

## Lessons from the saree run (tell the new chat)
- Gate the skin-protection mask with the subject alpha, or original background pixels leak into the studio version as debris.
- Remove leftover background with colour-aware masks; hard rectangles leave visible straight edges.
- Limit zari/gold warming to the border area; otherwise it mottles the silk.
- Restore original hair last, using a mask inside the subject alpha, and fill the studio backdrop behind it by inpainting (a plain blur leaves a visible box).
- Motion-blurred hands leave ghosts of the old background; accept a little ghost rather than cut into fingers.
- Source resolution is the limit: a 1242 px photo will look soft at 2x. Ask for the sharpest original or a video frame.
- Faces: closed lips and open mouths are never fixed here (that would need regeneration, which is banned). Pick a better frame instead.
