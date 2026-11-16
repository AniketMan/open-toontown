# ---------------------------------------------------------------- head: a blunt cone with a flat top
# HEAD is the outer surface (front view half-widths, side view front and back). Pieces: the shell in two halves on a
# hairline seam, with the brow ridge worked into it, over a closed inner shell; the mouth cassette, two enormous
# lips; small deep-set eyes under slanted lids; nose; a ringed disc on a square plate at each ear.
HEAD = [fb(3.78, 0.50, -0.60, 0.30), fb(3.90, 0.505, -0.59, 0.30), fb(4.10, 0.475, -0.55, 0.28),
        fb(4.30, 0.43, -0.50, 0.25), fb(4.50, 0.36, -0.45, 0.20), fb(4.65, 0.29, -0.38, 0.15),
        fb(4.76, 0.20, -0.28, 0.11), fb(4.79, 0.17, -0.25, 0.10)]
HEAD_N = 2.3
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.002
CORE_IN = 0.015


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def th_of(x, z):
    return math.degrees(math.asin(min(1.0, (min(0.999, abs(x) / interp(HEAD, z)[3])) ** (HEAD_N / 2.0)))) * (1 if x >= 0 else -1)


def bulge(th, z):
    a = abs(th)
    brow = 0.05 * math.exp(-((a - 28) / 30) ** 2 - ((z - (4.60 + 0.0012 * a)) / 0.045) ** 2)
    cheek = 0.02 * math.exp(-((a - 55) / 25) ** 2 - ((z - 4.3) / 0.12) ** 2)
    return (brow + cheek) if a < 100 else 0.0


