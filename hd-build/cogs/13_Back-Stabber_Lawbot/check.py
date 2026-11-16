"""Render check views of the Back Stabber. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/13_Back-Stabber_Lawbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["BKCam"]
PXU = 190.0
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
    cam.data.clip_end = 300
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = SP + PREFIX + name + ".png"
    bpy.ops.render.render(write_still=True)
    done.append(name)


shot("front", (0, -30, 3.4), (0, 0, 3.4), 4.4, 7.0)
shot("left", (30, 0, 3.4), (0, 0, 3.4), 3.2, 7.0)
shot("back", (0, 30, 3.4), (0, 0, 3.4), 4.4, 7.0)
shot("headfront", (0, -20, 5.72), (0, 0, 5.72), 1.3, 2.4, k=4)
shot("headleft", (20, 0, 5.72), (0, 0, 5.72), 1.3, 2.4, k=4)
shot("headback", (0, 20, 5.72), (0, 0, 5.72), 1.3, 2.4, k=4)
shot("head34", (-10, -16, 7.4), (0, 0, 5.68), 1.3, 2.4, k=4)
shot("headrear", (-12, 14, 6.8), (0, 0, 5.68), 1.3, 2.4, k=4)
shot("mouth", (4, -18, 4.9), (0.0, -0.2, 5.1), 0.9, 0.8, k=6)
shot("chestfront", (0, -20, 3.7), (0, 0, 3.7), 3.0, 2.3, k=2)
shot("chestback", (0, 20, 3.7), (0, 0, 3.7), 3.0, 2.3, k=2)
shot("neck", (4, -17, 7.0), (0, -0.2, 4.5), 1.6, 1.1, k=3)
shot("above", (0, -7, 22), (0, -0.1, 4.4), 3.6, 2.3, k=2)
shot("medal", (2.5, -19, 4.6), (0.0, -0.5, 3.68), 0.9, 1.0, k=7)
shot("walkfront", (0, -30, 3.4), (0, 0, 3.4), 4.8, 7.0)
shot("walkleft", (30, 0, 3.4), (0, 0, 3.4), 4.8, 7.0)
shot("walkback", (0, 30, 3.4), (0, 0, 3.4), 4.8, 7.0)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 30, -math.cos(a) * 30, 4.0), (0, 0, 3.4), 4.4, 7.0, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
