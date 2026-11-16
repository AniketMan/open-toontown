B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D = B + "10_Bloodsucker_Lawbot/"; DS = B + "05_Downsizer_Bossbot/"; BF = B + "09_Bottom-Feeder_Lawbot/"


def rep(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b)


def cut(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]


def ren(s):
    return (s.replace(DS, D).replace("05_Downsizer_Bossbot", "10_Bloodsucker_Lawbot").replace("Downsizer", "Bloodsucker")
            .replace("DS_", "BS_").replace("ds_ref_", "b_ref_").replace('"ds_rig.json"', '"b_rig.json"')
            .replace("DSCam", "BSCam").replace("DSSun", "BSSun").replace("DSFill", "BSFill"))


ds = open(DS + "build.py").read()
i_head = ds.index("# ---------------------------------------------------------------- head: a tall tapering shell")
i_front = ds.index("# ---------------------------------------------------------------- suit front")
p1, p3 = ren(ds[:i_head]), ren(ds[i_front:])

p1 = rep(p1, "K = 4.5 / 5.29          # suit B scale for this cog",
         "K = 4.375 / 5.29        # suit B scale for this cog\n"
         "# The coat is the Downsizer's cut (same body, suit B). It is laid out at his size and brought to this cog's at the end.\n"
         "BODY_S = 4.375 / 4.5")
p1 = rep(p1, "def ref(name, loc, rot):\n", "def ref(name, loc, rot):\n    import os\n    if not os.path.exists(SP + \"refplanes/b_ref_%s.png\" % name):\n        return\n")
p1 = rep(p1, 'M_SUIT = pmat("BS_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18)',
         'M_SUIT = pmat("BS_Suit", (0.028, 0.032, 0.085), 0.88, var=0.35, grime=0.12, stripe=(0.045, 0.05, 0.12)')
p1 = rep(p1, 'M_STITCH = pmat("BS_Stitch", (0.66, 0.50, 0.42)', 'M_STITCH = pmat("BS_Piping", (0.22, 0.035, 0.27)')
p1 = rep(p1, 'M_PLATE = pmat("BS_Plate", (0.33, 0.50, 0.44)', 'M_PLATE = pmat("BS_Plate", (0.80, 0.76, 0.68)')
p1 = rep(p1, 'M_HAND = pmat("BS_Hand", (0.76, 0.60, 0.50)', 'M_HAND = pmat("BS_Hand", (0.82, 0.80, 0.76)')
p1 = rep(p1, 'M_HAIR = pmat("BS_Hair", (0.012, 0.011, 0.011)', 'M_HAIR = pmat("BS_Hair", (0.03, 0.011, 0.012)')
p1 = rep(p1, 'M_PEWTER = pmat("BS_Pewter", (0.60, 0.48, 0.40)', 'M_PEWTER = pmat("BS_Pewter", (0.40, 0.41, 0.46)')
p1 = rep(p1, 'M_EYE = pmat("BS_Eye", (0.80, 0.72, 0.58)', 'M_EYE = pmat("BS_Eye", (0.90, 0.88, 0.80)')
p1 = rep(p1, 'plate, joint, steel, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()',
         'M_LID = pmat("BS_Lid", (0.27, 0.13, 0.48), 0.4, 0.1, var=0.25, grime=0.3, bump=0.08, bscale=40, rvar=0.12, coat=0.2)\n'
         'M_FANG = pmat("BS_Fang", (0.92, 0.90, 0.84), 0.25, var=0.1, grime=0.2, coat=0.5)\n'
         'M_BOW = pmat("BS_Bow", (0.60, 0.04, 0.03), 0.6, var=0.25, weave=0.5, sheen=0.3, rvar=0.1)\n'
         'M_BROW = pmat("BS_Dark", (0.05, 0.035, 0.07), 0.4, 0.1, var=0.3)\n'
         'M_IRISRING = pmat("BS_IrisRing", (0.50, 0.38, 0.10), 0.2, var=0.2, coat=0.6)\n'
         'M_EMBLEM = pmat("BS_Emblem", (0.06, 0.063, 0.08), 0.35, 0.9, var=0.2, grime=0.3, bump=0.08, bscale=80, rvar=0.15)\n'
         'plate, joint, steel, pewter = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()\n\n\n'
         'def stud(bm, p, n, r=0.024):\n'
         '    lathe(bm, p, n, [(0.0, r), (0.4 * r, r), (0.78 * r, 0.5 * r), (0.9 * r, 0.05 * r)], seg=8)')
