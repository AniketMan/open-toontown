"""Rig the HD Flunky as tools/ENEMY_MODEL_SWAP.md requires.

- Skeleton: the body's own joints (names and hierarchy unchanged) in the body's own rest pose and native size,
  read from suit<Body>-mod (flunky_rig.json "bind").
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

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/01_Flunky_Bossbot/"
data = json.load(open(SP + "flunky_rig.json"))
col = bpy.data.collections["Flunky"]
K = data["suit_scale"]                       # the game scales the body by this (4.0 / 4.14 for the Flunky)
X = Matrix.Scale(-1, 4, (1, 0, 0))           # mirror left <-> right

PAIRS = [("Lh_wrist", "Rh_wrist"), ("Lh_1", "Rh_5"), ("Lh_2", "Rh_6"), ("Lh_index1", "Rh_index5"),
         ("Lh_index2", "Rh_index6"), ("Lh_thumb1", "Rh_thumb7"), ("Lh_thumb2", "Rh_thumb8"), ("LupVct", "RupVct"),
         ("Lh_arm", "Rh_arm"), ("Lshoulder_arm", "Rshoulder_arm"), ("Lsleeve_trans", "Rsleeve_trans"),
         ("null5", "null4"), ("jnt23_1", "jnt24_1"), ("scale_jnt26_1", "scale_jnt27_1"), ("Luparm", "Ruparm"),
         ("jnt26_2", "jnt27_2"), ("Lforearm", "Rforearm"), ("jnt14_1", "jnt13_1"), ("jnt14_2", "jnt13_2"),
         ("to_coatl", "to_coatr"), ("to_legL", "to_legR"), ("to_ballL", "to_ballR"), ("CONSlegL", "CONSlegR"),
         ("to_coatLBack", "to_coatRBack"), ("to_coatLFront", "to_coatRFront"), ("shoulderL1", "shoulderR1"),
         ("joint_Lhold", "joint_Rhold")]
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
    if m is not None and name not in L2R:
        m = (m + X @ m @ X) * 0.5
    TO_REST[name] = m
for name in ORDER:
    if TO_REST.get(name) is None and name not in R2L:
        p = PARENT[name]
        TO_REST[name] = TO_REST.get(p) if p else Matrix.Identity(4)
for r, l in R2L.items():
    TO_REST[r] = X @ TO_REST[l] @ X

# ---------------------------------------------------------------- armature in the body's rest pose
old = bpy.data.objects.get("Flunky_Rig")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
arm_data = bpy.data.armatures.new("Flunky_Rig")
arm = bpy.data.objects.new("Flunky_Rig", arm_data)
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
SUBSETS = {"torso": [], "arms": [], "legs": []}
for g in data["geoms"]:
    for p, w in zip(g["verts"], g["weights"]):
        if not w or p[0] < -0.3 or any(n in R2L for n in w):
            continue
        names = set(w)
        if g["name"] == "torso":
            kind = "torso"
        elif g["name"] == "legs" or any(n.startswith(("to_leg", "to_ball")) for n in names):
            kind = "legs"
        elif g["name"] == "hands" or any(n[1:3] == "h_" or n.endswith("upVct") for n in names):
            continue
        else:
            kind = "arms"
        SUBSETS[kind].append((Vector(p), w))


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


GARMENT_SOURCE = {"Flunky_Jacket": "torso", "Flunky_Vest": "torso", "Flunky_ShirtBody": "torso"}
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
    x = abs(co.x)                                               # shoulder joint 1.18, elbow joint 2.13, wrist 3.09
    # Checked against the game's poses: jnt23_1 stays on the shoulder, Luparm carries the upper arm (it lands the
    # elbow within 0.01 in every pose), jnt26_2 carries the forearm.
    if x <= 1.05:
        w = {"jnt23_1": 1.0}                                    # shoulder dome
    elif x < 1.32:
        w = two("Luparm", "jnt23_1", ramp(1.05, 1.32, x))
    elif x <= 2.02:
        w = {"Luparm": 1.0}
    elif x < 2.26:
        w = two("jnt26_2", "Luparm", ramp(2.02, 2.26, x))
    else:
        w = {"jnt26_2": 1.0}
    return mirror_names(w) if co.x < 0 else w


def leg_weights(co, side):
    """Thigh on the hip joint, shin on the knee joint, one blend across the knee (hip joint z 1.96, knee z 1.10)."""
    z = co.z
    w = {"jnt14_1": 1.0} if z >= 1.30 else (two("jnt14_1", "jnt14_2", ramp(0.95, 1.30, z)) if z >= 0.95 else {"jnt14_2": 1.0})
    return mirror_names(w) if side == 'R' else w


def trouser_weights(co):
    return leg_weights(co, 'L' if co.x >= 0 else 'R')


def seat_weights(co):
    """The seat is the pelvis (to_MAIN carries both hip joints exactly in every pose); only its underside, round
    the crotch, gives toward the two thighs."""
    t = ramp(1.15, 1.55, co.z)
    if t >= 0.996:
        return {"to_MAIN": 1.0}
    left = max(0.0, min(1.0, 0.5 + co.x / 0.5))
    w = {"to_MAIN": t, "jnt14_1": (1 - t) * left, "jnt13_1": (1 - t) * (1 - left)}
    return {k: v for k, v in w.items() if v > 0.004}


def shoe_weights(co):
    w = two("to_ballL", "to_legL", ramp(0.35, 0.60, -co.y))     # ankle joint, bending at the ball joint (y -0.45)
    return mirror_names(w) if co.x < 0 else w


REST_FN = {"Flunky_Sleeves": sleeve_weights, "Flunky_Trousers": trouser_weights, "Flunky_Seat": seat_weights, "Flunky_Shoes": shoe_weights,
           "Flunky_Soles": shoe_weights, "Flunky_SleeveButtons": sleeve_weights, "Flunky_SleeveStitching": sleeve_weights}
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
    for _ in range(3):
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
DIRECTIVE = {"@jacket": "Flunky_Jacket", "@vest": "Flunky_Vest", "@shirt": "Flunky_ShirtBody",
             "@sleeve": "Flunky_Sleeves", "@trousers": "Flunky_Trousers"}
OBJECT_GARMENT = {"Flunky_Lapels": "@jacket", "Flunky_Pockets": "@jacket", "Flunky_Collar": "@jacket", "Flunky_Seams": "@jacket",
                  "Flunky_Stitching": "@jacket", "Flunky_VestButtonStand": "@vest", "Flunky_Tie": "@shirt",
                  "Flunky_ShirtCollar": "@shirt", "Flunky_Shirt": "@shirt", "Flunky_Brass": "@vest", "Flunky_Joints": "@vest",
                  "Flunky_Plates": "@vest", "Flunky_HemLining": "@jacket"}


def from_garment(directive, co):
    if directive == "@sleeve":
        return sleeve_weights(co)
    if directive == "@trousers":
        return trouser_weights(co)
    name = DIRECTIVE[directive]
    pts, tree = garment_pts[name], GARMENT_TREE[name]
    acc = {}
    for _, idx, dist in tree.find_n(co, 3):
        f = 1.0 / (dist + 0.01) ** 2
        for n, wv in pts[idx][1].items():
            acc[n] = acc.get(n, 0.0) + wv * f
    return top3(acc)


unassigned = []
for ob in meshes:
    if ob.name in GARMENT_SOURCE or ob.get("rest_space"):
        continue
    for i, v in enumerate(ob.data.vertices):
        w = W[ob.name][i]
        if w is None or (isinstance(w, str)):
            directive = w if isinstance(w, str) else OBJECT_GARMENT.get(ob.name)
            if directive is None:
                unassigned.append(ob.name)
                directive = "@jacket"
            W[ob.name][i] = from_garment(directive, v.co)

# ---------------------------------------------------------------- carry every vertex to the rest pose, write groups, bind
for ob in meshes:
    ob.vertex_groups.clear()
    groups = {}
    for i, v in enumerate(ob.data.vertices):
        w = W[ob.name][i]
        p = Vector((0, 0, 0))
        for n, wv in w.items():
            p += (TO_REST[n] @ v.co) * wv
            if n not in groups:
                groups[n] = ob.vertex_groups.new(name=n)
            groups[n].add([i], wv, 'REPLACE')
        if not ob.get("rest_space"):              # limbs are already in the rest pose
            v.co = p
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
            m = scale_inv @ TO_REST[name].inverted() @ BIND[name]
        else:
            m = scale_inv @ frame[name]
        arm.pose.bones[name].matrix = bone_frame(m) if frame is not None else m
        bpy.context.view_layer.update()


apply_pose("sheet")
result = {"bones": len(arm.data.bones), "meshes": [o.name for o in result_objs],
          "verts": {o.name: len(o.data.vertices) for o in result_objs},
          "tris": sum(len(p.vertices) - 2 for o in result_objs for p in o.data.polygons),
          "max_weights_per_vertex": max_inf, "stale_group_refs": STALE[0], "objects_without_a_garment": sorted(set(unassigned)),
          "groups": {o.name: len(o.vertex_groups) for o in result_objs}}
