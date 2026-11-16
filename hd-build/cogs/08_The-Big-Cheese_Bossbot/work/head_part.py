# ---------------------------------------------------------------- head: a wedge of cheese standing on end
# A triangular slab: the front face is a tall triangle, the top is a ridge running front to back. HEAD is the outer
# surface (front view half-widths, side view front and back), a squared-off section. Pieces: the face in two halves
# on a hairline centre seam, each with its eye socket and the crease from the nose to the mouth corner; the jaw
# plate; the frown, a slot between them; side and back plates with the cheese holes cut through them; all over a
# closed inner shell, so a hole is a shallow cup, not a way in.
HEAD = [fb(7.28, 0.56, -0.42, 0.57), fb(7.35, 0.575, -0.42, 0.565), fb(7.60, 0.505, -0.37, 0.54),
        fb(8.00, 0.395, -0.30, 0.50), fb(8.40, 0.285, -0.24, 0.465), fb(8.80, 0.175, -0.18, 0.43),
        fb(9.20, 0.065, -0.12, 0.39), fb(9.38, 0.016, -0.10, 0.37)]
HEAD_N = 8.0
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.003
CORE_IN = 0.05
BASE_Z, TOP_Z = 7.28, 9.38
TH_C = 62.0                      # where the front face turns the corner into the side


def hwz(z):
    return interp(HEAD, z)[3]


def fp(u, z, eps=0.0):           # point on the front face: u = -1 .. 1 across it
    return surf(HEAD, u * 0.97 * hwz(z), z, eps)


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


MU = 0.90                        # mouth corners, as a fraction of the face's half-width


def frown(u):
    return 7.62 - 0.20 * min(1.0, abs(u) / MU) ** 2 * MU * MU / 0.81 * 0.81


def lip(u):
    return GAP + 0.022 * math.sqrt(max(0.0, 1 - (abs(u) / MU) ** 2))


def crease(u):
    a = abs(u)
    return 7.90 if a < 0.24 else (7.90 - 0.43 * (a - 0.24) / 0.64 if a < 0.88 else 7.47)


def crease_gap(u):
    a = abs(u)
    return 0.004 * min(1.0, (a - 0.24) / 0.06, (0.88 - a) / 0.06) if 0.24 < a < 0.88 else 0.0


EU, EZ, EA, EB_LO, EB_HI = 0.465, 8.08, 0.24, 0.078, 0.05


def eye(u):
    t = (abs(u) - EU) / EA
    return (EB_LO * math.sqrt(1 - t * t), EB_HI * math.sqrt(1 - t * t)) if abs(t) < 1 else (0.0, 0.0)


def bulge(u, z):
    a = abs(u)
    brow = 0.03 * math.exp(-((a - 0.5) / 0.4) ** 2 - ((z - 8.27) / 0.06) ** 2)
    lipb = 0.035 * math.exp(-((z - (frown(u) - 0.06)) / 0.05) ** 2) * max(0.0, 1 - (a / MU) ** 4)
    return brow + lipb


US = [0.04 * i for i in range(26)]
A_F, B_F, C_F = (0.0, 0.33, 0.66, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.1, 0.25, 0.45, 0.7, 1.0)
JAW_F = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)


def face_zs(u):
    bot = frown(u) + lip(u)
    zc, gc = max(crease(u), bot + 0.004), crease_gap(u)
    el, eh = eye(u)
    return ([bot + (zc - gc - bot) * f for f in A_F] + [zc + gc + (EZ - el - zc - gc) * f for f in B_F] +
            [EZ + eh + (TOP_Z - EZ - eh) * f for f in C_F])


def jaw_zs(u):
    top = frown(u) - lip(u)
    return [BASE_Z + (top - BASE_Z) * f for f in JAW_F]