p1 = rep(p1, "SHIRT_IN = {4.05: 0.07,", "SHIRT_IN = {3.80: 0.07, 4.05: 0.07,")
p1 = cut(p1, "    for x in (2.72, 2.86):", "    for x in (2.585, 2.975):",
         "    for k in range(8):                                           # studs round the band\n"
         "        a_ = 2 * math.pi * (k + 0.5) / 8\n"
         "        _, cy, cz, ry, rz = BAND[0]\n"
         "        n = Vector((0, math.cos(a_), math.sin(a_)))\n"
         "        stud(pewter_r, Vector((s * 2.78, cy + (ry + 0.003) * n.y, cz + (rz + 0.003) * n.z)), n, 0.026)\n")
p1 = rep(p1, "tube(stitch_r, ring, [0.0065] * len(ring), seg=4)", "tube(stitch_r, ring, [0.011] * len(ring), seg=5)")
anchor = 'new_obj("BS_Trousers", bm, M_SUIT, 60, rest=True)'
p1 = rep(p1, anchor, anchor + '''
# studded band round each trouser hem, piped along its top
hemb, studs_r, pipe_r = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    z0, cx, cy, rx, ry = LEG[0]
    z1 = 0.50
    loft(hemb, [(z0 - 0.005, cx, cy, rx + 0.012, ry + 0.012), (z1, cx, cy, rx + 0.012, ry + 0.012)], seg=20, sx=s, caps=(False, False), centres=(270, 90))
    for k in range(8):
        a_ = 2 * math.pi * (k + 0.5) / 8
        nrm = Vector((s * math.cos(a_) / rx, math.sin(a_) / ry, 0)).normalized()
        stud(studs_r, Vector((s * (cx + (rx + 0.016) * math.cos(a_)), cy + (ry + 0.016) * math.sin(a_), (z0 + z1) / 2)), nrm, 0.026)
    for zz in (z0 + 0.012, z1 - 0.012):
        ring = [Vector((s * (cx + (rx + 0.016) * math.cos(math.radians(a_))), cy + (ry + 0.016) * math.sin(math.radians(a_)), zz)) for a_ in range(0, 361, 18)]
        tube(pipe_r, ring, [0.011] * len(ring), seg=5)
    for _b in (hemb, studs_r, pipe_r):
        tag(_b, '@legL' if s > 0 else '@legR')
new_obj("BS_TrouserBands", hemb, M_SUIT, 60, rest=True)
new_obj("BS_LimbStuds", studs_r, M_PEWTER, 32, rest=True)
new_obj("BS_TrouserPiping", pipe_r, M_STITCH, 40, rest=True)''')

# ---- suit front
p3 = cut(p3, "patch(tie, SS, [(-0.06, 0.06, 4.50)", "panel(placket, TS,", '''# bow tie: a knot and two wings on the shirt under the chin; shirt studs below it
bowdots, zipteeth, ziptape = bmesh.new(), bmesh.new(), bmesh.new()
bow_c = surf(SS, 0.0, 4.43, 0.05)
bmesh.ops.create_uvsphere(tie, u_segments=14, v_segments=8, radius=1.0, matrix=Matrix.Translation(bow_c) @ Matrix.Diagonal((0.036, 0.036, 0.046, 1.0)))
BOW = [(0.015, 0.016, 0.018), (0.05, 0.022, 0.036), (0.10, 0.027, 0.058), (0.155, 0.027, 0.07), (0.182, 0.02, 0.066), (0.19, 0.008, 0.05)]
for sdx in (-1, 1):                                             # each wing: pinched at the knot, flaring to a blunt end
    xloft(tie, [(x_, bow_c.y + 0.006, bow_c.z, ry_, rz_) for x_, ry_, rz_ in BOW], seg=16, sx=sdx)
    for ddx, ddz in ((0.065, 0.012), (0.105, -0.026), (0.112, 0.03), (0.152, 0.002), (0.158, -0.04), (0.16, 0.042)):   # pale dots, as on the original
        puck(bowdots, bow_c + Vector((sdx * ddx, 0.006 - 0.0265, ddz)), (0, -1, 0), 0.0085, 0.004, seg=8)
# zipper down the shirt front, from under the bow to where the coat closes: two tapes, interlocking teeth, a slider and pull
ZT, ZB = 4.345, 3.93


def zframe(dx, z, lift):
    n_ = (surf(SS, dx, z, 1.0) - surf(SS, dx, z, 0.0)).normalized()
    up_ = (surf(SS, dx, z + 0.01) - surf(SS, dx, z - 0.01)).normalized()
    m_ = Matrix((up_.cross(n_).normalized(), up_, n_)).transposed().to_4x4()
    m_.translation = surf(SS, dx, z, lift)
    return m_


for sdx in (-1, 1):
    patch(ziptape, SS, [(sdx * 0.004, sdx * 0.042, ZB + (ZT - ZB) * i / 10) for i in range(11)], 0.003, nx=2)
nz = int((ZT - ZB) / 0.019)
for i in range(nz):
    sdx = 1 if i % 2 else -1
    rbox(zipteeth, zframe(sdx * 0.008, ZB + (ZT - ZB) * (i + 0.5) / nz, 0.008), (0.02, 0.012, 0.012), 0.003, 1)
rbox(zipteeth, zframe(0.0, ZT - 0.012, 0.012), (0.036, 0.044, 0.016), 0.006, 2)                    # slider
rbox(zipteeth, zframe(0.0, ZT - 0.062, 0.02), (0.02, 0.06, 0.006), 0.003, 1)                      # pull tab
lathe(zipteeth, zframe(0.0, ZT - 0.03, 0.016).translation - Vector((0.012, 0, 0)), (1, 0, 0), [(0.0, 0.005), (0.024, 0.005)], seg=8)


''')
p3 = rep(p3, "panel(placket, TS, [(-0.02, 2.428), (0.14, 2.428), (0.14, 3.78), (0.06, 3.955), (-0.02, 3.955)]",
         "panel(placket, TS, [(-0.095, 2.428), (0.095, 2.428), (0.095, 3.80), (0.03, 3.955), (-0.03, 3.955), (-0.095, 3.80)]")
