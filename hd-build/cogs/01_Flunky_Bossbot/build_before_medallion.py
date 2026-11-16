"""Build the HD Flunky (Bossbot) in Blender.
Shapes are measured off the concept sheet (404 px = 4.9 game units); scale and depth over the feet
are taken from the original low-poly model (same pose, wider build). Z up, character faces -Y, feet at z = 0."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/01_Flunky_Bossbot/"
PX = 404 / 4.9
H = math.pi / 2
YOFF = -0.10            # original model sits this much further forward over its feet than the sheet's bbox centre
STRIPE = 0.115          # pinstripe spacing
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'
if scene.world and scene.world.use_nodes and scene.world.node_tree.nodes.get('Background'):
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.6


def get_col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("Flunky")
refcol = get_col("Flunky_Reference")
root = bpy.data.objects.new("Flunky", None)
col.objects.link(root)
root.empty_display_size = 0.4


def ref(name, size, loc, rot, off):
    img = bpy.data.images.load(SP + "refplanes/flunky_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = size
    e.empty_image_offset = off
    e.location = loc
    e.rotation_euler = rot
    e.empty_image_side = 'FRONT'
    e.color[3] = 0.6
    e.use_empty_image_alpha = True
    e.hide_render = True


ref("front", 4.9, (0, 3, 0), (H, 0, 0), (-0.5, 0))
ref("back", 4.9, (0, -3, 0), (H, 0, math.pi), (-0.5, 0))
ref("left", 4.9, (-3, YOFF, 0), (H, 0, H), (-0.5, 0))
ref("right", 4.9, (3, YOFF, 0), (H, 0, -H), (-0.5, 0))
ref("top", 268 / PX, (0, YOFF, -0.02), (0, 0, 0), (-0.5, -0.5))


# ---------------------------------------------------------------- materials
def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*color, 1)
    return m


SUIT_BASE = (0.10, 0.02, 0.016)
SUIT_STRIPE = (0.24, 0.10, 0.08)


def pmat(name, base, rough=0.5, metal=0.0, *, var=0.15, grime=0.0, grime_col=(0.035, 0.022, 0.015), bump=0.0,
         bscale=80.0, rvar=0.1, nscale=5.0, coat=0.0, sheen=0.0, stripe=None, weave=0.0, wear=0.0):
    """Procedural surface: colour variation, grime gathered in crevices, uneven roughness, fine bump.
    stripe = pinstripe colour (read from UVs); weave = woven-cloth bump; wear = lighter scuffs."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    bsdf.inputs["Sheen Weight"].default_value = sheen
    tc = N.new("ShaderNodeTexCoord")

    def noise(scale, detail=4.0, rough=0.55):
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        L.new(tc.outputs["Object"], n.inputs["Vector"])
        return n

    def math(op, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def mix(blend, fac, a, b):
        n = N.new("ShaderNodeMix")
        n.data_type = 'RGBA'
        n.blend_type = blend
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v, 1)
            else:
                L.new(v, sock)
        return n.outputs[2]

    col = base
    if stripe:                                    # pinstripes: u counts stripes around every sleeve and leg
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(tc.outputs["UV"], sep.inputs[0])
        cr = N.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].position = 0.86
        cr.color_ramp.elements[0].color = (*base, 1)
        cr.color_ramp.elements[1].position = 0.93
        cr.color_ramp.elements[1].color = (*stripe, 1)
        L.new(math('FRACT', sep.outputs["X"]), cr.inputs["Fac"])
        col = cr.outputs["Color"]
    big = noise(nscale)
    col = mix('MULTIPLY', math('MULTIPLY', big.outputs["Fac"], var), col, (0.45, 0.42, 0.40))     # blotchy tone variation
    if wear:                                      # sparse lighter scuffs
        sc = noise(nscale * 7, 6.0, 0.7)
        col = mix('MIX', math('MULTIPLY', math('GREATER_THAN', sc.outputs["Fac"], 0.66), wear), col,
                  tuple(min(1.0, c * 1.5 + 0.05) for c in base))
    if grime:                                     # dirt gathers where surfaces meet: seams, joints, under plates
        ao = N.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = 0.14
        occ = math('SUBTRACT', 1.0, ao.outputs["AO"], clamp=True)
        streak = noise(nscale * 3, 5.0)
        fac = math('MULTIPLY', math('MULTIPLY', occ, grime * 2.2, clamp=True), math('ADD', streak.outputs["Fac"], 0.35), clamp=True)
        col = mix('MIX', fac, col, grime_col)
    if isinstance(col, tuple):
        bsdf.inputs["Base Color"].default_value = (*col, 1)
    else:
        L.new(col, bsdf.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.02, rough - rvar)
    mr.inputs["To Max"].default_value = min(1.0, rough + rvar)
    L.new(noise(nscale * 4, 5.0).outputs["Fac"], mr.inputs["Value"])
    L.new(mr.outputs[0], bsdf.inputs["Roughness"])
    height = None
    if weave:                                     # cloth: two crossed fine wave sets make a twill-like weave
        w1, w2 = N.new("ShaderNodeTexWave"), N.new("ShaderNodeTexWave")
        for w, d in ((w1, 'X'), (w2, 'Z')):
            w.bands_direction = d
            w.inputs["Scale"].default_value = 90.0
            w.inputs["Distortion"].default_value = 1.5
            L.new(tc.outputs["Object"], w.inputs["Vector"])
        height = math('MULTIPLY', math('ADD', w1.outputs["Fac"], w2.outputs["Fac"]), weave)
    if bump:
        nb = math('MULTIPLY', noise(bscale, 3.0).outputs["Fac"], bump)
        height = nb if height is None else math('ADD', height, nb)
    if height is not None:
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = 0.35
        bp.inputs["Distance"].default_value = 0.02
        L.new(height, bp.inputs["Height"])
        L.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    m.diffuse_color = (*base, 1)
    m.metallic = metal
    m.roughness = rough
    return m


M_SUIT = pmat("Flunky_Suit", SUIT_BASE, 0.88, var=0.35, grime=0.12, stripe=SUIT_STRIPE, weave=0.5, bump=0.25,
              bscale=160, sheen=0.04, rvar=0.06)                                           # pinstripe wool
M_STITCH = pmat("Flunky_Stitch", (0.40, 0.21, 0.17), 0.85, var=0.2)
M_VEST = pmat("Flunky_Vest", (0.048, 0.008, 0.007), 0.8, var=0.3, grime=0.15, stripe=(0.095, 0.03, 0.025), weave=0.5,
              bump=0.2, bscale=160, sheen=0.03, rvar=0.06)                                   # darker, quieter cloth
M_PLATE = pmat("Flunky_Plate", (0.56, 0.42, 0.33), 0.45, 0.15, var=0.3, grime=0.55, wear=0.1, bump=0.12,
               bscale=45, rvar=0.16)                                                       # worn painted plating
