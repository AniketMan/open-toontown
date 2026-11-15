#!/usr/bin/env python
"""
Writes a reference set for the player characters (Toons), the same kind of
set tools/export_cog_models.py + the cog turnaround sheets give for the cogs.

Into the output folder (default ../open-toontown-hd/toon-turnarounds):

  head_<species>_<code>.png   one sheet per head (front, three-quarter, side,
                              back, top), set up the way ToonHead sets it up
  torso_<size>_<clothes>.png  one sheet per torso model (front, three-quarter,
                              side, back), neutral pose
  legs_<size>.png             one sheet per legs model
  <same name>.obj/.mtl/.bam   the mesh of each piece (.obj is Y-up, game
                              units, in the pose shown; .bam keeps the rig)
  examples/<Toon name>.png    whole Toons built by toontown.toon.Toon
  manifest.json               everything measured while exporting
  README.md                   how a Toon is put together, written from the
                              code and from those measurements

Nothing is launched and nothing is captured from the screen: every picture is
rendered in an offscreen buffer.  The game's original textures are used (the
HD texture pack is not switched on).

Usage (from the repository root, with the game's Python):
    PYTHONPATH=. venv/bin/python tools/export_toon_models.py [output folder]
"""
import json
import os
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 64 64\naudio-library-name null\nwant-postfx 0\n'
                    'notify-level warning\ndefault-directnotify-level warning\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from direct.actor.Actor import Actor
from otp.otpbase import OTPGlobals
from toontown.toon import Toon, ToonDNA, ToonHead, NPCToons

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '../open-toontown-hd/toon-turnarounds')
EXAMPLES = os.path.join(OUT, 'examples')
os.makedirs(EXAMPLES, exist_ok=True)

BACKGROUND = (0.5, 0.5, 0.5, 1.0)       # plain mid grey
SUPERSAMPLE = 2                         # rendered at 2x, then filtered down
MARGIN = 1.10                           # the piece fills 1/MARGIN of a tile

# Colours used on the single pieces, so the sheets do not show white,
# untinted meshes.  All are entries of the game's own colour tables.
BODY_COLOR = 25      # ToonDNA.allColorsList index; ToonDNA.defaultColor() returns 25
GLOVE_COLOR = 0      # white; isValidNetString() only accepts 0 for gloves
TOP_COLOR = 8        # ToonDNA.ClothesColors index, shirt and sleeves
BOTTOM_COLOR = 10    # ToonDNA.ClothesColors index, shorts / skirt

# The user's own toon.
OWN_TOON_FILE = 'astron/databases/astrondb/100000002.yaml'
# The game's own characters shown as examples (ids in NPCToons.NPCToonDict).
EXAMPLE_NPCS = [2006,   # Clerk Clark: dog, long torso, long legs
                2207,   # Will Wiseacre: mouse, short torso, short legs
                1214,   # Gusty Kate: cat in a skirt
                3306,   # Paula Behr: bear in a skirt
                2001]   # Flippy: dog, medium torso and legs

# name, heading, pitch of the turntable the piece stands on.  The camera
# stays put and looks along +Y; Toons face +Y, so heading 180 shows the front.
VIEWS = [('front', 180, 0), ('three-quarter', 145, 0), ('side', 90, 0), ('back', 0, 0)]
TOP_VIEW = ('top', 180, -90)

scene = NodePath('toon-export-scene')
turntable = scene.attachNewNode('turntable')
_buffers = {}


def get_buffer(w, h):
    if (w, h) not in _buffers:
        tex = Texture()
        buf = b.win.makeTextureBuffer('tile-%dx%d' % (w, h), w * SUPERSAMPLE, h * SUPERSAMPLE, tex, True)
        buf.setClearColor(VBase4(*BACKGROUND))
        buf.setClearColorActive(True)
        lens = OrthographicLens()
        lens.setNearFar(1, 400)
        cam = scene.attachNewNode(Camera('tile-cam', lens))
        cam.setPosHpr(0, -200, 0, 0, 0, 0)
        buf.makeDisplayRegion().setCamera(cam)
        _buffers[(w, h)] = (buf, tex, cam, lens)
    for key, entry in _buffers.items():
        entry[0].setActive(key == (w, h))
    return _buffers[(w, h)]


def visible_geom_nodes(root):
    """The GeomNodes the game would draw: nothing hidden or stashed, no drop
    shadow or nametag, and of a Toon only the highest level of detail."""
    found = []
    for np in root.findAllMatches('**/+GeomNode'):
        chain = [np] + [a for a in np.getAncestors() if a != root and root.isAncestorOf(a)]
        if any(a.isHidden() for a in chain):
            continue
        names = [a.getName() for a in chain]
        if any('shadow' in n.lower() or 'nametag' in n.lower() for n in names):
            continue
        if '500' in names or '250' in names:
            continue
        found.append(np)
    return found


def posed_points(root):
    """Every drawn vertex, in root's coordinates, in the current pose."""
    thread = Thread.getCurrentThread()
    pts = []
    for np in visible_geom_nodes(root):
        mat = np.getMat(root)
        node = np.node()
        for gi in range(node.getNumGeoms()):
            vdata = node.getGeom(gi).getVertexData().animateVertices(True, thread)
            vr = GeomVertexReader(vdata, 'vertex')
            while not vr.isAtEnd():
                pts.append(mat.xformPoint(vr.getData3()))
    return pts


