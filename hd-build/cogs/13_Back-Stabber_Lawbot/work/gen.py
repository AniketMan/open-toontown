B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D = B + "13_Back-Stabber_Lawbot/"; DT = B + "11_Double-Talker_Lawbot/"


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]


def ren(s):
    return (s.replace(DT, D).replace("11_Double-Talker_Lawbot", "13_Back-Stabber_Lawbot").replace("DoubleTalker", "BackStabber")
            .replace("Double Talker", "Back Stabber").replace("DT_", "BK_").replace("dt_ref_", "bk_ref_")
            .replace('"dt_rig.json"', '"bs_rig.json"').replace("DTCam", "BKCam").replace("DTSun", "BKSun").replace("DTFill", "BKFill"))


dt = open(DT + "build.py").read()
i_head = dt.index("# ---------------------------------------------------------------- head: a faceted two-tier block")
i_front = dt.index("# ---------------------------------------------------------------- suit front")
p1, p3 = ren(dt[:i_head]), ren(dt[i_front:])
p1 = rep(p1, "K = 4.25 / 6.06", "K = 4.5 / 6.06")
p1 = rep(p1, "BODY_S = 4.25 / 6.5", "BODY_S = 4.5 / 6.5")
p1 = rep(p1, 'M_PLATE = pmat("BK_Plate", (0.60, 0.58, 0.79)', 'M_PLATE = pmat("BK_Plate", (0.40, 0.24, 0.70)')
p1 = rep(p1, 'M_LID = pmat("BK_Lid", (0.42, 0.34, 0.66)', 'M_LID = pmat("BK_Lid", (0.30, 0.17, 0.56)')
p1 = rep(p1, 'M_HAIR = pmat("BK_Hair", (0.40, 0.05, 0.02)', 'M_HAIR = pmat("BK_Hair", (0.36, 0.04, 0.03)')
p3 = rep(p3, "        if v.co.z < 4.2:                                         # the coat is longer on this cog: hem at 2.19, not 2.28\n            v.co.z = 4.2 - (4.2 - v.co.z) * 1.18\n", "")
x = "pewter_r, stitch_r = both_arms(sleeve_buttons), both_arms(sleeve_stitch)"
p1 = rep(p1, x, '''def shirt_cuff(bm):                                             # white shirt cuff showing between sleeve and hand
    xloft(bm, [(3.60, 0.07, AZ, 0.31, 0.30), (3.80, 0.07, AZ, 0.30, 0.29), (3.80, 0.07, AZ, 0.20, 0.19)], seg=20, caps=(False, False))


_cuffs = both_arms(shirt_cuff)
tag(_cuffs, '@sleeve')
new_obj("BK_ShirtCuffs", _cuffs, M_SHIRT, 40, rest=True)
''' + x)
open(D + "build.py", "w").write(p1 + open(D + "work/head_part.py").read() + p3)
open(D + "rig.py", "w").write(rep(ren(open(DT + "rig.py").read()), "REST_FN = {", 'REST_FN = {"BK_ShirtCuffs": sleeve_weights, '))
open(D + "run.py", "w").write(ren(open(DT + "run.py").read()).replace("dt_rig", "bk_rig"))
c = ren(open(DT + "check.py").read())
c = cut(c, 'shot("front"', "(sc.camera, sc.render.resolution_x", '''shot("front", (0, -30, 3.4), (0, 0, 3.4), 4.4, 7.0)
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
''')
open(D + "check.py", "w").write(c)
open(D + "bake.py", "w").write(open(DT + "bake.py").read().replace("11_Double-Talker_Lawbot", "13_Back-Stabber_Lawbot").replace("DT_Baked", "BK_Baked"))
s = open(D + "build_bam.py").read()
if "'bs':" not in s:
    s = rep(s, "'ac': 4.35 / 5.29}", "'ac': 4.35 / 5.29, 'bs': 4.5 / 6.06}"); open(D + "build_bam.py", "w").write(s)
print("ok")
