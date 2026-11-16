"""Give an HD enemy model a seat for the game's health light on its own medallion.

The game hangs the health light (a small round button with a glow) on joint_attachMeter, sized and placed for
the original flat icon. An HD model wears a thick sculpted medallion there, which buries the light. This adds a
child node `hd_meter` under joint_attachMeter, sitting on the medallion's face, turned to face the way the face
does and scaled so the light fills the middle of the medallion. Suit.generateHealthBar() uses it when present.

Usage (from the open-toontown repo root):
    PYTHONPATH=. venv/bin/python add_meter.py <slot> <export.json>
"""
import json, math, os, sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type none\naudio-library-name null\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
from toontown.toonbase import HDTextures
HDTextures.enable()      # without this the model's texture does not resolve, and it is written back with none

slot, export_path = sys.argv[1], sys.argv[2]
path = 'resources-hd/phase_3.5/models/char/%s_hd.bam' % slot
model = loader.loadModel(Filename.fromOsSpecific(os.path.abspath(path)))
char_np = model.find('**/+Character')
jn = model.find('**/joint_attachMeter')
old = jn.find('hd_meter')
if not old.isEmpty():
    old.removeNode()
to_char = LMatrix4f(char_np.getMat(model))
to_char.invertInPlace()
pts, nrm = [], []
for mesh in json.load(open(export_path))["meshes"]:
    for v in mesh["verts"]:
        if len(v["w"]) == 1 and v["w"][0][0] == "joint_attachMeter":
            pts.append(to_char.xformPoint(LPoint3f(-v["p"][0], -v["p"][1], v["p"][2])))
            nrm.append(to_char.xformVec(LVector3f(-v["n"][0], -v["n"][1], v["n"][2])))
if not pts:
    print(slot, "no medallion vertices on joint_attachMeter; nothing added")
    sys.exit(0)
front = LVector3f(0, -1, 0) if sum(n.y for n in nrm if abs(n.y) > 0.5) < 0 else LVector3f(0, 1, 0)
c = LPoint3f(0, 0, 0)
for p in pts:
    c += p
c /= len(pts)
n = LVector3f(0, 0, 0)
for q in nrm:
    if q.dot(front) > 0.6:
        n += q
n.normalize()
# the disc's radius, measured on its lower half so the bail on top does not count
radius = max(((p - c) - n * (p - c).dot(n)).length() for p in pts if abs((p - c).dot(n)) < 0.05 and p.z <= c.z)
ahead = max((p - c).dot(n) for p in pts if ((p - c) - n * (p - c).dot(n)).length() < radius * 0.8)
gui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
lo, hi = gui.find('**/minnieCircle').getTightBounds()
r0 = max(hi.x - lo.x, hi.z - lo.z) / 2.0
hd = jn.attachNewNode(ModelNode('hd_meter'))
hd.node().setPreserveTransform(ModelNode.PTLocal)
axis = front.cross(n)
rot = LQuaternionf()
if axis.length() > 1e-5:
    axis.normalize()
    rot.setFromAxisAngle(math.degrees(math.acos(max(-1.0, min(1.0, front.dot(n))))), axis)
hd.setQuat(char_np, jn.getQuat(char_np) * rot)
hd.setPos(char_np, c + n * (ahead + 0.012 * radius))
hd.setScale(char_np, 0.60 * radius / (3.0 * r0))

# ---- the emblem as its own piece, so the game can light it up
# The raised emblem on the medallion's face is split out of body_hd into a node of its own, `hd_emblem`. It shares
# body_hd's vertices, so it still rides the chest joint. Emblem triangles are the dark-metal ones on the front of the
# medallion: all three corners on joint_attachMeter, proud of the face, and dark in the baked texture.
tex_img = PNMImage()
tex_img.read(Filename.fromOsSpecific(os.path.abspath('resources-hd/phase_3.5/maps/%s_hd.png' % slot)))
body = [m for m in json.load(open(export_path))["meshes"] if m["name"] == "body_hd"][0]
vs = body["verts"]
on_meter = [len(v["w"]) == 1 and v["w"][0][0] == "joint_attachMeter" for v in vs]


def char_pt(v):
    return to_char.xformPoint(LPoint3f(-v["p"][0], -v["p"][1], v["p"][2]))


keep, emblem = [], []
for tri in body["tris"]:
    is_emblem = False
    if all(on_meter[i] for i in tri):
        mid = (char_pt(vs[tri[0]]) + char_pt(vs[tri[1]]) + char_pt(vs[tri[2]])) / 3.0
        # sampled at the middle and toward each corner: a long thin triangle of the disc's face can have its middle
        # land on another island of the texture
        dark = True
        for wts in ((1 / 3.0, 1 / 3.0, 1 / 3.0), (0.7, 0.15, 0.15), (0.15, 0.7, 0.15), (0.15, 0.15, 0.7)):
            u = sum(vs[i]["uv"][0] * w for i, w in zip(tri, wts))
            v_ = sum(vs[i]["uv"][1] * w for i, w in zip(tri, wts))
            x = min(tex_img.getXSize() - 1, max(0, int(u * tex_img.getXSize())))
            y = min(tex_img.getYSize() - 1, max(0, int((1.0 - v_) * tex_img.getYSize())))
            col = tex_img.getXel(x, y)
            dark = dark and max(col[0], col[1], col[2]) < 0.42
        # dark metal anywhere on the front of the disc: the whole relief, side walls included, so all of it lights
        is_emblem = dark and (mid - c).dot(n) > 0.0
    (emblem if is_emblem else keep).append(tri)
old_e = char_np.find('**/hd_emblem')
if not old_e.isEmpty():
    old_e.removeNode()
body_np = char_np.find('**/body_hd')
if emblem and not body_np.isEmpty():
    geom = body_np.node().modifyGeom(0)
    vdata = geom.getVertexData()
    for tris, target in ((keep, None), (emblem, 'hd_emblem')):
        prim = GeomTriangles(Geom.UHStatic)
        for a_, b_, c_ in tris:
            prim.addVertices(a_, b_, c_)
        prim.closePrimitive()
        if target is None:
            geom.clearPrimitives()
            geom.addPrimitive(prim)
        else:
            g2 = Geom(vdata)
            g2.addPrimitive(prim)
            gn = GeomNode(target)
            gn.addGeom(g2)
            e_np = char_np.attachNewNode(gn)
            e_np.setState(body_np.getState())
print(slot, "emblem triangles:", len(emblem), "of", len(body["tris"]))
# Put the texture back on every mesh, the way build_bam.py sets it, whatever state the file was loaded in.
tex_path = 'phase_3.5/maps/%s_hd.png' % slot
tex = loader.loadTexture(tex_path)
tex.setMinfilter(Texture.FTLinearMipmapLinear)
tex.setMagfilter(Texture.FTLinear)
tex.setFilename(Filename(tex_path))
tex.setFullpath(Filename(tex_path))
for gnp in char_np.findAllMatches('**/+GeomNode'):
    gnp.setTexture(tex, 1)
assert len(model.findAllTextures()) == 1, "texture missing on %s" % slot
model.writeBamFile(Filename.fromOsSpecific(os.path.abspath(path)))
print(slot, "medallion radius %.3f, face %.3f ahead of centre, normal (%.2f %.2f %.2f), light scale %.3f, front %s"
      % (radius, ahead, n.x, n.y, n.z, 0.60 * radius / (3.0 * r0), tuple(front)))
