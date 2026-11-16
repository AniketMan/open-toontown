"""Render check views of the Micromanager. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/04_Micromanager_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["MMCam"]
PXU = 275.0
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


shot("front", (0, -20, 1.65), (0, 0, 1.65), 2.5, 3.4)
shot("left", (20, 0, 1.65), (0, 0, 1.65), 1.9, 3.4)
shot("back", (0, 20, 1.65), (0, 0, 1.65), 2.5, 3.4)
shot("headfront", (0, -20, 2.8), (0, 0, 2.8), 1.1, 1.0, k=4)
shot("headleft", (20, 0, 2.8), (0, 0, 2.8), 1.1, 1.0, k=4)
shot("headback", (0, 20, 2.8), (0, 0, 2.8), 1.1, 1.0, k=4)
shot("head34", (-10, -16, 4.2), (0, 0, 2.78), 1.1, 1.0, k=4)
shot("head34b", (10, -14, 1.6), (0, 0, 2.75), 1.1, 1.0, k=4)
shot("headtop", (0, -4, 25), (0, 0, 2.8), 1.1, 1.0, k=4)
shot("headunder", (0, -10, -6), (0, 0, 2.6), 1.1, 1.0, k=4)
shot("mouth", (6, -18, 2.2), (0.05, -0.2, 2.6), 0.75, 0.5, k=6)
shot("eye", (-3, -19, 3.0), (-0.11, -0.3, 2.84), 0.4, 0.28, k=10)
shot("chestfront", (0, -20, 1.75), (0, 0, 1.75), 1.9, 1.5, k=3)
shot("chestback", (0, 20, 1.75), (0, 0, 1.75), 1.9, 1.5, k=3)
shot("chestleft", (20, -0.4, 1.8), (0, -0.4, 1.8), 1.2, 1.3, k=3)
shot("belly", (2, -20, 0.9), (0.05, 0, 1.3), 0.7, 0.6, k=6)
shot("neck", (4, -17, 5.0), (0, -0.2, 2.25), 1.2, 0.8, k=4)
shot("above", (0, -7, 20), (0, -0.1, 2.2), 2.4, 1.9, k=2)
shot("handfront", (0.95, -20, 1.0), (0.95, 0, 1.0), 0.6, 0.8, k=4)
shot("handleft", (20, 0.0, 1.0), (0, 0.0, 1.0), 0.8, 0.8, k=4)
shot("shoes", (0, -20, 0.2), (0, 0, 0.2), 1.5, 0.5, k=4)
shot("shoeside", (20, -0.15, 0.2), (0, -0.15, 0.2), 1.2, 0.5, k=4)
shot("under", (4, -9, -12), (0, 0, 1.0), 2.4, 1.9, k=2)
shot("strapL", (-6, 12, 6), (-0.6, 0.3, 2.2), 0.7, 0.55, k=6)
shot("strapF", (-5, -14, 6), (-0.6, -0.3, 2.22), 0.7, 0.55, k=6)
shot("walkfront", (0, -20, 1.65), (0, 0, 1.65), 2.9, 3.4)
shot("walkleft", (20, 0, 1.65), (0, 0, 1.65), 2.9, 3.4)
shot("walkback", (0, 20, 1.65), (0, 0, 1.65), 2.9, 3.4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 14, -math.cos(a) * 14, 2.1), (0, 0, 1.65), 2.5, 3.4, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
