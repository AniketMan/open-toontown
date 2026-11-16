"""Rig the HD Double Talker (suit A) as tools/ENEMY_MODEL_SWAP.md requires.

- Skeleton: the body's own joints (names and hierarchy unchanged) in the body's own rest pose and native size,
  read from suit<Body>-mod (ym_rig.json "bind").
- The model is built in the pose of the concept sheet, which is the original's neutral pose made symmetric.
  Each vertex is carried from that pose back to the rest pose by its joints, so the game's animations put it
  back where it was modelled.
- Rigid parts follow the joint named when they were built. Garments take their weights from the matching part
  of the original; every trim piece takes its weights from the garment it is sewn to, so nothing slides.
- At most three weights per vertex. The result is joined into two meshes, body_hd and head_hd.
"""
import bpy, json, math
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/11_Double-Talker_Lawbot/"
data = json.load(open(SP + "dt_rig.json"))
col = bpy.data.collections["DoubleTalker"]
K = data["suit_scale"]                       # the game scales the body by this (3.35 / 5.29 for the Pencil Pusher)
X = Matrix.Scale(-1, 4, (1, 0, 0))           # mirror left <-> right

PAIRS = [(a, a.replace("Lh_", "Rh_")) for a in ("Lh_wrist", "Lh_1", "Lh_2", "Lh_arm", "Lh_index1", "Lh_index2", "Lh_thumb1", "Lh_thumb2")]
PAIRS += [("Luparm", "Ruparm"), ("Lforearm", "Rforearm"), ("jnt24_2", "jnt27_2"), ("scale_jnt24_1", "scale_jnt27_1"),
          ("jnt22_1", "jnt28_1"), ("Lshoulder_arm", "null7"), ("Lsleeve_trans", "Rsleeve_trans"),
          ("scale_jnt3_1", "scale_jnt4_1"), ("jnt3_2", "jnt4_2"), ("to_LegL", "to_legR"), ("to_ballL", "to_ballR"),
          ("to_coatL", "to_coatR"), ("CONSlegL", "CONSlegR"), ("to_coatLBack", "to_coatRBack"),
          ("to_coatLFront", "to_coatRFront"), ("shoulderL1", "shoulderR1"), ("joint_Lhold", "joint_Rhold")]
ONE_SIDED = ()
L2R = dict(PAIRS)
R2L = {r: l for l, r in PAIRS}


def affine(j):
    m = Matrix((j["x"], j["y"], j["z"])).transposed().to_4x4()
    m.translation = Vector(j["head"])
    return m


def bone_frame(m):
    """Orthonormal bone frame from a joint transform (Blender bones point along the joint's y axis)."""
    y = m.col[1].xyz
    z = m.col[2].xyz
    if y.length < 1e-6:
        y = Vector((0, 1, 0))
    y = y.normalized()
    z = z - y * z.dot(y)
    if z.length < 1e-6:
        z = y.orthogonal()
    z.normalize()
    x = y.cross(z).normalized()
    out = Matrix((x, y, z)).transposed().to_4x4()
    out.translation = m.translation
    return out


BIND = {j["name"]: affine(j) for j in data["bind"]}
NEUTRAL = {j["name"]: affine(j) for j in data["joints"]}
ORDER = [j["name"] for j in data["bind"]]
PARENT = {j["name"]: j["parent"] for j in data["bind"]}

# Sheet pose -> rest pose, per joint. Left side and centre come from the original's neutral pose; the right
# side is the mirror of the left and the centre is made symmetric, because the HD model is symmetric.
TO_REST = {}
for name in ORDER:
    if name in R2L:
        continue
    n = NEUTRAL[name]
    m = BIND[name] @ n.inverted() if abs(n.determinant()) > 1e-9 else None
    if m is not None and name not in L2R and name not in ONE_SIDED:
        m = (m + X @ m @ X) * 0.5
    TO_REST[name] = m
for name in ORDER:
    if TO_REST.get(name) is None and name not in R2L:
        p = PARENT[name]
        TO_REST[name] = TO_REST.get(p) if p else Matrix.Identity(4)
