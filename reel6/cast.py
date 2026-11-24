"""Reel 6 cast sprites, taken from the approved campaign drawings so every character matches.
- Mum and Dad: elder() from reel5/kochi.py (branch claude/fervent-carson-ftddqc), unchanged.
- The girl: girl.py from reel3 (branch claude/hanta-campaign-video-q564qv), hair down (the straight bob),
  dressed in the Reel 6 dress: fitted racerback tank mini dress, Sunset (2) print turned on its side
  (sun half left, sea half right), rough linen.
- Her friend: the same girl drawing with a headscarf and a long teal tunic.
Usage: python3 cast.py <fervent worktree> <hanta worktree>   -> cast/*.png and cast/cast_sheet.jpg
"""
import os, sys, types
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "cast")
FERV, HANTA = sys.argv[1], sys.argv[2]

def linen(img, k=0.16, seed=7):
    w, h = img.size; r = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32) / 255
    rows = r.normal(0, 1, (h, 1)); cols = r.normal(0, 1, (1, w))
    slub = np.asarray(Image.fromarray((r.random((h // 6, w // 40)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    weave = 0.5 * rows + 0.5 * cols + 1.4 * (slub - 0.5) * (r.random((h, 1)) > 0.7)
    fine = (np.indices((h, w)).sum(0) % 4 < 2) * 0.5 - 0.25
    a = a * (1 + k * np.tanh(weave)[..., None] + 0.025 * fine[..., None])
    g = a.mean(2, keepdims=True); a = g + (a - g) * 0.97 + 0.01
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def dress_print():
    """The artwork turned on its side (sun half left, sea half right), at native resolution, never upscaled.
    A light sharpen, a little more colour, and a fine linen weave."""
    from PIL import ImageEnhance, ImageFilter
    art = os.path.join(HERE, "artwork.jpg")
    p = Image.open(art if os.path.exists(art) else os.path.join(HERE, "sunset2.jpg")).convert("RGB")
    if p.width > p.height: p = p.rotate(90, expand=True)
    p = p.crop((0, 0, int(p.width * 810 / 1083), p.height))
    p = ImageEnhance.Color(p).enhance(1.15); p = ImageEnhance.Contrast(p).enhance(1.06)
    p = p.filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=2))
    return linen(p, k=0.05)

def girl6():
    src = open(os.path.join(HANTA, "reel3", "girl.py")).read()
    src = src.replace('A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")', 'A = %r' % os.path.join(HANTA, "reel3", "assets"))
    src = src.replace("for x in ((-150, -95, -45, 0, 45, 95, 150) if coat != \"on\" else ()):", "for x in ():")
    src = src.replace("f.p(sx * 20, 560), f.p(sx * 19, 760)", "f.p(sx * 21, 500), f.p(sx * 19, 760)")
    # front: scoop-neck tank with wide straps instead of the sweetheart top
    src = src.replace("top_poly = [(-40, 292), (40, 292), (44, 200), (32, 186), (16, 186), (0, 200), (-16, 186), (-32, 186), (-44, 200)]",
                      "top_poly = [(-40, 292), (40, 292), (46, 214), (50, 170), (34, 162), (24, 186), (0, 196), (-24, 186), (-34, 162), (-50, 170), (-46, 214)]")
    src = src.replace("d.line(f.pl([(sx * 34, 188), (sx * 44, 164)]), fill=LINE, width=f.w(2.5))  # thin straps", "pass")
    # back: racerback
    src = src.replace("top_poly = [(-40, 292), (40, 292), (44, 226), (-44, 226)]\n        _tex(fig, PLAIN, f.pl(top_poly))",
                      "top_poly = [(-40, 292), (40, 292), (46, 222), (22, 172), (12, 158), (-12, 158), (-22, 172), (-46, 222)]\n        _tex(fig, SKIRT, f.pl(top_poly))")
    src = src.replace("d.line(f.pl([(-36, 228), (44, 166)]), fill=LINE, width=f.w(2.5))", "pass")
    src = src.replace("d.line(f.pl([(36, 228), (-44, 166)]), fill=LINE, width=f.w(2.5))", "pass")
    src = src.replace('''def _skirt_poly():
    right = [(37, 290), (62, 330), (98, 392), (136, 462), (166, 520), (182, 556)]
    return [(-37, 290)] + right + _wavy_hem(566, 182) + [(-x, y) for x, y in right[::-1]]''', '''def _skirt_poly():
    right = [(38, 290), (50, 330), (56, 400), (56, 470), (54, 524)]
    return [(-38, 290)] + right + [(-x, y) for x, y in right[::-1]]''')
    src = src.replace("    f = Fig(cx, top, height / 975)\n", "    f = Fig(cx, top, height / 975)\n    global _CURF; _CURF = f\n", 1)
    src += """

_tex_orig = _tex
def _tex(layer, tex, poly):
    if tex is not SKIRT and tex is not SPRING:
        return _tex_orig(layer, tex, poly)
    f = _CURF
    (x0, y0), (x1, y1) = f.p(-64, 150), f.p(64, 532)
    x0, y0, x1, y1 = int(x0), int(y0), int(x1) + 1, int(y1) + 1
    w, h = x1 - x0, y1 - y0
    tw = w; th = int(tex.height * w / tex.width)                 # the whole width of the painting across the dress
    one = tex.resize((tw, th), Image.LANCZOS)
    col = Image.new("RGB", (tw, h + th))
    col.paste(one, (0, 0)); y_ = th
    rest = one.crop((0, int(th * 659 / 1390), tw, th))             # below the sun, starting on a grid line: one sun only
    while y_ < h + th:
        col.paste(rest, (0, y_)); y_ += rest.height
    t = col.crop((0, 0, tw, h)).convert("RGBA")
    full = Image.new("RGBA", layer.size, (0, 0, 0, 0)); full.paste(t, (x0, y0))
    m = Image.new("L", layer.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    layer.paste(full, (0, 0), m)
"""
    m = types.ModuleType("girl6"); m.__file__ = os.path.join(HANTA, "reel3", "girl.py")
    exec(compile(src, "girl6", "exec"), m.__dict__)
    pr = dress_print()
    m.SKIRT = pr; m.SPRING = pr
    return m

def save(L, name): L.crop(L.getbbox()).save(os.path.join(OUT, name))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    g = girl6()
    for name, kw in (("girl_front.png", dict(view="front")), ("girl_open.png", dict(view="front", eyes="open")),
                     ("girl_back.png", dict(view="back")), ("girl_seat.png", dict(view="front", pose="seat", arms="knees"))):
        L = Image.new("RGBA", (1100, 1850), (0, 0, 0, 0)); g.draw(L, 550, 90, 1620, **kw); save(L, name)
    L = Image.new("RGBA", (700, 1200), (0, 0, 0, 0)); f = g.draw(L, 350, 60, 1050, view="front", earrings=False)
    d = ImageDraw.Draw(L); LINE = g.LINE; TEAL = (46, 128, 138)
    for sx in (-1, 1): g._limb(d, [f.p(sx * 21, 560), f.p(sx * 19, 760), f.p(sx * 17, 930)], f.w(26), (240, 236, 226), f)
    d.polygon(f.pl([(-54, 164), (54, 164), (72, 200), (64, 300), (96, 600), (-96, 600), (-64, 300), (-72, 200)]), fill=TEAL, outline=LINE, width=f.w(2.5))
    for sx in (-1, 1): d.polygon(f.pl([(sx * 58, 170), (sx * 80, 200), (sx * 96, 330), (sx * 76, 334), (sx * 60, 210)]), fill=TEAL, outline=LINE, width=f.w(2))
    d.polygon(f.pl([(-62, 40), (-56, 0), (-30, -16), (0, -22), (30, -16), (56, 0), (62, 40), (64, 110), (80, 170), (40, 190), (0, 196), (-40, 190), (-80, 170), (-64, 110)]),
              fill=(214, 190, 150), outline=LINE, width=f.w(2.5))
    d.polygon(f.pl([(-42, 40), (-43, 72), (-38, 96), (-23, 110), (0, 117), (23, 110), (38, 96), (43, 72), (42, 40), (26, 26), (0, 22), (-26, 26)]), fill=g.SKIN, outline=LINE, width=f.w(2))
    for sx in (-1, 1):
        d.arc([*f.p(sx * 21 - 11, 62), *f.p(sx * 21 + 11, 76)], 20, 160, fill=LINE, width=f.w(2))
        d.line(f.pl([(sx * 31, 56), (sx * 11, 53)]), fill=LINE, width=f.w(2))
    d.line(f.pl([(3, 74), (-1, 92)]), fill=g.SKIN_SH, width=f.w(2)); d.ellipse([*f.p(-9, 99), *f.p(9, 107)], fill=g.LIP)
    save(L, "friend.png")
    cwd = os.getcwd(); os.chdir(os.path.join(FERV, "reel5")); sys.path.insert(0, os.getcwd())
    import kochi
    kochi.elder("mum").save(os.path.join(OUT, "mum.png")); kochi.elder("dad").save(os.path.join(OUT, "dad.png"))
    kochi.elder("dad", laugh=True).save(os.path.join(OUT, "dad_laugh.png")); os.chdir(cwd)
    names = ["girl_front", "girl_back", "girl_seat", "friend", "mum", "dad", "dad_laugh"]
    ims = [Image.open(os.path.join(OUT, n + ".png")) for n in names]; h = 600
    ims = [i.resize((int(i.width * h / i.height), h), Image.LANCZOS) for i in ims]
    s = Image.new("RGB", (sum(i.width for i in ims) + 20 * (len(ims) + 1), h + 40), (240, 236, 228)); x = 20
    for i in ims: s.paste(i, (x, 20), i); x += i.width + 20
    s.save(os.path.join(OUT, "cast_sheet.jpg"), quality=90)
