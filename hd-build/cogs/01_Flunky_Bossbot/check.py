"""Render orthographic check views at exactly 2x the reference sheet's pixels-per-unit, plus a 3/4 beauty shot."""
import bpy, math
from mathutils import Vector

SP = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/01_Flunky_Bossbot/"
sc = bpy.context.scene
cam = bpy.data.objects["FlunkyCam"]
sun = bpy.data.objects["FlunkySun"]
PXU = 2 * 404 / 4.9
keep = (sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent)
sc.camera = cam
sc.render.film_transparent = True
sc.render.resolution_percentage = 100


def shot(name, loc, target, w_units, h_units, ortho=True, k=1):
    sc.render.resolution_x = round(w_units * PXU * k)
    sc.render.resolution_y = round(h_units * PXU * k)
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    cam.data.ortho_scale = max(w_units, h_units)
    cam.data.lens = 115
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = SP + "chk_" + name + ".png"
    bpy.ops.render.render(write_still=True)


shot("front", (0, -20, 2.45), (0, 0, 2.45), 3.8, 5.0)
shot("left", (20, -0.1, 2.45), (0, -0.1, 2.45), 2.8, 5.0)
shot("back", (0, 20, 2.45), (0, 0, 2.45), 3.8, 5.0)
shot("headfront", (0, -20, 4.3), (0, 0, 4.3), 1.4, 1.3, k=3)
shot("headleft", (20, -0.1, 4.3), (0, -0.1, 4.3), 1.4, 1.3, k=3)
shot("handfront", (1.37, -20, 1.72), (1.37, 0, 1.72), 0.85, 1.27, k=3)      # character's left hand, as on the sheet
shot("handleft", (20, -0.22, 1.72), (0, -0.22, 1.72), 1.03, 1.39, k=3)
shot("shoes", (0, -20, 0.33), (0, 0, 0.33), 2.43, 0.73, k=2)
shot("chest", (9, -17, 3.6), (0.0, -1.0, 3.2), 1.7, 1.4, k=3)                 # from the side: does the medallion sit on the chest?
shot("chestfront", (0, -20, 3.3), (0, 0, 3.3), 1.9, 1.3, k=3)
shot("above", (0, -9, 19), (0, -0.25, 3.6), 3.0, 2.2, k=2)                    # looking down on collar and shoulders
shot("shoulder", (14, -6, 12), (0.7, 0.0, 3.4), 2.0, 1.5, k=3)                # epaulette, sleeve head, armhole seam
shot("lapel34", (-8, -17, 4.5), (0.0, -0.9, 3.3), 1.9, 1.5, k=3)
shot("head34",(-9, -16, 5.2), (0, -0.1, 4.3), 1.5, 1.4, k=3)
shot("neck", (5, -17, 6.5), (0, -0.3, 3.75), 1.9, 1.3, k=3)                   # down into the collar: shirt, vest, jacket layers
shot("backtop", (0, 20, 4.2), (0, 0, 3.3), 3.0, 1.6, k=2)
shot("shoeside", (20, -0.1, 0.3), (0, -0.1, 0.3), 1.9, 0.75, k=3)
shot("shoe34", (-9, -17, 1.6), (0.3, -0.3, 0.25), 2.2, 0.9, k=3)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 19, -math.cos(a) * 19, 3.0), (0, 0, 2.45), 3.8, 5.0, ortho=False)
(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep
result = {"ok": True}
