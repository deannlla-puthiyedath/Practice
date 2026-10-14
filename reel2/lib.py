"""Reel 2 renderer pieces: painting, sun ring, rays, face, halo, wings, textures."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
ORANGE = np.array([228, 73, 14]) / 255
YELLOW = np.array([232, 208, 38]) / 255
BLUE = np.array([36, 70, 127]) / 255
MAGENTA = np.array([173, 51, 97]) / 255
GOLD = np.array([245, 196, 70]) / 255
SUNLIGHT = np.array([255, 226, 110]) / 255
INK = np.array([18, 18, 22]) / 255

rng = np.random.default_rng(7)
PAD = 900

# ---------- painting ----------
_paint = np.asarray(Image.open("fraternizing.jpeg").convert("RGB")).astype(np.float32) / 255
SUN_C = np.load("sun.npy")[:2]
SUN_R = float(np.load("sun.npy")[2])
SC = SUN_C + PAD  # sun centre in padded coords
# off-canvas fill: yellow canvas outside the sun, orange paint inside it (the sun runs past the top/left edge)
def _flat(p):
    lo = np.asarray(Image.fromarray((p * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))).astype(np.float32) / 255
    return np.clip(p - lo + p.reshape(-1, 3).mean(0), 0, 1)


def _tile(patch, h, w):
    patch = _flat(patch)
    # mirror-tile so there are no hard seams
    p2 = np.concatenate([patch, patch[:, ::-1]], 1)
    p2 = np.concatenate([p2, p2[::-1]], 0)
    reps = (h // p2.shape[0] + 1, w // p2.shape[1] + 1, 1)
    return np.tile(p2, reps)[:h, :w]
_ph, _pw = _paint.shape[0] + 2 * PAD, _paint.shape[1] + 2 * PAD
_r = np.random.default_rng(1)
_wv = np.asarray(Image.fromarray((_r.random((_ph // 4, _pw // 4)) * 255).astype(np.uint8)).resize((_pw, _ph), Image.BICUBIC)).astype(np.float32) / 255
_yy, _xx = np.mgrid[:_ph, :_pw]
_tex = (1 + 0.05 * (np.sin(_xx * 1.15) * np.sin(_yy * 1.15)) + 0.08 * (_wv - 0.5) + 0.04 * (_r.random((_ph, _pw)) - 0.5))[..., None]
_yel = (_paint[1700:2100, 40:180].reshape(-1, 3).mean(0) * _tex).astype(np.float32)
_org = (_paint[300:560, 300:560].reshape(-1, 3).mean(0) * _tex).astype(np.float32)
del _yy, _xx, _wv, _tex
_gy, _gx = np.mgrid[:_ph, :_pw]
_ins = np.hypot(_gx - SC[0], _gy - SC[1]) < SUN_R
PAINT = np.where(_ins[..., None], _org, _yel).astype(np.float32)
_cm = np.zeros((_ph, _pw), np.float32); _cm[PAD + 20:PAD + _paint.shape[0] - 20, PAD + 20:PAD + _paint.shape[1] - 20] = 1
_cm = np.asarray(Image.fromarray((_cm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32)[..., None] / 255
_full = PAINT.copy(); _full[PAD:PAD + _paint.shape[0], PAD:PAD + _paint.shape[1]] = _paint
PAINT = (_full * _cm + PAINT * (1 - _cm)).astype(np.float32)
del _cm, _full
del _yel, _org, _gy, _gx, _ins

# ring mask: the real painted outline (dark pixels in a band round the fitted circle)
yy, xx = np.mgrid[:PAINT.shape[0], :PAINT.shape[1]]
_dd = np.hypot(xx - SC[0], yy - SC[1])
_band = np.abs(_dd - SUN_R) < 26
_dark = PAINT.sum(2) < 0.95
RING = (_band & _dark).astype(np.float32)
# arcs off the canvas edge: the reflect pad mirrors them wrongly, so redraw those with a crayon line
_inside = (xx >= PAD) & (xx < PAD + _paint.shape[1]) & (yy >= PAD) & (yy < PAD + _paint.shape[0])
RING[~_inside] = 0
_miss = (~_inside) & (np.abs(_dd - SUN_R) < 6.5)
RING = np.maximum(RING, _miss * (rng.random(RING.shape) > 0.25))
RING = np.asarray(Image.fromarray((RING * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
del yy, xx, _dd, _band, _dark, _inside, _miss


def crop_affine(img, cx, cy, scale, rot=0.0, out=(W, H), center=(W / 2, H / 2), order=Image.BILINEAR):
    """Render img so that point (cx,cy) lands at `center`, scaled and rotated (deg, clockwise)."""
    a = np.deg2rad(rot)
    ca, sa = np.cos(a) / scale, np.sin(a) / scale
    ox, oy = center
    # output->input mapping: x_in = ca*(x-ox) + sa*(y-oy) + cx ...
    coeffs = (ca, sa, cx - ca * ox - sa * oy, -sa, ca, cy + sa * ox - ca * oy)
    if img.ndim == 3:
        pim = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        return np.asarray(pim.transform(out, Image.AFFINE, coeffs, order)).astype(np.float32) / 255
    pim = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "L")
    return np.asarray(pim.transform(out, Image.AFFINE, coeffs, order)).astype(np.float32) / 255


# ---------- textures ----------
def canvas_weave(h=H, w=W, k=0.06):
    y, x = np.mgrid[:h, :w]
    weave = 0.5 + 0.25 * np.sin(x * 1.9) * np.sin(y * 1.9) + 0.25 * np.sin((x + y) * 0.45)
    grain = rng.random((h, w))
    return 1 - k * (0.6 * weave + 0.4 * grain)


WEAVE = canvas_weave()


def paper_bg():
    base = np.ones((H, W, 3), np.float32) * np.array([0.985, 0.975, 0.955])
    return base * WEAVE[..., None] ** 0.6


def glow(mask, radius):
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius))).astype(np.float32) / 255


def screen(base, col, a):
    return 1 - (1 - base) * (1 - col * a[..., None])


def over(base, col, a):
    a = a[..., None]
    return base * (1 - a) + col * a


# ---------- sun rays (soft, flowing, yellow) ----------
def rays(cx, cy, r, t, strength):
    y, x = np.mgrid[:H, :W].astype(np.float32)
    dx, dy = x - cx, y - cy
    ang = np.arctan2(dy, dx)
    d = np.hypot(dx, dy)
    flow = 0.55 + 0.45 * np.sin(ang * 14 + t * 0.6 + 2.0 * np.sin(d / 180 - t * 1.4))
    flow *= 0.6 + 0.4 * np.sin(ang * 5 - t * 0.35)
    fall = np.exp(-np.maximum(d - r, 0) / (r * 0.9)) * (d > r * 0.9)
    halo = np.exp(-np.abs(d - r) / (r * 0.18))
    return np.clip((flow * fall * 0.75 + halo * 0.35) * strength, 0, 1)


# ---------- star doodle ----------
def star_pts(cx, cy, R, rot=0, n=5):
    pts = []
    for i in range(n * 2):
        rr = R if i % 2 == 0 else R * 0.45
        a = rot + i * np.pi / n - np.pi / 2
        pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))
    return pts


def crayon_line(draw, pts, col, w, jitter=1.2, passes=2, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    for _ in range(passes):
        jp = [(x + rng.normal(0, jitter), y + rng.normal(0, jitter)) for x, y in pts]
        draw.line(jp, fill=col, width=w, joint="curve")


def grain_mask(a, keep=0.78):
    return a * (rng.random(a.shape) < keep)


# ---------- face (kajal eyes, smile, wink) ----------
def face_layer(cx, cy, r, wink, smile=1.0, ss=2):
    """Returns (rgb, alpha). wink: 0 open .. 1 right eye shut."""
    w, h = W * ss, H * ss
    cx, cy, r = cx * ss, cy * ss, r * ss
    rgb = Image.new("RGB", (w, h), (0, 0, 0))
    al = Image.new("L", (w, h), 0)
    dr, da = ImageDraw.Draw(rgb), ImageDraw.Draw(al)
    ink = (20, 22, 40)
    ew, eh = r * 0.30, r * 0.15
    for side in (-1, 1):
        ex, ey = cx + side * r * 0.36, cy - r * 0.12
        closed = wink if side == 1 else 0.0
        hh = eh * (1 - closed)
        if hh > eh * 0.12:
            # almond: two arcs
            top = [(ex - ew + 2 * ew * u, ey - hh * np.sin(np.pi * u) ** 0.8) for u in np.linspace(0, 1, 40)]
            bot = [(ex + ew - 2 * ew * u, ey + hh * 0.75 * np.sin(np.pi * u) ** 0.9) for u in np.linspace(0, 1, 40)]
            dr.polygon(top + bot, fill=(250, 248, 240)); da.polygon(top + bot, fill=255)
            ir = min(hh, eh) * 0.82
            dr.ellipse((ex - ir, ey - ir * 0.95, ex + ir, ey + ir * 0.95), fill=(28, 30, 52))
            dr.ellipse((ex - ir * 0.25 + ir * 0.3, ey - ir * 0.55, ex + ir * 0.25 + ir * 0.3, ey - ir * 0.05), fill=(250, 248, 240))
            # re-clip iris to almond
            m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(top + bot, fill=255)
            rgb = Image.composite(rgb, Image.new("RGB", (w, h), (0, 0, 0)), Image.composite(m, Image.new("L", (w, h), 255), al))
            dr = ImageDraw.Draw(rgb)
            # kajal: thick upper line with flick, thinner lower line
            flick = [(ex + side * ew, ey), (ex + side * ew * 1.32, ey - eh * 0.55)]
            dr.line(top, fill=ink, width=int(r * 0.045), joint="curve"); da.line(top, fill=255, width=int(r * 0.045), joint="curve")
            dr.line(bot, fill=ink, width=int(r * 0.022), joint="curve"); da.line(bot, fill=255, width=int(r * 0.022), joint="curve")
            dr.line(flick, fill=ink, width=int(r * 0.035)); da.line(flick, fill=255, width=int(r * 0.035))
        else:
            # closed: a happy curved lash line with kajal flick + three lashes
            arc = [(ex - ew + 2 * ew * u, ey + eh * 0.35 * np.sin(np.pi * u)) for u in np.linspace(0, 1, 40)]
            dr.line(arc, fill=ink, width=int(r * 0.05), joint="curve"); da.line(arc, fill=255, width=int(r * 0.05), joint="curve")
            fl = [(ex + side * ew, ey), (ex + side * ew * 1.3, ey - eh * 0.5)]
            dr.line(fl, fill=ink, width=int(r * 0.035)); da.line(fl, fill=255, width=int(r * 0.035))
            for u in (0.3, 0.5, 0.7):
                bx, by = ex - ew + 2 * ew * u, ey + eh * 0.35 * np.sin(np.pi * u)
                seg = [(bx, by), (bx + (u - 0.5) * ew * 0.5, by + eh * 0.55)]
                dr.line(seg, fill=ink, width=int(r * 0.022)); da.line(seg, fill=255, width=int(r * 0.022))
    # smile
    sm = [(cx - r * 0.34 + r * 0.68 * u, cy + r * 0.28 + smile * r * 0.17 * np.sin(np.pi * u)) for u in np.linspace(0, 1, 50)]
    dr.line(sm, fill=ink, width=int(r * 0.045), joint="curve"); da.line(sm, fill=255, width=int(r * 0.045), joint="curve")
    # cheeks (magenta crayon blush)
    for side in (-1, 1):
        bx, by = cx + side * r * 0.55, cy + r * 0.18
        dr.ellipse((bx - r * 0.1, by - r * 0.05, bx + r * 0.1, by + r * 0.05), fill=(173, 51, 97))
        da.ellipse((bx - r * 0.1, by - r * 0.05, bx + r * 0.1, by + r * 0.05), fill=110)
    rgb = rgb.resize((W, H), Image.LANCZOS); al = al.resize((W, H), Image.LANCZOS)
    a = np.asarray(al).astype(np.float32) / 255
    return np.asarray(rgb).astype(np.float32) / 255, grain_mask(a, 0.93)


# ---------- halo ----------
def halo_layer(cx, cy, rw, tilt_deg, t, ring_col):
    """The real painted ring, squashed by tilt, painted gold, with dispersing light, dots and stars."""
    sy = np.cos(np.deg2rad(tilt_deg))
    s = rw / SUN_R
    # sample the ring from padded painting space with anisotropic scale
    sc = rw / SUN_R
    coeffs = (1 / sc, 0, SC[0] - W / 2 / sc + (W / 2 - cx) / sc, 0, 1 / (sc * sy), SC[1] - (cy) / (sc * sy))
    pim = Image.fromarray((RING * 255).astype(np.uint8), "L")
    a = np.asarray(pim.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)).astype(np.float32) / 255
    a = np.clip(a * 1.6, 0, 1)
    # thicken into a painted band
    band = glow(a, 2.0) * 3
    band = np.clip(np.maximum(a, band), 0, 1)
    light = glow(band, 16) * 1.8 + glow(band, 60) * 1.4
    # dotted ring + stars on a separate layer
    deco = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(deco)
    for i in range(64):
        ang = i / 64 * 2 * np.pi + t * 0.25
        x, y = cx + rw * 1.16 * np.cos(ang), cy + rw * 1.16 * sy * np.sin(ang)
        rr = 3.2
        dd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=230)
    srng = np.random.default_rng(3)
    for i in range(9):
        ang = i / 9 * 2 * np.pi + 0.3 + t * 0.12
        rad = rw * (1.32 + 0.12 * srng.random())
        x, y = cx + rad * np.cos(ang), cy + rad * sy * np.sin(ang) - 10
        R = 11 + 7 * srng.random()
        tw = 0.75 + 0.25 * np.sin(t * 3 + i)
        crayon_line(dd, star_pts(x, y, R * tw, srng.random()), 255, 3, jitter=0.6, closed=True)
    deco = np.asarray(deco).astype(np.float32) / 255
    return band, light, deco


# ---------- wings ----------
WING_COLS = [ORANGE, MAGENTA, YELLOW, BLUE]


def feather_poly(bx, by, ang, L, w, curl=0.08):
    """Long narrow feather from base (bx,by) pointing at angle ang (rad), pointed tip, slight curve."""
    d = np.array([np.cos(ang), np.sin(ang)]); n = np.array([-d[1], d[0]])
    left, right = [], []
    for u in np.linspace(0, 1, 18):
        c = np.array([bx, by]) + d * L * u + n * L * curl * u * u
        hw = w * (0.55 + 0.45 * np.sin(np.pi * min(u * 1.05, 1)) ** 0.7) * (1 - u ** 3)
        left.append(tuple(c + n * hw)); right.append(tuple(c - n * hw))
    tip = tuple(np.array([bx, by]) + d * L + n * L * curl)
    return left + [tip] + right[::-1], (bx, by), tip


def wing_layer(side, progress, ss=2):
    """Right wing (side=1) or mirrored left (side=-1). progress 0..1 = how much has 'appeared'.
    Returns rgb, alpha at frame size."""
    w, h = W * ss, H * ss
    rgb = np.zeros((h, w, 3), np.float32); al = np.zeros((h, w), np.float32)
    root = np.array([690.0, 700.0]) * ss
    wrist = np.array([1030.0, 200.0]) * ss
    ctrl = np.array([730.0, 230.0]) * ss
    frng = np.random.default_rng(11)
    rows = [  # (count, length range, width, colour idx cycle, arm offset)
        (16, (600, 1120), 24, [3], 0.0),
        (14, (380, 700), 25, [1], 0.02),
        (12, (200, 380), 26, [0], 0.04),
        (11, (80, 125), 24, [2], 0.06),
    ]
    order = 0
    total = sum(r[0] for r in rows)
    for ri, (cnt, (l0, l1), fw, cyc, off) in enumerate(rows):  # long rows drawn first, coverts layered over
        for i in range(cnt):
            u = (i + 0.5 * (ri % 2)) / (cnt - 0.5)
            u = min(u, 1.0)
            uu = off + (1 - off) * u
            # arm: quadratic bezier root->ctrl->wrist
            p = (1 - uu) ** 2 * root + 2 * (1 - uu) * uu * ctrl + uu ** 2 * wrist
            # direction: near root points down-out, near wrist points up-out
            a0, a1 = np.deg2rad(84), np.deg2rad(52)
            ang = a0 + (a1 - a0) * (u ** 1.6) + frng.normal(0, 0.015)
            L = (l0 + (l1 - l0) * u ** 0.8) * ss
            # staggered appearance: inner coverts first, flight feathers last, sweep root->tip
            k = (order / total)
            appear = np.clip((progress * 1.6 - (0.45 * (3 - ri) / 3 + 0.5 * u) * 0.9), 0, 1)
            order += 1
            if appear <= 0:
                continue
            ease = 1 - (1 - appear) ** 3
            poly, base, tip = feather_poly(p[0], p[1], ang + (1 - ease) * 0.5, L * (0.35 + 0.65 * ease), fw * ss)
            col = WING_COLS[cyc[i % len(cyc)]]
            m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
            # bounding box to keep it cheap
            xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            x0, x1 = int(max(min(xs) - 8, 0)), int(min(max(xs) + 8, w)); y0, y1 = int(max(min(ys) - 8, 0)), int(min(max(ys) + 8, h))
            if x1 <= x0 or y1 <= y0:
                continue
            mm = np.asarray(m.crop((x0, y0, x1, y1))).astype(np.float32) / 255
            # impasto streaks along the feather: lighter + darker strokes
            st = Image.new("L", (x1 - x0, y1 - y0), 128); sd = ImageDraw.Draw(st)
            dv = np.array([np.cos(ang), np.sin(ang)]); nv = np.array([-dv[1], dv[0]])
            for s_ in range(9):
                o = frng.uniform(-0.8, 0.8) * fw * ss * 0.8
                a_ = np.array(base) + nv * o - [x0, y0]
                b_ = a_ + dv * L * frng.uniform(0.4, 0.95)
                sd.line([tuple(a_), tuple(b_)], fill=int(frng.choice([70, 190, 215])), width=int(frng.uniform(2, 5) * ss))
            st = np.asarray(st.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
            shade = 0.82 + 0.4 * (st - 0.5)
            fc = np.clip(col * shade[..., None], 0, 1)
            # rachis
            rm = Image.new("L", (x1 - x0, y1 - y0), 0)
            ImageDraw.Draw(rm).line([tuple(np.array(base) - [x0, y0]), tuple(np.array(base) + dv * L * 0.85 - [x0, y0])], fill=255, width=int(2 * ss))
            rm = np.asarray(rm).astype(np.float32) / 255 * mm
            lite = np.clip(col * 0.6 + 0.4, 0, 1)
            fc = fc * (1 - rm[..., None] * 0.6) + lite * rm[..., None] * 0.6
            # grainy pastel outline (dark blue)
            edge = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(np.float32) / 255
            edge = np.clip(edge - mm, 0, 1)
            edge = edge * (frng.random(edge.shape) < 0.72)
            sub_rgb = rgb[y0:y1, x0:x1]; sub_a = al[y0:y1, x0:x1]
            fa = mm * ease
            sub_rgb[:] = sub_rgb * (1 - fa[..., None]) + fc * fa[..., None]
            ea = edge * ease
            sub_rgb[:] = sub_rgb * (1 - ea[..., None]) + BLUE * 0.7 * ea[..., None]
            sub_a[:] = np.maximum(sub_a, np.maximum(fa, ea))
    # canvas weave + grain over whole wing
    rgbi = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    ali = Image.fromarray((np.clip(al, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    rgb = np.asarray(rgbi).astype(np.float32) / 255 * (WEAVE[..., None] ** 1.6)
    al = np.asarray(ali).astype(np.float32) / 255
    if side == -1:
        rgb = rgb[:, ::-1]; al = al[:, ::-1]
    return rgb, al


def doodles(t, seed=5):
    """Child crayon doodles in painting colours: tiny suns, squiggles, stars. Kept to the edges."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    cols = [tuple(int(c * 255) for c in k) + (235,) for k in (ORANGE, MAGENTA, BLUE, YELLOW)]
    spots = [(120, 1560), (930, 1610), (160, 260), (880, 1760), (300, 1780)]
    for i, (x, y) in enumerate(spots):
        c = cols[i % 4]
        kind = i % 3
        if kind == 0:  # squiggle
            pts = [(x + k * 14, y + 14 * np.sin(k * 1.3 + t * 2)) for k in range(9)]
            crayon_line(d, pts, c, 6, jitter=1.4)
        elif kind == 1:  # little scribble sun
            crayon_line(d, [(x + 22 * np.cos(a), y + 22 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 20)], c, 5)
            for a in np.linspace(0, 2 * np.pi, 9)[:-1] + t * 0.5:
                crayon_line(d, [(x + 30 * np.cos(a), y + 30 * np.sin(a)), (x + 44 * np.cos(a), y + 44 * np.sin(a))], c, 5)
        else:
            crayon_line(d, star_pts(x, y, 26, t * 0.3), c, 5, closed=True)
    a = np.asarray(im).astype(np.float32) / 255
    return a[..., :3], grain_mask(a[..., 3], 0.8)


