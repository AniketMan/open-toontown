
# ---------------------------------------------------------------- head: a tall tapering shell
# HEAD is the outer surface (front view half-widths, side view front and back). Pieces: the face shell in two
# halves meeting on a hairline down the centre and the back; the mouth cassette, a domed plate whose arched top edge
# is the frown; a slit under the nose that turns up at each end; eye slots with the ball behind; the hair shell on
# the back; ears; and the hat. All of it over a closed inner shell.
HEAD = [fb(4.56, 0.262, -0.265, 0.19), fb(4.60, 0.257, -0.26, 0.188), fb(4.80, 0.235, -0.248, 0.18),
        fb(5.00, 0.208, -0.228, 0.17), fb(5.20, 0.168, -0.208, 0.158), fb(5.35, 0.147, -0.185, 0.15),
        fb(5.50, 0.13, -0.15, 0.14), fb(5.65, 0.112, -0.11, 0.13), fb(5.80, 0.10, -0.065, 0.12),
        fb(5.87, 0.095, -0.05, 0.115)]
GAP = 0.0012
CORE_IN = 0.008
BASE_Z, TOP_Z = 4.56, 5.87
ARCH_TOP, ARCH_END_Z, ARCH_END_X = 5.225, 4.86, 0.20


def hp(th, z, eps=0.0):          # point on the head, th degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def rxz(z):
    return interp(HEAD, z)[3]


def hx(th, z):                   # how far out from the centre line that point is
    return rxz(z) * math.sin(math.radians(min(abs(th), 90.0)))


def agap(z, d=GAP):
    return math.degrees(d / rxz(z))


def arch_z(x):                   # the frown: top edge of the mouth cassette
    return ARCH_TOP - (ARCH_TOP - ARCH_END_Z) * min(1.0, x / ARCH_END_X) ** 1.5


THC = math.degrees(math.asin(ARCH_END_X / rxz(ARCH_END_Z)))      # the cassette's sides run straight down from the ends of the frown


def arch_col(th):                # height at which a column crosses the frown
    lo, hi = ARCH_END_Z, ARCH_TOP
    for _ in range(40):
        mid = (lo + hi) / 2
        if mid < arch_z(hx(th, mid)):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def arch_gap(x):                 # the frown is cut wider than a panel line, closing to a hairline at its ends
    return GAP + 0.0035 * max(0.0, 1 - (x / ARCH_END_X) ** 2)


SLIT_X = 0.135


def slit_col(th):                # the line under the nose, turning up at each end; (height, half-gap)
    z = 5.36
    for _ in range(4):
        x = hx(th, z)
        z = 5.345 + 0.055 * min(1.0, x / SLIT_X) ** 3
    return z, (0.0018 * min(1.0, (SLIT_X - x) / 0.012) if x < SLIT_X and abs(th) < 89 else 0.0)


EYE_X, EYE_Z, EYE_A, EYE_B = 0.075, 5.525, 0.036, 0.024


def eye_col(th):                 # eye slot: (height below centre, height above centre); the lid covers the top of the ball
    t = (hx(th, EYE_Z) - EYE_X) / EYE_A
    if abs(t) >= 1 or abs(th) > 89:
        return 0.0, 0.0
    return EYE_B * math.sqrt(1 - t * t), 0.3 * EYE_B * math.sqrt(1 - t * t)


A_F, B_F, C_F = (0.0, 0.33, 0.66, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.2, 0.45, 0.75, 1.0)


def face_zs(th):
    bot = ARCH_END_Z if th >= THC - 1e-6 else arch_col(th) + arch_gap(hx(th, arch_col(th)))
    zs, gs = slit_col(th)
    el, eh = eye_col(th)
    return ([bot + (zs - gs - bot) * f for f in A_F] + [zs + gs + (EYE_Z - el - zs - gs) * f for f in B_F] +
            [EYE_Z + eh + (TOP_Z - EYE_Z - eh) * f for f in C_F])


