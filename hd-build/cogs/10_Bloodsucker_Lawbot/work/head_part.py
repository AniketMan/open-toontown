# ---------------------------------------------------------------- head: a tall slab with rounded corners
# Measured off the new turnaround (572 px = 6.19 game units): chin 4.57, mouth 4.75-4.95, nose tip 5.14, ears 5.2,
# eyes 5.50, hairline 5.84 with a widow's peak down to 5.62, top of the pompadour 6.19. Half-width 0.235 at the
# chin, 0.30 at the hairline. Pieces: the shell in two halves on a hairline centre seam; the mouth cassette, a
# proud plate with the mouth opening cut in it, fangs hanging from its upper jaw; eyes under slanted purple lids
# and raised brow ridges; a long hooked nose; disc ears; the pompadour shell. All of it over a closed inner shell.
HEAD = [fb(4.56, 0.235, -0.27, 0.24), fb(4.62, 0.245, -0.285, 0.25), fb(5.00, 0.26, -0.30, 0.26),
        fb(5.40, 0.28, -0.31, 0.275), fb(5.75, 0.30, -0.315, 0.29), fb(5.92, 0.30, -0.30, 0.29)]
HEAD_N = 3.5
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.0015
CORE_IN = 0.008
BASE_Z, TOP_Z = 4.56, 5.92
CX, CZ = 0.215, 5.03                 # how far out the lower jaw's swell runs
MX = 0.165                           # half-width of the mouth opening
CAS_LIFT = 0.004


def hp(th, z, eps=0.0):          # point on the head, th degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def th_of(x, z):                 # the column that is x out from the centre line at height z
    rx = interp(HEAD, z)[3]
    return math.degrees(math.asin(min(0.999, (min(abs(x), rx * 0.999) / rx) ** (HEAD_N / 2))))


def fnorm(x, z):
    return (surf(HEAD, x, z, 1.0) - surf(HEAD, x, z, 0.0)).normalized()


# The face is one continuous shell in two halves (hairline seam down the centre). The mouth is an opening cut in it,
# between the upper lip and the domed lower jaw: no separate plate, so there is no edge round the mouth.
def zu(x):
    return 4.955 - 0.02 * (x / MX) ** 2


def zl(x):
    return 4.875 - 0.13 * (abs(x) / MX) ** 2


ZUP = [5.12, 5.22, 5.32, 5.42, 5.52, 5.62, 5.72, 5.82, 5.92]


def col_zs(x):
    xx = min(MX, abs(x))
    lo, hi = zl(xx), zu(xx)
    return [BASE_Z + (lo - BASE_Z) * f for f in (0.0, 0.3, 0.6, 0.85, 1.0)] + [hi + (5.03 - hi) * f for f in (0.0, 0.5, 1.0)] + ZUP


def dome(x, z, k):               # the lower jaw swells out under the mouth
    if k >= 5 or abs(x) >= CX:
        return 0.0
    return 0.022 * (1 - (x / CX) ** 2) * math.sin(math.pi * min(1.0, (z - BASE_Z) / (zl(min(MX, abs(x))) - BASE_Z)) * 0.75)


plates = bmesh.new()
XF = [GAP, 0.02, 0.045, 0.07, 0.095, 0.12, 0.145, MX, 0.185, 0.20, CX]
F = [0.0, 0.07, 0.14, 0.22, 0.30, 0.38, 0.46, 0.54, 0.62, 0.70, 0.78, 0.86, 0.93, 1.0]
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(surf(HEAD, s * x, z, dome(x, z, k))) for k, z in enumerate(col_zs(x))] for x in XF]
    for (xa, ca), (xb, cb) in zip(zip(XF, cols), zip(XF[1:], cols[1:])):
        for k in range(len(ca) - 1):
            if k == 4 and xa <= MX + 1e-9 and xb <= MX + 1e-9:
                continue                                         # the mouth opening
            t.faces.new((ca[k], cb[k], cb[k + 1], ca[k + 1]))
    rows = []
    for z in col_zs(CX):
        t0 = th_of(CX, z)
        rows.append([hp(s * (t0 + (179.7 - t0) * f), z) for f in F])
    grid(t, rows)
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("BS_HeadPlates", plates, M_PLATE, 30, outward=True, thickness=-0.016)

