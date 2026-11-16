"""Dump a cog's skeleton and skin weights, assembled and posed exactly as tools/export_cog_models.py exports it
(neutral pose, frame 0, game scale). Output axes match the exported .obj converted to Blender: x right, -y front, z up.

Usage (from the open-toontown repo root):
    PYTHONPATH=. venv/bin/python extract_rig.py f out.json
"""
import json
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 64 64\naudio-library-name null\nwant-postfx 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.suit import Suit, SuitDNA

code, out = sys.argv[1], sys.argv[2]
s = Suit.Suit()
d = SuitDNA.SuitDNA()
d.newSuit(code)
s.setDNA(d)
s.reparentTo(b.render)
s.setPosHpr(0, 0, 0, 0, 0, 0)
s.pose('neutral', 0)
s.update()
b.graphicsEngine.renderFrame()
thread = Thread.getCurrentThread()


def to_blender(p):                       # game (x right, y forward, z up) -> same frame as the imported .obj
    return [-p[0], -p[1], p[2]]


def mat_rows(m):
    return [[m.getCell(r, c) for c in range(4)] for r in range(4)]


data = {"code": code, "scale": s.getScale()[0], "joints": [], "geoms": [], "nodes": []}

# ---- skeleton: every joint with its parent and its net transform in the posed, scaled suit
char_np = s.find('**/+Character')
char = char_np.node()
bundle = char.getBundle(0)
char_mat = char_np.getMat(s)


def walk(group, parent, out):
    name = group.getName()
    if isinstance(group, CharacterJoint):
        net = LMatrix4f()
        group.getNetTransform(net)
        m = net * char_mat
        origin = m.xformPoint(LPoint3f(0, 0, 0))
        out.append({
            "name": name, "parent": parent,
            "head": to_blender(origin),
            "x": to_blender(m.xformVec(LVector3f(1, 0, 0))),
            "y": to_blender(m.xformVec(LVector3f(0, 1, 0))),
            "z": to_blender(m.xformVec(LVector3f(0, 0, 1))),
        })
        parent = name
    for i in range(group.getNumChildren()):
        walk(group.getChild(i), parent, out)


walk(bundle, None, data["joints"])

# ---- a few frames of the game's own animations, as joint transforms, to test the HD skin against
data["poses"] = {}
for spec in sys.argv[3:]:
    anim, frame = spec.split(":")
    s.pose(anim, int(frame))
    s.update()
    b.graphicsEngine.renderFrame()
    frame_joints = []
    walk(bundle, None, frame_joints)
    data["poses"][spec] = frame_joints
s.pose('neutral', 0)
s.update()
b.graphicsEngine.renderFrame()

# ---- the body's own rest (bind) pose at its native size, straight from suit<Body>-mod with no animation applied
from direct.actor.Actor import Actor
body = SuitDNA.getSuitBodyType(code).upper()
rest_actor = Actor('phase_3.5/models/char/suit%s-mod' % body)
rest_np = rest_actor.find('**/+Character')
char_mat_saved = char_mat
char_mat = rest_np.getMat(rest_actor)
data["body"] = body
data["suit_scale"] = s.scale
data["bind"] = []
walk(rest_np.node().getBundle(0), None, data["bind"])
char_mat = char_mat_saved

# ---- geometry: posed vertex positions (same traversal and order as the .obj export) and their joint weights
for np in s.findAllMatches('**/+GeomNode'):
    if np.isHidden() or any(a.isHidden() for a in np.getAncestors()):
        continue
    if any('shadow' in a.getName().lower() or 'nametag' in a.getName().lower() for a in np.getAncestors()):
        continue
    node = np.node()
    mat = np.getMat(s)
    anc = [a.getName() for a in np.getAncestors()]
    for gi in range(node.getNumGeoms()):
        geom = node.getGeom(gi).decompose()
        vd = geom.getVertexData()
        posed = vd.animateVertices(True, thread)
        vr = GeomVertexReader(posed, 'vertex')
        table = vd.getTransformBlendTable()
        br = GeomVertexReader(vd, 'transform_blend') if (table and vd.hasColumn('transform_blend')) else None
        verts, weights = [], []
        for _ in range(posed.getNumRows()):
            verts.append(to_blender(mat.xformPoint(vr.getData3())))
            w = {}
            if br is not None:
                blend = table.getBlend(br.getData1i())
                for k in range(blend.getNumTransforms()):
                    t = blend.getTransform(k)
                    if isinstance(t, JointVertexTransform):
                        w[t.getJoint().getName()] = w.get(t.getJoint().getName(), 0.0) + blend.getWeight(k)
            weights.append(w)
        data["geoms"].append({"name": np.getName() or "part", "ancestors": anc, "verts": verts, "weights": weights})

# ---- which nodes hang rigidly off which exposed joint (head, glasses, icon ...)
for np in s.findAllMatches('**/*'):
    data["nodes"].append({"name": np.getName(), "type": np.node().getType().getName(),
                          "parent": np.getParent().getName() if not np.getParent().isEmpty() else None})

json.dump(data, open(out, 'w'))
print("joints", len(data["joints"]), "geoms", len(data["geoms"]), "verts", sum(len(g["verts"]) for g in data["geoms"]))
for g in data["geoms"]:
    used = sorted({j for w in g["weights"] for j in w})
    print("%-10s verts %3d  ancestors %s\n           joints: %s" % (g["name"], len(g["verts"]), "/".join(g["ancestors"][:4]), ", ".join(used) or "(rigid)"))