IN_TH = [3.0 * i for i in range(int(THC // 3) + 1)] + [THC]
OUT_TH = [THC] + [a for a in (66, 72, 78, 84, 90, 100, 110, 120, 130, 140, 150, 160, 170) if a > THC + 1] + [180]
plates = bmesh.new()
for s in (1, -1):
    t = bmesh.new()
    cols = []
    for th in IN_TH:
        cols.append([t.verts.new(hp(s * max(th, agap(z)), z)) for z in face_zs(th)])
    for a, b in zip(cols, cols[1:]):
        for k in range(12):
            if k not in (3, 7):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    cols = []
    for th in OUT_TH:
        zs = [BASE_Z + (ARCH_END_Z - BASE_Z) * f for f in (0.0, 0.35, 0.7)] + face_zs(th)
        col_ = []
        for z in zs:
            a = th
            if th == THC and z < ARCH_END_Z:
                a = THC + agap(z)
            if th == 180:
                a = 180 - agap(z)
            col_.append(t.verts.new(hp(s * a, z)))
        cols.append(col_)
    for a, b in zip(cols, cols[1:]):
        for k in range(15):
            if k not in (6, 10):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("DS_HeadPlates", plates, M_PLATE, 50, outward=True, thickness=-0.016)

# mouth cassette: one domed plate, a little proud of the shell, filling the arch
CAS_LIFT = 0.005
cas = bmesh.new()
CT = [-(THC - 0.3) + 2 * (THC - 0.3) * i / 40 for i in range(41)]
rows = []
for f in (0.0, 0.2, 0.4, 0.6, 0.8, 0.92, 1.0):
    row = []
    for th in CT:
        zc = arch_col(abs(th)) if abs(th) < THC else ARCH_END_Z
        top = zc - arch_gap(hx(th, zc))
        row.append(hp(th, BASE_Z + (top - BASE_Z) * f, CAS_LIFT))
    rows.append(row)
grid(cas, rows)
tag(cas, 'joint_head')
new_obj("DS_MouthCassette", cas, M_PLATE, 50, outward=True, thickness=-0.02)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36)
tag(core, 'joint_head')
new_obj("DS_HeadCore", core, M_JOINT, 60)
# top of the head (under the hat), the underside and the layered neck bearing
loft(plate, [fb(4.50, 0.16, -0.14, 0.14), fb(4.515, 0.22, -0.22, 0.165), fb(4.5605, 0.2615, -0.2645, 0.1895)], seg=32, caps=(True, False))
loft(plate, [fb(5.8695, 0.0945, -0.0495, 0.1145), fb(5.885, 0.05, -0.01, 0.07)], seg=32, caps=(False, True))
lathe(steel, (0, 0.0, 4.40), (0, 0, 1), [(0.0, 0.11), (0.03, 0.14), (0.05, 0.14), (0.058, 0.118), (0.066, 0.152), (0.088, 0.152),
                                          (0.096, 0.124), (0.104, 0.156), (0.128, 0.156), (0.136, 0.13), (0.15, 0.13)], seg=24)

# eyes: cream ball behind the slot, dark pupil low in it, a dark lid line along the top
eyes, iris, lash = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    rows = []
    for z in (5.495, 5.515, 5.535, 5.555):
        rows.append([hp(s * math.degrees(math.asin(min(0.99, (EYE_X + EYE_A * 1.15 * (i / 4 - 1)) / rxz(z)))), z, -0.005) for i in range(9)])
    grid(eyes, rows)
    p, n = ring_pt(HEAD, 5.516, 270 + s * math.degrees(math.asin((EYE_X - 0.004) / rxz(5.516))), -0.0042)
    puck(iris, p, n, 0.0115, 0.004, seg=12)
    pts, rr = [], []
    for i in range(11):
        x = EYE_X + EYE_A * (i / 5 - 1)
        th = math.degrees(math.asin(x / rxz(EYE_Z)))
        pts.append(hp(s * th, EYE_Z + eye_col(th)[1] + 0.002, 0.002))
        rr.append(0.003 + 0.003 * math.sin(math.pi * i / 10))
    tube(lash, pts, rr, seg=5)
for _b in (eyes, iris, lash):
    tag(_b, 'joint_head')
new_obj("DS_Eyes", eyes, M_EYE, 60, outward=True)
new_obj("DS_Iris", iris, M_IRIS, 40)
new_obj("DS_Lids", lash, M_HAIR, 40)

# brows: heavy black bars slanting down to the nose
brow = bmesh.new()
for s in (-1, 1):
    o = [(0.012, 5.572), (0.035, 5.615), (0.118, 5.652), (0.127, 5.628), (0.062, 5.592), (0.02, 5.552)]
    panel(brow, HEAD, [(s * x, z) for x, z in o], lambda x, z: 0.008, cuts=1)
tag(brow, 'joint_head')
new_obj("DS_Brows", brow, M_HAIR, 35, outward=True, thickness=-0.013)

# nose: a long ridge widening to a blunt end with two wings
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (5.61, 5.55, 5.48, 5.42, 5.385, 5.36, 5.35)
NR = (0.007, 0.011, 0.016, 0.022, 0.027, 0.024, 0.012)
tube(nose, [Vector((0, ny(z) + r * 0.5, z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.032, ny(5.385) + 0.022, 5.385)) @ Matrix.Diagonal((0.022, 0.022, 0.016, 1.0)))
tag(nose, 'joint_head')
new_obj("DS_Nose", nose, M_PLATE, 60)

# ears: small shells on the sides, at the front edge of the hair
ears = bmesh.new()
for a in (22, 158):
    p, n = ring_pt(HEAD, 5.52, a, 0.004)
    m = Matrix.Translation(p) @ n.to_track_quat('X', 'Z').to_matrix().to_4x4() @ Matrix.Diagonal((0.012, 0.026, 0.042, 1.0))
    bmesh.ops.create_uvsphere(ears, u_segments=12, v_segments=8, radius=1.0, matrix=m)
    lathe(joint, p + n * 0.011, n, [(0.0, 0.012), (0.003, 0.012)], seg=10)
tag(ears, 'joint_head')
new_obj("DS_Ears", ears, M_PLATE, 60)

# hair shell: a black tongue-shaped plate on the back of the head, from under the hat down to a rounded point
hair = bmesh.new()
rows = []
for i in range(12):
    z = 5.22 + (TOP_Z - 5.22) * i / 11
    half = 80.0 * min(1.0, max(0.0, (z - 5.22) / 0.33)) ** 0.6
    rows.append([ring_pt(HEAD, z, 90 + half * (j / 8 - 1), 0.011)[0] for j in range(17)])
grid(hair, rows)
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0003)
tag(hair, 'joint_head')
new_obj("DS_Hair", hair, M_HAIR, 50, outward=True, thickness=-0.011)

# hat: a small bowler tipped back, with a band
hat, hband = bmesh.new(), bmesh.new()
HO, HA = Vector((0, 0.03, 5.815)), Vector((0, 0.17, 1)).normalized()
lathe(hat, HO, HA, [(0.0, 0.10), (0.004, 0.172), (0.02, 0.183), (0.04, 0.172), (0.034, 0.108), (0.05, 0.10), (0.225, 0.095),
                    (0.245, 0.08), (0.252, 0.04), (0.254, 0.001)], seg=28)
lathe(hband, HO, HA, [(0.045, 0.1035), (0.095, 0.1025)], seg=28, caps=False)
tag(hat, 'joint_head')
tag(hband, 'joint_head')
new_obj("DS_Hat", hat, M_HAT, 50)
new_obj("DS_HatBand", hband, M_BAND, 50, outward=True, thickness=0.004)

# rivets
for th, z in ((6, 4.60), (-6, 4.60), (THC - 5, 4.62), (-THC + 5, 4.62), (THC + 6, 4.90), (-THC - 6, 4.90), (THC + 6, 4.62), (-THC - 6, 4.62),
              (5, 5.70), (-5, 5.70), (60, 5.30), (-60, 5.30)):
    p, n = ring_pt(HEAD, z, 270 + th, CAS_LIFT if abs(th) < THC and z < 4.8 else 0.0)
    puck(plate, p, n, 0.0075, 0.008, seg=6)
for z in (4.62, 4.85, 5.08):
    for a in (84, 96):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.0075, 0.008, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.005

loft(shirt, [fb(4.50, 0.235, -0.19, 0.265), fb(4.62, 0.21, -0.165, 0.235), fb(4.62, 0.195, -0.15, 0.22), fb(4.515, 0.20, -0.155, 0.225)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.025, s * 0.22, 4.54), (s * 0.065, s * 0.245, 4.47), (s * 0.12, s * 0.18, 4.37)], 0.014, nx=4)
patch(tie, SS, [(-0.06, 0.06, 4.50), (-0.08, 0.08, 4.44), (-0.05, 0.05, 4.36)], 0.03, nx=4)
patch(tie, SS, [(-0.05, 0.05, 4.37), (-0.08, 0.08, 4.15), (-0.085, 0.085, 4.06)], 0.008, nx=4)

panel(placket, TS, [(-0.02, 2.428), (0.14, 2.428), (0.14, 3.78), (0.06, 3.955), (-0.02, 3.955)], lambda x, z: 0.004, cuts=2)
for z in (3.50, 3.31, 3.09, 2.86, 2.67):
    p = surf(TS, 0.05, z, 0.013)
    lathe(pewter, p, (0, -1, 0), [(0.0, 0.04), (0.009, 0.04), (0.018, 0.031), (0.018, 0.023), (0.011, 0.021)], seg=14)
    lathe(pewter, p, (0, -1, 0), [(0.009, 0.021), (0.022, 0.015), (0.026, 0.004)], seg=10)
    lathe(joint, p, (0, -1, 0), [(0.0, 0.046), (0.005, 0.046)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.123, 3.76 - (3.76 - 2.60) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.021) for x, z in edge], [SR] * len(edge), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.005)[0] for a in HB] for z in (2.424, 2.50, 2.585)])
