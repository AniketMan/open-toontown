#!/usr/bin/env python3
"""
Writes two lists used by upscale_textures.py, one path relative to
resources/ per line:

  hd_texture_exclude.txt - textures used only by 2D art (GUI models, fonts)
  hd_texture_smooth.txt  - small textures used by character models (skin, faces)

upscale_textures.py skips the files listed there: AI upscaling suits the 3D
world's painted surfaces but makes menus, buttons and lettering look
artificial, so 2D art keeps its original textures.

Run with the game's Python (it needs Panda3D):
    venv/bin/python tools/list_gui_textures.py
"""
import os
import sys
from panda3d.core import Filename, NodePath, PNMImageHeader, getModelPath, loadPrcFileData

loadPrcFileData('', 'window-type none\naudio-library-name null\nnotify-level warning')
from panda3d.core import Loader, LoaderOptions

SRC = 'resources'
SMOOTH_MAX_SIZE = 64   # pixels, longest side
ROOT = os.path.abspath(SRC)
getModelPath().prependDirectory(Filename.fromOsSpecific(ROOT))


def textures_of(loader, path):
    node = loader.loadSync(Filename.fromOsSpecific(os.path.abspath(path)), LoaderOptions())
    out = set()
    if node is None:
        return out
    for tex in NodePath(node).findAllTextures():
        for fn in (tex.getFullpath(), tex.getAlphaFullpath()):
            p = fn.toOsSpecific()
            if p and os.path.abspath(p).startswith(ROOT + os.sep):
                out.add(os.path.relpath(os.path.abspath(p), ROOT).replace(os.sep, '/'))
    return out


def main():
    loader = Loader.getGlobalPtr()
    gui, world, chars = set(), set(), set()
    for dirpath, _, names in os.walk(SRC):
        d = dirpath.replace(os.sep, '/')
        is_gui = d.endswith('/models/gui') or d.endswith('/models/fonts')
        is_char = d.endswith('/models/char')
        for n in sorted(names):
            if n.endswith('.bam'):
                texs = textures_of(loader, os.path.join(dirpath, n))
                (gui if is_gui else world).update(texs)
                if is_char:
                    chars.update(texs)
    # Some atlases hold both 2D art and pieces of 3D models.  Those stay
    # upscaled, since the 3D world is where the extra detail matters.
    shared = gui & world
    found = gui - world
    print('%d textures are shared between GUI and 3D models and stay HD' % len(shared))
    # Font pages and anything else plainly 2D by name.
    for dirpath, _, names in os.walk(SRC):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), SRC).replace(os.sep, '/')
            low = rel.lower()
            if low.endswith(('.jpg', '.png', '.rgb', '.gif')) and (
                    '/fonts/' in low or 'gui' in os.path.basename(low) or '/icons/' in low):
                found.add(rel)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hd_texture_exclude.txt')
    with open(out, 'w') as f:
        f.write('\n'.join(sorted(found)) + '\n')
    print('%d GUI/font textures listed in %s' % (len(found), out))
    # Character skin and faces are tiny textures of soft shading.  The AI
    # upscaler turns those gradients into hard crease lines, so they get a
    # plain smooth enlargement instead.
    # Only the small ones: larger character textures (suits, clothing)
    # hold drawn detail that upscales well.
    smooth = set()
    for rel in chars - found:
        header = PNMImageHeader()
        if header.readHeader(Filename.fromOsSpecific(os.path.join(ROOT, rel))) and \
                max(header.getXSize(), header.getYSize()) <= SMOOTH_MAX_SIZE:
            smooth.add(rel)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hd_texture_smooth.txt')
    with open(out, 'w') as f:
        f.write('\n'.join(sorted(smooth)) + '\n')
    print('%d character textures listed in %s' % (len(smooth), out))


if __name__ == '__main__':
    sys.exit(main())