M_JOINT = pmat("Flunky_Joint", (0.10, 0.075, 0.055), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_DARK = pmat("Flunky_DarkMetal", (0.03, 0.028, 0.028), 0.35, 0.7, var=0.3, wear=0.2, rvar=0.15)
M_BLACK = mat("Flunky_Black", (0.004, 0.004, 0.004), 0.9)
M_SHOE = pmat("Flunky_Shoe", (0.016, 0.011, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14,
              coat=0.5, wear=0.12)                                                         # polished, creased leather
M_SOLE = pmat("Flunky_Sole", (0.018, 0.015, 0.013), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_LENS = pmat("Flunky_Lens", (0.04, 0.40, 0.43), 0.06, var=0.1, rvar=0.03, coat=1.0)        # glass
M_BRASS = pmat("Flunky_Brass", (0.45, 0.35, 0.24), 0.36, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("Flunky_Shirt", (0.75, 0.72, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("Flunky_Tie", (0.115, 0.012, 0.015), 0.5, var=0.25, grime=0.15, weave=0.6, sheen=0.5, rvar=0.1)
M_WHITE = mat("Flunky_Highlight", (0.9, 0.9, 0.9), 0.3)


# ---------------------------------------------------------------- helpers
BONES = []                     # bone names used by tag(); vertex layer "bone" stores index + 1 (-1 = skin from the original)


def tag(bm, bone):
    """Everything added to bm since the last tag follows this bone rigidly. A name starting with '@' is a garment
    ('@jacket', '@vest', '@shirt', '@sleeve', '@trousers'): the piece is sewn to it and takes that garment's weights."""
    layer = bm.verts.layers.int.get("bone") or bm.verts.layers.int.new("bone")
    if bone is None:
        value = -1
    else:
        if bone not in BONES:
            BONES.append(bone)
        value = BONES.index(bone) + 1
    for v in bm.verts:
        if v[layer] == 0:
            v[layer] = value


def new_obj(name, bm, material, angle=40, outward=False, thickness=0.0, rest=False):
    """outward: open cloth panels get normals facing away from the body axis.
    thickness: cloth thickness via a Solidify modifier (+ = grows outward, - = grows inward)."""
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if outward == 'up':
        for f in bm.faces:               # a saddle over the shoulder: up on top, out at the front and back
            c = f.calc_center_median()
            if f.normal.y * (c.y - 0.15) + f.normal.z * 0.5 < 0:
                f.normal_flip()
    elif outward:
        for f in bm.faces:
            c = f.calc_center_median()
            if f.normal.x * c.x + f.normal.y * c.y < 0:
                f.normal_flip()
    layer = bm.verts.layers.int.get("bone")
    tags = [v[layer] for v in bm.verts] if layer else []
    bm.to_mesh(me)
    bm.free()
    if not rest:                         # rest=True: already in the skeleton's rest pose, native size
        me.transform(Matrix.Translation((0, YOFF, 0)))
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    try:
        me.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.parent = root
    ob["rest_space"] = bool(rest)
    for value in sorted(set(t for t in tags if t > 0)):
        vg = ob.vertex_groups.new(name=BONES[value - 1])
        vg.add([i for i, t in enumerate(tags) if t == value], 1.0, 'REPLACE')
    if thickness:
        sol = ob.modifiers.new("Cloth thickness", 'SOLIDIFY')
        sol.thickness = abs(thickness)
        sol.offset = 1.0 if thickness > 0 else -1.0
        if abs(thickness) >= 0.02:
            bv = ob.modifiers.new("Edge", 'BEVEL')      # crisp turned edge on cloth and plates
            bv.width = min(0.006, abs(thickness) * 0.3)
            bv.segments = 1
            bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(55)
    return ob


class Girth:
    """Arc length around an ellipse, so pinstripes stay evenly spaced and parallel like cut cloth."""

    def __init__(self, rx, ry, n=120):
        self.n, self.tab = n, [0.0]
        p = Vector((rx, 0.0))
        for i in range(1, n + 1):
            a = 2 * math.pi * i / n
            q = Vector((rx * math.cos(a), ry * math.sin(a)))
            self.tab.append(self.tab[-1] + (q - p).length)
            p = q

    def at(self, deg):
        t = deg / 360.0
        whole = math.floor(t)
        f = (t - whole) * self.n
        i = min(int(f), self.n - 1)
        return whole * self.tab[-1] + self.tab[i] + (self.tab[i + 1] - self.tab[i]) * (f - i)


SHAPE = {}                     # id(rings) -> superellipse power (2 = ellipse, higher = squarer outline)


def sq(c, power):
    return math.copysign(abs(c) ** (2.0 / power), c)


def loft(bm, rings, seg=16, sx=1, caps=(True, True), centres=None, power=2.0):
    """rings: (z, cx, cy, rx, ry) horizontal ellipses, as measured on the sheet.
    centres: angles (deg) of the cloth panels' centre lines; stripes run parallel to them and are cut
    at the seams between panels (270 = centre front, 90 = centre back, 0 = outside of a sleeve)."""
    vs = [[bm.verts.new((sx * (cx + rx * sq(math.cos(2 * math.pi * k / seg), power)),
                         cy + ry * sq(math.sin(2 * math.pi * k / seg), power), z))
           for k in range(seg)] for z, cx, cy, rx, ry in rings]
    uv = bm.loops.layers.uv.verify()
    girth = [Girth(r[3], r[4]) for r in rings] if centres else None
    step = 360.0 / seg
    for i, (a, b) in enumerate(zip(vs, vs[1:])):
        for k in range(seg):
            f = bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
            if not centres:
                for loop in f.loops:
                    loop[uv].uv = (0.5, 0.0)
                continue
            mid = (k + 0.5) * step
            c = min(centres, key=lambda c: abs((mid - c + 180) % 360 - 180))
            mid_u = c + ((mid - c + 180) % 360 - 180)
            for loop, (kk, r) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                ang = mid_u + (kk - k - 0.5) * step
                loop[uv].uv = ((girth[r].at(ang) - girth[r].at(c)) / STRIPE + 0.5, rings[r][0])
    for flag, ring in zip(caps, (vs[0], vs[-1])):
        if flag:
            f = bm.faces.new(ring)
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.0)


def shell(bm, rings, gap, parts=(6, 16, 6)):
    """Open-fronted garment: like loft, but with a gap of half-width gap(z) down the centre front.
    Panels: right front, back, left front, with side seams at 0 and 180 degrees."""
    uv = bm.loops.layers.uv.verify()
    rows, angs = [], []
    for z, cx, cy, rx, ry in rings:
        a0 = -math.degrees(math.acos(min(0.995, gap(z) / rx)))
        a = [a0 + (0 - a0) * i / parts[0] for i in range(parts[0])]
        a += [180.0 * i / parts[1] for i in range(parts[1])]
        a += [180 + (-a0) * i / parts[2] for i in range(parts[2] + 1)]
        angs.append(a)
        rows.append([bm.verts.new((cx + rx * math.cos(math.radians(t)), cy + ry * math.sin(math.radians(t)), z)) for t in a])
    girth = [Girth(r[3], r[4]) for r in rings]
    for i in range(len(rings) - 1):
        for j in range(len(rows[i]) - 1):
            c = -90.0 if j < parts[0] else (90.0 if j < parts[0] + parts[1] else 270.0)
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            for loop, (jj, r) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                loop[uv].uv = ((girth[r].at(angs[r][jj]) - girth[r].at(c)) / STRIPE + 0.5, rings[r][0])
    return rows


def arc_band(bm, sections, a0, a1, n, zfun=None):
    """Band swept part-way round the body (a collar): sections are rings giving its cross profile."""
    uv = bm.loops.layers.uv.verify()
    rows = []
    for si, (z, cx, cy, rx, ry) in enumerate(sections):
        row = []
        for i in range(n + 1):
            t = math.radians(a0 + (a1 - a0) * i / n)
            dz = zfun(si, math.sin(t)) if zfun else 0.0
            row.append(bm.verts.new((cx + rx * math.cos(t), cy + ry * math.sin(t), z + dz)))
        rows.append(row)
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        for j in range(n):
            f = bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
            for loop, (jj, r) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                loop[uv].uv = (r * 1.4, 0.0)        # stripes run round the collar


def tube(bm, pts, radii, seg=6, caps=True):
    """Round section swept along pts (rings perpendicular to the path). Also used as a lathe."""
    pts = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.cross(Vector((0, 1, 0)))
        if u.length < 1e-3:
            u = d.cross(Vector((1, 0, 0)))
        u.normalize()
        v = d.cross(u).normalized()
        rings.append([bm.verts.new(p + radii[i] * (math.cos(a) * u + math.sin(a) * v))
                      for a in (2 * math.pi * k / seg for k in range(seg))])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])


def lathe(bm, origin, axis, profile, seg=16, caps=True):
    """profile: (distance along axis, radius)."""
    origin, axis = Vector(origin), Vector(axis).normalized()
    u = axis.cross(Vector((0, 1, 0)))
    if u.length < 1e-3:
        u = axis.cross(Vector((1, 0, 0)))
    u.normalize()
    v = axis.cross(u).normalized()
    rings = [[bm.verts.new(origin + axis * d + r * (math.cos(a) * u + math.sin(a) * v))
              for a in (2 * math.pi * k / seg for k in range(seg))] for d, r in profile]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])


def puck(bm, pos, normal, radius, depth, seg=8):
    """Small flat cylinder sitting on a surface: rivets, buttons, discs."""
    m = Matrix.Translation(Vector(pos)) @ Vector(normal).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=depth, matrix=m)


