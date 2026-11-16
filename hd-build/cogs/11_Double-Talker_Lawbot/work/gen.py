B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D = B + "11_Double-Talker_Lawbot/"; HH = B + "06_Head-Hunter_Bossbot/"; BF = B + "09_Bottom-Feeder_Lawbot/"


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]


def ren(s):
    return (s.replace(HH, D).replace("06_Head-Hunter_Bossbot", "11_Double-Talker_Lawbot").replace("HeadHunter", "DoubleTalker")
            .replace("Head Hunter", "Double Talker").replace("HH_", "DT_").replace("hh_ref_", "dt_ref_")
            .replace('"hh_rig.json"', '"dt_rig.json"').replace("HHCam", "DTCam").replace("HHSun", "DTSun").replace("HHFill", "DTFill"))


hh = open(HH + "build.py").read()
i_head = hh.index("# ---------------------------------------------------------------- head: a heavy block")
i_front = hh.index("# ---------------------------------------------------------------- suit front")
p1, p3 = ren(hh[:i_head]), ren(hh[i_front:])

p1 = rep(p1, "K = 6.5 / 6.06          # suit A scale for this cog",
         "K = 4.25 / 6.06         # suit A scale for this cog\n"
         "# The coat is the Head Hunter's cut (same body, suit A). It is laid out at his size and brought to this cog's at the end.\n"
         "BODY_S = 4.25 / 6.5")
p1 = rep(p1, "def ref(name, loc, rot):\n", "def ref(name, loc, rot):\n    import os\n    if not os.path.exists(SP + \"refplanes/dt_ref_%s.png\" % name):\n        return\n")
p1 = rep(p1, 'M_SUIT = pmat("DT_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18)',
         'M_SUIT = pmat("DT_Suit", (0.028, 0.032, 0.085), 0.88, var=0.35, grime=0.12, stripe=(0.045, 0.05, 0.12)')
p1 = rep(p1, 'M_LINING = pmat("DT_Lining", (0.05, 0.012, 0.01)', 'M_LINING = pmat("DT_Lining", (0.012, 0.013, 0.03)')
p1 = rep(p1, 'M_STITCH = pmat("DT_Stitch", (0.66, 0.50, 0.42)', 'M_STITCH = pmat("DT_Piping", (0.22, 0.035, 0.27)')
p1 = rep(p1, 'M_PLATE = pmat("DT_Plate", (0.78, 0.63, 0.53)', 'M_PLATE = pmat("DT_Plate", (0.60, 0.58, 0.79)')
p1 = rep(p1, 'M_HAND = pmat("DT_Hand", (0.76, 0.60, 0.50)', 'M_HAND = pmat("DT_Hand", (0.56, 0.50, 0.78)')
p1 = rep(p1, 'M_HAIR = pmat("DT_Hair", (0.012, 0.011, 0.011)', 'M_HAIR = pmat("DT_Hair", (0.40, 0.05, 0.02)')
p1 = rep(p1, 'M_PEWTER = pmat("DT_Pewter", (0.60, 0.48, 0.40)', 'M_PEWTER = pmat("DT_Pewter", (0.40, 0.41, 0.46)')
p1 = rep(p1, 'M_EYE = pmat("DT_Eye", (0.45, 0.38, 0.30)', 'M_EYE = pmat("DT_Eye", (0.90, 0.88, 0.80)')
p1 = rep(p1, "\n\ndef merge(dst, src, weld=0.0):",
         '\nM_LID = pmat("DT_Lid", (0.42, 0.34, 0.66), 0.4, 0.1, var=0.25, grime=0.3, bump=0.08, bscale=40, rvar=0.12, coat=0.2)\n'
         'M_FANG = pmat("DT_Teeth", (0.92, 0.90, 0.84), 0.25, var=0.1, grime=0.2, coat=0.5)\n'
         'M_BOW = pmat("DT_Bow", (0.60, 0.04, 0.03), 0.6, var=0.25, weave=0.5, sheen=0.3, rvar=0.1)\n'
         'M_BROW = pmat("DT_Dark", (0.035, 0.03, 0.07), 0.4, 0.1, var=0.3)\n'
         'M_IRISRING = pmat("DT_IrisRing", (0.10, 0.14, 0.30), 0.2, var=0.2, coat=0.6)\n\n\n'
         'def stud(bm, p, n, r=0.036):\n'
         '    lathe(bm, p, n, [(0.0, r), (0.4 * r, r), (0.78 * r, 0.5 * r), (0.9 * r, 0.05 * r)], seg=8)\n\n\n'
         'def merge(dst, src, weld=0.0):')
