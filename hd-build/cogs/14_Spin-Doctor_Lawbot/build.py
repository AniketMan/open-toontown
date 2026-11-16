"""Build the HD SpinDoctor (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (576 px = 6.08 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit B's rest pose at native size (game / 0.851).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/14_Spin-Doctor_Lawbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.06
K = 5.65 / 5.29        # suit B scale for this cog
# The coat is the Downsizer's cut (same body, suit B). It is laid out at his size and brought to this cog's at the end.
BODY_S = 5.65 / 4.5
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


col = get_col("SpinDoctor")
refcol = get_col("SpinDoctor_Reference")
root = bpy.data.objects.new("SpinDoctor", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    import os
    if not os.path.exists(SP + "refplanes/sd_ref_%s.png" % name):
        return
    img = bpy.data.images.load(SP + "refplanes/sd_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 6.4
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
M_SUIT = pmat("SD_Suit", (0.028, 0.032, 0.085), 0.88, var=0.35, grime=0.12, stripe=(0.045, 0.05, 0.12), weave=0.5, bump=0.25,
              bscale=110, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("SD_Lining", (0.012, 0.013, 0.03), 0.8, var=0.3)
M_STITCH = pmat("SD_Piping", (0.22, 0.035, 0.27), 0.85, var=0.2)
M_PLATE = pmat("SD_Plate", (0.36, 0.72, 0.58), 0.42, 0.15, var=0.22, grime=0.45, wear=0.1, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_HAND = pmat("SD_Hand", (0.36, 0.72, 0.58), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1, bscale=45, rvar=0.14, nscale=6.0)
M_JOINT = pmat("SD_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("SD_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("SD_Hair", (0.20, 0.095, 0.055), 0.3, 0.2, var=0.4, wear=0.15, bump=0.2, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_HAT = pmat("SD_Hat", (0.84, 0.83, 0.80), 0.45, var=0.4, wear=0.1, bump=0.3, bscale=200, rvar=0.1, sheen=0.3)
M_BAND = pmat("SD_HatBand", (0.12, 0.04, 0.025), 0.5, var=0.3, weave=0.4, sheen=0.3)
M_EYE = pmat("SD_Eye", (0.90, 0.88, 0.80), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("SD_Iris", (0.02, 0.016, 0.014), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("SD_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("SD_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("SD_Pewter", (0.40, 0.41, 0.46), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("SD_Shirt", (0.82, 0.74, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("SD_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

M_MIRROR = pmat("SD_Mirror", (0.72, 0.72, 0.74), 0.18, 0.95, var=0.15, grime=0.2, rvar=0.08)
M_LID = pmat("SD_Lid", (0.27, 0.58, 0.46), 0.4, 0.1, var=0.25, grime=0.3, bump=0.08, bscale=40, rvar=0.12, coat=0.2)
M_FANG = pmat("SD_Fang", (0.92, 0.90, 0.84), 0.25, var=0.1, grime=0.2, coat=0.5)
M_BOW = pmat("SD_Bow", (0.60, 0.04, 0.03), 0.6, var=0.25, weave=0.5, sheen=0.3, rvar=0.1)
M_BROW = pmat("SD_Dark", (0.05, 0.035, 0.07), 0.4, 0.1, var=0.3)
M_IRISRING = pmat("SD_IrisRing", (0.10, 0.30, 0.20), 0.2, var=0.2, coat=0.6)
M_EMBLEM = pmat("SD_Emblem", (0.06, 0.063, 0.08), 0.35, 0.9, var=0.2, grime=0.3, bump=0.08, bscale=80, rvar=0.15)
plate, joint, steel, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()


def stud(bm, p, n, r=0.024):
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
# A long straight box coat: half-widths from the front and back views, front and back from the side view.
TORSO = [fb(2.42, 0.51, -0.50, 0.35), fb(2.60, 0.52, -0.50, 0.345), fb(3.00, 0.525, -0.50, 0.33),
         fb(3.40, 0.525, -0.50, 0.33), fb(3.80, 0.53, -0.47, 0.34), fb(4.05, 0.54, -0.43, 0.36),
         fb(4.25, 0.59, -0.36, 0.37), fb(4.38, 0.63, -0.31, 0.37), fb(4.46, 0.58, -0.27, 0.355),
         fb(4.51, 0.47, -0.24, 0.33), fb(4.55, 0.36, -0.21, 0.30), fb(4.58, 0.27, -0.19, 0.27)]
TS = TORSO
BREAK = 3.98


def front_gap(z):
    return 0.003 if z <= BREAK else 0.003 + 0.20 * min(1.0, (z - BREAK) / (4.52 - BREAK)) ** 1.1


SHIRT_IN = {3.80: 0.07, 4.05: 0.07, 4.25: 0.06, 4.38: 0.05, 4.46: 0.05, 4.51: 0.05}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
SS += [fb(4.55, 0.27, -0.185, 0.25), fb(4.585, 0.20, -0.15, 0.20)]
bm = bmesh.new()
loft(bm, SS + [fb(4.59, 0.1, -0.08, 0.1)], seg=28)
new_obj("SD_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(8, 20, 8))
for v in bm.verts:
    if v.co.z > 4.565 and v.co.y < 0:
        v.co.z -= 0.04 * min(1.0, -v.co.y / 0.2)
new_obj("SD_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.035)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(2.418, 0, hem_cy, hem_rx - 0.008, hem_ry - 0.008), (2.44, 0, -0.06, 0.42, 0.33)], seg=28, caps=(False, False))
new_obj("SD_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(4.55, 0.27, -0.20, 0.285), fb(4.625, 0.275, -0.21, 0.31), fb(4.615, 0.35, -0.26, 0.36), fb(4.50, 0.50, -0.31, 0.385)]
arc_band(bm, COLLAR, -28, 208, 22, zfun=lambda si, sn: (0.02 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("SD_Collar", bm, M_SUIT, outward=False, thickness=0.024)
COLLAR_EDGE = []
for i in range(23):
    t = math.radians(-28 + 236 * i / 22)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 4.532)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt3_1 / scale_jnt9_1 carry the upper
# arms, jnt3_2 / jnt9_2 the forearms, scale_jnt1_1 / scale_jnt2_1 the thighs, jnt1_2 / jnt2_2 the shins,
# to_legL/R the feet and to_MAIN the pelvis.
RIG = json.load(open(SP + "sd_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.06 / K
AZ = JR["Lh_wrist"].z                    # the arm lies along x at this height (4.96)
WX = JR["Lh_wrist"].x                    # wrist joint (3.22); shoulder joint x 0.89, elbow about x 1.97
AY = JR["Lh_wrist"].y
# The shoulder end is a dome centred on the shoulder joint, so the arm can hang or swing without poking up.
SLEEVE = [(0.66, 0.15, AZ, 0.07, 0.05), (0.70, 0.15, AZ - 0.01, 0.16, 0.11), (0.76, 0.15, AZ - 0.02, 0.23, 0.15),
          (0.83, 0.15, AZ - 0.035, 0.265, 0.17), (0.89, 0.15, AZ - 0.04, 0.275, 0.175), (1.20, 0.16, AZ - 0.03, 0.275, 0.19),
          (1.60, 0.17, AZ - 0.015, 0.265, 0.20), (1.97, 0.17, AZ, 0.255, 0.205), (2.50, 0.15, AZ, 0.245, 0.205),
          (2.98, 0.14, AZ, 0.24, 0.205), (2.96, 0.14, AZ, 0.185, 0.165)]
BAND = [(2.56, 0.15, AZ, 0.262, 0.222), (2.995, 0.14, AZ, 0.257, 0.222)]      # turned-up cuff band
sleeves, plate_r, joint_r, pewter_r, stitch_r = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
cuffw = bmesh.new()
for s in (-1, 1):
    xloft(sleeves, SLEEVE, seg=22, sx=s)
    xloft(sleeves, BAND, seg=22, sx=s)
    xloft(cuffw, [(2.97, 0.14, AZ, 0.205, 0.185), (3.14, 0.14, AZ, 0.20, 0.18), (3.14, 0.14, AZ, 0.14, 0.13)], seg=20, sx=s, caps=(False, False))
    for k in range(8):                                           # studs round the band
        a_ = 2 * math.pi * (k + 0.5) / 8
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(a_), math.sin(a_)))
        stud(pewter_r, Vector((s * 2.78, cy + (ry + 0.003) * n.y, cz + (rz + 0.003) * n.z)), n, 0.026)
    for x in (2.585, 2.975):                                     # stitching round the band
        _, cy, cz, ry, rz = BAND[0] if x < 2.8 else BAND[1]
        ring = [Vector((s * x, cy + (ry + 0.003) * math.cos(math.radians(a)), cz + (rz + 0.003) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(stitch_r, ring, [0.011] * len(ring), seg=5)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
tag(cuffw, '@sleeve')
new_obj("SD_ShirtCuffs", cuffw, M_SHIRT, 40, rest=True)
new_obj("SD_Sleeves", sleeves, M_SUIT, 60, rest=True)

# ---- forearm cuff, wrist bearing and hand, flat in the rest pose: fingers straight out along x, index at the front
KN_X = JR["Lh_1"].x                                              # knuckle joints (0.44 from the wrist)
J2_X = JR["Lh_2"].x                                              # second finger joints (0.26 further)
FINGERS = (("index", JR["Lh_index1"].y - 0.02), ("rest", 0.105), ("rest", 0.23), ("rest", 0.355))
PLATE_Y = 0.165
for s in (-1, 1):
    S = 'L' if s > 0 else 'R'
    T = Matrix.Identity(4) if s > 0 else Matrix.Translation(JR["Rh_wrist"] - MIRROR @ JR["Lh_wrist"]) @ MIRROR
    R3 = T.to_3x3()
    names = dict(wrist=S + 'h_wrist', index=(S + 'h_index1', S + 'h_index2'), rest=(S + 'h_1', S + 'h_2'),
                 thumb=(S + 'h_thumb1', S + 'h_thumb2'))
    ax = R3 @ Vector((1, 0, 0))
    c0 = T @ Vector((WX - 0.45, AY, AZ))                         # metal cuff starts well inside the sleeve
    lathe(plate_r, c0, ax, [(0.0, 0.15), (0.015, 0.168), (0.33, 0.176), (0.345, 0.19), (0.372, 0.19), (0.38, 0.146)], seg=20)
    lathe(joint_r, c0, ax, [(0.372, 0.13), (0.386, 0.148), (0.402, 0.127), (0.42, 0.148), (0.436, 0.127), (0.45, 0.143)], seg=16)
    for n in (Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((0, 1, 0))):     # round boss on the cuff: outer, front and back faces
        n = R3 @ n
        puck(plate_r, c0 + ax * 0.265 + n * 0.176, n, 0.042, 0.014, seg=12)
        puck(joint_r, c0 + ax * 0.265 + n * 0.180, n, 0.028, 0.014, seg=10)
        puck(plate_r, c0 + ax * 0.265 + n * 0.184, n, 0.014, 0.012, seg=8)
    # back-of-hand plate (on top in the rest pose), palm pad below it, dark core between; rivet row at the wrist end
    rbox(plate_r, T @ Matrix.Translation((WX + 0.215, PLATE_Y, AZ + 0.026)), (0.41, 0.50, 0.15), 0.05, 3)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.225, PLATE_Y, AZ - 0.066)), (0.34, 0.42, 0.075), 0.022, 1)
    rbox(joint_r, T @ Matrix.Translation((WX + 0.22, PLATE_Y, AZ - 0.015)), (0.36, 0.45, 0.09), 0.0)
    for k in range(6):
        puck(plate_r, T @ Vector((WX + 0.06, PLATE_Y - 0.19 + 0.076 * k, AZ + 0.101)), R3 @ Vector((0, 0, 1)), 0.01, 0.01, seg=6)
    tag(plate_r, names['wrist'])                                 # cuff, bearing and hand plates move as one piece with the wrist
    tag(joint_r, names['wrist'])
    # fingers: first bone from the knuckle joint to the second joint, then a two-plate tip curling down, rigid with it
    for kind, fy in FINGERS:
        j1, j2 = names[kind]
        k0 = Vector((KN_X, fy, AZ + 0.01))
        k1 = Vector((J2_X, fy, AZ + 0.016))
        k2 = k1 + Vector((math.cos(math.radians(-14)), 0, math.sin(math.radians(-14)))) * 0.15
        k3 = k2 + Vector((math.cos(math.radians(-34)), 0, math.sin(math.radians(-34)))) * 0.13
        seg_box(plate_r, T, k0, k1, (0, 0, 1), 0.115, 0.112, 0.026, 2, gap=0.005)
        lathe(joint_r, T @ (k0 + Vector((0, -0.05, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.046), (0.10, 0.046)], seg=10)
        tag(plate_r, j1)
        tag(joint_r, j1)
        seg_box(plate_r, T, k1, k2, (0, 0, 1), 0.115, 0.112, 0.026, 2, gap=0.005)
        seg_box(plate_r, T, k2, k3, (0, 0, 1), 0.115, 0.112, 0.036, 2, gap=0.005)
        for q in (k1, k2):
            lathe(joint_r, T @ (q + Vector((0, -0.05, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.046), (0.10, 0.046)], seg=10)
        tag(plate_r, j2)
        tag(joint_r, j2)
    # thumb: pivot disc on the thumb joint at the front edge of the hand, first bone to the second thumb joint, then the tip
    t1, t2 = JR["Lh_thumb1"].copy(), JR["Lh_thumb2"].copy()
    td = (t2 - t1).normalized()
    t2e = t2 + td * 0.06
    t3 = t2e + (td + Vector((0.5, 0, -0.25))).normalized() * 0.14
    lathe(joint_r, T @ (t1 + Vector((0, 0, -0.055))), R3 @ Vector((0, 0, 1)), [(0.0, 0.075), (0.11, 0.075)], seg=14)
    tag(joint_r, names['wrist'])
    seg_box(plate_r, T, t1, t2e, (0, 0, 1), 0.105, 0.105, 0.026, 2, gap=0.003)
    lathe(plate_r, T @ (t1 + Vector((0, 0, 0.052))), R3 @ Vector((0, 0, 1)), [(0.0, 0.064), (0.015, 0.064), (0.026, 0.04)], seg=14)
    tag(plate_r, names['thumb'][0])
    seg_box(plate_r, T, t2e, t3, (0, 0, 1), 0.105, 0.105, 0.036, 2, gap=0.005)
    lathe(joint_r, T @ (t2e + Vector((0, 0, -0.046))), R3 @ Vector((0, 0, 1)), [(0, 0.042), (0.092, 0.042)], seg=10)
    tag(plate_r, names['thumb'][1])
    tag(joint_r, names['thumb'][1])
new_obj("SD_HandPlates", plate_r, M_HAND, 32, rest=True)
new_obj("SD_HandJoints", joint_r, M_JOINT, 40, rest=True)
new_obj("SD_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("SD_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- trousers: one sealed garment. The seat is a closed bowl on the pelvis (to_MAIN, z 3.45) running up inside
# the jacket (hem at z 2.84 here); each leg comes straight down round hip (z 3.16) -> knee (1.67) -> ankle (0.14).
seat = bmesh.new()
loft(seat, [(2.50, 0, -0.05, 0.05, 0.05), (2.54, 0, -0.05, 0.22, 0.20), (2.62, 0, -0.05, 0.34, 0.30), (2.75, 0, -0.05, 0.42, 0.36),
            (2.95, 0, -0.06, 0.47, 0.40), (3.20, 0, -0.07, 0.52, 0.43), (3.50, 0, -0.07, 0.54, 0.44), (3.75, 0, -0.06, 0.48, 0.40),
            (3.90, 0, -0.05, 0.35, 0.30)], seg=24, centres=(270, 90))
new_obj("SD_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
LEG = [(0.21, 0.212, 0.0, 0.20, 0.345), (0.50, 0.21, -0.02, 0.196, 0.325), (1.00, 0.208, -0.04, 0.192, 0.305),
       (1.67, 0.208, -0.05, 0.192, 0.30), (2.40, 0.21, -0.05, 0.196, 0.31), (3.00, 0.215, -0.05, 0.20, 0.33)]
for s in (-1, 1):
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("SD_Trousers", bm, M_SUIT, 60, rest=True)
# studded band round each trouser hem, piped along its top
hemb, studs_r, pipe_r = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    z0, cx, cy, rx, ry = LEG[0]
    z1 = 0.50
    loft(hemb, [(z0 - 0.005, cx, cy, rx + 0.012, ry + 0.012), (z1, cx, cy, rx + 0.012, ry + 0.012)], seg=20, sx=s, caps=(False, False), centres=(270, 90))
    for k in range(8):
        a_ = 2 * math.pi * (k + 0.5) / 8
        nrm = Vector((s * math.cos(a_) / rx, math.sin(a_) / ry, 0)).normalized()
        stud(studs_r, Vector((s * (cx + (rx + 0.016) * math.cos(a_)), cy + (ry + 0.016) * math.sin(a_), (z0 + z1) / 2)), nrm, 0.026)
    for zz in (z0 + 0.012, z1 - 0.012):
        ring = [Vector((s * (cx + (rx + 0.016) * math.cos(math.radians(a_))), cy + (ry + 0.016) * math.sin(math.radians(a_)), zz)) for a_ in range(0, 361, 18)]
        tube(pipe_r, ring, [0.011] * len(ring), seg=5)
    for _b in (hemb, studs_r, pipe_r):
        tag(_b, '@legL' if s > 0 else '@legR')
new_obj("SD_TrouserBands", hemb, M_SUIT, 60, rest=True)
new_obj("SD_LimbStuds", studs_r, M_PEWTER, 32, rest=True)
new_obj("SD_TrouserPiping", pipe_r, M_STITCH, 40, rest=True)

# ---- shoes: cap-toe, welted, separate heel, pointing straight ahead. Footprint follows the original's: heel on
# the ankle bone (x 0.25), 0.36 behind the ankle joint; toe 0.77 ahead of it; widening only toward the ball.
upper, sole = bmesh.new(), bmesh.new()
SHOE = [(0.40, 0.25, 0.08, 0.16), (0.36, 0.25, 0.13, 0.21), (0.22, 0.25, 0.17, 0.25), (0.0, 0.26, 0.20, 0.26),
        (-0.22, 0.28, 0.225, 0.24), (-0.42, 0.295, 0.235, 0.20), (-0.56, 0.295, 0.22, 0.16), (-0.65, 0.295, 0.18, 0.12),
        (-0.70, 0.295, 0.12, 0.075), (-0.72, 0.295, 0.05, 0.04)]          # (y, centre x, half-width, height above the welt)
WELT, OUTSOLE = 0.085, 0.052
NS = 12


def welt_extra(y):
    return 0.02 if y > 0.08 else 0.032


PLAN = [(y, cx, w) for y, cx, w, h in SHOE]
for s in (-1, 1):
    shoe_piece(upper, s, SHOE)                                                           # vamp and quarters
    cap_y = -0.48
    shoe_piece(upper, s, [(cap_y, *shoe_at(cap_y))] + [st for st in SHOE if st[0] < cap_y], grow=0.011)     # toe cap
    ctr_y = 0.14
    shoe_piece(upper, s, [st for st in SHOE if st[0] > ctr_y] + [(ctr_y, *shoe_at(ctr_y))], grow=0.009)     # heel counter
    for y in (-0.22, -0.10):                                                             # lace facing seams
        cx, w, h = shoe_at(y)
        tube(sole, [Vector((s * (cx + shoe_sec(w + 0.002, h + 0.002, k)[0]), y, shoe_sec(w + 0.002, h + 0.002, k)[1]))
                    for k in range(2, NS - 1)], [0.0045] * (NS - 3), seg=4)
    slab(sole, s, [(0.42, 0.25, 0.05)] + PLAN + [(-0.735, 0.295, 0.025)], OUTSOLE, WELT)  # welt ledge
    fore = [(-0.07, *shoe_at(-0.07)[:2])] + [p for p in PLAN if p[0] < -0.07] + [(-0.73, 0.295, 0.025)]
    slab(sole, s, fore, 0.009, OUTSOLE, 0.022)                                           # forefoot outsole
    heel = [(0.415, 0.25, 0.05)] + [p for p in PLAN if p[0] > 0.08] + [(0.08, *shoe_at(0.08)[:2])]
    slab(sole, s, heel, 0.009, OUTSOLE, 0.015)                                           # heel block
    for y in (-0.62, -0.53, -0.44, -0.35, -0.26, -0.17):                                 # tread bars
        cx, w, h = shoe_at(y)
        rbox(sole, Matrix.Translation((s * cx, y, 0.006)), (2 * w - 0.05, 0.05, 0.012), 0.0)
new_obj("SD_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("SD_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.06

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

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.009

loft(shirt, [fb(4.50, 0.235, -0.19, 0.265), fb(4.62, 0.21, -0.165, 0.235), fb(4.62, 0.195, -0.15, 0.22), fb(4.515, 0.20, -0.155, 0.225)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.025, s * 0.22, 4.54), (s * 0.065, s * 0.245, 4.47), (s * 0.12, s * 0.18, 4.37)], 0.014, nx=4)
# bow tie: a knot and two wings on the shirt under the chin; shirt studs below it
bowdots, zipteeth, ziptape = bmesh.new(), bmesh.new(), bmesh.new()
bow_c = surf(SS, 0.0, 4.43, 0.05)
bmesh.ops.create_uvsphere(tie, u_segments=14, v_segments=8, radius=1.0, matrix=Matrix.Translation(bow_c) @ Matrix.Diagonal((0.036, 0.036, 0.046, 1.0)))
BOW = [(0.015, 0.016, 0.018), (0.05, 0.022, 0.036), (0.10, 0.027, 0.058), (0.155, 0.027, 0.07), (0.182, 0.02, 0.066), (0.19, 0.008, 0.05)]
for sdx in (-1, 1):                                             # each wing: pinched at the knot, flaring to a blunt end
    xloft(tie, [(x_, bow_c.y + 0.006, bow_c.z, ry_, rz_) for x_, ry_, rz_ in BOW], seg=16, sx=sdx)
    for ddx, ddz in ((0.065, 0.012), (0.105, -0.026), (0.112, 0.03), (0.152, 0.002), (0.158, -0.04), (0.16, 0.042)):   # pale dots, as on the original
        puck(bowdots, bow_c + Vector((sdx * ddx, 0.006 - 0.0265, ddz)), (0, -1, 0), 0.0085, 0.004, seg=8)
# zipper down the shirt front, from under the bow to where the coat closes: two tapes, interlocking teeth, a slider and pull
ZT, ZB = 4.345, 3.93


def zframe(dx, z, lift):
    n_ = (surf(SS, dx, z, 1.0) - surf(SS, dx, z, 0.0)).normalized()
    up_ = (surf(SS, dx, z + 0.01) - surf(SS, dx, z - 0.01)).normalized()
    m_ = Matrix((up_.cross(n_).normalized(), up_, n_)).transposed().to_4x4()
    m_.translation = surf(SS, dx, z, lift)
    return m_


for sdx in (-1, 1):
    patch(ziptape, SS, [(sdx * 0.004, sdx * 0.042, ZB + (ZT - ZB) * i / 10) for i in range(11)], 0.003, nx=2)
nz = int((ZT - ZB) / 0.019)
for i in range(nz):
    sdx = 1 if i % 2 else -1
    rbox(zipteeth, zframe(sdx * 0.008, ZB + (ZT - ZB) * (i + 0.5) / nz, 0.008), (0.02, 0.012, 0.012), 0.003, 1)
rbox(zipteeth, zframe(0.0, ZT - 0.012, 0.012), (0.036, 0.044, 0.016), 0.006, 2)                    # slider
rbox(zipteeth, zframe(0.0, ZT - 0.062, 0.02), (0.02, 0.06, 0.006), 0.003, 1)                      # pull tab
lathe(zipteeth, zframe(0.0, ZT - 0.03, 0.016).translation - Vector((0.012, 0, 0)), (1, 0, 0), [(0.0, 0.005), (0.024, 0.005)], seg=8)


panel(placket, TS, [(-0.095, 2.428), (0.095, 2.428), (0.095, 3.80), (0.03, 3.955), (-0.03, 3.955), (-0.095, 3.80)], lambda x, z: 0.004, cuts=2)
for z in (3.56, 3.38, 3.20, 3.02, 2.84, 2.66):          # a column of studs down each side of the button stand
    for sx_ in (-1, 1):
        p = surf(TS, sx_ * 0.05, z, 0.017)
        stud(pewter, p, (surf(TS, sx_ * 0.05, z, 1.0) - surf(TS, sx_ * 0.05, z, 0.0)).normalized(), 0.026)
tag(pewter, '@jacket')
tag(joint, '@jacket')
for sx_ in (-1, 1):
    edge = [(sx_ * 0.088, 3.76 - (3.76 - 2.60) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.021) for x, z in edge], [SR] * len(edge), seg=5)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.005)[0] for a in HB] for z in (2.424, 2.50, 2.585)])
tag(hemband, '@jacket')
new_obj("SD_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.013)
for zz in (2.565, 2.44):
    hs = [ring_pt(TS, zz, a, 0.021)[0] for a in HB]
    tube(stitch, hs, [SR] * len(hs), seg=5)
for a in range(-80, 262, 20):
    p, n = ring_pt(TS, 2.50, a, 0.018)
    stud(pewter, p, n, 0.027)


def roll_lift(x, z):
    return 0.009 + 0.026 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.12)


def flat_lift(x, z):
    return 0.006


g = front_gap
for s in (-1, 1):
    lapel = [(0.004, 3.975), (0.40, 4.125), (0.43, 4.19), (0.33, 4.285), (g(4.30), 4.30), (g(4.20), 4.20), (g(4.08), 4.08)]
    collar_front = [(g(4.30), 4.30), (0.33, 4.285), (0.45, 4.30), (0.455, 4.36), (0.38, 4.49), (g(4.49), 4.49)]
    flap = [(0.27, 3.0), (0.455, 3.0), (0.455, 2.845), (0.44, 2.825), (0.285, 2.825), (0.27, 2.845)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.027, inset=0.02, step=0.05, radius=SR)
    for xs, zs in ((0.09, 4.05), (0.19, 4.09), (0.29, 4.13), (0.375, 4.175), (0.34, 4.235), (0.40, 4.335), (0.41, 4.40), (0.375, 4.455)):
        p = surf(TS, s * xs, zs, roll_lift(xs, zs) + 0.024)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0) - surf(TS, s * xs, zs, 0.0)).normalized(), 0.023)
breast = [(0.235, 3.76), (0.455, 3.76), (0.455, 3.44), (0.42, 3.40), (0.27, 3.40), (0.235, 3.44)]
panel(pockets, TS, breast, flat_lift, cuts=2)
panel(pockets, TS, [(0.235, 3.76), (0.455, 3.76), (0.455, 3.71), (0.235, 3.71)], lambda x, z: 0.014, cuts=1)
pocket_sq = [surf(TS, x, z, 0.026) for x, z in ((0.255, 3.755), (0.435, 3.755), (0.43, 3.82), (0.405, 3.80), (0.385, 3.875),
                                               (0.355, 3.81), (0.33, 3.885), (0.305, 3.81), (0.27, 3.84))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')

# Back: a pointed yoke patch on each shoulder blade, stitched round its edge
for s in (-1, 1):
    o = [(s * x, z) for x, z in ((0.31, 4.46), (0.55, 4.46), (0.505, 4.03), (0.29, 4.26))]
    panel(straps, TS, o, lambda x, z: 0.007, back=True, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.023, inset=0.016, back=True, step=0.05, radius=SR)
for s in (-1, 1):                                              # studs on the back yokes
    for xs, zs in ((0.355, 4.405), (0.44, 4.405), (0.515, 4.38), (0.505, 4.26), (0.485, 4.13), (0.40, 4.19), (0.335, 4.29)):
        p = surf(TS, s * xs, zs, 0.022, True)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0, True) - surf(TS, s * xs, zs, 0.0, True)).normalized(), 0.023)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 3.80
slope = (surf(TS, 0, MZ + 0.1).y - surf(TS, 0, MZ - 0.1).y) / 0.2
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.014
medal_p, medal_j = bmesh.new(), bmesh.new()
exec(compile(open(SP + "../medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc, mn, mt, 0.165, 'gavel')
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.20, 4.50, 0.02), surf(TS, s * (g(4.35) + 0.015), 4.35, 0.042), surf(TS, s * (g(4.20) + 0.012), 4.20, 0.042),
           surf(TS, s * 0.025, 4.04, 0.044), bail + Vector((s * 0.014, 0, 0))]
    tube(cord, pts, [0.01] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("SD_Shirt", shirt, M_SHIRT, 30)
new_obj("SD_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.012)
new_obj("SD_Stitching", stitch, M_STITCH, 40)
new_obj("SD_BowTie", tie, M_BOW, 50)
new_obj("SD_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.014)
new_obj("SD_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.024)
new_obj("SD_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("SD_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("SD_Medallion", medal_p, M_PEWTER, 32)
new_obj("SD_MedallionEmblem", medal_j, M_EMBLEM, 40)
new_obj("SD_Cord", cord, M_STEEL, 40)
new_obj("SD_BowDots", bowdots, M_SHIRT, 40)
new_obj("SD_Zipper", zipteeth, M_STEEL, 35)
new_obj("SD_ZipTape", ziptape, M_LINING, 30, outward=True, thickness=0.004)
new_obj("SD_Plates", plate, M_PLATE, 32)
new_obj("SD_Joints", joint, M_JOINT, 40)
new_obj("SD_Steel", steel, M_STEEL, 40)
new_obj("SD_Buttons", pewter, M_PEWTER, 32)

# The coat and everything sewn to it were laid out at the Downsizer's size; bring them to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        v.co *= BODY_S
    ob.data.update()

cam = bpy.data.objects.new("SDCam", bpy.data.cameras.new("SDCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("SDSun", bpy.data.lights.new("SDSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("SDFill", bpy.data.lights.new("SDFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 150
fill.data.size = 7
fill.location = (-7, -8, 4.5)
fill.rotation_euler = (Vector((0, 0, 2.8)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
