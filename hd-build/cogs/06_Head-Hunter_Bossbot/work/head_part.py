
# ---------------------------------------------------------------- head: a heavy block, wide at the jaw, narrow at the crown
# HEAD is the outer surface (front view half-widths, side view front and back), a squared-off section. Pieces: the
# face shell in two halves on a hairline centre seam, each with its eye slot and the crease from beside the nose to
# the mouth corner; the jaw plate; the frown, a slot between them; back plates; the flat-topped hair shell with its
# widow's peak; ringed ear discs; nose and brows. All over a closed inner shell.
HEAD = [fb(6.73, 0.32, -0.41, 0.22), fb(6.85, 0.34, -0.40, 0.21), fb(7.00, 0.345, -0.385, 0.19),
        fb(7.15, 0.32, -0.355, 0.16), fb(7.30, 0.285, -0.32, 0.13), fb(7.45, 0.25, -0.285, 0.09),
        fb(7.50, 0.24, -0.27, 0.08)]
HEAD_N = 3.0
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.0015
CORE_IN = 0.012
BASE_Z, TOP_Z, FA = 6.73, 7.50, 100.0
MX, MZ0, MZ1 = 0.29, 6.965, 6.86          # mouth corner distance out; height of the frown at the centre and at the corners


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def XR(th):                      # how far out from the centre line a column is (at cheek height)
    return 0.345 * sq(math.sin(math.radians(min(abs(th), 90.0))), HEAD_N)


def th_of(x, z):                 # the column that is x out from the centre line at height z
    return math.degrees(math.asin(min(1.0, (min(0.999, x / interp(HEAD, z)[3])) ** (HEAD_N / 2.0))))


def agap(z, d=GAP):
    return math.degrees(d / interp(HEAD, z)[3])


def frown(X):
    return MZ0 - (MZ0 - MZ1) * min(1.0, X / MX) ** 2


def lip(X):                      # half-height of the mouth slot: widest in the middle, a hairline from the corners on
    return GAP + 0.012 * math.sqrt(max(0.0, 1 - (X / MX) ** 2))


def crease(X):                   # from beside the nose down and out to the mouth corner
    return 7.20 if X < 0.06 else (7.20 - 0.30 * (X - 0.06) / 0.21 if X < 0.27 else 6.90)


def crease_gap(X):
    return 0.002 * min(1.0, (X - 0.06) / 0.02, (0.27 - X) / 0.02) if 0.06 < X < 0.27 else 0.0


EX, EZ, EA, EB = 0.14, 7.265, 0.042, 0.02


def eye(X):                      # (below centre, above centre): the brow hangs over the top of the eye
    t = (X - EX) / EA
    return (EB * math.sqrt(1 - t * t), 0.45 * EB * math.sqrt(1 - t * t)) if abs(t) < 1 else (0.0, 0.0)


def bulge(X, z):
    brow = 0.022 * math.exp(-((X - 0.11) / 0.12) ** 2 - ((z - 7.335) / 0.035) ** 2)
    cheek = 0.012 * math.exp(-((X - 0.24) / 0.09) ** 2 - ((z - 7.05) / 0.08) ** 2)
    return brow + cheek


PHI = [2.5 * i for i in range(41)]                               # 0 .. 100
BACK_PHI = [FA + 5.0 * i for i in range(17)]
A_F, B_F, C_F = (0.0, 0.33, 0.66, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.2, 0.45, 0.75, 1.0)
CHIN_F = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def face_zs(th):
    X = XR(th)
    bot = frown(X) + lip(X)
    zc, gc = crease(X), crease_gap(X)
    el, eh = eye(X)
    return ([bot + (zc - gc - bot) * f for f in A_F] + [zc + gc + (EZ - el - zc - gc) * f for f in B_F] +
            [EZ + eh + (TOP_Z - EZ - eh) * f for f in C_F])


def chin_zs(th):
    X = XR(th)
    top = frown(X) - lip(X)
    return [BASE_Z + (top - BASE_Z) * f for f in CHIN_F]