# the chin sits low on this cog: collar and shirt band come down so the head does not sink into them
p1 = rep(p1, "COLLAR = [fb(6.52, 0.42, -0.36, 0.47), fb(6.68, 0.43, -0.37, 0.50), fb(6.67, 0.56, -0.45, 0.60), fb(6.525, 0.80, -0.55, 0.70)]",
         "COLLAR = [fb(6.44, 0.42, -0.36, 0.47), fb(6.56, 0.43, -0.37, 0.50), fb(6.55, 0.56, -0.45, 0.60), fb(6.44, 0.80, -0.55, 0.70)]")
p1 = rep(p1, "math.sin(t), 6.565)))", "math.sin(t), 6.48)))")
p1 = cut(p1, "def sleeve_buttons(bm):", "def sleeve_stitch(bm):",
         "def sleeve_buttons(bm):                                          # studs round the band\n"
         "    for k in range(8):\n"
         "        a_ = 2 * math.pi * (k + 0.5) / 8\n"
         "        _, cy, cz, ry, rz = BAND[0]\n"
         "        n = Vector((0, math.cos(a_), math.sin(a_)))\n"
         "        stud(bm, Vector((3.43, cy + (ry + 0.004) * n.y, cz + (rz + 0.004) * n.z)), n, 0.04)\n\n\n")
p1 = rep(p1, "tube(bm, ring, [0.009] * len(ring), seg=4)", "tube(bm, ring, [0.016] * len(ring), seg=5)")
x = "pewter_r, stitch_r = both_arms(sleeve_buttons), both_arms(sleeve_stitch)"
p1 = rep(p1, x, '''# shoulder caps: a studded, piped plate of cloth over the top of each sleeve head, as on the sheet
CAP = [(SX - 0.12, 0.11, AZ, 0.41, 0.38), (SX - 0.03, 0.11, AZ, 0.475, 0.445), (SX + 0.08, 0.11, AZ, 0.495, 0.475), (SX + 0.24, 0.105, AZ, 0.50, 0.49),
       (SX + 0.40, 0.10, AZ, 0.50, 0.49)]
CAP_A = [-25 + 230 * i / 20 for i in range(21)]


def cap_pt(st, a_, lift):
    x_, cy, cz, ry, rz = st
    return Vector((x_, cy + (ry + lift) * math.cos(math.radians(a_)), cz + (rz + lift) * math.sin(math.radians(a_))))


def cap_cloth(bm):
    grid(bm, [[cap_pt(st, a_, 0.02) for a_ in CAP_A] for st in CAP])


def cap_studs(bm):
    for a_ in (0, 30, 60, 90, 120, 150, 180):
        n = Vector((0, math.cos(math.radians(a_)), math.sin(math.radians(a_))))
        stud(bm, cap_pt(CAP[4], a_, 0.04) - Vector((0.08, 0, 0)), n, 0.04)


def cap_pipe(bm):
    edge = [cap_pt(st, CAP_A[0], 0.04) for st in CAP] + [cap_pt(CAP[4], a_, 0.04) for a_ in CAP_A] + [cap_pt(st, CAP_A[-1], 0.04) for st in reversed(CAP)]
    tube(bm, edge, [0.016] * len(edge), seg=5)


_caps = {}
for _n, _f in (("cloth", cap_cloth), ("studs", cap_studs), ("pipe", cap_pipe)):
    _caps[_n] = both_arms(_f)
    tag(_caps[_n], '@sleeve')
_o = new_obj("DT_ShoulderCaps", _caps["cloth"], M_SUIT, 60, rest=True)
_s = _o.modifiers.new("Cloth thickness", 'SOLIDIFY')
_s.thickness, _s.offset = 0.04, 0.0
new_obj("DT_ShoulderCapStuds", _caps["studs"], M_PEWTER, 32, rest=True)
new_obj("DT_ShoulderCapPiping", _caps["pipe"], M_STITCH, 40, rest=True)
''' + x)
anchor = 'new_obj("DT_Trousers", bm, M_SUIT, 60, rest=True)'
p1 = rep(p1, anchor, anchor + '''
# studded band round each trouser hem, piped along its edges
hemb, studs_r, pipe_r = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    cx = HIP[s]
    rx, ry, z0, z1 = min(0.33, cx - 0.012), 0.465, 0.42, 0.86
    loft(hemb, [(z0 - 0.005, cx, 0.0, rx + 0.016, ry + 0.016), (z1, cx, 0.0, rx + 0.016, ry + 0.016)], seg=20, sx=s, caps=(False, False), centres=(270, 90))
    for k in range(8):
        a_ = 2 * math.pi * (k + 0.5) / 8
        nrm = Vector((s * math.cos(a_) / rx, math.sin(a_) / ry, 0)).normalized()
        stud(studs_r, Vector((s * (cx + (rx + 0.022) * math.cos(a_)), (ry + 0.022) * math.sin(a_), (z0 + z1) / 2)), nrm, 0.04)
    for zz in (z0 + 0.018, z1 - 0.018):
        ring = [Vector((s * (cx + (rx + 0.022) * math.cos(math.radians(a_))), (ry + 0.022) * math.sin(math.radians(a_)), zz)) for a_ in range(0, 361, 18)]
        tube(pipe_r, ring, [0.016] * len(ring), seg=5)
    for _b in (hemb, studs_r, pipe_r):
        tag(_b, '@legL' if s > 0 else '@legR')
new_obj("DT_TrouserBands", hemb, M_SUIT, 60, rest=True)
new_obj("DT_LimbStuds", studs_r, M_PEWTER, 32, rest=True)
new_obj("DT_TrouserPiping", pipe_r, M_STITCH, 40, rest=True)''')

