#!/usr/bin/env python3
"""
Builds smoother versions of low-polygon character models.

Each triangle is split into four (twice by default, so 16x the triangles)
and the new vertices are pushed out onto the curved surface implied by the
model's smooth normals ("Phong tessellation").  Round forms become round in
silhouette, not just in shading.  Edges sharper than CREASE_ANGLE (lapels,
box corners, open rims) are kept exactly as modelled.

Skinning survives: every new vertex blends the joint weights, UVs and
colours of the vertices it was created between, so existing animations play
on the new mesh unchanged.  The models also gain vertex normals.

Originals are not modified.  Output goes to resources-hd/ under the same
relative path, which the client lays over resources/ (see HDTextures.py).

Run with the game's Python (needs Panda3D):
    venv/bin/python tools/smooth_models.py phase_3/models/char/mickey-1200.bam
"""
import math
import os
import sys

from panda3d.core import (Filename, Geom, GeomNode, GeomTriangles,
                          GeomVertexData, GeomVertexReader, GeomVertexWriter,
                          InternalName, Loader, LoaderOptions, NodePath,
                          SparseArray, TransformBlend, TransformBlendTable,
                          Vec3, Point3, loadPrcFileData)

loadPrcFileData('', 'window-type none\naudio-library-name null\n'
                    'notify-level warning\nbam-texture-mode unchanged')

SRC = 'resources'
DST = 'resources-hd'
LEVELS = 2
CREASE_ANGLE = 50.0     # degrees; sharper edges stay sharp
ROUNDNESS = 0.75        # 0 = flat subdivision, 1 = full Phong tessellation

class Mesh:
    """Triangles over welded positions, with per-corner attribute recipes.

    points : list of Vec3, one per distinct position
    attrs  : list of (vdataKey, {sourceRow: weight}) describing how to build
             a vertex's UVs / colours / joint weights from the source rows
    tris   : list of (p0, p1, p2, a0, a1, a2, owner)
    """

    def __init__(self):
        self.points = []
        self.attrs = []
        self.tris = []


def analyse(mesh, cosCrease):
    """Returns (edgeFaces, creaseEdges, cornerNormal) for a mesh.

    cornerNormal[(point, tri)] is the smooth normal at that corner: the
    area-weighted average of the faces around the point that can be reached
    from this one without crossing a crease."""
    pts, tris = mesh.points, mesh.tris
    raw = []      # area-weighted face normals
    unit = []
    for t in tris:
        n = (pts[t[1]] - pts[t[0]]).cross(pts[t[2]] - pts[t[0]])
        raw.append(n)
        u = Vec3(n)
        u.normalize()
        unit.append(u)
    edgeFaces = {}
    for ti, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edgeFaces.setdefault((a, b) if a < b else (b, a), []).append(ti)
    crease = set()
    for e, faces in edgeFaces.items():
        if len(faces) != 2 or unit[faces[0]].dot(unit[faces[1]]) < cosCrease:
            crease.add(e)
    around = {}
    for ti, t in enumerate(tris):
        for p in t[:3]:
            around.setdefault(p, []).append(ti)
    corner = {}
    for p, faces in around.items():
        parent = {f: f for f in faces}

        def find(f):
            while parent[f] != f:
                parent[f] = parent[parent[f]]
                f = parent[f]
            return f
        for f in faces:
            t = tris[f]
            for q in t[:3]:
                if q == p:
                    continue
                e = (p, q) if p < q else (q, p)
                if e in crease:
                    continue
                for g in edgeFaces[e]:
                    if g != f and g in parent:
                        parent[find(g)] = find(f)
        sums = {}
        for f in faces:
            r = find(f)
            if r in sums:
                sums[r] += raw[f]
            else:
                sums[r] = Vec3(raw[f])
        for f in faces:
            n = Vec3(sums[find(f)])
            if not n.normalize():
                n = Vec3(unit[f])
            corner[(p, f)] = n
    return edgeFaces, crease, corner