p3 = cut(p3, "for z in (3.50, 3.31, 3.09, 2.86, 2.67):", "tag(pewter, '@jacket')", '''for z in (3.56, 3.38, 3.20, 3.02, 2.84, 2.66):          # a column of studs down each side of the button stand
    for sx_ in (-1, 1):
        p = surf(TS, sx_ * 0.05, z, 0.017)
        stud(pewter, p, (surf(TS, sx_ * 0.05, z, 1.0) - surf(TS, sx_ * 0.05, z, 0.0)).normalized(), 0.026)
''')
p3 = cut(p3, "edge = [(0.123, 3.76", "tube(stitch, COLLAR_EDGE", '''for sx_ in (-1, 1):
    edge = [(sx_ * 0.088, 3.76 - (3.76 - 2.60) * i / 12) for i in range(13)]
    tube(stitch, [surf(TS, x, z, 0.021) for x, z in edge], [SR] * len(edge), seg=5)
''')
p3 = rep(p3, "SR = 0.005", "SR = 0.009")
p3 = rep(p3, "hs = [ring_pt(TS, 2.565, a, 0.021)[0] for a in HB]\ntube(stitch, hs, [SR] * len(hs), seg=4)",
         "for zz in (2.565, 2.44):\n    hs = [ring_pt(TS, zz, a, 0.021)[0] for a in HB]\n    tube(stitch, hs, [SR] * len(hs), seg=5)")
p3 = cut(p3, "for a in (-70, -45, -20, 5, 30, 55, 80, 100, 125, 150, 175, 200, 225, 250):", "\n\ndef roll_lift",
         "for a in range(-80, 262, 20):\n    p, n = ring_pt(TS, 2.50, a, 0.018)\n    stud(pewter, p, n, 0.027)\n")
