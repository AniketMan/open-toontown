"""Build the HD Micromanager (Bossbot) in Blender.
Torso and head are measured off the turnaround sheet (447 px = 3.25 game units) and modelled standing, in game
units. Arms, hands, legs and shoes are built straight in suit C's rest pose at native size (game / 0.604).
Z up, character faces -Y, +x is his left, feet at z = 0."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/04_Micromanager_Bossbot/"
H = math.pi / 2
YOFF = 0.0
STRIPE = 0.05
K = 2.5 / 4.14          # suit C scale for this cog
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'


def get_col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


col = get_col("Micromanager")
refcol = get_col("Micromanager_Reference")
root = bpy.data.objects.new("Micromanager", None)
col.objects.link(root)
root.empty_display_size = 0.3
exec(compile(open(SP + "hd_lib.py").read(), SP + "hd_lib.py", "exec"), globals())


def ref(name, loc, rot):
    img = bpy.data.images.load(SP + "refplanes/mm_ref_%s.png" % name, check_existing=True)
    if not img.packed_file:
        img.pack()
    e = bpy.data.objects.new("Ref_" + name, None)
    refcol.objects.link(e)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 3.4
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
M_SUIT = pmat("MM_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.47, 0.25, 0.19), weave=0.5, bump=0.25,
              bscale=190, sheen=0.04, rvar=0.06, nscale=9.0)
M_LINING = pmat("MM_Lining", (0.05, 0.012, 0.01), 0.8, var=0.3)
M_STITCH = pmat("MM_Stitch", (0.66, 0.46, 0.38), 0.85, var=0.2)
M_PLATE = pmat("MM_Plate", (0.80, 0.66, 0.55), 0.42, 0.1, var=0.22, grime=0.45, wear=0.08, bump=0.1,
               bscale=70, rvar=0.14, nscale=9.0)
M_JOINT = pmat("MM_Joint", (0.10, 0.075, 0.06), 0.42, 0.85, var=0.4, grime=0.4, bump=0.15, bscale=90, rvar=0.18)
M_STEEL = pmat("MM_Steel", (0.33, 0.29, 0.26), 0.3, 0.9, var=0.3, grime=0.45, bump=0.08, bscale=100, rvar=0.14)
M_HAIR = pmat("MM_Hair", (0.115, 0.042, 0.028), 0.42, 0.25, var=0.35, grime=0.3, wear=0.12, bump=0.2, bscale=150, rvar=0.14,
              nscale=12.0, coat=0.15)
M_BROW = pmat("MM_Brow", (0.02, 0.012, 0.01), 0.35, 0.2, var=0.3, bump=0.15, bscale=160, rvar=0.1)
M_LIP = pmat("MM_Lip", (0.27, 0.022, 0.022), 0.22, var=0.3, grime=0.15, bump=0.06, bscale=120, rvar=0.08, coat=0.6)
M_MOUTH = pmat("MM_Mouth", (0.16, 0.016, 0.016), 0.45, var=0.35, grime=0.5, grime_col=(0.02, 0.002, 0.002), bump=0.05, bscale=90)
M_EYE = pmat("MM_Eye", (0.72, 0.70, 0.64), 0.2, var=0.1, grime=0.3, coat=0.5)
M_IRIS = pmat("MM_Iris", (0.025, 0.02, 0.018), 0.15, var=0.2, coat=0.8)
M_SHOE = pmat("MM_Shoe", (0.03, 0.014, 0.01), 0.3, var=0.4, grime=0.25, bump=0.3, bscale=110, rvar=0.14, coat=0.5, wear=0.12)
M_SOLE = pmat("MM_Sole", (0.03, 0.026, 0.023), 0.75, var=0.3, grime=0.3, bump=0.3, bscale=70)
M_PEWTER = pmat("MM_Pewter", (0.56, 0.44, 0.33), 0.34, 0.9, var=0.3, grime=0.5, bump=0.1, bscale=130, rvar=0.15)
M_SHIRT = pmat("MM_Shirt", (0.82, 0.75, 0.66), 0.75, var=0.12, grime=0.2, weave=0.25, sheen=0.2, rvar=0.05)
M_TIE = pmat("MM_Tie", (0.17, 0.02, 0.018), 0.55, var=0.25, grime=0.15, weave=0.6, sheen=0.08, rvar=0.1)

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
# A round barrel: half-widths from the front view (the hem and shoulders show; the middle is hidden behind the
# arms and comes from the top view), front and back from the side view.
TORSO = [fb(1.05, 0.70, -0.84, 0.61), fb(1.12, 0.745, -0.89, 0.64), fb(1.30, 0.79, -0.92, 0.66),
         fb(1.50, 0.81, -0.91, 0.67), fb(1.70, 0.81, -0.86, 0.65), fb(1.88, 0.80, -0.76, 0.61),
         fb(2.02, 0.79, -0.64, 0.56), fb(2.13, 0.76, -0.53, 0.51), fb(2.21, 0.70, -0.44, 0.46),
         fb(2.27, 0.57, -0.37, 0.42), fb(2.31, 0.52, -0.32, 0.385), fb(2.34, 0.42, -0.29, 0.36),
         fb(2.365, 0.35, -0.27, 0.34)]
TS = TORSO
BREAK = 1.995


def front_gap(z):
    """Half-width of the jacket opening: buttoned below the break, a V showing shirt and tie above it."""
    return 0.003 if z <= BREAK else 0.003 + 0.19 * min(1.0, (z - BREAK) / (2.33 - BREAK)) ** 1.1


SHIRT_IN = {2.02: 0.075, 2.13: 0.06, 2.21: 0.05, 2.27: 0.045, 2.31: 0.045}
SS = [(z, cx, cy, rx - SHIRT_IN[z], ry - SHIRT_IN[z]) for z, cx, cy, rx, ry in TS if z in SHIRT_IN]
SS += [fb(2.34, 0.37, -0.26, 0.31), fb(2.37, 0.31, -0.24, 0.29)]
bm = bmesh.new()
loft(bm, SS + [fb(2.375, 0.15, -0.12, 0.15)], seg=28)
new_obj("MM_ShirtBody", bm, M_SHIRT)

bm = bmesh.new()
shell(bm, TS, front_gap, parts=(9, 24, 9))
for v in bm.verts:
    if v.co.z > 2.35 and v.co.y < 0:
        v.co.z -= 0.035 * min(1.0, -v.co.y / 0.2)
new_obj("MM_Jacket", bm, M_SUIT, 60, outward=True, thickness=-0.026)

bm = bmesh.new()
_, _, hem_cy, hem_rx, hem_ry = TS[0]
loft(bm, [(1.049, 0, hem_cy, hem_rx - 0.006, hem_ry - 0.006), (1.075, 0, -0.10, 0.60, 0.58)], seg=28, caps=(False, False))
new_obj("MM_HemLining", bm, M_LINING)

bm = bmesh.new()
COLLAR = [fb(2.345, 0.36, -0.28, 0.355), fb(2.405, 0.37, -0.29, 0.385), fb(2.39, 0.44, -0.33, 0.435), fb(2.285, 0.565, -0.385, 0.45)]
arc_band(bm, COLLAR, -28, 208, 24, zfun=lambda si, sn: (0.015 if si in (1, 2) else 0.0) * max(0.0, sn) ** 0.6)
new_obj("MM_Collar", bm, M_SUIT, outward=False, thickness=0.018)
COLLAR_EDGE = []
for i in range(25):
    t = math.radians(-28 + 236 * i / 24)
    _, cx, cy, rx, ry = COLLAR[3]
    COLLAR_EDGE.append(Vector((cx + rx * 0.955 * math.cos(t), cy + ry * 0.955 * math.sin(t), 2.312)))

# ---------------------------------------------------------------- limbs: built straight, in the skeleton's rest pose
# Native units. Suit C (checked against the game's walk and neutral frames for the Flunky): jnt23_1 / jnt24_1 stay
# on the shoulders, Luparm / Ruparm carry the upper arms, jnt26_2 / jnt27_2 the forearms, jnt14_1 / jnt13_1 the
# thighs, jnt14_2 / jnt13_2 the shins, to_legL / to_legR the feet and to_MAIN the pelvis.
RIG = json.load(open(SP + "mm_rig.json"))
JR = {j["name"]: Vector(j["head"]) for j in RIG["bind"]}
MIRROR = Matrix.Scale(-1, 4, (1, 0, 0))
STRIPE = 0.05 / K
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
new_obj("MM_Sleeves", both_arms(sleeve_cloth), M_SUIT, 60, rest=True)
new_obj("MM_SleeveButtons", pewter_r, M_PEWTER, 32, rest=True)
new_obj("MM_SleeveStitching", stitch_r, M_STITCH, 40, rest=True)

# ---- forearm cuff, wrist joint and hand, flat in the rest pose: fingers straight out along x, index at the front
plate_r, joint_r = bmesh.new(), bmesh.new()
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
    lathe(plate_r, c0, ax, [(0.0, 0.243), (0.02, 0.271), (0.30, 0.281), (0.316, 0.298), (0.347, 0.298), (0.357, 0.233)], seg=20)
    lathe(joint_r, c0, ax, [(0.347, 0.207), (0.362, 0.233), (0.381, 0.202), (0.40, 0.233), (0.418, 0.202), (0.43, 0.226)], seg=16)
    for n in (Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((0, 1, 0))):   # ringed boss: outer, front and back faces once the arm hangs
        n = R3 @ n
        puck(plate_r, c0 + ax * 0.20 + n * 0.277, n, 0.062, 0.016, seg=12)
        puck(joint_r, c0 + ax * 0.20 + n * 0.281, n, 0.043, 0.016, seg=10)
        puck(plate_r, c0 + ax * 0.20 + n * 0.285, n, 0.023, 0.016, seg=8)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.165, PLATE_Y, AZ + 0.035)), (0.33, 0.68, 0.205), 0.07, 3)
    rbox(plate_r, T @ Matrix.Translation((WX + 0.18, PLATE_Y, AZ - 0.088)), (0.27, 0.58, 0.10), 0.03, 1)
    rbox(joint_r, T @ Matrix.Translation((WX + 0.175, PLATE_Y, AZ - 0.02)), (0.29, 0.62, 0.125), 0.0)
    for k in range(7):
        puck(plate_r, T @ Vector((WX + 0.055, PLATE_Y - 0.28 + 0.093 * k, AZ + 0.138)), R3 @ Vector((0, 0, 1)), 0.0135, 0.012, seg=6)
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
new_obj("MM_HandPlates", plate_r, M_PLATE, 32, rest=True)
new_obj("MM_HandJoints", joint_r, M_JOINT, 40, rest=True)

# ---- trousers: one sealed garment. Seat bowl on the pelvis (to_MAIN, z 2.21) running up inside the jacket (hem at
# z 1.74 here); legs straight down round hip (z 1.96) -> knee (1.10) -> ankle (0.14). Wide legs: each sits outside
# its bone (x 0.31) so the two meet down the middle without overlapping.
seat = bmesh.new()
loft(seat, [(1.30, 0, -0.12, 0.08, 0.08), (1.33, 0, -0.12, 0.40, 0.38), (1.40, 0, -0.12, 0.70, 0.64), (1.50, 0, -0.13, 0.90, 0.80),
            (1.62, 0, -0.13, 1.01, 0.88), (1.78, 0, -0.13, 1.04, 0.92), (1.95, 0, -0.13, 1.03, 0.92), (2.10, 0, -0.12, 0.96, 0.90),
            (2.25, 0, -0.10, 0.80, 0.75)], seg=24, centres=(270, 90))
new_obj("MM_Seat", seat, M_SUIT, 60, rest=True)
bm = bmesh.new()
LEG = [(0.42, 0.385, -0.08, 0.37, 0.50), (0.56, 0.385, -0.08, 0.375, 0.51), (0.85, 0.40, -0.08, 0.39, 0.56),
       (1.10, 0.43, -0.09, 0.42, 0.66), (1.35, 0.47, -0.11, 0.46, 0.77), (1.55, 0.50, -0.12, 0.49, 0.84),
       (1.80, 0.52, -0.13, 0.51, 0.88)]
for s in (-1, 1):
    loft(bm, LEG, seg=20, sx=s, centres=(270, 90))
    tag(bm, '@legL' if s > 0 else '@legR')
new_obj("MM_Trousers", bm, M_SUIT, 60, rest=True)

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
new_obj("MM_Shoes", upper, M_SHOE, 55, rest=True)
new_obj("MM_Soles", sole, M_SOLE, 30, rest=True)
STRIPE = 0.05

# ---------------------------------------------------------------- head
# The face is a prow: two flat cheek planes meeting on a rounded centre ridge (the sheet's top view shows the V,
# and the side view puts the eye corners and mouth corners well behind the nose). Sides and back are a box, under
# the hair shell. A section is given by half-width, front (nose ridge), back and the slope of the cheek planes.
HSEC = [(2.30, 0.20, 0.24, 0.20, 0.70), (2.3358, 0.29, 0.35, 0.28, 0.75), (2.37, 0.335, 0.405, 0.31, 0.80),
        (2.42, 0.355, 0.43, 0.34, 0.85), (2.50, 0.36, 0.44, 0.36, 0.95), (2.60, 0.36, 0.44, 0.37, 1.0),
        (2.75, 0.355, 0.435, 0.37, 1.0), (2.90, 0.35, 0.42, 0.37, 1.0), (3.00, 0.34, 0.40, 0.36, 1.0),
        (3.10, 0.32, 0.36, 0.34, 1.0), (3.15, 0.28, 0.31, 0.30, 1.0), (3.18, 0.16, 0.18, 0.17, 1.0),
        (3.187, 0.01, 0.012, 0.01, 1.0)]
HAIRSEC = [(2.51, 0.47, 0.49, 0.43, 1.0), (2.93, 0.43, 0.47, 0.41, 1.0), (3.20, 0.345, 0.385, 0.32, 1.0)]
HN, HAIRN = 8, 14
GAP = 0.0012
CORE_IN = 0.008
FA = 100.0                       # the front plates run this far round each side from centre front
FACE_TOP = 3.15
BASE_Z = 2.3358


def gsec(table, z):
    for a, b in zip(table, table[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * t for i in range(1, 5)]
    return list(table[-1][1:]) if z > table[-1][0] else list(table[0][1:])


def gauge_pt(table, n, phi, z, eps=0.0):
    """Point on a head section, phi degrees round from centre front (+ = his left), and its outward normal."""
    hw, F, back, s = gsec(table, z)
    Fw = F * 2 ** (1.0 / n)

    def terms(x, y):
        return ((x / hw, 1 / hw, 0.0), (-x / hw, -1 / hw, 0.0), (y / back, 0.0, 1 / back),
                ((-y + s * x) / Fw, s / Fw, -1 / Fw), ((-y - s * x) / Fw, -s / Fw, -1 / Fw))

    a = math.radians(phi)
    dx, dy = math.sin(a), -math.cos(a)
    g = sum(max(0.0, t) ** n for t, _, _ in terms(dx, dy)) ** (1.0 / n)
    x, y = dx / g, dy / g
    gx = sum(max(0.0, t) ** (n - 1) * u for t, u, _ in terms(x, y))
    gy = sum(max(0.0, t) ** (n - 1) * v for t, _, v in terms(x, y))
    nrm = Vector((gx, gy, 0.0)).normalized()
    return Vector((x, y, z)) + nrm * eps, nrm


def hp(phi, z, eps=0.0):
    return gauge_pt(HSEC, HN, phi, z, eps)[0]


def phi_of_x(table, n, x, z):
    lo, hi = 0.0, 89.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if gauge_pt(table, n, mid, z)[0].x < x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def hphi(x, z):
    return phi_of_x(HSEC, HN, x, z)


_XN = {}


def XN(phi):                     # how far out from the centre line a column sits (at mouth height)
    a = round(min(abs(phi), 100.0), 4)
    if a not in _XN:
        _XN[a] = hp(a, 2.6).x
    return _XN[a]


def agap(z, d=GAP):
    return math.degrees(d / 0.4)


XM, SIDE0 = 0.25, 2.505          # mouth corner: distance out, height
PHM = hphi(XM, 2.6)              # ... and how far round


def lip_top(X):                  # upper edge of the mouth opening (with the dip of the cupid's bow)
    t = min(1.0, X / XM)
    return SIDE0 + 0.163 * (1 - t ** 2.6) - 0.012 * math.exp(-(X / 0.022) ** 2)


def lip_bot(X):                  # lower edge of the mouth opening: nearly flat
    t = min(1.0, X / XM)
    return 2.497 + (SIDE0 - 2.497) * t * t


def side_z(phi):                 # seam from the mouth corner down to the jaw line and round under the hair
    t = min(1.0, max(0.0, (abs(phi) - PHM) / 25.0))
    return SIDE0 - 0.065 * t * t * (3 - 2 * t)


def in_mouth(phi):
    return abs(phi) < PHM - 1e-6


def mouth_top(phi):
    return lip_top(XN(phi)) if in_mouth(phi) else side_z(phi)


def mouth_bot(phi):
    return lip_bot(XN(phi)) if in_mouth(phi) else side_z(phi)


def crease(X):                   # the line from the wing of the nose out across the cheek
    return 2.742 if X < 0.07 else 2.742 - 0.062 * min(1.0, (X - 0.07) / 0.24) ** 0.9


def crease_gap(X):
    return GAP * min(1.0, max(0.0, (X - 0.07) / 0.02))


EC, EW = 0.1175, 0.0675          # eye: centre and half-width, as distance out from the centre line


def eye_z(X):
    return 2.822 + 0.006 * max(-1.0, min(1.0, (X - EC) / EW))


def eye_lo(X):
    t = (X - EC) / EW
    return 0.016 * math.sqrt(1 - t * t) if abs(t) < 1 else 0.0


def eye_hi(X):
    t = (X - EC) / EW
    return 0.011 * math.sqrt(1 - t * t) if abs(t) < 1 else 0.0


def muzzle(X):
    return 0.022 * max(0.0, 1 - (X / XM) ** 4)


def bulge(X, z):
    """Sculpted relief of the face: brow ridge, cheeks, the bags under the eyes, the muzzle round the upper lip."""
    brow = 0.012 * math.exp(-((X - 0.12) / 0.10) ** 2 - ((z - 2.895) / 0.03) ** 2)
    cheek = 0.010 * math.exp(-((X - 0.20) / 0.08) ** 2 - ((z - 2.72) / 0.06) ** 2)
    bag = 0.005 * math.exp(-((X - 0.12) / 0.06) ** 2 - ((z - 2.785) / 0.015) ** 2)
    lt = lip_top(X) if X < XM else SIDE0
    muz = muzzle(X) * math.exp(-(max(0.0, z - lt) / 0.05) ** 2)
    return brow + cheek + bag + muz


PHI = [1.25 * i for i in range(33)] + [42.5 + 2.5 * i for i in range(24)]        # 0 .. 60 fine, then to 100
BACK_PHI = [FA + 5.0 * i for i in range(17)]                                      # 100 .. 180
A_F, B_F, C_F = (0.0, 0.3, 0.65, 1.0), (0.0, 0.35, 0.7, 1.0), (0.0, 0.12, 0.3, 0.55, 0.8, 1.0)
CHIN_F = (0.0, 0.15, 0.3, 0.5, 0.7, 0.85, 1.0)


def face_zs(phi):
    X = XN(phi)
    bot = mouth_top(phi) + (0.0 if in_mouth(phi) else GAP)
    zc, gc = crease(X), crease_gap(X)
    ez, el, eh = eye_z(X), eye_lo(X), eye_hi(X)
    return ([bot + (zc - gc - bot) * f for f in A_F] + [zc + gc + (ez - el - zc - gc) * f for f in B_F] +
            [ez + eh + (FACE_TOP - ez - eh) * f for f in C_F])


def chin_zs(phi):
    top = mouth_bot(phi) - (0.0 if in_mouth(phi) else GAP)
    return [BASE_Z + (top - BASE_Z) * f for f in CHIN_F]


plates = bmesh.new()
# Each half of the face is one plate from the mouth up to the crown seam: the eye is a slot cut through it and the
# cheek crease a hairline slit running out from the wing of the nose. The halves meet on the centre ridge.
for s in (1, -1):
    t = bmesh.new()
    cols = []
    for ph in PHI:
        zs = face_zs(ph)
        cols.append([t.verts.new(hp(s * max(ph, agap(z)), z, bulge(XN(ph), z))) for z in zs])
    for a, b in zip(cols, cols[1:]):
        for k in range(13):
            if k in (3, 7):
                continue
            t.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    merge(plates, t, weld=0.0004)
    # jaw plate: under the mouth, wrapping up behind the mouth corner to the side seam
    grid(plates, [[hp(s * max(ph, agap(2.4)), chin_zs(ph)[k]) for ph in PHI] for k in range(len(CHIN_F))])
    # back plate (under the hair shell): its front edge uses the front plates' own heights
    BACK_Z = chin_zs(FA) + face_zs(FA)
    rows = []
    for z in BACK_Z:
        g = agap(z)
        rows.append([hp(s * a, z) for a in [BACK_PHI[0] + g] + BACK_PHI[1:-1] + [180 - g]])
    grid(plates, rows)
    # crown, closing the top of the head under the hair
    rows = []
    for z in (FACE_TOP + 2 * GAP, 3.165, 3.18, 3.187):
        rows.append([hp(s * a, z) for a in [agap(z)] + [a for a in PHI if a % 5 == 0 and a > 0] + BACK_PHI[1:-1] + [180 - agap(z)]])
    grid(plates, rows)
tag(plates, 'joint_head')
new_obj("MM_HeadPlates", plates, M_PLATE, 62, outward=True, thickness=-0.014)

# Inner shell: closed, just under the plates, for the whole head. Behind the mouth opening it is the mouth itself: a
# deep bowl (the cassette), built from the same points so there is no join to see.
MOUTH_F = (0.0, 0.04, 0.12, 0.25, 0.4, 0.5, 0.6, 0.75, 0.88, 0.96, 1.0)
CORE_CHIN_F, CORE_FACE_F = (0.0, 0.5, 1.0), (0.0, 0.25, 0.5, 0.75, 1.0)
MOUTH_DEPTH = 0.20


def core_col(phi):
    """Points up one column of the inner shell: jaw, mouth bowl, face. Returns (points, index of first mouth row)."""
    X = XN(phi)
    lo, hi = mouth_bot(phi), mouth_top(phi)
    out = [hp(phi, 2.30 + (lo - 2.30) * f, -CORE_IN) for f in CORE_CHIN_F[:-1]]
    k0 = len(out)
    for f in MOUTH_F:
        p = hp(phi, lo + (hi - lo) * f, -CORE_IN + bulge(X, hi) * f)
        if abs(phi) < PHM:
            p.y += MOUTH_DEPTH * math.sqrt(max(0.0, 1 - (X / XM) ** 4)) * math.sqrt(max(0.0, 1 - (2 * f - 1) ** 4))
        out.append(p)
    out += [hp(phi, hi + (3.18 - hi) * f, -CORE_IN) for f in CORE_FACE_F[1:]]
    return out, k0


core, bowl = bmesh.new(), bmesh.new()
CORE_PHI = [-a for a in reversed(BACK_PHI[:-1])] + [-a for a in reversed(PHI[1:])] + PHI + BACK_PHI[1:]
ccols = [core_col(a) for a in CORE_PHI]
k0 = ccols[0][1]
nrow = len(ccols[0][0])
cv = [[core.verts.new(p) for p in c] for c, _ in ccols]
bv = [[bowl.verts.new(p) for p in c] for c, _ in ccols]
for i in range(len(CORE_PHI)):
    j = (i + 1) % len(CORE_PHI)
    in_i, in_j = abs(CORE_PHI[i]) < PHM, abs(CORE_PHI[j]) < PHM
    for k in range(nrow - 1):
        is_mouth = k0 <= k < k0 + len(MOUTH_F) - 1
        if is_mouth and in_i and in_j:
            bowl.faces.new((bv[i][k], bv[j][k], bv[j][k + 1], bv[i][k + 1]))
        elif is_mouth and in_i:                                  # the corner: closes to a point on the outer column
            bowl.faces.new((bv[i][k], bv[j][k], bv[i][k + 1]))
        elif is_mouth and in_j:
            bowl.faces.new((bv[i][k], bv[j][k], bv[j][k + 1]))
        elif not is_mouth:
            core.faces.new((cv[i][k], cv[j][k], cv[j][k + 1], cv[i][k + 1]))
core.faces.new([c[0] for c in cv])
core.faces.new([c[-1] for c in cv])
bmesh.ops.delete(bowl, geom=[v for v in bowl.verts if not v.link_faces], context='VERTS')
tag(core, 'joint_head')
tag(bowl, 'joint_head')
new_obj("MM_HeadCore", core, M_JOINT, 60, outward=True)
new_obj("MM_MouthBowl", bowl, M_MOUTH, 70, outward=True)

# lips: the rim of the mouth cassette, proud of the face; thick in the middle, closing to nothing at the corners
lips = bmesh.new()
MPHI = [a for a in PHI if a < PHM] + [PHM]
LIPCOL = [-a for a in reversed(MPHI[1:])] + MPHI
up, lo_, ru, rl = [], [], [], []
for a in LIPCOL:
    X = XN(a) if abs(a) < PHM else XM
    t = min(1.0, X / XM)
    r1 = 0.004 + 0.014 * (1 - t * t) ** 0.6
    r2 = 0.004 + 0.015 * (1 - t * t) ** 0.6
    zt = lip_top(X)
    up.append(hp(a, zt + 0.45 * r1, bulge(X, zt + 0.45 * r1) + 0.25 * r1))
    lo_.append(hp(a, lip_bot(X) - 0.45 * r2, 0.25 * r2))
    ru.append(r1)
    rl.append(r2)
tube(lips, up, ru, seg=10)
tube(lips, lo_, rl, seg=10)
tag(lips, 'joint_head')
new_obj("MM_Lips", lips, M_LIP, 60)

# eyes: the ball shows through the slot in the face plate, half covered by a heavy lid; dark iris; a lash bead
eyes, iris, lash = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    rows = []
    for z in (2.795, 2.81, 2.825, 2.84):
        rows.append([hp(s * hphi(EC + EW * 1.15 * (i / 5 - 1), z), z, bulge(EC + EW * 1.15 * (i / 5 - 1), z) - 0.004) for i in range(11)])
    grid(eyes, rows)
    p, n = gauge_pt(HSEC, HN, s * hphi(EC + 0.006, 2.821), 2.821, bulge(EC + 0.006, 2.821) - 0.0035)
    puck(iris, p, n, 0.0165, 0.004, seg=14)
    pts, rr = [], []
    for i in range(13):
        X = EC + EW * (i / 6 - 1)
        pts.append(hp(s * hphi(X, 2.83), eye_z(X) + eye_hi(X) + 0.001, bulge(X, 2.83) + 0.001))
        rr.append(0.0022 + 0.0022 * math.sin(math.pi * i / 12))
    tube(lash, pts, rr, seg=5)
tag(eyes, 'joint_head')
tag(iris, 'joint_head')
tag(lash, 'joint_head')
new_obj("MM_Eyes", eyes, M_EYE, 60, outward=True)
new_obj("MM_Iris", iris, M_IRIS, 40)

# brows: raised dark bars, low and heavy over the nose, lifting and thinning toward the temples
brow = bmesh.new()
for s in (-1, 1):
    rows = [[], []]
    for i in range(13):
        tt = i / 12
        X = 0.04 + 0.21 * tt
        zc = 2.872 + 0.066 * (1 - (1 - tt) ** 2.2) - 0.010 * tt ** 3
        hw_ = 0.015 * (1 - 0.72 * tt)
        for k in (0, 1):
            z = zc + (hw_ if k else -hw_)
            rows[k].append(hp(s * hphi(X, z), z, bulge(X, z) + 0.006))
    grid(brow, rows)
tag(brow, 'joint_head')
new_obj("MM_Brows", brow, M_BROW, 35, outward=True, thickness=-0.012)
new_obj("MM_Lashes", lash, M_BROW, 40)

# nose: a small bulb with two wings on the centre ridge, and the bridge running up between the brows
nose = bmesh.new()
ny = lambda z: hp(0, z).y
NZ = (2.905, 2.88, 2.85, 2.82, 2.795, 2.775, 2.762, 2.752)
NR = (0.008, 0.011, 0.013, 0.016, 0.021, 0.027, 0.026, 0.016)
tube(nose, [Vector((0, ny(z) + r * 0.45 - (0.012 if 2.755 < z < 2.80 else 0.0), z)) for z, r in zip(NZ, NR)], NR, seg=12)
for sx_ in (-1, 1):
    bmesh.ops.create_uvsphere(nose, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation((sx_ * 0.026, ny(2.76) + 0.018, 2.76)) @ Matrix.Diagonal((0.02, 0.022, 0.016, 1.0)))
tag(nose, 'joint_head')
new_obj("MM_Nose", nose, M_PLATE, 60)

# underside of the head and the layered neck bearing
rows = [[hp(a, z) for a in range(-180, 180, 5)] for z in (2.30, 2.315, BASE_Z)]
base = bmesh.new()
grid(base, rows, wrap=True)
base.faces.new([base.verts.new(hp(a, 2.30)) for a in range(-180, 180, 5)])
tag(base, 'joint_head')
new_obj("MM_HeadBase", base, M_PLATE, 50, outward=True)
lathe(steel, (0, 0.0, 2.19), (0, 0, 1), [(0.0, 0.17), (0.03, 0.205), (0.045, 0.205), (0.05, 0.18), (0.058, 0.22), (0.075, 0.22),
                                          (0.08, 0.185), (0.088, 0.225), (0.105, 0.225), (0.11, 0.19), (0.13, 0.19)], seg=28)

# rivets beside the seams
for X, z in ((0.013, 3.105), (0.26, 2.905), (0.21, 2.728), (0.265, 2.705), (0.275, 2.535), (0.285, 2.47),
             (0.014, 2.405), (0.30, 2.40), (0.18, 2.385)):
    for s in (-1, 1):
        p, n = gauge_pt(HSEC, HN, s * hphi(X, z), z, bulge(X, z))
        puck(plate, p, n, 0.0058, 0.006, seg=6)
for a in (112, 140, 168):
    for s in (-1, 1):
        p, n = gauge_pt(HSEC, HN, s * a, 2.405)
        puck(plate, p, n, 0.0058, 0.006, seg=6)

# ---- hair shell: a separate rigid helmet of painted panels, standing off the head. Sides and back are a tapering
# box; the front faces carry on the angle of the cheeks, cut back to a vertical edge beside the face and rising to
# a peak over the forehead. Panels meet on hairline seams; a riveted band runs round at brow height.
def hairp(phi, z, eps=0.0):
    return gauge_pt(HAIRSEC, HAIRN, phi, z, eps)[0]


HAIR_EDGE_X, PEAK_Z, BAND_Z = 0.31, 3.165, 2.93
HAIR_TOP = Vector((0.0, -0.03, 3.235))


def hair_edge(z):                # how far round from centre front the hair starts at this height
    if z >= PEAK_Z:
        return agap(z)
    x = HAIR_EDGE_X if z <= BAND_Z else HAIR_EDGE_X * (PEAK_Z - z) / (PEAK_Z - BAND_Z)
    return max(agap(z), phi_of_x(HAIRSEC, HAIRN, x, z))


HAIR_Z = [2.51, 2.60, 2.70, 2.80, 2.905, 2.955, 3.0, 3.05, 3.10, 3.14, PEAK_Z, 3.185, 3.20]
TOP_K = (0.8, 0.5, 0.2, 0.02)
hair = bmesh.new()
SEAMS = (90.0, 115.0, 152.0, 180.0)
for s in (1, -1):
    lo_phi = None
    for hi_phi, ncol in zip(SEAMS, (12, 4, 6, 5)):
        rows = []
        for z in HAIR_Z:
            g = agap(z)
            a0 = hair_edge(z) if lo_phi is None else lo_phi + g
            a1 = hi_phi - g
            rows.append([hairp(s * (a0 + (a1 - a0) * i / ncol), z) for i in range(ncol + 1)])
        grid(hair, rows)
        # underside: from the outer skin in to the head, so the shell reads as a solid block from below
        g = agap(2.51)
        a0 = hair_edge(2.51) if lo_phi is None else lo_phi + g
        a1 = hi_phi - g
        grid(hair, [[hairp(s * (a0 + (a1 - a0) * i / ncol), 2.51) for i in range(ncol + 1)],
                    [hp(s * (a0 + (a1 - a0) * i / ncol), 2.51, 0.001) for i in range(ncol + 1)]])
        if lo_phi is None:                                       # the cut front edge, closed in to the head the same way
            zs = [z for z in HAIR_Z if z <= PEAK_Z]
            grid(hair, [[hairp(s * hair_edge(z), z) for z in zs], [hp(s * hair_edge(z), min(z, 3.14), 0.001) for z in zs]])
        lo_phi = hi_phi
tag(hair, 'joint_head')
new_obj("MM_Hair", hair, M_HAIR, 50, outward=True, thickness=-0.012)
# the top: one nearly flat plate, rising a little to the middle
htop = bmesh.new()
edge = [hairp(a, 3.20) for a in [7.5 * i - 180 for i in range(48)]]
htop.faces.new([htop.verts.new(p) for p in edge])
tag(htop, 'joint_head')
new_obj("MM_HairTop", htop, M_HAIR, 50, outward='up', thickness=-0.012)
band = bmesh.new()
for s in (1, -1):
    a0 = hair_edge(BAND_Z) + 3.0
    grid(band, [[hairp(s * (a0 + (180 - a0) * i / 28), z, 0.001) for i in range(29)] for z in (2.908, 2.952)])
tag(band, 'joint_head')
new_obj("MM_HairBand", band, M_HAIR, 50, outward=True, thickness=0.004)
for a in SEAMS:
    for z in (2.55, 2.885, 2.975, 3.165):
        for s in (-1, 1):
            for da in ((-2.6, 2.6) if a < 180 else (-2.6,)):
                p, n = gauge_pt(HAIRSEC, HAIRN, s * (a + da), z)
                puck(pewter, p, n, 0.0065, 0.007, seg=6)
for z in (2.55, 2.80, 2.885):
    for s in (-1, 1):
        a = hair_edge(z) + 4.5
        p, n = gauge_pt(HAIRSEC, HAIRN, s * a, z)
        puck(pewter, p, n, 0.0065, 0.007, seg=6)
for _bm in (plate, joint, steel, pewter):
    tag(_bm, 'joint_head')

# ---------------------------------------------------------------- suit front: layers, inside to outside
shirt, tie, lap, placket = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
pockets, straps, stitch = bmesh.new(), bmesh.new(), bmesh.new()
SR = 0.0036                      # stitch radius

loft(shirt, [fb(2.30, 0.31, -0.255, 0.30), fb(2.39, 0.29, -0.245, 0.285), fb(2.39, 0.275, -0.23, 0.27), fb(2.31, 0.285, -0.24, 0.28)],
     seg=24, caps=(False, False))
tag(shirt, '@shirt')
leaves = bmesh.new()
for s in (-1, 1):
    patch(leaves, SS, [(s * 0.02, s * 0.20, 2.365), (s * 0.06, s * 0.215, 2.30), (s * 0.135, s * 0.19, 2.225)], 0.011, nx=4)
patch(tie, SS, [(-0.05, 0.05, 2.345), (-0.07, 0.07, 2.30), (-0.045, 0.045, 2.215)], 0.022, nx=4)
patch(tie, SS, [(-0.04, 0.04, 2.22), (-0.065, 0.065, 2.10), (-0.07, 0.07, 2.03)], 0.007, nx=4)

panel(placket, TS, [(-0.045, 1.056), (0.15, 1.056), (0.15, 1.81), (0.07, 1.975), (-0.045, 1.975)], lambda x, z: 0.003, cuts=2)
for z in (1.69, 1.54, 1.39, 1.215):
    p = surf(TS, 0.045, z, 0.011)
    nrm = (surf(TS, 0.045, z, 1.0) - surf(TS, 0.045, z, 0.0)).normalized()
    lathe(pewter, p, nrm, [(0.0, 0.036), (0.008, 0.036), (0.016, 0.028), (0.016, 0.021), (0.010, 0.019)], seg=14)
    lathe(pewter, p, nrm, [(0.008, 0.019), (0.019, 0.014), (0.023, 0.004)], seg=10)
    lathe(joint, p, nrm, [(0.0, 0.042), (0.005, 0.042)], seg=14)
tag(pewter, '@jacket')
tag(joint, '@jacket')
for xe in (0.135, -0.031):
    edge = [(xe, 1.80 - (1.80 - 1.10) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.016) for x, z in edge], [SR] * len(edge), seg=4)
hem = [ring_pt(TS, 1.10, a, 0.004)[0] for a in range(-76, 257, 6)]
tube(stitch, hem, [SR] * len(hem), seg=4)
tube(stitch, COLLAR_EDGE, [SR] * len(COLLAR_EDGE), seg=4)
for s in (-1, 1):                                                # the two long seams down the back
    seam = [surf(TS, s * (0.30 - 0.03 * (z - 1.1)), z, 0.004, back=True) for z in [1.10 + 0.95 * i / 14 for i in range(15)]]
    tube(stitch, seam, [SR] * len(seam), seg=4)


def roll_lift(x, z):
    return 0.007 + 0.018 * max(0.0, 1.0 - (abs(x) - front_gap(z)) / 0.09)


def flat_lift(x, z):
    return 0.0045


g = front_gap
for s in (-1, 1):
    lapel = [(0.005, 1.995), (0.40, 2.115), (0.45, 2.165), (0.33, 2.20), (g(2.21), 2.21), (g(2.14), 2.14), (g(2.07), 2.07)]
    collar_front = [(g(2.21), 2.21), (0.33, 2.20), (0.475, 2.205), (0.50, 2.25), (0.42, 2.325), (g(2.325), 2.325)]
    flap = [(0.40, 1.40), (0.67, 1.40), (0.67, 1.25), (0.655, 1.23), (0.415, 1.23), (0.40, 1.25)]
    for outline, grain in ((lapel, (0.48, 0.43)), (collar_front, (0.3, -0.2))):
        o = [(s * x, z) for x, z in outline]
        panel(lap, TS, o, roll_lift, grain=(s * grain[0], grain[1]))
        topstitch(stitch, TS, o, lambda x, z: roll_lift(x, z) + 0.019, inset=0.014, step=0.035, radius=SR)
    o = [(s * x, z) for x, z in flap]
    panel(pockets, TS, o, flat_lift, cuts=2)
    topstitch(stitch, TS, o, lambda x, z: 0.017, inset=0.013, step=0.035, radius=SR)
breast = [(0.27, 1.90), (0.57, 1.90), (0.57, 1.64), (0.42, 1.575), (0.27, 1.64)]
panel(pockets, TS, breast, flat_lift, cuts=2)
topstitch(stitch, TS, breast, lambda x, z: 0.017, inset=0.013, step=0.035, radius=SR)
panel(pockets, TS, [(0.27, 1.90), (0.57, 1.90), (0.57, 1.862), (0.27, 1.862)], lambda x, z: 0.010, cuts=1)
pocket_sq = [surf(TS, x, z, 0.019) for x, z in ((0.30, 1.895), (0.54, 1.895), (0.535, 1.95), (0.50, 1.925), (0.47, 1.985),
                                               (0.44, 1.93), (0.405, 1.99), (0.375, 1.93), (0.335, 1.965))]
shirt.faces.new([shirt.verts.new(p) for p in pocket_sq])
tag(shirt, '@jacket')


# Shoulder straps: a band over each shoulder, from the chest up over the ridge and down the back, a stud at each end.
def ts_hw(z):
    return interp(TS, z)[3]


def strap_edge(dx, lift=0.012, n=7, m=9):
    """One edge of the strap: from the chest (x 0.655, z 2.19) up to the shoulder ridge and down the back to z 2.085."""
    lo, hi = 2.19, 2.36                                          # where this edge meets the ridge
    for _ in range(40):
        mid = (lo + hi) / 2
        if 0.655 + dx + (0.52 - 0.655) * (mid - 2.19) / 0.12 < 0.975 * ts_hw(mid):
            lo = mid
        else:
            hi = mid
    zt = lo
    xt = 0.975 * ts_hw(zt)
    pts = []
    for i in range(n):
        f = i / (n - 1)
        pts.append(surf(TS, 0.655 + dx + (xt - 0.655 - dx) * f, 2.19 + (zt - 2.19) * f, lift))
    for i in range(1, m):
        f = i / (m - 1)
        pts.append(surf(TS, xt + (0.635 + dx - xt) * f, zt + (2.085 - zt) * f, lift, back=True))
    return pts


for s in (-1, 1):
    grid(straps, [mirror(strap_edge(dx), s) for dx in (-0.055, 0.0, 0.055)])
    c0, c1 = strap_edge(0.0, 0.023), strap_edge(0.0, 1.023)
    for i in (1, -2):
        nrm = (c1[i] - c0[i]).normalized()
        lathe(pewter, Vector((s * c0[i].x, c0[i].y, c0[i].z)), Vector((s * nrm.x, nrm.y, nrm.z)),
              [(0.0, 0.017), (0.007, 0.017), (0.013, 0.008), (0.015, 0.001)], seg=10)
tag(pewter, '@jacket')
tag(stitch, '@jacket')

# Medallion: lies on the closed jacket front, tilted to the chest's slope, hanging from a cord under the collar.
MZ = 1.905
slope = (surf(TS, 0, MZ + 0.08).y - surf(TS, 0, MZ - 0.08).y) / 0.16
mn = Vector((0, -1, slope)).normalized()
mt = Vector((0, slope, 1)).normalized()
mc = surf(TS, 0.0, MZ) + mn * 0.028
medal_p, medal_j = bmesh.new(), bmesh.new()
exec(compile(open("/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc - mn * 0.0176, mn, mt, 0.135, 'tie')
tag(medal_p, 'joint_attachMeter')
tag(medal_j, 'joint_attachMeter')
cord = bmesh.new()
for s in (-1, 1):
    pts = [surf(SS, s * 0.17, 2.31, 0.016), surf(TS, s * (g(2.22) + 0.01), 2.22, 0.03), surf(TS, s * (g(2.12) + 0.008), 2.12, 0.03),
           surf(TS, s * 0.02, 2.035, 0.032), bail + Vector((s * 0.012, 0, 0))]
    tube(cord, pts, [0.008] * len(pts), seg=5)
tag(cord, '@jacket')

new_obj("MM_Shirt", shirt, M_SHIRT, 30)
new_obj("MM_ShirtCollar", leaves, M_SHIRT, 30, outward=True, thickness=0.009)
new_obj("MM_Stitching", stitch, M_STITCH, 40)
new_obj("MM_Tie", tie, M_TIE, 30, outward=True, thickness=0.013)
new_obj("MM_ButtonStand", placket, M_SUIT, 30, outward=True, thickness=0.011)
new_obj("MM_Lapels", lap, M_SUIT, 30, outward=True, thickness=0.018)
new_obj("MM_Pockets", pockets, M_SUIT, 30, outward=True, thickness=0.011)
new_obj("MM_Straps", straps, M_SUIT, 40, outward='up', thickness=0.011)
new_obj("MM_Medallion", medal_p, M_PEWTER, 32)
new_obj("MM_MedallionEmblem", medal_j, M_JOINT, 40)
new_obj("MM_Cord", cord, M_JOINT, 40)
new_obj("MM_Plates", plate, M_PLATE, 32)
new_obj("MM_Joints", joint, M_JOINT, 40)
new_obj("MM_Steel", steel, M_STEEL, 40)
new_obj("MM_Buttons", pewter, M_PEWTER, 32)

# ---------------------------------------------------------------- check camera + light, stats
cam = bpy.data.objects.new("MMCam", bpy.data.cameras.new("MMCam"))
col.objects.link(cam)
sun = bpy.data.objects.new("MMSun", bpy.data.lights.new("MMSun", 'SUN'))
col.objects.link(sun)
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fill = bpy.data.objects.new("MMFill", bpy.data.lights.new("MMFill", 'AREA'))
col.objects.link(fill)
fill.data.energy = 45
fill.data.size = 4
fill.location = (-3.7, -4.3, 2.5)
fill.rotation_euler = (Vector((0, 0, 1.5)) - Vector(fill.location)).to_track_quat('-Z', 'Y').to_euler()

dg = bpy.context.evaluated_depsgraph_get()
per = {}
for o in col.objects:
    if o.type == 'MESH' and not o.hide_render:
        em = o.evaluated_get(dg).to_mesh()
        per[o.name] = sum(len(p.vertices) - 2 for p in em.polygons)
result = {"tris": sum(per.values()), "per_object": per}
