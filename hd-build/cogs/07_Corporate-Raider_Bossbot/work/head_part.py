
# ---------------------------------------------------------------- head: an egg, with a jaw block bolted on the front
# HEAD is the outer surface. Pieces: the head shell in two halves on a hairline seam (front and back) over a closed
# inner shell; the blue mouth cassette, a block standing proud of the face; the ribbed moustache on it; a big nose;
# one eye and an eyepatch on its strap; the bandana shell with its spots; a hoop on a lug at each ear.
HEAD = [fb(6.50, 0.72, -0.55, 0.85), fb(6.70, 0.79, -0.58, 0.90), fb(7.00, 0.82, -0.58, 0.90),
        fb(7.30, 0.76, -0.55, 0.85), fb(7.60, 0.66, -0.50, 0.78), fb(7.85, 0.58, -0.45, 0.68),
        fb(8.05, 0.42, -0.30, 0.50), fb(8.16, 0.22, -0.12, 0.30)]
HEAD_N = 2.3
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.003
CORE_IN = 0.025


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def th_of(x, z):
    return math.degrees(math.asin(min(1.0, (min(0.999, abs(x) / interp(HEAD, z)[3])) ** (HEAD_N / 2.0)))) * (1 if x >= 0 else -1)


plates = bmesh.new()
HZ = [6.50, 6.60, 6.70, 6.85, 7.00, 7.15, 7.30, 7.45, 7.60, 7.72, 7.85, 7.95, 8.05, 8.11, 8.16]
for s in (1, -1):
    rows = []
    for z in HZ:
        g = abs(th_of(GAP, z))
        rows.append([hp(s * a, z) for a in [g] + [6.0 * i for i in range(1, 30)] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("CR_HeadPlates", plates, M_PLATE, 62, outward=True, thickness=-0.04)
core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("CR_HeadCore", core, M_JOINT, 60)
loft(plate, [fb(6.40, 0.50, -0.38, 0.60), fb(6.42, 0.64, -0.48, 0.76), fb(6.5005, 0.7205, -0.5505, 0.8505)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, 0.12, 6.16), (0, 0, 1), [(0.0, 0.50), (0.08, 0.58), (0.13, 0.58), (0.15, 0.50), (0.17, 0.61), (0.23, 0.61),
                                           (0.25, 0.52), (0.27, 0.62), (0.33, 0.62), (0.35, 0.54), (0.42, 0.54)], seg=28)

# mouth cassette: a blue block proud of the face, narrow at the top and flaring to the jaw
CAS_Z0, CAS_Z1 = 6.52, 7.40


def cas_hw(z):
    return 0.36 + 0.37 * (CAS_Z1 - z) / (CAS_Z1 - CAS_Z0)


def cas_pt(x, z, extra=0.0):
    u = max(-1.0, min(1.0, x / cas_hw(z)))
    v = (z - CAS_Z0) / (CAS_Z1 - CAS_Z0)
    lift = 0.30 * (1 - abs(u) ** 6) * (1 - max(0.0, 2 * v - 1) ** 6)
    return surf(HEAD, x * 0.9, z, 0.012 + lift + extra)


cas = bmesh.new()
grid(cas, [[cas_pt(cas_hw(z) * (i / 14 - 1), z) for i in range(29)] for z in [CAS_Z0 + (CAS_Z1 - CAS_Z0) * j / 14 for j in range(15)]])
tag(cas, 'joint_head')
new_obj("CR_MouthCassette", cas, M_BLUE, 50, outward=True, thickness=-0.03)
for x, z in ((0.3, 7.32), (-0.3, 7.32), (0.62, 6.62), (-0.62, 6.62), (0.2, 6.6), (-0.2, 6.6)):
    p = cas_pt(x, z, 0.0)
    puck(plate, p, (cas_pt(x, z, 1.0) - p).normalized(), 0.022, 0.02, seg=6)

# moustache: thick ribbed handlebar, modelled on the front of the cassette
UP = ((0.0, 7.17), (0.10, 7.25), (0.25, 7.28), (0.40, 7.20), (0.50, 7.00), (0.53, 6.78))
LO = ((0.0, 7.02), (0.10, 6.99), (0.25, 6.93), (0.38, 6.82), (0.47, 6.74), (0.53, 6.745))


def pl(pts, x):
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


stache = bmesh.new()
for s in (1, -1):
    rows = []
    for f in (0.0, 0.15, 0.35, 0.5, 0.65, 0.85, 1.0):
        row = []
        for i in range(33):
            x = 0.53 * i / 32
            zu, zl = pl(UP, x), pl(LO, x)
            rib = 0.012 * math.cos(x * 75.0)
            row.append(cas_pt(s * max(x, 0.004), zl + (zu - zl) * f, 0.008 + (0.07 + rib) * math.sin(math.pi * f) ** 0.7))
        rows.append(row)
    grid(stache, rows)
tag(stache, 'joint_head')
new_obj("CR_Moustache", stache, M_STACHE, 50, outward=True, thickness=-0.02)

# nose: a big wedge standing well out from the face
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (7.86, 7.76, 7.66, 7.57, 7.50, 7.455, 7.43)
ND = (0.0, 0.06, 0.13, 0.19, 0.22, 0.20, 0.12)
NR = (0.05, 0.07, 0.095, 0.12, 0.135, 0.12, 0.06)
tube(nose, [Vector((0, ny(z) - d + r * 0.3, z)) for z, d, r in zip(NZ, ND, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.12, ny(7.49) - 0.08, 7.49)) @ Matrix.Diagonal((0.085, 0.10, 0.07, 1.0)))
tag(nose, 'joint_head')
new_obj("CR_Nose", nose, M_PLATE, 60)

# his left eye: a ball in a socket rim under a heavy lid; his right eye: a patch on a strap
eyes, iris, dark = bmesh.new(), bmesh.new(), bmesh.new()
ep = surf(HEAD, 0.25, 7.72, -0.03)
en = (surf(HEAD, 0.25, 7.72, 1.0) - surf(HEAD, 0.25, 7.72, 0.0)).normalized()
bmesh.ops.create_uvsphere(eyes, u_segments=16, v_segments=10, radius=0.095, matrix=Matrix.Translation(ep))
puck(iris, ep + en * 0.088, en, 0.05, 0.016, seg=14)
lathe(plate, ep + en * 0.02, en, [(0.0, 0.135), (0.03, 0.135), (0.045, 0.118), (0.045, 0.098), (0.02, 0.094)], seg=20)
lid = [surf(HEAD, 0.25 + 0.13 * math.cos(math.radians(a)), 7.725 + 0.105 * math.sin(math.radians(a)), 0.055) for a in range(10, 171, 20)]
tube(dark, lid, [0.014] * len(lid), seg=5)
pp_ = surf(HEAD, -0.21, 7.72, 0.0)
pn = (surf(HEAD, -0.21, 7.72, 1.0) - pp_).normalized()
m = Matrix.Translation(pp_ + pn * 0.012) @ pn.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Diagonal((0.155, 0.125, 0.03, 1.0))
bmesh.ops.create_uvsphere(dark, u_segments=18, v_segments=8, radius=1.0, matrix=m)
strap = [hp(th, z, 0.014) for th, z in ((62, 7.93), (30, 7.86), (0, 7.80), (-th_of(0.21, 7.72), 7.72), (-48, 7.58), (-75, 7.45), (-100, 7.34))]
tube(dark, strap, [0.016] * len(strap), seg=5)
for _b in (eyes, iris, dark):
    tag(_b, 'joint_head')
new_obj("CR_Eye", eyes, M_EYE, 60)
new_obj("CR_Iris", iris, M_IRIS, 40)
new_obj("CR_Patch", dark, M_PATCH, 50)

# bandana: a rigid red shell over the crown, low at the back, with raised cream spots
def band_edge(th):
    return 7.90 - 0.80 * (math.sin(math.radians(th / 2)) ** 2) ** 1.3 + (0.05 if th > 0 else 0.0) * math.sin(math.radians(min(abs(th), 180)))


bandana, spots = bmesh.new(), bmesh.new()
BT = [-180 + 6.0 * i for i in range(61)]
rows = []
for f in (0.0, 0.2, 0.4, 0.6, 0.8, 0.93, 1.0):
    rows.append([hp(th, band_edge(th) + (8.16 - band_edge(th)) * f, 0.045 + 0.02 * math.sin(math.pi * f)) for th in BT])
grid(bandana, rows)
bmesh.ops.remove_doubles(bandana, verts=bandana.verts, dist=0.0005)
_z, _cx, _cy, _rx, _ry = HEAD[-1]
loft(bandana, [(8.16, _cx, _cy, _rx + 0.045, _ry + 0.045), (8.21, _cx, _cy, _rx * 0.5, _ry * 0.5), (8.225, _cx, _cy, 0.02, 0.02)],
     seg=60, power=HEAD_N, caps=(False, True))
tag(bandana, 'joint_head')
new_obj("CR_Bandana", bandana, M_BANDANA, 50, outward=True, thickness=-0.03)
for th, z, r in ((-40, 7.98, 0.07), (25, 8.03, 0.075), (70, 7.86, 0.07), (-85, 7.80, 0.075), (110, 7.98, 0.07), (-125, 7.95, 0.075),
                 (150, 7.72, 0.07), (-160, 7.62, 0.075), (180, 7.95, 0.07), (125, 7.52, 0.065), (-130, 7.45, 0.065), (0, 8.12, 0.06),
                 (-170, 7.25, 0.06), (165, 7.32, 0.06)):
    p, n = ring_pt(HEAD, z, 270 + th, 0.062)
    puck(spots, p, n, r, 0.012, seg=12)
tag(spots, 'joint_head')
new_obj("CR_BandanaSpots", spots, M_SPOT, 40)

# ear lugs and gold hoops
gold = bmesh.new()
for a in (2, 178):
    p, n = ring_pt(HEAD, 7.14, a, 0.0)
    lathe(steel, p - n * 0.01, n, [(0.0, 0.085), (0.035, 0.085), (0.05, 0.07), (0.05, 0.05), (0.03, 0.046)], seg=18)
    lathe(gold, p, n, [(0.03, 0.04), (0.06, 0.04), (0.07, 0.03), (0.072, 0.002)], seg=12)
    c = p + n * 0.05 + Vector((0, -0.04, -0.22))
    ring = [c + 0.19 * (Vector((0, 1, 0)) * math.cos(math.radians(t)) + Vector((0, 0, 1)) * math.sin(math.radians(t))) for t in range(0, 361, 15)]
    tube(gold, ring, [0.032] * len(ring), seg=8, caps=False)
tag(gold, 'joint_head')
new_obj("CR_Gold", gold, M_GOLD, 50)
for th, z in ((8, 7.60), (-8, 7.60), (60, 7.30), (-60, 7.30), (100, 6.80), (-100, 6.80), (172, 6.80), (-172, 6.80), (172, 7.0), (-172, 7.0)):
    p, n = ring_pt(HEAD, z, 270 + th, 0.0)
    puck(plate, p, n, 0.02, 0.02, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.011

loft(shirt, [fb(6.30, 0.85, -0.72, 0.86), fb(6.58, 0.78, -0.68, 0.80), fb(6.58, 0.74, -0.64, 0.76), fb(6.33, 0.77, -0.66, 0.79)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.05, s * 0.55, 6.50), (s * 0.16, s * 0.60, 6.32), (s * 0.36, s * 0.52, 6.12)], 0.03, nx=4)
patch(tie, SS, [(-0.14, 0.14, 6.45), (-0.19, 0.19, 6.32), (-0.12, 0.12, 6.10)], 0.06, nx=4)
patch(tie, SS, [(-0.11, 0.11, 6.12), (-0.18, 0.18, 5.80), (-0.19, 0.19, 5.62)], 0.02, nx=4)

panel(placket, TS, [(-0.12, 3.07), (0.40, 3.07), (0.40, 5.10), (0.18, 5.50), (-0.12, 5.50)], lambda x, z: 0.008, cuts=2)
for z in (4.68, 4.28, 3.88, 3.40):
    p = surf(TS, 0.12, z, 0.03)
    nrm = (surf(TS, 0.12, z, 1.0) - surf(TS, 0.12, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.10), (0.022, 0.10), (0.045, 0.078), (0.045, 0.058), (0.028, 0.053)], seg=14)
    lathe(pewter, p, nrm, [(0.022, 0.053), (0.053, 0.038), (0.064, 0.01)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.115), (0.013, 0.115)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
for xe in (0.36, -0.08):
    edge = [(xe, 5.05 - (5.05 - 3.18) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.044) for x, z in edge], [SR] * len(edge), seg=4)
hem = [ring_pt(TS, 3.18, a, 0.012)[0] for a in range(-76, 257, 6)]
tube(stitch, hem, [SR] * len(hem), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)


def roll_lift(x, z):
    return 0.02 + 0.05 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.25)