plates = bmesh.new()
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(hp(s * max(th, agap(z)), z, bulge(XR(th), z))) for z in face_zs(th)] for th in PHI]
    for a, b in zip(cols, cols[1:]):
        for k in range(12):
            if k not in (3, 7):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0004)
    grid(plates, [[hp(s * max(th, agap(6.8)), chin_zs(th)[k]) for th in PHI] for k in range(len(CHIN_F))])
    BACK_Z = chin_zs(FA) + face_zs(FA)
    rows = []
    for z in BACK_Z:
        g = agap(z)
        rows.append([hp(s * a, z) for a in [BACK_PHI[0] + g] + BACK_PHI[1:-1] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("HH_HeadPlates", plates, M_PLATE, 55, outward=True, thickness=-0.022)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("HH_HeadCore", core, M_JOINT, 60)
loft(plate, [fb(6.68, 0.22, -0.30, 0.16), fb(6.69, 0.29, -0.38, 0.20), fb(6.7305, 0.3205, -0.4105, 0.2205)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.02, 6.42), (0, 0, 1), [(0.0, 0.20), (0.05, 0.24), (0.085, 0.24), (0.095, 0.205), (0.11, 0.255), (0.15, 0.255),
                                            (0.16, 0.215), (0.175, 0.26), (0.215, 0.26), (0.225, 0.22), (0.28, 0.22)], seg=28)

# eyes: small and dark under the brow
eyes, iris = bmesh.new(), bmesh.new()
for s in (-1, 1):
    rows = [[hp(s * th_of(EX + EA * 1.15 * (i / 4 - 1), z), z, bulge(EX, z) - 0.007) for i in range(9)] for z in (7.235, 7.255, 7.275, 7.295)]
    grid(eyes, rows)
    p, n = ring_pt(HEAD, 7.26, 270 + s * th_of(EX - 0.008, 7.26), bulge(EX, 7.26) - 0.006)
    puck(iris, p, n, 0.016, 0.005, seg=12)
tag(eyes, 'joint_head')
tag(iris, 'joint_head')
new_obj("HH_Eyes", eyes, M_EYE, 60, outward=True)
new_obj("HH_Iris", iris, M_IRIS, 40)

# brows: thick black bars slanting down to meet over the nose
brow = bmesh.new()
for s in (-1, 1):
    rows = [[], []]
    for i in range(9):
        tt = i / 8
        X = 0.015 + 0.20 * tt
        zc = 7.325 + 0.09 * tt
        hw_ = 0.024 - 0.012 * tt
        for k in (0, 1):
            z = zc + (hw_ if k else -hw_)
            rows[k].append(hp(s * th_of(X, z), z, bulge(X, z) + 0.008))
    grid(brow, rows)
tag(brow, 'joint_head')
new_obj("HH_Brows", brow, M_HAIR, 35, outward=True, thickness=-0.016)

# nose: a long wedge from between the brows to a blunt end, with a wing each side
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (7.33, 7.26, 7.18, 7.11, 7.07, 7.045, 7.03)
NR = (0.02, 0.026, 0.034, 0.044, 0.05, 0.045, 0.02)
tube(nose, [Vector((0, ny(z) + r * 0.35, z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.05, ny(7.065) + 0.03, 7.065)) @ Matrix.Diagonal((0.035, 0.04, 0.028, 1.0)))
tag(nose, 'joint_head')
new_obj("HH_Nose", nose, M_PLATE, 60)

# hair shell: flat on top, down to a peak over the nose, cut back past the ears and down the back of the head
def hairline(th):
    X = XR(th)
    a = abs(th)
    if a <= 80:
        return 7.36 + 0.09 * min(1.0, X / 0.20) ** 0.8
    if a <= 110:
        return 7.45 - 0.25 * (a - 80) / 30
    if a <= 165:
        return 7.20 - 0.30 * (a - 110) / 55
    return 6.90


hair = bmesh.new()
HT = [-180 + 5.0 * i for i in range(73)]
grid(hair, [[hp(th, hairline(th) + (TOP_Z - hairline(th)) * f, 0.012) for th in HT] for f in (0.0, 0.25, 0.5, 0.75, 1.0)])
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0003)
tag(hair, 'joint_head')
new_obj("HH_Hair", hair, M_HAIR, 50, outward=True, thickness=-0.012)
htop = bmesh.new()
htop.faces.new([htop.verts.new(hp(th, TOP_Z, 0.012)) for th in HT[:-1]])
tag(htop, 'joint_head')
new_obj("HH_HairTop", htop, M_HAIR, 50, outward='up', thickness=-0.012)

# ear discs: concentric rings on the jaw pivots
for a in (4, 176):
    p, n = ring_pt(HEAD, 7.12, a, 0.0)
    lathe(steel, p - n * 0.008, n, [(0.0, 0.09), (0.03, 0.09), (0.04, 0.08), (0.04, 0.067), (0.028, 0.064)], seg=24)
    lathe(pewter, p, n, [(0.02, 0.058), (0.042, 0.058), (0.047, 0.052), (0.047, 0.041), (0.02, 0.038)], seg=20)
    lathe(steel, p, n, [(0.02, 0.032), (0.05, 0.032), (0.054, 0.027), (0.054, 0.021), (0.02, 0.018)], seg=16)
    lathe(pewter, p, n, [(0.02, 0.015), (0.058, 0.013), (0.063, 0.006), (0.064, 0.001)], seg=12)
# rivets
for X, z in ((0.02, 6.80), (0.30, 6.80), (0.31, 6.93), (0.02, 7.40), (0.26, 7.15)):
    for s in (-1, 1):
        p, n = ring_pt(HEAD, z, 270 + s * th_of(X, z), bulge(X, z))
        puck(plate, p, n, 0.009, 0.01, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.008

loft(shirt, [fb(6.40, 0.40, -0.32, 0.40), fb(6.62, 0.36, -0.30, 0.36), fb(6.62, 0.34, -0.28, 0.34), fb(6.43, 0.35, -0.29, 0.35)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.04, s * 0.36, 6.56), (s * 0.10, s * 0.40, 6.42), (s * 0.22, s * 0.33, 6.25)], 0.02, nx=4)
patch(tie, SS, [(-0.10, 0.10, 6.50), (-0.13, 0.13, 6.40), (-0.08, 0.08, 6.27)], 0.045, nx=4)
patch(tie, SS, [(-0.07, 0.07, 6.28), (-0.12, 0.12, 5.95), (-0.13, 0.13, 5.78)], 0.012, nx=4)

panel(placket, TS, [(-0.03, 3.49), (0.20, 3.49), (0.20, 5.25), (0.07, 5.56), (-0.03, 5.56)], lambda x, z: 0.006, cuts=2)
for z in (4.90, 4.65, 4.38, 4.10, 3.82):
    p = surf(TS, 0.07, z, 0.02)
    nrm = (surf(TS, 0.07, z, 1.0) - surf(TS, 0.07, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.055), (0.012, 0.055), (0.025, 0.043), (0.025, 0.032), (0.015, 0.029)], seg=14)
    lathe(pewter, p, nrm, [(0.012, 0.029), (0.03, 0.02), (0.036, 0.005)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.064), (0.007, 0.064)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.175, 5.22 - (5.22 - 3.74) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.032) for x, z in edge], [SR] * len(edge), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.008)[0] for a in HB] for z in (3.486, 3.58, 3.69)])