# ---------- ransom-note cut-out letters ----------
from PIL import ImageFont
_FD = "/usr/share/fonts/truetype/"
import glob as _glob
def _font_path(name):
    hits = _glob.glob(f"/usr/share/fonts/**/{name}", recursive=True)
    return hits[0] if hits else None
FONTS = [p for p in map(_font_path, ["DejaVuSerif-Bold.ttf", "FreeSansBold.ttf", "Caladea-Bold.ttf", "FreeMonoBold.ttf",
                                     "Inter-Black.otf", "Carlito-BoldItalic.ttf", "FreeSerifBoldItalic.ttf", "DejaVuSans-Bold.ttf"]) if p]
TILE_BG = [(255, 255, 255), (250, 244, 228), (246, 230, 120), (255, 255, 255), (240, 236, 230)]


def ransom(text, ink, size=64, seed=0, max_w=760):
    """Returns RGBA PIL image of the cut-out line(s), word-wrapped to max_w."""
    r = np.random.default_rng(seed)
    tiles = []
    for ch in text:
        if ch == " ":
            tiles.append(None); continue
        f = ImageFont.truetype(FONTS[r.integers(len(FONTS))], int(size * r.uniform(0.92, 1.12)))
        bb = f.getbbox(ch)
        tw, th = bb[2] - bb[0] + int(size * 0.22), int(size * 1.18)
        t = Image.new("RGBA", (tw, th), TILE_BG[r.integers(len(TILE_BG))] + (255,))
        ImageDraw.Draw(t).text(((tw - (bb[2] - bb[0])) / 2 - bb[0], (th - size) / 2 - size * 0.05), ch, font=f, fill=tuple(ink))
        t = t.rotate(r.uniform(-7, 7), expand=True, resample=Image.BICUBIC)
        tiles.append(t)
    # wrap into lines
    words, cur = [], []
    for t in tiles:
        if t is None:
            words.append(cur); cur = []
        else:
            cur.append(t)
    words.append(cur)
    gap = int(size * 0.32)
    lines, line, lw = [], [], 0
    for wd in words:
        ww = sum(t.width - 3 for t in wd)
        if line and lw + gap + ww > max_w:
            lines.append(line); line, lw = [], 0
        line.append(wd); lw += (gap if lw else 0) + ww
    lines.append(line)
    lh = int(size * 1.35)
    widths = [sum(sum(t.width - 3 for t in wd) for wd in ln) + gap * (len(ln) - 1) for ln in lines]
    out = Image.new("RGBA", (max(widths) + 24, lh * len(lines) + 24), (0, 0, 0, 0))
    for li, ln in enumerate(lines):
        x = 12 + (max(widths) - widths[li]) // 2
        for wd in ln:
            for t in wd:
                y = 12 + li * lh + (lh - t.height) // 2 + int(r.integers(-4, 5))
                out.alpha_composite(t, (x, max(y, 0)))
                x += t.width - 3
            x += gap
    # drop shadow
    a = out.split()[3]
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(4)).point(lambda v: v * 0.45))
    fin = Image.new("RGBA", (out.width + 8, out.height + 8), (0, 0, 0, 0))
    fin.alpha_composite(sh, (7, 7)); fin.alpha_composite(out, (0, 0))
    return fin


