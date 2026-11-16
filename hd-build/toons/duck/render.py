"""Render the original duck head and the HD one from the sheet's five views, into duck/work/o_*.png and a_*.png.
Run in Blender after build.py: exec(open(this file).read()). Then run compare.py with python3 for the stacked sheet."""
import bpy, math
from mathutils import Vector

OUT = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/toon-hd-build/duck/work/"
sc = bpy.context.scene
cam = bpy.data.objects["ToonCam"]
sc.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 2.6
sc.render.resolution_x = sc.render.resolution_y = 700
sc.render.film_transparent = False
CENTRE = Vector((0.0, 0.05, 0.5))
VIEWS = {"front": (0, 1, 0.05), "threeq": (-0.7, 0.72, 0.08), "side": (-1, 0, 0.05), "back": (0, -1, 0.05), "top": (0, 0.45, 1)}


def show(name, on):
    c = bpy.data.collections[name]
    for o in c.objects:
        o.hide_render = not on


for tag, colname in (("o", "duck_original"), ("a", "duck_hd")):
    show("duck_original", colname == "duck_original")
    show("duck_hd", colname == "duck_hd")
    if tag == "o":                                                # the original file holds every variant: show the short head only
        keep = {"orig_head-short", "orig_head-front-short", "orig_eyes-short", "orig_joint_pupilL_short",
                "orig_joint_pupilR_short", "orig_muzzle-short-neutral"}
        for o in bpy.data.collections["duck_original"].objects:
            o.hide_render = o.name not in keep
    for view, d in VIEWS.items():
        d = Vector(d).normalized()
        cam.location = CENTRE + d * 6
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = OUT + f"{tag}_{view}.png"
        bpy.ops.render.render(write_still=True)
show("duck_original", False)
show("duck_hd", True)
result = {"rendered": OUT}
