SP="/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/07_Corporate-Raider_Bossbot/"
import traceback, bpy
def run(only, prefix, pose="sheet", rebuild=True):
    out = {}
    if rebuild:
        for n in ("body_hd","head_hd","CR_Rig"):
            o=bpy.data.objects.get(n)
            if o: bpy.data.objects.remove(o, do_unlink=True)
        ns=dict(globals().get('EXTRA', {}))
        exec(compile(open(SP+"build.py").read(), SP+"build.py","exec"), ns)
        rig={}
        exec(compile(open(SP+"rig.py").read(), SP+"rig.py","exec"), rig)
        bpy.app.driver_namespace["cr_rig"]=rig
        out["rig"]=rig["result"]
    rig=bpy.app.driver_namespace["cr_rig"]
    rig["apply_pose"](pose)
    if only:
        ns={"ONLY":only,"PREFIX":prefix}
        exec(compile(open(SP+"check.py").read(), "check","exec"), ns)
        out["rendered"]=ns["result"]["rendered"]
    return out