# ---- suit front
p3 = rep(p3, "loft(shirt, [fb(6.40, 0.40, -0.32, 0.40), fb(6.62, 0.36, -0.30, 0.36), fb(6.62, 0.34, -0.28, 0.34), fb(6.43, 0.35, -0.29, 0.35)],",
         "loft(shirt, [fb(6.34, 0.40, -0.32, 0.40), fb(6.52, 0.36, -0.30, 0.36), fb(6.52, 0.34, -0.28, 0.34), fb(6.37, 0.35, -0.29, 0.35)],")
p3 = rep(p3, "[(s * 0.04, s * 0.36, 6.56), (s * 0.10, s * 0.40, 6.42), (s * 0.22, s * 0.33, 6.25)]", "[(s * 0.04, s * 0.36, 6.48), (s * 0.10, s * 0.40, 6.36), (s * 0.22, s * 0.33, 6.22)]")
p3 = cut(p3, "patch(tie, SS, [(-0.10, 0.10, 6.50)", "panel(placket, TS,", '''# bow tie: a knot and two wings on the shirt under the chin, dotted as on the original; the zip runs down from it
exec(compile(open(SP + "../medallion.py").read(), "medallion.py", "exec"), globals())
bowdots, zipteeth, ziptape = bmesh.new(), bmesh.new(), bmesh.new()
bow_c = surf(SS, 0.0, 6.33, 0.075)
bmesh.ops.create_uvsphere(tie, u_segments=14, v_segments=8, radius=1.0, matrix=Matrix.Translation(bow_c) @ Matrix.Diagonal((0.055, 0.055, 0.07, 1.0)))
BOW = [(0.023, 0.024, 0.028), (0.077, 0.034, 0.055), (0.153, 0.041, 0.089), (0.237, 0.041, 0.107), (0.278, 0.03, 0.10), (0.29, 0.012, 0.076)]
for sdx in (-1, 1):
    xloft(tie, [(x_, bow_c.y + 0.009, bow_c.z, ry_, rz_) for x_, ry_, rz_ in BOW], seg=16, sx=sdx)
    for ddx, ddz in ((0.10, 0.018), (0.16, -0.04), (0.17, 0.046), (0.232, 0.003), (0.24, -0.06), (0.245, 0.064)):
        puck(bowdots, bow_c + Vector((sdx * ddx, 0.009 - 0.0405, ddz)), (0, -1, 0), 0.013, 0.006, seg=8)
zipper(zipteeth, ziptape, SS, 6.20, 5.50, 1.55)

''')
p3 = rep(p3, "panel(placket, TS, [(-0.03, 3.49), (0.20, 3.49), (0.20, 5.25), (0.07, 5.56), (-0.03, 5.56)]",
         "panel(placket, TS, [(-0.14, 3.49), (0.14, 3.49), (0.14, 5.30), (0.05, 5.56), (-0.05, 5.56), (-0.14, 5.30)]")