def render_sheet(root, path, views, tile):
    """Renders root once per view into tiles laid side by side."""
    w, h = tile
    buf, tex, cam, lens = get_buffer(w, h)
    root.reparentTo(turntable)
    root.setPosHpr(0, 0, 0, 0, 0, 0)
    pts = posed_points(root)
    boxes = []
    for name, heading, pitch in views:
        turntable.setPosHpr(0, 0, 0, heading, pitch, 0)
        mat = turntable.getMat(scene)
        xs, zs = [], []
        for p in pts:
            q = mat.xformPoint(p)
            xs.append(q[0]); zs.append(q[2])
        boxes.append((min(xs), max(xs), min(zs), max(zs)))
    # one scale for the whole sheet, so the views can be measured against each other
    need_w = max(bx[1] - bx[0] for bx in boxes) * MARGIN
    need_h = max(bx[3] - bx[2] for bx in boxes) * MARGIN
    film_h = max(need_h, need_w * h / float(w))
    lens.setFilmSize(film_h * w / float(h), film_h)
    sheet = PNMImage(w * len(views), h, 3)
    for i, (name, heading, pitch) in enumerate(views):
        turntable.setPosHpr(0, 0, 0, heading, pitch, 0)
        bx = boxes[i]
        cam.setPos((bx[0] + bx[1]) / 2.0, -200, (bx[2] + bx[3]) / 2.0)
        b.graphicsEngine.renderFrame()
        b.graphicsEngine.renderFrame()
        big = PNMImage()
        tex.store(big)
        small = PNMImage(w, h, 3)
        small.boxFilterFrom(1.0, big)
        sheet.copySubImage(small, i * w, 0)
    sheet.write(Filename.fromOsSpecific(path))
    turntable.setPosHpr(0, 0, 0, 0, 0, 0)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    return {'min': [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
            'max': [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
            'units_per_tile_height': round(film_h, 3)}


def export_mesh(root, folder, base):
    """Same .obj/.mtl/.bam export as tools/export_cog_models.py."""
    thread = Thread.getCurrentThread()
    materials = {}
    lines = ['# %s' % base, 'mtllib %s.mtl' % base]
    faces = []
    nv = 0
    tris = 0
    nodes = []
    for np in visible_geom_nodes(root):
        node = np.node()
        mat = np.getMat(root)
        net = np.getState(root)
        name = np.getName() or np.getParent().getName() or 'part'
        nodes.append(name)
        for gi in range(node.getNumGeoms()):
            state = net.compose(node.getGeomState(gi))
            tex = None
            ta = state.getAttrib(TextureAttrib)
            if ta is not None and not ta.isOff() and ta.getNumOnStages():
                tex = ta.getTexture()
            colour = (1.0, 1.0, 1.0)
            ca = state.getAttrib(ColorAttrib)
            if ca is not None and ca.getColorType() == ColorAttrib.TFlat:
                colour = tuple(ca.getColor())[:3]
            cs = state.getAttrib(ColorScaleAttrib)
            if cs is not None:
                colour = tuple(colour[k] * cs.getScale()[k] for k in range(3))
            key = (tex.getName() if tex else None, tuple(round(c, 3) for c in colour))
            if key not in materials:
                path = Filename(tex.getFullpath()).toOsSpecific() if tex and tex.hasFullpath() else None
                materials[key] = ('mat%02d_%s' % (len(materials), (key[0] or 'plain').replace(' ', '_')), path, colour)
            geom = node.getGeom(gi).decompose()
            vdata = geom.getVertexData().animateVertices(True, thread)
            vr = GeomVertexReader(vdata, 'vertex')
            hasN, hasT = vdata.hasColumn('normal'), vdata.hasColumn('texcoord')
            nr = GeomVertexReader(vdata, 'normal') if hasN else None
            tr = GeomVertexReader(vdata, 'texcoord') if hasT else None
            rows = vdata.getNumRows()
            for _ in range(rows):
                p = mat.xformPoint(vr.getData3())
                lines.append('v %.5f %.5f %.5f' % (p[0], p[2], -p[1]))
                if hasN:
                    n = mat.xformVec(nr.getData3()); n.normalize()
                    lines.append('vn %.4f %.4f %.4f' % (n[0], n[2], -n[1]))
                else:
                    lines.append('vn 0 1 0')
                uv = tr.getData2() if hasT else (0, 0)
                lines.append('vt %.5f %.5f' % (uv[0], uv[1]))
            faces.append('g %s' % name)
            faces.append('usemtl %s' % materials[key][0])
            for prim in geom.getPrimitives():
                if prim.getNumVerticesPerPrimitive() != 3:
                    continue
                for k in range(prim.getNumPrimitives()):
                    st = prim.getPrimitiveStart(k)
                    i = [prim.getVertex(st + j) + nv + 1 for j in range(3)]
                    faces.append('f %d/%d/%d %d/%d/%d %d/%d/%d' % (i[0], i[0], i[0], i[1], i[1], i[1], i[2], i[2], i[2]))
                    tris += 1
            nv += rows
    with open(os.path.join(folder, base + '.obj'), 'w') as f:
        f.write('\n'.join(lines + faces) + '\n')
    with open(os.path.join(folder, base + '.mtl'), 'w') as f:
        for name, path, colour in materials.values():
            f.write('newmtl %s\nKd %.3f %.3f %.3f\nKs 0 0 0\n' % ((name,) + colour))
            if path:
                f.write('map_Kd %s\n' % path)
            f.write('\n')
    root.writeBamFile(Filename.fromOsSpecific(os.path.join(folder, base + '.bam')))
    textures = sorted(set(k[0] for k in materials if k[0]))
    return {'triangles': tris, 'nodes': nodes, 'textures': textures}


def piece_dna(head='dls', torso='ms', legs='m', gender='m'):
    dna = ToonDNA.ToonDNA()
    dna.newToonFromProperties(head, torso, legs, gender, BODY_COLOR, GLOVE_COLOR, BODY_COLOR, BODY_COLOR,
                              0, TOP_COLOR, 0, TOP_COLOR, 0, BOTTOM_COLOR)
    return dna


def head_prefix(code):
    return ToonHead.HeadDict[code] if code[0] == 'd' else ToonHead.HeadDict[code[0]]


def model_nodes(path):
    """Names of the GeomNodes a model file holds, as stored."""
    m = loader.loadModel(path)
    names = [np.getName() or '(unnamed, under %s)' % np.getParent().getName() for np in m.findAllMatches('**/+GeomNode')]
    return names


def joint_tree(path):
    """The joint hierarchy of a model file, and where its exposed joints sit at rest."""
    m = loader.loadModel(path)
    char = m.find('**/+Character')
    lines = []

    def walk(group, depth):
        for i in range(group.getNumChildren()):
            child = group.getChild(i)
            if isinstance(child, CharacterJoint):
                lines.append('  ' * depth + child.getName())
                walk(child, depth + 1)
            else:
                walk(child, depth)

    walk(char.node().getBundle(0), 0)
    exposed = {}
    for np in m.findAllMatches('**/+ModelNode'):
        if np.node().hasEffect(CharacterJointEffect.getClassType()):
            pos = np.getPos(m); hpr = np.getHpr(m)
            exposed[np.getName()] = {'pos': [round(v, 4) for v in pos], 'hpr': [round(v, 3) for v in hpr]}
    return {'character': char.getName(), 'joints': lines, 'exposed': exposed}


def count_triangles(path):
    m = loader.loadModel(path, okMissing=True)
    if not m:
        return None
    total = 0
    for np in m.findAllMatches('**/+GeomNode'):
        for gi in range(np.node().getNumGeoms()):
            for prim in np.node().getGeom(gi).decompose().getPrimitives():
                total += prim.getNumPrimitives()
    return total


def build_head(code):
    """A head the way ToonHead.generateToonHead leaves it for a male toon:
    the unused long/short parts removed, the emotion muzzles hidden, eyes
    open, no eyelashes."""
    head = ToonHead.ToonHead()
    dna = piece_dna(head=code)
    head.generateToonHead(1, dna, ('1000',))
    head.generateToonColor(dna)
    if code[0] == 'd':
        head.loadAnims({'neutral': Toon.HeadAnimDict[code]['neutral']}, 'head', 'lodRoot')
        head.pose('neutral', 0)
        head.update(force=True)
    return head


def build_torso(key):
    """A torso model in the neutral pose, coloured the way
    Toon.generateToonColor / generateToonClothes colour it."""
    path = 'phase_3' + Toon.TorsoDict[key] + '1000'
    if not loader.loadModel(path, okMissing=True):
        return None
    torso = Actor(path, {'neutral': Toon.TorsoAnimDict[key]['neutral']})
    dna = piece_dna(torso=key)
    for name in ('arms', 'neck'):
        torso.find('**/' + name).setColor(dna.getArmColor())
    torso.find('**/hands').setColor(dna.getGloveColor())
    if len(key) == 1:
        torso.findAllMatches('**/torso*').setColor(dna.getArmColor())
    else:
        top = ToonDNA.ClothesColors[TOP_COLOR]
        bottom = ToonDNA.ClothesColors[BOTTOM_COLOR]
        dark = bottom * 0.5
        dark.setW(1.0)
        torso.find('**/torso-top').setColor(top)
        torso.find('**/sleeves').setColor(top)
        torso.findAllMatches('**/torso-bot').setColor(bottom)
        torso.findAllMatches('**/torso-bot-cap').setColor(dark)
    torso.pose('neutral', 0)
    torso.update(force=True)
    return torso


def build_legs(key):
    """A legs model in the neutral pose; the shoe and boot meshes stashed as
    Toon.generateToonLegs stashes them, leaving the bare feet."""
    path = 'phase_3' + Toon.LegDict[key] + '1000'
    legs = Actor(path, {'neutral': Toon.LegsAnimDict[key]['neutral']})
    for name in ('boots_short', 'boots_long', 'shoes'):
        legs.findAllMatches('**/' + name).stash()
    dna = piece_dna(legs=key)
    for name in ('legs', 'feet'):
        legs.find('**/%s;+s' % name).setColor(dna.getLegColor())
    legs.pose('neutral', 0)
    legs.update(force=True)
    return legs


def build_toon(dna_string):
    toon = Toon.Toon()
    toon.setDNAString(dna_string)
    toon.pose('neutral', 0)
    toon.update(force=True)
    if getattr(toon, 'dropShadow', None):
        toon.dropShadow.hide()
    try:
        toon.nametag3d.hide()
    except Exception:
        pass
    lod = toon.getLODNode()
    if lod is not None:
        # draw the "1000" level whatever the camera distance
        lod.forceSwitch(lod.getHighestSwitch())
    return toon


def read_own_toon():
    name, hexstr = None, None
    with open(OWN_TOON_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith('setName:'):
                name = line.split('"')[1]
            elif line.startswith('setDNAString:'):
                hexstr = line.split('<')[1].split('>')[0]
    raw = bytes.fromhex(hexstr)
    # the database stores the field as a "blob": a 2-byte little-endian length, then the bytes
    length = raw[0] | (raw[1] << 8)
    return name, raw[2:2 + length]


def describe_dna(dna):
    bottoms = ToonDNA.BoyShorts[dna.botTex] if dna.gender == 'm' else ToonDNA.GirlBottoms[dna.botTex][0]
    return {'head': dna.head, 'torso': dna.torso, 'legs': dna.legs, 'gender': dna.gender,
            'species': dna.getAnimal(),
            'headColor': dna.headColor, 'armColor': dna.armColor, 'legColor': dna.legColor,
            'gloveColor': dna.gloveColor,
            'headColorRGB': [round(v, 3) for v in tuple(dna.getHeadColor())[:3]],
            'armColorRGB': [round(v, 3) for v in tuple(dna.getArmColor())[:3]],
            'legColorRGB': [round(v, 3) for v in tuple(dna.getLegColor())[:3]],
            'topTex': dna.topTex, 'topTexFile': ToonDNA.Shirts[dna.topTex], 'topTexColor': dna.topTexColor,
            'sleeveTex': dna.sleeveTex, 'sleeveTexFile': ToonDNA.Sleeves[dna.sleeveTex],
            'sleeveTexColor': dna.sleeveTexColor,
            'botTex': dna.botTex, 'botTexFile': bottoms, 'botTexColor': dna.botTexColor}


def safe_name(name):
    return ''.join(c if c.isalnum() else '_' for c in name).strip('_')


manifest = {'pieces': [], 'examples': [], 'skipped': [], 'lods': [], 'joints': {}, 'anims': {}}

# ---------------------------------------------------------------- heads
for code in ToonDNA.toonHeadTypes:
    species = ToonDNA.getSpeciesName(code)
    base = 'head_%s_%s' % (species, code)
    source = 'phase_3' + head_prefix(code) + '1000'
    stored = model_nodes(source)
    head = build_head(code)
    info = render_sheet(head, os.path.join(OUT, base + '.png'), VIEWS + [TOP_VIEW], (600, 600))
    info.update(export_mesh(head, OUT, base))
    info.update({'file': base, 'kind': 'head', 'code': code, 'species': species, 'source': source,
                 'stored_nodes': stored})
    if code[0] == 'd':
        info['extra_source'] = 'phase_3' + ToonHead.DogMuzzleDict[code] + '1000'
        info['extra_nodes'] = model_nodes(info['extra_source'])
    manifest['pieces'].append(info)
    print('%s: %d triangles, drawn nodes %s' % (base, info['triangles'], info['nodes']))
    head.detachNode()

# ---------------------------------------------------------------- torsos
CLOTHES = {1: 'undressed', 's': 'shorts', 'd': 'skirt'}
for key in ('ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l'):
    base = 'torso_%ss_%s' % (key[0], CLOTHES[1] if len(key) == 1 else CLOTHES[key[1]])
    source = 'phase_3' + Toon.TorsoDict[key] + '1000'
    torso = build_torso(key)
    if torso is None:
        manifest['skipped'].append({'file': base, 'source': source,
                                    'reason': 'model file is not in resources/ (Toon.TorsoDict[%r] names it, the loader cannot find it)' % key})
        print('%s: SKIPPED, %s does not exist' % (base, source))
        continue
    info = render_sheet(torso, os.path.join(OUT, base + '.png'), VIEWS, (600, 600))
    info.update(export_mesh(torso, OUT, base))
    info.update({'file': base, 'kind': 'torso', 'code': key, 'source': source, 'stored_nodes': model_nodes(source)})
    manifest['pieces'].append(info)
    print('%s: %d triangles, drawn nodes %s' % (base, info['triangles'], info['nodes']))
    torso.detachNode()

# ---------------------------------------------------------------- legs
for key in ToonDNA.toonLegTypes:
    base = 'legs_%s' % key
    source = 'phase_3' + Toon.LegDict[key] + '1000'
    legs = build_legs(key)
    info = render_sheet(legs, os.path.join(OUT, base + '.png'), VIEWS, (450, 600))
    info.update(export_mesh(legs, OUT, base))
    info.update({'file': base, 'kind': 'legs', 'code': key, 'source': source, 'stored_nodes': model_nodes(source)})
    manifest['pieces'].append(info)
    print('%s: %d triangles, drawn nodes %s' % (base, info['triangles'], info['nodes']))
    legs.detachNode()

# ---------------------------------------------------------------- whole toons
examples = []
own_name, own_dna = read_own_toon()
examples.append((own_name, own_dna, OWN_TOON_FILE))
for npcId in EXAMPLE_NPCS:
    zone, name, dnaType, gender, protected, kind = NPCToons.NPCToonDict[npcId]
    dna = ToonDNA.ToonDNA()
    dna.newToonFromProperties(*dnaType)
    examples.append((name, dna.makeNetString(), 'toontown/toon/NPCToons.py NPCToonDict[%d]' % npcId))
for name, dna_string, origin in examples:
    toon = build_toon(dna_string)
    base = safe_name(name)
    info = render_sheet(toon, os.path.join(EXAMPLES, base + '.png'), VIEWS, (450, 700))
    info.update({'file': 'examples/' + base, 'name': name, 'origin': origin, 'dna_hex': dna_string.hex(),
                 'height': round(toon.getHeight(), 3),
                 'body_scale': OTPGlobals.toonBodyScales[toon.style.getAnimal()]})
    info.update(describe_dna(toon.style))
    manifest['examples'].append(info)
    print('examples/%s: %s' % (base, {k: info[k] for k in ('head', 'torso', 'legs', 'gender', 'height')}))
    toon.detachNode()

# ---------------------------------------------------------------- measurements for the README
for label, prefixes in (('head', sorted(set(ToonHead.HeadDict.values()))),
                        ('dog muzzles', sorted(set(ToonHead.DogMuzzleDict.values()))),
                        ('torso', [Toon.TorsoDict[k] for k in ('ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l')]),
                        ('legs', [Toon.LegDict[k] for k in ('s', 'm', 'l')])):
    for prefix in prefixes:
        manifest['lods'].append({'kind': label, 'prefix': 'phase_3' + prefix,
                                 'triangles': {lod: count_triangles('phase_3' + prefix + lod) for lod in ('1000', '500', '250')}})
for key, path in (('head dls', 'phase_3' + ToonHead.HeadDict['dls'] + '1000'),
                  ('head dss', 'phase_3' + ToonHead.HeadDict['dss'] + '1000'),
                  ('head dsl', 'phase_3' + ToonHead.HeadDict['dsl'] + '1000'),
                  ('head dll', 'phase_3' + ToonHead.HeadDict['dll'] + '1000'),
                  ('head cat', 'phase_3' + ToonHead.HeadDict['c'] + '1000'),
                  ('torso ss', 'phase_3' + Toon.TorsoDict['ss'] + '1000'),
                  ('torso ms', 'phase_3' + Toon.TorsoDict['ms'] + '1000'),
                  ('torso ls', 'phase_3' + Toon.TorsoDict['ls'] + '1000'),
                  ('torso sd', 'phase_3' + Toon.TorsoDict['sd'] + '1000'),
                  ('torso md', 'phase_3' + Toon.TorsoDict['md'] + '1000'),
                  ('torso ld', 'phase_3' + Toon.TorsoDict['ld'] + '1000'),
                  ('legs s', 'phase_3' + Toon.LegDict['s'] + '1000'),
                  ('legs m', 'phase_3' + Toon.LegDict['m'] + '1000'),
                  ('legs l', 'phase_3' + Toon.LegDict['l'] + '1000')):
    manifest['joints'][key] = dict(joint_tree(path), source=path)

vfs = VirtualFileSystem.getGlobalPtr()
search = getModelPath().getValue()


def anim_exists(path):
    return vfs.resolveFilename(Filename(path), search, 'bam')


phases = (('phase_3', Toon.Phase3AnimList), ('phase_3.5', Toon.Phase3_5AnimList), ('phase_4', Toon.Phase4AnimList),
          ('phase_5', Toon.Phase5AnimList), ('phase_5.5', Toon.Phase5_5AnimList), ('phase_6', Toon.Phase6AnimList),
          ('phase_9', Toon.Phase9AnimList), ('phase_10', Toon.Phase10AnimList), ('phase_12', Toon.Phase12AnimList))
parts = [('legs ' + k, Toon.LegDict[k]) for k in ('s', 'm', 'l')] + \
        [('torso ' + k, Toon.TorsoDict[k]) for k in ('ss', 'ms', 'ls', 'sd', 'md', 'ld')] + \
        [('head ' + k, ToonHead.HeadDict[k]) for k in ('dls', 'dss', 'dsl', 'dll')]
for phase, animList in phases:
    entry = {'names': [a[0] for a in animList], 'files': [a[1] for a in animList], 'missing': []}
    for label, prefix in parts:
        for anim in animList:
            fn = Filename(phase + prefix + anim[1])
            if not anim_exists(fn):
                entry['missing'].append(str(fn))
    manifest['anims'][phase] = entry

manifest['colors'] = {'allColorsList': [[round(v, 3) for v in tuple(c)[:3]] for c in ToonDNA.allColorsList],
                      'ClothesColors': [[round(v, 3) for v in tuple(c)[:3]] for c in ToonDNA.ClothesColors]}
manifest['scales'] = {'toonBodyScales': dict(OTPGlobals.toonBodyScales),
                      'toonHeadScales': {k: list(v) for k, v in OTPGlobals.toonHeadScales.items()},
                      'legHeightDict': dict(OTPGlobals.legHeightDict),
                      'torsoHeightDict': dict(OTPGlobals.torsoHeightDict),
                      'headHeightDict': dict(OTPGlobals.headHeightDict)}
manifest['settings'] = {'BODY_COLOR': BODY_COLOR, 'GLOVE_COLOR': GLOVE_COLOR, 'TOP_COLOR': TOP_COLOR,
                        'BOTTOM_COLOR': BOTTOM_COLOR, 'background': BACKGROUND[:3]}
with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=1, sort_keys=True)
print('pieces', len(manifest['pieces']), 'examples', len(manifest['examples']), 'skipped', len(manifest['skipped']))


# ---------------------------------------------------------------- README.md
def fmt(v):
    return ', '.join('%g' % x for x in v)


def size_of(info):
    return ' x '.join('%.2f' % (info['max'][i] - info['min'][i]) for i in range(3))


R = []
R += ['# Toon turnarounds', '',
      'Reference set for the player characters (Toons) of Open Toontown, the counterpart of',
      '`../cog-turnarounds/`.  Written by `tools/export_toon_models.py` in the open-toontown repository',
      '(offscreen render, original textures, HD texture pack off).  Everything below was read from',
      '`toontown/toon/Toon.py`, `ToonHead.py`, `ToonDNA.py`, `otp/otpbase/OTPGlobals.py` or measured from',
      'the model files while exporting; the raw measurements are in `manifest.json`.', '',
      '## What is in this folder', '',
      '- `head_<species>_<code>.png`: one sheet per head, views left to right: front, three-quarter, side, back, top.',
      '- `torso_<size>_<clothes>.png`, `legs_<size>.png`: views left to right: front, three-quarter, side, back.',
      '- next to every sheet: `<name>.obj` + `.mtl` (Y-up, game units, the mesh in the pose shown, only the',
      '  nodes that are drawn; material colours are the tints used on the sheet, `map_Kd` points at the',
      '  texture in `resources/`) and `<name>.bam` (the same Panda3D node, which keeps the skeleton).',
      '- `examples/`: six whole Toons built by `toontown.toon.Toon`, same four views.',
      '- Sheets carry no text.  Background is RGB %s.  All views of one sheet share one orthographic scale;' % fmt(BACKGROUND[:3]),
      '  `units_per_tile_height` in `manifest.json` gives game units per tile height for each sheet.', '',
      'A single piece has no colour of its own (see "Colours"), so the piece sheets are tinted with entries of',
      'the game\'s own tables: body `allColorsList[%d]` (%s; `ToonDNA.defaultColor()` returns %d), gloves' % (
          BODY_COLOR, fmt(manifest['colors']['allColorsList'][BODY_COLOR]), BODY_COLOR),
      '`allColorsList[%d]` (white), shirt and sleeves `ClothesColors[%d]` (%s), shorts / skirt `ClothesColors[%d]` (%s).' % (
          GLOVE_COLOR, TOP_COLOR, fmt(manifest['colors']['ClothesColors'][TOP_COLOR]),
          BOTTOM_COLOR, fmt(manifest['colors']['ClothesColors'][BOTTOM_COLOR])),
      'The clothing textures on the piece sheets are the ones stored in the torso models (index 0 of each list).', '',
      'Heads are shown as `ToonHead.generateToonHead` leaves them for a male Toon: unused long/short parts',
      'removed, emotion muzzles hidden, eyes open, no eyelashes.  Torsos and legs are posed on frame 0 of',
      'their `neutral` animation; legs have the `shoes`, `boots_short` and `boots_long` meshes stashed, as',
      '`Toon.generateToonLegs` does, leaving the bare feet.', '']

R += ['## Not exported', '']
for s in manifest['skipped']:
    R.append('- `%s`: `%s` %s.' % (s['file'], s['source'], s['reason']))
R += ['', 'These are the three "undressed" torsos (`Toon.TorsoDict` keys `s`, `m`, `l`).  `Toon.setDNAString` never',
      'uses them either: a one-letter torso code gets `s` appended (shorts) before the Toon is built.', '']

R += ['## How a Toon is put together', '',
      'A Toon is one `Actor` (`toontown.toon.Toon.Toon`, which also inherits `ToonHead`) with three parts named',
      '`legs`, `torso` and `head`, each loaded at three levels of detail named `1000`, `500` and `250`.',
      '`Toon.generateToon` runs: `setLODs`, `generateToonLegs`, `generateToonHead`, `generateToonTorso`',
      '(which calls `generateToonClothes`), `generateToonColor`, `parentToonParts`, `rescaleToon`, `resetHeight`,',
      '`setupToonNodes`.', '',
      'A Toon is described by its DNA (`ToonDNA.ToonDNA`), 15 bytes on the network (`makeNetString`): type `t`,',
      'head index (`toonHeadTypes`), torso index (`toonTorsoTypes`), legs index (`toonLegTypes`), gender (1 = m),',
      'shirt texture, shirt colour, sleeve texture, sleeve colour, bottom texture, bottom colour, arm colour,',
      'glove colour, leg colour, head colour.', '',
      '### Model files', '',
      'All under `resources/phase_3/models/char/`; the level of detail (`1000`, `500`, `250`) is appended to the prefix.',
      'These are the names used with `want-new-anims` on, which is its default.', '',
      '| part | DNA code | file prefix |', '|---|---|---|']
for k in ('s', 'm', 'l'):
    R.append('| legs | `%s` | `phase_3%s` |' % (k, Toon.LegDict[k]))
for k in ('ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l'):
    note = '' if len(k) == 2 else ' (file not present)'
    R.append('| torso | `%s` | `phase_3%s`%s |' % (k, Toon.TorsoDict[k], note))
for k in ('dls', 'dss', 'dsl', 'dll'):
    R.append('| head | `%s` | `phase_3%s` |' % (k, ToonHead.HeadDict[k]))
for k in ('c', 'h', 'm', 'r', 'f', 'p', 'b', 's'):
    codes = ', '.join('`%s`' % c for c in ToonDNA.toonHeadTypes if c[0] == k)
    R.append('| head | %s | `phase_3%s` |' % (codes, ToonHead.HeadDict[k]))
for k in ('dls', 'dss', 'dsl', 'dll'):
    R.append('| dog emotion muzzles | `%s` | `phase_3%s` (only `1000` and `500`) |' % (k, ToonHead.DogMuzzleDict[k]))
for k in ToonDNA.toonSpeciesTypes:
    R.append('| eyelashes (female) | species `%s` | `phase_3%s` (no level of detail suffix) |' % (k, ToonHead.EyelashDict[k]))
R += ['',
      'Torso codes: first letter is the size (`s`, `m`, `l`), second is `s` for shorts or `d` for a skirt.',
      'Torso and legs models are shared by every species.  A female Toon whose bottom texture is a skirt',
      '(`ToonDNA.GirlBottoms[i][1] == SKIRT`) is switched to the `d` torso by `generateToonClothes`, and back',
      'to the `s` torso if the texture is a pair of shorts.', '',
      'Head codes are three letters: species (`d` dog, `c` cat, `h` horse, `m` mouse, `r` rabbit, `f` duck,',
      '`p` monkey, `b` bear, `s` pig), head size (`l` long, `s` short), muzzle size (`l` long, `s` short).',
      'The dog has one model file per head code.  Every other species has ONE head file holding both the',
      'long and the short version of each part (`head-long`, `head-short`, `head-front-*`, `ears-*`, `eyes-*`,',
      '`joint_pupilL_*`, `joint_pupilR_*`, and six `muzzle-<long|short>-<neutral|surprise|sad|smile|angry|laugh>`',
      'nodes); `ToonHead.__fixHeadLongLong / LongShort / ShortLong / ShortShort` remove the parts the head code',
      'does not use.  The "drawn nodes" column of the sheet table below is what is left.  Two things the',
      'code does that the table shows: for horse and duck the mixed codes (`ls`, `sl`) do not remove any `ears-*`',
      'node, so `hls` and `hsl` keep both `ears-long` and `ears-short`; and for the rabbit the mixed codes pick',
      'the ears and the muzzle the other way round from the other species.', '',
      'After the fix, `setupMuzzles` hides the `surprise`, `angry`, `sad`, `smile` and `laugh` muzzles and leaves',
      '`muzzle-*-neutral` showing (`showSurpriseMuzzle` etc. swap them later).  The dog head file only has the',
      'neutral `muzzle`; its five emotion muzzles are loaded from the `headMuzzles` file and parented to the',
      'head\'s `def_head` node.  `setupEyelashes` adds eyelashes only when the DNA gender is `f`: it copies the',
      'nodes `open-long` / `closed-long` or `open-short` / `closed-short` (by head size) from the species\'',
      'lashes model onto the head.  When `base.launcher` exists, a pumpkin head and a snowman head from phase_4',
      'are also attached to the head for the holiday effects; the exporter has no launcher, so they are absent here.', '',
      '### Joints the pieces attach to', '',
      '`Toon.parentToonParts`, for every level of detail:', '',
      '- head onto the torso: `self.attach(\'head\', \'torso\', \'def_head\')` when the torso has a `def_head` node,',
      '  otherwise `joint_head`.  All six torso models here have `def_head` (child of `def_neck`).',
      '- torso onto the legs: `self.attach(\'torso\', \'legs\', \'joint_hips\')`.', '',
      'Other attachment points used by `Toon.py`:', '',
      '- right / left hand props: `def_joint_right_hold` / `def_joint_left_hold` on the torso (fallback names',
      '  `joint_Rhold` / `joint_Lhold`), collected by `setupToonNodes`.',
      '- backpack: a `backpackNode` under the torso\'s `def_joint_attachFlower` (`generateBackpack`); the same joint',
      '  carries the squirting flower (`toontown/battle/MovieSquirt.py`).',
      '- hat and glasses: a `hatNode` / `glassesNode` directly under each `__Actor_head` node, placed with the',
      '  per-head-shape offsets in `toontown/toon/AccessoryGlobals.py`.',
      '- drop shadow: `joint_shadow` on the legs (`getShadowJoint`); nametag: `joint_nameTag` on the legs.', '',
      'Rest position of the exposed joints, measured in each model\'s own coordinates (x, y, z; Toons face +y, z is up):', '',
      '| model | joint | position | hpr |', '|---|---|---|---|']
for key in ('legs s', 'legs m', 'legs l', 'torso ss', 'torso ms', 'torso ls', 'torso sd', 'torso md', 'torso ld'):
    j = manifest['joints'][key]
    for name in sorted(j['exposed']):
        e = j['exposed'][name]
        R.append('| %s (`%s`) | `%s` | %s | %s |' % (key, os.path.basename(j['source']), name, fmt(e['pos']), fmt(e['hpr'])))
R += ['', 'Joint hierarchies as stored (indent = child).  The three legs models have the same joints.', '']
for key, title in (('legs m', 'legs (all three sizes)'), ('torso ms', 'torso `ms`'), ('torso ss', 'torso `ss`'),
                   ('torso md', 'torso `md`'), ('torso sd', 'torso `sd`'), ('torso ld', 'torso `ld`'),
                   ('head dls', 'dog head (all four files)'), ('head cat', 'cat head')):
    R += ['%s, character `%s`:' % (title, manifest['joints'][key]['character']), '', '```'] + manifest['joints'][key]['joints'] + ['```', '']
same_ls = manifest['joints']['torso ls']['joints'] == manifest['joints']['torso ms']['joints']
R += ['Torso `ls` has %s joint list as torso `ms`.  The other species\' head files each have a single joint' % (
          'the same' if same_ls else 'a different'),
      '(`<Species>Head1000Polys` in the `1000` file) that all the head geometry hangs under; they have no',
      'animation of their own.  Only dog heads get animations loaded (`Toon.generateToonHead`): their ears are',
      'skinned to the `def_*_ear*` joints.', '']

R += ['### Colours and clothing', '',
      'Body colours are indices into `ToonDNA.allColorsList` (%d entries); clothing colours are indices into' % len(ToonDNA.allColorsList),
      '`ToonDNA.ClothesColors` (%d entries).  They are applied with `setColor` on these nodes, at every level of detail:' % len(ToonDNA.ClothesColors), '',
      '| node(s) | part | gets | set in |', '|---|---|---|---|',
      '| `**/head*` (matches `head`, `head-front`, `head-long`, `head-front-short`, ...) | head | head colour | `ToonHead.generateToonColor` |',
      '| `**/ear?-*` (`ears-long`, `ears-short`) | head | head colour, only for cat, rabbit, bear, mouse, pig | `ToonHead.generateToonColor` |',
      '| `arms`, `neck` | torso | arm colour | `Toon.generateToonColor` |',
      '| `hands` | torso | glove colour (`isValidNetString` only accepts index 0, white) | `Toon.generateToonColor` |',
      '| `legs`, `feet` | legs | leg colour | `Toon.generateToonColor` |',
      '| `torso-top` | torso | texture `ToonDNA.Shirts[topTex]` (override priority 1), colour `ClothesColors[topTexColor]` | `Toon.generateToonClothes` |',
      '| `sleeves` | torso | texture `ToonDNA.Sleeves[sleeveTex]`, colour `ClothesColors[sleeveTexColor]` | `Toon.generateToonClothes` |',
      '| `torso-bot` | torso | texture `ToonDNA.BoyShorts[botTex]` (gender m) or `ToonDNA.GirlBottoms[botTex][0]` (gender f), colour `ClothesColors[botTexColor]` | `Toon.generateToonClothes` |',
      '| `torso-bot-cap` | torso | half the bottom colour, alpha 1 (of the `1000` files only the `ss` torso has this node) | `Toon.generateToonClothes` |',
      '| `eyes*` | head | `setColorOff`; the texture is swapped between `ToonHead.EyesOpen`, `EyesClosed`, `EyesSurprised`, `EyesSad*`, `EyesAngry*` | `ToonHead.__fixEyes`, eyelid states |',
      '',
      'Nodes not listed (muzzles, nose, dog ears, pupils) keep the colour and texture stored in the model.',
      'Dog, horse, duck and monkey ears are not tinted by the code.  The clothing textures are loaded with',
      'min filter linear-mipmap-linear and mag filter linear.  The eyes are drawn in front of `head-front*` and',
      'the pupils in front of the eyes with `Actor.drawInFront`.  Shoes (`Toon.generateShoes`):',
      'the legs model holds `feet`, `shoes`, `boots_short`, `boots_long`; all are stashed except',
      '`ToonDNA.ShoesModels[shoes[0]]`, which gets `ToonDNA.ShoesTextures[shoes[1]]` when it is not the bare feet.',
      'The texture files themselves are in `../toon-sprites/`.', '',
      '### Scale and height', '',
      '`Toon.rescaleToon` scales the whole geometry by the species\' body scale (`Avatar.setAvatarScale`) and',
      'each head part by the species\' head scale (`otp/otpbase/OTPGlobals.py`, re-exported by `ToontownGlobals`):', '',
      '| species | toonBodyScales | toonHeadScales |', '|---|---|---|']
for sp in ('dog', 'cat', 'horse', 'mouse', 'rabbit', 'duck', 'monkey', 'bear', 'pig'):
    R.append('| %s | %g | %s |' % (sp, OTPGlobals.toonBodyScales[sp], fmt(OTPGlobals.toonHeadScales[sp])))
R += ['', '`Toon.resetHeight` sets the nominal height (used for the nametag and collisions) to',
      '`(legHeightDict[legs] + torsoHeightDict[torso]) * bodyScale + headHeightDict[head] * headScale.z`:', '',
      '- `legHeightDict`: ' + ', '.join('`%s` %g' % (k, OTPGlobals.legHeightDict[k]) for k in ('s', 'm', 'l')),
      '- `torsoHeightDict`: ' + ', '.join('`%s` %g' % (k, OTPGlobals.torsoHeightDict[k]) for k in ('ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l')),
      '- `headHeightDict`: %g for every head code with a long head (second letter `l`), %g for a short head' % (
          OTPGlobals.headHeightDict['dls'], OTPGlobals.headHeightDict['dss']), '']
assert all(OTPGlobals.headHeightDict[c] == (0.75 if c[1] == 'l' else 0.5) for c in ToonDNA.toonHeadTypes)

R += ['### Levels of detail', '',
      '`Toon.setLODs` adds three levels to one LODNode; the switch distances come from config variables with these',
      'defaults: `1000` from %d to %d, `500` from %d to %d, `250` from %d to %d (far, near; game units from the camera).' % (
          ConfigVariableInt('lod1-in', 20).value, ConfigVariableInt('lod1-out', 0).value,
          ConfigVariableInt('lod2-in', 80).value, ConfigVariableInt('lod2-out', 20).value,
          ConfigVariableInt('lod3-in', 280).value, ConfigVariableInt('lod3-out', 80).value),
      'Triangles stored in each file (every node counted, so the non-dog head files include both the long and',
      'the short parts and all six muzzles, and the legs files include feet, shoes and both boots):', '',
      '| part | file prefix | 1000 | 500 | 250 |', '|---|---|---|---|---|']
for l in manifest['lods']:
    t = l['triangles']
    R.append('| %s | `%s` | %s | %s | %s |' % (l['kind'], l['prefix'], *[('%d' % t[k]) if t[k] is not None else 'no file' for k in ('1000', '500', '250')]))
R += ['', 'The sheets and meshes in this folder are all the `1000` level.', '']

R += ['### Animation sets', '',
      'Animations are separate files per part: `<phase>` + the part\'s file prefix + the animation\'s file name',
      '(`Toon.compileGlobalAnimList`), for the three legs, the torsos and the four dog heads.  The first name is',
      'the one the code plays, the name in brackets is the file suffix when it differs.', '']
total_missing = 0
for phase, animList in phases:
    entry = manifest['anims'][phase]
    names = ', '.join(('`%s`' % a[0]) if a[0] == a[1] else '`%s` (`%s`)' % a for a in animList) or 'none'
    R.append('- `%s` (%d): %s' % (phase, len(animList), names))
    total_missing += len(entry['missing'])
R.append('')
if total_missing:
    R += ['%d of the animation files those lists name are not in `resources/` (checked for legs `s m l`, torsos' % total_missing,
          '`ss ms ls sd md ld` and the four dog heads).  Per animation file name, the parts without a file:', '']
    by_anim = {}
    for phase, animList in phases:
        for path in manifest['anims'][phase]['missing']:
            for label, prefix in parts:
                for anim in animList:
                    if path == phase + prefix + anim[1]:
                        by_anim.setdefault((phase, anim[1]), []).append(label)
    for (phase, anim) in sorted(by_anim):
        labels = by_anim[(phase, anim)]
        R.append('- `%s` `%s`: %s' % (phase, anim, 'all %d parts' % len(parts) if len(labels) == len(parts) else ', '.join(labels)))
    R.append('')

R += ['## Sheets and their sources', '',
      'Size is x (width) x y (depth) x z (height) of the drawn mesh in game units, before any body scale.', '',
      '| sheet | source model | drawn nodes | triangles | size |', '|---|---|---|---|---|']
for p in manifest['pieces']:
    src = '`%s`' % p['source']
    R.append('| `%s.png` | %s | %s | %d | %s |' % (p['file'], src, ', '.join('`%s`' % n for n in p['nodes']), p['triangles'], size_of(p)))
R += ['',
      'For the dog heads, `def_left_pupil` / `def_right_pupil` are the joints the two (unnamed) pupil meshes hang',
      'under.  `MouseHead1000Polys` / `RabbitHead1000Polys` in the drawn nodes stand for an unnamed mesh directly',
      'under that joint node.', '',
      'Nodes stored in each source model (before `ToonHead` / `Toon` remove, hide or stash any):', '']
seen = set()
for p in manifest['pieces']:
    if p['source'] in seen:
        continue
    seen.add(p['source'])
    R.append('- `%s`: %s' % (p['source'], ', '.join('`%s`' % n for n in p['stored_nodes'])))
    if 'extra_source' in p:
        R.append('- `%s`: %s' % (p['extra_source'], ', '.join('`%s`' % n for n in p['extra_nodes'])))
R.append('')

R += ['## Examples', '',
      'Whole Toons, built with `Toon.Toon()` + `setDNAString`, posed on frame 0 of `neutral`, level of detail `1000`.',
      'Colour columns are `allColorsList` indices; clothing columns are list index / `ClothesColors` index.',
      '"Height" is `Toon.getHeight()`; "measured" is the top of the drawn mesh above the feet.', '',
      '| sheet | from | DNA (hex) | species | head | torso | legs | gender | head / arm / leg colour | shirt | sleeve | bottom | body scale | height | measured |',
      '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for e in manifest['examples']:
    R.append('| `%s.png` | %s | `%s` | %s | `%s` | `%s` | `%s` | %s | %d / %d / %d | `%s` %d / %d | `%s` %d / %d | `%s` %d / %d | %g | %g | %.2f |' % (
        e['file'], e['origin'], e['dna_hex'], e['species'], e['head'], e['torso'], e['legs'], e['gender'],
        e['headColor'], e['armColor'], e['legColor'],
        os.path.basename(e['topTexFile']), e['topTex'], e['topTexColor'],
        os.path.basename(e['sleeveTexFile']), e['sleeveTex'], e['sleeveTexColor'],
        os.path.basename(e['botTexFile']), e['botTex'], e['botTexColor'],
        e['body_scale'], e['height'], e['max'][2] - e['min'][2]))
R += ['',
      '`Loaded_Duck` is read from the `setDNAString` field of `%s` (a 2-byte length, then the 15 DNA bytes).' % OWN_TOON_FILE,
      'The others are entries of `NPCToons.NPCToonDict` with a fixed (not random) DNA.', '',
      '## Re-running', '',
      'From the open-toontown repository root:', '',
      '```', 'PYTHONPATH=. venv/bin/python tools/export_toon_models.py ../open-toontown-hd/toon-turnarounds',
      'PYTHONPATH=. venv/bin/python tools/export_toon_sprites.py ../open-toontown-hd/toon-sprites', '```', '']
with open(os.path.join(OUT, 'README.md'), 'w') as f:
    f.write('\n'.join(R))
print('README.md written')
