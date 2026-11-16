"""Build enemies through the game's own Suit class and photograph them, HD model beside the original."""
import os, sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 1500 800\naudio-library-name null\nwant-postfx 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.toonbase import HDTextures
HDTextures.enable()
from toontown.suit import Suit, SuitDNA
out = sys.argv[1]


def make(code, hd):
    loadPrcFileData('', 'want-hd-suits %s' % ('#t' if hd else '#f'))
    Suit._hdModelPaths.clear()
    s = Suit.Suit(); d = SuitDNA.SuitDNA(); d.newSuit(code); s.setDNA(d)
    return s


results = []
CODE = sys.argv[2] if len(sys.argv) > 2 else 'f'
row = [(CODE + " HD neutral", make(CODE, True), 'neutral', 0, 180), (CODE + " original", make(CODE, False), 'neutral', 0, 180),
       (CODE + " HD walk", make(CODE, True), 'walk', 6, 150), (CODE + " HD back", make(CODE, True), 'neutral', 20, 0),
       (CODE + " HD walk 12", make(CODE, True), 'walk', 12, 210)]
b.setBackgroundColor(0.82, 0.82, 0.82)
b.disableMouse()
for i, (label, s, anim, frame, h) in enumerate(row):
    s.reparentTo(b.render)
    s.setPos((i - 2) * 6.0, 0, 0)
    s.setH(h)
    s.pose(anim, frame)
    if getattr(s, 'dropShadow', None):
        s.dropShadow.hide()
    results.append((label, s.hdModel, [n.getName() for n in s.findAllMatches('**/+GeomNode')][:6],
                    bool(s.leftHand) and not s.leftHand.isEmpty(), round(s.getGeomNode().getScale()[0], 4)))
b.camLens.setFov(30)
b.camera.setPos(0, -52, 3.6)
b.camera.lookAt(0, 0, 2.6)
b.graphicsEngine.renderFrame(); b.graphicsEngine.renderFrame()
b.win.saveScreenshot(Filename.fromOsSpecific(os.path.abspath(out)))
for r in results:
    print("SUIT", r)
# the other code paths the doc lists must not break on an HD enemy
s = make(CODE, True)
lose = s.getLoseActor(); print("lose actor ok:", not lose.isEmpty(), "| uses original parts:", not lose.find('**/torso').isEmpty())
s2 = make(CODE, True); s2.makeWaiter(); print("makeWaiter ok, still HD:", s2.hdModel)
s3 = make(CODE, True)
s3.getStyleDept = (lambda: SuitDNA.getDeptFullname(s3.style.dept)); s3.getActualLevel = (lambda: 1)
s3.makeSkeleton(); print("makeSkeleton ok, hd flag:", s3.hdModel, "| medallion stashed:", s3.corpMedallion.isStashed())
s4 = make(CODE, True); print("HD medallion stashed:", s4.corpMedallion.isStashed(), "| health bar parent:", s4.healthBar.getParent().getName())
