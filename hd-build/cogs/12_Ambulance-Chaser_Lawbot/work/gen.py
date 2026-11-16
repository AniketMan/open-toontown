B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D = B + "12_Ambulance-Chaser_Lawbot/"; BS = B + "10_Bloodsucker_Lawbot/"


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]


def ren(s):
    return (s.replace(BS, D).replace("10_Bloodsucker_Lawbot", "12_Ambulance-Chaser_Lawbot").replace("Bloodsucker", "AmbulanceChaser")
            .replace("BS_", "AC_").replace("b_ref_", "ac_ref_").replace('"b_rig.json"', '"ac_rig.json"')
            .replace("BSCam", "ACCam").replace("BSSun", "ACSun").replace("BSFill", "ACFill"))


bs = open(BS + "build.py").read()
i_head = bs.index("# ---------------------------------------------------------------- head: a tall slab with rounded corners")
i_front = bs.index("# ---------------------------------------------------------------- suit front")
p1, p3 = ren(bs[:i_head]), ren(bs[i_front:])
p1 = rep(p1, "K = 4.375 / 5.29", "K = 4.35 / 5.29")
p1 = rep(p1, "BODY_S = 4.375 / 4.5", "BODY_S = 4.35 / 4.5")
p1 = rep(p1, 'M_PLATE = pmat("AC_Plate", (0.80, 0.76, 0.68)', 'M_PLATE = pmat("AC_Plate", (0.56, 0.51, 0.80)')
p1 = rep(p1, 'M_HAND = pmat("AC_Hand", (0.82, 0.80, 0.76)', 'M_HAND = pmat("AC_Hand", (0.56, 0.50, 0.78)')
p1 = rep(p1, 'M_HAIR = pmat("AC_Hair", (0.03, 0.011, 0.012)', 'M_HAIR = pmat("AC_Hair", (0.012, 0.011, 0.012)')
p1 = rep(p1, 'M_HAT = pmat("AC_Hat", (0.014, 0.012, 0.011), 0.7', 'M_HAT = pmat("AC_Hat", (0.84, 0.83, 0.80), 0.45')
p1 = rep(p1, 'M_LID = pmat("AC_Lid", (0.27, 0.13, 0.48)', 'M_LID = pmat("AC_Lid", (0.40, 0.33, 0.66)')
p1 = rep(p1, 'M_IRISRING = pmat("AC_IrisRing", (0.50, 0.38, 0.10)', 'M_IRISRING = pmat("AC_IrisRing", (0.22, 0.10, 0.04)')
# white shirt cuffs showing between sleeve and hand, as on the sheets and the original
x = "    xloft(sleeves, BAND, seg=22, sx=s)\n"
p1 = rep(p1, x, x + "    xloft(cuffw, [(2.97, 0.14, AZ, 0.205, 0.185), (3.14, 0.14, AZ, 0.20, 0.18), (3.14, 0.14, AZ, 0.14, 0.13)], seg=20, sx=s, caps=(False, False))\n")
p1 = rep(p1, "sleeves, plate_r, joint_r, pewter_r, stitch_r = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()",
         "sleeves, plate_r, joint_r, pewter_r, stitch_r = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()\ncuffw = bmesh.new()")
p1 = rep(p1, 'new_obj("AC_Sleeves", sleeves, M_SUIT, 60, rest=True)', "tag(cuffw, '@sleeve')\nnew_obj(\"AC_ShirtCuffs\", cuffw, M_SHIRT, 40, rest=True)\nnew_obj(\"AC_Sleeves\", sleeves, M_SUIT, 60, rest=True)")
open(D + "build.py", "w").write(p1 + open(D + "work/head_part.py").read() + p3)
r = ren(open(BS + "rig.py").read())
r = rep(r, 'REST_FN = {', 'REST_FN = {"AC_ShirtCuffs": sleeve_weights, ')
open(D + "rig.py", "w").write(r)
open(D + "run.py", "w").write(ren(open(BS + "run.py").read()).replace("bs_rig", "ac_rig"))
c = ren(open(BS + "check.py").read())
c = cut(c, 'shot("headfront"', 'shot("chestfront"', '''shot("headfront", (0, -20, 5.46), (0, 0, 5.46), 1.3, 2.2, k=4)
shot("headleft", (20, 0, 5.46), (0, 0, 5.46), 1.3, 2.2, k=4)
shot("headback", (0, 20, 5.46), (0, 0, 5.46), 1.3, 2.2, k=4)
shot("head34", (-10, -16, 7.2), (0, 0, 5.42), 1.3, 2.2, k=4)
shot("headrear", (-12, 14, 6.6), (0, 0, 5.42), 1.3, 2.2, k=4)
shot("face", (3, -19, 5.6), (0, -0.2, 5.3), 0.8, 0.7, k=6)
shot("mouth", (4, -18, 4.6), (0.0, -0.2, 4.85), 0.8, 0.7, k=6)
shot("medal", (2.5, -19, 4.6), (0.0, -0.35, 3.76), 0.75, 0.9, k=8)
''')
open(D + "check.py", "w").write(c)
open(D + "bake.py", "w").write(open(BS + "bake.py").read().replace("10_Bloodsucker_Lawbot", "12_Ambulance-Chaser_Lawbot").replace("BS_Baked", "AC_Baked"))
s = open(D + "build_bam.py").read()
if "'ac':" not in s:
    s = rep(s, "'b': 4.375 / 5.29}", "'b': 4.375 / 5.29, 'ac': 4.35 / 5.29}"); open(D + "build_bam.py", "w").write(s)
print("ok")
