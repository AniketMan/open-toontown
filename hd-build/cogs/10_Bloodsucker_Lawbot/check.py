"""Render check views of the Bloodsucker. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/10_Bloodsucker_Lawbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["BSCam"]
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
    cam.data.clip_end = 200
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = SP + PREFIX + name + ".png"
    bpy.ops.render.render(write_still=True)
    done.append(name)


shot("front", (0, -20, 3.1), (0, 0, 3.1), 2.6, 6.4)
shot("left", (20, 0, 3.1), (0, 0, 3.1), 2.0, 6.4)
shot("back", (0, 20, 3.1), (0, 0, 3.1), 2.6, 6.4)
shot("headfront", (0, -20, 5.4), (0, 0, 5.4), 1.1, 2.0, k=4)
shot("headleft", (20, 0, 5.4), (0, 0, 5.4), 1.2, 2.0, k=4)
shot("headback", (0, 20, 5.4), (0, 0, 5.4), 1.1, 2.0, k=4)
shot("head34", (-10, -16, 7.2), (0, 0, 5.35), 1.2, 2.0, k=4)
shot("headrear", (-12, 14, 6.6), (0, 0, 5.35), 1.2, 2.0, k=4)
shot("face", (3, -19, 5.7), (0, -0.2, 5.45), 0.8, 0.7, k=6)
shot("mouth", (5, -18, 4.5), (0.0, -0.2, 4.9), 0.8, 0.7, k=6)
shot("medal", (2.5, -19, 4.6), (0.0, -0.35, 3.78), 0.75, 0.9, k=8)
shot("medalside", (14, -14, 4.0), (0.0, -0.35, 3.78), 0.75, 0.9, k=6)
shot("chestfront", (0, -20, 3.5), (0, 0, 3.5), 2.2, 2.4, k=2)
shot("chestback", (0, 20, 3.5), (0, 0, 3.5), 2.2, 2.4, k=2)
shot("neck", (4, -17, 7.5), (0, -0.2, 4.4), 1.4, 1.0, k=3)
shot("above", (0, -7, 22), (0, -0.1, 4.4), 2.4, 1.9, k=2)
shot("handfront", (0.8, -20, 2.3), (0.8, 0, 2.3), 0.7, 1.0, k=4)
shot("shoes", (0, -20, 0.25), (0, 0, 0.25), 1.6, 0.6, k=4)
shot("under", (4, -9, -10), (0, 0, 2.2), 2.4, 1.9, k=2)
shot("hem", (-6, 16, 3.5), (0, 0.2, 2.6), 1.4, 0.8, k=4)
shot("walkfront", (0, -20, 3.1), (0, 0, 3.1), 3.4, 6.4)
shot("walkleft", (20, 0, 3.1), (0, 0, 3.1), 3.4, 6.4)
shot("walkback", (0, 20, 3.1), (0, 0, 3.1), 3.4, 6.4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 22, -math.cos(a) * 22, 3.8), (0, 0, 3.1), 2.6, 6.4, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
