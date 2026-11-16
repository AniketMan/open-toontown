"""The chest medallion every cog wears, built as solid metal: a rimmed disc with a stepped face, a lug and D-ring
bail on top, and the department emblem standing off the face in relief. Shared by every cog's build.py.

    bail = medallion(disc_bm, emblem_bm, origin, normal, up, R, kind)

origin: centre of the disc's back; normal: the way it faces; up: its vertical; R: outer radius.
kind: 'gavel' (Lawbot), 'tie' (Bossbot). Returns the point the cord ties to.
The emblem goes in its own bmesh so it can take the dark-metal material: add_meter.py picks the emblem out of the
exported model by that (dark in the texture, proud of the face) and the game lights it as the health light.
Needs hd_lib.py's lathe, tube and inset_outline in the namespace."""


def _prism(bm, M, outline, z0, depth, bev):
    """outline: (x, y) points in the medallion's plane, in order. A block standing depth off z0 with a chamfered top."""
    inner = inset_outline(outline, bev)
    rings = [[bm.verts.new(M @ Vector((x, y, z))) for x, y in pts]
             for pts, z in ((outline, z0), (outline, z0 + depth - bev), (inner, z0 + depth))]
    n = len(outline)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(rings[-1])


def _box(cx, cy, hw, hh):
    return [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]


def medallion(disc, emblem, origin, normal, up, R, kind):
    n = Vector(normal).normalized()
    u = Vector(up).normalized()
    x = u.cross(n).normalized()
    M = Matrix((x, u, n)).transposed().to_4x4()
    M.translation = Vector(origin)
    FACE = 0.21 * R
    R0 = R
    # disc: chamfered back, a tall rounded rim, then the flat face
    lathe(disc, origin, n, [(0.0, 0.93 * R), (0.05 * R, R), (0.24 * R, R), (0.30 * R, 0.965 * R), (0.32 * R, 0.92 * R),
                            (0.30 * R, 0.885 * R), (FACE, 0.875 * R)], seg=40)
    # the border: a raised ring round the face, part of the emblem so it lights with it
    lathe(emblem, origin, n, [(FACE, 0.87 * R), (0.29 * R, 0.86 * R), (0.31 * R, 0.84 * R), (0.31 * R, 0.79 * R), (0.29 * R, 0.77 * R),
                              (FACE, 0.76 * R)], seg=40, caps=False)
    # lug on the rim and a D-ring through it
    _prism(disc, M, [(-0.14 * R, 0.93 * R), (0.14 * R, 0.93 * R), (0.11 * R, 1.13 * R), (-0.11 * R, 1.13 * R)], 0.04 * R, 0.22 * R, 0.03 * R)
    ring_c = Vector((0, 1.22 * R, 0.15 * R))
    pts = [M @ (ring_c + Vector((0.15 * R * math.cos(math.radians(a)), 0.13 * R * math.sin(math.radians(a)), 0))) for a in range(0, 361, 20)]
    tube(disc, pts, [0.04 * R] * len(pts), seg=8, caps=False)
    if kind == 'gavel':
        # an upright mallet: a block head with a flared cap on each end, a tapering handle, a foot
        _prism(emblem, M, _box(0.0, 0.36 * R, 0.30 * R, 0.15 * R), FACE, 0.17 * R, 0.035 * R)
        for s in (-1, 1):
            _prism(emblem, M, _box(s * 0.365 * R, 0.36 * R, 0.075 * R, 0.185 * R), FACE, 0.20 * R, 0.03 * R)
        _prism(emblem, M, [(-0.06 * R, -0.50 * R), (0.06 * R, -0.50 * R), (0.085 * R, 0.21 * R), (-0.085 * R, 0.21 * R)], FACE, 0.14 * R, 0.035 * R)
        _prism(emblem, M, _box(0.0, -0.16 * R, 0.095 * R, 0.035 * R), FACE, 0.16 * R, 0.025 * R)        # a turned ring on the handle
        _prism(emblem, M, _box(0.0, 0.215 * R, 0.12 * R, 0.03 * R), FACE, 0.15 * R, 0.02 * R)         # collar under the head
        _prism(emblem, M, _box(0.0, -0.575 * R, 0.19 * R, 0.085 * R), FACE, 0.16 * R, 0.03 * R)
    elif kind == 'tie':
        R = R * 1.1                                     # the tie fills the face
        # a necktie: the knot, and a blade widening to a point, with raised diagonal stripes
        _prism(emblem, M, [(-0.10 * R, 0.36 * R), (0.10 * R, 0.36 * R), (0.17 * R, 0.60 * R), (-0.17 * R, 0.60 * R)], FACE, 0.17 * R, 0.035 * R)
        blade = [(-0.10 * R, 0.33 * R), (-0.27 * R, -0.36 * R), (0.0, -0.66 * R), (0.27 * R, -0.36 * R), (0.10 * R, 0.33 * R)]
        _prism(emblem, M, blade, FACE, 0.12 * R, 0.035 * R)
        for yc, hw in ((0.14 * R, 0.13 * R), (-0.08 * R, 0.18 * R), (-0.30 * R, 0.22 * R)):
            _prism(emblem, M, [(-hw, yc - 0.10 * R), (hw, yc + 0.02 * R), (hw, yc + 0.10 * R), (-hw, yc - 0.02 * R)], FACE + 0.10 * R, 0.065 * R, 0.02 * R)
    for _bm in (disc, emblem):                  # every face outward, whatever order its corners were given in
        bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces[:])
    return M @ (ring_c + Vector((0, 0.13 * R0, 0)))


def zipper(teeth, tape, rings, zt, zb, k=1.0):
    """A zip down the centre front of a shirt (rings), from zt down to zb: two tapes, interlocking teeth, a slider with
    its pull. k scales the hardware. Needs hd_lib.py's surf, patch, rbox and lathe."""
    def frame(dx, z, lift):
        n_ = (surf(rings, dx, z, 1.0) - surf(rings, dx, z, 0.0)).normalized()
        up_ = (surf(rings, dx, z + 0.01 * k) - surf(rings, dx, z - 0.01 * k)).normalized()
        m_ = Matrix((up_.cross(n_).normalized(), up_, n_)).transposed().to_4x4()
        m_.translation = surf(rings, dx, z, lift)
        return m_
    for s in (-1, 1):
        patch(tape, rings, [(s * 0.004 * k, s * 0.042 * k, zb + (zt - zb) * i / 10) for i in range(11)], 0.003 * k, nx=2)
    nz = int((zt - zb) / (0.019 * k))
    for i in range(nz):
        s = 1 if i % 2 else -1
        rbox(teeth, frame(s * 0.008 * k, zb + (zt - zb) * (i + 0.5) / nz, 0.008 * k), (0.02 * k, 0.012 * k, 0.012 * k), 0.003 * k, 1)
    rbox(teeth, frame(0.0, zt - 0.012 * k, 0.012 * k), (0.036 * k, 0.044 * k, 0.016 * k), 0.006 * k, 2)
    rbox(teeth, frame(0.0, zt - 0.062 * k, 0.02 * k), (0.02 * k, 0.06 * k, 0.006 * k), 0.003 * k, 1)
    lathe(teeth, frame(0.0, zt - 0.03 * k, 0.016 * k).translation - Vector((0.012 * k, 0, 0)), (1, 0, 0), [(0.0, 0.005 * k), (0.024 * k, 0.005 * k)], seg=8)
