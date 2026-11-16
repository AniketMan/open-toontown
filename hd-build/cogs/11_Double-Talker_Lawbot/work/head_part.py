# ---------------------------------------------------------------- head: a faceted two-tier block, four planes
# Read off all five sheets and the original. In plan the head is a diamond: ridges at the front and back, sharp
# corners at the sides. It has two tiers: a hood of four flat planes flaring from a small flat crown down to a wide
# belt, and under the belt's overhang a narrower jaw block. Each hood plane carries one eye; each jaw plane half a
# mouth. The two planes on his left make the sad face (frown), the two on his right the angry one (bared teeth), so
# the front and back views show an eye and half a mouth of each, as every sheet draws them, and the side views show
# one whole face each, as the new turnaround and the original do.
# Measured on the new turnaround (540 px = 5.63 units): crown 5.60 (half-width 0.23), belt 4.84 (half-width 0.55,
# half-depth 0.365), chin 4.28 (half-width 0.385); the crown sits toward the back, so the back ridge is upright and
# the front one slopes. Everything is 0.08 higher here: three sheets show a neck bearing under the chin.
C0 = 0.02
HT = (5.68, C0 + 0.135, 0.23, 0.23)          # (z, centre y, half-width, half-depth)
HB = (4.92, C0, 0.55, 0.365)
HL = (4.90, C0, 0.55, 0.365)                # underside of the hood's edge
BT = (4.90, C0 + 0.008, 0.505, 0.35)
BM = (4.44, C0 + 0.02, 0.40, 0.315)
BB = (4.36, C0 + 0.02, 0.31, 0.24)
UP = Vector((0, 0, 1))
PLANES = {'LF': ('F', 'L'), 'LB': ('B', 'L'), 'RF': ('F', 'R'), 'RB': ('B', 'R')}
TIERS = {'hood': (HB, HT), 'jaw': (BM, BT)}


def corner(ring, name):
    z, cy, w, d = ring
    return {'F': Vector((0, cy - d, z)), 'B': Vector((0, cy + d, z)), 'L': Vector((w, cy, z)), 'R': Vector((-w, cy, z))}[name]


def raw(tier, pl, u, v):
    lo, hi = TIERS[tier]
    c0_, c1_ = PLANES[pl]
    a = corner(lo, c0_).lerp(corner(lo, c1_), u)
    b = corner(hi, c0_).lerp(corner(hi, c1_), u)
    return a.lerp(b, v)


def P(tier, pl, u, v, eps=0.0):
    """Point on a plane: u from the ridge (0) to the side corner (1), v from the tier's bottom (0) to its top (1).
    Returns (point, outward normal, unit direction toward the side corner, unit direction up the plane)."""
    p = raw(tier, pl, u, v)
    du = (raw(tier, pl, min(1.0, u + 0.01), v) - raw(tier, pl, max(0.0, u - 0.01), v)).normalized()
    dv = (raw(tier, pl, u, min(1.0, v + 0.01)) - raw(tier, pl, u, max(0.0, v - 0.01))).normalized()
    n = du.cross(dv).normalized()
    if n.x * p.x + n.y * (p.y - C0) < 0:
        n = -n
    return p + n * eps, n, du, dv


def edge_off(tier, pl, u, v, d):
    """Offset d off the surface that meets the neighbouring plane's offset along a shared edge."""
    p, n, _, _ = P(tier, pl, u, v)
    if u < 1e-6 or u > 1 - 1e-6:
        other = {('LF', 0): 'RF', ('RF', 0): 'LF', ('LB', 0): 'RB', ('RB', 0): 'LB',
                 ('LF', 1): 'LB', ('LB', 1): 'LF', ('RF', 1): 'RB', ('RB', 1): 'RF'}[(pl, int(round(u)))]
        n2 = P(tier, other, u, v)[1]
        return p + (n + n2) / (1 + n.dot(n2)) * d
    return p + n * d


