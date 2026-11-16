# ---------------------------------------------------------------- head: a tall slab under a white top hat
# All five sheets and the original agree. Measured off the new turnaround (587 px = 6.39 units; 91.9 px/unit): hat
# top 6.39, brim 5.69, brows 5.44, eyes 5.28, nose tip 5.0, grin 4.49-4.95, chin 4.41; head half-width 0.28, hat
# half-width 0.27 at the brim and 0.305 at the top, brim half-width 0.38. The neck is fixed by the skeleton, so the
# head starts at 4.50 and its heights are 0.97 of the sheet's above that: hat top 6.42.
# Pieces: the face shell in two halves on a hairline centre seam, with the grin cut straight into it (no plate edge
# round the mouth) and the teeth set behind the opening; eyes under heavy slanted lids; thick black brows; a long
# nose; small ears; a black hair shell on the back and sides; the hat. All of it over a closed inner shell.
HEAD = [fb(4.50, 0.262, -0.27, 0.26), fb(4.56, 0.275, -0.288, 0.275), fb(5.00, 0.28, -0.30, 0.285), fb(5.40, 0.283, -0.30, 0.287),
        fb(5.74, 0.283, -0.30, 0.287)]
HEAD_N = 3.5
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.0015
CORE_IN = 0.008
BASE_Z, TOP_Z = 4.50, 5.74
MX, CX = 0.225, 0.25                 # half-width of the grin, and of the front panel it is cut in


def hp(th, z, eps=0.0):          # point on the head, th degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def th_of(x, z):                 # the column that is x out from the centre line at height z
    rx = interp(HEAD, z)[3]
    return math.degrees(math.asin(min(0.999, (min(abs(x), rx * 0.999) / rx) ** (HEAD_N / 2))))


def fnorm(x, z):
    return (surf(HEAD, x, z, 1.0) - surf(HEAD, x, z, 0.0)).normalized()


def zu(x):                       # upper lip: the grin's corners turn up
    return 5.005 + 0.06 * (x / MX) ** 2


def zl(x):                       # lower lip: two lobes of teeth hang down, the chin rising to a point between them
    t = abs(x) / MX
    if t <= 0.13:                                               # the narrow point of chin between the lobes
        return 4.975 - 0.15 * (t / 0.13)
    return 4.59 + 0.435 * (abs(t - 0.54) / 0.46) ** 2.6            # each lobe: a full, round-bottomed U


ZUP = [5.20, 5.30, 5.40, 5.50, 5.60, 5.74]


def col_zs(x):
    xx = min(MX, abs(x))
    lo, hi = zl(xx), zu(xx)
    return [BASE_Z, 4.56] + [4.56 + (lo - 4.56) * f for f in (0.33, 0.66, 1.0)] + [hi + (5.12 - hi) * f for f in (0.0, 0.5, 1.0)] + ZUP


plates = bmesh.new()
XF = [GAP, 0.015, 0.029, 0.045, 0.065, 0.09, 0.12, 0.15, 0.175, 0.195, 0.21, MX, 0.238, CX]
F = [0.0, 0.07, 0.14, 0.22, 0.30, 0.38, 0.46, 0.54, 0.62, 0.70, 0.78, 0.86, 0.93, 1.0]
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(surf(HEAD, s * x, z)) for z in col_zs(x)] for x in XF]
    for (xa, ca), (xb, cb) in zip(zip(XF, cols), zip(XF[1:], cols[1:])):
        for k in range(len(ca) - 1):
            if k == 4 and xa <= MX + 1e-9 and xb <= MX + 1e-9:
                continue                                         # the grin
            t.faces.new((ca[k], cb[k], cb[k + 1], ca[k + 1]))
    rows = []
    for z in col_zs(CX):
        t0 = th_of(CX, z)
        rows.append([hp(s * (t0 + (179.7 - t0) * f), z) for f in F])
    grid(t, rows)
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("AC_HeadPlates", plates, M_PLATE, 30, outward=True, thickness=-0.016)

