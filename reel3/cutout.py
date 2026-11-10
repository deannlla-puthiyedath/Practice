"""Cut the swimsuit (garment only, no person) out of the product photo -> swimsuit_cut.png (RGBA)."""
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

im = Image.open("swimsuit.jpg").convert("RGB").crop((50, 14, 1246, 1206))  # front view panel
a = np.asarray(im).astype(np.int16)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
blue = (b - r > 28) & (b > 120)                       # printed sea + teal trim
m = Image.fromarray((blue * 255).astype(np.uint8))
m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # close the white grid lines
# fill holes: flood the background from the border, everything not reached is inside the suit
f = m.convert("L"); W, H = f.size
seed = Image.new("L", (W + 2, H + 2), 0); seed.paste(f, (1, 1))
ImageDraw.floodfill(seed, (0, 0), 128)
s = np.asarray(seed)[1:-1, 1:-1]
mask = (s != 128).astype(np.uint8) * 255
# keep the biggest blob only (drops stray blue specks)
mk = Image.fromarray(mask)
lab = np.asarray(mk) > 0
ys, xs = np.nonzero(lab)
# simple largest-component via repeated floodfill
tmp = mk.copy(); best, best_n = None, 0; seen = np.zeros_like(lab)
for y, x in zip(ys[::400], xs[::400]):
    if seen[y, x]: continue
    t = mk.copy(); ImageDraw.floodfill(t, (int(x), int(y)), 77)
    comp = np.asarray(t) == 77; seen |= comp
    if comp.sum() > best_n: best, best_n = comp, comp.sum()
mask = Image.fromarray((best * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
out = im.convert("RGBA"); out.putalpha(mask)
bb = mask.getbbox(); out = out.crop(bb)
out.save("swimsuit_cut.png"); print("bbox", bb, "size", out.size)

# ---- repair the bites left by the model's hand: rebuild the side edges, fill with nearby print ----
a = np.asarray(out).astype(np.float32)
al = a[..., 3] > 128
Hc, Wc = al.shape
L = np.full(Hc, -1); R = np.full(Hc, -1)
for y in range(Hc):
    xs_ = np.nonzero(al[y])[0]
    if len(xs_): L[y], R[y] = xs_.min(), xs_.max()
def smooth_edge(E, inward, y0, y1, win=70, q=50):
    E2 = E.copy()
    for y in range(y0, y1):
        lo, hi = max(y0, y - win), min(y1, y + win)
        ref = np.percentile(E[lo:hi], q)
        if inward(E[y], ref): E2[y] = int(ref)
    return E2
y0, y1 = int(Hc * 0.30), int(Hc * 0.80)
L2 = smooth_edge(L, lambda e, ref: e > ref + 6, y0, y1, q=12)
R2 = smooth_edge(R, lambda e, ref: e < ref - 6, y0, y1, q=88)
rgb = a[..., :3].copy(); alpha = a[..., 3].copy()
for y in range(y0, y1):
    row = al[y]
    need = np.zeros(Wc, bool); need[L2[y]:R2[y] + 1] = True
    need &= ~row
    for x in np.nonzero(need)[0]:
        # borrow print from the same row, 110 px toward the middle (wraps inside the suit)
        sx = x + 110 if x < Wc / 2 else x - 110
        sx = int(np.clip(sx, L2[y], R2[y]))
        rgb[y, x] = rgb[y, sx] if al[y, sx] else rgb[y, Wc // 2]
        alpha[y, x] = 255
fixed = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")
fa = fixed.split()[3].filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
fixed.putalpha(fa)
fixed.save("swimsuit_cut.png"); print("repaired")

# ---- paint over finger outlines (warm skin tones left inside the garment) ----
a = np.asarray(Image.open("swimsuit_cut.png")).astype(np.float32)
rgb, alpha = a[..., :3], a[..., 3]
warm = (rgb[..., 0] - rgb[..., 2] > 22) & (rgb[..., 0] - rgb[..., 1] > 8) & (alpha > 20)
warm = np.asarray(Image.fromarray((warm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
warm &= alpha > 20
Hc, Wc = warm.shape
for y, x in zip(*np.nonzero(warm)):
    for d in (70, 110, 150, -70, -110):
        sx = x + d if x < Wc / 2 else x - d
        if 0 <= sx < Wc and alpha[y, sx] > 200 and not warm[y, sx]:
            rgb[y, x] = rgb[y, sx]; break
# soften the silhouette a touch so the repaired sides read as fabric, not steps
al = Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 128 else 0)
al = al.filter(ImageFilter.GaussianBlur(1.0))
Image.fromarray(np.dstack([rgb, np.asarray(al)]).astype(np.uint8), "RGBA").save("swimsuit_cut.png"); print("cleaned", int(warm.sum()))