p3 = cut(p3, "for z in (4.90, 4.65, 4.38, 4.10, 3.82):", "tag(pewter, '@jacket')", '''for z in (4.98, 4.72, 4.46, 4.20, 3.94):          # a column of studs down each side of the button stand
    for sx_ in (-1, 1):
        p = surf(TS, sx_ * 0.075, z, 0.026)
        stud(pewter, p, (surf(TS, sx_ * 0.075, z, 1.0) - surf(TS, sx_ * 0.075, z, 0.0)).normalized(), 0.04)
''')
p3 = cut(p3, "edge = [(0.175, 5.22", "tube(stitch, COLLAR_EDGE", '''for sx_ in (-1, 1):
    edge = [(sx_ * 0.13, 5.24 - (5.24 - 3.74) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.032) for x, z in edge], [SR] * len(edge), seg=5)
''')
p3 = rep(p3, "SR = 0.008", "SR = 0.014")
p3 = rep(p3, "hs = [ring_pt(TS, 3.665, a, 0.033)[0] for a in HB]\ntube(stitch, hs, [SR] * len(hs), seg=4)",
         "for zz in (3.665, 3.51):\n    hs = [ring_pt(TS, zz, a, 0.033)[0] for a in HB]\n    tube(stitch, hs, [SR] * len(hs), seg=5)")
p3 = cut(p3, "for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):", "\n\ndef roll_lift",
         "for a in range(-80, 262, 20):\n    p, n = ring_pt(TS, 3.58, a, 0.028)\n    stud(pewter, p, n, 0.042)\n")
x = "    o = [(s * x, z) for x, z in flap]\n    panel(pockets, TS, o, flat_lift, cuts=2)\n    topstitch(stitch, TS, o, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)\n"
p3 = rep(p3, x, '''    for xs, zs in ((0.15, 5.715), (0.30, 5.78), (0.45, 5.845), (0.60, 5.905), (0.69, 5.99), (0.60, 6.11), (0.72, 6.28), (0.75, 6.36), (0.65, 6.42)):
        p = surf(TS, s * xs, zs, roll_lift(xs, zs) + 0.036)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0) - surf(TS, s * xs, zs, 0.0)).normalized(), 0.036)
''')
p3 = rep(p3, "topstitch(stitch, TS, breast, lambda x, z: 0.037, inset=0.026, step=0.07, radius=SR)\n", "")
p3 = cut(p3, "    for outline, back, pts in ((", "        o = [(s * x, z) for x, z in outline]\n        panel(straps", '''    # shoulder yokes: a broad studded plate of cloth over the front of each shoulder and a broader one across each shoulder blade
    for outline, back, pts in (([(0.90, 6.33), (1.15, 6.36), (1.62, 6.10), (1.66, 5.86), (1.35, 5.74), (1.02, 5.84), (0.90, 6.02)], False,
                                ((1.02, 5.95), (1.20, 5.84), (1.42, 5.83), (1.57, 5.95), (1.05, 6.22), (1.30, 6.20))),
                               ([(0.55, 6.38), (1.05, 6.40), (1.62, 6.10), (1.66, 5.80), (1.30, 5.66), (0.90, 5.80), (0.62, 6.06)], True,
                                ((0.74, 5.98), (0.95, 5.84), (1.20, 5.75), (1.45, 5.78), (1.58, 5.92), (0.80, 6.28), (1.10, 6.27), (1.40, 6.13)))):
''')
p3 = rep(p3, "0.23, 'tie')", "0.34, 'gavel')")
p3 = rep(p3, 'new_obj("DT_Tie", tie, M_TIE, 30, outward=True, thickness=0.027)', 'new_obj("DT_BowTie", tie, M_BOW, 50)')
p3 = rep(p3, 'new_obj("DT_Cord", cord, M_JOINT, 40)', 'new_obj("DT_Cord", cord, M_STEEL, 40)\nnew_obj("DT_BowDots", bowdots, M_SHIRT, 40)\nnew_obj("DT_Zipper", zipteeth, M_STEEL, 35)\nnew_obj("DT_ZipTape", ziptape, M_LINING, 30, outward=True, thickness=0.006)')
i_cam = p3.index('cam = bpy.data.objects.new("DTCam"')
p3 = p3[:i_cam] + '''# The coat and everything sewn to it were laid out at the Head Hunter's size; bring them to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        if v.co.z < 4.2:                                         # the coat is longer on this cog: hem at 2.19, not 2.28
            v.co.z = 4.2 - (4.2 - v.co.z) * 1.18
        v.co *= BODY_S
    for m in ob.modifiers:
        if m.type == 'SOLIDIFY' and hg is None:
            m.thickness *= BODY_S
    ob.data.update()

''' + p3[i_cam:]
open(D + "build.py", "w").write(p1 + open(D + "work/head_part.py").read() + p3)

