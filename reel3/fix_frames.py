"""Two check frames for the fixed character: front and back, in her room. `python3 fix_frames.py`"""
import os, numpy as np
from PIL import Image, ImageDraw
import girl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "board"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920


def room_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    wall = np.array([196, 218, 236]) * (1 - y) + np.array([228, 236, 242]) * y
    img = Image.fromarray(np.broadcast_to(wall, (H, W, 3)).astype(np.uint8).copy()).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1520, W, H], fill=(176, 128, 88))
    for k in range(6):
        d.line([0, 1530 + k * 70, W, 1530 + k * 70], fill=(156, 110, 76), width=3)
    d.rectangle([70, 330, 370, 1000], fill=(238, 240, 236)); d.rectangle([92, 352, 348, 978], fill=(206, 228, 214))
    d.line([220, 352, 220, 978], fill=(238, 240, 236), width=12); d.line([92, 665, 348, 665], fill=(238, 240, 236), width=12)
    return img


def frame(view, path):
    img = room_bg()
    girl.draw(img, 560, 300, 1500, view=view, eyes="closed", necklace=None)
    img.convert("RGB").resize((540, 960), Image.LANCZOS).save(path, quality=88)


frame("front", os.path.join(OUT, "fix_front.jpg"))
frame("back", os.path.join(OUT, "fix_back.jpg"))
a, b = Image.open(os.path.join(OUT, "fix_front.jpg")), Image.open(os.path.join(OUT, "fix_back.jpg"))
s = Image.new("RGB", (a.width * 2 + 30, a.height + 20), (246, 242, 236)); s.paste(a, (10, 10)); s.paste(b, (a.width + 20, 10))
s.save(os.path.join(OUT, "fix_pair.jpg"), quality=88)
print("ok")