# The shoulder joints ride rigidly on to_SHOULDER, which is made symmetric above; give them the same transform, or
# cloth weighted between the two is pulled two ways and wrinkles.
TO_REST["shoulderL1"] = TO_REST["to_shoulder"]
# Suit A's rest pose is not symmetric and its right-side joints have mirrored axes. A right joint's move from rest
# to the modelled pose is the mirror of the left joint's (same turn, mirrored), taking the right joint's OWN rest
# position to the mirror of where the left joint stands.
for r, l in R2L.items():
    if TO_REST.get(l) is None or abs(TO_REST[l].determinant()) < 1e-9:
        TO_REST[r] = X @ TO_REST[l] @ X if TO_REST.get(l) is not None else Matrix.Identity(4)
        continue
    d = X @ TO_REST[l].inverted() @ X                      # mirrored left deformation (rest -> modelled pose)
    m3 = d.to_3x3()
    target = X @ NEUTRAL[l].translation
    d.translation = target - m3 @ BIND[r].translation
    TO_REST[r] = d.inverted()
TO_REST["shoulderR1"] = TO_REST["to_shoulder"]

# ---------------------------------------------------------------- armature in the body's rest pose
old = bpy.data.objects.get("DT_Rig")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
arm_data = bpy.data.armatures.new("DT_Rig")
arm = bpy.data.objects.new("DT_Rig", arm_data)
col.objects.link(arm)
arm.show_in_front = True
arm_data.display_type = 'STICK'
bpy.context.view_layer.objects.active = arm
for o in bpy.context.selected_objects:
    o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
REST = {}
for name in ORDER:
    m = bone_frame(BIND[name])
    REST[name] = m
    eb = arm_data.edit_bones.new(name)
    eb.head = m.translation
    eb.tail = m.translation + m.col[1].xyz * 0.16
    eb.align_roll(m.col[2].xyz)
for name in ORDER:
    if PARENT[name]:
        arm_data.edit_bones[name].parent = arm_data.edit_bones[PARENT[name]]
        arm_data.edit_bones[name].use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- weights
meshes = [o for o in col.objects if o.type == 'MESH' and not o.hide_render]


def top3(acc):
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:3]
    total = sum(w for _, w in top) or 1.0
    return {n: w / total for n, w in top if w / total > 0.01}


def mirror_names(w):
    return {L2R.get(n, R2L.get(n, n)): v for n, v in w.items()}


# source points from the original, left side and centre only, sorted by part (its unnamed parts mix shoes and cuffs)
SUBSETS = {"torso": []}
for g in data["geoms"]:
    if g["name"] != "torso":
        continue
    for p, w in zip(g["verts"], g["weights"]):
        if not w or p[0] < -0.02 or any(n in R2L for n in w):
            continue
        w = {("to_shoulder" if n == "to_head" else n): v for n, v in w.items()}     # the head is its own rigid piece
        SUBSETS["torso"].append((Vector(p), w))


def tree_of(points):
    t = KDTree(len(points))
    for i, (p, w) in enumerate(points):
        t.insert(p, i)
    t.balance()
    return t


def lookup(tree, points, co, k=4):
    """Blend the weights of the nearest source points; right-side vertices read the mirrored left side."""
    flip = co.x < 0
    q = Vector((-co.x, co.y, co.z)) if flip else co
    acc = {}
    for _, idx, dist in tree.find_n(q, k):
        f = 1.0 / (dist + 0.02) ** 2
        for n, w in points[idx][1].items():
            acc[n] = acc.get(n, 0.0) + w * f
    w = top3(acc)
    return mirror_names(w) if flip else w


GARMENT_SOURCE = {"DT_Jacket": "torso", "DT_ShirtBody": "torso"}
TREES = {k: (tree_of(v), v) for k, v in SUBSETS.items()}
W = {}                                       # object name -> list of {bone: weight} per vertex
for ob in meshes:
    names = [g.name for g in ob.vertex_groups]
    W[ob.name] = []
    for v in ob.data.vertices:
        n = names[v.groups[0].group] if v.groups else None
        W[ob.name].append({n: 1.0} if n in REST else (n if n and n.startswith("@") else None))

