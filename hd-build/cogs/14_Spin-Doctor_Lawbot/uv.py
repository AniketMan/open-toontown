"""Give the whole character one non-overlapping UV layout ("atlas") shared by body_hd and head_hd.
The pinstripe shader keeps its own layer ("stripes"), which only counts stripes and is not a texture layout."""
import bpy, bmesh, math

objs = [bpy.data.objects["body_hd"], bpy.data.objects["head_hd"]]
for ob in objs:
    uvs = ob.data.uv_layers
    if len(uvs) == 0:
        uvs.new(name="stripes")
    if "stripes" not in uvs:
        uvs[0].name = "stripes"
    if "atlas" not in uvs:
        uvs.new(name="atlas")
    uvs.active = uvs["atlas"]
    uvs["stripes"].active_render = True

# the suit shader must read the stripe layer by name, so it no longer depends on which layer is active
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    for link in list(nt.links):
        if link.from_node.type == 'TEX_COORD' and link.from_socket.name == 'UV':
            uv = nt.nodes.get("StripeUV") or nt.nodes.new("ShaderNodeUVMap")
            uv.name = "StripeUV"
            uv.uv_map = "stripes"
            to = link.to_socket
            nt.links.remove(link)
            nt.links.new(uv.outputs["UV"], to)

win = bpy.context.window
area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
region = next(r for r in area.regions if r.type == 'WINDOW')
for o in bpy.context.selected_objects:
    o.select_set(False)
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
with bpy.context.temp_override(window=win, area=area, region=region):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='SELECT')
    # islands split at hard edges (plate edges, cloth turn-backs); scale kept proportional so texel density is even
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.002, margin_method='FRACTION', shape_method='CONCAVE')   # packs by true island shape
    bpy.ops.object.mode_set(mode='OBJECT')

# measure the result: overlap-free packing inside 0..1, and how much of the square is used
stats = {}
used = 0.0
for ob in objs:
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv["atlas"]
    us = [l[uv].uv.x for f in bm.faces for l in f.loops]
    vs = [l[uv].uv.y for f in bm.faces for l in f.loops]
    area_uv = 0.0
    for f in bm.faces:
        p = [l[uv].uv for l in f.loops]
        area_uv += abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) / 2
    used += area_uv
    stats[ob.name] = {"u": [round(min(us), 3), round(max(us), 3)], "v": [round(min(vs), 3), round(max(vs), 3)]}
    bm.free()
result = {"bounds": stats, "atlas_coverage": round(used, 3)}
