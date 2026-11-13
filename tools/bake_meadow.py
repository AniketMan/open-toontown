#!/usr/bin/env python3
"""
Bakes the meadow ground texture used under the grass blades.

The game's lawns are one flat painted green.  This generates, once, a
seamlessly tiling "detail" image: patchy lighter and darker growth, drifts
towards yellow and blue-green, worn brownish patches and fine speckle.  The
client multiplies it over the painted lawn (GrassField), so each
playground keeps its own green and nothing is computed per frame.

The image is stored so that mid grey (0.5) means "leave the lawn colour
alone"; brighter lightens, darker darkens, per channel.

Usage:  python3 tools/bake_meadow.py [--size 1024] [--seed 11]
Needs:  numpy, Pillow.  Writes resources-hd/materials/meadow_detail.png
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def noise(rng, size, cells):
    """Tiling value noise: a random grid of cells x cells, smoothly
    interpolated up to size x size, wrapping at the edges."""
    grid = rng.random((cells, cells))
    t = np.arange(size) * cells / float(size)
    i0 = np.floor(t).astype(int) % cells
    i1 = (i0 + 1) % cells
    f = t - np.floor(t)
    f = f * f * (3 - 2 * f)
    rows = grid[i0] * (1 - f)[:, None] + grid[i1] * f[:, None]
    return rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :]


def fbm(rng, size, cells, octaves):
    total, amp, norm = 0.0, 1.0, 0.0
    for _ in range(octaves):
        if cells > size:
            break
        total = total + noise(rng, size, cells) * amp
        norm += amp
        amp *= 0.5
        cells *= 2
    return total / norm


def blades(rng, size, count):
    """Thousands of short strokes, lighter and darker than their
    surroundings, mostly leaning one way: seen from a distance they read as
    grass.  Drawn nine times over so the image still tiles.  Returns values
    around 0, roughly -1..1."""
    img = Image.new('L', (size, size), 128)
    draw = ImageDraw.Draw(img)
    scale = size / 1024.0
    for _ in range(count):
        x, y = rng.random() * size, rng.random() * size
        length = (5 + rng.random() ** 2 * 22) * scale
        angle = rng.normal(1.25, 0.55)          # mostly "up and to the right"
        dx, dy = np.cos(angle) * length, -np.sin(angle) * length
        value = float(rng.choice([-1.0, -0.7, 0.6, 1.0]) * (0.5 + 0.5 * rng.random()))
        width = int(round((1 + (rng.random() < 0.3)) * scale))
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                if -40 * scale < x + ox < size + 40 * scale and -40 * scale < y + oy < size + 40 * scale:
                    draw.line((x + ox, y + oy, x + ox + dx, y + oy + dy), fill=int(128 + value * 110), width=max(1, width))
    return (np.asarray(img.filter(ImageFilter.GaussianBlur(0.6 * scale)), dtype=np.float32) - 128.0) / 110.0


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--size', type=int, default=2048)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--out', default='resources-hd/materials/meadow_detail.png')
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    n = args.size

    growth = fbm(rng, n, 6, 5) - 0.5          # thick and thin growth
    clumps = fbm(rng, n, 24, 4) - 0.5         # tuft-sized mottling
    speckle = fbm(rng, n, 160, 2) - 0.5       # individual blades and gaps
    warm = fbm(rng, n, 4, 4) - 0.5            # drift yellow <-> blue-green
    worn = smooth(fbm(rng, n, 5, 5) + clumps * 0.25, 0.60, 0.72)   # bare, dry patches
    straw = smooth(fbm(rng, n, 40, 3), 0.66, 0.80) * 0.5           # scattered dry blades

    # Multipliers around 1.0 for red, green, blue.
    strokes = blades(rng, n, int(26000 * (n / 1024.0) ** 2))
    light = 1.0 + growth * 0.46 + clumps * 0.36 + speckle * 0.22 + strokes * 0.42
    r = light * (1.0 + warm * 0.22)
    g = light * (1.0 + warm * 0.04)
    b = light * (1.0 - warm * 0.25)
    # Worn ground and straw.  The lawns are a bright yellow-green, so brown
    # comes mostly from taking green and blue away, not from adding red.
    dry = np.clip(worn * 0.8 + straw, 0, 1)
    r = r * (1.0 + dry * 0.10)
    g = g * (1.0 - dry * 0.30)
    b = b * (1.0 - dry * 0.50)
    # Keep the lawn's overall colour: each channel averages to "no change".
    r, g, b = r / r.mean(), g / g.mean(), b / b.mean()

    img = np.stack([r, g, b], axis=2) * 0.5
    img = np.clip(img * 255.0, 0, 255).round().astype(np.uint8)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    Image.fromarray(img).save(args.out)
    print('wrote %s (%dx%d), mean %s' % (args.out, n, n, img.reshape(-1, 3).mean(axis=0).round(1)))


if __name__ == '__main__':
    main()