def paste_rgba(base, im, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    x, y = int(x - im.width / 2), int(y - im.height / 2)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + im.width, W), min(y + im.height, H)
    if x1 <= x0 or y1 <= y0:
        return base
    sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
    al = sub[..., 3:4] * alpha
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - al) + sub[..., :3] * al
    return base


def logo_sticker(px=250):
    """Della's rose logo on a torn-edge paper sticker (keeps its white ground honest)."""
    lg = Image.open("logo.png").convert("RGB").resize((px, int(px * 126 / 130)), Image.LANCZOS)
    pad = 18
    st = Image.new("RGBA", (lg.width + pad * 2, lg.height + pad * 2), (255, 255, 255, 255))
    st.paste(lg, (pad, pad))
    m = Image.new("L", st.size, 0); r = np.random.default_rng(4)
    pts = []
    for u in np.linspace(0, 1, 60, endpoint=False):  # wobbly torn edge
        a = u * 2 * np.pi
        rr = 0.5 + 0.02 * r.standard_normal()
        pts.append((st.width / 2 + rr * st.width * np.cos(a) * 1.0, st.height / 2 + rr * st.height * np.sin(a) * 1.0))
    ImageDraw.Draw(m).polygon(pts, fill=255)
    st.putalpha(m)
    st = st.rotate(-4, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", st.size, (0, 0, 0, 0)); sh.putalpha(st.split()[3].filter(ImageFilter.GaussianBlur(5)).point(lambda v: v * 0.4))
    fin = Image.new("RGBA", (st.width + 10, st.height + 10), (0, 0, 0, 0))
    fin.alpha_composite(sh, (8, 8)); fin.alpha_composite(st, (0, 0))
    return fin