def ramp(lo, hi, z):
    t = max(0.0, min(1.0, (z - lo) / (hi - lo)))
    return t * t * (3 - 2 * t)


def two(a, b, t):
    return {k: v for k, v in ((a, t), (b, 1.0 - t)) if v > 0.004}


# Limbs are built in the rest pose, straight along their bones, so their weights are simply which stretch of
# bone a point lies beside: rigid sections with one short blend at the elbow and at the knee.
def sleeve_weights(co):
    x = abs(co.x)                                               # shoulder joint 1.67, elbow about 2.55, wrist 3.87
    # Checked against the game's poses: scale_jnt24_1 carries the upper arm and Lh_arm the forearm (it lands the
    # wrist within 0.01 in every pose); shoulderL1 stays on the shoulder.
    if x <= 1.52:
        w = {"shoulderL1": 1.0}
    elif x < 1.82:
        w = two("scale_jnt24_1", "shoulderL1", ramp(1.52, 1.82, x))
    elif x <= 2.36:
        w = {"scale_jnt24_1": 1.0}
    elif x < 2.74:
        w = two("Lh_arm", "scale_jnt24_1", ramp(2.36, 2.74, x))
    else:
        w = {"Lh_arm": 1.0}
    return mirror_names(w) if co.x < 0 else w


def leg_weights(co, side):
    """Thigh on the hip joint, shin on the knee joint, one blend across the knee (hip joint z 3.5, knee z 1.95)."""
    z = co.z
    w = {"scale_jnt3_1": 1.0} if z >= 2.25 else (two("scale_jnt3_1", "jnt3_2", ramp(1.68, 2.25, z)) if z >= 1.68 else {"jnt3_2": 1.0})
    return mirror_names(w) if side == 'R' else w


def trouser_weights(co):
    return leg_weights(co, 'L' if co.x >= 0 else 'R')


def seat_weights(co):
    """The seat is the pelvis (to_MAIN); only its underside, round the crotch, gives toward the two thighs."""
    t = ramp(2.82, 3.4, co.z)
    if t >= 0.996:
        return {"to_MAIN": 1.0}
    left = max(0.0, min(1.0, 0.5 + co.x / 0.6))
    w = {"to_MAIN": t, "scale_jnt3_1": (1 - t) * left, "scale_jnt4_1": (1 - t) * (1 - left)}
    return {k: v for k, v in w.items() if v > 0.004}


def shoe_weights(co):
    w = two("to_ballL", "to_LegL", ramp(0.28, 0.50, -co.y))     # ankle joint, bending at the ball joint (y -0.36)
    return mirror_names(w) if co.x < 0 else w


REST_FN = {"DT_ShoulderCaps": sleeve_weights, "DT_ShoulderCapStuds": sleeve_weights, "DT_ShoulderCapPiping": sleeve_weights, "DT_TrouserBands": trouser_weights, "DT_LimbStuds": trouser_weights, "DT_TrouserPiping": trouser_weights, "DT_Sleeves": sleeve_weights, "DT_Trousers": trouser_weights, "DT_Seat": seat_weights, "DT_Shoes": shoe_weights,
           "DT_Soles": shoe_weights, "DT_SleeveButtons": sleeve_weights, "DT_SleeveStitching": sleeve_weights}
for ob in meshes:
    if not ob.get("rest_space"):
        continue
    for i, v in enumerate(ob.data.vertices):
        w = W[ob.name][i]
        if w is None or isinstance(w, str):
            if w in ("@legL", "@legR"):
                W[ob.name][i] = leg_weights(v.co, w[-1])
            else:
                W[ob.name][i] = (sleeve_weights if w == "@sleeve" else REST_FN[ob.name])(v.co)

