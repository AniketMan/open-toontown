"""Overlay the model's check renders on the reference views and score silhouette overlap."""
from PIL import Image
import numpy as np

PXU = 2 * 404 / 4.9
full = np.load("mask.npy")
boxes = {"front": (12, 121, 303, 525), "left": (629, 121, 825, 525), "back": (316, 121, 601, 525)}
for name, (x0, y0, x1, y1) in boxes.items():
    ref = Image.open(f"refplanes/flunky_ref_{name}.png").convert("RGB")
    ref2 = ref.resize((ref.width * 2, ref.height * 2), Image.LANCZOS)
    rm = Image.fromarray((full[y0:y1, x0:x1] * 255).astype("uint8")).resize(ref2.size, Image.NEAREST)
    chk = Image.open(f"chk_{name}.png").convert("RGBA")
    W, Hh = chk.size
    canvas = Image.new("L", (W, Hh), 0)
    ox = (W - ref2.width) // 2
    oy = round(Hh - 0.05 * PXU) - ref2.height
    canvas.paste(rm, (ox, oy))
    R = np.asarray(canvas) > 127
    M = np.asarray(chk)[..., 3] > 127
    print(f"{name}: silhouette overlap {(R & M).sum() / (R | M).sum():.3f}")
    ov = np.zeros((Hh, W, 3), "uint8") + 200
    ov[R & M] = (90, 90, 90)
    ov[M & ~R] = (0, 200, 0)
    ov[R & ~M] = (220, 0, 0)
    bg = Image.new("RGBA", chk.size, (210, 210, 210, 255))
    bg.alpha_composite(chk)
    refc = Image.new("RGB", (W, Hh), (210, 210, 210))
    refc.paste(ref2, (ox, oy))
    sheet = Image.new("RGB", (W * 3 + 20, Hh), (255, 255, 255))
    sheet.paste(refc, (0, 0))
    sheet.paste(bg.convert("RGB"), (W + 10, 0))
    sheet.paste(Image.fromarray(ov), (2 * W + 20, 0))
    sheet.save(f"cmp_{name}.png")
hs = []
for n in ("front", "left"):
    h = Image.open(f"chk_head{n}.png").convert("RGBA")
    b = Image.new("RGBA", h.size, (210, 210, 210, 255))
    b.alpha_composite(h)
    hs += [Image.open(f"head_{n}.png").convert("RGB").resize(h.size), b.convert("RGB")]
sheet = Image.new("RGB", (sum(i.width for i in hs) + 30, hs[0].height), (255, 255, 255))
x = 0
for i in hs:
    sheet.paste(i, (x, 0))
    x += i.width + 10
sheet.save("cmp_head.png")
src = Image.open("concept_sheet.webp").convert("RGB")
tiles = []
for n, box in (("handfront", (235, 335, 305, 440)), ("handleft", (675, 330, 760, 445)), ("shoes", (60, 470, 260, 530))):
    h = Image.open(f"chk_{n}.png").convert("RGBA")
    b = Image.new("RGBA", h.size, (210, 210, 210, 255))
    b.alpha_composite(h)
    tiles += [src.crop(box).resize(h.size, Image.LANCZOS), b.convert("RGB")]
Hmax = max(i.height for i in tiles[:4])
sheet = Image.new("RGB", (sum(i.width for i in tiles[:4]) + 30, Hmax + tiles[4].height + 10), (255, 255, 255))
x = 0
for i in tiles[:4]:
    sheet.paste(i, (x, 0))
    x += i.width + 10
sheet.paste(tiles[4], (0, Hmax + 10))
sheet.paste(tiles[5], (tiles[4].width + 10, Hmax + 10))
sheet.save("cmp_hand.png")
t = Image.open("chk_threeq.png").convert("RGBA")
bg = Image.new("RGBA", t.size, (210, 210, 210, 255))
bg.alpha_composite(t)
r4 = Image.open("ref_4_2x.png").convert("RGB")
sheet = Image.new("RGB", (r4.width + t.width + 10, max(r4.height, t.height)), (210, 210, 210))
sheet.paste(r4, (0, 0))
sheet.paste(bg.convert("RGB"), (r4.width + 10, 0))
sheet.save("cmp_threeq.png")