def subdivide(mesh, cosCrease):
    edgeFaces, crease, corner = analyse(mesh, cosCrease)
    pts = mesh.points
    out = Mesh()
    out.points = list(pts)
    out.attrs = list(mesh.attrs)
    midPoint = {}
    midAttr = {}

    def mid_point(a, b):
        e = (a, b) if a < b else (b, a)
        if e in midPoint:
            return midPoint[e]
        pa, pb = pts[a], pts[b]
        m = (pa + pb) * 0.5
        if e not in crease:
            f = edgeFaces[e][0]
            na, nb = corner[(a, f)], corner[(b, f)]
            qa = m - na * (m - pa).dot(na)
            qb = m - nb * (m - pb).dot(nb)
            m = m * (1.0 - ROUNDNESS) + (qa + qb) * (0.5 * ROUNDNESS)
        out.points.append(m)
        midPoint[e] = len(out.points) - 1
        return midPoint[e]

    def mid_attr(a, b):
        e = (a, b) if a < b else (b, a)
        if e in midAttr:
            return midAttr[e]
        key, ra = mesh.attrs[a]
        _, rb = mesh.attrs[b]
        recipe = {}
        for src in (ra, rb):
            for row, w in src.items():
                recipe[row] = recipe.get(row, 0.0) + w * 0.5
        out.attrs.append((key, recipe))
        midAttr[e] = len(out.attrs) - 1
        return midAttr[e]

    for p0, p1, p2, a0, a1, a2, owner in mesh.tris:
        m01, m12, m20 = mid_point(p0, p1), mid_point(p1, p2), mid_point(p2, p0)
        b01, b12, b20 = mid_attr(a0, a1), mid_attr(a1, a2), mid_attr(a2, a0)
        out.tris.append((p0, m01, m20, a0, b01, b20, owner))
        out.tris.append((m01, p1, m12, b01, a1, b12, owner))
        out.tris.append((m20, m12, p2, b20, b12, a2, owner))
        out.tris.append((m01, m12, m20, b01, b12, b20, owner))
    return out


