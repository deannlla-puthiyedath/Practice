"""Reel 3 approval stills: the swimsuit (garment only, no person) rising out of box 26's calm blue.
python3 stills.py -> still_rise.jpg, still_settled.jpg, stills_for_approval.jpg"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REEL2 = os.path.join(HERE, "..", "reel2")
_cwd = os.getcwd(); os.chdir(REEL2); sys.path.insert(0, REEL2)
import lib  # cut-letter tiles + paper weave from Reel 2
LOGO = lib.logo_sticker(200)
os.chdir(_cwd)

W, H = 1080, 1920
PAINT = Image.open(os.path.join(HERE, "sunset2.jpg")).convert("RGB")
P = np.asarray(PAINT).astype(np.float32) / 255
XS = [0, 125, 270, 425, 578, 735, 878, 1020, 1165, 1310, 1390]
YS = [410, 555, 700, 848, 990, 1083]
SEA_INK = (22, 74, 168)
CALM = P[722:830, 600:715].reshape(-1, 3).mean(0)  # box 26's own flat blue


def calm_field(t=0.0):
    """Box 26 filling the screen: its flat blue, slow light ripples, the sun's reflection glowing in it."""
    y, x = np.mgrid[:H, :W].astype(np.float32)
    rip = 0.5 + 0.5 * np.sin(y * 0.045 + 1.3 * np.sin(x * 0.006 + t) + t * 2)
    band = np.exp(-((x - W / 2) / 170) ** 2)  # vertical column of sunlight, like the sun above box 26
    img = CALM[None, None] * (0.94 + 0.05 * rip[..., None])
    img = img + band[..., None] * (0.10 + 0.06 * rip[..., None]) * np.array([1.0, 0.92, 0.55])
    img *= lib.WEAVE[..., None] ** 0.35  # canvas texture
    return np.clip(img, 0, 1)


def sticker(cut, border=16):
    """White paper border round the garment (no black halo), soft drop shadow."""
    a = cut.split()[3]
    pad = border + 12
    big = Image.new("L", (cut.width + pad * 2, cut.height + pad * 2), 0); big.paste(a, (pad, pad))
    edge = big.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: 255 if v > 110 else 0)
    paper = Image.new("RGBA", big.size, (252, 250, 244, 0)); paper.putalpha(edge.filter(ImageFilter.GaussianBlur(0.8)))
    paper.alpha_composite(cut, (pad, pad))
    sh = Image.new("RGBA", big.size, (8, 30, 70, 0)); sh.putalpha(edge.filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 0.35))
    out = Image.new("RGBA", (big.width + 14, big.height + 14), (0, 0, 0, 0))
    out.alpha_composite(sh, (12, 14)); out.alpha_composite(paper, (0, 0))
    return out


def ripples(img, cx, cy, n=4, t=0.0):
    """Light rings on the water where the garment breaks the surface."""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for k in range(n):
        rx = 230 + k * 95 + 20 * t; ry = rx * 0.16
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=int(200 - k * 40), width=6)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    return lib.screen(img, np.array([0.85, 0.93, 1.0]), m * 0.8)


def sea_tiles():
    """The painting's sea boxes as loose tiles (box 26 skipped: it's the one the garment came out of)."""
    tiles = []
    for r in range(4):
        for c in range(1, 9):
            if (r, c) == (2, 5):
                continue
            b = PAINT.crop((XS[c] + 6, YS[r] + 6, XS[c + 1] - 6, YS[r + 1] - 6)).convert("RGBA")
            tiles.append(b)
    return tiles


def card(img, text, y, size=74, seed=3):
    c = lib.ransom(text, SEA_INK, size=size, seed=seed, max_w=600)
    return lib.paste_rgba(img, c, (W - 230) / 2 + 40, y)


CUT = Image.open(os.path.join(HERE, "swimsuit_cut.png")).convert("RGBA")
SUIT = sticker(CUT)


def still_rise():
    img = calm_field(0.4)
    s = SUIT.resize((int(SUIT.width * 1.25), int(SUIT.height * 1.25)), Image.LANCZOS)
    water_y = 1390
    top = water_y - int(s.height * 0.62)  # ~62% of the garment is out of the water
    a = np.asarray(s).astype(np.float32) / 255
    # fade the part still under the surface into the blue
    yy = np.arange(s.height)[:, None] + top
    under = np.clip((yy - water_y) / 60.0, 0, 1)
    a[..., 3] *= (1 - 0.9 * under)
    s2 = Image.fromarray((a * 255).astype(np.uint8), "RGBA")
    img = lib.paste_rgba(img, s2, W / 2, top + s.height / 2)
    img = ripples(img, W / 2, water_y)
    img = card(img, "We listen with a stillness.", 330)
    return img


def still_settled():
    img = calm_field(1.1)
    r = np.random.default_rng(11)
    tiles = sea_tiles(); r.shuffle(tiles)
    # frame of sea boxes around the edges; the middle stays calm for the garment
    slots = [(x, y) for y in range(140, H, 210) for x in range(90, W, 225)
             if not (230 < x < 850 and 470 < y < 1700)]
    for (x, y), t in zip(slots, tiles):
        t = t.resize((190, 182)).rotate(r.uniform(-6, 6), expand=True, resample=Image.BICUBIC)
        pad = Image.new("RGBA", (t.width + 14, t.height + 14), (0, 0, 0, 0))
        wm = t.split()[3].filter(ImageFilter.MaxFilter(13))
        wh = Image.new("RGBA", pad.size, (252, 250, 244, 0)); wh.paste(Image.new("RGBA", wm.size, (252, 250, 244, 255)), (7, 7), wm)
        wh.alpha_composite(t, (7, 7))
        img = lib.paste_rgba(img, wh, x + r.integers(-12, 12), y + r.integers(-10, 10))
    s = SUIT.resize((int(SUIT.width * 1.25), int(SUIT.height * 1.25)), Image.LANCZOS)
    img = lib.paste_rgba(img, s, W / 2, 1090)
    img = card(img, "We listen with a stillness.", 330)
    return img


def to_pil(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    a, b = to_pil(still_rise()), to_pil(still_settled())
    a.save(os.path.join(HERE, "still_rise.jpg"), quality=92)
    b.save(os.path.join(HERE, "still_settled.jpg"), quality=92)
    sheet = Image.new("RGB", (W + 40 + W, H), (244, 239, 230))
    sheet.paste(a, (0, 0)); sheet.paste(b, (W + 40, 0))
    sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(os.path.join(HERE, "stills_for_approval.jpg"), quality=90)
    print("ok")