def basis(origin, x, y, z):
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def rbox(bm, m, size, bev=0.02, seg=1):
    """Chamfered hard-surface block; m places a unit frame, size is its local extent."""
    t = bmesh.new()
    bmesh.ops.create_cube(t, size=1.0)
    for v in t.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bev > 0:
        bmesh.ops.bevel(t, geom=list(t.edges), offset=bev, segments=seg, profile=0.5, affect='EDGES')
    bmesh.ops.transform(t, matrix=m, verts=t.verts)
    me = bpy.data.meshes.new("tmp")
    t.to_mesh(me)
    t.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def seg_box(bm, m, a, b, xref, thick, width, bev, seg=1, gap=0.012):
    """Plate running from a to b (in the frame m), e.g. one finger bone."""
    a, b = Vector(a), Vector(b)
    z = (b - a).normalized()
    y = z.cross(Vector(xref)).normalized()
    x = y.cross(z).normalized()
    rbox(bm, m @ basis((a + b) / 2, x, y, z), (thick, width, (b - a).length - 2 * gap), bev, seg)


def interp(rings, z):
    for a, b in zip(rings, rings[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * t for i in range(5)]
    return rings[-1] if z > rings[-1][0] else rings[0]


def surf(rings, x, z, eps=0.0, back=False):
    """Point on the front (or back) of a loft at (x, z), pushed out along the surface normal by eps."""
    _, cx, cy, rx, ry = interp(rings, z)
    x = max(-0.97 * rx, min(0.97 * rx, x))
    sgn = 1.0 if back else -1.0
    p = SHAPE.get(id(rings), 2.0)
    yy = ry * (1 - abs(x / rx) ** p) ** (1.0 / p)
    n = Vector((math.copysign(abs(x / rx) ** (p - 1), x) / rx, sgn * (yy / ry) ** (p - 1) / ry, 0)).normalized()
    return Vector((x, cy + sgn * yy, z)) + n * eps


def ring_pt(rings, z, ang, eps=0.0):
    """Point on a loft at height z and angle ang (0 = +x, 90 = back), with its outward normal."""
    _, cx, cy, rx, ry = interp(rings, z)
    a = math.radians(ang)
    p = SHAPE.get(id(rings), 2.0)
    c, sn = math.cos(a), math.sin(a)
    e = 2.0 * (p - 1) / p
    n = Vector((math.copysign(abs(c) ** e, c) / rx, math.copysign(abs(sn) ** e, sn) / ry, 0)).normalized()
    return Vector((cx + rx * sq(c, p), cy + ry * sq(sn, p), z)) + n * eps, n


def patch(bm, rings, rows, eps, nx=6, eps_out=None, back=False):
    """Cloth panel lying on a loft. rows: (x_inner, x_outer, z). eps lifts it off the surface;
    eps_out, if given, is the lift at the outer edge (a lapel rolls: high at the fold, flat at the edge)."""
    eo = eps if eps_out is None else eps_out
    g = [[bm.verts.new(surf(rings, xl + (xr - xl) * i / nx, z, eps + (eo - eps) * i / nx, back)) for i in range(nx + 1)]
         for xl, xr, z in rows]
    uv = bm.loops.layers.uv.verify()
    for a, b in zip(g, g[1:]):
        for i in range(nx):
            f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co.x / STRIPE + 0.5, loop.vert.co.z)


def inset_outline(outline, d):
    """Offset a closed (x, z) outline inward by d: where a row of topstitching runs."""
    n = len(outline)
    area = sum(outline[i][0] * outline[(i + 1) % n][1] - outline[(i + 1) % n][0] * outline[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(outline[i - 1]), Vector(outline[i]), Vector(outline[(i + 1) % n])
        e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n1, n2 = Vector((-e1.y, e1.x)) * sgn, Vector((-e2.y, e2.x)) * sgn
        b = (n1 + n2)
        if b.length < 1e-6:
            b = n1
        b.normalize()
        out.append(tuple(p1 + b * d / max(0.35, b.dot(n1))))
    return out


def panel(bm, rings, outline, lift, back=False, cuts=3, grain=None):
    """A cut piece of cloth with an exact outline, laid on a loft. outline: (x, z) points round the piece.
    lift(x, z): height off the surface. grain: (dx, dz) direction the pinstripes run on this piece."""
    t = bmesh.new()
    f = t.faces.new([t.verts.new((x, 0.0, z)) for x, z in outline])
    bmesh.ops.triangulate(t, faces=[f])
    bmesh.ops.subdivide_edges(t, edges=list(t.edges), cuts=cuts, use_grid_fill=True)
    uv = t.loops.layers.uv.verify()
    g = Vector(grain).normalized() if grain else Vector((0.0, 1.0))
    for face in t.faces:
        for loop in face.loops:
            c = loop.vert.co
            loop[uv].uv = ((c.x * g.y - c.z * g.x) / STRIPE + 0.5, c.z)
    for v in t.verts:
        v.co = surf(rings, v.co.x, v.co.z, lift(v.co.x, v.co.z), back)
    me = bpy.data.meshes.new("tmp")
    t.to_mesh(me)
    t.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def topstitch(bm, rings, outline, lift, inset=0.028, back=False, closed=True, step=0.06):
    """A row of stitching just inside a piece's edge, sitting on its outer face."""
    pts = inset_outline(outline, inset) if inset else list(outline)
    if closed:
        pts = pts + pts[:1]
    path = []
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        k = max(1, int((b - a).length / step))
        path += [a + (b - a) * i / k for i in range(k)]
    path.append(Vector(pts[-1]))
    tube(bm, [surf(rings, p.x, p.y, lift(p.x, p.y), back) for p in path], [0.0075] * len(path), seg=4)


def fb(z, half_w, front, back):
    """ring from a measured half-width (front view) and front/back depth (side view)"""
    return (z, 0.0, (front + back) / 2, half_w, (back - front) / 2)


plate, joint, dark, black, brass = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

# ---------------------------------------------------------------- jacket
TORSO = [fb(1.76, 1.00, -1.04, 1.03), fb(1.74, 1.13, -1.19, 1.18), fb(2.00, 1.13, -1.19, 1.18),
         fb(2.50, 1.11, -1.13, 1.14), fb(2.90, 1.09, -1.03, 1.08), fb(3.20, 1.07, -0.97, 1.01),
         fb(3.46, 1.00, -0.79, 0.92), fb(3.63, 0.92, -0.72, 0.82), fb(3.75, 0.72, -0.60, 0.74),
         fb(3.83, 0.56, -0.47, 0.64), fb(3.79, 0.34, -0.30, 0.40)]   # last ring = recessed neck opening
TS = TORSO[1:-1]                         # jacket surface, hem (1.74) to neckline (3.83)
BREAK = 2.95                             # where the lapels start folding back (just under the medallion)
VEST_V = 3.40                            # bottom of the vest's V neck


def front_gap(z):
    """Half-width of the open jacket front: the vest shows between the fronts below the break, and the
    roll lines of the lapels spread into a V above it (measured: 0.21 at z 3.5, 0.34 at the neckline)."""
    return 0.16 if z <= BREAK else 0.16 + 0.20 * ((z - BREAK) / (3.83 - BREAK)) ** 1.6


def vest_gap(z):
    """The vest is closed down the front and opens into a V neck above its top button."""
    return 0.003 if z <= VEST_V else 0.003 + (z - VEST_V) / (3.75 - VEST_V) * 0.25


# Layer 0: shirt. A closed white body under everything, up to the base of the neck.
SHIRT_IN = {2.90: 0.075, 3.20: 0.075, 3.46: 0.08, 3.63: 0.10, 3.75: 0.15}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
bm = bmesh.new()
loft(bm, SS + [fb(3.79, 0.42, -0.42, 0.46), fb(3.81, 0.30, -0.28, 0.34)], seg=28)
new_obj("Flunky_ShirtBody", bm, M_SHIRT)

# Layer 1: vest. Its own garment over the shirt: closed front with the buttons, V neck, open at the top.
INSET = {1.74: 0.035, 2.00: 0.035, 2.50: 0.035, 2.90: 0.035, 3.20: 0.035, 3.46: 0.04, 3.63: 0.06, 3.75: 0.10}
VS = [(z, cx, cy, rx - INSET[z], ry - INSET[z]) for z, cx, cy, rx, ry in TS if z in INSET]
bm = bmesh.new()
shell(bm, VS, vest_gap)
new_obj("Flunky_Vest", bm, M_VEST, outward=True, thickness=-0.02)

# Layer 2: jacket body, an open-fronted shell with real cloth thickness; hem and neckline are open.
bm = bmesh.new()
shell(bm, TS, front_gap)
for v in bm.verts:                       # neckline dips at the front
    if v.co.z > 3.76 and v.co.y < 0:
        v.co.z -= 0.07 * min(1.0, -v.co.y / 0.45)
new_obj("Flunky_Jacket", bm, M_SUIT, outward=True, thickness=-0.045)

# Hem lining: closes the underside of the jacket from the hem in to the trouser seat, so you cannot see up inside it.
bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(1.738, 0, hem_cy, hem_rx - 0.012, hem_ry - 0.012), (1.765, 0, hem_cy, 0.84, 0.88)], seg=28, caps=(False, False))
new_obj("Flunky_HemLining", bm, M_VEST)

