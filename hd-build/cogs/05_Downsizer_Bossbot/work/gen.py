B="/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
D=B+"05_Downsizer_Bossbot/"
OLD="/private/tmp/claude-501/-Users-aniketbhatt-Documents-GitHub-open-toontown/cf0310ce-0a2b-40d1-bcca-397bd93ed6dc/scratchpad/"
pp=open(B+"02_Pencil-Pusher_Bossbot/build.py").read().split("\n")
limbs="\n".join(pp[127:275])+"\nSTRIPE = 0.06\n"
def rep(s,a,b):
    assert a in s, a
    return s.replace(a,b)
limbs=rep(limbs,'"pp_rig.json"','"ds_rig.json"')
limbs=limbs.replace("PP_","DS_")
a=limbs.index("SLEEVE = ["); b=limbs.index("sleeves, plate_r, joint_r")
limbs=limbs[:a]+'''SLEEVE = [(0.66, 0.15, AZ, 0.07, 0.05), (0.70, 0.15, AZ, 0.16, 0.12), (0.76, 0.15, AZ, 0.23, 0.17),
          (0.83, 0.15, AZ, 0.265, 0.20), (0.89, 0.15, AZ, 0.275, 0.205), (1.20, 0.16, AZ, 0.275, 0.21),
          (1.60, 0.17, AZ, 0.265, 0.205), (1.97, 0.17, AZ, 0.255, 0.20), (2.50, 0.15, AZ, 0.245, 0.195),
          (2.98, 0.14, AZ, 0.24, 0.195), (2.96, 0.14, AZ, 0.185, 0.165)]
BAND = [(2.56, 0.15, AZ, 0.262, 0.212), (2.995, 0.14, AZ, 0.257, 0.212)]      # turned-up cuff band
'''+limbs[b:]
limbs=rep(limbs,"for x in (2.74, 2.86):","for x in (2.72, 2.86):")
limbs=rep(limbs,"for x in (2.625, 2.945):","for x in (2.585, 2.975):")
a=limbs.index("loft(seat, ["); b=limbs.index('new_obj("DS_Seat"')
limbs=limbs[:a]+'''loft(seat, [(2.50, 0, -0.05, 0.05, 0.05), (2.54, 0, -0.05, 0.22, 0.20), (2.62, 0, -0.05, 0.34, 0.30), (2.75, 0, -0.05, 0.42, 0.36),
            (2.95, 0, -0.06, 0.47, 0.40), (3.20, 0, -0.07, 0.52, 0.43), (3.50, 0, -0.07, 0.54, 0.44), (3.75, 0, -0.06, 0.48, 0.40),
            (3.90, 0, -0.05, 0.35, 0.30)], seg=24, centres=(270, 90))
'''+limbs[b:]
a=limbs.index("LEG = ["); b=limbs.index("for s in (-1, 1):\n    loft(bm, LEG")
limbs=limbs[:a]+'''LEG = [(0.21, 0.212, 0.0, 0.20, 0.345), (0.50, 0.21, -0.02, 0.196, 0.325), (1.00, 0.208, -0.04, 0.192, 0.305),
       (1.67, 0.208, -0.05, 0.192, 0.30), (2.40, 0.21, -0.05, 0.196, 0.31), (3.00, 0.215, -0.05, 0.20, 0.33)]
'''+limbs[b:]
limbs=rep(limbs,"STRIPE = 0.05 / K","STRIPE = 0.06 / K")
limbs=rep(limbs,'new_obj("DS_HandPlates", plate_r, M_PLATE','new_obj("DS_HandPlates", plate_r, M_HAND')
open(D+"build.py","w").write(open(D+"work/header_part.py").read()+limbs+open(D+"work/head_part.py").read())
r=open(B+"04_Micromanager_Bossbot/rig.py").read()
ppr=open(B+"02_Pencil-Pusher_Bossbot/rig.py").read()
r=r.replace(OLD,D).replace("Micromanager (suit C)","Downsizer (suit B)").replace('"mm_rig.json"','"ds_rig.json"').replace('collections["Micromanager"]','collections["Downsizer"]').replace("MM_","DS_")
a=r.index("PAIRS = ["); b=r.index("L2R = dict(PAIRS)")
pa=ppr.index("PAIRS = ["); pb=ppr.index("L2R = dict(PAIRS)")
r=r[:a]+ppr[pa:pb]+r[b:]
a=r.index("def sleeve_weights(co):"); b=r.index("REST_FN = {")
pa=ppr.index("def sleeve_weights(co):"); pb=ppr.index("REST_FN = {")
r=r[:a]+ppr[pa:pb]+r[b:]
r=rep(r,'"DS_Straps": "@jacket"','"DS_BackStraps": "@jacket", "DS_HemBand": "@jacket"')
r=rep(r,"RIGID_SIZE = 0.115","RIGID_SIZE = 0.15")
assert "FROM_REST" in r and "scale_jnt3_1" in r
open(D+"rig.py","w").write(r)
open(D+"run.py","w").write('''SP="%s"
import traceback, bpy
def run(only, prefix, pose="sheet", rebuild=True):
    out = {}
    if rebuild:
        for n in ("body_hd","head_hd","DS_Rig"):
            o=bpy.data.objects.get(n)
            if o: bpy.data.objects.remove(o, do_unlink=True)
        ns={}
        exec(compile(open(SP+"build.py").read(), SP+"build.py","exec"), ns)
        rig={}
        exec(compile(open(SP+"rig.py").read(), SP+"rig.py","exec"), rig)
        bpy.app.driver_namespace["ds_rig"]=rig
        out["rig"]=rig["result"]
    rig=bpy.app.driver_namespace["ds_rig"]
    rig["apply_pose"](pose)
    if only:
        ns={"ONLY":only,"PREFIX":prefix}
        exec(compile(open(SP+"check.py").read(), "check","exec"), ns)
        out["rendered"]=ns["result"]["rendered"]
    return out
''' % D)
c=open(B+"04_Micromanager_Bossbot/check.py").read()
a=c.index('shot("front"'); b=c.index("(sc.camera, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath, sc.render.film_transparent) = keep")
c=c[:a]+'''shot("front", (0, -20, 3.1), (0, 0, 3.1), 2.6, 6.4)
shot("left", (20, 0, 3.1), (0, 0, 3.1), 2.0, 6.4)
shot("back", (0, 20, 3.1), (0, 0, 3.1), 2.6, 6.4)
shot("headfront", (0, -20, 5.3), (0, 0, 5.3), 0.9, 1.7, k=4)
shot("headleft", (20, 0, 5.3), (0, 0, 5.3), 0.9, 1.7, k=4)
shot("headback", (0, 20, 5.3), (0, 0, 5.3), 0.9, 1.7, k=4)
shot("head34", (-10, -16, 7.0), (0, 0, 5.25), 1.0, 1.7, k=4)
shot("face", (3, -19, 5.6), (0, -0.1, 5.45), 0.5, 0.5, k=8)
shot("mouth", (6, -18, 4.6), (0.0, -0.1, 5.0), 0.7, 0.8, k=5)
shot("chestfront", (0, -20, 3.5), (0, 0, 3.5), 2.2, 2.4, k=2)
shot("chestback", (0, 20, 3.5), (0, 0, 3.5), 2.2, 2.4, k=2)
shot("neck", (4, -17, 7.5), (0, -0.2, 4.4), 1.4, 1.0, k=3)
shot("above", (0, -7, 22), (0, -0.1, 4.4), 2.4, 1.9, k=2)
shot("handfront", (0.8, -20, 2.3), (0.8, 0, 2.3), 0.7, 1.0, k=4)
shot("shoes", (0, -20, 0.25), (0, 0, 0.25), 1.6, 0.6, k=4)
shot("under", (4, -9, -10), (0, 0, 2.2), 2.4, 1.9, k=2)
shot("hem", (-6, 16, 3.5), (0, 0.2, 2.6), 1.4, 0.8, k=4)
shot("walkfront", (0, -20, 3.1), (0, 0, 3.1), 3.4, 6.4)
shot("walkleft", (20, 0, 3.1), (0, 0, 3.1), 3.4, 6.4)
shot("walkback", (0, 20, 3.1), (0, 0, 3.1), 3.4, 6.4)
a = math.radians(-38)
shot("threeq", (math.sin(a) * 22, -math.cos(a) * 22, 3.8), (0, 0, 3.1), 2.6, 6.4, ortho=False)
'''+c[b:]
c=c.replace(OLD+"mm/",D+"work/").replace('"MMCam"','"DSCam"').replace("PXU = 275.0","PXU = 190.0").replace("Micromanager","Downsizer")
open(D+"check.py","w").write(c)
bk=open(B+"04_Micromanager_Bossbot/bake.py").read().replace("04_Micromanager_Bossbot","05_Downsizer_Bossbot").replace("MM_Baked","DS_Baked")
open(D+"bake.py","w").write(bk)
print("ok")