tag(hemband, '@jacket')
new_obj("HH_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.02)
hs = [ring_pt(TS, 3.665, a, 0.033)[0] for a in HB]
tube(stitch, hs, [SR] * len(hs), seg=4)
for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):
    p, n = ring_pt(TS, 3.575, a, 0.028)
    lathe(pewter, p, n, [(0.0, 0.04), (0.013, 0.04), (0.025, 0.02), (0.03, 0.001)], seg=10)


def roll_lift(x, z):
    return 0.014 + 0.04 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.18)


def flat_lift(x, z):
    return 0.009


def studs(points, back):
    for x, z in points:
        p = surf(TS, x, z, 0.036, back=back)
        nrm = (surf(TS, x, z, 1.0, back=back) - surf(TS, x, z, 0.0, back=back)).normalized()
        lathe(pewter, p, nrm, [(0.0, 0.033), (0.013, 0.033), (0.024, 0.016), (0.028, 0.001)], seg=10)


g = front_gap
for s in (-1, 1):
    lapel = [(0.006, 5.59), (0.74, 5.90), (0.80, 6.02), (0.60, 6.22), (g(6.25), 6.25), (g(6.0), 6.0), (g(5.8), 5.8)]
    collar_front = [(g(6.25), 6.25), (0.60, 6.22), (0.84, 6.22), (0.87, 6.32), (0.66, 6.46), (g(6.46), 6.46)]
    flap = [(0.42, 4.25), (0.74, 4.25), (0.74, 4.07), (0.72, 4.04), (0.44, 4.04), (0.42, 4.07)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.042, inset=0.03, step=0.07, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)
    # studded straps: one down the front of each shoulder, one across each shoulder blade
    for outline, back, pts in (([(0.74, 6.30), (0.94, 6.33), (1.30, 6.03), (1.17, 5.92)], False, ((0.88, 6.27), (1.02, 6.15), (1.17, 6.02))),
                               ([(0.60, 6.34), (0.84, 6.38), (1.22, 5.86), (1.02, 5.72)], True, ((0.76, 6.30), (0.88, 6.14), (1.00, 5.98), (1.10, 5.83)))):
        o = [(s * x, z) for x, z in outline]
        panel(straps, TS, o, lambda x, z: 0.012, back=back, cuts=2)
        topstitch(stitch, TS, o, lambda x, z: 0.04, inset=0.026, back=back, step=0.07, radius=SR)
        studs([(s * x, z) for x, z in pts], back)
