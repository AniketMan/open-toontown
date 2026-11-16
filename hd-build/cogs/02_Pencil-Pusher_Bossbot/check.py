"""Render check views of the Pencil Pusher. Orthographic views are at 2x the sheet's pixels per unit (228 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/02_Pencil-Pusher_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["PPCam"]
PXU = 228.0
ONLY = globals().get("ONLY")
PREFIX = globals().get("PREFIX", "chk_")
keep = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent)
sc.camera = cam
sc.render.film_transparent = True
sc.render.resolution_percentage = 100
done = []


def shot(name, loc, target, w_units, h_units, ortho=True, k=1):
    if ONLY and name not in ONLY:
        return
    sc.render.resolution_x = round(w_units * PXU * k)
    sc.render.resolution_y = round(h_units * PXU * k)
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    cam.data.ortho_scale = max(w_units, h_units)
    cam.data.lens = 115
    cam.data.clip_end = 200
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = SP + PREFIX + name + ".png"
    bpy.ops.render.render(write_still=True)
    done.append(name)


shot("front", (0, -20, 2.5), (0, 0, 2.5), 2.6, 5.1)
shot("left", (20, 0, 2.5), (0, 0, 2.5), 2.0, 5.1)
shot("back", (0, 20, 2.5), (0, 0, 2.5), 2.6, 5.1)
shot("headfront", (0, -20, 4.15), (0, 0, 4.15), 0.9, 1.85, k=3)
shot("headleft", (20, 0, 4.15), (0, 0, 4.15), 0.9, 1.85, k=3)
shot("headback", (0, 20, 4.15), (0, 0, 4.15), 0.9, 1.85, k=3)
shot("head34", (-9, -16, 5.4), (0, 0, 3.95), 1.0, 1.5, k=3)
shot("mouth", (5, -18, 2.6), (0, -0.1, 3.62), 0.7, 0.6, k=5)
shot("chestfront", (0, -20, 2.6), (0, 0, 2.6), 1.6, 1.8, k=3)
shot("chestback", (0, 20, 2.6), (0, 0, 2.6), 1.6, 1.8, k=3)
shot("chestleft", (20, 0, 2.6), (0, 0, 2.6), 1.2, 1.8, k=3)
shot("chest34", (9, -17, 3.4), (0.0, -0.3, 2.9), 1.4, 1.2, k=3)
shot("neck", (4, -17, 6.0), (0, -0.1, 3.3), 1.2, 0.9, k=4)
shot("above", (0, -7, 19), (0, 0.0, 3.3), 2.0, 1.5, k=3)
shot("handfront", (0.6, -20, 1.55), (0.6, 0, 1.55), 0.6, 0.9, k=4)
shot("handleft", (20, 0.05, 1.55), (0, 0.05, 1.55), 0.7, 0.9, k=4)
shot("shoes", (0, -20, 0.22), (0, 0, 0.22), 1.5, 0.5, k=4)
shot("shoeside", (20, -0.1, 0.22), (0, -0.1, 0.22), 1.2, 0.5, k=4)
shot("shoe34", (-9, -17, 1.6), (0.2, -0.2, 0.18), 1.4, 0.6, k=4)
shot("under", (4, -9, -14), (0, 0, 1.6), 1.6, 1.4, k=3)
shot("strapL", (-6, 14, 5), (-0.36, 0.3, 3.14), 0.6, 0.5, k=6)
shot("strapR", (6, 14, 5), (0.36, 0.3, 3.14), 0.6, 0.5, k=6)
shot("jaw", (12, -14, 4.6), (0.05, -0.05, 3.63), 0.62, 0.62, k=6)
shot("jawfront", (0, -20, 3.62), (0, 0, 3.62), 0.6, 0.5, k=6)
shot("seams", (-10, 14, 5.2), (0, 0.05, 4.0), 0.6, 0.9, k=5)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 19, -math.cos(a) * 19, 3.0), (0, 0, 2.5), 2.6, 5.1, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
