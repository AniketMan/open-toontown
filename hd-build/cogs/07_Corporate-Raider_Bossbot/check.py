"""Render check views of the Corporate Raider. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/07_Corporate-Raider_Bossbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["CRCam"]
PXU = 130.0
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


shot("front", (0, -40, 4.2), (0, 0, 4.2), 6.6, 8.6)
shot("left", (40, 0, 4.2), (0, 0, 4.2), 5.0, 8.6)
shot("back", (0, 40, 4.2), (0, 0, 4.2), 6.6, 8.6)
shot("headfront", (0, -40, 7.35), (0, 0, 7.35), 2.4, 2.0, k=3)
shot("headleft", (40, 0, 7.35), (0, 0.1, 7.35), 2.4, 2.0, k=3)
shot("headback", (0, 40, 7.35), (0, 0, 7.35), 2.4, 2.0, k=3)
shot("head34", (-18, -32, 11), (0, 0, 7.3), 2.4, 2.0, k=3)
shot("head34b", (18, -32, 9), (0, 0, 7.3), 2.4, 2.0, k=3)
shot("headtop", (0, -8, 40), (0, 0.1, 7.4), 2.4, 2.0, k=3)
shot("chestfront", (0, -40, 4.8), (0, 0, 4.8), 5.4, 4.0, k=1.5)
shot("chestback", (0, 40, 4.8), (0, 0, 4.8), 5.4, 4.0, k=1.5)
shot("shtop", (0, -5, 45), (0, 0, 5.5), 6.6, 5.0, k=1.2)
shot("shfront", (0, -40, 14), (0, 0, 5.6), 6.6, 3.6, k=1.2)
shot("shback", (0, 40, 14), (0, 0, 5.6), 6.6, 3.6, k=1.2)
shot("walkfront", (0, -40, 4.2), (0, 0, 4.2), 7.6, 8.6)
shot("walkleft", (40, 0, 4.2), (0, 0, 4.2), 7.6, 8.6)
shot("walkback", (0, 40, 4.2), (0, 0, 4.2), 7.6, 8.6)
shot("eye", (4, -38, 9.2), (0.22, -0.3, 7.7), 0.8, 0.6, k=8)
shot("eyeside", (30, -26, 8.4), (0.25, -0.3, 7.7), 0.8, 0.6, k=8)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 38, -math.cos(a) * 38, 5.6), (0, 0, 4.2), 6.6, 8.6, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