def flat_lift(x, z):
    return 0.012


g = front_gap
for s in (-1, 1):
    lapel = [(0.012, 5.56), (1.00, 5.92), (1.12, 6.05), (0.85, 6.15), (g(6.18), 6.18), (g(5.95), 5.95), (g(5.75), 5.75)]
    collar_front = [(g(6.18), 6.18), (0.85, 6.15), (1.20, 6.16), (1.25, 6.27), (0.95, 6.42), (g(6.42), 6.42)]
    flap = [(1.05, 3.98), (1.72, 3.98), (1.72, 3.50), (1.68, 3.45), (1.09, 3.45), (1.05, 3.50)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.055, inset=0.04, step=0.1, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.048, inset=0.036, step=0.1, radius=SR)
breast = [(0.72, 5.22), (1.42, 5.22), (1.42, 4.62), (1.07, 4.45), (0.72, 4.62)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.048, inset=0.036, step=0.1, radius=SR)
panel(pockets, TS, [(0.72, 5.22), (1.42, 5.22), (1.42, 5.11), (0.72, 5.11)], lambda x, z: 0.028, cuts=1)
pocket_sq = [surf(TS, x, z, 0.052) for x, z in ((0.78, 5.21), (1.36, 5.21), (1.35, 5.33), (1.27, 5.29), (1.20, 5.44),
                                               (1.12, 5.30), (1.03, 5.45), (0.95, 5.30), (0.85, 5.37))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')


# Shoulder straps: a band over each shoulder, from the chest up over the ridge and down the back, a stud at each end.
def ts_hw(z):
    return interp(TS, z)[3]


XF, ZF, XB, ZB, XT, ZT = 1.62, 5.90, 1.55, 5.65, 1.25, 6.28


def strap_edge(dx, lift=0.03, n=7, m=9):
    lo, hi = ZF, 6.5
    for _ in range(40):
        mid = (lo + hi) / 2
        if XF + dx + (XT - XF) * (mid - ZF) / (ZT - ZF) < 0.975 * ts_hw(mid):
            lo = mid
        else:
            hi = mid
    zt = lo
    xt = 0.975 * ts_hw(zt)
    pts = []
    for i in range(n):
        f = i / (n - 1)
        pts.append(surf(TS, XF + dx + (xt - XF - dx) * f, ZF + (zt - ZF) * f, lift))
    for i in range(1, m):
        f = i / (m - 1)
        pts.append(surf(TS, xt + (XB + dx - xt) * f, zt + (ZB - zt) * f, lift, back=True))
    return pts


for s in (-1, 1):
    grid(straps, [mirror(strap_edge(dx), s) for dx in (-0.15, 0.0, 0.15)])
    c0, c1 = strap_edge(0.0, 0.06), strap_edge(0.0, 1.06)
    for i in (1, -2):
        nrm = (c1[i] - c0[i]).normalized()
        lathe(pewter, Vector((s * c0[i].x, c0[i].y, c0[i].z)), Vector((s * nrm.x, nrm.y, nrm.z)),
              [(0.0, 0.046), (0.02, 0.046), (0.035, 0.022), (0.04, 0.002)], seg=10)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 5.20
slope = (surf(TS, 0, MZ + 0.2).y - surf(TS, 0, MZ - 0.2).y) / 0.4
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.075
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.34), (0.075, 0.34), (0.10, 0.316), (0.103, 0.272), (0.07, 0.265)], seg=28)
lathe(medal_p, mc, mn, [(0.068, 0.265), (0.083, 0.15), (0.088, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.40 + mn * 0.055
lathe(medal_p, mc + mt * 0.325 + mn * 0.05, mt, [(0.0, 0.056), (0.05, 0.066), (0.10, 0.046)], seg=10)
lathe(medal_p, bail - Vector((0.056, 0, 0)), (1, 0, 0), [(0.0, 0.05), (0.112, 0.05)], seg=10)
for pts in (((-0.11, 0.19), (0.11, -0.19)), ((0.11, 0.19), (-0.11, -0.19)), ((-0.11, 0.19), (0.11, 0.19)), ((-0.11, -0.19), (0.11, -0.19))):
    loop = [mc + mn * 0.094 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    tube(medal_j, loop, [0.012, 0.012], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.45, 6.33, 0.04), surf(TS, s * (g(6.05) + 0.03), 6.05, 0.09), surf(TS, s * (g(5.8) + 0.025), 5.8, 0.09),
           surf(TS, s * 0.05, 5.64, 0.095), bail + Vector((s * 0.03, 0, 0))]
    tube(cord, pts, [0.02] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("CR_Shirt", shirt, M_SHIRT, 30)
new_obj("CR_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.026)
new_obj("CR_Stitching", stitch, M_STITCH, 40)
new_obj("CR_Tie", tie, M_TIE, 30, outward=True, thickness=0.036)
new_obj("CR_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.03)
new_obj("CR_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.05)
new_obj("CR_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.03)
new_obj("CR_Straps", straps, M_SUIT, 40, outward='up', thickness=0.03)
new_obj("CR_Medallion", medal_p, M_PEWTER, 32)
new_obj("CR_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("CR_Cord", cord, M_JOINT, 40)
new_obj("CR_Plates", plate, M_PLATE, 32)
new_obj("CR_Joints", joint, M_JOINT, 40)
new_obj("CR_Steel", steel, M_STEEL, 40)
new_obj("CR_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("CRCam", bpy.data.cameras.new("CRCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("CRSun", bpy.data.lights.new("CRSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("CRFill", bpy.data.lights.new("CRFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 280
fill.data.size = 10
fill.location = (-10, -11, 6)
fill.rotation_euler = (Vector((0, 0, 3.8)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
