"""Render check views of the Pencil Pusher. Orthographic views are at 2x the sheet's pixels per unit (228 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/03_Yesman_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["YMCam"]
PXU = 207.0
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


shot("front", (0, -20, 2.7), (0, 0, 2.7), 3.6, 5.5)
shot("left", (20, 0, 2.7), (0, 0, 2.7), 2.4, 5.5)
shot("back", (0, 20, 2.7), (0, 0, 2.7), 3.6, 5.5)
shot("headfront", (0, -20, 4.75), (0, 0, 4.75), 1.6, 1.4, k=3)
shot("headleft", (20, 0, 4.75), (0, 0, 4.75), 1.6, 1.4, k=3)
shot("headback", (0, 20, 4.75), (0, 0, 4.75), 1.6, 1.4, k=3)
shot("head34", (-10, -16, 6.5), (0, 0, 4.72), 1.6, 1.4, k=3)
shot("headtop", (0, -4, 25), (0, 0, 4.7), 1.6, 1.4, k=3)
shot("mouth", (8, -18, 4.2), (0.1, -0.1, 4.55), 1.2, 0.8, k=4)
shot("chestfront", (0, -20, 3.1), (0, 0, 3.1), 2.8, 2.2, k=2)
shot("chestback", (0, 20, 3.1), (0, 0, 3.1), 2.8, 2.2, k=2)
shot("neck", (5, -17, 7.0), (0, -0.2, 4.0), 1.8, 1.2, k=3)
shot("above", (0, -8, 20), (0, 0.0, 4.0), 3.2, 2.2, k=2)
shot("handfront", (1.15, -20, 2.0), (1.15, 0, 2.0), 0.9, 1.2, k=3)
shot("handleft", (20, 0.1, 2.0), (0, 0.1, 2.0), 1.0, 1.2, k=3)
shot("shoes", (0, -20, 0.3), (0, 0, 0.3), 2.0, 0.7, k=3)
shot("shoeside", (20, -0.2, 0.3), (0, -0.2, 0.3), 1.8, 0.7, k=3)
shot("under", (5, -10, -14), (0, 0, 2.0), 2.6, 2.0, k=2)
shot("strapL", (-7, 14, 6), (-0.65, 0.4, 3.62), 1.0, 0.8, k=4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 19, -math.cos(a) * 19, 3.2), (0, 0, 2.7), 3.6, 5.5, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
