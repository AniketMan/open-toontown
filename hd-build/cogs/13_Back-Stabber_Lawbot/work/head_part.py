# ---------------------------------------------------------------- head: a tall cone with a red fin up its back
# The sheets and the original agree on the form. Measured off the new turnaround (540 px = 6.71 units; 80.5 px/unit):
# chin 4.66, frown 4.84-5.34, eyes 5.84, top of the shell 6.40, tip of the fin 6.71; half-width 0.335 at the base and
# 0.25 half way up; depth 0.56 at the base, the back upright and the front sloping back to the point.
# Pieces: the shell in two halves on a hairline centre seam, the frown a slot cut straight into it (no plate edge
# round the mouth) with the jaw swelling a little below; eyes under slanted lids and raised brow ridges; a crease
# from each eye to the corner of the mouth; a bolt on each side; the fin. All of it over a closed inner shell.
# Re-measured 2026-11-14: the base flares straight to the collar (half-width 0.34, front -0.36, back 0.28); the back is
# upright to 5.63 and then the shell slopes in under the fin, ending at 6.32; the fin fills the back-top behind it.
HEAD = [fb(4.69, 0.34, -0.36, 0.28), fb(4.76, 0.34, -0.355, 0.28), fb(5.10, 0.295, -0.30, 0.28), fb(5.50, 0.245, -0.23, 0.28),
        fb(5.63, 0.225, -0.20, 0.28), fb(5.80, 0.195, -0.16, 0.19), fb(6.00, 0.155, -0.115, 0.09), fb(6.20, 0.105, -0.085, 0.0),
        fb(6.32, 0.05, -0.065, -0.035)]
CORE_IN = 0.008
BASE_Z, TOP_Z = 4.69, 6.32
THM = 62.0                           # the frown runs this far round each side
UP = Vector((0, 0, 1))


def hp(th, z, eps=0.0):          # point on the head, th degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def hn(th, z):
    return ring_pt(HEAD, z, 270 + th, 0.0)[1]


def zf(th):                      # the frown: highest in the middle, dropping to the corners
    return 5.22 - 0.24 * (min(abs(th), THM) / THM) ** 2


def gap(th):
    t = min(abs(th), THM) / THM
    return 0.003 + 0.022 * (1 - t * t)


ZUP = [5.63, 5.80, 6.00, 6.20, 6.32]
LIP_IN = 0.03                        # how far the upper lip sits back from the plate round it


def za(th):                      # the edge of the upper lip: from each nostril round and down to the corner of the mouth
    a = min(abs(th), THM)
    if a <= 28:                                                 # under the nose panel
        return 5.60
    return 5.60 - (5.60 - (zf(THM) + 0.012)) * ((a - 28) / (THM - 28)) ** 1.7


def col_zs(th):
    lo, hi = zf(th) - gap(th), zf(th) + gap(th)
    top = za(th)
    return ([BASE_Z, 4.76] + [4.76 + (lo - 4.76) * f for f in (0.33, 0.66, 1.0)] +
            [hi, (hi + top - 0.004) / 2, top - 0.004, top + 0.004] + ZUP)


def swell(th, k):                # the jaw stands out under the frown; the upper lip is set back inside its edge, like a person's
    a = abs(th)
    if a >= THM:
        return 0.0
    if k < 5:
        return 0.012 * (1 - (a / THM) ** 2) * math.sin(math.pi * (k / 4.0) * 0.8)
    if k <= 7:
        return -LIP_IN * min(1.0, (THM - a) / 7.0)
    return 0.0