# Jacket collar: stands up round the back of the neck, folds over and falls onto the shoulders.
bm = bmesh.new()
arc_band(bm, [fb(3.78, 0.50, -0.40, 0.60), fb(3.81, 0.50, -0.42, 0.63), fb(3.80, 0.62, -0.48, 0.73), fb(3.735, 0.69, -0.52, 0.795)],   # fall ends at z 3.73 at the back, as measured
         -32, 212, 22, zfun=lambda si, sn: (0.13 if si == 1 else (0.05 if si == 2 else 0.0)) * max(0.0, sn) ** 0.6)
new_obj("Flunky_Collar", bm, M_SUIT, outward=False, thickness=0.03)
collar_edge = []
for i in range(23):                      # stitched edge along the collar's fall
    t = math.radians(-32 + 244 * i / 22)
    _, cx, cy, rx, ry = fb(3.735, 0.69, -0.52, 0.795)
    collar_edge.append(Vector((cx + rx * 0.965 * math.cos(t), cy + ry * 0.965 * math.sin(t), 3.765 + 0.012 * max(0.0, math.sin(t)))))
COLLAR_EDGE = collar_edge

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Arms, hands, legs and shoes are rigid robot sections under cloth. They are modelled directly in the body's
# rest pose (a T-pose with the legs straight down) at native size, each section around its own bone, so every
# section turns exactly about its joint and nothing has to be un-bent afterwards. The game's neutral animation
# then hangs the arms at his sides. Numbers are native units (game units / 0.966).
import json
RIG = json.load(open(SP + "flunky_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}         # rest-pose joint positions
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))


def xloft(bm, rings, seg=18, sx=1, caps=(True, True)):
    """Tube along the arm (the x axis). rings: (x, cy, cz, ry, rz). Stripes run along the sleeve; seam underneath."""
    vs = [[bm.verts.new((sx * x, cy + ry * math.cos(2 * math.pi * k / seg), cz + rz * math.sin(2 * math.pi * k / seg)))
           for k in range(seg)] for x, cy, cz, ry, rz in rings]
    uv = bm.loops.layers.uv.verify()
    girth = [Girth(r[3], r[4]) for r in rings]
    step = 360.0 / seg
    for i, (a, b) in enumerate(zip(vs, vs[1:])):
        for k in range(seg):
            f = bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
            mid_u = 90 + (((k + 0.5) * step - 90 + 180) % 360 - 180)
            for loop, (kk, r) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                ang = mid_u + (kk - k - 0.5) * step
                loop[uv].uv = ((girth[r].at(ang) - girth[r].at(90)) / STRIPE + 0.5, rings[r][0])
    for flag, ring in zip(caps, (vs[0], vs[-1])):
        if flag:
            f = bm.faces.new(ring)
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.0)


AZ = JR["Lh_wrist"].z                                            # the arm lies along x at this height
WX = JR["Lh_wrist"].x                                            # wrist joint
# sleeve: shoulder joint x 1.18, elbow x 2.13, hem 0.39 short of the wrist; depth (y) and height (z) radii
# The shoulder end is a dome centred on the shoulder joint (x 1.18, radius 0.36 in the plane the arm swings in),
# so the arm can hang, lift or swing without the top of the sleeve poking up.
SLEEVE = [(0.83, 0.25, AZ, 0.11, 0.08), (0.88, 0.25, AZ, 0.25, 0.19), (0.96, 0.25, AZ, 0.38, 0.285),
          (1.08, 0.25, AZ, 0.46, 0.346), (1.18, 0.25, AZ, 0.48, 0.36), (1.45, 0.27, AZ, 0.48, 0.385),
          (1.80, 0.28, AZ, 0.45, 0.385), (2.18, 0.30, AZ, 0.41, 0.35), (2.55, 0.26, AZ, 0.37, 0.32),
          (2.70, 0.24, AZ, 0.36, 0.31), (2.67, 0.24, AZ, 0.28, 0.24)]