plates = bmesh.new()
SIDE_TH = [TH_C + (180 - TH_C) * i / 14 for i in range(15)]
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(fp(s * max(u, GAP / hwz(z)), z, bulge(u, z))) for z in face_zs(u)] for u in US]
    for a, b in zip(cols, cols[1:]):
        for k in range(13):
            if k not in (3, 7):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0005)
    grid(plates, [[fp(s * max(u, GAP / hwz(7.4)), jaw_zs(u)[k], bulge(u, jaw_zs(u)[k])) for u in US] for k in range(len(JAW_F))])
    rows = []
    for z in jaw_zs(1.0) + face_zs(1.0):
        g = math.degrees(GAP / 0.45)
        rows.append([hp(s * a, z) for a in [TH_C + 0.8] + SIDE_TH[1:-1] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
head_plates = new_obj("TBC_HeadPlates", plates, M_PLATE, 50, outward=True, thickness=-0.03)

core = bmesh.new()
loft(core, [(z, cx, cy, max(0.004, rx - CORE_IN), ry - CORE_IN) for z, cx, cy, rx, ry in HEAD[:-1]], seg=40, power=HEAD_N)
tag(core, 'joint_head')
new_obj("TBC_HeadCore", core, M_CORE, 60)
loft(plate, [fb(7.20, 0.40, -0.30, 0.42), fb(7.215, 0.50, -0.38, 0.52), fb(7.2805, 0.5605, -0.4205, 0.5705)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, 0.05, 6.93), (0, 0, 1), [(0.0, 0.26), (0.06, 0.31), (0.10, 0.31), (0.115, 0.27), (0.13, 0.33), (0.18, 0.33),
                                           (0.195, 0.28), (0.21, 0.335), (0.26, 0.335), (0.275, 0.29), (0.33, 0.29)], seg=28)

# cheese holes: cut right through the shell plates (a cutter the plates subtract), showing the inner shell behind
cut = bmesh.new()


def hole(p, n, ra, rb, up=Vector((0, 0, 1))):
    x = up.cross(n).normalized()
    y = n.cross(x).normalized()
    m = Matrix((x, y, n)).transposed().to_4x4()
    m.translation = p
    bmesh.ops.create_cone(cut, cap_ends=True, segments=20, radius1=1.0, radius2=1.0, depth=1.0,
                          matrix=m @ Matrix.Diagonal((ra, rb, 0.16, 1.0)))


def side_pt(s, y, z):
    lo, hi = TH_C, 150.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if hp(mid, z).y < y:
            lo = mid
        else:
            hi = mid
    return ring_pt(HEAD, z, 270 + s * (lo + hi) / 2, 0.0)


for s in (1, -1):
    for y, z, ra, rb in ((0.10, 8.88, 0.10, 0.11), (0.24, 9.14, 0.055, 0.065), (0.35, 8.60, 0.06, 0.13), (0.36, 8.20, 0.05, 0.10),
                         (0.12, 8.00, 0.10, 0.12), (0.36, 7.62, 0.08, 0.15)):
        p, n = side_pt(s, y + (0.03 if s < 0 else 0.0), z - (0.06 if s < 0 else 0.0))
        hole(p, n, ra, rb)
for x, z, ra, rb in ((0.12, 8.80, 0.07, 0.11), (-0.16, 8.25, 0.09, 0.12), (0.2, 7.75, 0.10, 0.14), (-0.05, 9.05, 0.035, 0.06)):
    p, n = ring_pt(HEAD, z, 90 - math.degrees(math.asin(max(-0.95, min(0.95, x / hwz(z)))) * 0.3), 0.0)
    p = surf(HEAD, x, z, 0.0, back=True)
    hole(p, Vector((0, 1, 0)), ra, rb)
for u, z, ra, rb in ((0.25, 8.98, 0.045, 0.085), (-0.45, 8.72, 0.05, 0.09)):
    p = fp(u, z)
    hole(p, (fp(u, z, 1.0) - p).normalized(), ra, rb)
cutter = new_obj("TBC_HoleCutter", cut, M_CORE, 60)
cutter.hide_render = True
cutter.hide_viewport = True
cutter.display_type = 'WIRE'
bo = head_plates.modifiers.new("Cheese holes", 'BOOLEAN')
bo.operation = 'DIFFERENCE'
bo.object = cutter
bo.solver = 'EXACT'

# eyes: big balls in the sockets, yellow-green iris, dark pupil
eyes, iris, pupil = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    p = fp(s * EU, EZ)
    n = (fp(s * EU, EZ, 1.0) - p).normalized()
    c = p - n * 0.085
    bmesh.ops.create_uvsphere(eyes, u_segments=18, v_segments=10, radius=0.105, matrix=Matrix.Translation(c))
    d = (n * 0.97 - Vector((s * 0.16, 0, 0.12))).normalized()
    puck(iris, c + d * 0.1035, d, 0.052, 0.006, seg=18)
    puck(pupil, c + d * 0.107, d, 0.027, 0.006, seg=14)
for _b in (eyes, iris, pupil):
    tag(_b, 'joint_head')
new_obj("TBC_Eyes", eyes, M_EYE, 60)
new_obj("TBC_Iris", iris, M_IRISRING, 40)
new_obj("TBC_Pupil", pupil, M_IRIS, 40)

# brows: heavy ridges slanting down to the nose
brow = bmesh.new()
for s in (-1, 1):
    rows = [[], []]
    for i in range(9):
        tt = i / 8
        u = 0.10 + 0.78 * tt
        zc = 8.255 + 0.15 * tt
        hh = 0.04 - 0.02 * tt
        for k in (0, 1):
            z = zc + (hh if k else -hh)
            rows[k].append(fp(s * u, z, bulge(u, z) + 0.012))
    grid(brow, rows)
tag(brow, 'joint_head')
new_obj("TBC_Brows", brow, M_BROW, 35, outward=True, thickness=-0.03)

# nose: a long ridge widening to a blunt end with a wing each side
nose = bmesh.new()
ny = lambda z: fp(0, z).y
NZ = (8.32, 8.20, 8.07, 7.95, 7.88, 7.84, 7.82)
NR = (0.025, 0.035, 0.05, 0.065, 0.075, 0.065, 0.03)
tube(nose, [Vector((0, ny(z) - r * 0.25, z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.07, ny(7.86) - 0.0, 7.86)) @ Matrix.Diagonal((0.045, 0.05, 0.038, 1.0)))
tag(nose, 'joint_head')
new_obj("TBC_Nose", nose, M_PLATE, 60)
for u, z in ((0.06, 7.33), (0.85, 7.34), (0.95, 7.52), (0.07, 8.45), (0.9, 8.0)):
    for s in (-1, 1):
        p = fp(s * u, z, bulge(u, z))
        puck(plate, p, (fp(s * u, z, 1.0) - fp(s * u, z, 0.0)).normalized(), 0.012, 0.012, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