plates = bmesh.new()
TF = [0.35, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 59, THM]
F = [0.0, 0.07, 0.14, 0.22, 0.30, 0.38, 0.46, 0.54, 0.62, 0.70, 0.78, 0.86, 0.93, 1.0]
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(hp(s * th, z, swell(th, k))) for k, z in enumerate(col_zs(th))] for th in TF]
    for (ta, ca), (tb, cb) in zip(zip(TF, cols), zip(TF[1:], cols[1:])):
        for k in range(len(ca) - 1):
            if k == 4 and tb <= THM - 1.0:
                continue                                         # the mouth slot, closing to nothing at its corners
            t.faces.new((ca[k], cb[k], cb[k + 1], ca[k + 1]))
    grid(t, [[hp(s * (THM + (179.65 - THM) * f), z) for f in F] for z in col_zs(THM)])
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("BK_HeadPlates", plates, M_PLATE, 30, outward=True, thickness=-0.016)
CORE_IN = 0.05                       # the inner shell clears the set-back lip
core = bmesh.new()
loft(core, [(z, cx, cy, rx - min(CORE_IN, rx * 0.5), ry - min(CORE_IN, ry * 0.5)) for z, cx, cy, rx, ry in HEAD], seg=40)
tag(core, 'joint_head')
new_obj("BK_HeadCore", core, M_JOINT, 30)
loft(plate, [fb(4.63, 0.17, -0.17, 0.15), fb(4.645, 0.27, -0.28, 0.22), fb(4.6905, 0.3395, -0.3595, 0.2795)], seg=32, caps=(True, False))
lathe(steel, (0, -0.02, 4.50), (0, 0, 1), [(0.0, 0.14), (0.03, 0.18), (0.05, 0.18), (0.058, 0.152), (0.066, 0.195), (0.088, 0.195),
                                          (0.096, 0.16), (0.104, 0.20), (0.128, 0.20), (0.136, 0.17), (0.19, 0.17)], seg=28)

