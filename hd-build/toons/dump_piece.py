"""Dump every mesh of an ORIGINAL toon piece to JSON for the Blender project: per GeomNode its name, vertices
(position, uv, colour if any, joint weights if skinned) and triangles, in the model's own coordinates.
Usage (open-toontown root): PYTHONPATH=. venv/bin/python dump_piece.py phase_3/models/char/duck-heads-1000 out.json"""
import json, os, sys
from panda3d.core import *
loadPrcFileData('', 'window-type none\naudio-library-name null\nnotify-level warning\nmodel-path resources\n')
loader = Loader.getGlobalPtr()
getModelPath().prependDirectory(Filename.fromOsSpecific(os.path.join(os.getcwd(), 'resources')))
rel, out = sys.argv[1], sys.argv[2]
model = NodePath(loader.loadSync(Filename(rel + '.bam'), LoaderOptions()))
nodes = []
for np in model.findAllMatches('**/+GeomNode'):
    gn = np.node()
    mat = np.getMat(model)
    for gi in range(gn.getNumGeoms()):
        geom = gn.getGeom(gi).decompose()
        vd = geom.getVertexData()
        rv = GeomVertexReader(vd, 'vertex')
        rt = GeomVertexReader(vd, 'texcoord') if vd.hasColumn('texcoord') else None
        rc = GeomVertexReader(vd, 'color') if vd.hasColumn('color') else None
        table = vd.getTransformBlendTable()
        rb = GeomVertexReader(vd, 'transform_blend') if table else None
        verts = []
        for i in range(vd.getNumRows()):
            p = mat.xformPoint(rv.getData3())
            v = {'p': [p.x, p.y, p.z]}
            if rt:
                uv = rt.getData2(); v['uv'] = [uv.x, uv.y]
            if rc:
                c = rc.getData4(); v['c'] = [c.x, c.y, c.z, c.w]
            if rb:
                bl = table.getBlend(rb.getData1i())
                v['w'] = [[bl.getTransform(k).getJoint().getName(), bl.getWeight(k)] for k in range(bl.getNumTransforms())]
            verts.append(v)
        tris = []
        for pi in range(geom.getNumPrimitives()):
            prim = geom.getPrimitive(pi)
            for f in range(prim.getNumPrimitives()):
                s = prim.getPrimitiveStart(f)
                tris.append([prim.getVertex(s), prim.getVertex(s + 1), prim.getVertex(s + 2)])
        nodes.append({'name': np.getName(), 'parent': np.getParent().getName(), 'geom': gi, 'verts': verts, 'tris': tris})
json.dump({'file': rel, 'nodes': nodes}, open(out, 'w'))
print(rel, len(nodes), 'meshes', sum(len(n['verts']) for n in nodes), 'verts')
