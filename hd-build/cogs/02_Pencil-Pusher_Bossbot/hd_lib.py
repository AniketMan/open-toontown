"""Shared HD cog build helpers (materials, lofts, garment panels, hard-surface blocks). Exec into the build script namespace, which must define: bpy, bmesh, math, Vector, Matrix, col, root, YOFF, STRIPE."""
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


def topstitch(bm, rings, outline, lift, inset=0.028, back=False, closed=True, step=0.06, radius=0.0075):
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
    tube(bm, [surf(rings, p.x, p.y, lift(p.x, p.y), back) for p in path], [radius] * len(path), seg=4)


def fb(z, half_w, front, back):
    """ring from a measured half-width (front view) and front/back depth (side view)"""
    return (z, 0.0, (front + back) / 2, half_w, (back - front) / 2)


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


def grid(bm, rows, wrap=False):
    vs = [[bm.verts.new(p) for p in r] for r in rows]
    n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n if wrap else n - 1):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


def mirror(row, s):
    return [Vector((s * p.x, p.y, p.z)) for p in row]

