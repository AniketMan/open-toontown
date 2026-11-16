"""Stack the reference sheet, the original model and the HD build into duck/preview_vs_sheet.png. python3 compare.py"""
import os
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
sheet = Image.open(os.path.expanduser("~/Downloads/toon-hd/turnarounds/head_duck_fss_new-turnaround.png")).convert("RGB")
W = 1700
sheet = sheet.resize((W, int(sheet.height * W / sheet.width)))
rows = [sheet]
for tag in ("o", "a"):
    row = Image.new("RGB", (W, W // 5), (170, 170, 170))
    for i, v in enumerate(("front", "threeq", "side", "back", "top")):
        im = Image.open(f"{D}/work/{tag}_{v}.png").convert("RGB").resize((W // 5, W // 5))
        row.paste(im, (i * W // 5, 0))
    rows.append(row)
out = Image.new("RGB", (W, sum(r.height for r in rows) + 4 * (len(rows) - 1)), (255, 255, 255))
y = 0
for r in rows:
    out.paste(r, (0, y))
    y += r.height + 4
out.save(f"{D}/preview_vs_sheet.png")
print("saved", out.size)
