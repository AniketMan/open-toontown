"""Build the HD BackStabber (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (539 px = 7.5 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit A's rest pose at native size (game / 1.073).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/13_Back-Stabber_Lawbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.09
K = 4.5 / 6.06         # suit A scale for this cog
# The coat is the Head Hunter's cut (same body, suit A). It is laid out at his size and brought to this cog's at the end.
BODY_S = 4.5 / 6.5
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


col = get_col("BackStabber")
refcol = get_col("BackStabber_Reference")
root = bpy.data.objects.new("BackStabber", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    import os
    if not os.path.exists(SP + "refplanes/bk_ref_%s.png" % name):
        return
    img = bpy.data.images.load(SP + "refplanes/bk_ref_%s.png" % name, check_existing=True)
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
M_SUIT = pmat("BK_Suit", (0.028, 0.032, 0.085), 0.88, var=0.35, grime=0.12, stripe=(0.045, 0.05, 0.12), weave=0.5, bump=0.25,
              bscale=75, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("BK_Lining", (0.012, 0.013, 0.03), 0.8, var=0.3)
M_STITCH = pmat("BK_Piping", (0.22, 0.035, 0.27), 0.85, var=0.2)
M_PLATE = pmat("BK_Plate", (0.40, 0.24, 0.70), 0.42, 0.1, var=0.22, grime=0.45, wear=0.1, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_HAND = pmat("BK_Hand", (0.56, 0.50, 0.78), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1, bscale=45, rvar=0.14, nscale=6.0)
M_JOINT = pmat("BK_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("BK_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("BK_Hair", (0.36, 0.04, 0.03), 0.3, 0.2, var=0.4, wear=0.15, bump=0.2, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_HAT = pmat("BK_Hat", (0.014, 0.012, 0.011), 0.7, var=0.4, wear=0.1, bump=0.3, bscale=200, rvar=0.1, sheen=0.3)
M_BAND = pmat("BK_HatBand", (0.12, 0.04, 0.025), 0.5, var=0.3, weave=0.4, sheen=0.3)
M_EYE = pmat("BK_Eye", (0.90, 0.88, 0.80), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("BK_Iris", (0.02, 0.016, 0.014), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("BK_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("BK_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("BK_Pewter", (0.40, 0.41, 0.46), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("BK_Shirt", (0.82, 0.74, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("BK_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

plate, joint, steel, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

M_LID = pmat("BK_Lid", (0.30, 0.17, 0.56), 0.4, 0.1, var=0.25, grime=0.3, bump=0.08, bscale=40, rvar=0.12, coat=0.2)
M_FANG = pmat("BK_Teeth", (0.92, 0.90, 0.84), 0.25, var=0.1, grime=0.2, coat=0.5)
M_BOW = pmat("BK_Bow", (0.60, 0.04, 0.03), 0.6, var=0.25, weave=0.5, sheen=0.3, rvar=0.1)
M_BROW = pmat("BK_Dark", (0.035, 0.03, 0.07), 0.4, 0.1, var=0.3)
M_IRISRING = pmat("BK_IrisRing", (0.10, 0.14, 0.30), 0.2, var=0.2, coat=0.6)


def stud(bm, p, n, r=0.036):
    lathe(bm, p, n, [(0.0, r), (0.4 * r, r), (0.78 * r, 0.5 * r), (0.9 * r, 0.05 * r)], seg=8)


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
new_obj("BK_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(9, 24, 9))
for v in bm.verts:
    if v.co.z > 6.565 and v.co.y < 0:
        v.co.z -= 0.06 * min(1.0, -v.co.y / 0.3)
new_obj("BK_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.05)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(3.478, 0, hem_cy, hem_rx - 0.012, hem_ry - 0.012), (3.52, 0, -0.14, 0.64, 0.50)], seg=28, caps=(False, False))
new_obj("BK_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(6.44, 0.42, -0.36, 0.47), fb(6.56, 0.43, -0.37, 0.50), fb(6.55, 0.56, -0.45, 0.60), fb(6.44, 0.80, -0.55, 0.70)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.03 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("BK_Collar", bm, M_SUIT, outward=False, thickness=0.036)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 6.48)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt24_1 / scale_jnt27_1 carry the upper
# arms, Lh_arm / Rh_arm the forearms, scale_jnt3_1 / scale_jnt4_1 the thighs, jnt3_2 / jnt4_2 the shins,
# to_LegL / to_legR the feet and to_MAIN the pelvis. Suit A's rest pose is not symmetric (shoulders at x 1.67 and
# -1.61, wrists at 3.87 and -3.91), so the right arm is the left one refitted to the right arm's own joints.
RIG = json.load(open(SP + "bs_rig.json"))
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


def sleeve_buttons(bm):                                          # studs round the band
    for k in range(8):
        a_ = 2 * math.pi * (k + 0.5) / 8
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(a_), math.sin(a_)))
        stud(bm, Vector((3.43, cy + (ry + 0.004) * n.y, cz + (rz + 0.004) * n.z)), n, 0.04)


def sleeve_stitch(bm):
    for x in (3.235, 3.63):
        _, cy, cz, ry, rz = BAND[0] if x < 3.4 else BAND[1]
        ring = [Vector((x, cy + (ry + 0.004) * math.cos(math.radians(a)), cz + (rz + 0.004) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(bm, ring, [0.016] * len(ring), seg=5)


# shoulder caps: a studded, piped plate of cloth over the top of each sleeve head, as on the sheet
CAP = [(SX - 0.12, 0.11, AZ, 0.41, 0.38), (SX - 0.03, 0.11, AZ, 0.475, 0.445), (SX + 0.08, 0.11, AZ, 0.495, 0.475), (SX + 0.24, 0.105, AZ, 0.50, 0.49),
       (SX + 0.40, 0.10, AZ, 0.50, 0.49)]
CAP_A = [-25 + 230 * i / 20 for i in range(21)]


def cap_pt(st, a_, lift):
    x_, cy, cz, ry, rz = st
    return Vector((x_, cy + (ry + lift) * math.cos(math.radians(a_)), cz + (rz + lift) * math.sin(math.radians(a_))))


def cap_cloth(bm):
    grid(bm, [[cap_pt(st, a_, 0.02) for a_ in CAP_A] for st in CAP])


def cap_studs(bm):
    for a_ in (0, 30, 60, 90, 120, 150, 180):
        n = Vector((0, math.cos(math.radians(a_)), math.sin(math.radians(a_))))
        stud(bm, cap_pt(CAP[4], a_, 0.04) - Vector((0.08, 0, 0)), n, 0.04)


def cap_pipe(bm):
    edge = [cap_pt(st, CAP_A[0], 0.04) for st in CAP] + [cap_pt(CAP[4], a_, 0.04) for a_ in CAP_A] + [cap_pt(st, CAP_A[-1], 0.04) for st in reversed(CAP)]
    tube(bm, edge, [0.016] * len(edge), seg=5)


_caps = {}
for _n, _f in (("cloth", cap_cloth), ("studs", cap_studs), ("pipe", cap_pipe)):
    _caps[_n] = both_arms(_f)
    tag(_caps[_n], '@sleeve')
_o = new_obj("BK_ShoulderCaps", _caps["cloth"], M_SUIT, 60, rest=True)
_s = _o.modifiers.new("Cloth thickness", 'SOLIDIFY')
_s.thickness, _s.offset = 0.04, 0.0
new_obj("BK_ShoulderCapStuds", _caps["studs"], M_PEWTER, 32, rest=True)
new_obj("BK_ShoulderCapPiping", _caps["pipe"], M_STITCH, 40, rest=True)
def shirt_cuff(bm):                                             # white shirt cuff showing between sleeve and hand
    xloft(bm, [(3.60, 0.07, AZ, 0.31, 0.30), (3.80, 0.07, AZ, 0.30, 0.29), (3.80, 0.07, AZ, 0.20, 0.19)], seg=20, caps=(False, False))


_cuffs = both_arms(shirt_cuff)
tag(_cuffs, '@sleeve')
new_obj("BK_ShirtCuffs", _cuffs, M_SHIRT, 40, rest=True)
pewter_r, stitch_r = both_arms(sleeve_buttons), both_arms(sleeve_stitch)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("BK_Sleeves", both_arms(sleeve_cloth), M_SUIT, 60, rest=True)
# shoulder fillers: a ball in the suit's own cloth on each shoulder joint, inside the sleeve head. It stays with the
# shoulder, so whatever angle the arm hangs at there is a joint between arm and body, never a gap.
ball = bmesh.new()
BALL_IN = globals().get("BALL_IN", 0.26)                         # how far in toward the body from the shoulder joint the ball sits
BALL_C = Vector((LS.x - BALL_IN, 0.11, AZ))
for bone, c in (("shoulderL1", BALL_C), ("shoulderR1", to_right(BALL_C))):
    bmesh.ops.create_uvsphere(ball, u_segments=24, v_segments=14, radius=0.37, matrix=Matrix.Translation(c))
    tag(ball, bone)
new_obj("BK_ShoulderJoints", ball, globals().get("M_DEBUG_BALL", M_SUIT), 60, rest=True)
new_obj("BK_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("BK_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

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
new_obj("BK_HandPlates", plate_r, M_HAND, 32, rest=True)
new_obj("BK_HandJoints", joint_r, M_JOINT, 40, rest=True)

# ---- trousers: one sealed garment. Seat bowl on the pelvis (to_MAIN, z 3.53) running up inside the jacket (hem at
# z 3.19 here); legs straight down round hip (z 3.5) -> knee (1.95) -> ankle (0.08).
seat = bmesh.new()
loft(seat, [(2.75, 0, -0.10, 0.06, 0.06), (2.80, 0, -0.10, 0.30, 0.26), (2.90, 0, -0.11, 0.50, 0.40), (3.05, 0, -0.12, 0.62, 0.48),
            (3.30, 0, -0.13, 0.68, 0.52), (3.60, 0, -0.13, 0.69, 0.53), (3.90, 0, -0.12, 0.60, 0.48), (4.05, 0, -0.10, 0.4, 0.35)],
     seg=24, centres=(270, 90))
new_obj("BK_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
HIP = {1: JR["scale_jnt3_1"].x, -1: -JR["scale_jnt4_1"].x}       # 0.44 and 0.39: each leg sits on its own hip joint
for s in (-1, 1):
    cx = HIP[s]
    w = min(0.33, cx - 0.012)                                    # the legs touch down the middle but do not overlap
    LEG = [(0.42, cx, 0.0, w, 0.465), (0.60, cx, 0.0, w - 0.01, 0.455), (1.95, cx, -0.02, w - 0.005, 0.46),
           (2.80, cx, -0.03, w, 0.50), (3.30, cx, -0.04, w, 0.54)]
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("BK_Trousers", bm, M_SUIT, 60, rest=True)
# studded band round each trouser hem, piped along its edges
hemb, studs_r, pipe_r = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    cx = HIP[s]
    rx, ry, z0, z1 = min(0.33, cx - 0.012), 0.465, 0.42, 0.86
    loft(hemb, [(z0 - 0.005, cx, 0.0, rx + 0.016, ry + 0.016), (z1, cx, 0.0, rx + 0.016, ry + 0.016)], seg=20, sx=s, caps=(False, False), centres=(270, 90))
    for k in range(8):
        a_ = 2 * math.pi * (k + 0.5) / 8
        nrm = Vector((s * math.cos(a_) / rx, math.sin(a_) / ry, 0)).normalized()
        stud(studs_r, Vector((s * (cx + (rx + 0.022) * math.cos(a_)), (ry + 0.022) * math.sin(a_), (z0 + z1) / 2)), nrm, 0.04)
    for zz in (z0 + 0.018, z1 - 0.018):
        ring = [Vector((s * (cx + (rx + 0.022) * math.cos(math.radians(a_))), (ry + 0.022) * math.sin(math.radians(a_)), zz)) for a_ in range(0, 361, 18)]
        tube(pipe_r, ring, [0.016] * len(ring), seg=5)
    for _b in (hemb, studs_r, pipe_r):
        tag(_b, '@legL' if s > 0 else '@legR')
new_obj("BK_TrouserBands", hemb, M_SUIT, 60, rest=True)
new_obj("BK_LimbStuds", studs_r, M_PEWTER, 32, rest=True)
new_obj("BK_TrouserPiping", pipe_r, M_STITCH, 40, rest=True)

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
new_obj("BK_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("BK_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.09


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

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.014

loft(shirt, [fb(6.34, 0.40, -0.32, 0.40), fb(6.52, 0.36, -0.30, 0.36), fb(6.52, 0.34, -0.28, 0.34), fb(6.37, 0.35, -0.29, 0.35)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.04, s * 0.36, 6.48), (s * 0.10, s * 0.40, 6.36), (s * 0.22, s * 0.33, 6.22)], 0.02, nx=4)
# bow tie: a knot and two wings on the shirt under the chin, dotted as on the original; the zip runs down from it
exec(compile(open(SP + "../medallion.py").read(), "medallion.py", "exec"), globals())
bowdots, zipteeth, ziptape = bmesh.new(), bmesh.new(), bmesh.new()
bow_c = surf(SS, 0.0, 6.33, 0.075)
bmesh.ops.create_uvsphere(tie, u_segments=14, v_segments=8, radius=1.0, matrix=Matrix.Translation(bow_c) @ Matrix.Diagonal((0.055, 0.055, 0.07, 1.0)))
BOW = [(0.023, 0.024, 0.028), (0.077, 0.034, 0.055), (0.153, 0.041, 0.089), (0.237, 0.041, 0.107), (0.278, 0.03, 0.10), (0.29, 0.012, 0.076)]
for sdx in (-1, 1):
    xloft(tie, [(x_, bow_c.y + 0.009, bow_c.z, ry_, rz_) for x_, ry_, rz_ in BOW], seg=16, sx=sdx)
    for ddx, ddz in ((0.10, 0.018), (0.16, -0.04), (0.17, 0.046), (0.232, 0.003), (0.24, -0.06), (0.245, 0.064)):
        puck(bowdots, bow_c + Vector((sdx * ddx, 0.009 - 0.0405, ddz)), (0, -1, 0), 0.013, 0.006, seg=8)
zipper(zipteeth, ziptape, SS, 6.20, 5.50, 1.55)

panel(placket, TS, [(-0.14, 3.49), (0.14, 3.49), (0.14, 5.30), (0.05, 5.56), (-0.05, 5.56), (-0.14, 5.30)], lambda x, z: 0.006, cuts=2)
for z in (4.98, 4.72, 4.46, 4.20, 3.94):          # a column of studs down each side of the button stand
    for sx_ in (-1, 1):
        p = surf(TS, sx_ * 0.075, z, 0.026)
        stud(pewter, p, (surf(TS, sx_ * 0.075, z, 1.0) - surf(TS, sx_ * 0.075, z, 0.0)).normalized(), 0.04)
tag(pewter, '@jacket')
tag(joint, '@jacket')
for sx_ in (-1, 1):
    edge = [(sx_ * 0.13, 5.24 - (5.24 - 3.74) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.032) for x, z in edge], [SR] * len(edge), seg=5)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.008)[0] for a in HB] for z in (3.486, 3.58, 3.69)])
tag(hemband, '@jacket')
new_obj("BK_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.02)
for zz in (3.665, 3.51):
    hs = [ring_pt(TS, zz, a, 0.033)[0] for a in HB]
    tube(stitch, hs, [SR] * len(hs), seg=5)
for a in range(-80, 262, 20):
    p, n = ring_pt(TS, 3.58, a, 0.028)
    stud(pewter, p, n, 0.042)


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
    for xs, zs in ((0.15, 5.715), (0.30, 5.78), (0.45, 5.845), (0.60, 5.905), (0.69, 5.99), (0.60, 6.11), (0.72, 6.28), (0.75, 6.36), (0.65, 6.42)):
        p = surf(TS, s * xs, zs, roll_lift(xs, zs) + 0.036)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0) - surf(TS, s * xs, zs, 0.0)).normalized(), 0.036)
    # studded straps: one down the front of each shoulder, one across each shoulder blade
    # shoulder yokes: a broad studded plate of cloth over the front of each shoulder and a broader one across each shoulder blade
    for outline, back, pts in (([(0.90, 6.33), (1.15, 6.36), (1.62, 6.10), (1.66, 5.86), (1.35, 5.74), (1.02, 5.84), (0.90, 6.02)], False,
                                ((1.02, 5.95), (1.20, 5.84), (1.42, 5.83), (1.57, 5.95), (1.05, 6.22), (1.30, 6.20))),
                               ([(0.55, 6.38), (1.05, 6.40), (1.62, 6.10), (1.66, 5.80), (1.30, 5.66), (0.90, 5.80), (0.62, 6.06)], True,
                                ((0.74, 5.98), (0.95, 5.84), (1.20, 5.75), (1.45, 5.78), (1.58, 5.92), (0.80, 6.28), (1.10, 6.27), (1.40, 6.13)))):
        o = [(s * x, z) for x, z in outline]
        panel(straps, TS, o, lambda x, z: 0.012, back=back, cuts=2)
        topstitch(stitch, TS, o, lambda x, z: 0.04, inset=0.026, back=back, step=0.07, radius=SR)
        studs([(s * x, z) for x, z in pts], back)
breast = [(0.47, 5.30), (0.93, 5.30), (0.93, 4.84), (0.88, 4.78), (0.52, 4.78), (0.47, 4.84)]
panel(pockets, TS, breast, flat_lift, cuts=2)
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
exec(compile(open("/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc - mn * 0.0299, mn, mt, 0.34, 'gavel')
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.32, 6.42, 0.03), surf(TS, s * (g(6.15) + 0.02), 6.15, 0.062), surf(TS, s * (g(5.9) + 0.018), 5.9, 0.062),
           surf(TS, s * 0.035, 5.68, 0.066), bail + Vector((s * 0.02, 0, 0))]
    tube(cord, pts, [0.014] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("BK_Shirt", shirt, M_SHIRT, 30)
new_obj("BK_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.018)
new_obj("BK_Stitching", stitch, M_STITCH, 40)
new_obj("BK_BowTie", tie, M_BOW, 50)
new_obj("BK_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.021)
new_obj("BK_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.036)
new_obj("BK_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("BK_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.023)
new_obj("BK_Medallion", medal_p, M_PEWTER, 32)
new_obj("BK_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("BK_Cord", cord, M_STEEL, 40)
new_obj("BK_BowDots", bowdots, M_SHIRT, 40)
new_obj("BK_Zipper", zipteeth, M_STEEL, 35)
new_obj("BK_ZipTape", ziptape, M_LINING, 30, outward=True, thickness=0.006)
new_obj("BK_Plates", plate, M_PLATE, 32)
new_obj("BK_Joints", joint, M_JOINT, 40)
new_obj("BK_Steel", steel, M_STEEL, 40)
new_obj("BK_Buttons", pewter, M_PEWTER, 32)

# The coat and everything sewn to it were laid out at the Head Hunter's size; bring them to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        v.co *= BODY_S
    for m in ob.modifiers:
        if m.type == 'SOLIDIFY' and hg is None:
            m.thickness *= BODY_S
    ob.data.update()

cam = bpy.data.objects.new("BKCam", bpy.data.cameras.new("BKCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("BKSun", bpy.data.lights.new("BKSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("BKFill", bpy.data.lights.new("BKFill", 'AREA'))
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