BAND = [(2.43, 0.27, AZ, 0.385, 0.335), (2.71, 0.24, AZ, 0.375, 0.325)]      # turned-up cuff band
sleeves, plate_r, joint_r, brass_r, stitch_r = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    xloft(sleeves, SLEEVE, seg=18, sx=s)
    xloft(sleeves, BAND, seg=18, sx=s)
    for x in (2.52, 2.62):                                       # two buttons on the back-outer side of the band
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(math.radians(50)), math.sin(math.radians(50))))
        puck(brass_r, (s * x, cy + (ry + 0.005) * n.y, cz + (rz + 0.005) * n.z), n, 0.036, 0.03)
    for x in (2.455, 2.69):                                      # stitching round the band
        _, cy, cz, ry, rz = BAND[0] if x < 2.6 else BAND[1]
        ring = [Vector((s * x, cy + (ry + 0.004) * math.cos(math.radians(a)), cz + (rz + 0.004) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(stitch_r, ring, [0.0075] * len(ring), seg=4)
tag(brass_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("Flunky_Sleeves", sleeves, M_SUIT, rest=True)

# ---- forearm cuff, wrist joint and hand, flat in the rest pose: fingers straight out along x, index at the front
KN_X = JR["Lh_1"].x                                              # knuckle joints (0.31 from the wrist)
J2_X = JR["Lh_2"].x                                              # second finger joints (0.19 further)
FINGERS = (("index", JR["Lh_index1"].y - 0.035), ("rest", 0.15), ("rest", 0.31), ("rest", 0.47))   # y of each finger
PLATE_Y = 0.225
for s in (-1, 1):
    S = 'L' if s > 0 else 'R'
    T = Matrix.Identity(4) if s > 0 else Matrix.Translation(JR["Rh_wrist"] - MIRROR @ JR["Lh_wrist"]) @ MIRROR
    R3 = T.to_3x3()
    names = {'L': dict(wrist='Lh_wrist', index=('Lh_index1', 'Lh_index2'), rest=('Lh_1', 'Lh_2'), thumb=('Lh_thumb1', 'Lh_thumb2')),
             'R': dict(wrist='Rh_wrist', index=('Rh_index5', 'Rh_index6'), rest=('Rh_5', 'Rh_6'), thumb=('Rh_thumb7', 'Rh_thumb8'))}[S]
    ax = R3 @ Vector((1, 0, 0))
    c0 = T @ Vector((WX - 0.43, PLATE_Y, AZ))                    # metal cuff starts inside the sleeve
    lathe(plate_r, c0, ax, [(0.0, 0.243), (0.02, 0.271), (0.30, 0.281), (0.316, 0.298), (0.347, 0.298), (0.357, 0.233)], seg=20)
    lathe(joint_r, c0, ax, [(0.347, 0.207), (0.362, 0.233), (0.381, 0.202), (0.40, 0.233), (0.418, 0.202), (0.43, 0.226)], seg=16)
    for k in range(10):                                          # cuff rivets
        a = 2 * math.pi * (k + 0.5) / 10
        n = R3 @ Vector((0, math.cos(a), math.sin(a)))
        puck(plate_r, c0 + ax * 0.26 + n * 0.281, n, 0.0145, 0.012, seg=6)
    for n in (Vector((0, 0, 1)), Vector((0, -1, 0))):            # embossed emblem: outer face and front face once the arm hangs
        n = R3 @ n
        puck(plate_r, c0 + ax * 0.135 + n * 0.277, n, 0.062, 0.016, seg=12)
        puck(joint_r, c0 + ax * 0.135 + n * 0.281, n, 0.043, 0.016, seg=10)
        puck(plate_r, c0 + ax * 0.135 + n * 0.285, n, 0.023, 0.016, seg=8)
    # back-of-hand plate (on top in the rest pose), palm pad below it, dark core between; rivet row at the wrist end
    rbox(plate_r, T @ Matrix.Translation((WX + 0.165, PLATE_Y, AZ + 0.035)), (0.33, 0.68, 0.205), 0.07, 3)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.18, PLATE_Y, AZ - 0.088)), (0.27, 0.58, 0.10), 0.03, 1)
    rbox(joint_r, T @ Matrix.Translation((WX + 0.175, PLATE_Y, AZ - 0.02)), (0.29, 0.62, 0.125), 0.0)
    for k in range(7):
        puck(plate_r, T @ Vector((WX + 0.055, PLATE_Y - 0.28 + 0.093 * k, AZ + 0.138)), R3 @ Vector((0, 0, 1)), 0.0135, 0.012, seg=6)
    tag(plate_r, names['wrist'])                                 # cuff, wrist and hand plates move as one piece with the wrist
    tag(joint_r, names['wrist'])
    # fingers: first bone from the knuckle joint to the second joint, then a two-plate tip curling down, rigid with it
    for kind, fy in FINGERS:
        j1, j2 = names[kind]
        k0 = Vector((KN_X, fy, AZ + 0.012))
        k1 = Vector((J2_X, fy, AZ + 0.022))
        k2 = k1 + Vector((math.cos(math.radians(-14)), 0, math.sin(math.radians(-14)))) * 0.17
        k3 = k2 + Vector((math.cos(math.radians(-34)), 0, math.sin(math.radians(-34)))) * 0.15
        seg_box(plate_r, T, k0, k1, (0, 0, 1), 0.155, 0.152, 0.035, 2, gap=0.006)
        lathe(joint_r, T @ (k0 + Vector((0, -0.068, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.062), (0.136, 0.062)], seg=10)
        tag(plate_r, j1)
        tag(joint_r, j1)
        seg_box(plate_r, T, k1, k2, (0, 0, 1), 0.155, 0.152, 0.035, 2, gap=0.006)
        seg_box(plate_r, T, k2, k3, (0, 0, 1), 0.155, 0.152, 0.05, 2, gap=0.006)
        for q in (k1, k2):
            lathe(joint_r, T @ (q + Vector((0, -0.068, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.062), (0.136, 0.062)], seg=10)
        tag(plate_r, j2)
        tag(joint_r, j2)
    # thumb: pivot disc on the thumb joint at the front edge of the hand, first bone to the second thumb joint, then the tip
    t1, t2 = JR["Lh_thumb1"].copy(), JR["Lh_thumb2"].copy()
    td = (t2 - t1).normalized()
    t3 = t2 + (td + Vector((0.25, 0, -0.25))).normalized() * 0.17
    lathe(joint_r, T @ (t1 + Vector((0, 0, -0.075))), R3 @ Vector((0, 0, 1)), [(0.0, 0.10), (0.15, 0.10)], seg=14)
    tag(joint_r, names['wrist'])
    seg_box(plate_r, T, t1, t2 + td * 0.02, (0, 0, 1), 0.14, 0.14, 0.035, 2, gap=0.004)
    lathe(plate_r, T @ (t1 + Vector((0, 0, 0.07))), R3 @ Vector((0, 0, 1)), [(0.0, 0.085), (0.02, 0.085), (0.035, 0.055)], seg=14)
    tag(plate_r, names['thumb'][0])
    seg_box(plate_r, T, t2 + td * 0.02, t3, (0, 0, 1), 0.14, 0.14, 0.05, 2, gap=0.006)
    lathe(joint_r, T @ (t2 + td * 0.02 + Vector((0, 0, -0.062))), R3 @ Vector((0, 0, 1)), [(0, 0.056), (0.124, 0.056)], seg=10)
    tag(plate_r, names['thumb'][1])
    tag(joint_r, names['thumb'][1])
new_obj("Flunky_HandPlates", plate_r, M_PLATE, 32, rest=True)
new_obj("Flunky_HandJoints", joint_r, M_JOINT, 40, rest=True)
new_obj("Flunky_SleeveButtons", brass_r, M_BRASS, 32, rest=True)
new_obj("Flunky_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- trousers: one sealed garment. The seat is a closed bowl on the pelvis: rounded under the crotch, and running
# up well inside the jacket (the jacket hem is at z 1.80 here), so nothing is open from below. Each leg comes
# straight down out of it round the hip -> knee -> ankle bones (hip joint z 1.96, knee joint z 1.10).
seat = bmesh.new()
loft(seat, [(1.10, 0, 0, 0.08, 0.08), (1.14, 0, 0, 0.34, 0.33), (1.22, 0, 0, 0.62, 0.55), (1.33, 0, 0, 0.83, 0.70),
            (1.48, 0, 0, 0.98, 0.82), (1.66, 0, 0, 1.03, 0.93), (1.86, 0, 0, 1.02, 1.00), (2.05, 0, 0, 0.92, 0.92),
            (2.20, 0, 0, 0.75, 0.75)], seg=24, centres=(270, 90))
new_obj("Flunky_Seat", seat, M_SUIT, rest=True)
bm = bmesh.new()
# each leg sits just outside its bone (x 0.31), as the original's does, so the two legs do not run into each other
LEG = [(0.38, 0.36, -0.03, 0.31, 0.44), (0.52, 0.36, -0.03, 0.31, 0.45), (0.77, 0.38, -0.01, 0.35, 0.53),
       (1.04, 0.41, 0.0, 0.39, 0.62), (1.30, 0.44, 0.0, 0.43, 0.72), (1.50, 0.46, 0.0, 0.46, 0.81),
       (1.78, 0.48, 0.0, 0.48, 0.91)]
for s in (-1, 1):
    loft(bm, LEG, seg=16, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')                   # which leg a vertex belongs to, not which side of centre it is on
new_obj("Flunky_Trousers", bm, M_SUIT, rest=True)

# ---- shoes: cap-toe, welted, separate heel; pointing straight ahead in the rest pose (the stance turns them out)
# Footprint follows the original's, measured in the rest pose: the heel is narrow and sits on the ankle bone
# (x 0.31), 0.43 behind the ankle joint; the shoe widens only toward the ball and toe, and to the outside; the toe
# is 1.04 ahead of the joint. That is what lets the feet turn out 52 degrees without the heels meeting.
upper, sole = bmesh.new(), bmesh.new()
SHOE = [(0.48, 0.32, 0.10, 0.20), (0.42, 0.32, 0.145, 0.26), (0.22, 0.33, 0.175, 0.30), (-0.05, 0.36, 0.24, 0.30),
        (-0.35, 0.42, 0.32, 0.28), (-0.60, 0.44, 0.335, 0.25), (-0.78, 0.43, 0.30, 0.21), (-0.90, 0.42, 0.23, 0.16),
        (-0.965, 0.42, 0.14, 0.10), (-0.99, 0.42, 0.06, 0.05)]            # (y, centre x, half-width, height above the welt)
WELT, OUTSOLE = 0.104, 0.067
NS = 12


def shoe_at(y):
    for (y0, c0, w0, h0), (y1, c1, w1, h1) in zip(SHOE, SHOE[1:]):
        if y1 <= y <= y0:
            t = (y - y0) / (y1 - y0)
            return c0 + (c1 - c0) * t, w0 + (w1 - w0) * t, h0 + (h1 - h0) * t
    return SHOE[-1][1:]


def welt_extra(y):               # the welt ledge is slimmer round the heel so the heels stay clear of each other
    return 0.028 if y > 0.1 else 0.045


def shoe_sec(hw, h, k):
    c, sn = math.cos(math.pi * k / NS), math.sin(math.pi * k / NS)
    return hw * math.copysign(abs(c) ** 0.62, c), WELT + h * sn ** 0.6


def shoe_piece(bm, s, stations, grow=0.0):
    rings = [[bm.verts.new((s * (cx + shoe_sec(hw + grow, h + grow, k)[0]), y, shoe_sec(hw + grow, h + grow, k)[1]))
              for k in range(NS + 1)] for y, cx, hw, h in stations]
    for a, b in zip(rings, rings[1:]):
        for k in range(NS):
            bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])


def slab(bm, s, stations, z0, z1, extra=None):
    """stations: (y, centre x, half-width); extra widens it (a number, or None for the welt's own profile)."""
    ex = (lambda y: welt_extra(y)) if extra is None else (lambda y: extra)
    loop = [(s * (cx + w + ex(y)), y) for y, cx, w in stations] + [(s * (cx - w - ex(y)), y) for y, cx, w in reversed(stations)]
    top = [bm.verts.new((x, y, z1)) for x, y in loop]
    bot = [bm.verts.new((x, y, z0)) for x, y in loop]
    n = len(loop)
    for k in range(n):
        bm.faces.new((top[k], top[(k + 1) % n], bot[(k + 1) % n], bot[k]))
    bm.faces.new(top)
    bm.faces.new(bot)


PLAN = [(y, cx, w) for y, cx, w, h in SHOE]
for s in (-1, 1):
    shoe_piece(upper, s, SHOE)                                                           # vamp and quarters
    cap_y = -0.66
    shoe_piece(upper, s, [(cap_y, *shoe_at(cap_y))] + [st for st in SHOE if st[0] < cap_y], grow=0.0145)    # toe cap
    ctr_y = 0.16
    shoe_piece(upper, s, [st for st in SHOE if st[0] > ctr_y] + [(ctr_y, *shoe_at(ctr_y))], grow=0.0125)    # heel counter
    for y in (-0.30, -0.14):                                                             # lace facing seams
        cx, w, h = shoe_at(y)
        tube(sole, [Vector((s * (cx + shoe_sec(w + 0.003, h + 0.003, k)[0]), y, shoe_sec(w + 0.003, h + 0.003, k)[1]))
                    for k in range(2, NS - 1)], [0.006] * (NS - 3), seg=4)
    slab(sole, s, [(0.50, 0.32, 0.06)] + PLAN + [(-1.01, 0.42, 0.03)], OUTSOLE, WELT)    # welt ledge
    fore = [(-0.10, *shoe_at(-0.10)[:2])] + [p for p in PLAN if p[0] < -0.10] + [(-1.005, 0.42, 0.03)]
    slab(sole, s, fore, 0.012, OUTSOLE, 0.03)                                            # forefoot outsole
    heel = [(0.495, 0.32, 0.06)] + [p for p in PLAN if p[0] > 0.10] + [(0.10, *shoe_at(0.10)[:2])]
    slab(sole, s, heel, 0.012, OUTSOLE, 0.02)                                            # heel block
    for y in (-0.84, -0.72, -0.60, -0.48, -0.36, -0.24):                                 # tread bars
        cx, w, h = shoe_at(y)
        rbox(sole, Matrix.Translation((s * cx, y, 0.008)), (2 * w - 0.06, 0.072, 0.016), 0.0)
new_obj("Flunky_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("Flunky_Soles", sole, M_SOLE, 30, rest=True)

# ---------------------------------------------------------------- head: built from its plates, over a dark inner core
# HEAD is the outer surface the plates lie on: a cone 0.9 wide at the jaw, the jaw band jutting under the frown.
HEAD = [fb(3.91, 0.435, -0.51, 0.48), fb(3.94, 0.445, -0.54, 0.49), fb(4.03, 0.44, -0.55, 0.50),
        fb(4.10, 0.425, -0.50, 0.475), fb(4.16, 0.42, -0.45, 0.455), fb(4.22, 0.41, -0.44, 0.44),
        fb(4.30, 0.385, -0.42, 0.41), fb(4.40, 0.36, -0.37, 0.38), fb(4.56, 0.30, -0.31, 0.33),
        fb(4.73, 0.245, -0.255, 0.245), fb(4.82, 0.20, -0.215, 0.20), fb(4.87, 0.17, -0.185, 0.165),
        fb(4.90, 0.14, -0.155, 0.13)]
HEAD_N = 2.8                     # squared-off outline, like the original's boxy head (2 would be a round ellipse)
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.007                      # half the gap between neighbouring plates
BROW = 4.33                      # seam between the cranium and the face/side plates
JAWLINE = 4.00                   # seam between the side plates and the jaw band
HIDE_LATER = []


def frown(x):                    # the mouth line: z 4.125 at the centre, meeting the jawline at x = +-0.37
    return 4.125 - 0.125 * (x / 0.37) ** 2


def crease(z):                   # cheek crease: from (0.19, BROW) down and out to the mouth corner (0.33, JAWLINE)
    return 0.19 + (BROW - z) / (BROW - JAWLINE) * 0.14


def mouth_half(x):               # half-height of the frown cut: narrow at the centre, wide at the corners
    return 0.016 + 0.024 * min(1.3, abs(x) / 0.33) ** 2


def side_half(p):                # past the corners the cut carries on round the side, closing toward the back
    _, cx, cy, rx, ry = interp(HEAD, JAWLINE)
    return GAP + 0.034 * max(0.0, min(1.0, -(p.y - cy) / (0.75 * ry)))


def rim(x):                      # underside of the jaw band, frown shaped: the top edge of the open mouth
    return 3.97 - 0.09 * (x / 0.44) ** 2


def hp(a, z):
    return ring_pt(HEAD, z, a)[0]


def front_angle(x, z):
    return 360 - math.degrees(math.acos(max(-1.0, min(1.0, (x / interp(HEAD, z)[3]) ** (HEAD_N / 2)))))


def grid(bm, rows, wrap=False):
    vs = [[bm.verts.new(p) for p in r] for r in rows]
    n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n if wrap else n - 1):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


def mirror(row, s):
    return [Vector((s * p.x, p.y, p.z)) for p in row]


plates = bmesh.new()
for s in (1, -1):
    # cranium half: brow seam up to the crown, centre front round to centre back
    grid(plates, [mirror([hp(271.5 + 177.0 * i / 14, z) for i in range(15)], s)
                  for z in (BROW + GAP, 4.40, 4.48, 4.56, 4.65, 4.73, 4.80, 4.85, 4.885)])
    # cheek and side plate: from the cheek crease round to centre back, brow seam down to the jawline
    rows = []
    top = BROW - GAP
    for j in range(6):
        z = top + (JAWLINE + GAP - top) * j / 5
        a0 = front_angle(crease(z) + GAP, z)
        row = []
        for i in range(13):
            p = hp(a0 + (448.5 - a0) * i / 12, z)
            p.z = top + (JAWLINE + side_half(p) - top) * j / 5       # lower edge lifts where the mouth cut runs
            row.append(p)
        rows.append(mirror(row, s))
    grid(plates, rows)
loft(plates, [fb(4.892, 0.135, -0.15, 0.125), fb(4.90, 0.115, -0.13, 0.105)], seg=16, caps=(False, True), power=HEAD_N)   # flat crown cap
# muzzle plate: between the two cheek creases, from the brow seam down to the frown
rows = []
for j in range(7):
    t = j / 6
    row = []
    for i in range(9):
        c = -1 + i / 4
        xt, xb = c * (0.19 - GAP), c * (0.33 - GAP)
        zt, zb = BROW - GAP, frown(xb) + mouth_half(xb)
        row.append(surf(HEAD, xt + (xb - xt) * t, zt + (zb - zt) * t))
    rows.append(row)
grid(plates, rows)
# jaw band: one piece right round the head, under the frown at the front and under the jawline elsewhere
rows = []
NJ = 44
for f in (0.0, 0.3, 0.65, 1.0):
    row = []
    for i in range(NJ):
        a = 360.0 * i / NJ
        x = interp(HEAD, JAWLINE)[3] * math.cos(math.radians(a))
        if math.sin(math.radians(a)) < 0 and abs(x) < 0.37:
            top = frown(x) - mouth_half(x)
        else:
            top = JAWLINE - side_half(hp(a, JAWLINE))
        p = hp(a, 3.91 + f * (top - 3.91))
        row.append(Vector((p.x, p.y, rim(x) + f * (top - rim(x)))))
    rows.append(row)
grid(plates, rows, wrap=True)
tag(plates, 'joint_head')
head_ob = new_obj("Flunky_HeadPlates", plates, M_PLATE, 35, outward=True, thickness=-0.03)
bev = head_ob.modifiers.new("Chamfer", 'BEVEL')       # chamfered plate edges catch the light
bev.width = 0.006
bev.segments = 1
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(50)

# Inner core: fills the skull above the mouth only, and shows in the gaps between the upper plates. Below z 4.20
# the head is hollow: behind the lips (the muzzle plate above, the jaw band below) is open space back to the throat.
MOUTH_ROOF = 4.20
core = bmesh.new()
loft(core, [(MOUTH_ROOF,) + tuple(interp(HEAD, MOUTH_ROOF)[1:3]) + (interp(HEAD, MOUTH_ROOF)[3] - 0.032, interp(HEAD, MOUTH_ROOF)[4] - 0.032)]
     + [(z, cx, cy, rx - 0.032, ry - 0.032) for z, cx, cy, rx, ry in HEAD[:-1] if z > MOUTH_ROOF + 0.01]
     + [fb(4.885, 0.10, -0.115, 0.09)], seg=24, power=HEAD_N)
tag(core, 'joint_head')
new_obj("Flunky_HeadCore", core, M_JOINT, 50)

# lower jaw plate under the open mouth, its dark floor, and the ribbed neck running up into the head
loft(plate, [fb(3.775, 0.34, -0.42, 0.40), fb(3.81, 0.43, -0.535, 0.47), fb(3.845, 0.43, -0.545, 0.47)], seg=28, power=HEAD_N)
loft(black, [fb(3.846, 0.40, -0.50, 0.44), fb(3.85, 0.40, -0.50, 0.44)], seg=24, power=HEAD_N)
loft(black, [fb(3.84, 0.30, -0.02, 0.43), fb(MOUTH_ROOF + 0.01, 0.30, -0.02, 0.41)], seg=16)      # back of the mouth, 0.45 behind the lips
loft(joint, [(3.66 + 0.035 * i, 0, -0.16, 0.235 if i % 2 else 0.19, 0.235 if i % 2 else 0.19) for i in range(15)], seg=16)   # neck column, up into the mouth

# rivets along the plate edges
for a in (-18, 20, 45, 70, 110, 135, 160, 198):
    for z in (BROW + 0.035, BROW - 0.035):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.011, 0.012, seg=6)
for z in (4.75, 4.56, 4.45, 4.20, 4.08):
    for a in (84, 96):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.011, 0.012, seg=6)
for s in (-1, 1):
    for z in (4.26, 4.16, 4.07):
        p = surf(HEAD, s * (crease(z) + 0.035), z)
        puck(plate, p, (p.x, p.y - interp(HEAD, z)[2], 0), 0.01, 0.012, seg=6)

# nose: a small wedge plate on the muzzle
tube(plate, [(0, -0.37, 4.41), (0, -0.44, 4.355), (0, -0.485, 4.32), (0, -0.44, 4.295)], [0.022, 0.034, 0.036, 0.018], seg=4)

# glasses: round wire rims, domed lenses, pupils, bridge, temple arms; lens plane leans back with the face
LENS_Z, LENS_Y, TILT = 4.52, -0.375, 0.34
LN = Vector((0, -1, TILT)).normalized()
lens, white = bmesh.new(), bmesh.new()
for s in (-1, 1):
    c = Vector((s * 0.20, LENS_Y, LENS_Z))
    lathe(dark, c, LN, [(-0.022, 0.166), (-0.021, 0.19), (0.021, 0.19), (0.022, 0.166)], seg=24, caps=False)
    lathe(lens, c, LN, [(-0.006, 0.168), (0.006, 0.14), (0.014, 0.08), (0.017, 0.012)], seg=24)
    pc = c + Vector((-s * 0.095, TILT * -0.01, -0.01)) + LN * 0.016
    puck(black, pc, LN, 0.034, 0.008, seg=12)                                    # pupil, inner side at mid height
    puck(white, pc + Vector((-0.012, 0, 0.012)) + LN * 0.004, LN, 0.009, 0.006, seg=6)
    # temple arm: hinged on the outer edge of the rim, running straight back to the top-front of the earpiece
    e = Vector((s * 0.30, 0.08, 4.39))
    hinge = c + Vector((s * 0.19, 0, 0))
    ear_top = Vector((s * 0.455, e.y - 0.172 * 0.62, e.z + 0.172 * 0.72))
    rbox(dark, Matrix.Translation(hinge + Vector((s * 0.012, 0.012, 0))), (0.04, 0.05, 0.035), 0.008)
    tube(dark, [hinge + Vector((s * 0.01, 0.0, 0)), hinge + Vector((s * 0.03, 0.10, 0.0)), ear_top], [0.012] * 3, seg=6)
    # earpiece: rounded housing, two raised rings with a groove between them, and a centre knob
    ax = (s, 0, 0)
    lathe(dark, e, ax, [(0.0, 0.15), (0.07, 0.165), (0.10, 0.178), (0.15, 0.178), (0.175, 0.166), (0.186, 0.142),
                        (0.168, 0.138)], seg=24)
    lathe(brass, e, ax, [(0.16, 0.126), (0.192, 0.126), (0.202, 0.117), (0.202, 0.099), (0.16, 0.097)], seg=22)
    lathe(brass, e, ax, [(0.16, 0.078), (0.206, 0.078), (0.214, 0.070), (0.214, 0.053), (0.16, 0.051)], seg=18)
    lathe(brass, e, ax, [(0.16, 0.034), (0.222, 0.034), (0.234, 0.022), (0.238, 0.008)], seg=12)
tube(dark, [(-0.03, LENS_Y - 0.015, 4.535), (0.0, LENS_Y - 0.03, 4.55), (0.03, LENS_Y - 0.015, 4.535)], [0.013] * 3, seg=5)
for _bm in (lens, white, plate, joint, dark, black, brass):
    tag(_bm, 'joint_head')
new_obj("Flunky_Lenses", lens, M_LENS, 30)
new_obj("Flunky_EyeHighlights", white, M_WHITE)

# ---------------------------------------------------------------- suit front: real layers, inside to outside
shirt, tie, lap, vest_trim = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, epaul, seams = bmesh.new(), bmesh.new(), bmesh.new()

# Shirt collar: a band standing round the whole neck, folded down all the way round, with two points at the front.
loft(shirt, [fb(3.66, 0.42, -0.43, 0.40), fb(3.79, 0.36, -0.385, 0.40)], seg=24, caps=(False, False))
arc_band(shirt, [fb(3.79, 0.365, -0.39, 0.405), fb(3.81, 0.39, -0.41, 0.43), fb(3.71, 0.45, -0.46, 0.49)], -55, 235, 24)
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.045, s * 0.31, 3.745), (s * 0.11, s * 0.33, 3.63), (s * 0.24, s * 0.30, 3.53)], 0.014, nx=4)

