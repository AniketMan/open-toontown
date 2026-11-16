B="/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D=B+"08_The-Big-Cheese_Bossbot/"; HH=B+"06_Head-Hunter_Bossbot/"; CR=B+"07_Corporate-Raider_Bossbot/"
def rep(s,a,b):
    assert a in s, a
    return s.replace(a,b)
hh=open(HH+"build.py").read()
i_head=hh.index("# ---------------------------------------------------------------- head: a heavy block")
i_front=hh.index("# ---------------------------------------------------------------- suit front")
p1, p3 = hh[:i_head], hh[i_front:]
def ren(s):
    return s.replace(HH,D).replace("06_Head-Hunter_Bossbot","08_The-Big-Cheese_Bossbot").replace("HeadHunter","BigCheese").replace("HH_","TBC_").replace("hh_ref_","tbc_ref_").replace('"hh_rig.json"','"tbc_rig.json"').replace("HHCam","TBCCam").replace("HHSun","TBCSun").replace("HHFill","TBCFill")
p1, p3 = ren(p1), ren(p3)
p1=rep(p1,"Build the HD Downsizer (Bossbot)","Build the HD Big Cheese (Bossbot)") if "Build the HD Downsizer (Bossbot)" in p1 else p1
p1=rep(p1,"K = 6.5 / 6.06          # suit A scale for this cog","K = 7.0 / 6.06          # suit A scale for this cog\nBODY_S = 1.106          # the coat is the Head Hunter's cut, 1.106 times the size (hem 3.48 -> 3.85, shoulders 6.3 -> 7.0)")
p1=rep(p1,"e.empty_display_size = 7.8","e.empty_display_size = 9.8")
p1=rep(p1,'(0.78, 0.63, 0.53), 0.42, 0.1','(0.52, 0.62, 0.10), 0.42, 0.1')
p1=rep(p1,'M_HAND = pmat("TBC_Hand", (0.76, 0.60, 0.50)','M_HAND = pmat("TBC_Hand", (0.42, 0.60, 0.10)')
p1=rep(p1,'M_EYE = pmat("TBC_Eye", (0.45, 0.38, 0.30)','M_EYE = pmat("TBC_Eye", (0.85, 0.85, 0.72)')
p1=rep(p1,"plate, joint, steel, pewter = bmesh.new()",'''M_CORE = pmat("TBC_CheeseInside", (0.20, 0.26, 0.03), 0.6, var=0.3, grime=0.4, bump=0.1, bscale=40)
M_BROW = pmat("TBC_Brow", (0.16, 0.22, 0.03), 0.45, 0.1, var=0.3, grime=0.4, bump=0.1, bscale=60)
M_IRISRING = pmat("TBC_IrisRing", (0.55, 0.58, 0.08), 0.2, var=0.3, coat=0.6)
M_CUFF = pmat("TBC_Cuff", (0.80, 0.70, 0.60), 0.6, var=0.15, grime=0.3, weave=0.2, rvar=0.06)
plate, joint, steel, pewter = bmesh.new()''')
p1=rep(p1,"plate_r, joint_r = bmesh.new(), bmesh.new()","plate_r, joint_r, cuff_r = bmesh.new(), bmesh.new(), bmesh.new()")
p1=rep(p1,"lathe(plate_r, c0, ax, [(0.0, 0.22)","lathe(cuff_r, c0, ax, [(0.0, 0.22)")
p1=rep(p1,"    tag(plate_r, names['wrist'])\n    tag(joint_r, names['wrist'])\n    for kind, fy in FINGERS:","    tag(cuff_r, names['wrist'])\n    tag(plate_r, names['wrist'])\n    tag(joint_r, names['wrist'])\n    for kind, fy in FINGERS:")
p1=rep(p1,'new_obj("TBC_HandPlates", plate_r, M_HAND, 32, rest=True)','new_obj("TBC_HandPlates", plate_r, M_HAND, 32, rest=True)\nnew_obj("TBC_Cuffs", cuff_r, M_CUFF, 40, rest=True)')
p3+='''
# The coat and everything sewn to it were laid out at the Head Hunter's size; bring them up to this cog's size.
for ob in col.objects:
    if ob.type != 'MESH' or ob.get("rest_space"):
        continue
    hg = ob.vertex_groups.get("joint_head")
    for v in ob.data.vertices:
        if hg is not None and any(g.group == hg.index for g in v.groups):
            continue
        v.co *= BODY_S
    ob.data.update()
'''
open(D+"build.py","w").write(p1+open(D+"work/head_part.py").read()+p3)
r=open(HH+"rig.py").read().replace(HH,D).replace("Head Hunter (suit A)","Big Cheese (suit A)").replace('"hh_rig.json"','"tbc_rig.json"').replace('collections["HeadHunter"]','collections["BigCheese"]').replace("HH_","TBC_")
r=rep(r,"RIGID_SIZE = 0.22","RIGID_SIZE = 0.24")
open(D+"rig.py","w").write(r)
open(D+"run.py","w").write(open(HH+"run.py").read().replace(HH,D).replace("HH_Rig","TBC_Rig").replace("hh_rig","tbc_rig"))
c=open(CR+"check.py").read()
a=c.index('shot("front"'); b=c.index("(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep")
c=c[:a]+open(D+"work/shots_part.py").read()+c[b:]
c=c.replace(CR,D).replace('"CRCam"','"TBCCam"').replace("PXU = 130.0","PXU = 115.0").replace("Corporate Raider","Big Cheese")
open(D+"check.py","w").write(c)
open(D+"bake.py","w").write(open(CR+"bake.py").read().replace("07_Corporate-Raider_Bossbot","08_The-Big-Cheese_Bossbot").replace("CR_Baked","TBC_Baked"))
s=open(D+"build_bam.py").read()
if "'tbc'" not in s:
    s=rep(s,"'cr': 6.75 / 4.14}","'cr': 6.75 / 4.14, 'tbc': 7.0 / 6.06}"); open(D+"build_bam.py","w").write(s)
print("ok")