fang, mouth = bmesh.new(), bmesh.new()
for s in (-1, 1):
    x = s * 0.128
    top = surf(HEAD, x, zu(x) + 0.012, 0.004)
    tip = surf(HEAD, x * 0.97, 4.765, 0.012)
    tube(fang, [top, top + (tip - top) * 0.45, top + (tip - top) * 0.8, tip], [0.024, 0.02, 0.011, 0.002], seg=10)
    for xs in (0.04, 0.082):                                    # small teeth between the fangs
        t0_ = surf(HEAD, s * xs, zu(xs) + 0.01, 0.004)
        tube(fang, [t0_, t0_ - Vector((0, 0, 0.03)), t0_ - Vector((0, 0, 0.045))], [0.014, 0.012, 0.004], seg=8)
tag(fang, 'joint_head')
new_obj("BS_Fangs", fang, M_FANG, 50)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=40, power=HEAD_N)
tag(core, 'joint_head')
new_obj("BS_HeadCore", core, M_JOINT, 30)
# the underside and the layered neck bearing
loft(plate, [fb(4.50, 0.15, -0.15, 0.13), fb(4.515, 0.21, -0.24, 0.21), fb(4.5605, 0.2345, -0.2695, 0.2395)], seg=32,
     caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.01, 4.40), (0, 0, 1), [(0.0, 0.11), (0.03, 0.14), (0.05, 0.14), (0.058, 0.118), (0.066, 0.152), (0.088, 0.152),
                                           (0.096, 0.124), (0.104, 0.156), (0.128, 0.156), (0.136, 0.13), (0.15, 0.13)], seg=24)

