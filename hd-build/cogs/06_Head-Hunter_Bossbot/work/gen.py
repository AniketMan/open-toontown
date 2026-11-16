B="/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D=B+"06_Head-Hunter_Bossbot/"; DS=B+"05_Downsizer_Bossbot/"
OLD="/private/tmp/claude-501/-Users-aniketbhatt-Documents-GitHub-open-toontown/cf0310ce-0a2b-40d1-bcca-397bd93ed6dc/scratchpad/"
def rep(s,a,b):
    assert a in s, a
    return s.replace(a,b)
h=open(DS+"work/header_part.py").read()
h=h[:h.index("# ---------------------------------------------------------------- jacket")]
h=h.replace("05_Downsizer_Bossbot","06_Head-Hunter_Bossbot").replace("Downsizer","HeadHunter").replace("DS_","HH_").replace("ds_ref_","hh_ref_")
h=rep(h,"576 px = 6.08 game units","539 px = 7.5 game units"); h=rep(h,"suit B's rest pose at native size (game / 0.851)","suit A's rest pose at native size (game / 1.073)")
h=rep(h,"STRIPE = 0.06\nK = 4.5 / 5.29          # suit B scale for this cog","STRIPE = 0.09\nK = 6.5 / 6.06          # suit A scale for this cog")
h=rep(h,"e.empty_display_size = 6.4","e.empty_display_size = 7.8")
h=rep(h,'(0.33, 0.50, 0.44), 0.42, 0.15','(0.78, 0.63, 0.53), 0.42, 0.1')
h=rep(h,'M_EYE = pmat("HH_Eye", (0.80, 0.72, 0.58)','M_EYE = pmat("HH_Eye", (0.45, 0.38, 0.30)')
h=h.replace("bscale=110, sheen=0.04","bscale=75, sheen=0.04")
h+=open(D+"work/torso_part.py").read()
ym=open(B+"03_Yesman_Bossbot/build.py").read()
a=ym.index("# ---------------------------------------------------------------- limbs"); b=ym.index("# ---------------------------------------------------------------- head")
limbs=ym[a:b]
limbs=rep(limbs,'"ym_rig.json"','"hh_rig.json"').replace("YM_","HH_")
limbs=rep(limbs,"STRIPE = 0.075 / K","STRIPE = 0.09 / K"); limbs=rep(limbs,"\nSTRIPE = 0.075\n","\nSTRIPE = 0.09\n")
a=limbs.index("loft(seat, ["); b=limbs.index('new_obj("HH_Seat"')
limbs=limbs[:a]+'''loft(seat, [(2.75, 0, -0.10, 0.06, 0.06), (2.80, 0, -0.10, 0.30, 0.26), (2.90, 0, -0.11, 0.50, 0.40), (3.05, 0, -0.12, 0.62, 0.48),
            (3.30, 0, -0.13, 0.68, 0.52), (3.60, 0, -0.13, 0.69, 0.53), (3.90, 0, -0.12, 0.60, 0.48), (4.05, 0, -0.10, 0.4, 0.35)],
     seg=24, centres=(270, 90))
'''+limbs[b:]
limbs=limbs.replace('new_obj("HH_HandPlates", plate_r, M_PLATE','new_obj("HH_HandPlates", plate_r, M_HAND')
open(D+"build.py","w").write(h+limbs+open(D+"work/head_part.py").read())
r=open(B+"04_Micromanager_Bossbot/rig.py").read(); y=open(B+"03_Yesman_Bossbot/rig.py").read()
r=r.replace(OLD,D).replace("Micromanager (suit C)","Head Hunter (suit A)").replace('"mm_rig.json"','"hh_rig.json"').replace('collections["Micromanager"]','collections["HeadHunter"]').replace("MM_","HH_")
a=r.index("PAIRS = ["); b=r.index("L2R = dict(PAIRS)"); pa=y.index("PAIRS = ["); pb=y.index("L2R = dict(PAIRS)")
r=r[:a]+y[pa:pb]+r[b:]
a=r.index("def sleeve_weights(co):"); b=r.index("REST_FN = {"); pa=y.index("def sleeve_weights(co):"); pb=y.index("REST_FN = {")
r=r[:a]+y[pa:pb]+r[b:]
r=r.replace('TO_REST["to_SHOULDER"]','TO_REST["to_shoulder"]').replace('("to_SHOULDER" if n == "to_head" else n)','("to_shoulder" if n == "to_head" else n)')
r=rep(r,'"HH_Straps": "@jacket"','"HH_BackStraps": "@jacket", "HH_HemBand": "@jacket"')
r=rep(r,"RIGID_SIZE = 0.115","RIGID_SIZE = 0.22")
assert "FROM_REST" in r and "scale_jnt24_1" in r
open(D+"rig.py","w").write(r)
open(D+"run.py","w").write(open(DS+"run.py").read().replace(DS,D).replace("DS_Rig","HH_Rig").replace("ds_rig","hh_rig"))
c=open(DS+"check.py").read()
a=c.index('shot("front"'); b=c.index("(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep")
c=c[:a]+open(D+"work/shots_part.py").read()+c[b:]
c=c.replace(DS,D).replace('"DSCam"','"HHCam"').replace("PXU = 190.0","PXU = 145.0").replace("Downsizer","Head Hunter").replace("cam.data.clip_end = 200","cam.data.clip_end = 300")
open(D+"check.py","w").write(c)
open(D+"bake.py","w").write(open(DS+"bake.py").read().replace("05_Downsizer_Bossbot","06_Head-Hunter_Bossbot").replace("DS_Baked","HH_Baked"))
s=open(D+"build_bam.py").read()
if "'hh'" not in s:
    s=rep(s,"'ds': 4.5 / 5.29}","'ds': 4.5 / 5.29, 'hh': 6.5 / 6.06}"); open(D+"build_bam.py","w").write(s)
print("ok")