for ob in meshes:                            # body garments: from the original, then smoothed along the cloth
    kind = GARMENT_SOURCE.get(ob.name)
    if not kind:
        continue
    tree, pts = TREES[kind]
    w = [lookup(tree, pts, v.co) for v in ob.data.vertices]
    nbrs = [[] for _ in ob.data.vertices]
    for e in ob.data.edges:
        a, b = e.vertices
        nbrs[a].append(b)
        nbrs[b].append(a)
    for _ in range(8):
        new = []
        for i, wi in enumerate(w):
            acc = {n: v * 0.5 for n, v in wi.items()}
            for j in nbrs[i]:
                for n, v in w[j].items():
                    acc[n] = acc.get(n, 0.0) + v * 0.5 / max(1, len(nbrs[i]))
            new.append(top3(acc))
        w = new
    W[ob.name] = w

# trim: every piece moves with the garment it is sewn to. Pieces say which garment when they are built
# ('@sleeve', '@jacket', ...); an untagged piece belongs to the garment its whole object sits on.
garment_pts = {n: [(ob.data.vertices[i].co.copy(), W[n][i]) for i in range(len(ob.data.vertices))]
               for n in GARMENT_SOURCE for ob in [bpy.data.objects[n]]}
GARMENT_TREE = {n: tree_of(p) for n, p in garment_pts.items()}
DIRECTIVE = {"@jacket": "DT_Jacket", "@shirt": "DT_ShirtBody", "@sleeve": "DT_Sleeves", "@trousers": "DT_Trousers"}
OBJECT_GARMENT = {"DT_Lapels": "@jacket", "DT_Pockets": "@jacket", "DT_Collar": "@jacket", "DT_BackStraps": "@jacket", "DT_HemBand": "@jacket",
                  "DT_Stitching": "@jacket", "DT_ButtonStand": "@jacket", "DT_Tie": "@shirt", "DT_BowTie": "@shirt", "DT_BowDots": "@shirt", "DT_Zipper": "@shirt", "DT_ZipTape": "@shirt", "DT_ShirtCollar": "@shirt",
                  "DT_Shirt": "@shirt", "DT_Buttons": "@jacket", "DT_Cord": "@jacket", "DT_HemLining": "@jacket"}


def from_garment(directive, co):
    if directive == "@sleeve":
        return sleeve_weights(co)
    if directive == "@trousers":
        return trouser_weights(co)
    name = DIRECTIVE[directive]
    pts, tree = garment_pts[name], GARMENT_TREE[name]
    acc = {}
    for _, idx, dist in tree.find_n(co, 8):
        f = 1.0 / (dist + 0.03) ** 2
        for n, wv in pts[idx][1].items():
            acc[n] = acc.get(n, 0.0) + wv * f
    return top3(acc)


