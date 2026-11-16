"""Build the HD Pencil Pusher (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (570 px = 5.0 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit B's rest pose at native size (game / 0.633).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/02_Pencil-Pusher_Bossbot/"
H = math.pi / 2
YOFF = 0.0              # the sheet's centre line (the pencil tip) is the skeleton's centre line
STRIPE = 0.05           # pinstripe spacing, game units
K = 3.35 / 5.29         # suit B scale for this cog
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'
if scene.world and scene.world.use_nodes and scene.world.node_tree.nodes.get('Background'):
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.6


def get_col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("PencilPusher")
refcol = get_col("PencilPusher_Reference")
root = bpy.data.objects.new("PencilPusher", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "refplanes/pp_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 5.0
    e.empty_image_offset = (-0.5, 0)
    e.location = loc
    e.rotation_euler = rot
    e.color[3] = 0.6
    e.use_empty_image_alpha = True
    e.hide_render = True


ref("front", (0, 3, 0), (H, 0, 0))
ref("back", (0, -3, 0), (H, 0, math.pi))
ref("left", (-3, 0, 0), (H, 0, H))
ref("right", (3, 0, 0), (H, 0, -H))

# ---------------------------------------------------------------- materials
M_SUIT = pmat("PP_Suit", (0.17, 0.045, 0.032), 0.88, var=0.35, grime=0.12, stripe=(0.40, 0.19, 0.15), weave=0.5, bump=0.25,
              bscale=160, sheen=0.04, rvar=0.06, nscale=8.0)                               # pinstripe wool
M_LINING = pmat("PP_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("PP_Stitch", (0.62, 0.42, 0.36), 0.85, var=0.2)
M_PLATE = pmat("PP_Plate", (0.70, 0.50, 0.41), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1,
               bscale=60, rvar=0.14, nscale=8.0)                                           # painted, worn head and hand plating
M_JOINT = pmat("PP_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=80, rvar=0.18)
M_STEEL = pmat("PP_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=90, rvar=0.14)
M_GRAPHITE = pmat("PP_Graphite", (0.022, 0.022, 0.024), 0.32, 0.6, var=0.3, wear=0.25, rvar=0.12, nscale=14.0)
M_BLACK = mat("PP_Black", (0.004, 0.004, 0.004), 0.9)
M_EYE = pmat("PP_Eye", (0.006, 0.006, 0.006), 0.08, var=0.05, rvar=0.03, coat=1.0)
M_SHOE = pmat("PP_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=140, rvar=0.14,
              coat=0.5, wear=0.12)
M_SOLE = pmat("PP_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=90)
M_PEWTER = pmat("PP_Pewter", (0.62, 0.52, 0.47), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=110, rvar=0.15)
M_SHIRT = pmat("PP_Shirt", (0.80, 0.74, 0.68), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("PP_Tie", (0.22, 0.035, 0.03), 0.5, var=0.25, grime=0.15, weave=0.6, sheen=0.5, rvar=0.1)
M_WHITE = mat("PP_Highlight", (0.9, 0.9, 0.9), 0.3)

plate, joint, steel, black, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

# ---------------------------------------------------------------- jacket (game units, modelled standing)
TORSO = [fb(1.80, 0.47, -0.36, 0.34), fb(2.00, 0.47, -0.36, 0.33), fb(2.40, 0.475, -0.37, 0.31),
         fb(2.80, 0.48, -0.38, 0.30), fb(3.00, 0.50, -0.33, 0.32), fb(3.12, 0.56, -0.31, 0.34),
         fb(3.20, 0.62, -0.28, 0.34), fb(3.26, 0.60, -0.26, 0.335), fb(3.30, 0.52, -0.23, 0.32),
         fb(3.33, 0.38, -0.20, 0.29), fb(3.35, 0.25, -0.17, 0.25)]
TS = TORSO
BREAK = 2.98                             # the fronts close here; above it the lapels fold back


def front_gap(z):
    """Half-width of the jacket opening: buttoned shut below the break, a V showing shirt and tie above it
    (measured: 0.06 at z 3.1, 0.11 at 3.2, 0.19 at the neckline)."""
    return 0.003 if z <= BREAK else 0.003 + 0.19 * min(1.0, (z - BREAK) / (3.34 - BREAK)) ** 1.1


# Layer 0: shirt body, closed, up to the base of the neck. Only the V shows.
SHIRT_IN = {2.80: 0.03, 3.00: 0.03, 3.12: 0.03, 3.20: 0.035, 3.26: 0.045, 3.30: 0.06}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
bm = bmesh.new()
loft(bm, SS + [fb(3.325, 0.22, -0.16, 0.22), fb(3.33, 0.12, -0.09, 0.13)], seg=28)
new_obj("PP_ShirtBody", bm, M_SHIRT)

# Layer 1: the jacket, a buttoned single-breasted shell with real cloth thickness; hem and neckline are open.
bm = bmesh.new()
shell(bm, TS, front_gap, parts=(8, 20, 8))
for v in bm.verts:                       # neckline dips toward the front
    if v.co.z > 3.34 and v.co.y < 0:
        v.co.z -= 0.035 * min(1.0, -v.co.y / 0.17)
new_obj("PP_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.03)

# Hem lining: closes the underside of the jacket in to the trouser seat.
bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(1.798, 0, hem_cy, hem_rx - 0.008, hem_ry - 0.008), (1.815, 0, 0.0, 0.36, 0.27)], seg=28, caps=(False, False))
new_obj("PP_HemLining", bm, M_LINING)

# Jacket collar: stands round the back of the neck, folds over and falls onto the shoulders (back view: top at
# z 3.40, fall ending at z 3.30, 0.64 wide).
bm = bmesh.new()
COLLAR = [fb(3.33, 0.20, -0.15, 0.245), fb(3.385, 0.205, -0.16, 0.265), fb(3.38, 0.265, -0.20, 0.31), fb(3.315, 0.32, -0.23, 0.345)]
arc_band(bm, COLLAR, -28, 208, 22, zfun=lambda si, sn: (0.02 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("PP_Collar", bm, M_SUIT, outward=False, thickness=0.02)
COLLAR_EDGE = []
for i in range(23):
    t = math.radians(-28 + 236 * i / 22)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 3.337)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Checked against the game's walk and neutral frames: scale_jnt3_1 / scale_jnt9_1 carry the upper
# arms, jnt3_2 / jnt9_2 the forearms, scale_jnt1_1 / scale_jnt2_1 the thighs, jnt1_2 / jnt2_2 the shins,
# to_legL/R the feet and to_MAIN the pelvis.
RIG = json.load(open(SP + "pp_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.05 / K
AZ = JR["Lh_wrist"].z                    # the arm lies along x at this height (4.96)
WX = JR["Lh_wrist"].x                    # wrist joint (3.22); shoulder joint x 0.89, elbow about x 1.97
AY = JR["Lh_wrist"].y
# The shoulder end is a dome centred on the shoulder joint, so the arm can hang or swing without poking up.
SLEEVE = [(0.66, 0.15, AZ, 0.07, 0.05), (0.70, 0.15, AZ, 0.16, 0.13), (0.76, 0.15, AZ, 0.24, 0.19),
          (0.83, 0.15, AZ, 0.28, 0.225), (0.89, 0.15, AZ, 0.29, 0.235), (1.20, 0.16, AZ, 0.29, 0.24),
          (1.60, 0.17, AZ, 0.27, 0.235), (1.97, 0.17, AZ, 0.255, 0.225), (2.50, 0.15, AZ, 0.24, 0.215),
          (2.95, 0.14, AZ, 0.235, 0.21), (2.93, 0.14, AZ, 0.185, 0.165)]
BAND = [(2.60, 0.15, AZ, 0.257, 0.232), (2.965, 0.14, AZ, 0.252, 0.227)]      # turned-up cuff band
sleeves, plate_r, joint_r, pewter_r, stitch_r = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    xloft(sleeves, SLEEVE, seg=22, sx=s)
    xloft(sleeves, BAND, seg=22, sx=s)
    for x in (2.74, 2.86):                                       # two buttons on the back-outer side of the band
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(math.radians(50)), math.sin(math.radians(50))))
        puck(pewter_r, (s * x, cy + (ry + 0.003) * n.y, cz + (rz + 0.003) * n.z), n, 0.026, 0.02)
    for x in (2.625, 2.945):                                     # stitching round the band
        _, cy, cz, ry, rz = BAND[0] if x < 2.8 else BAND[1]
        ring = [Vector((s * x, cy + (ry + 0.003) * math.cos(math.radians(a)), cz + (rz + 0.003) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(stitch_r, ring, [0.0065] * len(ring), seg=4)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("PP_Sleeves", sleeves, M_SUIT, 60, rest=True)

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
new_obj("PP_HandPlates", plate_r, M_PLATE, 32, rest=True)
new_obj("PP_HandJoints", joint_r, M_JOINT, 40, rest=True)
new_obj("PP_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("PP_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- trousers: one sealed garment. The seat is a closed bowl on the pelvis (to_MAIN, z 3.45) running up inside
# the jacket (hem at z 2.84 here); each leg comes straight down round hip (z 3.16) -> knee (1.67) -> ankle (0.14).
seat = bmesh.new()
loft(seat, [(2.50, 0, 0.03, 0.05, 0.05), (2.54, 0, 0.03, 0.25, 0.22), (2.62, 0, 0.03, 0.40, 0.32), (2.75, 0, 0.03, 0.50, 0.38),
            (2.95, 0, 0.02, 0.52, 0.42), (3.20, 0, 0.01, 0.58, 0.46), (3.50, 0, 0.0, 0.60, 0.47), (3.75, 0, 0.0, 0.50, 0.40),
            (3.90, 0, 0.0, 0.35, 0.30)], seg=24, centres=(270, 90))
new_obj("PP_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
LEG = [(0.30, 0.262, 0.04, 0.252, 0.345), (0.45, 0.26, 0.04, 0.248, 0.34), (1.00, 0.255, 0.04, 0.24, 0.33),
       (1.67, 0.255, 0.03, 0.24, 0.33), (2.40, 0.255, 0.03, 0.245, 0.34), (3.00, 0.26, 0.02, 0.25, 0.36)]
for s in (-1, 1):
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("PP_Trousers", bm, M_SUIT, 60, rest=True)

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
new_obj("PP_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("PP_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.05

# ---------------------------------------------------------------- head: a pencil, built from its plates
# HEAD is the outer surface the plates lie on (front view half-widths, side view front and back). Plates: two
# halves split by the centre seam, in three bands split by the seams at z 3.78 and z 4.25 (back view); the mouth
# cassette (upper and lower jaw) sits in the front of the lowest band; the graphite point sits in the scalloped
# top of the shell.
HEAD = [fb(3.47, 0.20, -0.175, 0.26), fb(3.60, 0.185, -0.16, 0.235), fb(3.80, 0.16, -0.135, 0.20),
        fb(4.00, 0.135, -0.11, 0.17), fb(4.20, 0.11, -0.095, 0.135), fb(4.40, 0.085, -0.08, 0.09),
        fb(4.63, 0.052, -0.052, 0.052), fb(4.70, 0.043, -0.043, 0.043)]
GAP = 0.0012                     # half the width of a panel line: a hairline, the plates all but touch
SEAM1, SEAM2, SHELL_TOP = 3.78, 4.25, 4.615
CAS_HALF, CAS_TOP = 68.0, 3.777          # cassette: half-angle at the base, height of its arched top
MOUTH_HALF = 58.0


def hp(a, z, eps=0.0):
    return ring_pt(HEAD, z, a, eps)[0]


def arch(theta):                 # top of the mouth cassette at angle theta from centre front
    return 3.45 + (CAS_TOP - 3.45) * math.sqrt(max(0.0, 1 - (theta / CAS_HALF) ** 2))


def arch_half(z):                # half-angle of the cassette at height z
    return 0.0 if z >= CAS_TOP else CAS_HALF * math.sqrt(max(0.0, 1 - ((z - 3.45) / (CAS_TOP - 3.45)) ** 2))


def frown(theta):                # the mouth line: z 3.70 at the centre, 3.56 at the corners (front view x 0.17)
    return 3.70 - 0.14 * (theta / MOUTH_HALF) ** 2


def lip(theta):                  # half-height of the mouth slot: a lens that closes at each corner
    return 0.012 * math.sqrt(max(0.0, 1 - (theta / MOUTH_HALF) ** 2))


def agap(z):                     # the plate gap as an angle at height z
    return math.degrees(GAP / interp(HEAD, z)[3])


def cas_x(z):                    # front-view half-width of the mouth cassette at height z
    return interp(HEAD, z)[3] * math.sin(math.radians(arch_half(z)))


CREASE_LOW = 3.70                # the crease beside the nose runs down to the edge of the mouth plate here


def crease(z):                   # the line from beside the nose down and out to the edge of the mouth, as on a face
    pts = [(CREASE_LOW, cas_x(CREASE_LOW)), (3.78, 0.105), (3.90, 0.085), (4.00, 0.035), (4.03, 0.0)]
    for (z0, x0), (z1, x1) in zip(pts, pts[1:]):
        if z <= z1:
            return x0 + (x1 - x0) * max(0.0, (z - z0) / (z1 - z0))
    return 0.0


EYE = (0.055, 4.135, 0.03, 0.045)        # socket: centre x, z, half-width, half-height


def in_eye(x, z, grow=1.0):
    return ((abs(x) - EYE[0]) / (EYE[2] * grow)) ** 2 + ((z - EYE[1]) / (EYE[3] * grow)) ** 2 < 1.0


plates = bmesh.new()
for s in (1, -1):
    # top band: centre front round to centre back, up to a scalloped rim like a sharpened pencil
    rows = []
    zs = (SEAM2 + GAP, 4.33, 4.42, 4.51, 4.58, SHELL_TOP)
    for z in zs:
        g = agap(z)
        row = []
        for i in range(11):
            a = 270 + g + (180 - 2 * g) * i / 10
            zz = z + (0.022 * math.cos(math.radians(6 * (a - 270))) if z == SHELL_TOP else 0.0)
            row.append(hp(a, zz))
        rows.append(mirror(row, s))
    grid(plates, rows)
    # middle band: the face. Front part laid out by x so the eye socket can be cut; then round to centre back.
    zs = (SEAM1 + GAP, 3.85, 3.92, 3.98, 4.03, 4.065, 4.085, 4.10, 4.118, 4.135, 4.152, 4.17, 4.185, 4.205, SEAM2 - GAP)
    NX, NA = 20, 7
    P, V = [], []
    for z in zs:
        rx = interp(HEAD, z)[3]
        x0, xe = crease(z) + GAP, 0.88 * rx
        prow = [(x0 + (xe - x0) * i / NX, z) for i in range(NX + 1)]
        a0 = 360 - math.degrees(math.acos(xe / rx))
        prow += [(None, a0 + (450 - agap(z) - a0) * j / NA) for j in range(1, NA + 1)]
        P.append(prow)
    INSIDE = [[p[0] is not None and in_eye(p[0], p[1]) for p in prow] for prow in P]
    for r, prow in enumerate(P):             # socket rim: points just inside it move out onto its edge
        for c, (x, z) in enumerate(prow):
            if INSIDE[r][c]:
                near = any(not INSIDE[rr][cc] for rr in (r - 1, r, r + 1) for cc in (c - 1, c, c + 1)
                           if 0 <= rr < len(P) and 0 <= cc <= NX)
                if near:
                    d = Vector(((x - EYE[0]) / EYE[2], (z - EYE[1]) / EYE[3]))
                    d = d.normalized() if d.length > 1e-6 else Vector((1, 0))
                    P[r][c] = (EYE[0] + d.x * EYE[2], EYE[1] + d.y * EYE[3])
    for r, prow in enumerate(P):
        vrow = []
        for c, p in enumerate(prow):
            if p[0] is None:
                co = hp(p[1], zs[r])
            else:
                co = surf(HEAD, p[0], p[1])
            vrow.append(plates.verts.new((s * co.x, co.y, co.z)))
        V.append(vrow)
    for r in range(len(P) - 1):
        for c in range(len(P[0]) - 1):
            if INSIDE[r][c] and INSIDE[r][c + 1] and INSIDE[r + 1][c + 1] and INSIDE[r + 1][c]:
                continue                         # inside the socket: left open
            plates.faces.new((V[r][c], V[r][c + 1], V[r + 1][c + 1], V[r + 1][c]))
    # bottom band: from the edge of the mouth plate (or, above it, from the crease) round to centre back. The seam
    # at z 3.78 therefore stops at the crease: nothing cuts across the face.
    rows = []
    for z in (3.47 + GAP, 3.53, 3.60, 3.66, CREASE_LOW, 3.72, 3.74, 3.757, 3.768, SEAM1 - GAP):
        if z < CREASE_LOW:
            a0 = 270 + arch_half(z) + agap(z)
        else:
            a0 = 270 + math.degrees(math.asin(min(0.99, (crease(z) + GAP) / interp(HEAD, z)[3])))
        rows.append(mirror([hp(a0 + (450 - agap(z) - a0) * i / 9, z) for i in range(10)], s))
    grid(plates, rows)
for v in [v for v in plates.verts if not v.link_faces]:
    plates.verts.remove(v)
# plate under the nose: one piece between the two creases, from the nose down to the top edge of the mouth plate
mid = bmesh.new()
for sgn in (1, -1):
    rows = []
    for z in (CREASE_LOW + 0.002, 3.72, 3.74, 3.757, 3.768, 3.7745, 3.7765, CAS_TOP + GAP, 3.79, 3.83, 3.88, 3.93, 3.97, 3.995):
        inner = cas_x(z) + GAP if z < CAS_TOP else 0.0          # above the mouth plate the two halves meet and are welded
        outer = max(inner + 0.0005, crease(z) - GAP)
        rows.append([surf(HEAD, sgn * (inner + (outer - inner) * i / 5), z) for i in range(6)])
    grid(mid, rows)
bmesh.ops.remove_doubles(mid, verts=mid.verts, dist=0.0004)
_me = bpy.data.meshes.new("tmp")
mid.to_mesh(_me)
mid.free()
plates.from_mesh(_me)
bpy.data.meshes.remove(_me)
# mouth cassette: upper jaw (between the arched top and the mouth line) and lower jaw (mouth line down to the base)
# mouth cassette: ONE domed plate with the frown cut through it as a slot that stops short of the plate's edges, so
# the upper and lower jaw are joined at both corners (no loose points, nothing open at the ends).
CAS_LIFT = 0.006
LT = [-66.5 + 133.0 * i / 38 for i in range(39)]
cas = bmesh.new()
crow = []
for th in LT:
    top = arch(th) - GAP
    mid = max(3.485, min(frown(th), top - 0.004))
    h = lip(th) if abs(th) < MOUTH_HALF else 0.0
    zs_col = [3.475 + (mid - h - 3.475) * f for f in (0.0, 0.4, 0.75, 1.0)] + [mid + h + (top - mid - h) * f for f in (0.0, 0.25, 0.6, 1.0)]
    crow.append([(cas.verts.new(hp(270 + th, z, CAS_LIFT)), h) for z in zs_col])
for a, b in zip(crow, crow[1:]):
    for k in range(7):
        if k == 3 and (a[k][1] > 0 or b[k][1] > 0):
            continue                                     # the slot itself
        if k == 3:
            continue                                     # outside the slot the two rows coincide and are welded below
        cas.faces.new((a[k][0], b[k][0], b[k + 1][0], a[k + 1][0]))
bmesh.ops.remove_doubles(cas, verts=cas.verts, dist=0.0005)
_me = bpy.data.meshes.new("tmp")
cas.to_mesh(_me)
cas.free()
plates.from_mesh(_me)
bpy.data.meshes.remove(_me)
tag(plates, 'joint_head')
head_ob = new_obj("PP_HeadPlates", plates, M_PLATE, 35, outward=True, thickness=-0.02)

# Substructure: a closed inner shell just under the plates, the full height of the head. Every panel line, the eye
# sockets and the mouth slot open onto it, so a seam is a shallow dark groove and never a hole into the head.
core = bmesh.new()
CORE_IN = 0.011
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in [interp(HEAD, 3.45)] + [r for r in HEAD if r[0] < 4.65]], seg=32)
tag(core, 'joint_head')
new_obj("PP_HeadCore", core, M_JOINT, 60)
# dark throat seen through the mouth slot, lying on the substructure
UT = [-MOUTH_HALF + 2 * MOUTH_HALF * i / 24 for i in range(25)]
grid(black, [[hp(270 + th, frown(th) + k * (lip(th) + 0.006), -CORE_IN + 0.0015) for th in UT] for k in (-1, 1)])
# base of the head: chamfered underside with the neck socket in it
loft(plate, [fb(3.43, 0.135, -0.11, 0.15), fb(3.425, 0.17, -0.145, 0.225), fb(3.466, 0.199, -0.174, 0.259)], seg=28, caps=(False, False))
# neck bearing: stacked rings from the shirt collar up into the socket
lathe(steel, (0, 0.02, 3.29), (0, 0, 1), [(0.0, 0.10), (0.03, 0.125), (0.05, 0.125), (0.058, 0.105), (0.066, 0.138), (0.088, 0.138),
                                          (0.096, 0.112), (0.104, 0.142), (0.128, 0.142), (0.136, 0.118), (0.17, 0.118)], seg=24)
# graphite point: seated inside the scalloped rim, ground to a point
lathe(steel, (0, 0, 4.555), (0, 0, 1), [(0.0, 0.050), (0.02, 0.057)], seg=18, caps=False)      # ferrule lip under the scallops
graphite = bmesh.new()
lathe(graphite, (0, 0, 4.56), (0, 0, 1), [(0.0, 0.03), (0.02, 0.054), (0.07, 0.05), (0.20, 0.03), (0.33, 0.013), (0.425, 0.003), (0.44, 0.0005)], seg=18)
tag(graphite, 'joint_head')
new_obj("PP_Graphite", graphite, M_GRAPHITE, 40)

# brows: raised ridges angled down toward the nose; nose: a small wedge on the plate under the eyes
brow = bmesh.new()
for s in (-1, 1):
    o = [(0.01, 4.15), (0.028, 4.19), (0.088, 4.245), (0.102, 4.218), (0.05, 4.168), (0.016, 4.128)]
    panel(brow, HEAD, [(s * x, z) for x, z in o], lambda x, z: 0.016, cuts=1)
tag(brow, 'joint_head')
new_obj("PP_Brows", brow, M_GRAPHITE, 35, outward=True, thickness=-0.022)
ny = lambda z: surf(HEAD, 0, z).y
tube(plate, [(0, ny(4.04) + 0.006, 4.04), (0, ny(3.99) - 0.004, 3.99), (0, ny(3.955) - 0.009, 3.955), (0, ny(3.938) + 0.004, 3.938)],
     [0.006, 0.013, 0.02, 0.012], seg=6)
eyes, white = bmesh.new(), bmesh.new()
for s in (-1, 1):
    c = surf(HEAD, s * EYE[0], EYE[1], -0.024)
    n = (surf(HEAD, s * EYE[0], EYE[1], 1.0) - surf(HEAD, s * EYE[0], EYE[1], 0.0)).normalized()
    bmesh.ops.create_uvsphere(eyes, u_segments=14, v_segments=8, radius=0.03,
                              matrix=Matrix.Translation(c) @ Matrix.Diagonal((1.0, 1.0, 1.35, 1.0)))
    puck(white, c + n * 0.028 + Vector((-s * 0.006, 0, 0.008)), n, 0.007, 0.004, seg=6)
# rivets along the seams
for z in (SEAM1 + 0.03, SEAM2 + 0.03, SEAM2 - 0.03, SEAM1 - 0.03):
    for a in (20, 60, 82, 98, 120, 160):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.0065, 0.008, seg=6)
for z in (3.52, 3.66, 3.95, 4.10, 4.40, 4.52):
    for a in (83, 97):
        p, n = ring_pt(HEAD, z, a, 0.0)
        puck(plate, p, n, 0.0065, 0.008, seg=6)
for th in (-52, -18, 18, 52):                                    # cassette fixings
    for z in (3.50,):
        p, n = ring_pt(HEAD, z, 270 + th, CAS_LIFT)
        puck(plate, p, n, 0.008, 0.008, seg=6)
for _bm in (eyes, white, plate, joint, steel, black, pewter):
    tag(_bm, 'joint_head')
new_obj("PP_Eyes", eyes, M_EYE, 60)
new_obj("PP_EyeHighlights", white, M_WHITE)

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()

# Shirt collar: a band standing round the neck, folded down all the way round, with two points at the front.
loft(shirt, [fb(3.30, 0.175, -0.14, 0.20), fb(3.395, 0.155, -0.12, 0.175), fb(3.395, 0.145, -0.11, 0.165), fb(3.31, 0.15, -0.115, 0.17)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.02, s * 0.17, 3.33), (s * 0.05, s * 0.19, 3.295), (s * 0.115, s * 0.16, 3.255)], 0.012, nx=4)

# Tie: knot under the collar, blade running down the shirt front to where the jacket closes.
patch(tie, SS, [(-0.05, 0.05, 3.335), (-0.066, 0.066, 3.295), (-0.04, 0.04, 3.25)], 0.026, nx=4)
patch(tie, SS, [(-0.038, 0.038, 3.255), (-0.06, 0.06, 3.10), (-0.066, 0.066, 2.99)], 0.007, nx=4)

# Button stand: the left front laps over the right; its stitched edge runs down to the hem. Five buttons, the top
# one behind the medallion.
panel(placket, TS, [(-0.012, 1.806), (0.095, 1.806), (0.095, 2.80), (0.03, 2.955), (-0.012, 2.955)], lambda x, z: 0.004, cuts=2)
for z in (2.78, 2.61, 2.44, 2.245, 2.00):
    p = surf(TS, 0.03, z, 0.012)
    lathe(pewter, p, (0, -1, 0), [(0.0, 0.036), (0.008, 0.036), (0.016, 0.028), (0.016, 0.021), (0.01, 0.019)], seg=14)
    lathe(pewter, p, (0, -1, 0), [(0.008, 0.019), (0.02, 0.014), (0.024, 0.004)], seg=10)
    lathe(joint, p, (0, -1, 0), [(0.0, 0.042), (0.005, 0.042)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
edge = [(0.082, 2.80 - (2.80 - 1.87) * i / 12) for i in range(13)]
tube(stitch, [surf(TS, x, z, 0.02) for x, z in edge], [0.0042] * len(edge), seg=4)                    # front edge
hem = [ring_pt(TS, 1.865, a, 0.004)[0] for a in range(-82, 263, 6) if not (-90 <= a < -76)]
tube(stitch, hem, [0.0042] * len(hem), seg=4)                                                         # hem
tube(stitch, COLLAR_EDGE, [0.0042] * len(COLLAR_EDGE), seg=4)


def roll_lift(x, z):             # a lapel stands highest at the fold and lies flat at its outer edge
    return 0.008 + 0.022 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.10)


def flat_lift(x, z):
    return 0.005


g = front_gap
for s in (-1, 1):
    lapel = [(0.004, 2.975), (0.30, 3.155), (0.33, 3.215), (0.215, 3.235), (g(3.25), 3.25), (g(3.16), 3.16), (g(3.07), 3.07)]
    collar_front = [(g(3.25), 3.25), (0.215, 3.235), (0.345, 3.235), (0.36, 3.295), (0.29, 3.325), (g(3.325), 3.325)]
    flap = [(0.225, 2.305), (0.455, 2.305), (0.455, 2.11), (0.44, 2.085), (0.24, 2.085), (0.225, 2.11)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.022, inset=0.016, step=0.04, radius=0.004)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)                                             # pocket flap
    topstitch(stitch, TS, o, lambda x, z: 0.02, inset=0.014, step=0.04, radius=0.004)
breast = [(0.165, 2.795), (0.37, 2.795), (0.37, 2.555), (0.34, 2.52), (0.195, 2.52), (0.165, 2.555)]
panel(pockets, TS, breast, flat_lift, cuts=2)                                            # breast pocket
topstitch(stitch, TS, breast, lambda x, z: 0.02, inset=0.014, step=0.04, radius=0.004)
welt = [(0.165, 2.795), (0.37, 2.795), (0.37, 2.755), (0.165, 2.755)]
panel(pockets, TS, welt, lambda x, z: 0.012, cuts=1)
pocket_sq = [surf(TS, x, z, 0.022) for x, z in ((0.185, 2.79), (0.35, 2.79), (0.345, 2.845), (0.315, 2.83), (0.295, 2.895),
                                                (0.268, 2.84), (0.248, 2.905), (0.225, 2.84), (0.195, 2.86))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')

# Back: two yoke straps sewn from the collar out to the armholes, three studs each, and a half belt with five studs.
for s in (-1, 1):
    o = [(s * x, z) for x, z in ((0.24, 3.232), (0.305, 3.252), (0.455, 3.03), (0.405, 2.985))]
    panel(straps, TS, o, lambda x, z: 0.006, back=True, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.019, inset=0.012, back=True, step=0.04, radius=0.004)
    for x, z in ((0.30, 3.195), (0.35, 3.12), (0.40, 3.047)):
        p = surf(TS, s * x, z, 0.019, back=True)
        nrm = (surf(TS, s * x, z, 1.0, back=True) - surf(TS, s * x, z, 0.0, back=True)).normalized()
        lathe(pewter, p, nrm, [(0.0, 0.017), (0.008, 0.017), (0.014, 0.008), (0.016, 0.001)], seg=10)
belt = [(-0.35, 1.825), (-0.35, 1.92)] + [(x, 1.965 - 0.045 * (x / 0.35) ** 2) for x in (-0.26, -0.13, 0.0, 0.13, 0.26)] + [(0.35, 1.92), (0.35, 1.825)]
panel(straps, TS, belt, lambda x, z: 0.006, back=True, cuts=2)
topstitch(stitch, TS, belt, lambda x, z: 0.019, inset=0.014, back=True, step=0.04, radius=0.004)
for x in (-0.28, -0.14, 0.0, 0.14, 0.28):
    z = 1.905 - 0.03 * (x / 0.35) ** 2
    p = surf(TS, x, z, 0.019, back=True)
    nrm = (surf(TS, x, z, 1.0, back=True) - surf(TS, x, z, 0.0, back=True)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.02), (0.008, 0.02), (0.015, 0.01), (0.017, 0.001)], seg=10)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion (the corp icon). It lies on the closed jacket front, tilted to the chest's slope, and hangs from a cord
# that runs up along the lapel rolls and under the shirt collar.
slope = (surf(TS, 0, 2.94).y - surf(TS, 0, 2.74).y) / 0.2
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, 2.84) + mn * 0.03
medal_p, medal_j = bmesh.new(), bmesh.new()
exec(compile(open("/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc - mn * 0.0166, mn, mt, 0.128, 'tie')
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.155, 3.30, 0.02), surf(TS, s * (g(3.20) + 0.012), 3.20, 0.034), surf(TS, s * (g(3.10) + 0.012), 3.10, 0.034),
           surf(TS, s * 0.02, 3.02, 0.036), bail + Vector((s * 0.012, 0, 0))]
    tube(cord, pts, [0.009] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("PP_Shirt", shirt, M_SHIRT, 30)
new_obj("PP_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.01)
new_obj("PP_Stitching", stitch, M_STITCH, 40)
new_obj("PP_Tie", tie, M_TIE, 30, outward=True, thickness=0.016)
new_obj("PP_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.012)
new_obj("PP_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.02)
new_obj("PP_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.013)
new_obj("PP_BackStraps", straps, M_SUIT, 30, outward=True, thickness=0.013)
new_obj("PP_Medallion", medal_p, M_PEWTER, 32)
new_obj("PP_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("PP_Cord", cord, M_JOINT, 40)
new_obj("PP_Plates", plate, M_PLATE, 32)
new_obj("PP_Joints", joint, M_JOINT, 40)
new_obj("PP_Steel", steel, M_STEEL, 40)
new_obj("PP_MouthInterior", black, M_BLACK)
new_obj("PP_Buttons", pewter, M_PEWTER, 32)

# ---------------------------------------------------------------- check camera + light, stats
cam = bpy.data.objects.new("PPCam", bpy.data.cameras.new("PPCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("PPSun", bpy.data.lights.new("PPSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("PPFill", bpy.data.lights.new("PPFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 110
fill.data.size = 6
fill.location = (-6, -7, 4)
fill.rotation_euler = (Vector((0, 0, 2.4)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
tris = 0
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        n = sum(len(p.vertices) - 2 for p in em.polygons)
        per[o.name] = n
        tris += n
result = {"tris": tris, "per_object": per}