# eyes: small, close-set, glaring from under lids that slant steeply down to the middle
eyes, iris, pupil, dark, lids, brow = (bmesh.new() for _ in range(6))
for s in (-1, 1):
    eth, ez = s * 24.0, 5.92
    p, n = hp(eth, ez), hn(eth, ez)
    e_out = UP.cross(n).normalized()
    if e_out.x * s < 0:
        e_out = -e_out
    eu = n.cross(e_out).normalized()
    if eu.z < 0:
        eu = -eu
    EM = Matrix((e_out, eu, n)).transposed().to_4x4()
    c = p - n * 0.034
    bmesh.ops.create_uvsphere(eyes, u_segments=18, v_segments=12, radius=0.066, matrix=Matrix.Translation(c))
    d = (n * 0.97 - e_out * 0.16 - eu * 0.12).normalized()
    puck(iris, c + d * 0.065, d, 0.026, 0.004, seg=14)
    puck(pupil, c + d * 0.067, d, 0.014, 0.004, seg=10)
    ang = math.radians(26)
    nl = (eu * math.cos(ang) - e_out * math.sin(ang)).normalized()
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=22, v_segments=12, radius=1.0,
                              matrix=Matrix.Translation(p + eu * 0.008) @ EM @ Matrix.Diagonal((0.084, 0.07, 0.032, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p + eu * 0.026, plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.005, plane_no=n, clear_inner=True)
    merge(lids, t)
    e_edge = n.cross(nl).normalized()
    lash = [p + eu * 0.024 + e_edge * (0.078 * math.cos(math.radians(a))) + n * (0.002 + 0.026 * math.sin(math.radians(a)) ** 0.8) for a in range(0, 181, 15)]
    tube(dark, lash, [0.003 + 0.004 * math.sin(math.radians(a)) for a in range(0, 181, 15)], seg=5)
    # brows: thick dark strokes pressed down to a V over the nose
    tube(dark, [hp(s * th_, z_, 0.004) for th_, z_ in ((3, 5.915), (12, 5.97), (24, 6.02), (38, 6.045), (50, 6.03))], [0.011, 0.024, 0.028, 0.02, 0.006], seg=10)
# the thin line of the jaw panel: an arch from the base on one side over the frown to the other, and a crooked mark under the nose
for s in (-1, 1):                                              # a fine dark line in the step round the upper lip
    tube(dark, [hp(s * th_, za(th_), -0.004) for th_ in range(28, 63, 2)], [0.002] + [0.004] * 16 + [0.002], seg=5)
# the lip line along the frown, and the bolts
tube(dark, [hp(th_, zf(th_) + gap(th_) + 0.004, -LIP_IN * min(1.0, (THM - abs(th_)) / 7.0) + 0.001) for th_ in range(-62, 63, 4)], [0.004] + [0.011] * 30 + [0.004], seg=6)
nose = bmesh.new()
# nose: a long hard-edged wedge, flat-sided like the rest of him. A narrow bridge between the eyes widens down to a
# blunt end with a flat underside; its wings land where the edge of the upper lip starts.
nv = {k: nose.verts.new(q) for k, q in (
    ('al', hp(4, 5.99, 0.004)), ('ar', hp(-4, 5.99, 0.004)),               # corrected sheet (2026-11-14): a wide flat-fronted
    ('ml', hp(10, 5.82, 0.09)), ('mr', hp(-10, 5.82, 0.09)),               # triangular panel, a third of the face wide at its base
    ('tl', hp(20, 5.665, 0.19)), ('tr', hp(-20, 5.665, 0.19)),
    ('ul', hp(20, 5.615, 0.16)), ('ur', hp(-20, 5.615, 0.16)),
    ('sl', hp(13, 5.90, 0.0)), ('sr', hp(-13, 5.90, 0.0)),
    ('bl', hp(28, 5.60, -0.002)), ('br', hp(-28, 5.60, -0.002)))}
for f in (('al', 'ar', 'mr', 'ml'), ('ml', 'mr', 'tr', 'tl'), ('tl', 'tr', 'ur', 'ul'), ('ul', 'ur', 'br', 'bl'),
          ('al', 'ml', 'sl'), ('ar', 'sr', 'mr'), ('ml', 'tl', 'bl', 'sl'), ('mr', 'sr', 'br', 'tr'), ('tl', 'ul', 'bl'), ('tr', 'br', 'ur')):
    nose.faces.new([nv[k] for k in f])
bmesh.ops.recalc_face_normals(nose, faces=nose.faces)
for sx_ in (-1, 1):                                             # nostrils, in the flat underside
    puck(dark, hp(sx_ * 9, 5.622, 0.135), Vector((0, -0.35, -1)), 0.016, 0.012, seg=10)
for a in (0, 180):                                               # a bolt on each side
    p, n = ring_pt(HEAD, 5.30, a, 0.0)
    lathe(steel, p - n * 0.006, n, [(0.0, 0.045), (0.02, 0.045), (0.028, 0.036), (0.028, 0.02), (0.036, 0.016), (0.04, 0.001)], seg=16)
for _b in (eyes, iris, pupil, dark, lids, brow, nose):
    tag(_b, 'joint_head')
new_obj("BK_Eyes", eyes, M_EYE, 60)
new_obj("BK_Iris", iris, M_IRISRING, 40)
new_obj("BK_Pupil", pupil, M_IRIS, 40)
new_obj("BK_EyeLines", dark, M_BROW, 50)
new_obj("BK_Lids", lids, M_LID, 50)
new_obj("BK_Brows", brow, M_PLATE, 60)
_o = new_obj("BK_Nose", nose, M_PLATE, 25)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.008, 2, 'ANGLE', math.radians(25)

# the fin: a thin red blade up the back of the head, rising past the shell to the point
fin = bmesh.new()
FIN = [(5.63, 0, 0.29, 0.012, 0.012), (5.80, 0, 0.235, 0.06, 0.065), (6.00, 0, 0.185, 0.085, 0.115), (6.20, 0, 0.14, 0.08, 0.16),
       (6.32, 0, 0.12, 0.07, 0.18), (6.50, 0, 0.15, 0.05, 0.15), (6.65, 0, 0.20, 0.03, 0.10), (6.725, 0, 0.24, 0.014, 0.06),
       (6.73, 0, 0.24, 0.006, 0.05)]
loft(fin, FIN, seg=20)
for k in range(7):                                               # combed ridges down each side of the blade
    for sx_ in (-1, 1):
        pts = []
        for z, cx, cy, rx, ry in FIN[1:8]:
            a_ = math.radians(90 + sx_ * (70 - 22 * (k - 3)))
            pts.append(Vector((cx + (rx + 0.002) * math.cos(a_), cy + (ry + 0.002) * math.sin(a_), z)))
        tube(fin, pts, [0.004, 0.006, 0.007, 0.007, 0.007, 0.006, 0.004], seg=4)
tag(fin, 'joint_head')
new_obj("BK_Fin", fin, M_HAIR, 40)

# rivets down each side of the centre seam and round the base
for th_, z_ in ((7, 4.80), (-7, 4.80), (9, 6.05), (-9, 6.05), (40, 4.74), (-40, 4.74), (75, 4.74), (-75, 4.74),
                (120, 4.74), (-120, 4.74), (160, 4.74), (-160, 4.74)):
    puck(plate, hp(th_, z_), hn(th_, z_), 0.011, 0.012, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

