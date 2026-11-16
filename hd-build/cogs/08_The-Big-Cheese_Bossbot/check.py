"""Render check views of the Big Cheese. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/08_The-Big-Cheese_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["TBCCam"]
PXU = 115.0
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


shot("front", (0, -40, 4.8), (0, 0, 4.8), 5.4, 9.8)
shot("left", (40, 0, 4.8), (0, 0, 4.8), 3.6, 9.8)
shot("back", (0, 40, 4.8), (0, 0, 4.8), 5.4, 9.8)
shot("headfront", (0, -40, 8.3), (0, 0, 8.3), 1.6, 2.4, k=3)
shot("headleft", (40, 0, 8.3), (0, 0.05, 8.3), 1.6, 2.4, k=3)
shot("headback", (0, 40, 8.3), (0, 0, 8.3), 1.6, 2.4, k=3)
shot("head34", (-18, -32, 12), (0, 0, 8.25), 1.8, 2.4, k=3)
shot("head34b", (22, -28, 9.5), (0, 0, 8.25), 1.8, 2.4, k=3)
shot("face", (4, -38, 9), (0, -0.3, 7.9), 1.3, 1.3, k=5)
shot("chestfront", (0, -40, 5.9), (0, 0, 5.9), 5.0, 3.8, k=1.5)
shot("shtop", (0, -5, 45), (0, 0, 6.2), 5.6, 4.0, k=1.2)
shot("shfront", (0, -40, 15), (0, 0, 6.4), 5.6, 3.4, k=1.2)
shot("shback", (0, 40, 15), (0, 0, 6.4), 5.6, 3.4, k=1.2)
shot("walkfront", (0, -40, 4.8), (0, 0, 4.8), 6.4, 9.8)
shot("walkleft", (40, 0, 4.8), (0, 0, 4.8), 6.4, 9.8)
shot("walkback", (0, 40, 4.8), (0, 0, 4.8), 6.4, 9.8)
shot("rear34", (22, 30, 9.5), (0, 0.1, 8.1), 2.2, 2.6, k=3)
shot("rear34b", (-24, 26, 11), (0, 0.1, 8.1), 2.2, 2.6, k=3)
shot("neckside", (40, 6, 8.2), (0, 0.05, 7.3), 2.4, 1.2, k=4)
shot("neckfront", (6, -38, 8.6), (0, 0, 7.3), 2.4, 1.2, k=4)
shot("vee", (0, -40, 7.4), (0, -0.6, 6.55), 1.8, 1.6, k=4)
shot("vee2", (8, -38, 5.6), (0, -0.6, 6.5), 1.8, 1.6, k=4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 40, -math.cos(a) * 40, 6.2), (0, 0, 4.8), 5.4, 9.8, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
