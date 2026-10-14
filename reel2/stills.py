import numpy as np, time
from PIL import Image
from lib import *

def save(a, p): Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(p, quality=92)

def sun_frame(t, wink, recol, ray_s, scale=0.78, rot=0.0):
    cx, cy = 540, 900
    base = crop_affine(PAINT, SC[0], SC[1], scale, rot, center=(cx, cy))
    ring = crop_affine(RING, SC[0], SC[1], scale, rot, center=(cx, cy))
    r = SUN_R*scale
    base = screen(base, YELLOW*0.9+0.1, rays(cx, cy, r, t, ray_s))
    # outline recolour: black -> orange -> sunlight gold
    col = ORANGE*(1-max(0,recol*2-1)) + SUNLIGHT*max(0,recol*2-1) if recol>0 else INK
    if recol>0 and recol<0.5: col = INK*(1-recol*2)+ORANGE*recol*2
    base = over(base, col, np.clip(ring*1.3,0,1))
    base = screen(base, SUNLIGHT, glow(ring, 10)*0.8*recol)
    frgb, fa = face_layer(cx, cy, r, wink)
    return over(base, frgb, fa)

t0=time.time()
save(sun_frame(8.0, 1.0, 0.55, 0.9), "still_wink.jpg")
save(sun_frame(8.0, 0.0, 0.55, 0.9), "still_open.jpg")

bg = paper_bg()
for side in (-1, 1):
    rgb, a = wing_layer(side, 1.0)
    bg = over(bg, rgb, a)
band, light, deco = halo_layer(540, 560, 300, 72, 1.0, GOLD)
bg = screen(bg, SUNLIGHT, np.clip(light,0,1)*0.85)
bg = over(bg, GOLD*0.95, band)
bg = over(bg, GOLD*0.9, deco*0.9)
drgb, da = doodles(1.0); bg = over(bg, drgb, da)
save(bg, "still_halo_wings.jpg")
print("ok", time.time()-t0)
