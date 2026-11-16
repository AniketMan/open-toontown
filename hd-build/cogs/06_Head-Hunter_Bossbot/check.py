"""Render check views of the Head Hunter. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/06_Head-Hunter_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["HHCam"]
PXU = 145.0
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


shot("front", (0, -30, 3.8), (0, 0, 3.8), 4.6, 7.8)
shot("left", (30, 0, 3.8), (0, 0, 3.8), 3.0, 7.8)
shot("back", (0, 30, 3.8), (0, 0, 3.8), 4.6, 7.8)
shot("headfront", (0, -30, 7.1), (0, 0, 7.1), 1.1, 1.0, k=5)
shot("headleft", (30, 0, 7.1), (0, -0.1, 7.1), 1.1, 1.0, k=5)
shot("headback", (0, 30, 7.1), (0, 0, 7.1), 1.1, 1.0, k=5)
shot("head34", (-14, -24, 10), (0, -0.1, 7.08), 1.1, 1.0, k=5)
shot("headtop", (0, -6, 30), (0, -0.1, 7.1), 1.1, 1.0, k=5)
shot("chestfront", (0, -30, 5.2), (0, 0, 5.2), 4.2, 3.4, k=2)
shot("chestback", (0, 30, 5.2), (0, 0, 5.2), 4.2, 3.4, k=2)
shot("neck", (6, -25, 11), (0, -0.3, 6.4), 2.2, 1.5, k=3)
shot("above", (0, -10, 30), (0, -0.1, 6.0), 4.6, 3.2, k=1.5)
shot("walkfront", (0, -30, 3.8), (0, 0, 3.8), 5.4, 7.8)
shot("walkleft", (30, 0, 3.8), (0, 0, 3.8), 5.4, 7.8)
shot("walkback", (0, 30, 3.8), (0, 0, 3.8), 5.4, 7.8)
shot("shtop", (0, -4, 40), (0, 0, 5.5), 5.4, 3.4, k=1.5)
shot("shfront", (0, -30, 12), (0, 0, 5.8), 5.4, 3.0, k=1.5)
shot("shback", (0, 30, 12), (0, 0, 5.8), 5.4, 3.0, k=1.5)
shot("shside", (30, 0, 8), (0, 0, 5.8), 3.4, 3.0, k=1.5)
shot("vee", (0, -30, 6.8), (0, -0.6, 6.0), 1.8, 1.6, k=4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 30, -math.cos(a) * 30, 4.8), (0, 0, 3.8), 4.6, 7.8, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