def ridge(bm, tier, pl, path, w_lo, w_hi, crest):
    """A sculpted fold standing out of a plane along path [(u, v)]: flat at both edges, rising to a crest, fading out
    at its ends. Brows and lips are made of these, so they read as part of the shell and not as bars laid on it."""
    n_ = len(path)
    rows = []
    for i, (u, v) in enumerate(path):
        t = math.sin(math.pi * (0.12 + 0.88 * i / (n_ - 1)) / 1.0) ** 0.6 if i < n_ - 1 else 0.75
        rows.append([P(tier, pl, u, v + dv_, 0.0005 + crest * t * k_)[0] for dv_, k_ in
                     ((-w_lo, 0.0), (-0.62 * w_lo, 0.55), (-0.25 * w_lo, 0.92), (0.0, 1.0), (0.25 * w_hi, 0.92), (0.62 * w_hi, 0.55), (w_hi, 0.0))])
    grid(bm, rows)


shellbm = bmesh.new()
G = [i / 8 for i in range(9)]
for pl in PLANES:
    for tier in TIERS:
        grid(shellbm, [[raw(tier, pl, u, v) for u in G] for v in G])
    c0_, c1_ = PLANES[pl]
    for a, b in ((HB, HL), (HL, BT), (BM, BB)):                  # the hood's edge band, its underside, the chin chamfer
        shellbm.faces.new([shellbm.verts.new(q) for q in (corner(a, c0_), corner(a, c1_), corner(b, c1_), corner(b, c0_))])
for ring in (HT, BB):
    shellbm.faces.new([shellbm.verts.new(corner(ring, k)) for k in 'FLBR'])
bmesh.ops.remove_doubles(shellbm, verts=shellbm.verts, dist=0.0005)
bmesh.ops.recalc_face_normals(shellbm, faces=shellbm.faces)
tag(shellbm, 'joint_head')
_o = new_obj("DT_HeadShell", shellbm, M_PLATE, 28)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.012, 2, 'ANGLE', math.radians(35)
lathe(steel, (0, C0 + 0.03, 4.20), (0, 0, 1), [(0.0, 0.13), (0.03, 0.17), (0.05, 0.17), (0.058, 0.145), (0.066, 0.185), (0.088, 0.185),
                                               (0.096, 0.15), (0.104, 0.19), (0.128, 0.19), (0.136, 0.16), (0.165, 0.16)], seg=28)