plates = bmesh.new()
HZ = [3.78, 3.84, 3.90, 4.00, 4.10, 4.20, 4.30, 4.40, 4.47, 4.53, 4.58, 4.62, 4.66, 4.71, 4.76, 4.79]
for s in (1, -1):
    rows = []
    for z in HZ:
        g = abs(th_of(GAP, z))
        rows.append([hp(s * a, z, bulge(a, z)) for a in [g] + [5.0 * i for i in range(1, 36)] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("BF_HeadPlates", plates, M_PLATE, 30, outward=True, thickness=-0.025)
core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("BF_HeadCore", core, M_JOINT, 60)
_z, _cx, _cy, _rx, _ry = HEAD[-1]
loft(plate, [(4.7905, _cx, _cy, _rx + 0.0005, _ry + 0.0005), (4.80, _cx, _cy, _rx * 0.6, _ry * 0.6), (4.803, _cx, _cy, 0.06, 0.06)], seg=32,
     caps=(False, True), power=HEAD_N)
loft(plate, [fb(3.72, 0.36, -0.44, 0.22), fb(3.73, 0.45, -0.53, 0.27), fb(3.7805, 0.5005, -0.6005, 0.3005)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.1, 3.52), (0, 0, 1), [(0.0, 0.30), (0.05, 0.345), (0.08, 0.345), (0.09, 0.30), (0.10, 0.36), (0.14, 0.36),
                                           (0.15, 0.31), (0.16, 0.365), (0.20, 0.365), (0.21, 0.32), (0.25, 0.32)], seg=28)

# lips: the mouth cassette is two great lips, the lower the bigger, meeting on a downturned line
LW = 0.31


def lip_top(x):
    t = abs(x) / LW
    return 4.375 - 0.295 * t ** 1.6 - 0.02 * math.exp(-(x / 0.03) ** 2)


def lip_mid(x):
    return 4.15 - 0.07 * (abs(x) / LW) ** 2


def lip_bot(x):
    return 3.815 + 0.265 * (abs(x) / LW) ** 2.2


lips = bmesh.new()
for lo_f, hi_f, amp in ((lip_mid, lip_top, 0.085), (lip_bot, lip_mid, 0.125)):
    rows = []
    for f in (0.0, 0.08, 0.2, 0.35, 0.5, 0.65, 0.8, 0.92, 1.0):
        row = []
        for i in range(41):
            x = LW * (i / 20 - 1)
            z = lo_f(x) + (hi_f(x) - lo_f(x)) * f
            lift = 0.004 + amp * math.sin(math.pi * f) ** 0.55 * math.sqrt(max(0.0, 1 - (x / LW) ** 4))
            row.append(surf(HEAD, x, z, lift))
        rows.append(row)
    grid(lips, rows)
tag(lips, 'joint_head')
new_obj("BF_Lips", lips, M_LIP, 60, outward=True, thickness=-0.02)

# eyes: small, deep-set, glaring from under slanted lids
eyes, iris, pupil, dark = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    ex, ez = s * 0.115, 4.553
    p = surf(HEAD, ex, ez, 0.0)
    n = (surf(HEAD, ex, ez, 1.0) - p).normalized()
    e_out = Vector((0, 0, 1)).cross(n).normalized()
    if e_out.x * s < 0:
        e_out = -e_out
    eu = n.cross(e_out).normalized()
    if eu.z < 0:
        eu = -eu
    EM = Matrix((e_out, eu, n)).transposed().to_4x4()
    c = p - n * 0.04
    bmesh.ops.create_uvsphere(eyes, u_segments=16, v_segments=10, radius=0.058, matrix=Matrix.Translation(c))
    d = (n * 0.97 - e_out * 0.12 - eu * 0.16).normalized()
    puck(iris, c + d * 0.057, d, 0.024, 0.004, seg=14)
    puck(pupil, c + d * 0.059, d, 0.011, 0.004, seg=10)
    ang = math.radians(22)
    nl = (eu * math.cos(ang) - e_out * math.sin(ang)).normalized()
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=20, v_segments=10, radius=1.0,
                              matrix=Matrix.Translation(p) @ EM @ Matrix.Diagonal((0.07, 0.058, 0.03, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - eu * 0.006, plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.008, plane_no=n, clear_inner=True)
    merge(plate, t)
    e_edge = n.cross(nl).normalized()
    lash = [p - eu * 0.008 + e_edge * (0.066 * math.cos(math.radians(a))) + n * (0.002 + 0.028 * math.sin(math.radians(a)) ** 0.8)
            for a in range(0, 181, 15)]
    tube(dark, lash, [0.004 + 0.004 * math.sin(math.radians(a)) for a in range(0, 181, 15)], seg=5)
for _b in (eyes, iris, pupil, dark):
    tag(_b, 'joint_head')
new_obj("BF_Eyes", eyes, M_EYE, 60)
new_obj("BF_Iris", iris, M_IRISRING, 40)
new_obj("BF_Pupil", pupil, M_IRIS, 40)
new_obj("BF_EyeLines", dark, M_BROW, 50)

# nose: short and broad, with a wing each side
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (4.60, 4.54, 4.48, 4.43, 4.40, 4.385)
NR = (0.03, 0.045, 0.062, 0.078, 0.07, 0.035)
ND = (0.0, 0.01, 0.03, 0.045, 0.04, 0.02)
tube(nose, [Vector((0, ny(z) - d + r * 0.4, z)) for z, r, d in zip(NZ, NR, ND)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.075, ny(4.41) + 0.005, 4.41)) @ Matrix.Diagonal((0.045, 0.05, 0.04, 1.0)))
tag(nose, 'joint_head')
new_obj("BF_Nose", nose, M_PLATE, 60)

# ear discs on square plates
for a in (8, 172):
    p, n = ring_pt(HEAD, 4.53, a, 0.0)
    rbox(plate, Matrix.Translation(p + n * 0.004) @ n.to_track_quat('Z', 'Y').to_matrix().to_4x4(), (0.13, 0.13, 0.016), 0.006, 1)
    lathe(steel, p + n * 0.01, n, [(0.0, 0.05), (0.014, 0.05), (0.02, 0.043), (0.02, 0.034), (0.012, 0.032)], seg=18)
    lathe(pewter, p + n * 0.01, n, [(0.008, 0.028), (0.024, 0.028), (0.028, 0.02), (0.03, 0.002)], seg=12)
for th, z in ((10, 3.83), (-10, 3.83), (60, 3.84), (-60, 3.84), (120, 3.84), (-120, 3.84), (172, 3.9), (-172, 3.9), (172, 4.4), (-172, 4.4),
              (8, 4.74), (-8, 4.74), (55, 4.1), (-55, 4.1)):
    p, n = ring_pt(HEAD, z, 270 + th, 0.0)
    puck(plate, p, n, 0.01, 0.01, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

