"""Dump body_hd and head_hd (rest pose, native size, atlas UVs, split normals, joint weights) for build_bam.py.
Set OUT before running."""
import bpy, json

OUT = globals()["OUT"]
meshes = []
for name in ("body_hd", "head_hd"):
    ob = bpy.data.objects[name]
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers["atlas"].data
    groups = [g.name for g in ob.vertex_groups]
    normals = me.corner_normals
    index, verts, tris = {}, [], []
    for t in me.loop_triangles:
        tri = []
        for li in t.loops:
            vi = me.loops[li].vertex_index
            n = normals[li].vector
            u = uv[li].uv
            key = (vi, round(n.x, 3), round(n.y, 3), round(n.z, 3), round(u.x, 5), round(u.y, 5))
            k = index.get(key)
            if k is None:
                k = index[key] = len(verts)
                v = me.vertices[vi]
                verts.append({"p": [round(c, 5) for c in v.co], "n": [round(c, 4) for c in n], "uv": [round(u.x, 5), round(u.y, 5)],
                              "w": [[groups[g.group], round(g.weight, 4)] for g in v.groups if g.weight > 0.001]})
            tri.append(k)
        tris.append(tri)
    meshes.append({"name": name, "verts": verts, "tris": tris})
json.dump({"meshes": meshes}, open(OUT, "w"))
result = {m["name"]: [len(m["verts"]), len(m["tris"])] for m in meshes}
