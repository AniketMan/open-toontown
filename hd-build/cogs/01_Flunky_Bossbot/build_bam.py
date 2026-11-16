"""Write a replacement enemy model (<slot>_hd.bam) as tools/ENEMY_MODEL_SWAP.md describes.

The game's own body file supplies the skeleton, so joint names, hierarchy and rest pose are exactly the
original's: this loads suit<Body>-mod, removes its meshes, and hangs the HD meshes on the same joints.

Usage (from the open-toontown repo root):
    PYTHONPATH=. venv/bin/python build_bam.py <suit code> <export.json> <slot> [screenshot.png]
"""
import json
import os
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 1400 900\naudio-library-name null\nwant-postfx 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.toonbase import HDTextures
HDTextures.enable()
from toontown.suit import SuitDNA
from direct.actor.Actor import Actor

code, export_path, slot = sys.argv[1], sys.argv[2], sys.argv[3]
shot = sys.argv[4] if len(sys.argv) > 4 else None
body = SuitDNA.getSuitBodyType(code).upper()
src = 'phase_3.5/models/char/suit%s-mod' % body
out_dir = 'resources-hd/phase_3.5/models/char'
out = '%s/%s_hd.bam' % (out_dir, slot)
tex_path = 'phase_3.5/maps/%s_hd.png' % slot

model = loader.loadModel(src)
char_np = model.find('**/+Character')
char = char_np.node()
removed = []
for np in model.findAllMatches('**/+GeomNode'):
    removed.append(np.getName())
    np.removeNode()

joints = {}


def collect(group):
    if isinstance(group, CharacterJoint):
        joints[group.getName()] = group
    for i in range(group.getNumChildren()):
        collect(group.getChild(i))


collect(char.getBundle(0))
to_char = LMatrix4f(char_np.getMat(model))
to_char.invertInPlace()

array = GeomVertexArrayFormat()
array.addColumn(InternalName.getVertex(), 3, Geom.NTFloat32, Geom.CPoint)
array.addColumn(InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CNormal)
array.addColumn(InternalName.getTexcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
blend_array = GeomVertexArrayFormat()
blend_array.addColumn(InternalName.getTransformBlend(), 1, Geom.NTUint16, Geom.CIndex)
fmt = GeomVertexFormat()
fmt.addArray(array)
fmt.addArray(blend_array)
spec = GeomVertexAnimationSpec()
spec.setPanda()
fmt.setAnimation(spec)
fmt = GeomVertexFormat.registerFormat(fmt)

tex = loader.loadTexture(tex_path)
tex.setMinfilter(Texture.FTLinearMipmapLinear)
tex.setMagfilter(Texture.FTLinear)
tex.setFilename(Filename(tex_path))
tex.setFullpath(Filename(tex_path))

jvt = {}
data = json.load(open(export_path))
stats = {}
missing = set()
for mesh in data["meshes"]:
    table = TransformBlendTable()
    blends = {}
    vdata = GeomVertexData(mesh["name"], fmt, Geom.UHStatic)
    vdata.setNumRows(len(mesh["verts"]))
    wv, wn, wt = GeomVertexWriter(vdata, 'vertex'), GeomVertexWriter(vdata, 'normal'), GeomVertexWriter(vdata, 'texcoord')
    wb = GeomVertexWriter(vdata, InternalName.getTransformBlend())
    for v in mesh["verts"]:
        # Blender (x left of character, -y front) -> game (y forward): a half turn about the vertical axis
        p = to_char.xformPoint(LPoint3f(-v["p"][0], -v["p"][1], v["p"][2]))
        n = to_char.xformVec(LVector3f(-v["n"][0], -v["n"][1], v["n"][2]))
        n.normalize()
        wv.addData3(p)
        wn.addData3(n)
        wt.addData2(v["uv"][0], v["uv"][1])
        ws = sorted(((nm, w) for nm, w in v["w"] if nm in joints), key=lambda t: -t[1])[:3]
        missing.update(nm for nm, w in v["w"] if nm not in joints)
        total = sum(w for nm, w in ws) or 1.0
        key = tuple((nm, round(w / total, 4)) for nm, w in ws)
        if key not in blends:
            tb = TransformBlend()
            for nm, w in key:
                if nm not in jvt:
                    jvt[nm] = JointVertexTransform(joints[nm])
                tb.addTransform(jvt[nm], w)
            blends[key] = table.addBlend(tb)
        wb.addData1i(blends[key])
    table.setRows(SparseArray.lowerOn(len(mesh["verts"])))      # which vertices the table animates: without this none move
    vdata.setTransformBlendTable(table)
    prim = GeomTriangles(Geom.UHStatic)
    for a, bb, c in mesh["tris"]:
        prim.addVertices(a, bb, c)
    prim.closePrimitive()
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode(mesh["name"])
    node.addGeom(geom)
    np = char_np.attachNewNode(node)
    np.setTexture(tex, 1)
    stats[mesh["name"]] = (len(mesh["verts"]), len(mesh["tris"]), len(blends))

os.makedirs(out_dir, exist_ok=True)
model.writeBamFile(Filename.fromOsSpecific(os.path.abspath(out)))
print("wrote", out, os.path.getsize(out), "bytes; removed original meshes:", removed)
print("meshes (verts, tris, distinct weightings):", stats, "| weights on joints the body lacks:", sorted(missing))

# ---- check it as section 4.5 of the doc says: same joints, and the game's animations bind
orig = Actor(src)
new = Actor('phase_3.5/models/char/%s_hd' % slot, {'walk': 'phase_3.5/models/char/suit%s-walk' % body,
                                                    'neutral': 'phase_3.5/models/char/suit%s-neutral' % body})
a = sorted(j.getName() for j in orig.getJoints())
c = sorted(j.getName() for j in new.getJoints())
print("joint lists identical:", a == c, len(a), len(c))
print("frames: walk", new.getNumFrames('walk'), "neutral", new.getNumFrames('neutral'))

if shot:
    from toontown.suit import Suit
    b.setBackgroundColor(0.82, 0.82, 0.82)
    b.disableMouse()
    views = []
    scale = 4.0 / 4.14 if code == 'f' else 1.0
    for i, (anim, frame, h) in enumerate((('neutral', 0, 180), ('neutral', 0, 135), ('walk', 6, 180), ('walk', 12, 110))):
        act = Actor('phase_3.5/models/char/%s_hd' % slot, {'walk': 'phase_3.5/models/char/suit%s-walk' % body,
                                                            'neutral': 'phase_3.5/models/char/suit%s-neutral' % body})
        act.reparentTo(b.render)
        act.setScale(scale)
        act.setPos((i - 1.5) * 5.2, 0, 0)
        act.setH(h)
        act.pose(anim, frame)
        views.append(act)
    b.camLens.setFov(28)
    b.camera.setPos(0, -46, 3.4)
    b.camera.lookAt(0, 0, 2.4)
    b.graphicsEngine.renderFrame()
    b.graphicsEngine.renderFrame()
    b.win.saveScreenshot(Filename.fromOsSpecific(os.path.abspath(shot)))
    print("screenshot", shot)
