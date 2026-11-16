"""Photograph HD enemies' medallions through the game's Suit class, health light off and on.
Usage (open-toontown root): PYTHONPATH=. venv/bin/python glow_test.py out.png code [code ...]"""
import os, sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 2800 300\naudio-library-name null\nwant-postfx 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.toonbase import HDTextures
HDTextures.enable()
from toontown.suit import Suit, SuitDNA
out, codes = sys.argv[1], sys.argv[2:]
POSE = ('neutral', 0)
if codes and ':' in codes[0]:
    POSE = (codes[0].split(':')[0], int(codes[0].split(':')[1])); codes = codes[1:]
b.setBackgroundColor(0.82, 0.82, 0.82)
b.disableMouse()
n = len(codes) * 2
SP_ = 4.5
for i, code in enumerate(codes):
    for k, on in enumerate((False, True)):
        s = Suit.Suit(); d = SuitDNA.SuitDNA(); d.newSuit(code); s.setDNA(d)
        s.reparentTo(b.render); s.setH(180)
        s.pose(*POSE); s.update()
        if getattr(s, 'dropShadow', None):
            s.dropShadow.hide()
        if on:
            s.setHealthLight(True)
        seat = s.find('**/hd_meter')
        k_ = 0.25 / max(0.01, seat.getScale(b.render)[0])
        s.setScale(s.getScale() * k_)
        p = seat.getPos(b.render)
        s.setPos(((i * 2 + k) - (n - 1) / 2.0) * 1.4 - p.x, -p.y, -p.z)
        print(code, on, 'emblem node:', not s.find('**/hd_emblem').isEmpty())
b.camLens.setFov(1.3 * n)
b.camera.setPos(0, -62.0, 0.0)
b.camera.lookAt(0, 0, 0)
b.graphicsEngine.renderFrame(); b.graphicsEngine.renderFrame()
b.win.saveScreenshot(Filename.fromOsSpecific(os.path.abspath(out)))
