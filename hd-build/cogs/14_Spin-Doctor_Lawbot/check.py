"""Render check views of the SpinDoctor. Orthographic views are at 2x the sheet's pixels per unit (275 px/unit).
Set ONLY = [names] before running to render a subset; PREFIX names the output files."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/14_Spin-Doctor_Lawbot/work/"
sc = bpy.context.scene
cam = bpy.data.objects["SDCam"]
PXU = 150.0
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


shot("front", (0, -30, 4.0), (0, 0, 4.0), 3.6, 8.2)
shot("left", (30, 0, 4.0), (0, 0, 4.0), 2.8, 8.2)
shot("back", (0, 30, 4.0), (0, 0, 4.0), 3.6, 8.2)
shot("headfront", (0, -20, 6.9), (0, 0, 6.9), 1.8, 2.6, k=3)
shot("headleft", (20, 0, 6.9), (0, 0, 6.9), 1.8, 2.6, k=3)
shot("headback", (0, 20, 6.9), (0, 0, 6.9), 1.8, 2.6, k=3)
shot("head34", (-10, -16, 8.6), (0, 0, 6.85), 1.8, 2.6, k=3)
shot("mouth", (5, -18, 6.0), (0.0, -0.3, 6.4), 1.2, 1.0, k=5)
shot("chestfront", (0, -20, 4.6), (0, 0, 4.6), 2.8, 3.0, k=2)
shot("neck", (4, -17, 8.6), (0, -0.2, 5.7), 1.8, 1.3, k=3)
shot("medal", (2.5, -19, 5.8), (0.0, -0.45, 4.85), 1.0, 1.1, k=6)
shot("walkfront", (0, -30, 4.0), (0, 0, 4.0), 4.4, 8.2)
shot("walkleft", (30, 0, 4.0), (0, 0, 4.0), 4.4, 8.2)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 30, -math.cos(a) * 30, 4.8), (0, 0, 4.0), 3.6, 8.2, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"rendered": done}
