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
TORSO = [fb(2.42, 0.49, -0.50, 0.35), fb(2.60, 0.495, -0.50, 0.345), fb(3.00, 0.50, -0.50, 0.33),
         fb(3.40, 0.50, -0.50, 0.33), fb(3.80, 0.51, -0.47, 0.34), fb(4.05, 0.53, -0.43, 0.36),
         fb(4.25, 0.60, -0.36, 0.37), fb(4.38, 0.66, -0.31, 0.37), fb(4.46, 0.62, -0.27, 0.355),
         fb(4.51, 0.50, -0.24, 0.33), fb(4.55, 0.36, -0.21, 0.30), fb(4.58, 0.27, -0.19, 0.27)]
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