eyes, iris, pupil, dark, lids, brow, nose, lips, teeth = (bmesh.new() for _ in range(9))
sm = lambda t: t * t * (3 - 2 * t)
US = [0.22 + 0.78 * i / 14 for i in range(15)]
for pl in PLANES:
    angry = pl[0] == 'R'
    # ---- eye: a big round ball set into the plane, under a heavy lid; the lid's edge and the brow run down toward
    # the face's nose on the angry side and up toward it on the sad side
    p, n, a, up = P('hood', pl, 0.52, 0.30)
    EM = Matrix((a, up, n)).transposed().to_4x4()
    c = p - n * 0.05
    bmesh.ops.create_uvsphere(eyes, u_segments=20, v_segments=14, radius=0.105, matrix=Matrix.Translation(c))
    d = (n * 0.93 + a * (0.18 if angry else 0.24) + up * (-0.10 if angry else 0.16)).normalized()
    puck(iris, c + d * 0.104, d, 0.042, 0.004, seg=18)
    puck(pupil, c + d * 0.106, d, 0.022, 0.004, seg=12)
    rim_r = math.sqrt(0.105 ** 2 - 0.05 ** 2)
    tube(dark, [p + n * 0.001 + (a * math.cos(math.radians(q)) + up * math.sin(math.radians(q))) * rim_r for q in range(0, 361, 15)], [0.005] * 25, seg=5, caps=False)
    ang = math.radians(15)
    nl = (up * math.cos(ang) + a * math.sin(ang) * (1 if angry else -1)).normalized()
    t = bmesh.new()
    bmesh.ops.create_uvsphere(t, u_segments=24, v_segments=12, radius=1.0,
                              matrix=Matrix.Translation(p + up * 0.012) @ EM @ Matrix.Diagonal((0.135, 0.122, 0.05, 1.0)))
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p + up * (0.045 if angry else 0.072), plane_no=nl, clear_inner=True)
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=p - n * 0.006, plane_no=n, clear_inner=True)
    merge(lids, t)
    e_edge = n.cross(nl).normalized()
    lash = [p + up * (0.043 if angry else 0.07) + e_edge * (0.118 * math.cos(math.radians(q))) + n * (0.002 + 0.046 * math.sin(math.radians(q)) ** 0.8) for q in range(0, 181, 12)]
    tube(dark, lash, [0.003 + 0.004 * math.sin(math.radians(q)) for q in range(0, 181, 12)], seg=5)
    low = [p - up * 0.10 + a * (0.11 * math.cos(math.radians(q))) + up * (0.03 * (1 - math.sin(math.radians(q)))) for q in range(0, 181, 15)]
    tube(lids, low, [0.004 + 0.007 * math.sin(math.radians(q)) for q in range(0, 181, 15)], seg=6)        # lower lid
    # brows: pressed down toward the face's nose on the angry planes, lifted toward it on the sad ones
    bp = ([(0.08, 0.66), (0.24, 0.655), (0.42, 0.62), (0.60, 0.56), (0.78, 0.49), (0.95, 0.42)] if angry else
          [(0.08, 0.47), (0.24, 0.52), (0.42, 0.575), (0.60, 0.62), (0.78, 0.655), (0.95, 0.68)])
    ridge(brow, 'hood', pl, bp, 0.055, 0.075, 0.042)
    # ---- half a mouth on the jaw plane; the two halves of a face meet on its side corner
    if angry:                                                    # bared teeth: a white band between heavy lips
        vt = lambda u: 0.50 + 0.26 * ((u - 0.22) / 0.78) ** 0.7
        vb = lambda u: 0.50 - 0.17 * ((u - 0.22) / 0.78) ** 0.9
        grid(teeth, [[P('jaw', pl, u, vb(u) + (vt(u) - vb(u)) * f, 0.004)[0] for u in US] for f in (0.0, 0.5, 1.0)])
        ridge(lips, 'jaw', pl, [(u, vt(u) + 0.045) for u in US], 0.04, 0.07, 0.034)
        ridge(lips, 'jaw', pl, [(u, vb(u) - 0.05) for u in US], 0.075, 0.045, 0.036)
        for vf_ in (vt, vb):
            tube(dark, [P('jaw', pl, u, vf_(u), 0.005)[0] for u in US], [0.003] + [0.007] * 14, seg=5)
        tube(dark, [P('jaw', pl, u, (vt(u) + vb(u)) / 2 + (0.012 if i % 2 else -0.012), 0.006)[0] for i, u in enumerate(US)], [0.004] * 15, seg=4)
        for u in (0.42, 0.57, 0.72, 0.87, 0.995):
            tube(dark, [P('jaw', pl, u, vb(u) + (vt(u) - vb(u)) * f, 0.006)[0] for f in (0.04, 0.5, 0.96)], [0.0035] * 3, seg=4)
    else:                                                        # a long frown: the lip line drops away from the nose
        vf = lambda u: 0.42 + 0.20 * ((u - 0.22) / 0.78) ** 0.55
        tube(dark, [P('jaw', pl, u, vf(u), 0.003)[0] for u in US], [0.004] + [0.014] * 13 + [0.014], seg=6)
        UL = [0.62 + 0.38 * i / 6 for i in range(7)]
        ridge(lips, 'jaw', pl, [(u, vf(u) - 0.11) for u in UL], 0.085, 0.09, 0.04)                 # lower lip pushed out under the frown
        tube(dark, [P('jaw', pl, u, v, 0.001)[0] for u, v in ((0.93, 0.97), (0.70, 0.90), (0.42, 0.76), (0.20, 0.52), (0.14, 0.34))],
             [0.003, 0.006, 0.007, 0.006, 0.003], seg=5)                                          # the fold from the nose round the mouth
    # ---- rivets along the belt, the top of the jaw and the chin
    for u in (0.10, 0.30, 0.50, 0.70, 0.90):
        q, qn = P('hood', pl, u, 0.045)[:2]
        puck(plate, q, qn, 0.011, 0.012, seg=6)
    for u, v in ((0.12, 0.93), (0.50, 0.93), (0.12, 0.10), (0.55, 0.10), (0.90, 0.10)):
        q, qn = P('jaw', pl, u, v)[:2]
        puck(plate, q, qn, 0.01, 0.011, seg=6)
