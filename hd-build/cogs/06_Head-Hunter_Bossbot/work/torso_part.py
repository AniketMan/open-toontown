# ---------------------------------------------------------------- jacket (game units, modelled standing)
# A wedge: narrow hips flaring to very wide shoulders. Half-widths from the front and back views, depth from the side.
TORSO = [fb(3.48, 0.78, -0.80, 0.47), fb(3.80, 0.78, -0.80, 0.47), fb(4.20, 0.80, -0.78, 0.50),
         fb(4.60, 0.88, -0.85, 0.56), fb(5.00, 1.00, -0.98, 0.64), fb(5.40, 1.14, -1.07, 0.72),
         fb(5.75, 1.30, -1.03, 0.80), fb(6.00, 1.50, -0.90, 0.82), fb(6.15, 1.50, -0.78, 0.80),
         fb(6.30, 1.25, -0.65, 0.72), fb(6.42, 0.90, -0.55, 0.62), fb(6.52, 0.60, -0.45, 0.52),
         fb(6.58, 0.42, -0.38, 0.45)]
TS = TORSO
BREAK = 5.60


def front_gap(z):
    return 0.004 if z <= BREAK else 0.004 + 0.34 * min(1.0, (z - BREAK) / (6.5 - BREAK)) ** 1.1


SHIRT_IN = {5.75: 0.10, 6.00: 0.09, 6.15: 0.08, 6.30: 0.07, 6.42: 0.07, 6.52: 0.07}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
SS += [fb(6.58, 0.36, -0.31, 0.38), fb(6.63, 0.25, -0.2, 0.25)]
bm = bmesh.new()
loft(bm, SS + [fb(6.64, 0.1, -0.08, 0.1)], seg=28)
new_obj("HH_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(9, 24, 9))
for v in bm.verts:
    if v.co.z > 6.565 and v.co.y < 0:
        v.co.z -= 0.06 * min(1.0, -v.co.y / 0.3)
new_obj("HH_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.05)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(3.478, 0, hem_cy, hem_rx - 0.012, hem_ry - 0.012), (3.52, 0, -0.14, 0.64, 0.50)], seg=28, caps=(False, False))
new_obj("HH_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(6.52, 0.42, -0.36, 0.47), fb(6.66, 0.43, -0.37, 0.50), fb(6.64, 0.56, -0.45, 0.60), fb(6.42, 0.82, -0.55, 0.68)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.03 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("HH_Collar", bm, M_SUIT, outward=False, thickness=0.036)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 6.475)))