tag(hemband, '@jacket')
new_obj("DS_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.013)
hs = [ring_pt(TS, 2.565, a, 0.021)[0] for a in HB]
tube(stitch, hs, [SR] * len(hs), seg=4)
for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):
    p, n = ring_pt(TS, 2.495, a, 0.018)
    lathe(pewter, p, n, [(0.0, 0.027), (0.009, 0.027), (0.017, 0.014), (0.02, 0.001)], seg=10)


def roll_lift(x, z):
    return 0.009 + 0.026 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.12)


def flat_lift(x, z):
    return 0.006


g = front_gap
for s in (-1, 1):
    lapel = [(0.004, 3.975), (0.40, 4.125), (0.43, 4.19), (0.33, 4.285), (g(4.30), 4.30), (g(4.20), 4.20), (g(4.08), 4.08)]
    collar_front = [(g(4.30), 4.30), (0.33, 4.285), (0.45, 4.30), (0.455, 4.36), (0.38, 4.49), (g(4.49), 4.49)]
    flap = [(0.27, 3.0), (0.455, 3.0), (0.455, 2.845), (0.44, 2.825), (0.285, 2.825), (0.27, 2.845)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.027, inset=0.02, step=0.05, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)
breast = [(0.235, 3.76), (0.455, 3.76), (0.455, 3.44), (0.42, 3.40), (0.27, 3.40), (0.235, 3.44)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)
panel(pockets, TS, [(0.235, 3.76), (0.455, 3.76), (0.455, 3.71), (0.235, 3.71)], lambda x, z: 0.014, cuts=1)
pocket_sq = [surf(TS, x, z, 0.026) for x, z in ((0.255, 3.755), (0.435, 3.755), (0.43, 3.82), (0.405, 3.80), (0.385, 3.875),
                                               (0.355, 3.81), (0.33, 3.885), (0.305, 3.81), (0.27, 3.84))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')

# Back: a pointed yoke patch on each shoulder blade, stitched round its edge
for s in (-1, 1):
    o = [(s * x, z) for x, z in ((0.31, 4.46), (0.55, 4.46), (0.505, 4.03), (0.29, 4.26))]
    panel(straps, TS, o, lambda x, z: 0.007, back=True, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.023, inset=0.016, back=True, step=0.05, radius=SR)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 3.80
slope = (surf(TS, 0, MZ + 0.1).y - surf(TS, 0, MZ - 0.1).y) / 0.2
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.034
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.155), (0.034, 0.155), (0.046, 0.144), (0.047, 0.124), (0.032, 0.121)], seg=28)
lathe(medal_p, mc, mn, [(0.031, 0.121), (0.038, 0.07), (0.04, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.182 + mn * 0.026
lathe(medal_p, mc + mt * 0.148 + mn * 0.024, mt, [(0.0, 0.026), (0.024, 0.031), (0.048, 0.022)], seg=10)
lathe(medal_p, bail - Vector((0.026, 0, 0)), (1, 0, 0), [(0.0, 0.024), (0.052, 0.024)], seg=10)
for pts in (((-0.03, 0.085), (0.03, 0.085), (0.02, 0.048), (-0.02, 0.048)),
            ((-0.02, 0.04), (0.02, 0.04), (0.046, -0.048), (0.0, -0.09), (-0.046, -0.048))):
    loop = [mc + mn * 0.043 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    for a, b in zip(loop, loop[1:] + loop[:1]):
        tube(medal_j, [a, b], [0.0055, 0.0055], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.20, 4.50, 0.02), surf(TS, s * (g(4.35) + 0.015), 4.35, 0.042), surf(TS, s * (g(4.20) + 0.012), 4.20, 0.042),
           surf(TS, s * 0.025, 4.04, 0.044), bail + Vector((s * 0.014, 0, 0))]
    tube(cord, pts, [0.01] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("DS_Shirt", shirt, M_SHIRT, 30)
new_obj("DS_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.012)
new_obj("DS_Stitching", stitch, M_STITCH, 40)
new_obj("DS_Tie", tie, M_TIE, 30, outward=True, thickness=0.018)
new_obj("DS_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.014)
new_obj("DS_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.024)
new_obj("DS_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("DS_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("DS_Medallion", medal_p, M_PEWTER, 32)
new_obj("DS_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("DS_Cord", cord, M_JOINT, 40)
new_obj("DS_Plates", plate, M_PLATE, 32)
new_obj("DS_Joints", joint, M_JOINT, 40)
new_obj("DS_Steel", steel, M_STEEL, 40)
new_obj("DS_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("DSCam", bpy.data.cameras.new("DSCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("DSSun", bpy.data.lights.new("DSSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("DSFill", bpy.data.lights.new("DSFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 150
fill.data.size = 7
fill.location = (-7, -8, 4.5)
fill.rotation_euler = (Vector((0, 0, 2.8)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
