#!/usr/bin/env python
"""
Writes every cog, assembled as the game shows it (body, head, suit textures,
neutral pose), as a model file next to its turnaround sheet.

For each "NN_Name_Dept.png" in the turnaround folder this writes
"NN_Name_Dept_model.obj" (+ .mtl), which Blender and most tools open, and
"NN_Name_Dept_model.bam", Panda3D's own format.  The .obj is Y-up, in game
units (feet); its materials point at the game's texture files in resources/.

Usage (from the repository root, with the game's Python):
    PYTHONPATH=. venv/bin/python tools/export_cog_models.py ../open-toontown-hd/cog-turnarounds
"""
import os
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 64 64\naudio-library-name null\nwant-postfx 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.suit import Suit, SuitDNA

out = sys.argv[1]
sheets = sorted(f for f in os.listdir(out) if f.endswith('.png') and f[:2].isdigit())


def make(code):
    s = Suit.Suit(); d = SuitDNA.SuitDNA(); d.newSuit(code); s.setDNA(d)
    return s, d


def build():
    for code in SuitDNA.suitHeadTypes:
        yield make(code)[0]
    for code in ('f', 'cc', 'p', 'sd', 'ym', 'mb'):
        s, d = make(code)
        s.getStyleDept = (lambda dd=d: SuitDNA.getDeptFullname(dd.dept)); s.getActualLevel = (lambda: 1)
        s.makeSkeleton()
        yield s
    for code in ('f', 'ym'):
        s, d = make(code); s.makeWaiter()
        yield s


def export(s, base):
    s.reparentTo(b.render); s.setPosHpr(0, 0, 0, 0, 0, 0); s.pose('neutral', 0)
    if getattr(s, 'dropShadow', None):
        s.dropShadow.hide()
    try:
        s.nametag3d.hide()
    except Exception:
        pass
    s.update()
    b.graphicsEngine.renderFrame()
    thread = Thread.getCurrentThread()
    materials = {}
    lines = ['# %s' % base, 'mtllib %s.mtl' % base]
    faces = []
    nv = 0
    tris = 0
    for np in s.findAllMatches('**/+GeomNode'):
        if np.isHidden() or any(a.isHidden() for a in np.getAncestors()):
            continue
        if any('shadow' in a.getName().lower() or 'nametag' in a.getName().lower() for a in np.getAncestors()):
            continue
        node = np.node()
        mat = np.getMat(s)
        net = np.getNetState()
        for gi in range(node.getNumGeoms()):
            state = net.compose(node.getGeomState(gi))
            tex = None
            ta = state.getAttrib(TextureAttrib)
            if ta is not None and not ta.isOff() and ta.getNumOnStages():
                tex = ta.getTexture()
            colour = (1.0, 1.0, 1.0)
            ca = state.getAttrib(ColorAttrib)
            if ca is not None and ca.getColorType() == ColorAttrib.TFlat:
                colour = tuple(ca.getColor())[:3]
            cs = state.getAttrib(ColorScaleAttrib)
            if cs is not None:
                colour = tuple(colour[k] * cs.getScale()[k] for k in range(3))
            key = (tex.getName() if tex else None, tuple(round(c, 3) for c in colour))
            if key not in materials:
                path = Filename(tex.getFullpath()).toOsSpecific() if tex and tex.hasFullpath() else None
                materials[key] = ('mat%02d_%s' % (len(materials), (key[0] or 'plain').replace(' ', '_')), path, colour)
            geom = node.getGeom(gi).decompose()
            vdata = geom.getVertexData().animateVertices(True, thread)
            vr = GeomVertexReader(vdata, 'vertex')
            hasN, hasT = vdata.hasColumn('normal'), vdata.hasColumn('texcoord')
            nr = GeomVertexReader(vdata, 'normal') if hasN else None
            tr = GeomVertexReader(vdata, 'texcoord') if hasT else None
            rows = vdata.getNumRows()
            for _ in range(rows):
                p = mat.xformPoint(vr.getData3())
                lines.append('v %.5f %.5f %.5f' % (p[0], p[2], -p[1]))
                if hasN:
                    n = mat.xformVec(nr.getData3()); n.normalize()
                    lines.append('vn %.4f %.4f %.4f' % (n[0], n[2], -n[1]))
                else:
                    lines.append('vn 0 1 0')
                uv = tr.getData2() if hasT else (0, 0)
                lines.append('vt %.5f %.5f' % (uv[0], uv[1]))
            faces.append('g %s' % (np.getName() or 'part'))
            faces.append('usemtl %s' % materials[key][0])
            for prim in geom.getPrimitives():
                if prim.getNumVerticesPerPrimitive() != 3:
                    continue
                for k in range(prim.getNumPrimitives()):
                    st = prim.getPrimitiveStart(k)
                    i = [prim.getVertex(st + j) + nv + 1 for j in range(3)]
                    faces.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (i[0], i[0], i[0], i[1], i[1], i[1], i[2], i[2], i[2]))
                    tris += 1
            nv += rows
    with open(os.path.join(out, base + '.obj'), 'w') as f:
        f.write('\n'.join(lines + faces) + '\n')
    with open(os.path.join(out, base + '.mtl'), 'w') as f:
        for name, path, colour in materials.values():
            f.write('newmtl %s\nKd %.3f %.3f %.3f\nKs 0 0 0\n' % ((name,) + colour))
            if path:
                f.write('map_Kd %s\n' % path)
            f.write('\n')
    s.writeBamFile(Filename.fromOsSpecific(os.path.join(out, base + '.bam')))
    s.detachNode()
    return tris


count = 0
for sheet, s in zip(sheets, build()):
    base = sheet[:-4] + '_model'
    tris = export(s, base)
    print('%s: %d triangles' % (base, tris))
    count += 1
print('exported', count, 'of', len(sheets))