# teeth: one white wall behind the grin, its big interlocking teeth marked by a zigzag and the gaps between them
teeth, dark = bmesh.new(), bmesh.new()
TX = [-MX - 0.012 + (2 * MX + 0.024) * i / 16 for i in range(17)]
grid(teeth, [[surf(HEAD, x, z, -0.0065) for x in TX] for z in (4.56, 4.72, 4.88, 5.04, 5.10)])
for sx_ in (-1, 1):                                             # the gaps between the long teeth in each lobe
    for t_, lean in ((0.22, -0.012), (0.40, -0.006), (0.58, 0.004), (0.76, 0.012)):
        x0 = sx_ * t_ * MX
        x1 = x0 + sx_ * lean
        tube(dark, [surf(HEAD, x0 + (x1 - x0) * f, zu(x0) + (zl(x1) - zu(x0)) * f, -0.004) for f in (0.02, 0.35, 0.7, 0.98)], [0.0045] * 4, seg=4)
LX = [-MX + 2 * MX * i / 48 for i in range(49)]
for edge, r_ in ((zu, 0.009), (zl, 0.009)):                      # the dark lip line round the grin
    tube(dark, [surf(HEAD, x, edge(x), 0.001) for x in LX], [0.004] + [r_] * 47 + [0.004], seg=6)
tag(teeth, 'joint_head')
new_obj("AC_Teeth", teeth, M_FANG, 50, outward=True)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=40, power=HEAD_N)
tag(core, 'joint_head')
new_obj("AC_HeadCore", core, M_JOINT, 30)
loft(plate, [fb(4.44, 0.15, -0.15, 0.13), fb(4.455, 0.21, -0.24, 0.21), fb(4.5005, 0.2615, -0.2695, 0.2595)], seg=32,
     caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.01, 4.34), (0, 0, 1), [(0.0, 0.11), (0.03, 0.14), (0.05, 0.14), (0.058, 0.118), (0.066, 0.152), (0.088, 0.152),
                                           (0.096, 0.124), (0.104, 0.156), (0.128, 0.156), (0.136, 0.13), (0.15, 0.13)], seg=24)

