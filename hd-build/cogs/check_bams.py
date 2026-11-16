"""List every HD enemy model with what the game needs from it: a texture, the light seat, the emblem node."""
from panda3d.core import *
loadPrcFile('etc/Configrc.prc'); loadPrcFileData('', 'window-type none\naudio-library-name null\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
from toontown.toonbase import HDTextures
HDTextures.enable()
import glob, os
bad = 0
for f in sorted(glob.glob('resources-hd/phase_3.5/models/char/*_hd.bam')):
    m = loader.loadModel(Filename.fromOsSpecific(os.path.abspath(f)))
    tex = [t.getFilename().getBasename() for t in m.findAllTextures()]
    seat = not m.find('**/joint_attachMeter').find('hd_meter').isEmpty()
    e = m.find('**/hd_emblem')
    ok = bool(tex) and seat and not e.isEmpty()
    bad += not ok
    print('%-34s textures %-40s seat %-5s emblem tris %s' % (os.path.basename(f), tex, seat, e.node().getGeom(0).getPrimitive(0).getNumFaces() if not e.isEmpty() else 0))
print('MODELS WITH A PROBLEM:', bad)
