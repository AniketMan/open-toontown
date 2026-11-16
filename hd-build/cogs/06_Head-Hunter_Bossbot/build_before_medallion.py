"""Build the HD HeadHunter (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (539 px = 7.5 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit A's rest pose at native size (game / 1.073).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/06_Head-Hunter_Bossbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.09
K = 6.5 / 6.06          # suit A scale for this cog
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
if scene.world.node_tree.nodes.get('Background'):
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.6


def get_col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("HeadHunter")
refcol = get_col("HeadHunter_Reference")
root = bpy.data.objects.new("HeadHunter", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "refplanes/hh_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 7.8
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
M_SUIT = pmat("HH_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18), weave=0.5, bump=0.25,
              bscale=75, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("HH_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("HH_Stitch", (0.66, 0.50, 0.42), 0.85, var=0.2)
M_PLATE = pmat("HH_Plate", (0.78, 0.63, 0.53), 0.42, 0.1, var=0.22, grime=0.45, wear=0.1, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_HAND = pmat("HH_Hand", (0.76, 0.60, 0.50), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1, bscale=45, rvar=0.14, nscale=6.0)
M_JOINT = pmat("HH_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("HH_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("HH_Hair", (0.012, 0.011, 0.011), 0.3, 0.2, var=0.4, wear=0.15, bump=0.2, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_HAT = pmat("HH_Hat", (0.014, 0.012, 0.011), 0.7, var=0.4, wear=0.1, bump=0.3, bscale=200, rvar=0.1, sheen=0.3)
M_BAND = pmat("HH_HatBand", (0.12, 0.04, 0.025), 0.5, var=0.3, weave=0.4, sheen=0.3)
M_EYE = pmat("HH_Eye", (0.45, 0.38, 0.30), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("HH_Iris", (0.02, 0.016, 0.014), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("HH_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("HH_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("HH_Pewter", (0.60, 0.48, 0.40), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("HH_Shirt", (0.82, 0.74, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("HH_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

plate, joint, steel, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()


def merge(dst, src, weld=0.0):
    if weld:
        bmesh.ops.remove_doubles(src, verts=src.verts, dist=weld)
    me = bpy.data.meshes.new("tmp")
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


# ---------------------------------------------------------------- jacket (game units, modelled standing)
# A wedge: narrow hips flaring to very wide shoulders. Half-widths from the front and back views, depth from the side.
TORSO = [fb(3.48, 0.78, -0.80, 0.47), fb(3.80, 0.78, -0.80, 0.47), fb(4.20, 0.80, -0.78, 0.50),
         fb(4.60, 0.90, -0.85, 0.56), fb(5.00, 1.06, -0.98, 0.64), fb(5.40, 1.26, -1.07, 0.72),
         fb(5.75, 1.52, -1.03, 0.80), fb(6.00, 1.74, -0.90, 0.82), fb(6.15, 1.72, -0.78, 0.80),
         fb(6.30, 1.42, -0.65, 0.72), fb(6.42, 0.98, -0.55, 0.62), fb(6.52, 0.60, -0.45, 0.52),
         fb(6.58, 0.42, -0.38, 0.45)]
TS = TORSO
BREAK = 5.60


def front_gap(z):
    return 0.004 if z <= BREAK else 0.004 + 0.34 * min(1.0, (z - BREAK) / (6.5 - BREAK)) ** 1.1


SHIRT_IN = {5.00: 0.12, 5.40: 0.12, 5.75: 0.12, 6.00: 0.30, 6.15: 0.35, 6.30: 0.25, 6.42: 0.07, 6.52: 0.07}
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
COLLAR = [fb(6.52, 0.42, -0.36, 0.47), fb(6.68, 0.43, -0.37, 0.50), fb(6.67, 0.56, -0.45, 0.60), fb(6.525, 0.80, -0.55, 0.70)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.03 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("HH_Collar", bm, M_SUIT, outward=False, thickness=0.036)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 6.565)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt24_1 / scale_jnt27_1 carry the upper
# arms, Lh_arm / Rh_arm the forearms, scale_jnt3_1 / scale_jnt4_1 the thighs, jnt3_2 / jnt4_2 the shins,
# to_LegL / to_legR the feet and to_MAIN the pelvis. Suit A's rest pose is not symmetric (shoulders at x 1.67 and
# -1.61, wrists at 3.87 and -3.91), so the right arm is the left one refitted to the right arm's own joints.
RIG = json.load(open(SP + "hh_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.09 / K
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


SLEEVE = [(SX - 0.22, 0.11, AZ, 0.10, 0.08), (SX - 0.19, 0.11, AZ, 0.26, 0.24), (SX - 0.12, 0.11, AZ, 0.39, 0.36),
          (SX - 0.05, 0.11, AZ, 0.45, 0.42), (SX + 0.03, 0.11, AZ, 0.47, 0.45), (2.10, 0.10, AZ, 0.48, 0.47),
          (2.55, 0.09, AZ, 0.46, 0.45), (3.10, 0.08, AZ, 0.42, 0.41), (3.64, 0.07, AZ, 0.39, 0.38), (3.62, 0.07, AZ, 0.275, 0.265)]
BAND = [(3.20, 0.08, AZ, 0.435, 0.425), (3.655, 0.07, AZ, 0.41, 0.40)]


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
new_obj("HH_Sleeves", both_arms(sleeve_cloth), M_SUIT, 60, rest=True)
# shoulder fillers: a ball in the suit's own cloth on each shoulder joint, inside the sleeve head. It stays with the
# shoulder, so whatever angle the arm hangs at there is a joint between arm and body, never a gap.
ball = bmesh.new()
BALL_IN = globals().get("BALL_IN", 0.26)                         # how far in toward the body from the shoulder joint the ball sits
BALL_C = Vector((LS.x - BALL_IN, 0.11, AZ))
for bone, c in (("shoulderL1", BALL_C), ("shoulderR1", to_right(BALL_C))):
    bmesh.ops.create_uvsphere(ball, u_segments=24, v_segments=14, radius=0.37, matrix=Matrix.Translation(c))
    tag(ball, bone)
new_obj("HH_ShoulderJoints", ball, globals().get("M_DEBUG_BALL", M_SUIT), 60, rest=True)
new_obj("HH_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("HH_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

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
new_obj("HH_HandPlates", plate_r, M_HAND, 32, rest=True)
new_obj("HH_HandJoints", joint_r, M_JOINT, 40, rest=True)

# ---- trousers: one sealed garment. Seat bowl on the pelvis (to_MAIN, z 3.53) running up inside the jacket (hem at
# z 3.19 here); legs straight down round hip (z 3.5) -> knee (1.95) -> ankle (0.08).
seat = bmesh.new()
loft(seat, [(2.75, 0, -0.10, 0.06, 0.06), (2.80, 0, -0.10, 0.30, 0.26), (2.90, 0, -0.11, 0.50, 0.40), (3.05, 0, -0.12, 0.62, 0.48),
            (3.30, 0, -0.13, 0.68, 0.52), (3.60, 0, -0.13, 0.69, 0.53), (3.90, 0, -0.12, 0.60, 0.48), (4.05, 0, -0.10, 0.4, 0.35)],
     seg=24, centres=(270, 90))
new_obj("HH_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
HIP = {1: JR["scale_jnt3_1"].x, -1: -JR["scale_jnt4_1"].x}       # 0.44 and 0.39: each leg sits on its own hip joint
for s in (-1, 1):
    cx = HIP[s]
    w = min(0.33, cx - 0.012)                                    # the legs touch down the middle but do not overlap
    LEG = [(0.42, cx, 0.0, w, 0.465), (0.60, cx, 0.0, w - 0.01, 0.455), (1.95, cx, -0.02, w - 0.005, 0.46),
           (2.80, cx, -0.03, w, 0.50), (3.30, cx, -0.04, w, 0.54)]
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("HH_Trousers", bm, M_SUIT, 60, rest=True)

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
new_obj("HH_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("HH_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.09


# ---------------------------------------------------------------- head: a heavy block, wide at the jaw, narrow at the crown
# HEAD is the outer surface (front view half-widths, side view front and back), a squared-off section. Pieces: the
# face shell in two halves on a hairline centre seam, each with its eye slot and the crease from beside the nose to
# the mouth corner; the jaw plate; the frown, a slot between them; back plates; the flat-topped hair shell with its
# widow's peak; ringed ear discs; nose and brows. All over a closed inner shell.
HEAD = [fb(6.73, 0.32, -0.41, 0.22), fb(6.85, 0.34, -0.40, 0.21), fb(7.00, 0.345, -0.385, 0.19),
        fb(7.15, 0.32, -0.355, 0.16), fb(7.30, 0.285, -0.32, 0.13), fb(7.45, 0.25, -0.285, 0.09),
        fb(7.50, 0.24, -0.27, 0.08)]
HEAD_N = 3.0
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.0015
CORE_IN = 0.012
BASE_Z, TOP_Z, FA = 6.73, 7.50, 100.0
MX, MZ0, MZ1 = 0.29, 6.965, 6.86          # mouth corner distance out; height of the frown at the centre and at the corners


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def XR(th):                      # how far out from the centre line a column is (at cheek height)
    return 0.345 * sq(math.sin(math.radians(min(abs(th), 90.0))), HEAD_N)


def th_of(x, z):                 # the column that is x out from the centre line at height z
    return math.degrees(math.asin(min(1.0, (min(0.999, x / interp(HEAD, z)[3])) ** (HEAD_N / 2.0))))


def agap(z, d=GAP):
    return th_of(d, z)


def frown(X):
    return MZ0 - (MZ0 - MZ1) * min(1.0, X / MX) ** 2


def lip(X):                      # half-height of the mouth slot: widest in the middle, a hairline from the corners on
    return GAP + 0.012 * math.sqrt(max(0.0, 1 - (X / MX) ** 2))


def crease(X):                   # from beside the nose down and out to the mouth corner
    return 7.20 if X < 0.06 else (7.20 - 0.30 * (X - 0.06) / 0.21 if X < 0.27 else 6.90)


def crease_gap(X):
    return 0.002 * min(1.0, (X - 0.06) / 0.02, (0.27 - X) / 0.02) if 0.06 < X < 0.27 else 0.0


EX, EZ, EA, EB = 0.13, 7.262, 0.055, 0.028


def eye(X):                      # (below centre, above centre): the brow hangs over the top of the eye
    t = (X - EX) / EA
    return (EB * math.sqrt(1 - t * t), 0.45 * EB * math.sqrt(1 - t * t)) if abs(t) < 1 else (0.0, 0.0)


def bulge(X, z):
    brow = 0.022 * math.exp(-((X - 0.11) / 0.12) ** 2 - ((z - 7.335) / 0.035) ** 2)
    cheek = 0.012 * math.exp(-((X - 0.24) / 0.09) ** 2 - ((z - 7.05) / 0.08) ** 2)
    return brow + cheek


PHI = [2.5 * i for i in range(41)]                               # 0 .. 100
BACK_PHI = [FA + 5.0 * i for i in range(17)]
A_F, B_F, C_F = (0.0, 0.33, 0.66, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.2, 0.45, 0.75, 1.0)
CHIN_F = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def face_zs(th):
    X = XR(th)
    bot = frown(X) + lip(X)
    zc, gc = crease(X), crease_gap(X)
    el, eh = eye(X)
    return ([bot + (zc - gc - bot) * f for f in A_F] + [zc + gc + (EZ - el - zc - gc) * f for f in B_F] +
            [EZ + eh + (TOP_Z - EZ - eh) * f for f in C_F])


def chin_zs(th):
    X = XR(th)
    top = frown(X) - lip(X)
    return [BASE_Z + (top - BASE_Z) * f for f in CHIN_F]


plates = bmesh.new()
for s in (1, -1):
    t = bmesh.new()
    cols = [[t.verts.new(hp(s * max(th, agap(z)), z, bulge(XR(th), z))) for z in face_zs(th)] for th in PHI]
    for a, b in zip(cols, cols[1:]):
        for k in range(12):
            if k not in (3, 7):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0004)
    grid(plates, [[hp(s * max(th, agap(6.8)), chin_zs(th)[k]) for th in PHI] for k in range(len(CHIN_F))])
    BACK_Z = chin_zs(FA) + face_zs(FA)
    rows = []
    for z in BACK_Z:
        g = agap(z)
        rows.append([hp(s * a, z) for a in [BACK_PHI[0] + g] + BACK_PHI[1:-1] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("HH_HeadPlates", plates, M_PLATE, 55, outward=True, thickness=-0.022)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("HH_HeadCore", core, M_JOINT, 60)
loft(plate, [fb(6.68, 0.22, -0.30, 0.16), fb(6.69, 0.29, -0.38, 0.20), fb(6.7305, 0.3205, -0.4105, 0.2205)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, -0.02, 6.42), (0, 0, 1), [(0.0, 0.20), (0.05, 0.24), (0.085, 0.24), (0.095, 0.205), (0.11, 0.255), (0.15, 0.255),
                                            (0.16, 0.215), (0.175, 0.26), (0.215, 0.26), (0.225, 0.22), (0.28, 0.22)], seg=28)

# eyes: small and dark under the brow
eyes, iris = bmesh.new(), bmesh.new()
for s in (-1, 1):
    rows = [[hp(s * th_of(EX + EA * 1.15 * (i / 4 - 1), z), z, bulge(EX, z) - 0.007) for i in range(9)] for z in (7.225, 7.25, 7.275, 7.30)]
    grid(eyes, rows)
    p, n = ring_pt(HEAD, 7.26, 270 + s * th_of(EX - 0.008, 7.26), bulge(EX, 7.26) - 0.006)
    puck(iris, p, n, 0.024, 0.005, seg=12)
tag(eyes, 'joint_head')
tag(iris, 'joint_head')
new_obj("HH_Eyes", eyes, M_EYE, 60, outward=True)
new_obj("HH_Iris", iris, M_IRIS, 40)

# brows: thick black bars slanting down to meet over the nose
brow = bmesh.new()
for s in (-1, 1):
    rows = [[], []]
    for i in range(9):
        tt = i / 8
        X = 0.015 + 0.20 * tt
        zc = 7.325 + 0.09 * tt
        hw_ = 0.024 - 0.012 * tt
        for k in (0, 1):
            z = zc + (hw_ if k else -hw_)
            rows[k].append(hp(s * th_of(X, z), z, bulge(X, z) + 0.008))
    grid(brow, rows)
tag(brow, 'joint_head')
new_obj("HH_Brows", brow, M_HAIR, 35, outward=True, thickness=-0.016)

# nose: a long wedge from between the brows to a blunt end, with a wing each side
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (7.33, 7.26, 7.18, 7.11, 7.07, 7.045, 7.03)
NR = (0.02, 0.026, 0.034, 0.044, 0.05, 0.045, 0.02)
tube(nose, [Vector((0, ny(z) + r * 0.35, z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.05, ny(7.065) + 0.03, 7.065)) @ Matrix.Diagonal((0.035, 0.04, 0.028, 1.0)))
tag(nose, 'joint_head')
new_obj("HH_Nose", nose, M_PLATE, 60)

# hair shell: flat on top, down to a peak over the nose, cut back past the ears and down the back of the head
def hairline(th):
    X = XR(th)
    a = abs(th)
    if a <= 80:
        return 7.36 + 0.09 * min(1.0, X / 0.20) ** 0.8
    if a <= 110:
        return 7.45 - 0.25 * (a - 80) / 30
    if a <= 165:
        return 7.20 - 0.30 * (a - 110) / 55
    return 6.90


hair = bmesh.new()
HT = [-180 + 5.0 * i for i in range(73)]
grid(hair, [[hp(th, hairline(th) + (TOP_Z + 0.01 - hairline(th)) * f, 0.012) for th in HT] for f in (0.0, 0.25, 0.5, 0.75, 1.0)])
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0003)
tag(hair, 'joint_head')
new_obj("HH_Hair", hair, M_HAIR, 50, outward=True, thickness=-0.012)
htop = bmesh.new()
_z, _cx, _cy, _rx, _ry = HEAD[-1]
loft(htop, [(TOP_Z + 0.010, _cx, _cy, _rx + 0.0115, _ry + 0.0115), (TOP_Z + 0.0115, _cx, _cy, _rx * 0.5, _ry * 0.5),
            (TOP_Z + 0.012, _cx, _cy, 0.02, 0.02)], seg=36, power=HEAD_N, caps=(False, True))
tag(htop, 'joint_head')
new_obj("HH_HairTop", htop, M_HAIR, 50, outward='up')

# ear discs: concentric rings on the jaw pivots
for a in (4, 176):
    p, n = ring_pt(HEAD, 7.12, a, 0.0)
    lathe(steel, p - n * 0.008, n, [(0.0, 0.09), (0.03, 0.09), (0.04, 0.08), (0.04, 0.067), (0.028, 0.064)], seg=24)
    lathe(pewter, p, n, [(0.02, 0.058), (0.042, 0.058), (0.047, 0.052), (0.047, 0.041), (0.02, 0.038)], seg=20)
    lathe(steel, p, n, [(0.02, 0.032), (0.05, 0.032), (0.054, 0.027), (0.054, 0.021), (0.02, 0.018)], seg=16)
    lathe(pewter, p, n, [(0.02, 0.015), (0.058, 0.013), (0.063, 0.006), (0.064, 0.001)], seg=12)
# rivets
for X, z in ((0.02, 6.80), (0.30, 6.80), (0.31, 6.93), (0.02, 7.40), (0.26, 7.15)):
    for s in (-1, 1):
        p, n = ring_pt(HEAD, z, 270 + s * th_of(X, z), bulge(X, z))
        puck(plate, p, n, 0.009, 0.01, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.008

loft(shirt, [fb(6.40, 0.40, -0.32, 0.40), fb(6.62, 0.36, -0.30, 0.36), fb(6.62, 0.34, -0.28, 0.34), fb(6.43, 0.35, -0.29, 0.35)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.04, s * 0.36, 6.56), (s * 0.10, s * 0.40, 6.42), (s * 0.22, s * 0.33, 6.25)], 0.02, nx=4)
patch(tie, SS, [(-0.10, 0.10, 6.50), (-0.13, 0.13, 6.40), (-0.08, 0.08, 6.27)], 0.045, nx=4)
patch(tie, SS, [(-0.07, 0.07, 6.27), (-0.10, 0.10, 6.10), (-0.115, 0.115, 6.00), (-0.12, 0.12, 5.875), (-0.13, 0.13, 5.75), (-0.14, 0.14, 5.60),
                (-0.15, 0.15, 5.40), (-0.11, 0.11, 5.22)], 0.014, nx=4)

panel(placket, TS, [(-0.03, 3.49), (0.20, 3.49), (0.20, 5.25), (0.07, 5.56), (-0.03, 5.56)], lambda x, z: 0.006, cuts=2)
for z in (4.90, 4.65, 4.38, 4.10, 3.82):
    p = surf(TS, 0.07, z, 0.02)
    nrm = (surf(TS, 0.07, z, 1.0) - surf(TS, 0.07, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.055), (0.012, 0.055), (0.025, 0.043), (0.025, 0.032), (0.015, 0.029)], seg=14)
    lathe(pewter, p, nrm, [(0.012, 0.029), (0.03, 0.02), (0.036, 0.005)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.064), (0.007, 0.064)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.175, 5.22 - (5.22 - 3.74) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.032) for x, z in edge], [SR] * len(edge), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.008)[0] for a in HB] for z in (3.486, 3.58, 3.69)])
tag(hemband, '@jacket')
new_obj("HH_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.02)
hs = [ring_pt(TS, 3.665, a, 0.033)[0] for a in HB]
tube(stitch, hs, [SR] * len(hs), seg=4)
for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):
    p, n = ring_pt(TS, 3.575, a, 0.028)
    lathe(pewter, p, n, [(0.0, 0.04), (0.013, 0.04), (0.025, 0.02), (0.03, 0.001)], seg=10)


def roll_lift(x, z):
    return 0.014 + 0.04 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.18)


def flat_lift(x, z):
    return 0.009


def studs(points, back):
    for x, z in points:
        p = surf(TS, x, z, 0.036, back=back)
        nrm = (surf(TS, x, z, 1.0, back=back) - surf(TS, x, z, 0.0, back=back)).normalized()
        lathe(pewter, p, nrm, [(0.0, 0.033), (0.013, 0.033), (0.024, 0.016), (0.028, 0.001)], seg=10)


g = front_gap
for s in (-1, 1):
    lapel = [(0.006, 5.59), (0.74, 5.90), (0.80, 6.02), (0.60, 6.22), (g(6.25), 6.25), (g(6.0), 6.0), (g(5.8), 5.8)]
    collar_front = [(g(6.25), 6.25), (0.60, 6.22), (0.84, 6.22), (0.87, 6.32), (0.66, 6.46), (g(6.46), 6.46)]
    flap = [(0.42, 4.25), (0.74, 4.25), (0.74, 4.07), (0.72, 4.04), (0.44, 4.04), (0.42, 4.07)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        if outline is lapel:                                 # the collar piece is small and folded: stitching only on the lapel
            topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.042, inset=0.03, step=0.07, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)
    # studded straps: one down the front of each shoulder, one across each shoulder blade
    for outline, back, pts in (([(0.74, 6.30), (0.94, 6.33), (1.30, 6.03), (1.17, 5.92)], False, ((0.88, 6.27), (1.02, 6.15), (1.17, 6.02))),
                               ([(0.60, 6.34), (0.84, 6.38), (1.22, 5.86), (1.02, 5.72)], True, ((0.76, 6.30), (0.88, 6.14), (1.00, 5.98), (1.10, 5.83)))):
        o = [(s * x, z) for x, z in outline]
        panel(straps, TS, o, lambda x, z: 0.012, back=back, cuts=2)
        topstitch(stitch, TS, o, lambda x, z: 0.04, inset=0.026, back=back, step=0.07, radius=SR)
        studs([(s * x, z) for x, z in pts], back)
breast = [(0.47, 5.30), (0.93, 5.30), (0.93, 4.84), (0.88, 4.78), (0.52, 4.78), (0.47, 4.84)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)
panel(pockets, TS, [(0.47, 5.30), (0.93, 5.30), (0.93, 5.22), (0.47, 5.22)], lambda x, z: 0.022, cuts=1)
pocket_sq = [surf(TS, x, z, 0.04) for x, z in ((0.51, 5.29), (0.89, 5.29), (0.88, 5.38), (0.83, 5.36), (0.78, 5.47),
                                              (0.72, 5.37), (0.66, 5.48), (0.61, 5.37), (0.54, 5.42))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 5.30
slope = (surf(TS, 0, MZ + 0.12).y - surf(TS, 0, MZ - 0.12).y) / 0.24
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.05
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.23), (0.05, 0.23), (0.068, 0.214), (0.07, 0.184), (0.048, 0.18)], seg=28)
lathe(medal_p, mc, mn, [(0.046, 0.18), (0.056, 0.10), (0.06, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.27 + mn * 0.038
lathe(medal_p, mc + mt * 0.22 + mn * 0.035, mt, [(0.0, 0.038), (0.035, 0.046), (0.07, 0.032)], seg=10)
lathe(medal_p, bail - Vector((0.038, 0, 0)), (1, 0, 0), [(0.0, 0.035), (0.076, 0.035)], seg=10)
for pts in (((-0.044, 0.126), (0.044, 0.126), (0.03, 0.07), (-0.03, 0.07)),
            ((-0.03, 0.06), (0.03, 0.06), (0.068, -0.07), (0.0, -0.134), (-0.068, -0.07))):
    loop = [mc + mn * 0.064 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    for a, b in zip(loop, loop[1:] + loop[:1]):
        tube(medal_j, [a, b], [0.008, 0.008], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.32, 6.42, 0.03), surf(TS, s * (g(6.15) + 0.02), 6.15, 0.062), surf(TS, s * (g(5.9) + 0.018), 5.9, 0.062),
           surf(TS, s * 0.035, 5.68, 0.066), bail + Vector((s * 0.02, 0, 0))]
    tube(cord, pts, [0.014] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("HH_Shirt", shirt, M_SHIRT, 30)
new_obj("HH_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.018)
new_obj("HH_Stitching", stitch, M_STITCH, 40)
new_obj("HH_Tie", tie, M_TIE, 30, outward=True, thickness=0.027)
new_obj("HH_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.021)
new_obj("HH_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.036)
new_obj("HH_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("HH_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("HH_Medallion", medal_p, M_PEWTER, 32)
new_obj("HH_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("HH_Cord", cord, M_JOINT, 40)
new_obj("HH_Plates", plate, M_PLATE, 32)
new_obj("HH_Joints", joint, M_JOINT, 40)
new_obj("HH_Steel", steel, M_STEEL, 40)
new_obj("HH_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("HHCam", bpy.data.cameras.new("HHCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("HHSun", bpy.data.lights.new("HHSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("HHFill", bpy.data.lights.new("HHFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 230
fill.data.size = 9
fill.location = (-9, -10, 5.5)
fill.rotation_euler = (Vector((0, 0, 3.5)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