# ---- noses: a small wedge on each side corner, sitting on the belt
for sx_ in (1, -1):
    side = 'L' if sx_ > 0 else 'R'
    top = corner(HB, side).lerp(corner(HT, side), 0.2)
    bot = corner(HL, side) + Vector((0, 0, -0.005))
    tip = corner(HB, side) + Vector((sx_ * 0.04, 0, 0.004))
    wa = P('hood', side + 'F', 0.88, 0.0, 0.002)[0]
    wb = P('hood', side + 'B', 0.88, 0.0, 0.002)[0]
    vs_ = [nose.verts.new(q) for q in (top, tip, wa, wb, bot)]
    for tri in ((0, 2, 1), (0, 1, 3), (2, 4, 1), (4, 3, 1), (0, 3, 4), (0, 4, 2)):
        nose.faces.new([vs_[i] for i in tri])
for _b in (eyes, iris, pupil, dark, lids, brow, nose, lips, teeth):
    tag(_b, 'joint_head')
new_obj("DT_Eyes", eyes, M_EYE, 60)
new_obj("DT_Iris", iris, M_IRISRING, 40)
new_obj("DT_Pupil", pupil, M_IRIS, 40)
new_obj("DT_EyeLines", dark, M_BROW, 50)
new_obj("DT_Lids", lids, M_PLATE, 50)
new_obj("DT_Brows", brow, M_PLATE, 60)
_o = new_obj("DT_Nose", nose, M_PLATE, 30)
_bv = _o.modifiers.new("Edge", 'BEVEL')
_bv.width, _bv.segments, _bv.limit_method, _bv.angle_limit = 0.01, 2, 'ANGLE', math.radians(30)
new_obj("DT_Lips", lips, M_PLATE, 60)
new_obj("DT_Teeth", teeth, M_FANG, 50)


# ---- hair: a riveted red cap over the crown. Its edge runs level round the sides and drops in a long peak down the
# front ridge and the back ridge, to between the eyes.
def hairline(u):
    return 0.36 + 0.34 * (u / 0.22) if u <= 0.22 else 0.70 + 0.16 * (u - 0.22) / 0.78


hair = bmesh.new()
HU = [0.0, 0.055, 0.11, 0.165, 0.22, 0.32, 0.45, 0.6, 0.75, 0.9, 1.0]
crown = {}
for pl in PLANES:
    rows = [[edge_off('hood', pl, u, hairline(u) + (1 - hairline(u)) * f, 0.014) for u in HU] for f in (0.0, 0.34, 0.67, 1.0)]
    grid(hair, rows)
    crown[PLANES[pl][0]] = rows[-1][0]
    crown[PLANES[pl][1]] = rows[-1][-1]
    for u in (0.34, 0.60, 0.88):
        q, qn = P('hood', pl, u, hairline(u) + 0.03, 0.014)[:2]
        puck(plate, q, qn, 0.01, 0.011, seg=6)
hair.faces.new([hair.verts.new(crown[k] + Vector((0, 0, 0.004))) for k in 'FLBR'])
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.006)
bmesh.ops.recalc_face_normals(hair, faces=hair.faces)
if sum(f.normal.dot(f.calc_center_median() - Vector((0, C0 + 0.1, 5.4))) for f in hair.faces) < 0:
    bmesh.ops.reverse_faces(hair, faces=hair.faces)
tag(hair, 'joint_head')
_h = new_obj("DT_Hair", hair, M_HAIR, 28)
_sol = _h.modifiers.new("Cloth thickness", 'SOLIDIFY')
_sol.thickness = 0.014
_sol.offset = -1.0
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

