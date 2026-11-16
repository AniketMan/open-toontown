B="/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D=B+"09_Bottom-Feeder_Lawbot/"; CR=B+"07_Corporate-Raider_Bossbot/"; TBC=B+"08_The-Big-Cheese_Bossbot/"
def rep(s,a,b):
    assert a in s, a[:60]
    return s.replace(a,b)
cr=open(CR+"build.py").read()
i_head=cr.index("# ---------------------------------------------------------------- head: an egg")
i_front=cr.index("# ---------------------------------------------------------------- suit front")
def ren(s):
    return s.replace(CR,D).replace("07_Corporate-Raider_Bossbot","09_Bottom-Feeder_Lawbot").replace("CorporateRaider","BottomFeeder").replace("CR_","BF_").replace("cr_ref_","bf_ref_").replace('"cr_rig.json"','"bf_rig.json"').replace("CRCam","BFCam").replace("CRSun","BFSun").replace("CRFill","BFFill")
p1, p3 = ren(cr[:i_head]), ren(cr[i_front:])
p1=rep(p1,"K = 6.75 / 4.14         # suit C scale for this cog","K = 4.0 / 4.14          # suit C scale for this cog\n# The coat is the Corporate Raider's cut. It is laid out at his size and brought to this cog's at the end:\n# widths by 0.593 (the two cogs' scale ratio), heights so that hem 3.05 -> 1.60 and neck 6.53 -> 3.78 on this sheet.\nBODY_XY, BODY_ZA, BODY_ZB = 0.593, 0.6264, -0.3106")
p1=rep(p1,"e.empty_display_size = 8.6","e.empty_display_size = 5.1")
p1=rep(p1,'M_SUIT = pmat("BF_Suit", (0.20, 0.052, 0.036), 0.88, var=0.35, grime=0.12, stripe=(0.45, 0.24, 0.18)','M_SUIT = pmat("BF_Suit", (0.028, 0.032, 0.085), 0.88, var=0.35, grime=0.12, stripe=(0.05, 0.055, 0.13)')
p1=rep(p1,'M_STITCH = pmat("BF_Stitch", (0.66, 0.50, 0.42)','M_STITCH = pmat("BF_Piping", (0.20, 0.035, 0.26)')
p1=rep(p1,'(0.80, 0.66, 0.56), 0.42, 0.1','(0.56, 0.47, 0.78), 0.42, 0.1')
p1=rep(p1,'M_HAND = pmat("BF_Hand", (0.78, 0.47, 0.44)','M_HAND = pmat("BF_Hand", (0.50, 0.42, 0.74)')
p1=rep(p1,'M_EYE = pmat("BF_Eye", (0.92, 0.90, 0.84)','M_EYE = pmat("BF_Eye", (0.88, 0.84, 0.70)')
p1=rep(p1,'M_IRISRING = pmat("BF_IrisRing", (0.22, 0.10, 0.04)','M_LIP = pmat("BF_Lip", (0.20, 0.14, 0.40), 0.4, 0.1, var=0.25, grime=0.35, bump=0.08, bscale=40, rvar=0.12, coat=0.2)\nM_BOW = pmat("BF_Bow", (0.60, 0.04, 0.03), 0.6, var=0.25, weave=0.5, sheen=0.3, rvar=0.1)\nM_BROW = pmat("BF_Dark", (0.06, 0.04, 0.12), 0.4, 0.1, var=0.3)\nM_IRISRING = pmat("BF_IrisRing", (0.45, 0.36, 0.10)')
p1=rep(p1,'new_obj("BF_Cuffs", cuff_r, M_SHIRT, 40, rest=True)','new_obj("BF_Cuffs", cuff_r, M_STEEL, 40, rest=True)')
p1=rep(p1,"SHIRT_IN = {5.60: 0.20,","SHIRT_IN = {5.20: 0.20, 5.60: 0.20,")
# studded bands on the trouser hems and studs round the sleeve bands (rest space)
anchor='new_obj("BF_Trousers", bm, M_SUIT, 60, rest=True)'
p1=rep(p1,anchor,anchor+'''
# studded band round each trouser hem, and a row of studs round each sleeve band
hemb, studs_r = bmesh.new(), bmesh.new()
for s in (-1, 1):
    z0, cx, cy, rx, ry = LEG[0]
    z1 = LEG[1][0] + 0.12
    loft(hemb, [(z0 - 0.005, cx, cy, rx + 0.02, ry + 0.02), (z1, cx, cy, rx + 0.025, ry + 0.025)], seg=20, sx=s, caps=(False, False), centres=(270, 90))
    tag(hemb, '@legL' if s > 0 else '@legR')
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        nrm = Vector((s * math.cos(a) / rx, math.sin(a) / ry, 0)).normalized()
        p = Vector((s * (cx + (rx + 0.03) * math.cos(a)), cy + (ry + 0.03) * math.sin(a), (z0 + z1) / 2))
        lathe(studs_r, p, nrm, [(0.0, 0.036), (0.015, 0.036), (0.028, 0.018), (0.032, 0.002)], seg=8)
    tag(studs_r, '@legL' if s > 0 else '@legR')
new_obj("BF_TrouserBands", hemb, M_SUIT, 60, rest=True)


def cuff_studs(bm):
    x, cy, cz, ry, rz = BAND[0]
    for k in range(9):
        a = 2 * math.pi * k / 9
        nrm = Vector((0, math.cos(a), math.sin(a)))
        lathe(bm, Vector((2.62, cy + (ry + 0.006) * nrm.y, cz + (rz + 0.006) * nrm.z)), nrm, [(0.0, 0.034), (0.014, 0.034), (0.026, 0.017), (0.03, 0.002)], seg=8)


cs = both_arms(cuff_studs)
tag(cs, '@sleeve')
merge(studs_r, cs)
new_obj("BF_LimbStuds", studs_r, M_PEWTER, 32, rest=True)''')
# suit front changes
a=p3.index("patch(tie, SS, [(-0.14, 0.14, 6.45)"); b=p3.index("panel(placket, TS,")
p3=p3[:a]+'''# bow tie: a knot and two wings, sitting on the shirt under the chin; shirt studs below it
bow_c = surf(SS, 0.0, 6.36, 0.10)
for dx, sc in ((0.0, (0.10, 0.08, 0.11)), (0.30, (0.25, 0.07, 0.17)), (-0.30, (0.25, 0.07, 0.17))):
    bmesh.ops.create_uvsphere(tie, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation(bow_c + Vector((dx, 0.02 if dx else 0.0, 0))) @ Matrix.Diagonal((*sc, 1.0)))
tag(tie, '@shirt')
for z in (6.12, 5.98, 5.84, 5.70):
    p = surf(SS, 0.0, z, 0.01)
    puck(pewter, p, (surf(SS, 0.0, z, 1.0) - surf(SS, 0.0, z, 0.0)).normalized(), 0.045, 0.03, seg=8)
tag(pewter, '@shirt')

'''+p3[b:]
p3=rep(p3,'new_obj("BF_Tie", tie, M_TIE, 30, outward=True, thickness=0.036)','new_obj("BF_BowTie", tie, M_BOW, 50)')
p3=rep(p3,"SR = 0.011","SR = 0.02")
# studs along the lapels and a studded hem band
x="    o = [(s * x, z) for x, z in flap]"
p3=rep(p3,x,'''    for (xa, za), (xb, zb) in zip(lapel[:4], lapel[1:4]):                # studs along the lapel's outer edge
        n_st = max(1, int(math.hypot(xb - xa, zb - za) / 0.24))
        for k in range(n_st):
            f = (k + 0.5) / n_st
            xs, zs = xa + (xb - xa) * f, za + (zb - za) * f
            xs2 = xs - 0.09 * (1 if xs > 0.2 else 0)
            p = surf(TS, s * xs2, zs + 0.06, roll_lift(xs2, zs) + 0.05)
            nrm = (surf(TS, s * xs2, zs + 0.06, 1.0) - surf(TS, s * xs2, zs + 0.06, 0.0)).normalized()
            lathe(pewter, p, nrm, [(0.0, 0.05), (0.02, 0.05), (0.036, 0.025), (0.042, 0.003)], seg=8)
'''+x)
x="# Shoulder straps: a band over each shoulder"
p3=rep(p3,x,'''# hem band: a studded strap sewn round the bottom of the coat
hemband = bmesh.new()
HB = [a for a in range(-88, 269, 4)]
grid(hemband, [[ring_pt(TS, z, a, 0.012)[0] for a in HB] for z in (3.056, 3.16, 3.27)])
tag(hemband, '@jacket')
new_obj("BF_HemBand", hemband, M_SUIT, 40, outward=True, thickness=0.03)
for zz in (3.065, 3.26):
    hs = [ring_pt(TS, zz, a, 0.05)[0] for a in HB]
    tube(stitch, hs, [SR] * len(hs), seg=4)
for a in range(-80, 262, 19):
    p, nrm = ring_pt(TS, 3.165, a, 0.042)
    lathe(pewter, p, nrm, [(0.0, 0.055), (0.02, 0.055), (0.038, 0.028), (0.045, 0.003)], seg=8)

'''+x)
a=p3.index("for pts in (((-0.11, 0.19), (0.11, -0.19))"); b=p3.index("tag(medal_p, 'joint_attachMeter')")
p3=p3[:a]+'''for pts in (((-0.14, 0.12), (0.14, 0.12)), ((-0.14, 0.06), (0.14, 0.06)), ((-0.14, 0.12), (-0.14, 0.06)), ((0.14, 0.12), (0.14, 0.06)),
            ((-0.03, 0.06), (-0.03, -0.19)), ((0.03, 0.06), (0.03, -0.19)), ((-0.03, -0.19), (0.03, -0.19))):          # a gavel
    loop = [mc + mn * 0.094 + Vector((x, 0, 0)) + mt * t for x, t in pts]
    tube(medal_j, loop, [0.014, 0.014], seg=4)
'''+p3[b:]
p3=rep(p3,'new_obj("BF_Cord", cord, M_JOINT, 40)','new_obj("BF_Cord", cord, M_STEEL, 40)')
p3+='''
# The coat and everything sewn to it were laid out at the Corporate Raider's size; bring them to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    moved = False
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        v.co = Vector((v.co.x * BODY_XY, v.co.y * BODY_XY, v.co.z * BODY_ZA + BODY_ZB))
        moved = True
    if moved:
        for m in ob.modifiers:
            if m.type == 'SOLIDIFY':
                m.thickness *= 0.62
    ob.data.update()
'''
open(D+"build.py","w").write(p1+open(D+"work/head_part.py").read()+p3)
r=open(CR+"rig.py").read().replace(CR,D).replace("Corporate Raider (suit C)","Bottom Feeder (suit C)").replace('"cr_rig.json"','"bf_rig.json"').replace('collections["CorporateRaider"]','collections["BottomFeeder"]').replace("CR_","BF_")
r=rep(r,"RIGID_SIZE = 0.30","RIGID_SIZE = 0.2")
r=rep(r,'"BF_Straps": "@jacket"','"BF_Straps": "@jacket", "BF_HemBand": "@jacket", "BF_BowTie": "@shirt"')
r=rep(r,'REST_FN = {','REST_FN = {"BF_TrouserBands": trouser_weights, "BF_LimbStuds": trouser_weights, ')
open(D+"rig.py","w").write(r)
open(D+"run.py","w").write(open(TBC+"run.py").read().replace(TBC,D).replace("TBC_Rig","BF_Rig").replace("tbc_rig","bf_rig"))
c=open(TBC+"check.py").read()
a=c.index('shot("front"'); b=c.index("(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep")
c=c[:a]+open(D+"work/shots_part.py").read()+c[b:]
c=c.replace(TBC,D).replace('"TBCCam"','"BFCam"').replace("PXU = 115.0","PXU = 190.0").replace("Big Cheese","Bottom Feeder")
open(D+"check.py","w").write(c)
open(D+"bake.py","w").write(open(TBC+"bake.py").read().replace("08_The-Big-Cheese_Bossbot","09_Bottom-Feeder_Lawbot").replace("TBC_Baked","BF_Baked").replace("(0.20, 0.052, 0.036, 1)","(0.028, 0.032, 0.085, 1)"))
s=open(D+"build_bam.py").read()
if "'bf'" not in s:
    s=rep(s,"'tbc': 7.0 / 6.06}","'tbc': 7.0 / 6.06, 'bf': 4.0 / 4.14}"); open(D+"build_bam.py","w").write(s)
print("ok")