def islands(me):
    """Connected pieces of a mesh, as lists of vertex indices."""
    parent = list(range(len(me.vertices)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    out = {}
    for i in range(len(parent)):
        out.setdefault(find(i), []).append(i)
    return list(out.values())


RIGID_SIZE = 0.22          # a separate piece smaller than this is a hard part (stud, button, rivet): it moves as one
unassigned = []
rigid_pieces = 0
for ob in meshes:
    if ob.name in GARMENT_SOURCE or ob.get("rest_space"):
        continue
    for isl in islands(ob.data):
        cos = [ob.data.vertices[i].co for i in isl]
        lo = Vector((min(c.x for c in cos), min(c.y for c in cos), min(c.z for c in cos)))
        hi = Vector((max(c.x for c in cos), max(c.y for c in cos), max(c.z for c in cos)))
        whole = None
        for i in isl:
            w = W[ob.name][i]
            if w is None or isinstance(w, str):
                directive = w if isinstance(w, str) else OBJECT_GARMENT.get(ob.name)
                if directive is None:
                    unassigned.append(ob.name)
                    directive = "@jacket"
                if (hi - lo).length < RIGID_SIZE:
                    if whole is None:
                        whole = from_garment(directive, (lo + hi) / 2)
                        rigid_pieces += 1
                    W[ob.name][i] = whole
                else:
                    W[ob.name][i] = from_garment(directive, ob.data.vertices[i].co)

# ---------------------------------------------------------------- carry every vertex to the rest pose, write groups, bind
FROM_REST = {n: m.inverted() for n, m in TO_REST.items() if m is not None}
for ob in meshes:
    ob.vertex_groups.clear()
    groups = {}
    for i, v in enumerate(ob.data.vertices):
        w = W[ob.name][i]
        blend = Matrix.Diagonal((0.0, 0.0, 0.0, 0.0))            # the skinning transform this vertex will get in the sheet pose
        for n, wv in w.items():
            blend += FROM_REST[n] * wv
            if n not in groups:
                groups[n] = ob.vertex_groups.new(name=n)
            groups[n].add([i], wv, 'REPLACE')
        if not ob.get("rest_space"):              # limbs are already in the rest pose
            v.co = blend.inverted() @ v.co        # exact inverse of the blend, so the sheet pose gives back the modelled shape
    ob.data.update()

# cloth thickness and chamfers become real geometry, then everything is joined into the two meshes the game expects
dg = bpy.context.evaluated_depsgraph_get()
baked = []
for ob in meshes:
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    new = bpy.data.objects.new(ob.name + "_baked", me)
    for g in ob.vertex_groups:
        if g.name not in new.vertex_groups:
            new.vertex_groups.new(name=g.name)
    col.objects.link(new)
    baked.append((new, any(g.name == "joint_head" for g in ob.vertex_groups) and len(ob.vertex_groups) == 1))
for ob in meshes:
    bpy.data.objects.remove(ob, do_unlink=True)


def join(objs, name):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    out = bpy.context.view_layer.objects.active
    out.name = name
    out.data.name = name
    return out


head_parts = [o for o, is_head in baked if is_head]
body_parts = [o for o, is_head in baked if not is_head]
result_objs = [join(body_parts, "body_hd"), join(head_parts, "head_hd")]
for ob in result_objs:                       # chamfering blends neighbours' groups: cut back to three and renormalise
    vgs = list(ob.vertex_groups)
    STALE = [0]
    for v in ob.data.vertices:
        STALE[0] += sum(1 for g in v.groups if g.group >= len(vgs))
        gs = sorted((g for g in v.groups if g.group < len(vgs)), key=lambda g: -g.weight)
        keep, drop = gs[:3], gs[3:]
        total = sum(g.weight for g in keep) or 1.0
        pairs = [(g.group, g.weight / total) for g in keep]
        drop_ids = [g.group for g in drop]             # read before removing: removal shifts the element list
        for gi in drop_ids:
            vgs[gi].remove([v.index])
        for gi, w in pairs:
            vgs[gi].add([v.index], w, 'REPLACE')
max_inf = 0
for ob in result_objs:
    ob.parent = arm
    ob.matrix_parent_inverse = Matrix.Identity(4)
    mod = ob.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm
    max_inf = max(max_inf, max(len(v.groups) for v in ob.data.vertices))
arm.scale = (K, K, K)                         # the game applies this scale; rest pose is native size


def apply_pose(key="sheet"):
    """"sheet" = the pose he was modelled in; "anim:frame" = a frame of the game's animation; None = rest pose."""
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    if key is None:
        return
    frame = {j["name"]: affine(j) for j in data["poses"][key]} if key != "sheet" else None
    scale_inv = Matrix.Scale(1.0 / K, 4)
    for name in ORDER:                         # parents come before children
        if frame is None:
            m = scale_inv @ TO_REST[name].inverted() @ REST[name]      # the bone's own frame: a joint's axes may be left-handed
        else:
            m = scale_inv @ frame[name]
        if frame is not None:                  # the joint's true move from rest, applied to the bone's own frame
            m = scale_inv @ frame[name] @ BIND[name].inverted() @ REST[name] if abs(BIND[name].determinant()) > 1e-9 else bone_frame(m)
        arm.pose.bones[name].matrix = m
        bpy.context.view_layer.update()


apply_pose("sheet")
result = {"bones": len(arm.data.bones), "meshes": [o.name for o in result_objs],
          "verts": {o.name: len(o.data.vertices) for o in result_objs},
          "tris": sum(len(p.vertices) - 2 for o in result_objs for p in o.data.polygons),
          "max_weights_per_vertex": max_inf, "stale_group_refs": STALE[0], "objects_without_a_garment": sorted(set(unassigned)),
          "groups": {o.name: len(o.vertex_groups) for o in result_objs}}
