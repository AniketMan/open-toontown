# ---------------------------------------------------------------- head: a faceted mint block under a tall block of hair
# All five sheets and the original agree. Measured off the new turnaround (560 px = 7.9 units; 70.9 px/unit): chin
# 5.81, cheek corners 6.37 (half-width 0.705), eyes 6.91, reflector centre 7.47, hair top 7.9; chin and crown half-
# width 0.32. The neck is fixed by the skeleton, so everything is 0.08 higher here.
# Pieces: the shell in two halves on a hairline centre seam, the frown a slot cut straight into it (no plate edge
# round the mouth) with the jaw swelling below; a big wedge of a nose whose nostrils start the creases that frame
# the upper mouth; eyes under heavy lids; thick brows; ringed ears; the forehead reflector; the hair block.
# Rebuilt 2026-11-14 on the ORIGINAL head mesh's own vertices (14_Spin-Doctor_Lawbot_model.obj, group telemarketer),
# raised 0.12 to clear the collar: the face is a wedge thrust forward. Crown front -0.24, nose level -0.70, lip -0.73,
# then the jaw recedes to a chin at -0.335; jaw corners low and wide (0.70 at 6.285); temples 0.46; a small crown.
HEAD = [fb(5.72, 0.25, -0.335, 0.15), fb(5.80, 0.37, -0.39, 0.30), fb(6.285, 0.70, -0.64, 0.40), fb(6.47, 0.64, -0.73, 0.40),
        fb(6.74, 0.51, -0.66, 0.42), fb(6.876, 0.46, -0.70, 0.43), fb(7.30, 0.36, -0.49, 0.44), fb(7.75, 0.27, -0.24, 0.45)]
HEAD_N = 1.6
SHAPE[id(HEAD)] = HEAD_N
CORE_IN = 0.01
BASE_Z, TOP_Z = 5.72, 7.75
THM = 68.0
UP = Vector((0, 0, 1))


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def hn(th, z):
    return ring_pt(HEAD, z, 270 + th, 0.0)[1]


def zf(th):                      # the frown
    return 6.44 - 0.24 * (min(abs(th), THM) / THM) ** 2


def gap(th):
    t = min(abs(th), THM) / THM
    return 0.003 + 0.022 * (1 - t * t)


ZUP = [6.90, 7.10, 7.30, 7.52, 7.75]
LIP_IN = 0.04                        # how far the upper lip sits back from the plate round it


def za(th):                      # the edge of the upper lip: from each nostril out and down to the corner of the mouth
    a = min(abs(th), THM)
    if a <= 10:
        return 6.80
    return 6.80 - (6.80 - (zf(THM) + 0.012)) * ((a - 10) / (THM - 10)) ** 1.7


def col_zs(th):
    lo, hi = zf(th) - gap(th), zf(th) + gap(th)
    top = za(th)
    return ([BASE_Z, 5.80] + [5.80 + (lo - 5.80) * f for f in (0.33, 0.66, 1.0)] +
            [hi, (hi + top - 0.004) / 2, top - 0.004, top + 0.004, max(top + 0.02, 6.285), max(top + 0.04, 6.47)] + ZUP)


def swell(th, k):                # the jaw stands out under the frown; the upper lip is set back inside its edge, like a person's
    a = abs(th)
    if a >= THM:
        return 0.0
    if k < 5:
        return 0.03 * (1 - (a / THM) ** 2) * math.sin(math.pi * (k / 4.0) * 0.8)
    if k <= 7:
        return -LIP_IN * min(1.0, (THM - a) / 8.0)
    return 0.0


plates = bmesh.new()
TF = [0.3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, THM]
F = [0.0, 0.07, 0.14, 0.22, 0.30, 0.38, 0.46, 0.54, 0.62, 0.70, 0.78, 0.86, 0.93, 1.0]
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(hp(s * th, z, swell(th, k))) for k, z in enumerate(col_zs(th))] for th in TF]
    for (ta, ca), (tb, cb) in zip(zip(TF, cols), zip(TF[1:], cols[1:])):
        for k in range(len(ca) - 1):
            if k == 4 and tb <= THM - 1.0:
                continue                                         # the mouth slot
            t.faces.new((ca[k], cb[k], cb[k + 1], ca[k + 1]))
    grid(t, [[hp(s * (THM + (179.7 - THM) * f), z) for f in F] for z in col_zs(THM)])
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("SD_HeadPlates", plates, M_PLATE, 28, outward=True, thickness=-0.02)
core = bmesh.new()
loft(core, [(z, cx, cy, rx - min(0.065, rx * 0.4), ry - min(0.065, ry * 0.4)) for z, cx, cy, rx, ry in HEAD], seg=40, power=HEAD_N)
tag(core, 'joint_head')
new_obj("SD_HeadCore", core, M_JOINT, 30)
loft(plate, [fb(5.66, 0.14, -0.20, 0.08), fb(5.675, 0.20, -0.28, 0.12), fb(5.7205, 0.2495, -0.3345, 0.1495)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.06, 5.54), (0, 0, 1), [(0.0, 0.14), (0.03, 0.18), (0.055, 0.18), (0.064, 0.152), (0.073, 0.195), (0.098, 0.195),
                                           (0.107, 0.16), (0.116, 0.20), (0.142, 0.20), (0.151, 0.17), (0.19, 0.17)], seg=28)

