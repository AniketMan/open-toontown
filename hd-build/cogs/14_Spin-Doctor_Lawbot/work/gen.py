B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D = B + "14_Spin-Doctor_Lawbot/"; AC = B + "12_Ambulance-Chaser_Lawbot/"


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]


def ren(s):
    return (s.replace(AC, D).replace("12_Ambulance-Chaser_Lawbot", "14_Spin-Doctor_Lawbot").replace("AmbulanceChaser", "SpinDoctor")
            .replace("AC_", "SD_").replace("ac_ref_", "sd_ref_").replace('"ac_rig.json"', '"sd_rig.json"')
            .replace("ACCam", "SDCam").replace("ACSun", "SDSun").replace("ACFill", "SDFill"))


ac = open(AC + "build.py").read()
i_head = ac.index("# ---------------------------------------------------------------- head: a tall slab under a white top hat")
i_front = ac.index("# ---------------------------------------------------------------- suit front")
p1, p3 = ren(ac[:i_head]), ren(ac[i_front:])
p1 = rep(p1, "K = 4.35 / 5.29", "K = 5.65 / 5.29")
p1 = rep(p1, "BODY_S = 4.35 / 4.5", "BODY_S = 5.65 / 4.5")
p1 = rep(p1, 'M_PLATE = pmat("SD_Plate", (0.56, 0.51, 0.80)', 'M_PLATE = pmat("SD_Plate", (0.36, 0.72, 0.58)')
p1 = rep(p1, 'M_HAND = pmat("SD_Hand", (0.56, 0.50, 0.78)', 'M_HAND = pmat("SD_Hand", (0.36, 0.72, 0.58)')
p1 = rep(p1, 'M_HAIR = pmat("SD_Hair", (0.012, 0.011, 0.012)', 'M_HAIR = pmat("SD_Hair", (0.20, 0.095, 0.055)')
p1 = rep(p1, 'M_LID = pmat("SD_Lid", (0.40, 0.33, 0.66)', 'M_MIRROR = pmat("SD_Mirror", (0.72, 0.72, 0.74), 0.18, 0.95, var=0.15, grime=0.2, rvar=0.08)\nM_LID = pmat("SD_Lid", (0.27, 0.58, 0.46)')
p1 = rep(p1, 'M_IRISRING = pmat("SD_IrisRing", (0.22, 0.10, 0.04)', 'M_IRISRING = pmat("SD_IrisRing", (0.10, 0.30, 0.20)')
open(D + "build.py", "w").write(p1 + open(D + "work/head_part.py").read() + p3)
open(D + "rig.py", "w").write(ren(open(AC + "rig.py").read()))
open(D + "run.py", "w").write(ren(open(AC + "run.py").read()).replace("ac_rig", "sd_rig"))
c = ren(open(AC + "check.py").read())
c = cut(c, 'shot("front"', "(sc.camera, sc.render.resolution_x", '''shot("front", (0, -30, 4.0), (0, 0, 4.0), 3.6, 8.2)
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
''')
c = c.replace("PXU = 190.0", "PXU = 150.0")
open(D + "check.py", "w").write(c)
open(D + "bake.py", "w").write(open(AC + "bake.py").read().replace("12_Ambulance-Chaser_Lawbot", "14_Spin-Doctor_Lawbot").replace("AC_Baked", "SD_Baked"))
s = open(D + "build_bam.py").read()
if "'sd':" not in s:
    s = rep(s, "'bs': 4.5 / 6.06}", "'bs': 4.5 / 6.06, 'sd': 5.65 / 5.29}"); open(D + "build_bam.py", "w").write(s)
print("ok")