# Tie: knot under the collar, blade running down the shirt front and into the vest's V.
patch(tie, SS, [(-0.095, 0.095, 3.735), (-0.125, 0.125, 3.665), (-0.075, 0.075, 3.585)], 0.03, nx=4)
patch(tie, SS, [(-0.07, 0.07, 3.59), (-0.10, 0.10, 3.40), (-0.11, 0.11, 3.28)], 0.006, nx=4)

# Vest front: a narrow button stand with four brass buttons, and a stitched edge round the V neck.
patch(vest_trim, VS, [(-0.055, 0.055, VEST_V), (-0.055, 0.055, 1.78)], 0.003, nx=2)
for z in (2.77, 2.53, 2.29, 2.03):
    p = surf(VS, 0.0, z, 0.018)
    lathe(brass, p, (0, -1, 0), [(0.0, 0.072), (0.02, 0.072), (0.036, 0.05), (0.044, 0.015)], seg=12)
    lathe(joint, p, (0, -1, 0), [(0.0, 0.082), (0.012, 0.082)], seg=12)                    # button shank shadow ring
tag(brass, '@vest')
tag(joint, '@vest')
stitch = bmesh.new()
for s in (-1, 1):
    zs = [VEST_V + (3.74 - VEST_V) * i / 6 for i in range(7)]
    tube(stitch, [surf(VS, s * (vest_gap(z) + 0.03), z, 0.004) for z in zs], [0.006] * 7, seg=4)             # vest V edge
    tag(stitch, '@vest')
    zs = [1.80 + (BREAK - 1.80) * i / 8 for i in range(9)]
    tube(stitch, [surf(TS, s * (front_gap(z) + 0.045), z, 0.004) for z in zs], [0.006] * 9, seg=4)           # jacket front edge
    tag(stitch, '@jacket')