eyes, iris, pupil, dark, lids, brow, nose = (bmesh.new() for _ in range(7))
for s in (-1, 1):
    eth, ez = s * 30.0, 7.06
    p, n = hp(eth, ez), hn(eth, ez)
    e_out = UP.cross(n).normalized()
    if e_out.x * s < 0:
        e_out = -e_out
    eu = n.cross(e_out).normalized()
    if eu.z < 0:
        eu = -eu
    EM = Matrix((e_out, eu, n)).transposed().to_4x4()
    c = p - n * 0.05
    bmesh.ops.create_uvsphere(eyes, u_segments=18, v_segments=12, radius=0.085, matrix=Matrix.Translation(c))
    d = (n * 0.97 - e_out * 0.12 - eu * 0.14).normalized()
    puck(iris, c + d * 0.084, d, 0.036, 0.004, seg=16)
    puck(pupil, c + d * 0.086, d, 0.017, 0.004, seg=12)
    ang = math.radians(16)
    nl = (eu * math.cos(ang) - e_out * math.sin(ang)).normalized()
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=22, v_segments=12, radius=1.0,
                              matrix=Matrix.Translation(p + eu * 0.01) @ EM @ Matrix.Diagonal((0.115, 0.092, 0.04, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p + eu * 0.012, plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.006, plane_no=n, clear_inner=True)
    merge(lids, t)
    e_edge = n.cross(nl).normalized()
    lash = [p + eu * 0.01 + e_edge * (0.108 * math.cos(math.radians(a))) + n * (0.002 + 0.038 * math.sin(math.radians(a)) ** 0.8) for a in range(0, 181, 15)]
    tube(dark, lash, [0.004 + 0.005 * math.sin(math.radians(a)) for a in range(0, 181, 15)], seg=5)
    tube(dark, [hp(s * (12 + 36 * i / 8), 6.97 - 0.04 * math.sin(math.pi * i / 8) + 0.03 * i / 8, 0.001) for i in range(9)],
         [0.002 + 0.003 * math.sin(math.pi * i / 8) for i in range(9)], seg=4)                      # the bag under the eye
    # brows: thick dark bars pressed down toward the nose
    tube(brow, [hp(s * th_, z_, 0.006) for th_, z_ in ((6, 7.15), (17, 7.20), (31, 7.24), (45, 7.235), (58, 7.18))], [0.02, 0.04, 0.046, 0.036, 0.012], seg=10)
    tube(dark, [hp(s * th_, za(th_), -0.005) for th_ in range(10, 69, 3)], [0.002] + [0.005] * 18 + [0.002], seg=5)   # the step round the upper lip
tube(dark, [hp(th_, zf(th_) + gap(th_) + 0.004, -LIP_IN * min(1.0, (THM - abs(th_)) / 8.0) + 0.001) for th_ in range(-68, 69, 4)], [0.004] + [0.012] * 33 + [0.004], seg=6)
# nose: a big angular wedge. A narrow bridge between the brows widens down to a broad blunt end with a flat underside.
nv = {k: nose.verts.new(q) for k, q in (
    ('al', hp(3, 7.18, 0.004)), ('ar', hp(-3, 7.18, 0.004)),
    ('ml', hp(5, 7.00, 0.07)), ('mr', hp(-5, 7.00, 0.07)),
    ('tl', hp(7, 6.87, 0.15)), ('tr', hp(-7, 6.87, 0.15)),
    ('ul', hp(7, 6.81, 0.12)), ('ur', hp(-7, 6.81, 0.12)),
    ('sl', hp(9, 7.05, 0.0)), ('sr', hp(-9, 7.05, 0.0)),
    ('bl', hp(14, 6.805, -0.002)), ('br', hp(-14, 6.805, -0.002)))}
for f in (('al', 'ar', 'mr', 'ml'), ('ml', 'mr', 'tr', 'tl'), ('tl', 'tr', 'ur', 'ul'), ('ul', 'ur', 'br', 'bl'),
          ('al', 'ml', 'sl'), ('ar', 'sr', 'mr'), ('ml', 'tl', 'bl', 'sl'), ('mr', 'sr', 'br', 'tr'), ('tl', 'ul', 'bl'), ('tr', 'br', 'ur')):
    nose.faces.new([nv[k] for k in f])
bmesh.ops.recalc_face_normals(nose, faces=nose.faces)
ears = bmesh.new()
for a in (-14, 194):
    p, n = ring_pt(HEAD, 6.82, a, 0.0)
    lathe(ears, p + n * 0.05, n, [(0.0, 0.10), (0.03, 0.10), (0.045, 0.086), (0.045, 0.066), (0.028, 0.06), (0.028, 0.036), (0.04, 0.03), (0.045, 0.001)], seg=22)
for _b in (eyes, iris, pupil, dark, lids, brow, nose, ears):
    tag(_b, 'joint_head')
new_obj("SD_Eyes", eyes, M_EYE, 60)
new_obj("SD_Iris", iris, M_IRISRING, 40)
new_obj("SD_Pupil", pupil, M_IRIS, 40)
new_obj("SD_EyeLines", dark, M_BROW, 50)
new_obj("SD_Lids", lids, M_LID, 50)
new_obj("SD_Brows", brow, M_HAIR, 60)
_o = new_obj("SD_Nose", nose, M_PLATE, 25)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.012, 2, 'ANGLE', math.radians(25)
new_obj("SD_Ears", ears, M_PLATE, 40)

# forehead reflector: a dished steel mirror with a dark boss, on a short mount
refl, boss = bmesh.new(), bmesh.new()
rp, rn = hp(0, 7.58), hn(0, 7.58)
rn = (Vector((0, rn.y, 0)).normalized() + Vector((0, 0, 0.2))).normalized()
lathe(steel, rp - rn * 0.01, rn, [(0.0, 0.07), (0.05, 0.07), (0.06, 0.05)], seg=14)                # mount
lathe(refl, rp + rn * 0.05, rn, [(0.0, 0.21), (0.014, 0.245), (0.045, 0.25), (0.056, 0.238), (0.05, 0.21), (0.032, 0.12), (0.026, 0.055)], seg=36)
lathe(boss, rp + rn * 0.072, rn, [(0.0, 0.058), (0.022, 0.058), (0.034, 0.04), (0.036, 0.001)], seg=18)
tag(refl, 'joint_head')
tag(boss, 'joint_head')
new_obj("SD_Reflector", refl, M_MIRROR, 35)
new_obj("SD_ReflectorBoss", boss, M_IRIS, 40)

# hair: a tall brown block. It covers the crown, the back and the sides down to the ears, with a hairline across the
# forehead behind the reflector, and rises past the crown, flaring a little to a flat top.
HTOP = [fb(7.75, 0.31, -0.29, 0.49), fb(7.86, 0.30, -0.34, 0.50), fb(7.96, 0.28, -0.345, 0.49), fb(7.995, 0.25, -0.31, 0.47),
        (8.0, 0.0, 0.08, 0.02, 0.02)]
SHAPE[id(HTOP)] = 2.2


def hairline(th):
    a = abs(th)
    sm = lambda t: t * t * (3 - 2 * t)
    if a <= 35:
        return 7.52 - 0.10 * sm(a / 35.0)
    if a <= 66:
        return 7.42 - 0.24 * sm((a - 35) / 31.0)
    if a <= 84:                                                 # down the side of the face in front of the ear
        return 7.18 - 0.60 * sm((a - 66) / 18.0)
    return 6.58


def hair_pt(th, z):
    if z <= TOP_Z:
        return hp(th, z, 0.035 + 0.03 * max(0.0, min(1.0, (7.0 - z) / 0.5)))       # it stands a little off the head lower down
    return ring_pt(HTOP, z, 270 + th)[0]


hair = bmesh.new()
HT = [-180 + 4 * i for i in range(90)]
HF = [0.0, 0.1, 0.2, 0.32, 0.45, 0.58, 0.7, 0.8, 0.88, 0.94, 0.985, 1.0]
grid(hair, [[hair_pt(th, hairline(th) + (8.0 - hairline(th)) * f) for th in HT] for f in HF], wrap=True)
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.002)
bmesh.ops.recalc_face_normals(hair, faces=hair.faces)
if sum(f.normal.dot(f.calc_center_median() - Vector((0, 0, 7.2))) for f in hair.faces) < 0:
    bmesh.ops.reverse_faces(hair, faces=hair.faces)
tag(hair, 'joint_head')
_h = new_obj("SD_Hair", hair, M_HAIR, 35)
_sol = _h.modifiers.new("Cloth thickness", 'SOLIDIFY')
_sol.thickness, _sol.offset = 0.035, -1.0
strand = bmesh.new()
for th in range(-176, 180, 9):
    hl = hairline(th)
    tube(strand, [hair_pt(th, hl + (7.97 - hl) * f) for f in (0.03, 0.2, 0.4, 0.6, 0.8, 0.96)], [0.005, 0.011, 0.012, 0.012, 0.011, 0.005], seg=5)
tag(strand, 'joint_head')
new_obj("SD_HairStrands", strand, M_HAIR, 60)

# rivets
for th_, z_ in ((8, 5.95), (-8, 5.95), (76, 6.50), (-76, 6.50), (78, 6.20), (-78, 6.20), (45, 5.95), (-45, 5.95)):
    puck(plate, hp(th_, z_), hn(th_, z_), 0.013, 0.014, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

