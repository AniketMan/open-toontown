"""Build the HD duck head (short head, short muzzle: head_duck_fss) in the toon Blender project.

Rule from the user (2026-11-15): take the size and shape from the ORIGINAL model, and do the feathers mainly as a
texture with only light modelling to suggest them. So every part here starts as the original mesh from
duck-heads-1000 (collection "duck_original", imported from work/duck_heads.json), keeps its place, size and UVs,
and is refined: subdivided smooth, its open edge pinned back onto the original edge so it still meets the flat eye
plate with no seam, and given a soft clumped surface. The feather look is the material (a strand texture and bump).
Reference: ~/Downloads/toon-hd/turnarounds/head_duck_fss_new-turnaround.png and its modeling breakdown.
Coordinates are the game's own for this head file: +y is the face, z up.
Run in Blender: exec(open(this file).read())."""
import bpy, bmesh, math
from mathutils import Vector, noise

REF = "/Users/aniketbhatt/Downloads/toon-hd/textures/head/"
sc = bpy.context.scene


def get_col(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("duck_hd")


def feather_mat(name, colour):
    """Feathers as a texture: fine strands running down the head, in colour and in relief."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    co = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (26.0, 26.0, 3.2)          # stretched along z: long thin strands
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 3.0
    n1.inputs["Detail"].default_value = 6.0
    n1.inputs["Roughness"].default_value = 0.62
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (colour[0] * 0.80, colour[1] * 0.80, colour[2] * 0.84, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (min(1, colour[0] * 1.12), min(1, colour[1] * 1.12), min(1, colour[2] * 1.10), 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(n1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.9
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def flat_mat(name, colour, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def tex_mat(name, path):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    t = nt.nodes.get("Image Texture") or nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


M_FEATHER = feather_mat("duck_feathers", (0.62, 0.62, 0.74))
M_BEAK = flat_mat("duck_beak", (1.0, 0.30, 0.015), rough=0.42)


def refine(src_name, new_name, mat, levels=2, clump=0.0, cap_z=None):
    """The original part, subdivided smooth, with its open edges pinned back where they were."""
    names = (src_name,) if isinstance(src_name, str) else tuple(src_name)
    srcs = [bpy.data.objects[n] for n in names]
    me = bpy.data.meshes.new(new_name)
    bm = bmesh.new()
    for s_ in srcs:                                                # several parts welded into ONE surface, so they smooth as one
        bm.from_mesh(s_.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002 if len(srcs) > 1 else 0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if cap_z is not None:                                          # the crest is built separately: press its spikes into the dome
        for v in bm.verts:
            if v.co.z > cap_z:
                v.co.z = cap_z + (v.co.z - cap_z) * 0.04
    edge_segs = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in bm.edges if e.is_boundary]   # the original open edges
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(new_name, me)
    col.objects.link(ob)
    mod = ob.modifiers.new("smooth", 'SUBSURF')
    mod.levels = levels
    mod.render_levels = levels
    mod.boundary_smooth = 'PRESERVE_CORNERS'
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = new
    bm = bmesh.new()
    bm.from_mesh(new)

    def onto_edge(p):
        best, bd = None, 1e9
        for a, b in edge_segs:
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
            q = a + ab * t
            d = (p - q).length
            if d < bd:
                best, bd = q, d
        return best

    if edge_segs:
        for v in bm.verts:
            if v.is_boundary:
                v.co = onto_edge(v.co)                                     # so it still meets its neighbours exactly: no seam
    # Smoothing a coarse mesh shrinks it (the duck's head lost 9% of its width). Bring it back to the ORIGINAL's exact
    # extents, axis by axis, easing off toward the pinned edges.
    allv = [v.co for s_ in srcs for v in s_.data.vertices]
    lo0 = Vector([min(c[i] for c in allv) for i in range(3)])
    hi0 = Vector([max(c[i] for c in allv) for i in range(3)])
    if cap_z is not None:
        hi0.z = cap_z + 0.02
    lo1 = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
    hi1 = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
    for v in bm.verts:
        if v.is_boundary:
            continue
        w = min(1.0, (v.co - onto_edge(v.co)).length / 0.18) if edge_segs else 1.0
        t = Vector([lo0[i] + (v.co[i] - lo1[i]) * (hi0[i] - lo0[i]) / max(hi1[i] - lo1[i], 1e-9) for i in range(3)])
        v.co = v.co.lerp(t, w)
    if clump:
        bm.normal_update()
        for v in bm.verts:
            if v.is_boundary:
                continue
            p = v.co
            k = noise.noise(Vector((p.x * 9.0, p.y * 9.0, p.z * 2.4)))     # long soft clumps running down the head
            v.co = p + v.normal * clump * k
    bm.to_mesh(new)
    bm.free()
    for poly in new.polygons:
        poly.use_smooth = True
    new.materials.clear()
    new.materials.append(mat)
    return ob


DOME_TOP = 1.06                                                 # the original dome under its crest (crest tips reach 1.46)
# The game splits the face off as a flat plate ("head-front") for the eye decal to sit on. Smoothed separately it stayed
# a flat box on a round head, so the plate is welded into the head here and the two are smoothed as one surface. The
# only edge left open is the one under the bill.
head = refine(("orig_head-short", "orig_head-front-short"), "head-short", M_FEATHER, levels=3, clump=0.012, cap_z=DOME_TOP)

# crest: sized from the original's (two tufts splayed in front, a longer spike leaning back, tips at z 1.46),
# shaped like the sheet's: flat tufts widening to a blunt slanted end, and a pointed spike
cr = bmesh.new()
for base, direction, length, width, flat, spike in (((-0.07, -0.02, DOME_TOP - 0.05), (-0.48, 0.06, 1.0), 0.40, 0.15, 0.22, False),
                                                    ((0.08, -0.02, DOME_TOP - 0.05), (0.52, 0.06, 1.0), 0.43, 0.155, 0.22, False),
                                                    ((0.0, -0.16, DOME_TOP - 0.06), (0.0, -0.62, 1.0), 0.53, 0.13, 0.5, True)):
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 1, 0)))
    side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    fw = side.cross(d).normalized()
    rings = []
    for i in range(9):
        t = i / 8
        w = width * ((0.95 - 0.8 * t) if spike else (0.5 + 0.7 * t))
        c = Vector(base) + d * length * t + fw * (-0.10 * length * t * t)
        ring = []
        for q in (2 * math.pi * k / 14 for k in range(14)):
            sx_, sy_ = math.copysign(abs(math.cos(q)) ** 0.6, math.cos(q)), math.sin(q)
            ring.append(cr.verts.new(c + side * w * sx_ + fw * flat * w * sy_ + d * ((0.0 if spike else 0.10 * length) * sx_ * t * t)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(14):
            cr.faces.new((a[k], a[(k + 1) % 14], b[(k + 1) % 14], b[k]))
    if spike:
        tip = cr.verts.new(Vector(base) + d * length * 1.05 + fw * (-0.11 * length))
        for k in range(14):
            cr.faces.new((rings[-1][k], rings[-1][(k + 1) % 14], tip))
    else:
        cr.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(cr, faces=cr.faces[:])
cme = bpy.data.meshes.new("head-short-crest")
cr.to_mesh(cme)
cr.free()
for poly in cme.polygons:
    poly.use_smooth = True
cme.materials.append(M_FEATHER)
crest = bpy.data.objects.new("head-short-crest", cme)
col.objects.link(crest)
_s = crest.modifiers.new("smooth", 'SUBSURF')
_s.levels = _s.render_levels = 1
# ---- bill: built by hand to the sheet, inside the ORIGINAL bill's box --------------------------------------------
# Sheet reading: a thick soft upper bill with a rolled lip, rising to a peak against the face between the eyes,
# broad rounded front, slightly upturned tip; a thinner lower bill tucked under it; a wavy mouth line (dips in the
# middle, lifts either side, drops at the corners). The back half is a crescent wrapped round the head (hidden inside it).
OB = bpy.data.objects["orig_muzzle-short-neutral"]
B_LO = Vector([min(v.co[i] for v in OB.data.vertices) for i in range(3)])
B_HI = Vector([max(v.co[i] for v in OB.data.vertices) for i in range(3)])


def lerp_tab(tab, y):
    for (y0, v0), (y1, v1) in zip(tab, tab[1:]):
        if y <= y1:
            t = max(0.0, (y - y0) / (y1 - y0))
            t = t * t * (3 - 2 * t)
            return v0 + (v1 - v0) * t
    return tab[-1][1]


def bill_w(y):                                                   # half width: cheeks at the back, broad rounded front
    if y < 0.2:
        return 0.50 + 0.065 * math.sin(math.pi / 2 * y / 0.2)
    t = min(1.0, (y - 0.2) / 0.686)
    return 0.565 * max(0.0, 1 - t ** 3.4) ** (1 / 3.4)


LIP = ((0.0, -0.185), (0.3, -0.20), (0.6, -0.19), (0.8, -0.165), (0.886, -0.145))     # mouth line height along the bill
TOP = ((0.0, 0.10), (0.46, 0.124), (0.6, 0.035), (0.72, -0.025), (0.82, -0.035), (0.886, -0.05))   # upper bill ridge
BOT = ((0.0, -0.345), (0.6, -0.363), (0.74, -0.345), (0.84, -0.30))                    # underside of the lower bill
NR = 20


def bill_half(bm_, upper):
    ys = [-0.012, 0.02, 0.07, 0.15, 0.24, 0.33, 0.42, 0.50, 0.57, 0.64, 0.70, 0.76, 0.81, 0.845, 0.868]
    if not upper:
        ys = [y for y in ys if y < 0.83] + [0.835]
    rings = []
    for y in ys:
        w = bill_w(y) * (1.0 if upper else 0.93)
        zl = lerp_tab(LIP, y) - (0.0 if upper else 0.014)
        up = (lerp_tab(TOP, y) - zl) if upper else 0.012
        dn = 0.04 if upper else (zl - lerp_tab(BOT, y))
        back = 0.62 if y < 0 else (0.9 if y < 0.05 else 1.0)       # rounded-off back corners where the bill leaves the head
        w, up, dn = w * back, up * back, dn * back
        fade = min(1.0, w / 0.4)
        up, dn = up * (0.8 + 0.2 * fade), dn * (0.8 + 0.2 * fade)           # stays thick to a blunt tip
        # against the face the upper bill is a narrow ridge rising between the eyes (so it does not cover them);
        # forward of the face it flattens into the broad bill
        peak = 1.0 - min(1.0, max(0.0, (y - 0.5) / 0.2))
        e_up = 0.85 + 1.25 * peak
        ring = []
        for k in range(NR):
            a = 2 * math.pi * k / NR
            c, sn = math.cos(a), math.sin(a)
            u = math.copysign(abs(c) ** 0.72, c)                 # squarish section: broad flat top, round rolled edge
            h = math.copysign(abs(sn) ** ((e_up if sn > 0 else 0.85) if upper else 0.8), sn)
            wave = (-0.022 * math.cos(math.pi * 1.5 * abs(u)) - 0.03 * abs(u) ** 4) * fade     # the wavy mouth line
            lipness = 1.0 if (h < 0) == upper else max(0.0, 1 - abs(h) * 1.6)
            z = zl + (up if h > 0 else dn) * h + wave * lipness
            ring.append(bm_.verts.new((w * u, y, z)))
        rings.append(ring)
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(NR):
            bm_.faces.new((a_[k], a_[(k + 1) % NR], b_[(k + 1) % NR], b_[k]))
    y_tip = 0.886 if upper else 0.85
    tip = bm_.verts.new((0, y_tip, lerp_tab(LIP, y_tip) + (0.03 if upper else -0.05)))
    for k in range(NR):
        bm_.faces.new((rings[-1][k], rings[-1][(k + 1) % NR], tip))
    y0 = ys[0]
    butt = bm_.verts.new((0, y0 - 0.012, lerp_tab(LIP, 0.0) + (0.03 if upper else -0.06)))
    for k in range(NR):
        bm_.faces.new((rings[0][(k + 1) % NR], rings[0][k], butt))


bb = bmesh.new()
bill_half(bb, True)
bill_half(bb, False)
bmesh.ops.recalc_face_normals(bb, faces=bb.faces[:])
bme = bpy.data.meshes.new("muzzle-short-neutral")
bb.to_mesh(bme)
bb.free()
beak = bpy.data.objects.new("muzzle-short-neutral", bme)
col.objects.link(beak)
_m = beak.modifiers.new("smooth", 'SUBSURF')
_m.levels = _m.render_levels = 2
_dg = bpy.context.evaluated_depsgraph_get()
_new = bpy.data.meshes.new_from_object(beak.evaluated_get(_dg))
beak.modifiers.clear()
beak.data = _new
_lo = Vector([min(v.co[i] for v in _new.vertices) for i in range(3)])
_hi = Vector([max(v.co[i] for v in _new.vertices) for i in range(3)])
for v in _new.vertices:                                          # exactly the original bill's box
    v.co = Vector([B_LO[i] + (v.co[i] - _lo[i]) * (B_HI[i] - B_LO[i]) / (_hi[i] - _lo[i]) for i in range(3)])
for poly in _new.polygons:
    poly.use_smooth = True
_new.materials.append(M_BEAK)

# ---- eyes and pupils: the game's own decals (same UVs), laid onto the round face instead of a flat plate ----------
from mathutils.bvhtree import BVHTree
_hb = bmesh.new()
_hb.from_mesh(head.data)
_bvh = BVHTree.FromBMesh(_hb)
for src_name, mat, lift in (("orig_eyes-short", tex_mat("toon_eyes", REF + "eyes.png"), 0.006),
                            ("orig_joint_pupilL_short", tex_mat("toon_pupils", REF + "pupils.png"), 0.012),
                            ("orig_joint_pupilR_short", tex_mat("toon_pupils", REF + "pupils.png"), 0.012)):
    s = bpy.data.objects[src_name]
    em = bmesh.new()
    em.from_mesh(s.data)
    bmesh.ops.subdivide_edges(em, edges=em.edges[:], cuts=7, use_grid_fill=True)
    bmesh.ops.triangulate(em, faces=[f for f in em.faces if len(f.verts) > 4])
    for v in em.verts:
        hit, nrm, _i, _d = _bvh.ray_cast(Vector((v.co.x, 3.0, v.co.z)), Vector((0, -1, 0)))
        if hit is None or hit.y < v.co.y - 0.25:                  # through the opening under the bill: take the nearest face point
            hit, nrm, _i, _d = _bvh.find_nearest(v.co)
        v.co = hit + nrm * lift
    me_ = bpy.data.meshes.new(src_name.replace("orig_", ""))
    em.to_mesh(me_)
    em.free()
    for poly in me_.polygons:
        poly.use_smooth = True
    me_.materials.append(mat)
    o = bpy.data.objects.new(src_name.replace("orig_", ""), me_)
    o.visible_shadow = False
    col.objects.link(o)
_hb.free()


orig = bpy.data.objects["orig_head-short"]
size = lambda o: [round(max(v.co[i] for v in o.data.vertices) - min(v.co[i] for v in o.data.vertices), 3) for i in range(3)]
result = {"objects": [o.name for o in col.objects], "tris": sum(len(o.data.polygons) for o in col.objects),
          "head size original (no plate)": size(orig), "head size hd (plate welded in)": size(head),
          "beak size original": size(bpy.data.objects["orig_muzzle-short-neutral"]), "beak size hd": size(beak)}
