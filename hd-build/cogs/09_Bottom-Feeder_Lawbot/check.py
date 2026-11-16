"""Render check views of the Bottom Feeder. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/09_Bottom-Feeder_Lawbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["BFCam"]
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


shot("front", (0, -30, 2.45), (0, 0, 2.45), 3.8, 5.1)
shot("left", (30, 0, 2.45), (0, 0, 2.45), 3.0, 5.1)
shot("back", (0, 30, 2.45), (0, 0, 2.45), 3.8, 5.1)
shot("headfront", (0, -30, 4.25), (0, 0, 4.25), 1.5, 1.3, k=4)
shot("headleft", (30, 0, 4.25), (0, -0.15, 4.25), 1.5, 1.3, k=4)
shot("head34", (-14, -24, 6.4), (0, -0.15, 4.22), 1.5, 1.3, k=4)
shot("head34b", (16, -22, 4.9), (0, -0.15, 4.22), 1.5, 1.3, k=4)
shot("rear34", (16, 22, 5.6), (0, -0.1, 4.2), 1.6, 1.4, k=4)
shot("rear34b", (-18, 20, 6.2), (0, -0.1, 4.2), 1.6, 1.4, k=4)
shot("neckside", (30, 4, 4.6), (0, -0.1, 3.75), 1.8, 0.9, k=4)
shot("vee", (0, -30, 4.0), (0, -0.6, 3.3), 1.8, 1.5, k=4)
shot("chestfront", (0, -30, 2.75), (0, 0, 2.75), 3.2, 2.4, k=2)
shot("chestback", (0, 30, 2.75), (0, 0, 2.75), 3.2, 2.4, k=2)
shot("shtop", (0, -4, 36), (0, 0, 3.2), 3.8, 2.9, k=2)
shot("shfront", (0, -30, 9), (0, 0, 3.3), 3.8, 2.2, k=2)
shot("shback", (0, 30, 9), (0, 0, 3.3), 3.8, 2.2, k=2)
shot("legs", (0, -30, 0.7), (0, 0, 0.7), 2.4, 1.5, k=3)
shot("walkfront", (0, -30, 2.45), (0, 0, 2.45), 4.4, 5.1)
shot("walkleft", (30, 0, 2.45), (0, 0, 2.45), 4.4, 5.1)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 26, -math.cos(a) * 26, 3.3), (0, 0, 2.45), 3.8, 5.1, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