def process(root):
    """Subdivides every GeomNode under root in place.  Returns (before, after)
    triangle counts."""
    cosCrease = math.cos(math.radians(CREASE_ANGLE))
    mesh = Mesh()
    weld = {}
    attrOf = {}
    sources = {}     # vdataKey -> (vdata, node index)
    nodes = [np for np in root.findAllMatches('**/+GeomNode')]
    mats = []
    for ni, np in enumerate(nodes):
        node = np.node()
        mat = np.getMat(root)
        mats.append(mat)
        for gi in range(node.getNumGeoms()):
            geom = node.getGeom(gi)
            vdata = geom.getVertexData()
            if not vdata.hasColumn('vertex'):
                continue
            key = (ni, vdata.this)
            if key not in sources:
                sources[key] = vdata
                reader = GeomVertexReader(vdata, 'vertex')
                for row in range(vdata.getNumRows()):
                    p = mat.xformPoint(Point3(reader.getData3()))
                    k = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
                    if k not in weld:
                        mesh.points.append(Vec3(p))
                        weld[k] = len(mesh.points) - 1
                    mesh.attrs.append((key, {row: 1.0}))
                    attrOf[(key, row)] = (weld[k], len(mesh.attrs) - 1)
            for prim in geom.decompose().getPrimitives():
                if prim.getNumVerticesPerPrimitive() != 3:
                    continue
                for t in range(prim.getNumPrimitives()):
                    s = prim.getPrimitiveStart(t)
                    c = [attrOf[(key, prim.getVertex(s + j))] for j in range(3)]
                    if len({c[0][0], c[1][0], c[2][0]}) < 3:
                        continue      # degenerate
                    mesh.tris.append((c[0][0], c[1][0], c[2][0],
                                      c[0][1], c[1][1], c[2][1], (ni, gi)))
    before = len(mesh.tris)
    if before == 0:
        return 0, 0
    for _ in range(LEVELS):
        mesh = subdivide(mesh, cosCrease)
    _, _, corner = analyse(mesh, cosCrease)

    byOwner = {}
    for ti, t in enumerate(mesh.tris):
        byOwner.setdefault(t[6], []).append(ti)

    for (ni, gi), triIndices in byOwner.items():
        node = nodes[ni].node()
        inv = mats[ni].__class__(mats[ni])
        inv.invertInPlace()
        key = mesh.attrs[mesh.tris[triIndices[0]][3]][0]
        src = sources[key]
        newData = GeomVertexData(src.replaceColumn(
            InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CNormal))
        newData.clearRows()
        rowOf = {}
        rows = []         # (point, attr, normal)
        indices = []
        for ti in triIndices:
            t = mesh.tris[ti]
            for j in range(3):
                n = corner[(t[j], ti)]
                k = (t[j], t[3 + j], round(n[0], 3), round(n[1], 3), round(n[2], 3))
                if k not in rowOf:
                    rowOf[k] = len(rows)
                    rows.append((t[j], t[3 + j], n))
                indices.append(rowOf[k])
        newData.setNumRows(len(rows))

        fmt = newData.getFormat()
        srcTable = src.getTransformBlendTable()
        newTable = TransformBlendTable() if srcTable is not None else None
        for ci in range(fmt.getNumColumns()):
            name = fmt.getColumn(ci).getName()
            sname = name.getName()
            writer = GeomVertexWriter(newData, name)
            if sname == 'vertex':
                for point, _, _ in rows:
                    writer.setData3(inv.xformPoint(Point3(mesh.points[point])))
            elif sname == 'normal':
                for _, _, n in rows:
                    v = inv.xformVec(n)
                    v.normalize()
                    writer.setData3(v)
            elif sname == 'transform_blend':
                reader = GeomVertexReader(src, name)
                for _, attr, _ in rows:
                    blend = TransformBlend()
                    for row, w in mesh.attrs[attr][1].items():
                        reader.setRow(row)
                        sb = srcTable.getBlend(reader.getData1i())
                        for k in range(sb.getNumTransforms()):
                            blend.addTransform(sb.getTransform(k), sb.getWeight(k) * w)
                    blend.normalizeWeights()
                    writer.setData1i(newTable.addBlend(blend))
            else:
                reader = GeomVertexReader(src, name)
                for _, attr, _ in rows:
                    acc = [0.0, 0.0, 0.0, 0.0]
                    for row, w in mesh.attrs[attr][1].items():
                        reader.setRow(row)
                        d = reader.getData4()
                        for k in range(4):
                            acc[k] += d[k] * w
                    writer.setData4(acc[0], acc[1], acc[2], acc[3])
        if newTable is not None:
            newTable.setRows(SparseArray.lowerOn(len(rows)))
            newData.setTransformBlendTable(newTable)

        prim = GeomTriangles(Geom.UHStatic)
        for k in range(0, len(indices), 3):
            prim.addVertices(indices[k], indices[k + 1], indices[k + 2])
        prim.closePrimitive()
        newGeom = Geom(newData)
        newGeom.addPrimitive(prim)
        node.setGeom(gi, newGeom)
    return before, len(mesh.tris)


def main():
    files = sys.argv[1:]
    if not files:
        print(__doc__)
        return 1
    loader = Loader.getGlobalPtr()
    root_dir = os.path.abspath(SRC)
    for rel in files:
        src = os.path.join(root_dir, rel)
        node = loader.loadSync(Filename.fromOsSpecific(src), LoaderOptions(LoaderOptions.LFNoCache))
        if node is None:
            print('%s: could not load' % rel)
            continue
        np = NodePath(node)
        before, after = process(np)
        # Store texture names relative to the model path, so they resolve
        # the same way wherever this file is loaded from.
        for tex in np.findAllTextures():
            for getter, setter in ((tex.getFullpath, tex.setFilename),
                                   (tex.getAlphaFullpath, tex.setAlphaFilename)):
                p = getter().toOsSpecific()
                if p and os.path.abspath(p).startswith(root_dir + os.sep):
                    setter(Filename.fromOsSpecific(os.path.relpath(os.path.abspath(p), root_dir)))
        dst = os.path.join(os.path.abspath(DST), rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ok = np.writeBamFile(Filename.fromOsSpecific(dst))
        print('%s: %d -> %d triangles%s' % (rel, before, after, '' if ok else '  (WRITE FAILED)'))


if __name__ == '__main__':
    sys.exit(main())
