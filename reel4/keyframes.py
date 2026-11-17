"""Reel 4 (Reverie) key frames for approval. python3 keyframes.py -> key_*.jpg + keyframes_sheet.jpg"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.join(HERE, "..", "reel2")
os.chdir(R2); sys.path.insert(0, R2)
import lib
os.chdir(HERE)
W, H = lib.W, lib.H

# Painting cut from the Saatchi screenshot. Left 70 px dropped (a sale tab covered it).
PAINT = Image.open("raw_crop.png").convert("RGB").crop((70, 6, 1062, 910))
PAINT.save("reverie.jpg", quality=95)
PW, PH = PAINT.size

INK = (74, 40, 140)            # verandah purple
INK2 = (190, 60, 40)           # wall red
CX, CY = (W - 230) / 2 + 40, 340   # text centre, clear of IG buttons
os.chdir(R2); LOGO = lib.logo_sticker(200); os.chdir(HERE)

def f(im): return np.asarray(im.convert("RGB")).astype(np.float32) / 255
def u8(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def fill_crop(box):
    """Crop painting region and cover the 1080x1920 frame."""
    c = PAINT.crop(box)
    s = max(W / c.width, H / c.height)
    c = c.resize((int(c.width * s) + 1, int(c.height * s) + 1), Image.LANCZOS)
    x, y = (c.width - W) // 2, (c.height - H) // 2
    return f(c.crop((x, y, x + W, y + H)))

def on_paper(box, width, cy):
    img = lib.paper_bg()
    c = PAINT.crop(box)
    c = c.resize((width, int(c.height * width / c.width)), Image.LANCZOS)
    rgba = c.convert("RGBA")
    pad = Image.new("RGBA", (c.width + 24, c.height + 24), (252, 250, 244, 255))
    pad.alpha_composite(rgba, (12, 12))
    return lib.paste_rgba(img, pad, W / 2, cy)

def card(img, text, seed, ink=INK, y=CY, size=72):
    t = lib.ransom(text, ink, size=size, seed=seed, max_w=720)
    return lib.paste_rgba(img, t, CX, y + t.height / 2 - 90)

def mosaic_tiles(n=22, seed=4):
    r = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        x = int(r.integers(0, 480)); y = int(r.integers(740, 830))
        t = PAINT.crop((x, y, x + 60, y + 58)).resize((150, 145), Image.LANCZOS).convert("RGBA")
        t = t.rotate(r.uniform(-7, 7), expand=True, resample=Image.BICUBIC)
        p = Image.new("RGBA", (t.width + 14, t.height + 14), (0, 0, 0, 0))
        m = t.split()[3].filter(ImageFilter.MaxFilter(13))
        p.paste(Image.new("RGBA", m.size, (252, 250, 244, 255)), (7, 7), m); p.alpha_composite(t, (7, 7))
        out.append(p)
    return out

def tee():
    """Oversized tee silhouette printed with Reverie, white paper border."""
    S = 2; w, h = 760, 820
    m = Image.new("L", (w * S, h * S), 0); d = ImageDraw.Draw(m)
    pts = [(250, 20), (310, 60), (380, 75), (450, 60), (510, 20),     # neck
           (700, 120), (760, 330), (640, 370), (610, 300),               # right sleeve
           (615, 800), (145, 800), (150, 300), (120, 370), (0, 330), (60, 120)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=255)
    d.ellipse((310 * S, -20 * S, 450 * S, 70 * S), fill=0)               # neckline scoop
    m = m.resize((w, h), Image.LANCZOS)
    body = Image.new("RGB", (w, h), (24, 22, 20))                         # black tee
    art = PAINT.resize((440, int(PH * 440 / PW)), Image.LANCZOS)          # print on chest
    body.paste(art, ((w - 440) // 2, 170))
    shade = np.ones((h, w, 1), np.float32)
    xs = np.linspace(-1, 1, w)[None, :, None]
    shade *= 1 - 0.10 * xs ** 2                                           # soft fabric falloff
    body = u8(f(body) * shade)
    tee = body.convert("RGBA"); tee.putalpha(m)
    pad = Image.new("RGBA", (w + 28, h + 28), (0, 0, 0, 0))
    mm = m.filter(ImageFilter.MaxFilter(15))
    pad.paste(Image.new("RGBA", (w, h), (252, 250, 244, 255)), (14, 14), mm)
    pad.alpha_composite(tee, (14, 14))
    return pad

frames = {}
# 1. Hook: inside the dark kitchen, the door edge, bright shed beyond (0 s)
img = fill_crop((230, 0, 740, 904))
frames["1_hook_0s"] = card(img, "we want to run home,", 3)
# 2. Cover: whole painting on paper (6 s)
img = on_paper((0, 0, PW, PH), 1040, 1000)
img = card(img, "wherever it may be.", 5, y=300)
frames["2_cover_6s"] = img
# 3. Mosaic floor close-up (8 s)
img = fill_crop((0, 340, 390, 904))
frames["3_mosaic_8s"] = card(img, "We tried the comfortable way.", 8)
# 4. Saffron and white glow (17 s)
img = fill_crop((330, 100, 700, 560))
lum = img.mean(2)
img = lib.screen(img, np.array([1.0, 0.86, 0.5]), np.clip((lum - 0.7) * 2.2, 0, 1) * 0.5)
frames["4_other_way_17s"] = card(img, "So we now try the other way.", 13, ink=INK2)
# 5. The tee rises on the mosaic tiles (23 s)
img = lib.paper_bg()
r = np.random.default_rng(2)
slots = [(x, y) for y in range(140, H, 200) for x in range(90, W, 215)
         if not (200 < x < 880 and 480 < y < 1560) and not (190 < y < 470)]
for (x, y), t in zip(slots, mosaic_tiles(len(slots))):
    img = lib.paste_rgba(img, t, x + r.integers(-10, 10), y + r.integers(-10, 10))
img = lib.paste_rgba(img, tee(), W / 2, 1040)
frames["5_tee_23s"] = card(img, "Wear art, not a logo.", 21)

thumbs = []
for k, a in frames.items():
    im = u8(a); im.save(f"key_{k}.jpg", quality=90)
    thumbs.append(im.resize((360, 640), Image.LANCZOS))
sheet = Image.new("RGB", (360 * 5 + 40, 680), (245, 240, 230))
for i, t in enumerate(thumbs): sheet.paste(t, (10 + i * 366, 20))
sheet.save("keyframes_sheet.jpg", quality=90)
print("ok")