r = ren(open(HH + "rig.py").read())
r = rep(r, '"DT_Tie": "@shirt"', '"DT_Tie": "@shirt", "DT_BowTie": "@shirt", "DT_BowDots": "@shirt", "DT_Zipper": "@shirt", "DT_ZipTape": "@shirt"')
r = rep(r, 'REST_FN = {', 'REST_FN = {"DT_ShoulderCaps": sleeve_weights, "DT_ShoulderCapStuds": sleeve_weights, "DT_ShoulderCapPiping": sleeve_weights, "DT_TrouserBands": trouser_weights, "DT_LimbStuds": trouser_weights, "DT_TrouserPiping": trouser_weights, ')
open(D + "rig.py", "w").write(r)
open(D + "run.py", "w").write(open(BF + "run.py").read().replace(BF, D).replace("BF_Rig", "DT_Rig").replace("bf_rig", "dt_rig"))
c = ren(open(HH + "check.py").read())
c = cut(c, 'shot("front"', "(sc.camera, sc.render.resolution_x", '''shot("front", (0, -30, 2.9), (0, 0, 2.9), 4.0, 6.0)
shot("left", (30, 0, 2.9), (0, 0, 2.9), 3.0, 6.0)
shot("right", (-30, 0, 2.9), (0, 0, 2.9), 3.0, 6.0)
shot("back", (0, 30, 2.9), (0, 0, 2.9), 4.0, 6.0)
shot("headfront", (0, -20, 5.05), (0, 0, 5.05), 1.5, 1.7, k=4)
shot("headleft", (20, 0, 5.05), (0, 0, 5.05), 1.3, 1.7, k=4)
shot("headright", (-20, 0, 5.05), (0, 0, 5.05), 1.3, 1.7, k=4)
shot("headback", (0, 20, 5.05), (0, 0, 5.05), 1.5, 1.7, k=4)
shot("head34", (-12, -14, 6.6), (0, 0, 5.0), 1.5, 1.7, k=4)
shot("headrear", (12, 14, 6.2), (0, 0, 5.0), 1.5, 1.7, k=4)
shot("chestfront", (0, -20, 3.5), (0, 0, 3.5), 2.8, 2.2, k=2)
shot("chestback", (0, 20, 3.5), (0, 0, 3.5), 2.8, 2.2, k=2)
shot("neck", (4, -17, 6.6), (0, -0.2, 4.2), 1.6, 1.1, k=3)
shot("above", (0, -7, 22), (0, -0.1, 4.2), 3.4, 2.2, k=2)
shot("medal", (2.5, -19, 4.3), (0.0, -0.5, 3.47), 0.9, 1.0, k=7)
shot("walkfront", (0, -30, 2.9), (0, 0, 2.9), 4.4, 6.0)
shot("walkleft", (30, 0, 2.9), (0, 0, 2.9), 4.4, 6.0)
shot("walkback", (0, 30, 2.9), (0, 0, 2.9), 4.4, 6.0)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 30, -math.cos(a) * 30, 3.6), (0, 0, 2.9), 4.0, 6.0, ortho=False)
''')
c = c.replace("PXU = 145.0", "PXU = 190.0")
open(D + "check.py", "w").write(c)
open(D + "bake.py", "w").write(open(HH + "bake.py").read().replace("06_Head-Hunter_Bossbot", "11_Double-Talker_Lawbot").replace("HH_Baked", "DT_Baked").replace("(0.20, 0.052, 0.036, 1)", "(0.028, 0.032, 0.085, 1)"))
s = open(D + "build_bam.py").read()
if "'dt':" not in s:
    s = rep(s, "'b': 4.375 / 5.29}", "'b': 4.375 / 5.29, 'dt': 4.25 / 6.06}"); open(D + "build_bam.py", "w").write(s)
print("ok")