tube(stitch, COLLAR_EDGE, [0.011] * len(COLLAR_EDGE), seg=5)
hem = [ring_pt(TS, 1.80, a, 0.004)[0] for a in range(-78, 259, 8)]
tube(stitch, hem, [0.006] * len(hem), seg=4)                                                                # jacket hem

# Jacket lapels and collar. The front edge of each jacket front folds back along the roll line (the edge of
# the opening) from the break up to the collar; the collar's front end meets the lapel along the gorge seam,
# and the step between them is the notch. Outlines are traced from the sheet's front view. Every piece has a
# row of topstitching just inside its edge.
def roll_lift(x, z):             # a lapel stands highest at the fold and lies flat at its outer edge
    return 0.012 + 0.04 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.16)


def flat_lift(x, z):
    return 0.006


for s in (-1, 1):
    g = front_gap
    lapel = [(g(2.95), 2.95), (0.66, 3.38), (0.53, 3.45), (g(3.56), 3.56), (g(3.36), 3.36), (g(3.15), 3.15)]
    collar_front = [(g(3.56), 3.56), (0.53, 3.45), (0.72, 3.50), (0.74, 3.66), (0.60, 3.74), (g(3.74), 3.74)]
    flap = [(0.62, 2.36), (1.04, 2.36), (1.04, 2.10), (1.00, 2.06), (0.66, 2.06), (0.62, 2.10)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.033)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)                                             # pocket flap
    topstitch(stitch, TS, o, lambda x, z: 0.029)