# eyes: sunk balls with brown irises, half shut under heavy lids that slant down to the nose
eyes, iris, pupil, lids = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    ex, ez = s * 0.118, 5.34
    p = surf(HEAD, ex, ez, 0.0)
    n = fnorm(ex, ez)
    e_out = Vector((0, 0, 1)).cross(n).normalized()
    if e_out.x * s < 0:
        e_out = -e_out
    eu = Vector((0, 0, 1))
    EM = Matrix((e_out, eu, n)).transposed().to_4x4()
    c = p - n * 0.042
    bmesh.ops.create_uvsphere(eyes, u_segments=18, v_segments=12, radius=0.068, matrix=Matrix.Translation(c))
    d = (n * 0.97 - e_out * 0.10 - eu * 0.14).normalized()
    puck(iris, c + d * 0.067, d, 0.03, 0.004, seg=16)
    puck(pupil, c + d * 0.069, d, 0.014, 0.004, seg=12)
    ang = math.radians(20)
    nl = (eu * math.cos(ang) - e_out * math.sin(ang)).normalized()
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=24, v_segments=12, radius=1.0,
                              matrix=Matrix.Translation(p + eu * 0.01) @ EM @ Matrix.Diagonal((0.09, 0.07, 0.028, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p + eu * 0.022, plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.006, plane_no=n, clear_inner=True)
    merge(lids, t)
    e_edge = n.cross(nl).normalized()
    lash = [p + eu * 0.02 + e_edge * (0.085 * math.cos(math.radians(a))) + n * (0.002 + 0.032 * math.sin(math.radians(a)) ** 0.8)
            for a in range(0, 181, 12)]
    tube(dark, lash, [0.004 + 0.004 * math.sin(math.radians(a)) for a in range(0, 181, 12)], seg=5)
    bag = [surf(HEAD, s * (0.04 + 0.16 * i / 8), 5.285 - 0.03 * math.sin(math.pi * i / 8) + 0.025 * i / 8, 0.001) for i in range(9)]
    tube(dark, bag, [0.002 + 0.0025 * math.sin(math.pi * i / 8) for i in range(9)], seg=4)
# brows: thick black arches, pressed low over the nose
brow_bm = bmesh.new()
for s in (-1, 1):
    bp = [(0.03, 5.44), (0.075, 5.505), (0.135, 5.55), (0.20, 5.545), (0.25, 5.49)]
    tube(brow_bm, [surf(HEAD, s * x, z, 0.004) for x, z in bp], [0.016, 0.034, 0.04, 0.032, 0.01], seg=10)
    pts = [(0.075, 5.14), (0.13, 5.115), (0.185, 5.085), (0.228, 5.07)]          # crease from the nose to the corner of the grin
    tube(dark, [surf(HEAD, s * x, z, 0.0005) for x, z in pts], [0.002, 0.005, 0.005, 0.002], seg=5)
for _b in (eyes, iris, pupil, dark, lids, brow_bm):
    tag(_b, 'joint_head')
new_obj("AC_Eyes", eyes, M_EYE, 60)
new_obj("AC_Iris", iris, M_IRISRING, 40)
new_obj("AC_Pupil", pupil, M_IRIS, 40)
new_obj("AC_EyeLines", dark, M_BROW, 50)
new_obj("AC_Lids", lids, M_LID, 50)
new_obj("AC_Brows", brow_bm, M_HAIR, 60)

# nose: a long hard-edged wedge with flat faces: a narrow bridge between the brows widening down to a blunt end
# with a flat underside. Robots do not have round noses.
nose = bmesh.new()
nv = {k: nose.verts.new(surf(HEAD, x, z, e)) for k, (x, z, e) in {
    'al': (0.02, 5.44, 0.003),
    'ar': (-0.02, 5.44, 0.003),
    'ml': (0.03, 5.28, 0.052),
    'mr': (-0.03, 5.28, 0.052),
    'tl': (0.046, 5.115, 0.125),
    'tr': (-0.046, 5.115, 0.125),
    'ul': (0.046, 5.065, 0.098),
    'ur': (-0.046, 5.065, 0.098),
    'sl': (0.05, 5.33, 0.0),
    'sr': (-0.05, 5.33, 0.0),
    'bl': (0.088, 5.06, -0.002),
    'br': (-0.088, 5.06, -0.002),
}.items()}
for f in (('al', 'ar', 'mr', 'ml'), ('ml', 'mr', 'tr', 'tl'), ('tl', 'tr', 'ur', 'ul'), ('ul', 'ur', 'br', 'bl'),
          ('al', 'ml', 'sl'), ('ar', 'sr', 'mr'), ('ml', 'tl', 'bl', 'sl'), ('mr', 'sr', 'br', 'tr'), ('tl', 'ul', 'bl'), ('tr', 'br', 'ur')):
    nose.faces.new([nv[k] for k in f])
bmesh.ops.recalc_face_normals(nose, faces=nose.faces)
tag(nose, 'joint_head')
_o = new_obj("AC_Nose", nose, M_PLATE, 25)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.008, 2, 'ANGLE', math.radians(25)

# ears: a small ringed ear on each side, level with the nose
ears = bmesh.new()
for a in (-4, 184):
    p, n = ring_pt(HEAD, 5.17, a, 0.0)
    lathe(ears, p, n, [(0.0, 0.078), (0.024, 0.078), (0.036, 0.066), (0.036, 0.05), (0.02, 0.045), (0.02, 0.026), (0.03, 0.02), (0.034, 0.001)], seg=20)
tag(ears, 'joint_head')
new_obj("AC_Ears", ears, M_PLATE, 40)


# hair: a black shell slicked back over the sides and the back of the head, from under the hat down past the ears
def hair_bottom(th):
    a = abs(th)
    if a <= 84:                                                 # the sideburn, coming down to a point in front of the ear
        return 5.02 + 0.225 * min(1.0, abs(a - 77) / 7.0) ** 1.5
    if a <= 106:
        return 5.245
    if a <= 128:
        t = (a - 106) / 22.0
        return 5.245 - 0.265 * t * t * (3 - 2 * t)
    return 4.98


hair = bmesh.new()
for s in (1, -1):
    HT = [70 + (180 - 70) * i / 44 for i in range(45)]
    grid(hair, [[hp(s * th, hair_bottom(th) + (TOP_Z - hair_bottom(th)) * f, 0.014) for th in HT] for f in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)])
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0015)
bmesh.ops.recalc_face_normals(hair, faces=hair.faces)
if sum(f.normal.dot(f.calc_center_median() - Vector((0, 0, 5.4))) for f in hair.faces) < 0:
    bmesh.ops.reverse_faces(hair, faces=hair.faces)