# eyes: sunk balls glaring from under heavy purple lids that slant down to the nose
eyes, iris, pupil, dark, lids = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    ex, ez = s * 0.128, 5.50
    p = surf(HEAD, ex, ez, 0.0)
    n = fnorm(ex, ez)
    e_out = Vector((0, 0, 1)).cross(n).normalized()
    if e_out.x * s < 0:
        e_out = -e_out
    eu = n.cross(e_out).normalized()
    if eu.z < 0:
        eu = -eu
    EM = Matrix((e_out, eu, n)).transposed().to_4x4()
    c = p - n * 0.05
    bmesh.ops.create_uvsphere(eyes, u_segments=18, v_segments=12, radius=0.074, matrix=Matrix.Translation(c))
    d = (n * 0.96 - e_out * 0.16 - eu * 0.22).normalized()
    puck(iris, c + d * 0.073, d, 0.03, 0.004, seg=16)
    puck(pupil, c + d * 0.075, d, 0.014, 0.004, seg=12)
    ang = math.radians(24)
    nl = (eu * math.cos(ang) - e_out * math.sin(ang)).normalized()
    lid_c = p + eu * 0.012
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=24, v_segments=12, radius=1.0,
                              matrix=Matrix.Translation(lid_c) @ EM @ Matrix.Diagonal((0.108, 0.086, 0.04, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - eu * 0.002, plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.008, plane_no=n, clear_inner=True)
    merge(lids, t)
    e_edge = n.cross(nl).normalized()
    lash = [p - eu * 0.004 + e_edge * (0.102 * math.cos(math.radians(a))) + n * (0.002 + 0.036 * math.sin(math.radians(a)) ** 0.8)
            for a in range(0, 181, 12)]
    tube(dark, lash, [0.004 + 0.005 * math.sin(math.radians(a)) for a in range(0, 181, 12)], seg=5)
    bag = [surf(HEAD, s * (0.045 + 0.17 * i / 8), 5.44 - 0.035 * math.sin(math.pi * i / 8) + 0.03 * i / 8, 0.001) for i in range(9)]
    tube(dark, bag, [0.002 + 0.002 * math.sin(math.pi * i / 8) for i in range(9)], seg=4)      # line under the eye
for _b in (eyes, iris, pupil, dark, lids):
    tag(_b, 'joint_head')
new_obj("BS_Eyes", eyes, M_EYE, 60)
new_obj("BS_Iris", iris, M_IRISRING, 40)
new_obj("BS_Pupil", pupil, M_IRIS, 40)
new_obj("BS_EyeLines", dark, M_BROW, 50)
new_obj("BS_Lids", lids, M_LID, 50)

# brow ridges: raised from the shell, low over the nose and sweeping up to the temples
brow = bmesh.new()
for s in (-1, 1):
    pts = [(0.022, 5.555), (0.06, 5.605), (0.11, 5.65), (0.17, 5.675), (0.225, 5.672), (0.262, 5.645)]
    tube(brow, [surf(HEAD, s * x, z, 0.004) for x, z in pts], [0.016, 0.024, 0.026, 0.022, 0.016, 0.007], seg=10)
tag(brow, 'joint_head')
new_obj("BS_Brows", brow, M_PLATE, 60)

# nose: a long hard-edged wedge with flat faces: a narrow bridge between the brows widening down to a blunt end
# with a flat underside. Robots do not have round noses.
nose = bmesh.new()
nv = {k: nose.verts.new(surf(HEAD, x, z, e)) for k, (x, z, e) in {
    'al': (0.02, 5.6, 0.003),
    'ar': (-0.02, 5.6, 0.003),
    'ml': (0.03, 5.38, 0.058),
    'mr': (-0.03, 5.38, 0.058),
    'tl': (0.046, 5.18, 0.135),
    'tr': (-0.046, 5.18, 0.135),
    'ul': (0.046, 5.125, 0.105),
    'ur': (-0.046, 5.125, 0.105),
    'sl': (0.05, 5.45, 0.0),
    'sr': (-0.05, 5.45, 0.0),
    'bl': (0.088, 5.12, -0.002),
    'br': (-0.088, 5.12, -0.002),
}.items()}
for f in (('al', 'ar', 'mr', 'ml'), ('ml', 'mr', 'tr', 'tl'), ('tl', 'tr', 'ur', 'ul'), ('ul', 'ur', 'br', 'bl'),
          ('al', 'ml', 'sl'), ('ar', 'sr', 'mr'), ('ml', 'tl', 'bl', 'sl'), ('mr', 'sr', 'br', 'tr'), ('tl', 'ul', 'bl'), ('tr', 'br', 'ur')):
    nose.faces.new([nv[k] for k in f])
bmesh.ops.recalc_face_normals(nose, faces=nose.faces)
tag(nose, 'joint_head')
_o = new_obj("BS_Nose", nose, M_PLATE, 25)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.008, 2, 'ANGLE', math.radians(25)

# creases from the nose wings to the corners of the cassette, and a frown line each side of the bridge
crease = bmesh.new()
for s in (-1, 1):
    pts = [(0.085, 5.21), (0.13, 5.16), (0.175, 5.09), (0.21, 5.00), (0.228, 4.88)]
    tube(crease, [surf(HEAD, s * x, z, 0.0005) for x, z in pts], [0.002, 0.0045, 0.005, 0.0045, 0.002], seg=5)
    pts = [(0.03, 5.66), (0.024, 5.72), (0.03, 5.775)]
    tube(crease, [surf(HEAD, s * x, z, 0.0005) for x, z in pts], [0.002, 0.004, 0.002], seg=5)
tag(crease, 'joint_head')
new_obj("BS_Creases", crease, M_BROW, 50)

# ears: a ringed disc on each side, level with the end of the nose
ears = bmesh.new()
for a in (6, 174):
    p, n = ring_pt(HEAD, 5.22, a, 0.0)
    lathe(ears, p, n, [(0.0, 0.07), (0.022, 0.07), (0.032, 0.06), (0.032, 0.044), (0.02, 0.04), (0.02, 0.024), (0.03, 0.02), (0.033, 0.001)], seg=20)
    lathe(joint, p + n * 0.019, n, [(0.0, 0.041), (0.003, 0.041)], seg=14)
tag(ears, 'joint_head')
new_obj("BS_Ears", ears, M_PLATE, 40)

# hair: a pompadour shell. It starts at a widow's peak over the nose, runs back along the temples, comes down in
# front of each ear and covers the back of the head; on top it rises and swells out past the shell.
HTOP = [fb(5.92, 0.344, -0.344, 0.334), fb(6.00, 0.342, -0.345, 0.36), fb(6.07, 0.325, -0.325, 0.372), fb(6.13, 0.29, -0.28, 0.365),
        fb(6.17, 0.235, -0.215, 0.335), fb(6.195, 0.15, -0.12, 0.27), fb(6.205, 0.06, -0.03, 0.18), (6.208, 0.0, 0.07, 0.004, 0.004)]
SHAPE[id(HTOP)] = 3.0


def hairline(th):
    a = abs(th)
    x = interp(HEAD, 5.8)[3] * abs(math.sin(math.radians(a))) ** (2.0 / HEAD_N)
    sm = lambda t: t * t * (3 - 2 * t)
    if a <= 50:
        return 5.70 + 0.16 * min(1.0, x / 0.15)
    if a <= 90:
        return 5.86 - 0.54 * ((a - 50) / 40.0) ** 1.15
    if a <= 104:
        return 5.32
    if a <= 128:
        return 5.32 - 0.27 * sm((a - 104) / 24.0)
    return 5.05


def hair_pt(th, z):
    if z <= 5.92:
        t = max(0.0, min(1.0, (z - 5.3) / 0.62))
        return hp(th, z, 0.014 + 0.03 * t * t * (3 - 2 * t))
    return ring_pt(HTOP, z, 270 + th)[0]


hair = bmesh.new()
HT = [-180 + 4 * i for i in range(90)]
HF = [0.0, 0.07, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.74, 0.82, 0.89, 0.94, 0.975, 1.0]
grid(hair, [[hair_pt(th, hairline(th) + (6.208 - hairline(th)) * f) for th in HT] for f in HF], wrap=True)
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0015)
bmesh.ops.recalc_face_normals(hair, faces=hair.faces)
_c = Vector((0, 0, 5.6))
if sum(f.normal.dot(f.calc_center_median() - _c) for f in hair.faces) < 0:
    bmesh.ops.reverse_faces(hair, faces=hair.faces)
tag(hair, 'joint_head')
_h = new_obj("BS_Hair", hair, M_HAIR, 40)
_sol = _h.modifiers.new("Cloth thickness", 'SOLIDIFY')
_sol.thickness = 0.02
_sol.offset = -1.0
# comb lines: raised strands running from the hairline up and over
strand = bmesh.new()
for th in range(-176, 180, 8):
    hl = hairline(th)
    pts = [hair_pt(th, hl + (6.19 - hl) * f) for f in (0.03, 0.15, 0.3, 0.45, 0.6, 0.75, 0.88, 0.96)]
    tube(strand, pts, [0.004, 0.009, 0.01, 0.01, 0.01, 0.009, 0.007, 0.003], seg=5)
tag(strand, 'joint_head')
new_obj("BS_HairStrands", strand, M_HAIR, 60)

# rivets
for x, z in ((0.03, 5.80), (-0.03, 5.80), (0.03, 5.08), (-0.03, 5.08), (0.25, 5.45), (-0.25, 5.45), (0.232, 4.62), (-0.232, 4.62)):
    puck(plate, surf(HEAD, x, z, 0.0), fnorm(x, z), 0.011, 0.012, seg=6)
for z in (4.66, 4.84):
    for a in (82, 98):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.011, 0.012, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