breast = [(0.45, 3.05), (0.84, 3.05), (0.84, 2.76), (0.645, 2.66), (0.45, 2.76)]
panel(pockets, TS, breast, flat_lift, cuts=2)                                            # breast pocket, pointed
topstitch(stitch, TS, breast, lambda x, z: 0.029)
pocket_sq = [surf(TS, x, z, 0.035) for x, z in ((0.47, 3.04), (0.82, 3.04), (0.80, 3.14), (0.735, 3.09), (0.69, 3.17),
                                         (0.645, 3.09), (0.60, 3.17), (0.555, 3.09), (0.49, 3.14))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')
tag(stitch, '@jacket')                                        # pocket square


# Medallion (the corp icon; its height matches the original's icon). It lies against the chest, resting on the
# lapel rolls, tilted to the chest's slope, and hangs from a strap that runs up under the shirt collar.
for _bm in (brass, plate, joint):
    tag(_bm, '@vest')
slope = (surf(TS, 0, 3.23).y - surf(TS, 0, 3.03).y) / 0.2
mn = Vector((0, -1, slope)).normalized()                 # outward normal of the chest here
mt = Vector((0, slope, 1)).normalized()                  # "up" along the chest
mc = surf(TS, 0.0, 3.13) + mn * 0.082
lathe(brass, mc, mn, [(0.0, 0.215), (0.05, 0.215), (0.065, 0.20), (0.066, 0.172), (0.045, 0.170)], seg=28)
lathe(plate, mc, mn, [(0.044, 0.165), (0.052, 0.165)], seg=28)
bail = mc + mt * 0.245 + mn * 0.03
lathe(brass, bail - Vector((0.03, 0, 0)), (1, 0, 0), [(0.0, 0.035), (0.06, 0.035)], seg=10)                 # bail the strap threads through
for pts in (((-0.04, 0.12), (0.04, 0.12), (0.027, 0.065), (-0.027, 0.065)),
            ((-0.027, 0.055), (0.027, 0.055), (0.062, -0.07), (0.0, -0.13), (-0.062, -0.07))):
    loop = [mc + mn * 0.056 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    for a, b in zip(loop, loop[1:] + loop[:1]):          # engraved tie outline
        tube(joint, [a, b], [0.007, 0.007], seg=4)
for _bm in (brass, plate, joint):
    tag(_bm, 'joint_attachMeter')
for s in (-1, 1):
    strap = [surf(SS, s * 0.33, 3.70, 0.03), surf(VS, s * 0.27, 3.52, 0.03), surf(VS, s * 0.13, 3.40, 0.07),
             bail + Vector((s * 0.02, 0, 0))]
    tube(joint, strap, [0.017] * 4, seg=5)

new_obj("Flunky_Shirt", shirt, M_SHIRT, 30)
new_obj("Flunky_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.014)
new_obj("Flunky_Stitching", stitch, M_STITCH, 40)
new_obj("Flunky_Tie", tie, M_TIE, 30, outward=True, thickness=0.022)
new_obj("Flunky_VestButtonStand", vest_trim, M_VEST, 30, outward=True, thickness=0.012)
new_obj("Flunky_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.03)
new_obj("Flunky_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.02)
tag(joint, '@vest')                        # the medallion strap lies on the vest
new_obj("Flunky_Plates", plate, M_PLATE, 32)
new_obj("Flunky_Joints", joint, M_JOINT, 40)
new_obj("Flunky_DarkParts", dark, M_DARK, 40)
new_obj("Flunky_MouthInterior", black, M_BLACK)
new_obj("Flunky_Brass", brass, M_BRASS, 32)

# ---------------------------------------------------------------- check camera + light, stats
cam = bpy.data.objects.new("FlunkyCam", bpy.data.cameras.new("FlunkyCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("FlunkySun", bpy.data.lights.new("FlunkySun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("FlunkyFill", bpy.data.lights.new("FlunkyFill", 'AREA'))     # soft fill so metal and cloth read
col.objects.link(fill)
fill.data.energy = 110
fill.data.size = 6
fill.location = (-6, -7, 4)
fill.rotation_euler = (Vector((0, 0, 2.4)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()
for o in list(bpy.data.collections.get("Flunky_Original", refcol).objects) + HIDE_LATER:                   # keep the original out of the way
    o.hide_set(True) if o.name in bpy.context.view_layer.objects else None

dg = bpy.context.evaluated_depsgraph_get()
tris = 0
pts = []
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        tris += sum(len(p.vertices) - 2 for p in em.polygons)
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
result = {"tris": tris, "x": [round(min(v.x for v in pts), 3), round(max(v.x for v in pts), 3)],
          "y": [round(min(v.y for v in pts), 3), round(max(v.y for v in pts), 3)],
          "z": [round(min(v.z for v in pts), 3), round(max(v.z for v in pts), 3)]}
