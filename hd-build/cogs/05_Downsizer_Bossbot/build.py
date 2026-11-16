"""Build the HD Downsizer (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (576 px = 6.08 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit B's rest pose at native size (game / 0.851).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/05_Downsizer_Bossbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.06
K = 4.5 / 5.29          # suit B scale for this cog
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


col = get_col("Downsizer")
refcol = get_col("Downsizer_Reference")
root = bpy.data.objects.new("Downsizer", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "refplanes/ds_ref_%s.png" % name, check_existing=True)
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
M_SUIT = pmat("DS_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18), weave=0.5, bump=0.25,
              bscale=110, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("DS_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("DS_Stitch", (0.66, 0.50, 0.42), 0.85, var=0.2)
M_PLATE = pmat("DS_Plate", (0.33, 0.50, 0.44), 0.42, 0.15, var=0.22, grime=0.45, wear=0.1, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_HAND = pmat("DS_Hand", (0.76, 0.60, 0.50), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1, bscale=45, rvar=0.14, nscale=6.0)
M_JOINT = pmat("DS_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("DS_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("DS_Hair", (0.012, 0.011, 0.011), 0.3, 0.2, var=0.4, wear=0.15, bump=0.2, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_HAT = pmat("DS_Hat", (0.014, 0.012, 0.011), 0.7, var=0.4, wear=0.1, bump=0.3, bscale=200, rvar=0.1, sheen=0.3)
M_BAND = pmat("DS_HatBand", (0.12, 0.04, 0.025), 0.5, var=0.3, weave=0.4, sheen=0.3)
M_EYE = pmat("DS_Eye", (0.80, 0.72, 0.58), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("DS_Iris", (0.02, 0.016, 0.014), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("DS_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("DS_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("DS_Pewter", (0.60, 0.48, 0.40), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("DS_Shirt", (0.82, 0.74, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("DS_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

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
# A long straight box coat: half-widths from the front and back views, front and back from the side view.
TORSO = [fb(2.42, 0.51, -0.50, 0.35), fb(2.60, 0.52, -0.50, 0.345), fb(3.00, 0.525, -0.50, 0.33),
         fb(3.40, 0.525, -0.50, 0.33), fb(3.80, 0.53, -0.47, 0.34), fb(4.05, 0.54, -0.43, 0.36),
         fb(4.25, 0.59, -0.36, 0.37), fb(4.38, 0.63, -0.31, 0.37), fb(4.46, 0.58, -0.27, 0.355),
         fb(4.51, 0.47, -0.24, 0.33), fb(4.55, 0.36, -0.21, 0.30), fb(4.58, 0.27, -0.19, 0.27)]
TS = TORSO
BREAK = 3.98


def front_gap(z):
    return 0.003 if z <= BREAK else 0.003 + 0.20 * min(1.0, (z - BREAK) / (4.52 - BREAK)) ** 1.1


SHIRT_IN = {4.05: 0.07, 4.25: 0.06, 4.38: 0.05, 4.46: 0.05, 4.51: 0.05}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
SS += [fb(4.55, 0.27, -0.185, 0.25), fb(4.585, 0.20, -0.15, 0.20)]
bm = bmesh.new()
loft(bm, SS + [fb(4.59, 0.1, -0.08, 0.1)], seg=28)
new_obj("DS_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(8, 20, 8))
for v in bm.verts:
    if v.co.z > 4.565 and v.co.y < 0:
        v.co.z -= 0.04 * min(1.0, -v.co.y / 0.2)
new_obj("DS_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.035)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(2.418, 0, hem_cy, hem_rx - 0.008, hem_ry - 0.008), (2.44, 0, -0.06, 0.42, 0.33)], seg=28, caps=(False, False))
new_obj("DS_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(4.55, 0.27, -0.20, 0.285), fb(4.625, 0.275, -0.21, 0.31), fb(4.615, 0.35, -0.26, 0.36), fb(4.50, 0.50, -0.31, 0.385)]
arc_band(bm, COLLAR, -28, 208, 22, zfun=lambda si, sn: (0.02 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("DS_Collar", bm, M_SUIT, outward=False, thickness=0.024)
COLLAR_EDGE = []
for i in range(23):
    t = math.radians(-28 + 236 * i / 22)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 4.532)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt3_1 / scale_jnt9_1 carry the upper
# arms, jnt3_2 / jnt9_2 the forearms, scale_jnt1_1 / scale_jnt2_1 the thighs, jnt1_2 / jnt2_2 the shins,
# to_legL/R the feet and to_MAIN the pelvis.
RIG = json.load(open(SP + "ds_rig.json"))
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
for s in (-1, 1):
    xloft(sleeves, SLEEVE, seg=22, sx=s)
    xloft(sleeves, BAND, seg=22, sx=s)
    for x in (2.72, 2.86):                                       # two buttons on the back-outer side of the band
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(math.radians(50)), math.sin(math.radians(50))))
        puck(pewter_r, (s * x, cy + (ry + 0.003) * n.y, cz + (rz + 0.003) * n.z), n, 0.026, 0.02)
    for x in (2.585, 2.975):                                     # stitching round the band
        _, cy, cz, ry, rz = BAND[0] if x < 2.8 else BAND[1]
        ring = [Vector((s * x, cy + (ry + 0.003) * math.cos(math.radians(a)), cz + (rz + 0.003) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(stitch_r, ring, [0.0065] * len(ring), seg=4)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("DS_Sleeves", sleeves, M_SUIT, 60, rest=True)

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
new_obj("DS_HandPlates", plate_r, M_HAND, 32, rest=True)
new_obj("DS_HandJoints", joint_r, M_JOINT, 40, rest=True)
new_obj("DS_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("DS_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- trousers: one sealed garment. The seat is a closed bowl on the pelvis (to_MAIN, z 3.45) running up inside
# the jacket (hem at z 2.84 here); each leg comes straight down round hip (z 3.16) -> knee (1.67) -> ankle (0.14).
seat = bmesh.new()
loft(seat, [(2.50, 0, -0.05, 0.05, 0.05), (2.54, 0, -0.05, 0.22, 0.20), (2.62, 0, -0.05, 0.34, 0.30), (2.75, 0, -0.05, 0.42, 0.36),
            (2.95, 0, -0.06, 0.47, 0.40), (3.20, 0, -0.07, 0.52, 0.43), (3.50, 0, -0.07, 0.54, 0.44), (3.75, 0, -0.06, 0.48, 0.40),
            (3.90, 0, -0.05, 0.35, 0.30)], seg=24, centres=(270, 90))
new_obj("DS_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
LEG = [(0.21, 0.212, 0.0, 0.20, 0.345), (0.50, 0.21, -0.02, 0.196, 0.325), (1.00, 0.208, -0.04, 0.192, 0.305),
       (1.67, 0.208, -0.05, 0.192, 0.30), (2.40, 0.21, -0.05, 0.196, 0.31), (3.00, 0.215, -0.05, 0.20, 0.33)]
for s in (-1, 1):
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("DS_Trousers", bm, M_SUIT, 60, rest=True)

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
new_obj("DS_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("DS_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.06

# ---------------------------------------------------------------- head: a tall tapering shell
# HEAD is the outer surface (front view half-widths, side view front and back). Pieces: the face shell in two
# halves meeting on a hairline down the centre and the back; the mouth cassette, a domed plate whose arched top edge
# is the frown; a slit under the nose that turns up at each end; eye slots with the ball behind; the hair shell on
# the back; ears; and the hat. All of it over a closed inner shell.
HEAD = [fb(4.56, 0.262, -0.265, 0.19), fb(4.60, 0.257, -0.26, 0.188), fb(4.80, 0.235, -0.248, 0.18),
        fb(5.00, 0.208, -0.228, 0.17), fb(5.20, 0.168, -0.208, 0.158), fb(5.35, 0.147, -0.185, 0.15),
        fb(5.50, 0.13, -0.15, 0.14), fb(5.65, 0.112, -0.11, 0.13), fb(5.80, 0.10, -0.065, 0.12),
        fb(5.87, 0.095, -0.05, 0.115)]
GAP = 0.0012
CORE_IN = 0.008
BASE_Z, TOP_Z = 4.56, 5.87
ARCH_TOP, ARCH_END_Z, ARCH_END_X = 5.225, 4.86, 0.20


def hp(th, z, eps=0.0):          # point on the head, th degrees round from centre front (+ = his left)
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def rxz(z):
    return interp(HEAD, z)[3]


def hx(th, z):                   # how far out from the centre line that point is
    return rxz(z) * math.sin(math.radians(min(abs(th), 90.0)))


def agap(z, d=GAP):
    return math.degrees(d / rxz(z))


def arch_z(x):                   # the frown: top edge of the mouth cassette
    return ARCH_TOP - (ARCH_TOP - ARCH_END_Z) * min(1.0, x / ARCH_END_X) ** 1.5


THC = math.degrees(math.asin(ARCH_END_X / rxz(ARCH_END_Z)))      # the cassette's sides run straight down from the ends of the frown


def arch_col(th):                # height at which a column crosses the frown
    lo, hi = ARCH_END_Z, ARCH_TOP
    for _ in range(40):
        mid = (lo + hi) / 2
        if mid < arch_z(hx(th, mid)):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def arch_gap(x):                 # the frown is cut wider than a panel line, closing to a hairline at its ends
    return GAP + 0.0048 * max(0.0, 1 - (x / ARCH_END_X) ** 2)


SLIT_X = 0.135


def slit_col(th):                # the line under the nose, turning up at each end; (height, half-gap)
    z = 5.36
    for _ in range(4):
        x = hx(th, z)
        z = 5.345 + 0.055 * min(1.0, x / SLIT_X) ** 3
    return z, (0.0042 * min(1.0, (SLIT_X - x) / 0.03) if x < SLIT_X and abs(th) < 89 else 0.0)


EYE_X, EYE_Z, EYE_A, EYE_B = 0.075, 5.525, 0.036, 0.024


def eye_col(th):                 # eye slot: (height below centre, height above centre); the lid covers the top of the ball
    t = (hx(th, EYE_Z) - EYE_X) / EYE_A
    if abs(t) >= 1 or abs(th) > 89:
        return 0.0, 0.0
    return EYE_B * math.sqrt(1 - t * t), 0.3 * EYE_B * math.sqrt(1 - t * t)


A_F, B_F, C_F = (0.0, 0.33, 0.66, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.2, 0.45, 0.75, 1.0)


def face_zs(th):
    bot = ARCH_END_Z if th >= THC - 1e-6 else arch_col(th) + arch_gap(hx(th, arch_col(th)))
    zs, gs = slit_col(th)
    el, eh = eye_col(th)
    return ([bot + (zs - gs - bot) * f for f in A_F] + [zs + gs + (EYE_Z - el - zs - gs) * f for f in B_F] +
            [EYE_Z + eh + (TOP_Z - EYE_Z - eh) * f for f in C_F])


IN_TH = [3.0 * i for i in range(int(THC // 3) + 1)] + [THC]
OUT_TH = [THC] + [a for a in (66, 72, 78, 84, 90, 100, 110, 120, 130, 140, 150, 160, 170) if a > THC + 1] + [180]
plates = bmesh.new()
for s in (1, -1):
    t = bmesh.new()
    cols = []
    for th in IN_TH:
        cols.append([t.verts.new(hp(s * max(th, agap(z)), z)) for z in face_zs(th)])
    for a, b in zip(cols, cols[1:]):
        for k in range(12):
            if k not in (3, 7):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    cols = []
    for th in OUT_TH:
        zs = [BASE_Z + (ARCH_END_Z - BASE_Z) * f for f in (0.0, 0.35, 0.7)] + face_zs(th)
        col_ = []
        for z in zs:
            a = th
            if th == THC and z < ARCH_END_Z:
                a = THC + agap(z)
            if th == 180:
                a = 180 - agap(z)
            col_.append(t.verts.new(hp(s * a, z)))
        cols.append(col_)
    for a, b in zip(cols, cols[1:]):
        for k in range(15):
            if k not in (6, 10):
                t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0004)
tag(plates, 'joint_head')
new_obj("DS_HeadPlates", plates, M_PLATE, 50, outward=True, thickness=-0.016)

# mouth cassette: one domed plate, a little proud of the shell, filling the arch
CAS_LIFT = 0.005
cas = bmesh.new()
CT = [-(THC - 0.3) + 2 * (THC - 0.3) * i / 40 for i in range(41)]
rows = []
for f in (0.0, 0.2, 0.4, 0.6, 0.8, 0.92, 1.0):
    row = []
    for th in CT:
        zc = arch_col(abs(th)) if abs(th) < THC else ARCH_END_Z
        top = zc - arch_gap(hx(th, zc))
        row.append(hp(th, BASE_Z + (top - BASE_Z) * f, CAS_LIFT))
    rows.append(row)
grid(cas, rows)
tag(cas, 'joint_head')
new_obj("DS_MouthCassette", cas, M_PLATE, 50, outward=True, thickness=-0.02)

core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36)
tag(core, 'joint_head')
new_obj("DS_HeadCore", core, M_JOINT, 60)
# top of the head (under the hat), the underside and the layered neck bearing
loft(plate, [fb(4.50, 0.16, -0.14, 0.14), fb(4.515, 0.22, -0.22, 0.165), fb(4.5605, 0.2615, -0.2645, 0.1895)], seg=32, caps=(True, False))
loft(plate, [fb(5.8695, 0.0945, -0.0495, 0.1145), fb(5.885, 0.05, -0.01, 0.07)], seg=32, caps=(False, True))
lathe(steel, (0, 0.0, 4.40), (0, 0, 1), [(0.0, 0.11), (0.03, 0.14), (0.05, 0.14), (0.058, 0.118), (0.066, 0.152), (0.088, 0.152),
                                          (0.096, 0.124), (0.104, 0.156), (0.128, 0.156), (0.136, 0.13), (0.15, 0.13)], seg=24)

# eyes: cream ball behind the slot, dark pupil low in it, a dark lid line along the top
eyes, iris, lash = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    rows = []
    for z in (5.495, 5.515, 5.535, 5.555):
        rows.append([hp(s * math.degrees(math.asin(min(0.99, (EYE_X + EYE_A * 1.15 * (i / 4 - 1)) / rxz(z)))), z, -0.005) for i in range(9)])
    grid(eyes, rows)
    p, n = ring_pt(HEAD, 5.516, 270 + s * math.degrees(math.asin((EYE_X - 0.004) / rxz(5.516))), -0.0042)
    puck(iris, p, n, 0.0115, 0.004, seg=12)
    pts, rr = [], []
    for i in range(11):
        x = EYE_X + EYE_A * (i / 5 - 1)
        th = math.degrees(math.asin(x / rxz(EYE_Z)))
        pts.append(hp(s * th, EYE_Z + eye_col(th)[1] + 0.002, 0.002))
        rr.append(0.003 + 0.003 * math.sin(math.pi * i / 10))
    tube(lash, pts, rr, seg=5)
for _b in (eyes, iris, lash):
    tag(_b, 'joint_head')
new_obj("DS_Eyes", eyes, M_EYE, 60, outward=True)
new_obj("DS_Iris", iris, M_IRIS, 40)
new_obj("DS_Lids", lash, M_HAIR, 40)

# brows: heavy black bars slanting down to the nose
brow = bmesh.new()
for s in (-1, 1):
    o = [(0.012, 5.572), (0.035, 5.615), (0.118, 5.652), (0.127, 5.628), (0.062, 5.592), (0.02, 5.552)]
    panel(brow, HEAD, [(s * x, z) for x, z in o], lambda x, z: 0.008, cuts=1)
tag(brow, 'joint_head')
new_obj("DS_Brows", brow, M_HAIR, 35, outward=True, thickness=-0.013)

# nose: a long ridge widening to a blunt end with two wings
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (5.61, 5.55, 5.48, 5.42, 5.385, 5.36, 5.35)
NR = (0.007, 0.011, 0.016, 0.022, 0.027, 0.024, 0.012)
tube(nose, [Vector((0, ny(z) + r * 0.5, z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.032, ny(5.385) + 0.022, 5.385)) @ Matrix.Diagonal((0.022, 0.022, 0.016, 1.0)))
tag(nose, 'joint_head')
new_obj("DS_Nose", nose, M_PLATE, 60)

# ears: small shells on the sides, at the front edge of the hair
ears = bmesh.new()
for a in (26, 154):
    p, n = ring_pt(HEAD, 5.52, a, 0.004)
    m = Matrix.Translation(p) @ n.to_track_quat('X', 'Z').to_matrix().to_4x4() @ Matrix.Diagonal((0.014, 0.034, 0.055, 1.0))
    bmesh.ops.create_uvsphere(ears, u_segments=12, v_segments=8, radius=1.0, matrix=m)
    lathe(joint, p + n * 0.011, n, [(0.0, 0.012), (0.003, 0.012)], seg=10)
tag(ears, 'joint_head')
new_obj("DS_Ears", ears, M_PLATE, 60)

# hair shell: a black tongue-shaped plate on the back of the head, from under the hat down to a rounded point
hair = bmesh.new()
rows = []
for i in range(12):
    z = 5.22 + (TOP_Z - 5.22) * i / 11
    half = 68.0 * min(1.0, max(0.0, (z - 5.22) / 0.33)) ** 0.6
    rows.append([ring_pt(HEAD, z, 90 + half * (j / 8 - 1), 0.011)[0] for j in range(17)])
grid(hair, rows)
bmesh.ops.remove_doubles(hair, verts=hair.verts, dist=0.0003)
tag(hair, 'joint_head')
new_obj("DS_Hair", hair, M_HAIR, 50, outward=True, thickness=-0.011)

# hat: a small bowler tipped back, with a band
hat, hband = bmesh.new(), bmesh.new()
HO, HA = Vector((0, 0.03, 5.815)), Vector((0, 0.17, 1)).normalized()
lathe(hat, HO, HA, [(0.0, 0.10), (0.004, 0.172), (0.02, 0.183), (0.04, 0.172), (0.034, 0.108), (0.05, 0.10), (0.20, 0.096),
                    (0.228, 0.085), (0.245, 0.06), (0.252, 0.03), (0.254, 0.001)], seg=28)
lathe(hband, HO, HA, [(0.045, 0.1035), (0.095, 0.1025)], seg=28, caps=False)
tag(hat, 'joint_head')
tag(hband, 'joint_head')
new_obj("DS_Hat", hat, M_HAT, 50)
new_obj("DS_HatBand", hband, M_BAND, 50, outward=True, thickness=0.004)

# rivets
for th, z in ((6, 4.60), (-6, 4.60), (THC - 5, 4.62), (-THC + 5, 4.62), (THC + 6, 4.90), (-THC - 6, 4.90), (THC + 6, 4.62), (-THC - 6, 4.62),
              (5, 5.70), (-5, 5.70), (60, 5.30), (-60, 5.30)):
    p, n = ring_pt(HEAD, z, 270 + th, CAS_LIFT if abs(th) < THC and z < 4.8 else 0.0)
    puck(plate, p, n, 0.0075, 0.008, seg=6)
for z in (4.62, 4.85, 5.08):
    for a in (84, 96):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.0075, 0.008, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.005

loft(shirt, [fb(4.50, 0.235, -0.19, 0.265), fb(4.62, 0.21, -0.165, 0.235), fb(4.62, 0.195, -0.15, 0.22), fb(4.515, 0.20, -0.155, 0.225)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.025, s * 0.22, 4.54), (s * 0.065, s * 0.245, 4.47), (s * 0.12, s * 0.18, 4.37)], 0.014, nx=4)
patch(tie, SS, [(-0.06, 0.06, 4.50), (-0.08, 0.08, 4.44), (-0.05, 0.05, 4.36)], 0.03, nx=4)
patch(tie, SS, [(-0.05, 0.05, 4.37), (-0.08, 0.08, 4.15), (-0.085, 0.085, 4.06)], 0.008, nx=4)

panel(placket, TS, [(-0.02, 2.428), (0.14, 2.428), (0.14, 3.78), (0.06, 3.955), (-0.02, 3.955)], lambda x, z: 0.004, cuts=2)
for z in (3.50, 3.31, 3.09, 2.86, 2.67):
    p = surf(TS, 0.05, z, 0.013)
    lathe(pewter, p, (0, -1, 0), [(0.0, 0.04), (0.009, 0.04), (0.018, 0.031), (0.018, 0.023), (0.011, 0.021)], seg=14)
    lathe(pewter, p, (0, -1, 0), [(0.009, 0.021), (0.022, 0.015), (0.026, 0.004)], seg=10)
    lathe(joint, p, (0, -1, 0), [(0.0, 0.046), (0.005, 0.046)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.123, 3.76 - (3.76 - 2.60) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.021) for x, z in edge], [SR] * len(edge), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)

# hem band: a riveted strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.005)[0] for a in HB] for z in (2.424, 2.50, 2.585)])
tag(hemband, '@jacket')
new_obj("DS_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.013)
hs = [ring_pt(TS, 2.565, a, 0.021)[0] for a in HB]
tube(stitch, hs, [SR] * len(hs), seg=4)
for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):
    p, n = ring_pt(TS, 2.495, a, 0.018)
    lathe(pewter, p, n, [(0.0, 0.027), (0.009, 0.027), (0.017, 0.014), (0.02, 0.001)], seg=10)


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
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)
breast = [(0.235, 3.76), (0.455, 3.76), (0.455, 3.44), (0.42, 3.40), (0.27, 3.40), (0.235, 3.44)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)
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
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 3.80
slope = (surf(TS, 0, MZ + 0.1).y - surf(TS, 0, MZ - 0.1).y) / 0.2
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.034
medal_p, medal_j = bmesh.new(), bmesh.new()
exec(compile(open("/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc - mn * 0.0202, mn, mt, 0.155, 'tie')
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.20, 4.50, 0.02), surf(TS, s * (g(4.35) + 0.015), 4.35, 0.042), surf(TS, s * (g(4.20) + 0.012), 4.20, 0.042),
           surf(TS, s * 0.025, 4.04, 0.044), bail + Vector((s * 0.014, 0, 0))]
    tube(cord, pts, [0.01] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("DS_Shirt", shirt, M_SHIRT, 30)
new_obj("DS_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.012)
new_obj("DS_Stitching", stitch, M_STITCH, 40)
new_obj("DS_Tie", tie, M_TIE, 30, outward=True, thickness=0.018)
new_obj("DS_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.014)
new_obj("DS_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.024)
new_obj("DS_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("DS_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.015)
new_obj("DS_Medallion", medal_p, M_PEWTER, 32)
new_obj("DS_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("DS_Cord", cord, M_JOINT, 40)
new_obj("DS_Plates", plate, M_PLATE, 32)
new_obj("DS_Joints", joint, M_JOINT, 40)
new_obj("DS_Steel", steel, M_STEEL, 40)
new_obj("DS_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("DSCam", bpy.data.cameras.new("DSCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("DSSun", bpy.data.lights.new("DSSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("DSFill", bpy.data.lights.new("DSFill", 'AREA'))
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