tag(hair, 'joint_head')
_h = new_obj("AC_Hair", hair, M_HAIR, 40)
_sol = _h.modifiers.new("Cloth thickness", 'SOLIDIFY')
_sol.thickness, _sol.offset = 0.014, -1.0
strand = bmesh.new()
for s in (1, -1):
    for th in range(80, 181, 9):
        hb = hair_bottom(th)
        tube(strand, [hp(s * th, hb + (TOP_Z - hb) * f, 0.014) for f in (0.04, 0.3, 0.6, 0.95)], [0.004, 0.008, 0.008, 0.005], seg=5)
tag(strand, 'joint_head')
new_obj("AC_HairStrands", strand, M_HAIR, 60)

# hat: a white top hat. A brim all round, a crown flaring a little toward its flat top, a red cross on the front.
hat, cross = bmesh.new(), bmesh.new()
HY = -0.008
BY = -0.045                                                     # the brim reaches further forward than back, and barely past the sides
loft(hat, [(5.705, 0, BY, 0.30, 0.37), (5.715, 0, BY, 0.33, 0.405), (5.745, 0, BY, 0.335, 0.41), (5.765, 0, BY, 0.325, 0.395), (5.775, 0, BY, 0.29, 0.35)], seg=40, power=2.2)
CROWN = [(5.765, 0, HY, 0.284, 0.318), (5.81, 0, HY, 0.28, 0.314), (6.10, 0, HY, 0.29, 0.325), (6.385, 0, HY, 0.30, 0.335),
         (6.41, 0, HY, 0.293, 0.328), (6.42, 0, HY, 0.265, 0.30)]
SHAPE[id(CROWN)] = 2.2
loft(hat, CROWN, seg=40, power=2.2)
cz_ = 6.15
cp = surf(CROWN, 0.0, cz_, 0.0)
cn = fnorm(0.0, 5.3)
slope_ = (surf(CROWN, 0.0, cz_ + 0.1).y - surf(CROWN, 0.0, cz_ - 0.1).y) / 0.2
cm = Matrix.Rotation(-math.atan(slope_), 4, 'X')
cm.translation = cp + Vector((0, -0.004, 0))
rbox(cross, cm, (0.075, 0.024, 0.25), 0.006, 1)
rbox(cross, cm, (0.235, 0.024, 0.075), 0.006, 1)
for a in (60, 120, 240, 300):                                    # seam rivets up the crown
    for z in (5.85, 6.05, 6.25):
        q, qn = ring_pt(CROWN, z, a, 0.0)
        puck(hat, q, qn, 0.009, 0.01, seg=6)
tag(hat, 'joint_head')
tag(cross, 'joint_head')
new_obj("AC_Hat", hat, M_HAT, 35)
new_obj("AC_HatCross", cross, M_BOW, 40)

# rivets
for x, z in ((0.03, 5.64), (-0.03, 5.64), (0.25, 5.38), (-0.25, 5.38), (0.25, 5.62), (-0.25, 5.62)):
    puck(plate, surf(HEAD, x, z, 0.0), fnorm(x, z), 0.01, 0.011, seg=6)
for z in (4.62, 4.82):
    for a in (82, 98):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.01, 0.011, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