x = "    o = [(s * x, z) for x, z in flap]"
p3 = rep(p3, x, '''    for xs, zs in ((0.09, 4.05), (0.19, 4.09), (0.29, 4.13), (0.375, 4.175), (0.34, 4.235), (0.40, 4.335), (0.41, 4.40), (0.375, 4.455)):
        p = surf(TS, s * xs, zs, roll_lift(xs, zs) + 0.024)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0) - surf(TS, s * xs, zs, 0.0)).normalized(), 0.023)
''' + x)
x = "tag(pewter, '@jacket')\ntag(stitch, '@jacket')"
p3 = rep(p3, x, '''for s in (-1, 1):                                              # studs on the back yokes
    for xs, zs in ((0.355, 4.405), (0.44, 4.405), (0.515, 4.38), (0.505, 4.26), (0.485, 4.13), (0.40, 4.19), (0.335, 4.29)):
        p = surf(TS, s * xs, zs, 0.022, True)
        stud(pewter, p, (surf(TS, s * xs, zs, 1.0, True) - surf(TS, s * xs, zs, 0.0, True)).normalized(), 0.023)
''' + x)
p3 = rep(p3, "    o = [(s * x, z) for x, z in flap]\n    panel(pockets, TS, o, flat_lift, cuts=2)\n    topstitch(stitch, TS, o, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)\n", "")
p3 = rep(p3, "topstitch(stitch, TS, breast, lambda x, z: 0.024, inset=0.017, step=0.05, radius=SR)\n", "")
p3 = cut(p3, "mc = surf(TS, 0.0, MZ) + mn * 0.034", "tag(medal_p, 'joint_attachMeter')", '''mc = surf(TS, 0.0, MZ) + mn * 0.014
medal_p, medal_j = bmesh.new(), bmesh.new()
exec(compile(open(SP + "../medallion.py").read(), "medallion.py", "exec"), globals())
bail = medallion(medal_p, medal_j, mc, mn, mt, 0.165, 'gavel')
''')
p3 = rep(p3, 'new_obj("BS_MedallionEmblem", medal_j, M_JOINT, 40)', 'new_obj("BS_MedallionEmblem", medal_j, M_EMBLEM, 40)')
p1 = rep(p1, 'M_LINING = pmat("BS_Lining", (0.05, 0.012, 0.01)', 'M_LINING = pmat("BS_Lining", (0.012, 0.013, 0.03)')
p3 = rep(p3, 'new_obj("BS_Tie", tie, M_TIE, 30, outward=True, thickness=0.018)', 'new_obj("BS_BowTie", tie, M_BOW, 50)')
p3 = rep(p3, 'new_obj("BS_Cord", cord, M_JOINT, 40)', 'new_obj("BS_Cord", cord, M_STEEL, 40)\nnew_obj("BS_BowDots", bowdots, M_SHIRT, 40)\nnew_obj("BS_Zipper", zipteeth, M_STEEL, 35)\nnew_obj("BS_ZipTape", ziptape, M_LINING, 30, outward=True, thickness=0.004)')
i_cam = p3.index('cam = bpy.data.objects.new("BSCam"')
p3 = p3[:i_cam] + '''# The coat and everything sewn to it were laid out at the Downsizer's size; bring them to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        v.co *= BODY_S
    ob.data.update()

''' + p3[i_cam:]
open(D + "build.py", "w").write(p1 + open(D + "work/head_part.py").read() + p3)

r = ren(open(DS + "rig.py").read())
r = rep(r, '"BS_Tie": "@shirt"', '"BS_Tie": "@shirt", "BS_BowTie": "@shirt", "BS_BowDots": "@shirt", "BS_Zipper": "@shirt", "BS_ZipTape": "@shirt"')
r = rep(r, 'REST_FN = {', 'REST_FN = {"BS_TrouserBands": trouser_weights, "BS_LimbStuds": trouser_weights, "BS_TrouserPiping": trouser_weights, ')
open(D + "rig.py", "w").write(r)
open(D + "run.py", "w").write(open(BF + "run.py").read().replace(BF, D).replace("BF_Rig", "BS_Rig").replace("bf_rig", "bs_rig"))
c = ren(open(DS + "check.py").read())
c = cut(c, 'shot("headfront"', 'shot("chestfront"', '''shot("headfront", (0, -20, 5.4), (0, 0, 5.4), 1.1, 2.0, k=4)
shot("headleft", (20, 0, 5.4), (0, 0, 5.4), 1.2, 2.0, k=4)
shot("headback", (0, 20, 5.4), (0, 0, 5.4), 1.1, 2.0, k=4)
shot("head34", (-10, -16, 7.2), (0, 0, 5.35), 1.2, 2.0, k=4)
shot("headrear", (-12, 14, 6.6), (0, 0, 5.35), 1.2, 2.0, k=4)
shot("face", (3, -19, 5.7), (0, -0.2, 5.45), 0.8, 0.7, k=6)
shot("mouth", (5, -18, 4.5), (0.0, -0.2, 4.9), 0.8, 0.7, k=6)
shot("medal", (2.5, -19, 4.6), (0.0, -0.35, 3.78), 0.75, 0.9, k=8)
shot("medalside", (14, -14, 4.0), (0.0, -0.35, 3.78), 0.75, 0.9, k=6)
''')
open(D + "check.py", "w").write(c)
open(D + "bake.py", "w").write(open(DS + "bake.py").read().replace("05_Downsizer_Bossbot", "10_Bloodsucker_Lawbot").replace("DS_Baked", "BS_Baked").replace("(0.20, 0.052, 0.036, 1)", "(0.028, 0.032, 0.085, 1)"))
s = open(D + "build_bam.py").read()
if "'b':" not in s:
    s = rep(s, "'bf': 4.0 / 4.14}", "'bf': 4.0 / 4.14, 'b': 4.375 / 5.29}"); open(D + "build_bam.py", "w").write(s)
print("ok")
