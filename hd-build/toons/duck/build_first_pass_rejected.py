"""Build the HD duck head (short head, short muzzle: head_duck_fss) in the toon Blender project.
Reference: ~/Downloads/toon-hd/turnarounds/head_duck_fss_new-turnaround.png and its modeling breakdown, which name
the volumes: head mass, muzzle (beak), crest (two front tufts and a rear spike), and the flat eye decal.
Coordinates are the game's own for this head file: +y is the face, z up, units as in duck-heads-1000.
The original meshes are already in the collection "duck_original" (imported from work/duck_heads.json); their
bounds give the size: head x +-0.69, y -0.75..0.44, z -0.30..1.1 (crest to 1.46); muzzle x +-0.57, y -0.02..0.89,
z -0.36..0.12; eye decal x +-0.54, z -0.09..0.84 at y 0.32..0.60.
Run in Blender: exec(open(this file).read())."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

T = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/toon-hd-build/"
REF = "/Users/aniketbhatt/Downloads/toon-hd/textures/head/"
sc = bpy.context.scene
random.seed(7)


def get_col(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("duck_hd")


def flat_mat(name, colour, rough=0.85):
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
    b.inputs["Roughness"].default_value = 0.6
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


M_BODY = flat_mat("duck_feathers", (0.62, 0.62, 0.74))
M_BEAK = flat_mat("duck_beak", (1.0, 0.36, 0.02), 0.5)
M_LIP = flat_mat("duck_beak_lower", (0.86, 0.27, 0.015), 0.5)
M_MOUTH = flat_mat("duck_mouth_line", (0.35, 0.12, 0.02), 0.6)


def add(name, bm, mat, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


# ---------------------------------------------------------------- head mass: a round, slightly squashed ball
HC, HR = Vector((0.0, -0.17, 0.44)), Vector((0.80, 0.68, 0.74))
plate = bpy.data.objects["orig_head-front-short"].data
pbvh = BVHTree.FromPolygons([v.co for v in plate.vertices], [p.vertices for p in plate.polygons])


def head_pt(d):
    """Point on the head mass along unit direction d from its centre."""
    k = 1.0 + 0.06 * max(0.0, -d.z) + 0.03 * max(0.0, d.z)        # fuller cheeks low down, as on the sheet
    p = Vector((HC.x + d.x * HR.x * k, HC.y + d.y * HR.y * k, HC.z + d.z * HR.z))
    if d.y > -0.1:                                               # sit flush just behind the flat eye plate: no seam round it
        loc, nor, idx, dist = pbvh.find_nearest(p)
        dxz = math.hypot(p.x - loc.x, p.z - loc.z)
        w = max(0.0, 1.0 - dxz / 0.30)
        w = w * w * (3 - 2 * w)
        p.y += (loc.y - 0.006 - p.y) * w
    return p


bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=36, radius=1.0)
for v in bm.verts:
    v.co = head_pt(v.co.normalized())
add("head-short", bm, M_BODY)


# ---------------------------------------------------------------- feathers: soft overlapping tufts
def leaf(bm, base, along, normal, length, width, lift, curl=0.25, seg=5):
    """A feather tuft: a tapered, slightly cupped blade lying along the surface and lifting at its tip."""
    along, normal = Vector(along).normalized(), Vector(normal).normalized()
    side = along.cross(normal).normalized()
    rows = []
    for i in range(seg + 1):
        t = i / seg
        w = width * math.sin(math.pi * (0.12 + 0.88 * (1 - t))) * (1 - 0.35 * t)
        c = Vector(base) + along * length * t + normal * (lift * t * t + 0.004)
        rows.append([c - side * w + normal * (curl * w * 0.5), c + normal * (-curl * w * 0.2), c + side * w + normal * (curl * w * 0.5)])
    vs = [[bm.verts.new(p) for p in r] for r in rows]
    for a, b in zip(vs, vs[1:]):
        for k in range(2):
            bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))


fe = bmesh.new()
N = 5200
for i in range(N):                                               # an even spiral of tufts over the head, pointing down and back
    z = 1 - 2 * (i + 0.5) / N
    r = math.sqrt(max(0.0, 1 - z * z))
    a = i * math.pi * (3 - math.sqrt(5))
    d = Vector((r * math.cos(a), r * math.sin(a), z))
    p = head_pt(d)
    if d.y > 0.25 and abs(p.x) < 0.62 and -0.15 < p.z < 0.9:     # keep the face clear, where the eyes are drawn
        continue
    if d.z < -0.72:                                              # the underside sits on the neck
        continue
    n = Vector((d.x / HR.x, d.y / HR.y, d.z / HR.z)).normalized()
    flow = (Vector((0, -0.55, -1.0)) - n * Vector((0, -0.55, -1.0)).dot(n))
    if flow.length < 0.2:
        flow = Vector((0, -1, 0)) - n * Vector((0, -1, 0)).dot(n)
    flow.normalize()
    flow = (flow + Vector((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), random.uniform(-0.15, 0.15)))).normalized()
    leaf(fe, p, flow, n, random.uniform(0.06, 0.10), random.uniform(0.006, 0.011), random.uniform(0.004, 0.012), seg=2)       # fine, soft, like fur
add("head-short-feathers", fe, M_BODY)

# ---------------------------------------------------------------- crest: two tufts in front, a longer spike behind
cr = bmesh.new()
top = head_pt(Vector((0, -0.1, 1)).normalized())
for base_off, direction, length, width, flat in (((-0.12, 0.06, -0.05), (-0.50, 0.0, 1.0), 0.40, 0.125, 0.24),      # two broad flat paddles in front,
                                                 ((0.13, 0.06, -0.05), (0.55, 0.0, 1.0), 0.44, 0.13, 0.24),       # splayed in a V
                                                 ((0.0, -0.14, -0.04), (0.0, -0.62, 1.0), 0.58, 0.12, 0.45)):      # and a spike leaning back
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 1, 0)))
    side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    fw = side.cross(d).normalized()
    spike = flat > 0.4
    rings = []
    for i in range(9):
        t = i / 8
        if spike:
            w = width * (0.9 - 0.75 * t) * (0.6 + 0.4 * math.sin(math.pi * min(1.0, 0.15 + t)))
        else:
            w = width * (0.42 + 0.72 * t)                           # widening toward the tip, like the sheet's tufts
        slant = (0.0 if spike else 0.10 * length)                   # the blunt end is cut on a slant
        c = top + Vector(base_off) + d * length * t + fw * (-0.10 * length * t * t)
        ring = []
        for q in (2 * math.pi * k / 14 for k in range(14)):
            sx_, sy_ = math.copysign(abs(math.cos(q)) ** 0.6, math.cos(q)), math.sin(q)      # squarish in section: flat faces, soft edges
            ring.append(cr.verts.new(c + side * w * sx_ + fw * flat * w * 0.55 * sy_ + d * (slant * sx_ * t * t)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(14):
            cr.faces.new((a[k], a[(k + 1) % 14], b[(k + 1) % 14], b[k]))
    if spike:
        tip = cr.verts.new(top + Vector(base_off) + d * length * 1.05 + fw * (-0.11 * length))
        for k in range(14):
            cr.faces.new((rings[-1][k], rings[-1][(k + 1) % 14], tip))
    else:
        cr.faces.new(rings[-1])
add("head-short-crest", cr, M_BODY)


# ---------------------------------------------------------------- beak: a short, wide, soft bill and a lower lip
def bill(bm, stations, top_dome, bottom_dome, seg=24, bow=0.0, droop=0.0):
    """stations: (y, half-width, z of the widest line, half-thickness). A rounded slab swept along y."""
    rings = []
    for y, hw, zc, ht in stations:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            cx, sz = math.cos(a), math.sin(a)
            x = hw * math.copysign(abs(cx) ** 0.7, cx)
            z = zc + ht * (top_dome if sz > 0 else bottom_dome) * math.copysign(abs(sz) ** 0.9, sz)
            e = (abs(x) / max(hw, 1e-6)) ** 2
            z -= droop * e                                               # the corners of the bill hang down
            if sz > 0:                                                   # a soft bow in the middle of the upper edge, fading toward the tip
                z += bow * math.exp(-(x / 0.17) ** 2) * max(0.0, 1.0 - y / 0.5)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))


bk = bmesh.new()                                                 # upper bill: thick, soft and nearly as wide as the head, short
bill(bk, [(0.05, 0.54, 0.0, 0.20), (0.22, 0.64, -0.03, 0.21), (0.42, 0.68, -0.07, 0.195), (0.58, 0.64, -0.10, 0.165),
          (0.69, 0.53, -0.12, 0.13), (0.76, 0.36, -0.13, 0.09), (0.79, 0.16, -0.135, 0.05)], 1.0, 0.5, bow=0.085, droop=0.06)
add("muzzle-short-neutral-upper", bk, M_BEAK)
bl = bmesh.new()                                                 # lower lip: thinner, tucked under, a little shorter
bill(bl, [(0.03, 0.50, -0.17, 0.11), (0.22, 0.58, -0.185, 0.11), (0.42, 0.60, -0.20, 0.10), (0.56, 0.54, -0.21, 0.085),
          (0.66, 0.41, -0.215, 0.062), (0.71, 0.22, -0.218, 0.035)], 0.3, 1.0, droop=0.07)
add("muzzle-short-neutral-lower", bl, M_LIP)

# ---------------------------------------------------------------- the flat eye decals, as the game draws them
for src_name, tex in (("orig_eyes-short", "eyes.png"), ("orig_joint_pupilL_short", "pupils.png"), ("orig_joint_pupilR_short", "pupils.png")):
    s = bpy.data.objects[src_name]
    o = s.copy()
    o.data = s.data.copy()
    o.name = src_name.replace("orig_", "")
    o.data.materials.clear()
    o.data.materials.append(tex_mat("toon_" + tex, REF + tex))
    o.location.y += 0.004 if "pupil" in src_name else 0.0
    o.hide_render = False
    o.visible_shadow = False
    col.objects.link(o)

result = {"objects": [o.name for o in col.objects], "tris": sum(len(o.data.polygons) for o in col.objects)}
