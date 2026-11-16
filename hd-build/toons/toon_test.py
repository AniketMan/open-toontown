"""Photograph whole Toons built by the game's own Toon class: front, three-quarter, side, back.
The HD resource overlay is on, so any piece present in resources-hd/ is the one drawn.
Usage (open-toontown root): PYTHONPATH=. venv/bin/python toon_test.py out.png [hd|orig] [head torso legs gender ...]"""
import os, sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 2400 900\naudio-library-name null\nwant-postfx 0\n'
                    'notify-level warning\ndefault-directnotify-level warning\n')
out = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'hd'
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
if mode == 'hd':
    from toontown.toonbase import HDTextures
    HDTextures.enable()
from toontown.toon import Toon, ToonDNA
specs = [a.split(',') for a in sys.argv[3:]] or [['dss', 'ms', 'm', 'm'], ['cls', 'ls', 'l', 'm'], ['rss', 'sd', 's', 'f']]
b.setBackgroundColor(0.5, 0.5, 0.5)
b.disableMouse()
toons = []
k = 0
for head, torso, legs, gender in specs:
    for h in (180, 140, 90, 0):
        dna = ToonDNA.ToonDNA()
        dna.newToonFromProperties(head, torso, legs, gender, 25, 0, 25, 25, 0, 8, 0, 8, 0, 10)
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
        for lod in t.getLODNames():
            pass
        t.getLODNode().forceSwitch(t.getLODNode().getHighestSwitch()) if hasattr(t, 'getLODNode') and t.getLODNode() else None
        t.reparentTo(b.render)
        t.setPos((k - (len(specs) * 4 - 1) / 2.0) * 3.2, 0, 0)
        t.setH(h)
        toons.append(t)
        k += 1
b.camLens.setFov(22)
b.camera.setPos(0, -55 * max(1.0, len(specs) / 3.0), 2.4)
b.camera.lookAt(0, 0, 1.9)
b.graphicsEngine.renderFrame(); b.graphicsEngine.renderFrame()
b.win.saveScreenshot(Filename.fromOsSpecific(os.path.abspath(out)))
t = toons[0]
print("legs file:", [str(n.node().getFullpath()) for n in t.findAllMatches('**/+ModelRoot')][:3])
print("triangles drawn at LOD 1000:", sum(g.node().getGeom(i).getPrimitive(0).getNumFaces() for g in t.getPart('legs', '1000').findAllMatches('**/+GeomNode') for i in range(g.node().getNumGeoms())))
