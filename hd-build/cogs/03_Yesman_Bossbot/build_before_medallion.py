"""Build the HD Yesman (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (549 px = 5.3 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit A's rest pose at native size (game / 0.681).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/03_Yesman_Bossbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.075
K = 4.125 / 6.06        # suit A scale for this cog
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'


def get_col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("Yesman")
refcol = get_col("Yesman_Reference")
root = bpy.data.objects.new("Yesman", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "ym/refplanes/ym_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 5.3
    e.empty_image_offset = (-0.5, 0)
    e.location = loc
    e.rotation_euler = rot
    e.color[3] = 0.6
    e.use_empty_image_alpha = True
    e.hide_render = True
    e.hide_viewport = True


ref("front", (0, 3, 0), (H, 0, 0))
ref("back", (0, -3, 0), (H, 0, math.pi))
ref("left", (-3, 0, 0), (H, 0, H))
ref("right", (3, 0, 0), (H, 0, -H))

# ---------------------------------------------------------------- materials
M_SUIT = pmat("YM_Suit", (0.17, 0.045, 0.032), 0.88, var=0.35, grime=0.12, stripe=(0.40, 0.19, 0.15), weave=0.5, bump=0.25,
              bscale=120, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("YM_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("YM_Stitch", (0.62, 0.42, 0.36), 0.85, var=0.2)
M_PLATE = pmat("YM_Plate", (0.72, 0.56, 0.47), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_TEETH = pmat("YM_Teeth", (0.80, 0.72, 0.60), 0.25, var=0.15, grime=0.35, bump=0.05, bscale=60, rvar=0.08, coat=0.4)
M_JOINT = pmat("YM_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("YM_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("YM_Hair", (0.012, 0.011, 0.011), 0.28, 0.2, var=0.4, wear=0.15, bump=0.25, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_BLACK = mat("YM_Black", (0.004, 0.004, 0.004), 0.9)
M_SHOE = pmat("YM_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("YM_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("YM_Pewter", (0.55, 0.44, 0.36), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("YM_Shirt", (0.80, 0.74, 0.68), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("YM_Tie", (0.22, 0.035, 0.03), 0.5, var=0.25, grime=0.15, weave=0.6, sheen=0.5, rvar=0.1)

plate, joint, steel, black, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()


def merge(dst, src, weld=0.0):
    if weld:
        bmesh.ops.remove_doubles(src, verts=src.verts, dist=weld)
    me = bpy.data.meshes.new("tmp")
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


# ---------------------------------------------------------------- jacket (game units, modelled standing)
# A barrel chest over a narrow waist: half-widths from the front view (the waist shows between the arms, the chest
# is hidden behind them), front and back from the side view.
TORSO = [fb(2.17, 0.58, -0.51, 0.42), fb(2.40, 0.57, -0.53, 0.42), fb(2.80, 0.59, -0.58, 0.44),
         fb(3.00, 0.68, -0.62, 0.46), fb(3.20, 0.80, -0.66, 0.47), fb(3.50, 0.93, -0.71, 0.50),
         fb(3.70, 1.12, -0.60, 0.52), fb(3.82, 1.17, -0.50, 0.50), fb(3.90, 1.08, -0.45, 0.47),
         fb(3.97, 0.82, -0.40, 0.43), fb(4.03, 0.52, -0.33, 0.38), fb(4.075, 0.31, -0.24, 0.30)]
TS = TORSO
BREAK = 3.57


def front_gap(z):
    """Half-width of the jacket opening: buttoned below the break, a V showing shirt and tie above it."""
    return 0.004 if z <= BREAK else 0.004 + 0.26 * min(1.0, (z - BREAK) / (4.05 - BREAK)) ** 1.1


SHIRT_IN = {3.50: 0.04, 3.70: 0.04, 3.82: 0.05, 3.90: 0.06, 3.97: 0.07}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
bm = bmesh.new()
loft(bm, SS + [fb(4.03, 0.40, -0.28, 0.33), fb(4.04, 0.2, -0.15, 0.2)], seg=28)
new_obj("YM_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(9, 24, 9))
for v in bm.verts:
    if v.co.z > 4.06 and v.co.y < 0:
        v.co.z -= 0.05 * min(1.0, -v.co.y / 0.24)
new_obj("YM_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.04)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(2.168, 0, hem_cy, hem_rx - 0.01, hem_ry - 0.01), (2.19, 0, 0.0, 0.50, 0.38)], seg=28, caps=(False, False))
new_obj("YM_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(4.04, 0.33, -0.25, 0.37), fb(4.125, 0.34, -0.26, 0.40), fb(4.115, 0.46, -0.33, 0.48), fb(4.01, 0.62, -0.40, 0.555)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.025 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("YM_Collar", bm, M_SUIT, outward=False, thickness=0.028)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 4.042)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt24_1 / scale_jnt27_1 carry the upper
# arms, Lh_arm / Rh_arm the forearms, scale_jnt3_1 / scale_jnt4_1 the thighs, jnt3_2 / jnt4_2 the shins,
# to_LegL / to_legR the feet and to_MAIN the pelvis. Suit A's rest pose is not symmetric (shoulders at x 1.67 and
# -1.61, wrists at 3.87 and -3.91), so the right arm is the left one refitted to the right arm's own joints.
RIG = json.load(open(SP + "ym_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.075 / K
LS, LW = JR["shoulderL1"], JR["Lh_wrist"]
RS, RW = JR["shoulderR1"], JR["Rh_wrist"]
AZ = LW.z
WX = LW.x
AY = LW.y
SX = LS.x                                # 1.67; elbow about 2.55; wrist 3.87


def to_right(co):
    """Left-arm point -> the matching point on the right arm, between its own shoulder and wrist joints."""
    t = (co.x - LS.x) / (LW.x - LS.x)
    tc = max(0.0, min(1.0, t))
    ref_l = LS + (LW - LS) * tc
    ref_r = RS + (RW - RS) * tc
    return Vector((ref_r.x - (co.x - ref_l.x) * (abs(RW.x - RS.x) / (LW.x - LS.x) if 0 < t < 1 else 1.0),
                   ref_r.y + (co.y - ref_l.y), ref_r.z + (co.z - ref_l.z)))


def both_arms(build):
    """build(bm) makes left-arm geometry; returns a bmesh with it and its right-arm twin."""
    out = bmesh.new()
    for side in (1, -1):
        t = bmesh.new()
        build(t)
        if side < 0:
            for v in t.verts:
                v.co = to_right(v.co)
            bmesh.ops.reverse_faces(t, faces=t.faces)
        merge(out, t)
    return out


SLEEVE = [(SX - 0.22, 0.11, AZ, 0.10, 0.08), (SX - 0.19, 0.11, AZ, 0.24, 0.22), (SX - 0.12, 0.11, AZ, 0.35, 0.32),
          (SX - 0.05, 0.11, AZ, 0.40, 0.375), (SX + 0.03, 0.11, AZ, 0.42, 0.40), (2.10, 0.10, AZ, 0.42, 0.41),
          (2.55, 0.09, AZ, 0.40, 0.39), (3.10, 0.08, AZ, 0.37, 0.36), (3.64, 0.07, AZ, 0.35, 0.34), (3.62, 0.07, AZ, 0.275, 0.265)]
BAND = [(3.20, 0.08, AZ, 0.39, 0.38), (3.655, 0.07, AZ, 0.37, 0.36)]


def sleeve_cloth(bm):
    xloft(bm, SLEEVE, seg=24)
    xloft(bm, BAND, seg=24)


def sleeve_buttons(bm):
    for x in (3.38, 3.53):
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(math.radians(50)), math.sin(math.radians(50))))
        puck(bm, (x, cy + (ry + 0.004) * n.y, cz + (rz + 0.004) * n.z), n, 0.038, 0.03)


def sleeve_stitch(bm):
    for x in (3.235, 3.63):
        _, cy, cz, ry, rz = BAND[0] if x < 3.4 else BAND[1]
        ring = [Vector((x, cy + (ry + 0.004) * math.cos(math.radians(a)), cz + (rz + 0.004) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(bm, ring, [0.009] * len(ring), seg=4)


pewter_r, stitch_r = both_arms(sleeve_buttons), both_arms(sleeve_stitch)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("YM_Sleeves", both_arms(sleeve_cloth), M_SUIT, 60, rest=True)
new_obj("YM_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("YM_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- forearm cuff, wrist bearing and hand, flat in the rest pose: fingers straight out along x, index at the front
plate_r, joint_r = bmesh.new(), bmesh.new()
KN_X = JR["Lh_1"].x                                              # knuckle joints (0.63 from the wrist)
J2_X = JR["Lh_2"].x                                              # second finger joints (0.37 further)
FW = 0.185                                                       # finger width
FINGERS = (("index", JR["Lh_index1"].y - 0.03), ("rest", 0.065), ("rest", 0.255), ("rest", 0.445))
PLATE_Y = 0.155
for s in (-1, 1):
    S = 'L' if s > 0 else 'R'
    T = Matrix.Identity(4) if s > 0 else Matrix.Translation(RW - MIRROR @ LW) @ MIRROR
    R3 = T.to_3x3()
    names = dict(wrist=S + 'h_wrist', index=(S + 'h_index1', S + 'h_index2'), rest=(S + 'h_1', S + 'h_2'),
                 thumb=(S + 'h_thumb1', S + 'h_thumb2'))
    ax = R3 @ Vector((1, 0, 0))
    c0 = T @ Vector((WX - 0.62, AY, AZ))                         # metal cuff starts well inside the sleeve
    lathe(plate_r, c0, ax, [(0.0, 0.22), (0.02, 0.25), (0.47, 0.262), (0.49, 0.285), (0.53, 0.285), (0.54, 0.22)], seg=22)
    lathe(joint_r, c0, ax, [(0.53, 0.195), (0.548, 0.222), (0.566, 0.19), (0.584, 0.222), (0.602, 0.19), (0.62, 0.215)], seg=18)
    for n in (Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((0, 1, 0))):
        n = R3 @ n
        puck(plate_r, c0 + ax * 0.445 + n * 0.262, n, 0.058, 0.02, seg=12)
        puck(joint_r, c0 + ax * 0.445 + n * 0.268, n, 0.04, 0.02, seg=10)
        puck(plate_r, c0 + ax * 0.445 + n * 0.274, n, 0.02, 0.018, seg=8)
    LEN = KN_X - WX - 0.04
    rbox(plate_r, T @ Matrix.Translation((WX + 0.02 + LEN / 2, PLATE_Y, AZ + 0.04)), (LEN, 0.76, 0.225), 0.075, 3)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.04 + LEN / 2, PLATE_Y, AZ - 0.098)), (LEN - 0.1, 0.64, 0.11), 0.033, 1)
    rbox(joint_r, T @ Matrix.Translation((WX + 0.03 + LEN / 2, PLATE_Y, AZ - 0.022)), (LEN - 0.07, 0.68, 0.135), 0.0)
    for k in range(7):
        puck(plate_r, T @ Vector((WX + 0.085, PLATE_Y - 0.30 + 0.10 * k, AZ + 0.152)), R3 @ Vector((0, 0, 1)), 0.015, 0.014, seg=6)
    tag(plate_r, names['wrist'])
    tag(joint_r, names['wrist'])
    for kind, fy in FINGERS:
        j1, j2 = names[kind]
        k0 = Vector((KN_X, fy, AZ + 0.015))
        k1 = Vector((J2_X, fy, AZ + 0.024))
        k2 = k1 + Vector((math.cos(math.radians(-14)), 0, math.sin(math.radians(-14)))) * 0.22
        k3 = k2 + Vector((math.cos(math.radians(-34)), 0, math.sin(math.radians(-34)))) * 0.19
        seg_box(plate_r, T, k0, k1, (0, 0, 1), 0.175, FW - 0.01, 0.04, 2, gap=0.007)
        lathe(joint_r, T @ (k0 + Vector((0, -0.075, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.07), (0.15, 0.07)], seg=10)
        tag(plate_r, j1)
        tag(joint_r, j1)
        seg_box(plate_r, T, k1, k2, (0, 0, 1), 0.175, FW - 0.01, 0.04, 2, gap=0.007)
        seg_box(plate_r, T, k2, k3, (0, 0, 1), 0.175, FW - 0.01, 0.055, 2, gap=0.007)
        for q in (k1, k2):
            lathe(joint_r, T @ (q + Vector((0, -0.075, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.07), (0.15, 0.07)], seg=10)
        tag(plate_r, j2)
        tag(joint_r, j2)
    t1, t2 = JR["Lh_thumb1"].copy(), JR["Lh_thumb2"].copy()
    t1.z = t2.z = AZ
    td = (t2 - t1).normalized()
    t2e = t2 + td * 0.05
    t3 = t2e + (td + Vector((0.5, 0, -0.25))).normalized() * 0.2
    lathe(joint_r, T @ (t1 + Vector((0, 0, -0.08))), R3 @ Vector((0, 0, 1)), [(0.0, 0.11), (0.16, 0.11)], seg=14)
    tag(joint_r, names['wrist'])
    seg_box(plate_r, T, t1, t2e, (0, 0, 1), 0.16, 0.16, 0.04, 2, gap=0.004)
    lathe(plate_r, T @ (t1 + Vector((0, 0, 0.078))), R3 @ Vector((0, 0, 1)), [(0.0, 0.095), (0.022, 0.095), (0.038, 0.06)], seg=14)
    tag(plate_r, names['thumb'][0])
    seg_box(plate_r, T, t2e, t3, (0, 0, 1), 0.16, 0.16, 0.055, 2, gap=0.007)
    lathe(joint_r, T @ (t2e + Vector((0, 0, -0.07))), R3 @ Vector((0, 0, 1)), [(0, 0.064), (0.14, 0.064)], seg=10)
    tag(plate_r, names['thumb'][1])
    tag(joint_r, names['thumb'][1])
new_obj("YM_HandPlates", plate_r, M_PLATE, 32, rest=True)
new_obj("YM_HandJoints", joint_r, M_JOINT, 40, rest=True)

# ---- trousers: one sealed garment. Seat bowl on the pelvis (to_MAIN, z 3.53) running up inside the jacket (hem at
# z 3.19 here); legs straight down round hip (z 3.5) -> knee (1.95) -> ankle (0.08).
seat = bmesh.new()
loft(seat, [(2.75, 0, 0.0, 0.06, 0.06), (2.80, 0, 0.0, 0.32, 0.28), (2.90, 0, 0.0, 0.54, 0.43), (3.05, 0, -0.01, 0.68, 0.53),
            (3.30, 0, -0.02, 0.76, 0.59), (3.60, 0, -0.02, 0.78, 0.61), (3.90, 0, -0.02, 0.62, 0.5), (4.05, 0, -0.02, 0.4, 0.35)],
     seg=24, centres=(270, 90))
new_obj("YM_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
HIP = {1: JR["scale_jnt3_1"].x, -1: -JR["scale_jnt4_1"].x}       # 0.44 and 0.39: each leg sits on its own hip joint
for s in (-1, 1):
    cx = HIP[s]
    w = min(0.33, cx - 0.012)                                    # the legs touch down the middle but do not overlap
    LEG = [(0.42, cx, 0.0, w, 0.465), (0.60, cx, 0.0, w - 0.01, 0.455), (1.95, cx, -0.02, w - 0.005, 0.46),
           (2.80, cx, -0.03, w, 0.50), (3.30, cx, -0.04, w, 0.54)]
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("YM_Trousers", bm, M_SUIT, 60, rest=True)

# ---- shoes: cap-toe, welted, separate heel, pointing straight ahead; heel on the ankle bone, toe 1.0 ahead of it
upper, sole = bmesh.new(), bmesh.new()
SHOE = [(0.47, 0.0, 0.12, 0.20), (0.42, 0.0, 0.19, 0.27), (0.25, 0.0, 0.25, 0.33), (0.0, 0.01, 0.29, 0.34),
        (-0.30, 0.04, 0.33, 0.31), (-0.55, 0.06, 0.345, 0.26), (-0.72, 0.06, 0.32, 0.20), (-0.83, 0.06, 0.26, 0.15),
        (-0.89, 0.06, 0.17, 0.09), (-0.92, 0.06, 0.07, 0.05)]            # (y, x offset from the ankle, half-width, height above the welt)
WELT, OUTSOLE = 0.11, 0.07
NS = 12


def welt_extra(y):
    return 0.026 if y > 0.1 else 0.04


for s in (-1, 1):
    ank = HIP[s]
    ST = [(y, ank + dx, w, h) for y, dx, w, h in SHOE]
    SHOE_SAVE, SHOE = SHOE, ST                                   # shoe_at reads SHOE
    PLAN = [(y, cx, w) for y, cx, w, h in ST]
    shoe_piece(upper, s, ST)
    cap_y = -0.62
    shoe_piece(upper, s, [(cap_y, *shoe_at(cap_y))] + [st for st in ST if st[0] < cap_y], grow=0.015)
    ctr_y = 0.17
    shoe_piece(upper, s, [st for st in ST if st[0] > ctr_y] + [(ctr_y, *shoe_at(ctr_y))], grow=0.012)
    for y in (-0.30, -0.14):
        cx, w, h = shoe_at(y)
        tube(sole, [Vector((s * (cx + shoe_sec(w + 0.003, h + 0.003, k)[0]), y, shoe_sec(w + 0.003, h + 0.003, k)[1]))
                    for k in range(2, NS - 1)], [0.006] * (NS - 3), seg=4)
    slab(sole, s, [(0.49, ank, 0.07)] + PLAN + [(-0.94, ank + 0.06, 0.035)], OUTSOLE, WELT)
    fore = [(-0.10, *shoe_at(-0.10)[:2])] + [p for p in PLAN if p[0] < -0.10] + [(-0.935, ank + 0.06, 0.035)]
    slab(sole, s, fore, 0.012, OUTSOLE, 0.03)
    heel = [(0.485, ank, 0.07)] + [p for p in PLAN if p[0] > 0.10] + [(0.10, *shoe_at(0.10)[:2])]
    slab(sole, s, heel, 0.012, OUTSOLE, 0.02)
    for y in (-0.80, -0.68, -0.56, -0.44, -0.32, -0.20):
        cx, w, h = shoe_at(y)
        rbox(sole, Matrix.Translation((s * cx, y, 0.008)), (2 * w - 0.06, 0.07, 0.016), 0.0)
    SHOE = SHOE_SAVE
new_obj("YM_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("YM_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.075

# ---------------------------------------------------------------- head: built from its plates over a closed inner shell
# HEAD is the outer surface (front view half-widths, side view front and back). Pieces: the face plate (forehead,
# closed eyes, cheeks, upper lip), the chin plate, the mouth cassette of separate teeth between them, two back
# plates, the crown, the hair shell over the back, a jaw pivot disc at each ear. Panel lines are hairlines.
HEAD = [fb(4.245, 0.36, -0.42, 0.22), fb(4.30, 0.43, -0.46, 0.30), fb(4.40, 0.52, -0.47, 0.38),
        fb(4.50, 0.57, -0.47, 0.44), fb(4.60, 0.60, -0.47, 0.47), fb(4.70, 0.585, -0.46, 0.49),
        fb(4.80, 0.56, -0.44, 0.50), fb(4.90, 0.52, -0.43, 0.50), fb(5.00, 0.46, -0.43, 0.49),
        fb(5.10, 0.40, -0.42, 0.46), fb(5.20, 0.30, -0.36, 0.36), fb(5.27, 0.19, -0.27, 0.22),
        fb(5.30, 0.012, -0.062, -0.038)]
HEAD_N = 2.3
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.0012
CORE_IN = 0.012
FA = 100.0                       # the face and chin plates run this far round each side from centre front
MH = 84.0                        # the mouth runs this far round each side
SIDE_Z = 4.783                   # seam between face and chin plates behind the mouth corners
FACE_TOP = 5.215


def hp(theta, z, eps=0.0):       # point on the head, theta degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + theta, eps)[0]


def agap(z, d=GAP):
    return math.degrees(d / interp(HEAD, z)[3])


def lip_top(th):                 # upper edge of the mouth
    return 4.715 + (SIDE_Z - 4.715) * min(1.0, abs(th) / MH) ** 2


def lip_bot(th):                 # lower edge of the mouth
    return 4.29 + (SIDE_Z - 4.29) * min(1.0, abs(th) / MH) ** 2.4


def bite(th):                    # line where the upper and lower teeth meet
    return 4.47 + (SIDE_Z - 4.47) * min(1.0, abs(th) / MH) ** 2


EYE_C, EYE_W = 29.0, 19.5        # closed eye: centre and half-width in degrees


def lip_gap(th):                 # clearance between a lip and the teeth; closes to a hairline at the mouth corner
    return GAP + 0.005 * (1 - min(1.0, abs(th) / MH) ** 8)


def eye_z(th):
    t = (abs(th) - EYE_C) / EYE_W
    return 5.092 - 0.034 * min(1.0, t * t)


def eye_h(th):
    t = (abs(th) - EYE_C) / EYE_W
    return 0.011 * math.sqrt(1 - t * t) if abs(t) < 1 else 0.0


def bulge(th, z):
    """Sculpted relief of the face plate: cheeks pushed up by the grin, brow ridge, upper lip."""
    a = abs(th)
    cheek = 0.085 * math.exp(-((a - 46) / 24) ** 2 - ((z - 4.90) / 0.085) ** 2)
    brow = 0.02 * math.exp(-((a - 30) / 26) ** 2 - ((z - 5.14) / 0.035) ** 2)
    lipr = 0.022 * math.exp(-((z - lip_top(th) - 0.03) / 0.03) ** 2) * max(0.0, 1.0 - (a / MH) ** 6)
    return cheek + brow + lipr


plates = bmesh.new()
# Every seam is sampled identically on both of its sides (same angles round the head, same heights up it), so the
# two plate edges are the same polyline a hairline apart and no slivers open between them.
TH = [-FA + 2 * FA * i / 80 for i in range(81)]                  # 2.5 degree steps
FACE_F = ((0.0, 0.2, 0.42, 0.62, 0.8, 0.92, 1.0), (0.0, 0.25, 0.6, 1.0))
CHIN_F = (0.0, 0.12, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0)


def face_zs(th):
    bot = lip_top(th) + lip_gap(th)
    ez, eh = eye_z(th), eye_h(th)
    return [bot + (ez - eh - bot) * f for f in FACE_F[0]] + [ez + eh + (FACE_TOP - ez - eh) * f for f in FACE_F[1]]


def chin_zs(th):
    top = lip_bot(th) - lip_gap(th)
    return [4.25 + (top - 4.25) * f for f in CHIN_F]


# face plate: one piece, from the mouth up to the crown seam, with the two closed eyes cut through it as slots
t = bmesh.new()
cols = [[(t.verts.new(hp(th, z, bulge(th, z))), eye_h(th)) for z in face_zs(th)] for th in TH]
for a, b in zip(cols, cols[1:]):
    for k in range(10):
        if k == 6:
            continue
        t.faces.new((a[k][0], b[k][0], b[k + 1][0], a[k + 1][0]))
merge(plates, t, weld=0.0004)
# chin plate: one piece under the mouth, wrapping up behind the mouth corners to the side seam
grid(plates, [[hp(th, chin_zs(th)[k]) for th in TH] for k in range(len(CHIN_F))])
# back plates: two halves meeting at centre back, from the base to the crown seam (mostly under the hair shell).
# Their front edges use the chin and face plates' own heights, their top edges the crown's angles.
BACK_Z = chin_zs(FA) + face_zs(FA)
BACK_TH = [FA + 2.5 * i for i in range(33)]                      # 100 .. 180
for s in (1, -1):
    rows = []
    for z in BACK_Z:
        g = agap(z)
        ths = [BACK_TH[0] + g] + BACK_TH[1:-1] + [BACK_TH[-1] - g]
        rows.append([Vector((s * p.x, p.y, p.z)) for p in (hp(a, z) for a in ths)])
    grid(plates, rows)
# crown: two halves split by the centre seam, closing the top of the head
CROWN_TH = [2.5 * i for i in range(73)]                          # 0 .. 180, the same steps as the plates below
for s in (1, -1):
    rows = []
    for z in (FACE_TOP + 2 * GAP, 5.245, 5.27, 5.29, 5.3):
        g = agap(z) if z < 5.29 else 0.0
        ths = [g] + CROWN_TH[1:-1] + [180 - g]
        rows.append([Vector((s * p.x, p.y, p.z)) for p in (hp(a, z) for a in ths)])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("YM_HeadPlates", plates, M_PLATE, 62, outward=True, thickness=-0.022)

# mouth cassette: separate teeth, upper and lower row, set just inside the lips with a narrow gap round each one
teeth = bmesh.new()
TG = 0.0045                      # half the gap between teeth
EDGES_U = [-MH + 4, -57.0, -38.0, -19.5, 0.0, 19.5, 38.0, 57.0, MH - 4]
EDGES_L = [-MH + 4, -57.0, -37.0, -18.0, 0.0, 18.0, 37.0, 57.0, MH - 4]
for edges, lo, hi in ((EDGES_U, lambda th: bite(th) + TG, lambda th: lip_top(th) - 0.003),
                      (EDGES_L, lambda th: lip_bot(th) + 0.003, lambda th: bite(th) - TG)):
    for a, b in zip(edges, edges[1:]):
        ga = math.degrees(TG / 0.58)
        a, b = a + ga, b - ga
        rows = []
        for f in (0.0, 0.2, 0.5, 0.8, 1.0):
            row = []
            for i in range(5):
                th = a + (b - a) * i / 4
                l, h = lo(th), max(lo(th) + 0.004, hi(th))
                edge_in = 0.002 * (1 - math.sin(math.pi * f)) ** 2 + 0.002 * (1 - math.sin(math.pi * i / 4)) ** 2   # each tooth is a little domed
                row.append(hp(th, l + (h - l) * f, -0.004 - edge_in))
            rows.append(row)
        grid(teeth, rows)
tag(teeth, 'joint_head')
new_obj("YM_Teeth", teeth, M_TEETH, 40, outward=True, thickness=-0.02)

# substructure: a closed inner shell just under the plates, the full height of the head
core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD[:-1]] + [fb(5.288, 0.006, -0.056, -0.044)],
     seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("YM_HeadCore", core, M_JOINT, 60)
# base of the head and the layered neck bearing
loft(plate, [fb(4.20, 0.25, -0.25, 0.22), fb(4.205, 0.31, -0.36, 0.20), fb(4.2485, 0.3605, -0.4205, 0.2205)], seg=28, caps=(False, False), power=HEAD_N)
lathe(steel, (0, 0.0, 4.04), (0, 0, 1), [(0.0, 0.22), (0.04, 0.265), (0.065, 0.265), (0.075, 0.23), (0.085, 0.285), (0.115, 0.285),
                                         (0.125, 0.24), (0.135, 0.29), (0.165, 0.29), (0.175, 0.245), (0.21, 0.245)], seg=28)

# nose: a bulb with two nostril wings, bolted on over the face plate's centre
nose = bmesh.new()
ny = lambda z: hp(0, z).y
for (x, y, z), (rx, ry, rz) in (((0, ny(5.0) - 0.035, 5.0), (0.105, 0.105, 0.10)), ((0.115, ny(4.975) + 0.01, 4.975), (0.07, 0.065, 0.055)),
                                ((-0.115, ny(4.975) + 0.01, 4.975), (0.07, 0.065, 0.055)), ((0, ny(5.07) + 0.035, 5.07), (0.055, 0.06, 0.07))):
    bmesh.ops.create_uvsphere(nose, u_segments=16, v_segments=10, radius=1.0,
                              matrix=Matrix.Translation((x, y, z)) @ Matrix.Diagonal((rx, ry, rz, 1.0)))
tag(nose, 'joint_head')
new_obj("YM_Nose", nose, M_PLATE, 60)

# brows: raised dark arcs over the closed eyes
brow = bmesh.new()
for s in (-1, 1):
    rows = []
    for k in (0, 1):
        row = []
        for i in range(11):
            th = 9 + 56 * i / 10
            tt = (th - 34) / 28
            zc = 5.158 - 0.036 * tt * tt
            hw = 0.013 * (1 - 0.55 * abs(tt))
            row.append(hp(s * th, zc + (hw if k else -hw), bulge(th, zc) + 0.012))
        rows.append(row)
    grid(brow, rows)
tag(brow, 'joint_head')
new_obj("YM_Brows", brow, M_HAIR, 35, outward=True, thickness=-0.02)

# hair shell: a separate rigid shell over the back of the head, from behind the ears up to the crown
hair = bmesh.new()
rows = []
for f in (0.0, 0.12, 0.3, 0.5, 0.7, 0.85, 0.95, 1.0):
    row = []
    for i in range(33):
        a = 22 + 136 * i / 32                        # ring angle: 90 = centre back, 0 and 180 = the sides
        side = abs(a - 90) / 68                      # 0 at centre back, 1 at the front edge
        bot = 4.44 + 0.16 * max(0.0, (side - 0.55) / 0.45) ** 1.5
        top = 5.255 - 0.05 * side ** 2
        z = bot + (top - bot) * f
        row.append(ring_pt(HEAD, z, a, 0.03)[0])
    rows.append(row)
grid(hair, rows)
tag(hair, 'joint_head')
new_obj("YM_Hair", hair, M_HAIR, 50, outward=True, thickness=0.035)

# jaw pivot discs at the ears, and the hinge rod from each mouth corner back to its disc
for s in (-1, 1):
    p, n = ring_pt(HEAD, 4.72, 90 - s * 79, 0.0)
    # (three of the sheets show this as a large disc of concentric rings, like an earpiece)
    lathe(steel, p - n * 0.01, n, [(0.0, 0.145), (0.045, 0.145), (0.06, 0.13), (0.06, 0.108), (0.042, 0.104)], seg=24)
    lathe(pewter, p, n, [(0.03, 0.094), (0.062, 0.094), (0.07, 0.084), (0.07, 0.066), (0.03, 0.062)], seg=20)
    lathe(steel, p, n, [(0.03, 0.052), (0.074, 0.052), (0.08, 0.044), (0.08, 0.034), (0.03, 0.03)], seg=16)
    lathe(pewter, p, n, [(0.03, 0.024), (0.086, 0.022), (0.094, 0.01), (0.096, 0.001)], seg=12)
    rod = [hp(s * (MH + 2 + 13 * i / 4), 4.79 - 0.07 * i / 4, 0.012) for i in range(5)]
    tube(steel, rod, [0.011] * len(rod), seg=5)
# rivets
for th in (-70, -35, 0, 35, 70):
    p, n = ring_pt(HEAD, 4.275, 270 + th, 0.0)
    puck(plate, p, n, 0.01, 0.012, seg=6)
for th in (-92, 92):
    for z in (4.4, 4.6, 4.95, 5.1):
        p, n = ring_pt(HEAD, z, 270 + th, 0.0)
        puck(plate, p, n, 0.01, 0.012, seg=6)
for th in (-60, -20, 20, 60):
    p, n = ring_pt(HEAD, 5.19, 270 + th, 0.0)
    puck(plate, p, n, 0.009, 0.012, seg=6)
lathe(plate, (0, -0.05, 5.292), (0, 0, 1), [(0.0, 0.034), (0.012, 0.034), (0.018, 0.02), (0.019, 0.001)], seg=12)   # crown bolt where the top plates meet
for _bm in (plate, joint, steel, black, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.0055                      # stitch radius

loft(shirt, [fb(4.00, 0.33, -0.26, 0.33), fb(4.135, 0.305, -0.25, 0.31), fb(4.135, 0.29, -0.235, 0.295), fb(4.02, 0.30, -0.24, 0.30)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.03, s * 0.27, 4.03), (s * 0.08, s * 0.29, 3.97), (s * 0.19, s * 0.255, 3.90)], 0.016, nx=4)
patch(tie, SS, [(-0.08, 0.08, 4.04), (-0.105, 0.105, 3.97), (-0.065, 0.065, 3.89)], 0.034, nx=4)
patch(tie, SS, [(-0.06, 0.06, 3.895), (-0.10, 0.10, 3.70), (-0.11, 0.11, 3.59)], 0.01, nx=4)

panel(placket, TS, [(-0.02, 2.178), (0.15, 2.178), (0.15, 3.33), (0.05, 3.545), (-0.02, 3.545)], lambda x, z: 0.005, cuts=2)
for z in (3.36, 3.13, 2.90, 2.655, 2.385):
    p = surf(TS, 0.045, z, 0.016)
    nrm = (surf(TS, 0.045, z, 1.0) - surf(TS, 0.045, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.05), (0.011, 0.05), (0.022, 0.039), (0.022, 0.029), (0.014, 0.027)], seg=14)
    lathe(pewter, p, nrm, [(0.011, 0.027), (0.027, 0.02), (0.033, 0.005)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.058), (0.007, 0.058)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.13, 3.33 - (3.33 - 2.25) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.026) for x, z in edge], [SR] * len(edge), seg=4)
hem = [ring_pt(TS, 2.245, a, 0.005)[0] for a in range(-76, 257, 6)]
tube(stitch, hem, [SR] * len(hem), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)


def roll_lift(x, z):
    return 0.011 + 0.03 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.14)


def flat_lift(x, z):
    return 0.007


g = front_gap
for s in (-1, 1):
    lapel = [(0.006, 3.565), (0.50, 3.80), (0.535, 3.885), (0.34, 3.905), (g(3.92), 3.92), (g(3.80), 3.80), (g(3.68), 3.68)]
    collar_front = [(g(3.92), 3.92), (0.34, 3.905), (0.545, 3.91), (0.565, 3.985), (0.44, 4.03), (g(4.03), 4.03)]
    flap = [(0.33, 2.69), (0.60, 2.69), (0.60, 2.50), (0.58, 2.47), (0.35, 2.47), (0.33, 2.50)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.03, inset=0.022, step=0.05, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.027, inset=0.02, step=0.05, radius=SR)
breast = [(0.33, 3.385), (0.66, 3.385), (0.66, 3.06), (0.62, 3.01), (0.37, 3.01), (0.33, 3.06)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.027, inset=0.02, step=0.05, radius=SR)
panel(pockets, TS, [(0.33, 3.385), (0.66, 3.385), (0.66, 3.33), (0.33, 3.33)], lambda x, z: 0.016, cuts=1)
pocket_sq = [surf(TS, x, z, 0.03) for x, z in ((0.36, 3.38), (0.63, 3.38), (0.625, 3.46), (0.575, 3.435), (0.545, 3.52),
                                               (0.50, 3.44), (0.465, 3.53), (0.43, 3.44), (0.38, 3.48))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')

# Back: a yoke strap on each shoulder with three studs, and a half belt with five studs.
for s in (-1, 1):
    o = [(s * x, z) for x, z in ((0.40, 3.80), (0.55, 3.815), (0.90, 3.54), (0.81, 3.43))]
    panel(straps, TS, o, lambda x, z: 0.008, back=True, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.027, inset=0.018, back=True, step=0.05, radius=SR)
    for x, z in ((0.50, 3.775), (0.61, 3.68), (0.72, 3.59), (0.82, 3.505)):
        p = surf(TS, s * x, z, 0.027, back=True)
        nrm = (surf(TS, s * x, z, 1.0, back=True) - surf(TS, s * x, z, 0.0, back=True)).normalized()
        lathe(pewter, p, nrm, [(0.0, 0.026), (0.011, 0.026), (0.02, 0.012), (0.023, 0.001)], seg=10)
belt = [(-0.50, 2.20), (-0.50, 2.32)] + [(x, 2.375 - 0.055 * (x / 0.5) ** 2) for x in (-0.38, -0.19, 0.0, 0.19, 0.38)] + [(0.50, 2.32), (0.50, 2.20)]
panel(straps, TS, belt, lambda x, z: 0.008, back=True, cuts=2)
topstitch(stitch, TS, belt, lambda x, z: 0.027, inset=0.02, back=True, step=0.05, radius=SR)
for x in (-0.40, -0.20, 0.0, 0.20, 0.40):
    z = 2.30 - 0.035 * (x / 0.5) ** 2
    p = surf(TS, x, z, 0.027, back=True)
    nrm = (surf(TS, x, z, 1.0, back=True) - surf(TS, x, z, 0.0, back=True)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.03), (0.011, 0.03), (0.021, 0.015), (0.024, 0.001)], seg=10)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion: lies on the closed jacket front, tilted to the chest's slope, hanging from a cord under the collar.
slope = (surf(TS, 0, 3.52).y - surf(TS, 0, 3.32).y) / 0.2
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, 3.41) + mn * 0.04
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.172), (0.04, 0.172), (0.054, 0.16), (0.055, 0.137), (0.038, 0.134)], seg=28)
lathe(medal_p, mc, mn, [(0.036, 0.134), (0.044, 0.08), (0.047, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.20 + mn * 0.03
lathe(medal_p, mc + mt * 0.164 + mn * 0.027, mt, [(0.0, 0.03), (0.027, 0.035), (0.054, 0.024)], seg=10)
lathe(medal_p, bail - Vector((0.03, 0, 0)), (1, 0, 0), [(0.0, 0.027), (0.06, 0.027)], seg=10)
for pts in (((-0.032, 0.094), (0.032, 0.094), (0.021, 0.054), (-0.021, 0.054)),
            ((-0.021, 0.044), (0.021, 0.044), (0.05, -0.054), (0.0, -0.10), (-0.05, -0.054))):
    loop = [mc + mn * 0.05 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    for a, b in zip(loop, loop[1:] + loop[:1]):
        tube(medal_j, [a, b], [0.006, 0.006], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.25, 3.99, 0.03), surf(TS, s * (g(3.86) + 0.016), 3.86, 0.046), surf(TS, s * (g(3.72) + 0.016), 3.72, 0.046),
           surf(TS, s * 0.03, 3.615, 0.048), bail + Vector((s * 0.016, 0, 0))]
    tube(cord, pts, [0.012] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("YM_Shirt", shirt, M_SHIRT, 30)
new_obj("YM_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.013)
new_obj("YM_Stitching", stitch, M_STITCH, 40)
new_obj("YM_Tie", tie, M_TIE, 30, outward=True, thickness=0.02)
new_obj("YM_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.016)
new_obj("YM_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.027)
new_obj("YM_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.017)
new_obj("YM_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.017)
new_obj("YM_Medallion", medal_p, M_PEWTER, 32)
new_obj("YM_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("YM_Cord", cord, M_JOINT, 40)
new_obj("YM_Plates", plate, M_PLATE, 32)
new_obj("YM_Joints", joint, M_JOINT, 40)
new_obj("YM_Steel", steel, M_STEEL, 40)
new_obj("YM_Buttons", pewter, M_PEWTER, 32)

# ---------------------------------------------------------------- check camera + light, stats
cam = bpy.data.objects.new("YMCam", bpy.data.cameras.new("YMCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("YMSun", bpy.data.lights.new("YMSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("YMFill", bpy.data.lights.new("YMFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 110
fill.data.size = 6
fill.location = (-6, -7, 4)
fill.rotation_euler = (Vector((0, 0, 2.4)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
