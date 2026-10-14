import numpy as np
from PIL import Image
from lib import *
from lib import _paint
s = H / _paint.shape[0]
base = crop_affine(PAINT, PAD + _paint.shape[1] / 2, PAD + _paint.shape[0] / 2, s)
base = paste_rgba(base, logo_sticker(260), 470, 640)
base = paste_rgba(base, ransom("Della Antony", (173, 51, 97), size=96, seed=21, max_w=900), 470, 880)
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save("still_endcard.jpg", quality=92)