breast = [(0.47, 5.30), (0.93, 5.30), (0.93, 4.84), (0.88, 4.78), (0.52, 4.78), (0.47, 4.84)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)
panel(pockets, TS, [(0.47, 5.30), (0.93, 5.30), (0.93, 5.22), (0.47, 5.22)], lambda x, z: 0.022, cuts=1)
pocket_sq = [surf(TS, x, z, 0.04) for x, z in ((0.51, 5.29), (0.89, 5.29), (0.88, 5.38), (0.83, 5.36), (0.78, 5.47),
                                              (0.72, 5.37), (0.66, 5.48), (0.61, 5.37), (0.54, 5.42))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 5.30
slope = (surf(TS, 0, MZ + 0.12).y - surf(TS, 0, MZ - 0.12).y) / 0.24
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.05
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.23), (0.05, 0.23), (0.068, 0.214), (0.07, 0.184), (0.048, 0.18)], seg=28)
lathe(medal_p, mc, mn, [(0.046, 0.18), (0.056, 0.10), (0.06, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.27 + mn * 0.038
lathe(medal_p, mc + mt * 0.22 + mn * 0.035, mt, [(0.0, 0.038), (0.035, 0.046), (0.07, 0.032)], seg=10)
lathe(medal_p, bail - Vector((0.038, 0, 0)), (1, 0, 0), [(0.0, 0.035), (0.076, 0.035)], seg=10)
for pts in (((-0.044, 0.126), (0.044, 0.126), (0.03, 0.07), (-0.03, 0.07)),
            ((-0.03, 0.06), (0.03, 0.06), (0.068, -0.07), (0.0, -0.134), (-0.068, -0.07))):
    loop = [mc + mn * 0.064 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    for a, b in zip(loop, loop[1:] + loop[:1]):
        tube(medal_j, [a, b], [0.008, 0.008], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.32, 6.42, 0.03), surf(TS, s * (g(6.15) + 0.02), 6.15, 0.062), surf(TS, s * (g(5.9) + 0.018), 5.9, 0.062),
           surf(TS, s * 0.035, 5.68, 0.066), bail + Vector((s * 0.02, 0, 0))]
    tube(cord, pts, [0.014] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("HH_Shirt", shirt, M_SHIRT, 30)
new_obj("HH_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.018)
new_obj("HH_Stitching", stitch, M_STITCH, 40)
new_obj("HH_Tie", tie, M_TIE, 30, outward=True, thickness=0.027)
new_obj("HH_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.021)
new_obj("HH_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.036)
new_obj("HH_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("HH_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("HH_Medallion", medal_p, M_PEWTER, 32)
new_obj("HH_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("HH_Cord", cord, M_JOINT, 40)
new_obj("HH_Plates", plate, M_PLATE, 32)
new_obj("HH_Joints", joint, M_JOINT, 40)
new_obj("HH_Steel", steel, M_STEEL, 40)
new_obj("HH_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("HHCam", bpy.data.cameras.new("HHCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("HHSun", bpy.data.lights.new("HHSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("HHFill", bpy.data.lights.new("HHFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 230
fill.data.size = 9
fill.location = (-9, -10, 5.5)
fill.rotation_euler = (Vector((0, 0, 3.5)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
