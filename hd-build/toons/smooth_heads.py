"""Smoothed toon heads that keep their flat eye parts.

tools/smooth_models.py rounds every mesh in a head file, which bulges the flat decals the eyes are drawn on (eyes,
pupils and the head-front plate behind them) and breaks the face.  This runs that tool on the head, muzzle and lash
files and then puts the ORIGINAL geometry back on those flat parts, so only the skull, ears, muzzles and nose are
rounded.  Output: resources-hd/phase_3/models/char/<same name>.bam, which the game lays over the original.

Usage (open-toontown root): venv/bin/python <this file>
"""
import glob, os, subprocess, sys
from panda3d.core import *
loadPrcFileData('', 'window-type none\naudio-library-name null\nnotify-level warning\nbam-texture-mode unchanged')
SRC, DST = 'resources', 'resources-hd'
KEEP_FLAT = ('eyes', 'joint_pupil', 'head-front')   # tried rounding head-front on 2026-11-14: it bulges forward and hides the eyes
files = sorted(set(glob.glob(SRC + '/phase_3/models/char/*-heads-1000.bam') + glob.glob(SRC + '/phase_3/models/char/tt_a_chr_dg*_head_1000.bam') +
                   glob.glob(SRC + '/phase_3/models/char/dog*headMuzzles-1000.bam')))
rel = [f[len(SRC) + 1:] for f in files]
subprocess.run([sys.executable, 'tools/smooth_models.py'] + rel, check=True, capture_output=True)
loader = Loader.getGlobalPtr()
getModelPath().prependDirectory(Filename.fromOsSpecific(os.getcwd()))
getModelPath().prependDirectory(Filename.fromOsSpecific(os.path.join(os.getcwd(), SRC)))


def flat(np):
    name = np.getName()
    if any(name.startswith(k) for k in KEEP_FLAT):
        return True
    parent = np.getParent()
    return (not parent.isEmpty()) and 'pupil' in parent.getName()


for r in rel:
    orig = NodePath(loader.loadSync(Filename(SRC + '/' + r), LoaderOptions()))
    new = NodePath(loader.loadSync(Filename(DST + '/' + r), LoaderOptions()))
    o_nodes = [np for np in orig.findAllMatches('**/+GeomNode')]
    n_nodes = [np for np in new.findAllMatches('**/+GeomNode')]
    assert len(o_nodes) == len(n_nodes), r
    put_back = 0
    for o, n in zip(o_nodes, n_nodes):
        assert o.getName() == n.getName(), (r, o.getName(), n.getName())
        if flat(o):
            gn = n.node()
            gn.removeAllGeoms()
            for i in range(o.node().getNumGeoms()):
                gn.addGeom(o.node().getGeom(i).makeCopy(), o.node().getGeomState(i))
            put_back += 1
    new.writeBamFile(Filename(DST + '/' + r))
    tris = sum(np.node().getGeom(i).getPrimitive(0).getNumFaces() for np in n_nodes for i in range(np.node().getNumGeoms()))
    print('%-58s flat parts kept: %2d   triangles: %d' % (r, put_back, tris))
