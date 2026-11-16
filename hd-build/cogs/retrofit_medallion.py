"""One-off: give cogs 01-09 the solid medallion from medallion.py (and the Bottom Feeder its zip and bow dots)."""
import re, os
B = "/Users/aniketbhatt/Documents/GitHub/open-toontown-hd/cog-turnarounds/_hd_build/"
SCR = "/private/tmp/claude-501/-Users-aniketbhatt-Documents-GitHub-open-toontown/cf0310ce-0a2b-40d1-bcca-397bd93ed6dc/scratchpad/"
EXEC = 'exec(compile(open("%smedallion.py").read(), "medallion.py", "exec"), globals())\n' % B
KIND = {"09_Bottom-Feeder_Lawbot": "gavel"}
for d in sorted(os.listdir(B)):
    if not d[:2].isdigit() or d[:2] == "10":
        continue
    D = B + d + "/"
    for f in ("build.py", "rig.py", "run.py", "check.py"):
        if os.path.exists(D + f):
            s = open(D + f).read()
            if SCR in s:
                s = s.replace(SCR, D + ("work/" if f == "check.py" else ""))
                open(D + f, "w").write(s)
    os.makedirs(D + "work", exist_ok=True)
    s = open(D + "build.py").read()
    if "medallion(" in s:
        print(d, "already done"); continue
    if not os.path.exists(D + "build_before_medallion.py"):
        open(D + "build_before_medallion.py", "w").write(s)
    kind = KIND.get(d, "tie")
    if d.startswith("01"):
        a = s.index("lathe(brass, mc, mn, [(0.0, 0.215)"); b = s.index("for _bm in (brass, plate, joint):")
        s = s[:a] + EXEC + "bail = medallion(brass, joint, mc - mn * 0.05, mn, mt, 0.215, 'tie')\n" + s[b:]
    else:
        a = s.index("medal_p, medal_j = bmesh.new(), bmesh.new()"); b = s.index("tag(medal_p, 'joint_attachMeter')")
        R = float(re.search(r"lathe\(medal_p, mc, mn, \[\(0\.0, ([0-9.]+)\)", s[a:b]).group(1))
        s = s[:a] + "medal_p, medal_j = bmesh.new(), bmesh.new()\n" + EXEC + "bail = medallion(medal_p, medal_j, mc - mn * %.4f, mn, mt, %s, '%s')\n" % (0.13 * R, R, kind) + s[b:]
    if d.startswith("09"):
        a = s.index("for z in (6.12, 5.98, 5.84, 5.70):"); b = s.index("tag(pewter, '@shirt')", a)
        s = s[:a] + '''bowdots, zipteeth, ziptape = bmesh.new(), bmesh.new(), bmesh.new()
for sdx in (-1, 1):                                             # pale dots on the bow's wings, as on the original
    for ex_, ez_ in ((-0.12, 0.04), (0.0, -0.07), (0.02, 0.08), (0.13, 0.0), (0.10, -0.09), (-0.10, -0.06)):
        yy = 0.02 - 0.07 * math.sqrt(max(0.0, 1 - (ex_ / 0.25) ** 2 - (ez_ / 0.17) ** 2))
        puck(bowdots, bow_c + Vector((sdx * (0.30 + ex_), yy - 0.002, ez_)), (0, -1, 0), 0.026, 0.012, seg=8)
zipper(zipteeth, ziptape, SS, 6.22, 5.42, 2.3)                  # the zip down the shirt front, as on the original
new_obj("BF_BowDots", bowdots, M_SHIRT, 40)
new_obj("BF_Zipper", zipteeth, M_STEEL, 35)
new_obj("BF_ZipTape", ziptape, M_JOINT, 30, outward=True, thickness=0.01)
''' + s[b:]
        s = s.replace("bow_c = surf(SS, 0.0, 6.36, 0.10)", EXEC + "bow_c = surf(SS, 0.0, 6.36, 0.10)", 1)
        r = open(D + "rig.py").read()
        if "BF_Zipper" not in r:
            assert '"BF_BowTie": "@shirt"' in r
            r = r.replace('"BF_BowTie": "@shirt"', '"BF_BowTie": "@shirt", "BF_BowDots": "@shirt", "BF_Zipper": "@shirt", "BF_ZipTape": "@shirt"')
            open(D + "rig.py", "w").write(r)
    open(D + "build.py", "w").write(s)
    print(d, "patched", kind)
