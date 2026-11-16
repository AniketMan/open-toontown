"""Close-ups of Toon heads built by the game's Toon class: one row per run, front and three-quarter of each head.
Usage (open-toontown root): PYTHONPATH=. venv/bin/python head_test.py out.png hd|orig [head codes ...]"""
import os, sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 420 420\naudio-library-name null\nwant-postfx 0\n'
                    'notify-level warning\ndefault-directnotify-level warning\n')
out, mode = sys.argv[1], sys.argv[2]
codes = sys.argv[3:] or ['dls', 'cls', 'hls', 'mls', 'rls', 'fls', 'pls', 'bls', 'sls']
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
if mode == 'hd':
    from toontown.toonbase import HDTextures
    HDTextures.enable()
from toontown.toon import Toon, ToonDNA
b.setBackgroundColor(0.5, 0.5, 0.5)
b.disableMouse()
b.camLens.setFov(20)
tiles = []
for code in codes:
    dna = ToonDNA.ToonDNA()
    dna.newToonFromProperties(code, 'ms', 'm', 'm', 25, 0, 25, 25, 0, 8, 0, 8, 0, 10)
    t = Toon.Toon()
    t.setDNAString(dna.makeNetString())
    t.pose('neutral', 0)
    t.update(force=True)
    if getattr(t, 'dropShadow', None):
        t.dropShadow.hide()
    try:
        t.nametag3d.hide()
    except Exception:
        pass
    t.reparentTo(b.render)
    head = t.getPart('head', '1000')
    for h in (180, 140):
        t.setH(h)
        lo, hi = head.getTightBounds(b.render)
        c = (lo + hi) / 2
        size = max(hi.x - lo.x, hi.z - lo.z, 1.0)
        b.camera.setPos(c.x, c.y - size * 3.6, c.z)
        b.camera.lookAt(c)
        b.graphicsEngine.renderFrame(); b.graphicsEngine.renderFrame()
        img = PNMImage()
        b.win.getScreenshot(img)
        tiles.append(img)
    t.detachNode()
sheet = PNMImage(420 * len(tiles), 420, 3)
for i, img in enumerate(tiles):
    sheet.copySubImage(img, i * 420, 0, 0, 0, 420, 420)
sheet.write(Filename.fromOsSpecific(os.path.abspath(out)))
print("wrote", out, len(tiles), "tiles")
