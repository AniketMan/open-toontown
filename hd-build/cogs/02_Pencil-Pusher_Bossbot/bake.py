"""Bake the procedural materials to one texture set for the whole character (body_hd + head_hd, "atlas" UVs):
base colour and a tangent-space normal map. Then give both meshes a single material that uses them."""
import bpy, os

SLOT = "02_Pencil-Pusher_Bossbot"
OUT = "/Users/aniketbhatt/Documents/GitHub/open-toontown/resources-hd/phase_3.5/maps/"
SIZE = 2048
objs = [bpy.data.objects["body_hd"], bpy.data.objects["head_hd"]]
scene = bpy.context.scene


def image(name, colorspace, fill):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    img.generated_color = fill
    img.colorspace_settings.name = colorspace
    return img


base = image(SLOT + "_hd", "sRGB", (0.17, 0.045, 0.032, 1))
normal = image(SLOT + "_hd_normal", "Non-Color", (0.5, 0.5, 1.0, 1))

mats = {m for ob in objs for m in ob.data.materials if m and m.use_nodes}
targets, metal = {}, {}
for m in mats:
    nt = m.node_tree
    node = nt.nodes.get("BAKE_TARGET") or nt.nodes.new("ShaderNodeTexImage")
    node.name = "BAKE_TARGET"
    targets[m] = node
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    metal[m] = bsdf.inputs["Metallic"].default_value


def bake(img, kind, **kw):
    for m, node in targets.items():
        node.image = img
        m.node_tree.nodes.active = node
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for ob in objs:
        ob.select_set(True)
        ob.data.uv_layers.active = ob.data.uv_layers["atlas"]
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.bake(type=kind, margin=3, use_clear=True, **kw)


keep_engine = scene.render.engine
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
try:
    scene.cycles.device = 'GPU'
except Exception:
    pass
# metal has no diffuse colour to bake: bake colour with metallic off, then restore
for m in mats:
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Metallic"].default_value = 0.0
bake(base, 'DIFFUSE', pass_filter={'COLOR'})
for m in mats:
    next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Metallic"].default_value = metal[m]
scene.cycles.samples = 4
bake(normal, 'NORMAL', normal_space='TANGENT')
scene.render.engine = keep_engine

os.makedirs(OUT, exist_ok=True)
for img, fn in ((base, SLOT + "_hd.png"), (normal, SLOT + "_hd_normal.png")):
    img.filepath_raw = OUT + fn
    img.file_format = 'PNG'
    img.save()

# one material for the whole character, reading the baked textures through the atlas UVs
bm = bpy.data.materials.get("PP_Baked") or bpy.data.materials.new("PP_Baked")
bm.use_nodes = True
N, L = bm.node_tree.nodes, bm.node_tree.links
N.clear()
out = N.new("ShaderNodeOutputMaterial")
bsdf = N.new("ShaderNodeBsdfPrincipled")
uv = N.new("ShaderNodeUVMap")
uv.uv_map = "atlas"
tb = N.new("ShaderNodeTexImage")
tb.image = base
tn = N.new("ShaderNodeTexImage")
tn.image = normal
nm = N.new("ShaderNodeNormalMap")
nm.uv_map = "atlas"
L.new(uv.outputs["UV"], tb.inputs["Vector"])
L.new(uv.outputs["UV"], tn.inputs["Vector"])
L.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
L.new(tn.outputs["Color"], nm.inputs["Color"])
L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.6
L.new(bsdf.outputs[0], out.inputs[0])
for m in mats:
    m.use_fake_user = True                    # the procedural originals stay in the file
for ob in objs:
    ob.data.materials.clear()
    ob.data.materials.append(bm)
    for p in ob.data.polygons:
        p.material_index = 0
    ob.data.uv_layers["atlas"].active_render = True
result = {"base": OUT + SLOT + "_hd.png", "normal": OUT + SLOT + "_hd_normal.png", "size": SIZE,
          "bytes": [os.path.getsize(OUT + SLOT + "_hd.png"), os.path.getsize(OUT + SLOT + "_hd_normal.png")]}
