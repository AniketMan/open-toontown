#!/usr/bin/env python3
"""
Builds an HD texture pack by 4x upscaling the game's textures with
Real-ESRGAN (the anime/cartoon 6-block model).

The originals in resources/ are never touched.  Upscaled copies are written
with the same relative path and file format into resources-hd/, which the
client puts ahead of resources/ on the model path when want-hd-textures is
on, so every model picks them up without being rebuilt.

Usage:
    python3 tools/upscale_textures.py --model /path/RealESRGAN_x4plus_anime_6B.pth
    python3 tools/upscale_textures.py --model ... --only phase_3.5/maps/cobblestone_blue.jpg

Needs: torch, numpy, Pillow.  Re-running skips files that are already done.
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

EXTENSIONS = ('.jpg', '.jpeg', '.png', '.rgb', '.gif')
SCALE = 4
PAD = 8             # source pixels of context added on each side
MAX_SOURCE = 1024   # anything this large already is left alone
MAX_OUTPUT = 2048


class ResidualDenseBlock(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.rdb1 = ResidualDenseBlock(nf, gc)
        self.rdb2 = ResidualDenseBlock(nf, gc)
        self.rdb3 = ResidualDenseBlock(nf, gc)

    def forward(self, x):
        return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    """The Real-ESRGAN x4 generator; layer names match the released weights."""

    def __init__(self, nb=6, nf=64, gc=32):
        super().__init__()
        self.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x):
        feat = self.conv_first(x)
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode='nearest')))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode='nearest')))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


def load_model(path, device):
    state = torch.load(path, map_location='cpu', weights_only=True)
    state = state.get('params_ema', state.get('params', state))
    net = RRDBNet()
    net.load_state_dict(state, strict=True)
    return net.eval().to(device)


def tiles(arr, axis):
    """True if the image looks like it repeats along this axis: its two
    opposite edges are about as similar as two neighbouring rows inside it."""
    a = arr.astype(np.float32)
    if axis == 1:
        a = a.transpose(1, 0, 2)
    if a.shape[0] < 8:
        return False
    seam = np.abs(a[0] - a[-1]).mean()
    inner = np.abs(a[1:] - a[:-1]).mean()
    return seam <= max(inner * 2.0, 4.0)


def upscale_rgb(net, device, arr):
    """arr: HxWx3 uint8 -> 4Hx4Wx3 uint8."""
    wrap_v, wrap_h = tiles(arr, 0), tiles(arr, 1)
    # Give the network context beyond the border.  Repeating textures are
    # wrapped so their seams still line up afterwards; everything else
    # (atlases, signs, clothing) has its edge pixels extended instead.
    padded = np.pad(arr, ((PAD, PAD), (0, 0), (0, 0)), mode='wrap' if wrap_v else 'edge')
    padded = np.pad(padded, ((0, 0), (PAD, PAD), (0, 0)), mode='wrap' if wrap_h else 'edge')
    x = torch.from_numpy(padded).to(device).permute(2, 0, 1).float().div(255.0).unsqueeze(0)
    with torch.no_grad():
        y = net(x).clamp(0, 1)
    out = (y[0].permute(1, 2, 0) * 255.0).round().byte().cpu().numpy()
    p = PAD * SCALE
    return out[p:-p, p:-p]


def process(net, device, src, dst, smooth=False):
    img = Image.open(src)
    img.load()
    w, h = img.size
    if max(w, h) >= MAX_SOURCE or max(w, h) * SCALE > MAX_OUTPUT * 2:
        return 'skipped (already large)'
    ext = os.path.splitext(src)[1].lower()

    alpha = None
    if img.mode in ('L', 'LA', 'RGBA', 'P'):
        if img.mode == 'P':
            img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
        if img.mode in ('LA', 'RGBA'):
            alpha = np.asarray(img.getchannel('A'))
    gray = img.mode in ('L', 'LA')
    rgb = np.asarray(img.convert('RGB'))

    if smooth:
        # Plain resampling: nothing invented, just no visible pixels.
        big = (w * SCALE, h * SCALE)
        out = np.asarray(Image.fromarray(rgb).resize(big, Image.BICUBIC))
        if alpha is not None:
            alpha_big = Image.fromarray(alpha).resize(big, Image.BICUBIC)
    else:
        out = upscale_rgb(net, device, rgb)
    if gray:
        result = Image.fromarray(out.mean(axis=2).round().astype(np.uint8))
    else:
        result = Image.fromarray(out)
    if alpha is not None and smooth:
        result.putalpha(alpha_big)
    elif alpha is not None:
        a = upscale_rgb(net, device, np.repeat(alpha[:, :, None], 3, axis=2))
        result.putalpha(Image.fromarray(a.mean(axis=2).round().astype(np.uint8)))

    if max(result.size) > MAX_OUTPUT:
        f = MAX_OUTPUT / float(max(result.size))
        result = result.resize((round(result.size[0] * f), round(result.size[1] * f)), Image.LANCZOS)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.tmp'
    if ext in ('.jpg', '.jpeg'):
        result.convert('RGB').save(tmp, 'JPEG', quality=95, subsampling=0)
    elif ext == '.rgb':
        result.save(tmp, 'SGI')
    elif ext == '.gif':
        result.save(tmp, 'GIF')
    else:
        result.save(tmp, 'PNG')
    os.replace(tmp, dst)
    return '%dx%d -> %dx%d' % (w, h, result.size[0], result.size[1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', required=True, help='RealESRGAN_x4plus_anime_6B.pth')
    ap.add_argument('--src', default='resources')
    ap.add_argument('--dst', default='resources-hd')
    ap.add_argument('--only', nargs='*', help='paths relative to --src to process')
    ap.add_argument('--force', action='store_true', help='redo files that already exist')
    args = ap.parse_args()

    device = torch.device('mps' if torch.backends.mps.is_available() else
                          'cuda' if torch.cuda.is_available() else 'cpu')
    net = load_model(args.model, device)

    if args.only:
        files = list(args.only)
    else:
        files = []
        for root, _, names in os.walk(args.src):
            for n in sorted(names):
                if n.lower().endswith(EXTENSIONS):
                    files.append(os.path.relpath(os.path.join(root, n), args.src))
        files.sort()

    # 2D art (menus, buttons, fonts) keeps its original textures; see
    # tools/list_gui_textures.py, which writes this list.
    # hd_texture_exclude_cogs.txt keeps the cogs on their original art too.
    excluded = set()
    for name in ('hd_texture_exclude.txt', 'hd_texture_exclude_cogs.txt'):
        exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        if os.path.exists(exclude_file):
            with open(exclude_file) as f:
                excluded.update(line.strip() for line in f if line.strip())
    if excluded and not args.only:
        files = [rel for rel in files if rel.replace(os.sep, '/') not in excluded]

    smooth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hd_texture_smooth.txt')
    smooth_set = set()
    if os.path.exists(smooth_file):
        with open(smooth_file) as f:
            smooth_set = set(line.strip() for line in f if line.strip())

    done = skipped = failed = 0
    start = time.time()
    for i, rel in enumerate(files, 1):
        src, dst = os.path.join(args.src, rel), os.path.join(args.dst, rel)
        if os.path.exists(dst) and not args.force:
            skipped += 1
            continue
        try:
            msg = process(net, device, src, dst, smooth=rel.replace(os.sep, '/') in smooth_set)
            if msg.startswith('skipped'):
                skipped += 1
            else:
                done += 1
        except Exception as e:  # keep going; one odd file shouldn't stop the batch
            failed += 1
            msg = 'FAILED: %s' % e
        if args.only or failed and msg.startswith('FAILED') or i % 100 == 0:
            print('[%d/%d] %s: %s' % (i, len(files), rel, msg), flush=True)
    print('upscaled %d, skipped %d, failed %d in %.0fs (device: %s)'
          % (done, skipped, failed, time.time() - start, device), flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
