"""Build the HD CorporateRaider (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (467 px = 8.23 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit C's rest pose at native size (game / 1.63).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/07_Corporate-Raider_Bossbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.11
K = 6.75 / 4.14         # suit C scale for this cog
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


col = get_col("CorporateRaider")
refcol = get_col("CorporateRaider_Reference")
root = bpy.data.objects.new("CorporateRaider", None)
col.objects.link(root)
root.empty_display_size = 0.4
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "refplanes/cr_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 8.6
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
M_SUIT = pmat("CR_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18), weave=0.5, bump=0.25,
              bscale=60, sheen=0.04, rvar=0.06, nscale=6.0)
M_LINING = pmat("CR_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("CR_Stitch", (0.66, 0.50, 0.42), 0.85, var=0.2)
M_PLATE = pmat("CR_Plate", (0.80, 0.66, 0.56), 0.42, 0.1, var=0.22, grime=0.45, wear=0.1, bump=0.1,
               bscale=45, rvar=0.14, nscale=6.0)
M_HAND = pmat("CR_Hand", (0.78, 0.47, 0.44), 0.42, 0.1, var=0.25, grime=0.5, wear=0.08, bump=0.1, bscale=45, rvar=0.14, nscale=6.0)
M_JOINT = pmat("CR_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=60, rvar=0.18)
M_STEEL = pmat("CR_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=70, rvar=0.14)
M_HAIR = pmat("CR_Hair", (0.012, 0.011, 0.011), 0.3, 0.2, var=0.4, wear=0.15, bump=0.2, bscale=140, rvar=0.12, nscale=10.0, coat=0.3)
M_HAT = pmat("CR_Hat", (0.014, 0.012, 0.011), 0.7, var=0.4, wear=0.1, bump=0.3, bscale=200, rvar=0.1, sheen=0.3)
M_BAND = pmat("CR_HatBand", (0.12, 0.04, 0.025), 0.5, var=0.3, weave=0.4, sheen=0.3)
M_EYE = pmat("CR_Eye", (0.92, 0.90, 0.84), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("CR_Iris", (0.02, 0.016, 0.014), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("CR_Shoe", (0.022, 0.012, 0.009), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("CR_Sole", (0.02, 0.017, 0.015), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("CR_Pewter", (0.60, 0.48, 0.40), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=90, rvar=0.15)
M_SHIRT = pmat("CR_Shirt", (0.82, 0.74, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("CR_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

M_IRISRING = pmat("CR_IrisRing", (0.22, 0.10, 0.04), 0.2, var=0.3, coat=0.6)
M_BLUE = pmat("CR_Blue", (0.13, 0.25, 0.45), 0.45, 0.2, var=0.25, grime=0.4, wear=0.15, bump=0.1, bscale=30, rvar=0.14)
M_STACHE = pmat("CR_Moustache", (0.62, 0.60, 0.10), 0.4, 0.1, var=0.25, grime=0.5, grime_col=(0.10, 0.11, 0.01), bump=0.05, bscale=40, rvar=0.1, coat=0.2)
M_PATCH = pmat("CR_Patch", (0.02, 0.018, 0.016), 0.5, var=0.3, bump=0.2, bscale=120, rvar=0.1)
M_BANDANA = pmat("CR_Bandana", (0.45, 0.03, 0.035), 0.6, 0.1, var=0.25, grime=0.3, wear=0.1, bump=0.15, bscale=60, rvar=0.12)
M_SPOT = pmat("CR_Spot", (0.82, 0.70, 0.60), 0.55, 0.1, var=0.15, grime=0.3, rvar=0.1)
M_GOLD = pmat("CR_Gold", (0.75, 0.62, 0.10), 0.3, 0.9, var=0.25, grime=0.4, grime_col=(0.10, 0.12, 0.01), bump=0.05, bscale=60, rvar=0.12)
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

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Suit C (checked against the game's walk and neutral frames for the Flunky): jnt23_1 / jnt24_1 stay
# on the shoulders, Luparm / Ruparm carry the upper arms, jnt26_2 / jnt27_2 the forearms, jnt14_1 / jnt13_1 the
# thighs, jnt14_2 / jnt13_2 the shins, to_legL / to_legR the feet and to_MAIN the pelvis.
RIG = json.load(open(SP + "cr_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.11 / K
LS, LW = JR["jnt23_1"], JR["Lh_wrist"]
RS, RW = JR["jnt24_1"], JR["Rh_wrist"]
AZ = LW.z
WX = LW.x                                # shoulder joint x 1.18, elbow 2.13, wrist 3.09


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


# sleeve: a dome on the shoulder joint, short fat upper arm, hem 0.30 short of the wrist; depth (y) and height (z) radii
SLEEVE = [(0.83, 0.25, AZ, 0.11, 0.08), (0.88, 0.25, AZ, 0.25, 0.19), (0.96, 0.25, AZ - 0.03, 0.38, 0.25),
          (1.08, 0.25, AZ - 0.05, 0.46, 0.25), (1.18, 0.25, AZ - 0.055, 0.47, 0.25), (1.45, 0.27, AZ - 0.04, 0.47, 0.29),
          (1.80, 0.28, AZ - 0.02, 0.455, 0.33), (2.18, 0.30, AZ, 0.415, 0.35), (2.55, 0.26, AZ, 0.375, 0.325),
          (2.79, 0.24, AZ, 0.36, 0.315), (2.76, 0.24, AZ, 0.28, 0.24)]
BAND = [(2.44, 0.27, AZ, 0.395, 0.345), (2.805, 0.24, AZ, 0.378, 0.332)]      # turned-up cuff band


def sleeve_cloth(bm):
    xloft(bm, SLEEVE, seg=22)
    xloft(bm, BAND, seg=22)


def sleeve_buttons(bm):
    for x in (2.56, 2.68):
        _, cy, cz, ry, rz = BAND[0]
        n = Vector((0, math.cos(math.radians(50)), math.sin(math.radians(50))))
        puck(bm, (x, cy + (ry + 0.004) * n.y, cz + (rz + 0.004) * n.z), n, 0.036, 0.03)


def sleeve_stitch(bm):
    for x in (2.47, 2.78):
        _, cy, cz, ry, rz = BAND[0] if x < 2.6 else BAND[1]
        ring = [Vector((x, cy + (ry + 0.004) * math.cos(math.radians(a)), cz + (rz + 0.004) * math.sin(math.radians(a))))
                for a in range(0, 361, 20)]
        tube(bm, ring, [0.0075] * len(ring), seg=4)


pewter_r, stitch_r = both_arms(sleeve_buttons), both_arms(sleeve_stitch)
tag(pewter_r, '@sleeve')
tag(stitch_r, '@sleeve')
new_obj("CR_Sleeves", both_arms(sleeve_cloth), M_SUIT, 60, rest=True)
new_obj("CR_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("CR_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- forearm cuff, wrist joint and hand, flat in the rest pose: fingers straight out along x, index at the front
plate_r, joint_r, cuff_r = bmesh.new(), bmesh.new(), bmesh.new()
KN_X = JR["Lh_1"].x                                              # knuckle joints (0.31 from the wrist)
J2_X = JR["Lh_2"].x                                              # second finger joints (0.19 further)
FINGERS = (("index", JR["Lh_index1"].y - 0.035), ("rest", 0.15), ("rest", 0.31), ("rest", 0.47))   # y of each finger
PLATE_Y = 0.225
for s in (-1, 1):
    S = 'L' if s > 0 else 'R'
    T = Matrix.Identity(4) if s > 0 else Matrix.Translation(JR["Rh_wrist"] - MIRROR @ JR["Lh_wrist"]) @ MIRROR
    R3 = T.to_3x3()
    names = {'L': dict(wrist='Lh_wrist', index=('Lh_index1', 'Lh_index2'), rest=('Lh_1', 'Lh_2'), thumb=('Lh_thumb1', 'Lh_thumb2')),
             'R': dict(wrist='Rh_wrist', index=('Rh_index5', 'Rh_index6'), rest=('Rh_5', 'Rh_6'), thumb=('Rh_thumb7', 'Rh_thumb8'))}[S]
    ax = R3 @ Vector((1, 0, 0))
    c0 = T @ Vector((WX - 0.43, PLATE_Y, AZ))                    # metal cuff starts inside the sleeve
    lathe(cuff_r, c0, ax, [(0.0, 0.243), (0.02, 0.271), (0.30, 0.281), (0.316, 0.298), (0.347, 0.298), (0.357, 0.233)], seg=20)
    lathe(joint_r, c0, ax, [(0.347, 0.207), (0.362, 0.233), (0.381, 0.202), (0.40, 0.233), (0.418, 0.202), (0.43, 0.226)], seg=16)
    for n in (Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((0, 1, 0))):   # ringed boss: outer, front and back faces once the arm hangs
        n = R3 @ n
        puck(cuff_r, c0 + ax * 0.20 + n * 0.277, n, 0.062, 0.016, seg=12)
        puck(joint_r, c0 + ax * 0.20 + n * 0.281, n, 0.043, 0.016, seg=10)
        puck(cuff_r, c0 + ax * 0.20 + n * 0.285, n, 0.023, 0.016, seg=8)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.165, PLATE_Y, AZ + 0.035)), (0.33, 0.68, 0.205), 0.07, 3)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.18, PLATE_Y, AZ - 0.088)), (0.27, 0.58, 0.10), 0.03, 1)
    rbox(joint_r, T @ Matrix.Translation((WX + 0.175, PLATE_Y, AZ - 0.02)), (0.29, 0.62, 0.125), 0.0)
    for k in range(7):
        puck(plate_r, T @ Vector((WX + 0.055, PLATE_Y - 0.28 + 0.093 * k, AZ + 0.138)), R3 @ Vector((0, 0, 1)), 0.0135, 0.012, seg=6)
    tag(cuff_r, names['wrist'])
    tag(plate_r, names['wrist'])                                 # cuff, wrist and hand plates move as one piece with the wrist
    tag(joint_r, names['wrist'])
    for kind, fy in FINGERS:
        j1, j2 = names[kind]
        k0 = Vector((KN_X, fy, AZ + 0.012))
        k1 = Vector((J2_X, fy, AZ + 0.022))
        k2 = k1 + Vector((math.cos(math.radians(-14)), 0, math.sin(math.radians(-14)))) * 0.17
        k3 = k2 + Vector((math.cos(math.radians(-34)), 0, math.sin(math.radians(-34)))) * 0.15
        seg_box(plate_r, T, k0, k1, (0, 0, 1), 0.155, 0.152, 0.035, 2, gap=0.006)
        lathe(joint_r, T @ (k0 + Vector((0, -0.068, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.062), (0.136, 0.062)], seg=10)
        tag(plate_r, j1)
        tag(joint_r, j1)
        seg_box(plate_r, T, k1, k2, (0, 0, 1), 0.155, 0.152, 0.035, 2, gap=0.006)
        seg_box(plate_r, T, k2, k3, (0, 0, 1), 0.155, 0.152, 0.05, 2, gap=0.006)
        for q in (k1, k2):
            lathe(joint_r, T @ (q + Vector((0, -0.068, 0))), R3 @ Vector((0, 1, 0)), [(0, 0.062), (0.136, 0.062)], seg=10)
        tag(plate_r, j2)
        tag(joint_r, j2)
    t1, t2 = JR["Lh_thumb1"].copy(), JR["Lh_thumb2"].copy()
    td = (t2 - t1).normalized()
    t3 = t2 + (td + Vector((0.25, 0, -0.25))).normalized() * 0.17
    lathe(joint_r, T @ (t1 + Vector((0, 0, -0.075))), R3 @ Vector((0, 0, 1)), [(0.0, 0.10), (0.15, 0.10)], seg=14)
    tag(joint_r, names['wrist'])
    seg_box(plate_r, T, t1, t2 + td * 0.02, (0, 0, 1), 0.14, 0.14, 0.035, 2, gap=0.004)
    lathe(plate_r, T @ (t1 + Vector((0, 0, 0.07))), R3 @ Vector((0, 0, 1)), [(0.0, 0.085), (0.02, 0.085), (0.035, 0.055)], seg=14)
    tag(plate_r, names['thumb'][0])
    seg_box(plate_r, T, t2 + td * 0.02, t3, (0, 0, 1), 0.14, 0.14, 0.05, 2, gap=0.006)
    lathe(joint_r, T @ (t2 + td * 0.02 + Vector((0, 0, -0.062))), R3 @ Vector((0, 0, 1)), [(0, 0.056), (0.124, 0.056)], seg=10)
    tag(plate_r, names['thumb'][1])
    tag(joint_r, names['thumb'][1])
new_obj("CR_HandPlates", plate_r, M_HAND, 32, rest=True)
new_obj("CR_Cuffs", cuff_r, M_SHIRT, 40, rest=True)
new_obj("CR_HandJoints", joint_r, M_JOINT, 40, rest=True)

# ---- trousers: one sealed garment. Seat bowl on the pelvis (to_MAIN, z 2.21) running up inside the jacket (hem at
# z 1.74 here); legs straight down round hip (z 1.96) -> knee (1.10) -> ankle (0.14). Wide legs: each sits outside
# its bone (x 0.31) so the two meet down the middle without overlapping.
seat = bmesh.new()
loft(seat, [(1.30, 0, -0.12, 0.08, 0.08), (1.33, 0, -0.12, 0.40, 0.38), (1.40, 0, -0.12, 0.70, 0.64), (1.50, 0, -0.13, 0.90, 0.80),
            (1.62, 0, -0.13, 1.01, 0.88), (1.78, 0, -0.13, 1.04, 0.92), (1.95, 0, -0.13, 1.03, 0.92), (2.10, 0, -0.12, 0.96, 0.90),
            (2.25, 0, -0.10, 0.80, 0.75)], seg=24, centres=(270, 90))
new_obj("CR_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
LEG = [(0.42, 0.385, -0.08, 0.37, 0.50), (0.56, 0.385, -0.08, 0.375, 0.51), (0.85, 0.40, -0.08, 0.39, 0.56),
       (1.10, 0.43, -0.09, 0.42, 0.66), (1.35, 0.47, -0.11, 0.46, 0.77), (1.55, 0.50, -0.12, 0.49, 0.84),
       (1.80, 0.52, -0.13, 0.51, 0.88)]
for s in (-1, 1):
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("CR_Trousers", bm, M_SUIT, 60, rest=True)

# ---- shoes: chunky round-toed derbies, welted, separate heel, pointing straight ahead; heel on the ankle bone
upper, sole = bmesh.new(), bmesh.new()
SHOE = [(0.48, 0.34, 0.12, 0.20), (0.42, 0.34, 0.18, 0.27), (0.22, 0.35, 0.22, 0.31), (-0.05, 0.38, 0.30, 0.31),
        (-0.35, 0.44, 0.385, 0.29), (-0.60, 0.46, 0.405, 0.265), (-0.78, 0.455, 0.375, 0.225), (-0.90, 0.45, 0.30, 0.17),
        (-0.965, 0.45, 0.19, 0.11), (-0.99, 0.45, 0.08, 0.05)]            # (y, centre x, half-width, height above the welt)
WELT, OUTSOLE = 0.104, 0.067
NS = 12


def welt_extra(y):
    return 0.028 if y > 0.1 else 0.045


PLAN = [(y, cx, w) for y, cx, w, h in SHOE]
for s in (-1, 1):
    shoe_piece(upper, s, SHOE)
    cap_y = -0.66
    shoe_piece(upper, s, [(cap_y, *shoe_at(cap_y))] + [st for st in SHOE if st[0] < cap_y], grow=0.015)
    ctr_y = 0.17
    shoe_piece(upper, s, [st for st in SHOE if st[0] > ctr_y] + [(ctr_y, *shoe_at(ctr_y))], grow=0.012)
    for y in (-0.33, -0.16):
        cx, w, h = shoe_at(y)
        tube(sole, [Vector((s * (cx + shoe_sec(w + 0.003, h + 0.003, k)[0]), y, shoe_sec(w + 0.003, h + 0.003, k)[1]))
                    for k in range(2, NS - 1)], [0.006] * (NS - 3), seg=4)
    slab(sole, s, [(0.50, 0.34, 0.08)] + PLAN + [(-1.005, 0.45, 0.04)], OUTSOLE, WELT)
    fore = [(-0.10, *shoe_at(-0.10)[:2])] + [p for p in PLAN if p[0] < -0.10] + [(-1.0, 0.45, 0.04)]
    slab(sole, s, fore, 0.012, OUTSOLE, 0.03)
    heel = [(0.495, 0.34, 0.08)] + [p for p in PLAN if p[0] > 0.10] + [(0.10, *shoe_at(0.10)[:2])]
    slab(sole, s, heel, 0.012, OUTSOLE, 0.02)
    for y in (-0.86, -0.74, -0.62, -0.50, -0.38, -0.26):
        cx, w, h = shoe_at(y)
        rbox(sole, Matrix.Translation((s * cx, y, 0.008)), (2 * w - 0.06, 0.07, 0.016), 0.0)
new_obj("CR_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("CR_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.11


# ---------------------------------------------------------------- head: an egg, with a jaw block bolted on the front
# HEAD is the outer surface. Pieces: the head shell in two halves on a hairline seam (front and back) over a closed
# inner shell; the blue mouth cassette, a block standing proud of the face; the ribbed moustache on it; a big nose;
# one eye and an eyepatch on its strap; the bandana shell with its spots; a hoop on a lug at each ear.
HEAD = [fb(6.50, 0.72, -0.55, 0.85), fb(6.70, 0.79, -0.58, 0.90), fb(7.00, 0.82, -0.58, 0.90),
        fb(7.30, 0.76, -0.55, 0.85), fb(7.60, 0.66, -0.50, 0.78), fb(7.85, 0.58, -0.45, 0.68),
        fb(8.05, 0.42, -0.30, 0.50), fb(8.16, 0.22, -0.12, 0.30)]
HEAD_N = 2.3
SHAPE[id(HEAD)] = HEAD_N
GAP = 0.003
CORE_IN = 0.025


def hp(th, z, eps=0.0):
    return ring_pt(HEAD, z, 270 + th, eps)[0]


def th_of(x, z):
    return math.degrees(math.asin(min(1.0, (min(0.999, abs(x) / interp(HEAD, z)[3])) ** (HEAD_N / 2.0)))) * (1 if x >= 0 else -1)


plates = bmesh.new()
HZ = [6.50, 6.60, 6.70, 6.85, 7.00, 7.15, 7.30, 7.45, 7.60, 7.72, 7.85, 7.95, 8.05, 8.11, 8.16]
for s in (1, -1):
    rows = []
    for z in HZ:
        g = abs(th_of(GAP, z))
        rows.append([hp(s * a, z) for a in [g] + [6.0 * i for i in range(1, 30)] + [180 - g]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("CR_HeadPlates", plates, M_PLATE, 62, outward=True, thickness=-0.04)
core = bmesh.new()
loft(core, [(z, cx, cy, rx - CORE_IN, ry - CORE_IN) for z, cx, cy, rx, ry in HEAD], seg=36, power=HEAD_N)
tag(core, 'joint_head')
new_obj("CR_HeadCore", core, M_JOINT, 60)
loft(plate, [fb(6.40, 0.50, -0.38, 0.60), fb(6.42, 0.64, -0.48, 0.76), fb(6.5005, 0.7205, -0.5505, 0.8505)], seg=32, caps=(True, False), power=HEAD_N)
lathe(steel, (0, 0.12, 6.16), (0, 0, 1), [(0.0, 0.50), (0.08, 0.58), (0.13, 0.58), (0.15, 0.50), (0.17, 0.61), (0.23, 0.61),
                                           (0.25, 0.52), (0.27, 0.62), (0.33, 0.62), (0.35, 0.54), (0.42, 0.54)], seg=28)

# mouth cassette: a blue block proud of the face, narrow at the top and flaring to the jaw
CAS_Z0, CAS_Z1 = 6.52, 7.40


def cas_hw(z):
    return 0.50 + 0.24 * (CAS_Z1 - z) / (CAS_Z1 - CAS_Z0)


def cas_pt(x, z, extra=0.0):
    u = max(-1.0, min(1.0, x / cas_hw(z)))
    v = (z - CAS_Z0) / (CAS_Z1 - CAS_Z0)
    lift = 0.30 * (1 - abs(u) ** 6) * (1 - max(0.0, 2 * v - 1) ** 6)
    return surf(HEAD, x * 0.9, z, 0.012 + lift + extra)


cas = bmesh.new()
grid(cas, [[cas_pt(cas_hw(z) * (i / 14 - 1), z) for i in range(29)] for z in [CAS_Z0 + (CAS_Z1 - CAS_Z0) * j / 14 for j in range(15)]])
tag(cas, 'joint_head')
new_obj("CR_MouthCassette", cas, M_BLUE, 50, outward=True, thickness=-0.03)
for x, z in ((0.3, 7.32), (-0.3, 7.32), (0.62, 6.62), (-0.62, 6.62), (0.2, 6.6), (-0.2, 6.6)):
    p = cas_pt(x, z, 0.0)
    puck(plate, p, (cas_pt(x, z, 1.0) - p).normalized(), 0.022, 0.02, seg=6)

# moustache: thick ribbed handlebar, modelled on the front of the cassette
UP = ((0.0, 7.17), (0.10, 7.25), (0.25, 7.28), (0.40, 7.20), (0.50, 7.00), (0.53, 6.78))
LO = ((0.0, 7.02), (0.10, 6.99), (0.25, 6.93), (0.38, 6.82), (0.47, 6.74), (0.53, 6.745))


def pl(pts, x):
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


stache = bmesh.new()
for s in (1, -1):
    rows = []
    for f in (0.0, 0.15, 0.35, 0.5, 0.65, 0.85, 1.0):
        row = []
        for i in range(33):
            x = 0.53 * i / 32
            zu, zl = pl(UP, x), pl(LO, x)
            rib = 0.012 * math.cos(x * 75.0)
            row.append(cas_pt(s * max(x, 0.004), zl + (zu - zl) * f, 0.008 + (0.07 + rib) * math.sin(math.pi * f) ** 0.7))
        rows.append(row)
    grid(stache, rows)
tag(stache, 'joint_head')
new_obj("CR_Moustache", stache, M_STACHE, 50, outward=True, thickness=-0.02)

# nose: a big wedge standing well out from the face
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (7.86, 7.76, 7.66, 7.57, 7.50, 7.455, 7.43)
ND = (0.0, 0.05, 0.10, 0.15, 0.18, 0.16, 0.10)
NR = (0.05, 0.065, 0.085, 0.105, 0.12, 0.105, 0.05)
tube(nose, [Vector((0, ny(z) - d + r * 0.3, z)) for z, d, r in zip(NZ, ND, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.12, ny(7.49) - 0.08, 7.49)) @ Matrix.Diagonal((0.065, 0.08, 0.055, 1.0)))
tag(nose, 'joint_head')
new_obj("CR_Nose", nose, M_PLATE, 60)

# his left eye: a ball in a socket rim under a heavy lid; his right eye: a patch on a strap
eyes, iris, dark, brown = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
# The eye: a ball set deep in the head so only a low dome shows, a big dark iris looking a little inward, and a
# heavy upper lid: a domed plate over the top of the ball, cut straight along its lower edge, with a dark lash line.
ep0 = surf(HEAD, 0.25, 7.72, 0.0)
en = (surf(HEAD, 0.25, 7.72, 1.0) - ep0).normalized()
er = en.cross(Vector((0, 0, 1))).normalized()
if er.x < 0:
    er = -er
eu = er.cross(en).normalized()
if eu.z < 0:
    eu = -eu
EM = Matrix((er, eu, en)).transposed().to_4x4()
bc = ep0 - en * 0.088
bmesh.ops.create_uvsphere(eyes, u_segments=20, v_segments=12, radius=0.125, matrix=Matrix.Translation(bc))
ic = bc + (en * 0.985 - er * 0.12 - eu * 0.13).normalized() * 0.1245
puck(brown, ic, (ic - bc).normalized(), 0.062, 0.006, seg=20)
puck(iris, ic + (ic - bc).normalized() * 0.004, (ic - bc).normalized(), 0.034, 0.006, seg=16)
LID_Y = 0.004
t = bmesh.new()
bmesh.ops.create_uvsphere(t, u_segments=24, v_segments=12, radius=1.0,
                          matrix=Matrix.Translation(ep0 + en * 0.002) @ EM @ Matrix.Diagonal((0.125, 0.105, 0.052, 1.0)))
bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=ep0 + eu * LID_Y, plane_no=eu, clear_inner=True)
bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=ep0, plane_no=en, clear_inner=True)
merge(plate, t)
lash = [ep0 + er * (0.118 * math.cos(math.radians(a))) + eu * (LID_Y - 0.002) + en * (0.004 + 0.05 * math.sin(math.radians(a)) ** 0.8)
        for a in range(0, 181, 12)]
tube(dark, lash, [0.006 + 0.006 * math.sin(math.radians(a)) for a in range(0, 181, 12)], seg=6)
bag = [ep0 + er * (0.105 * math.cos(math.radians(a))) + eu * (0.085 * math.sin(math.radians(a))) + en * 0.0 for a in range(195, 346, 15)]
tube(plate, bag, [0.006 + 0.008 * math.sin(math.radians((a - 195) * 180 / 150)) for a in range(195, 346, 15)], seg=6)
pp_ = surf(HEAD, -0.21, 7.72, 0.0)
pn = (surf(HEAD, -0.21, 7.72, 1.0) - pp_).normalized()
m = Matrix.Translation(pp_ + pn * 0.012) @ pn.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Diagonal((0.155, 0.125, 0.03, 1.0))
bmesh.ops.create_uvsphere(dark, u_segments=18, v_segments=8, radius=1.0, matrix=m)
strap = [hp(th, z, 0.014) for th, z in ((62, 7.93), (30, 7.86), (0, 7.80), (-th_of(0.21, 7.72), 7.72), (-48, 7.58), (-75, 7.45), (-100, 7.34))]
tube(dark, strap, [0.016] * len(strap), seg=5)
for _b in (eyes, iris, dark):
    tag(_b, 'joint_head')
new_obj("CR_Eye", eyes, M_EYE, 60)
new_obj("CR_Iris", iris, M_IRIS, 40)
tag(brown, 'joint_head')
new_obj("CR_IrisRing", brown, M_IRISRING, 40)
new_obj("CR_Patch", dark, M_PATCH, 50)

# bandana: a rigid red shell over the crown, low at the back, with raised cream spots
def band_edge(th):
    return 7.90 - 0.80 * (math.sin(math.radians(th / 2)) ** 2) ** 1.3 + (0.05 if th > 0 else 0.0) * math.sin(math.radians(min(abs(th), 180)))


bandana, spots = bmesh.new(), bmesh.new()
BT = [-180 + 6.0 * i for i in range(61)]
rows = []
for f in (0.0, 0.2, 0.4, 0.6, 0.8, 0.93, 1.0):
    rows.append([hp(th, band_edge(th) + (8.16 - band_edge(th)) * f, 0.045 + 0.02 * math.sin(math.pi * f)) for th in BT])
grid(bandana, rows)
bmesh.ops.remove_doubles(bandana, verts=bandana.verts, dist=0.0005)
_z, _cx, _cy, _rx, _ry = HEAD[-1]
loft(bandana, [(8.16, _cx, _cy, _rx + 0.045, _ry + 0.045), (8.195, _cx, _cy, _rx * 0.6, _ry * 0.6), (8.205, _cx, _cy, 0.12, 0.12)],
     seg=60, power=HEAD_N, caps=(False, True))
tag(bandana, 'joint_head')
new_obj("CR_Bandana", bandana, M_BANDANA, 50, outward=True, thickness=-0.03)
def band_pt(th, z):
    f = (z - band_edge(th)) / (8.16 - band_edge(th))
    return hp(th, z, 0.045 + 0.02 * math.sin(math.pi * max(0.0, min(1.0, f))))


for th, z, r in ((-40, 7.98, 0.07), (25, 8.0, 0.075), (70, 7.86, 0.07), (-85, 7.80, 0.075), (110, 7.98, 0.07), (-125, 7.95, 0.075),
                 (150, 7.72, 0.07), (-160, 7.62, 0.075), (180, 7.95, 0.07), (125, 7.52, 0.065), (-130, 7.45, 0.065), (-5, 8.03, 0.06),
                 (-170, 7.25, 0.06), (165, 7.32, 0.06), (60, 8.03, 0.06), (-75, 8.02, 0.06)):
    p = band_pt(th, z)
    n = (band_pt(th + 2, z) - band_pt(th - 2, z)).cross(band_pt(th, z + 0.02) - band_pt(th, z - 0.02)).normalized()
    if n.dot(p - Vector((0, 0.15, 7.3))) < 0:
        n = -n
    puck(spots, p + n * 0.002, n, r, 0.012, seg=12)
tag(spots, 'joint_head')
new_obj("CR_BandanaSpots", spots, M_SPOT, 40)

# ear lugs and gold hoops
gold = bmesh.new()
for a in (2, 178):
    p, n = ring_pt(HEAD, 7.14, a, 0.0)
    lathe(steel, p - n * 0.01, n, [(0.0, 0.085), (0.035, 0.085), (0.05, 0.07), (0.05, 0.05), (0.03, 0.046)], seg=18)
    lathe(gold, p, n, [(0.03, 0.04), (0.06, 0.04), (0.07, 0.03), (0.072, 0.002)], seg=12)
    c = p + n * 0.05 + Vector((0, -0.04, -0.22))
    ring = [c + 0.19 * (Vector((0, 1, 0)) * math.cos(math.radians(t)) + Vector((0, 0, 1)) * math.sin(math.radians(t))) for t in range(0, 361, 15)]
    tube(gold, ring, [0.032] * len(ring), seg=8, caps=False)
tag(gold, 'joint_head')
new_obj("CR_Gold", gold, M_GOLD, 50)
for th, z in ((8, 7.60), (-8, 7.60), (60, 7.30), (-60, 7.30), (100, 6.80), (-100, 6.80), (172, 6.80), (-172, 6.80), (172, 7.0), (-172, 7.0)):
    p, n = ring_pt(HEAD, z, 270 + th, 0.0)
    puck(plate, p, n, 0.02, 0.02, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.011

loft(shirt, [fb(6.30, 0.85, -0.72, 0.86), fb(6.58, 0.78, -0.68, 0.80), fb(6.58, 0.74, -0.64, 0.76), fb(6.33, 0.77, -0.66, 0.79)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.05, s * 0.55, 6.50), (s * 0.16, s * 0.60, 6.32), (s * 0.36, s * 0.52, 6.12)], 0.03, nx=4)
patch(tie, SS, [(-0.14, 0.14, 6.45), (-0.19, 0.19, 6.32), (-0.12, 0.12, 6.10)], 0.06, nx=4)
patch(tie, SS, [(-0.11, 0.11, 6.12), (-0.18, 0.18, 5.80), (-0.19, 0.19, 5.62)], 0.02, nx=4)

panel(placket, TS, [(-0.12, 3.07), (0.40, 3.07), (0.40, 5.10), (0.18, 5.50), (-0.12, 5.50)], lambda x, z: 0.008, cuts=2)
for z in (4.68, 4.28, 3.88, 3.40):
    p = surf(TS, 0.12, z, 0.03)
    nrm = (surf(TS, 0.12, z, 1.0) - surf(TS, 0.12, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.10), (0.022, 0.10), (0.045, 0.078), (0.045, 0.058), (0.028, 0.053)], seg=14)
    lathe(pewter, p, nrm, [(0.022, 0.053), (0.053, 0.038), (0.064, 0.01)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.115), (0.013, 0.115)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
for xe in (0.36, -0.08):
    edge = [(xe, 5.05 - (5.05 - 3.18) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.044) for x, z in edge], [SR] * len(edge), seg=4)
hem = [ring_pt(TS, 3.18, a, 0.012)[0] for a in range(-76, 257, 6)]
tube(stitch, hem, [SR] * len(hem), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)


def roll_lift(x, z):
    return 0.02 + 0.05 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.25)


def flat_lift(x, z):
    return 0.012


g = front_gap
for s in (-1, 1):
    lapel = [(0.012, 5.56), (1.00, 5.92), (1.12, 6.05), (0.85, 6.15), (g(6.18), 6.18), (g(5.95), 5.95), (g(5.75), 5.75)]
    collar_front = [(g(6.18), 6.18), (0.85, 6.15), (1.20, 6.16), (1.25, 6.27), (0.95, 6.42), (g(6.42), 6.42)]
    flap = [(1.05, 3.98), (1.72, 3.98), (1.72, 3.50), (1.68, 3.45), (1.09, 3.45), (1.05, 3.50)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.055, inset=0.04, step=0.1, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.048, inset=0.036, step=0.1, radius=SR)
breast = [(0.72, 5.22), (1.42, 5.22), (1.42, 4.62), (1.07, 4.45), (0.72, 4.62)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.048, inset=0.036, step=0.1, radius=SR)
panel(pockets, TS, [(0.72, 5.22), (1.42, 5.22), (1.42, 5.11), (0.72, 5.11)], lambda x, z: 0.028, cuts=1)
pocket_sq = [surf(TS, x, z, 0.052) for x, z in ((0.78, 5.21), (1.36, 5.21), (1.35, 5.33), (1.27, 5.29), (1.20, 5.44),
                                               (1.12, 5.30), (1.03, 5.45), (0.95, 5.30), (0.85, 5.37))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')


# Shoulder straps: a band over each shoulder, from the chest up over the ridge and down the back, a stud at each end.
def ts_hw(z):
    return interp(TS, z)[3]


XF, ZF, XB, ZB, XT, ZT = 1.62, 5.90, 1.55, 5.65, 1.25, 6.28


def strap_edge(dx, lift=0.03, n=7, m=9):
    lo, hi = ZF, 6.5
    for _ in range(40):
        mid = (lo + hi) / 2
        if XF + dx + (XT - XF) * (mid - ZF) / (ZT - ZF) < 0.975 * ts_hw(mid):
            lo = mid
        else:
            hi = mid
    zt = lo
    xt = 0.975 * ts_hw(zt)
    pts = []
    for i in range(n):
        f = i / (n - 1)
        pts.append(surf(TS, XF + dx + (xt - XF - dx) * f, ZF + (zt - ZF) * f, lift))
    for i in range(1, m):
        f = i / (m - 1)
        pts.append(surf(TS, xt + (XB + dx - xt) * f, zt + (ZB - zt) * f, lift, back=True))
    return pts


for s in (-1, 1):
    grid(straps, [mirror(strap_edge(dx), s) for dx in (-0.15, 0.0, 0.15)])
    c0, c1 = strap_edge(0.0, 0.06), strap_edge(0.0, 1.06)
    for i in (1, -2):
        nrm = (c1[i] - c0[i]).normalized()
        lathe(pewter, Vector((s * c0[i].x, c0[i].y, c0[i].z)), Vector((s * nrm.x, nrm.y, nrm.z)),
              [(0.0, 0.046), (0.02, 0.046), (0.035, 0.022), (0.04, 0.002)], seg=10)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion on a cord
MZ = 5.20
slope = (surf(TS, 0, MZ + 0.2).y - surf(TS, 0, MZ - 0.2).y) / 0.4
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.075
medal_p, medal_j = bmesh.new(), bmesh.new()
lathe(medal_p, mc, mn, [(0.0, 0.34), (0.075, 0.34), (0.10, 0.316), (0.103, 0.272), (0.07, 0.265)], seg=28)
lathe(medal_p, mc, mn, [(0.068, 0.265), (0.083, 0.15), (0.088, 0.0)], seg=28, caps=False)
bail = mc + mt * 0.40 + mn * 0.055
lathe(medal_p, mc + mt * 0.325 + mn * 0.05, mt, [(0.0, 0.056), (0.05, 0.066), (0.10, 0.046)], seg=10)
lathe(medal_p, bail - Vector((0.056, 0, 0)), (1, 0, 0), [(0.0, 0.05), (0.112, 0.05)], seg=10)
for pts in (((-0.11, 0.19), (0.11, -0.19)), ((0.11, 0.19), (-0.11, -0.19)), ((-0.11, 0.19), (0.11, 0.19)), ((-0.11, -0.19), (0.11, -0.19))):
    loop = [mc + mn * 0.094 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    tube(medal_j, loop, [0.012, 0.012], seg=4)
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.45, 6.33, 0.04), surf(TS, s * (g(6.05) + 0.03), 6.05, 0.09), surf(TS, s * (g(5.8) + 0.025), 5.8, 0.09),
           surf(TS, s * 0.05, 5.64, 0.095), bail + Vector((s * 0.03, 0, 0))]
    tube(cord, pts, [0.02] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("CR_Shirt", shirt, M_SHIRT, 30)
new_obj("CR_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.026)
new_obj("CR_Stitching", stitch, M_STITCH, 40)
new_obj("CR_Tie", tie, M_TIE, 30, outward=True, thickness=0.036)
new_obj("CR_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.03)
new_obj("CR_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.05)
new_obj("CR_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.03)
new_obj("CR_Straps", straps, M_SUIT, 40, outward='up', thickness=0.03)
new_obj("CR_Medallion", medal_p, M_PEWTER, 32)
new_obj("CR_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("CR_Cord", cord, M_JOINT, 40)
new_obj("CR_Plates", plate, M_PLATE, 32)
new_obj("CR_Joints", joint, M_JOINT, 40)
new_obj("CR_Steel", steel, M_STEEL, 40)
new_obj("CR_Buttons", pewter, M_PEWTER, 32)

cam = bpy.data.objects.new("CRCam", bpy.data.cameras.new("CRCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("CRSun", bpy.data.lights.new("CRSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("CRFill", bpy.data.lights.new("CRFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 280
fill.data.size = 10
fill.location = (-10, -11, 6)
fill.rotation_euler = (Vector((0, 0, 3.8)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
