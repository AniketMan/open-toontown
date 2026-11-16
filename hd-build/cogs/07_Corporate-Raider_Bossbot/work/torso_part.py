# ---------------------------------------------------------------- jacket (game units, modelled standing)
# A big round barrel: half-widths from the front and back views, front and back from the side view.
TORSO = [fb(3.05, 1.72, -2.06, 1.66), fb(3.25, 1.80, -2.14, 1.70), fb(3.70, 1.88, -2.18, 1.72),
         fb(4.20, 1.92, -2.15, 1.72), fb(4.70, 1.92, -2.05, 1.68), fb(5.20, 1.90, -1.85, 1.60),
         fb(5.60, 1.88, -1.58, 1.48), fb(5.90, 1.84, -1.30, 1.36), fb(6.10, 1.70, -1.10, 1.26),
         fb(6.25, 1.38, -0.95, 1.16), fb(6.37, 1.10, -0.85, 1.06), fb(6.46, 0.92, -0.78, 0.98),
         fb(6.53, 0.78, -0.72, 0.92)]
TS = TORSO
BREAK = 5.55


def front_gap(z):
    return 0.008 if z <= BREAK else 0.008 + 0.50 * min(1.0, (z - BREAK) / (6.45 - BREAK)) ** 1.1


SHIRT_IN = {5.60: 0.20, 5.90: 0.17, 6.10: 0.15, 6.25: 0.13, 6.37: 0.12, 6.46: 0.12}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
SS += [fb(6.53, 0.70, -0.62, 0.80), fb(6.60, 0.50, -0.45, 0.60)]
bm = bmesh.new()
loft(bm, SS + [fb(6.61, 0.2, -0.15, 0.2)], seg=28)
new_obj("CR_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(9, 24, 9))
for v in bm.verts:
    if v.co.z > 6.50 and v.co.y < 0:
        v.co.z -= 0.09 * min(1.0, -v.co.y / 0.5)
new_obj("CR_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.07)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(3.048, 0, hem_cy, hem_rx - 0.016, hem_ry - 0.016), (3.12, 0, -0.25, 1.60, 1.50)], seg=28, caps=(False, False))
new_obj("CR_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(6.46, 0.95, -0.80, 1.00), fb(6.63, 0.97, -0.82, 1.06), fb(6.61, 1.20, -0.95, 1.22), fb(6.33, 1.50, -1.05, 1.27)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.04 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("CR_Collar", bm, M_SUIT, outward=False, thickness=0.05)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 6.39)))

