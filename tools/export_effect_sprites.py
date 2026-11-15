#!/usr/bin/env python
"""
Writes the 2D images the game's visual effects are drawn with as PNG files,
alpha merged in.

What is collected (every entry below is a model the code or a particle file
names; see SOURCES for the reference each one comes from):
  * the battle particle sprites: the nodes of the suit-particles model that
    BattleParticles.getParticle() and the *.ptf particle files pick by name,
    and the other models the *.ptf files name with setTextureFromNode();
  * the flat effect cards among the battle props (BattleProps.Props):
    splats, stun stars, glow, the "kapow" and suit explosions, dust, geyser;
  * the world effects in toontown/effects (firework and particle cards,
    smoke, sparks, bubbles), drop shadows, lightning, water spray and the like;
  * flipbooks (SequenceNode models the code plays frame by frame): every
    frame, numbered, plus one tiled contact sheet per effect.

Most of these sprites are not files of their own: they are rectangles of a
shared "palette" texture.  Each such sprite is written cropped out by the UV
rectangle of its card, and the whole palette is written once under sheets/.
A sprite whose card shows a whole texture is written under that texture's
own base name.

Output folder (default ../open-toontown-hd/effect-sprites):
  battle-particles/  battle-props/  world-effects/  shadows/
  flipbooks/<effect>/   frames + <effect>_contact_sheet.png
  sheets/               the shared palette textures the crops come from
  README.md             every file, where it comes from, size, alpha, users

These are the ORIGINAL textures from resources/: the HD texture pack
(toontown.toonbase.HDTextures) is not switched on.  Nothing is launched and
no window is opened; ShowBase only gives the loader a context.

Usage (from the repository root, with the game's Python):
    PYTHONPATH=. venv/bin/python tools/export_effect_sprites.py [output folder]
"""
import glob
import math
import os
import re
import shutil
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type none\naudio-library-name null\nwant-postfx 0\n'
                    'notify-level warning\ndefault-directnotify-level warning\n'
                    # keep every image at the size it has on disk
                    'textures-power-2 none\ntexture-scale 1\nmax-texture-dimension -1\n'
                    'compressed-textures 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '../open-toontown-hd/effect-sprites')
RESOURCES = os.path.abspath('resources')
FOLDERS = ('battle-particles', 'battle-props', 'world-effects', 'shadows', 'flipbooks', 'sheets')
vfs = VirtualFileSystem.getGlobalPtr()
search = getModelPath().getValue()

# ---------------------------------------------------------------- what to export
# folder, model, mode, options.
#   mode 'sprites' : every textured card in the model is one sprite
#   mode 'flipbook': the children of the model's SequenceNode are the frames, in order
# options:
#   naming  'node'  -> file named after the card's node (models that are a set of named sprites)
#           'model' -> file named after the model, "<model>__<part>" when it has several parts
#   find    list of substrings; the .py / .ptf files containing one of them are the users
#   pernode True: also look for each sprite's own name, quoted, in the code and particle files
#   skip    node names not exported (see NOT_EXPORTED for why)
#   note    said in the README row
def src(folder, model, mode='sprites', naming='model', find=(), pernode=False, skip=(), note=''):
    return dict(folder=folder, model=model, mode=mode, naming=naming, find=list(find) or [model],
                pernode=pernode, skip=set(skip), note=note)


def prop(name):
    return "getProp('%s')" % name


SOURCES = [
    # --- shadows (first, so a shadow card reused inside another prop is filed here)
    src('shadows', 'phase_3/models/props/drop_shadow'),
    src('shadows', 'phase_3/models/props/square_drop_shadow'),
    src('shadows', 'phase_10/models/cogHQ/RoundShadow'),
    # --- BattleParticles.loadParticles() / getParticle(); *.ptf setTextureFromNode()
    src('battle-particles', 'phase_3.5/models/props/suit-particles', naming='node', pernode=True,
        note='BattleParticles.getParticle'),
    src('battle-particles', 'phase_5/models/props/uberSoundEffects', naming='node', pernode=True),
    # --- BattleProps.Props entries that are flat cards (model path = PropPool.getPath(phase, model))
    src('battle-props', 'phase_3.5/models/props/splat-mod', find=["'splat-", 'splash-from-splat'],
        note="BattleProps props 'splat-*' and 'splash-from-splat', tinted per pie"),
    src('battle-props', 'phase_3.5/models/props/stun-mod', find=[prop('stun')], note="BattleProps prop 'stun'"),
    src('battle-props', 'phase_3.5/models/props/glow', find=[prop('glow')], note="BattleProps prop 'glow'"),
    src('battle-props', 'phase_3.5/models/props/suit_explosion-mod', find=["'suit_explosion'"],
        note="BattleProps prop 'suit_explosion'"),
    src('battle-props', 'phase_5/models/props/kapow-mod', find=["'kapow'"], note="BattleProps prop 'kapow'"),
    src('battle-props', 'phase_5/models/props/dust-mod', find=["'dust'"], note="BattleProps prop 'dust'"),
    src('battle-props', 'phase_5/models/props/geyser', find=[prop('geyser')], skip=['hole'],
        note="BattleProps prop 'geyser'"),
    # --- toontown/effects and other world effects
    src('world-effects', 'phase_4/models/props/tt_m_efx_ext_fireworkCards', naming='node', pernode=True),
    src('world-effects', 'phase_4/models/props/tt_m_efx_ext_particleCards', naming='node', pernode=True),
    src('world-effects', 'phase_4/models/props/tt_m_efx_ext_smoke'),
    src('world-effects', 'phase_4/models/props/tt_m_efx_fireball'),
    src('world-effects', 'phase_4/models/props/tt_m_efx_smoke'),
    src('world-effects', 'phase_4/models/char/bubble'),
    src('world-effects', 'phase_6/models/karting/driftSmoke'),
    src('world-effects', 'phase_6/models/karting/particleSpark'),
    src('world-effects', 'phase_6/models/karting/pie_splat_1'),
    src('world-effects', 'phase_8/models/props/snowflake_particle', note='snowdisk.ptf'),
    src('world-effects', 'phase_4/models/props/test_clouds'),
    src('world-effects', 'phase_4/models/props/SZ_splashdown-mod', find=[prop('splashdown')],
        note="BattleProps prop 'splashdown'"),
    src('world-effects', 'phase_3.5/models/props/portal-mod'),
    src('world-effects', 'phase_10/models/cogHQ/CBLightning'),
    src('world-effects', 'phase_5/models/char/tt_m_efx_hydrantSquirt'),
    src('world-effects', 'phase_4/models/minigames/prop_waterspray'),
    src('world-effects', 'phase_4/models/minigames/particleGlow'),
    # the sprite textures of the older Fireworks.py particle fireworks (Fireworks.textures)
    src('world-effects', 'phase_4/models/props/icecream'),
    src('world-effects', 'phase_8/models/props/snowflake_treasure', note='also the treasure pickup'),
    src('world-effects', 'phase_6/models/props/music_treasure', note='also the treasure pickup'),
    src('world-effects', 'phase_8/models/props/flower_treasure', note='also the treasure pickup'),
    src('world-effects', 'phase_6/models/props/starfish_treasure', note='also the treasure pickup'),
    src('world-effects', 'phase_8/models/props/zzz_treasure', note='also the treasure pickup'),
    # --- flipbooks
    src('flipbooks', 'phase_3.5/models/props/explosion', mode='flipbook'),
    src('flipbooks', 'phase_3.5/models/props/dust_cloud', mode='flipbook',
        find=[prop('suit_explosion_dust'), 'DustCloud.DustCloud(', 'DustCloud('],
        note="BattleProps prop 'suit_explosion_dust', effects/DustCloud.py"),
    src('flipbooks', 'phase_4/models/props/ripples', mode='flipbook', find=[prop('ripples'), 'Ripples.Ripples('],
        note="BattleProps prop 'ripples', effects/Ripples.py, effects/Wake.py"),
    src('flipbooks', 'phase_4/models/props/wake', mode='flipbook', find=[prop('wake')],
        note="BattleProps prop 'wake', effects/Wake.py WakeSequence"),
    src('flipbooks', 'phase_4/models/props/tt_m_efx_ext_fireworkBurst_tflip', mode='flipbook'),
    src('flipbooks', 'phase_3/models/makeatoon/tt_m_ara_mat_smoke', mode='flipbook'),
]

# things the code names that produce no image here, and why (checked when the script runs)
NOT_EXPORTED = [
    ('phase_3.5/models/props/splash', "BattleProps.Props entry 'splash' (3.5, 'splash', 'splash')"),
    ('phase_3.5/models/props/spray', "BattleProps.Props entry 'spray' (MovieUtil.getSprayTrack), the water squirt stream"),
    ('phase_4/models/props/stormcloud-mod', "BattleProps.Props entry 'stormcloud'"),
]

# ---------------------------------------------------------------- helpers
def rel(fullpath):
    p = Filename(fullpath).toOsSpecific()
    if p.startswith(RESOURCES + os.sep):
        p = p[len(RESOURCES) + 1:]
    return p.replace(os.sep, '/')


images = {}     # texture path -> (PNMImage, alpha path or None)
alpha_only = set()


def image_of(tex):
    """The texture's image as stored on disk, with its separate alpha file merged in."""
    path = rel(tex.getFullpath())
    if path not in images:
        alpha = rel(tex.getAlphaFullpath()) if tex.hasAlphaFullpath() else None
        fresh = Texture()
        fn = Filename(tex.getFullpath())
        ok = fresh.read(fn, Filename(tex.getAlphaFullpath()), 0, 0) if alpha else fresh.read(fn)
        img = PNMImage()
        if not ok or not fresh.store(img):
            raise RuntimeError('cannot read ' + path)
        if tex.getFormat() == Texture.FAlpha and img.getNumChannels() == 1:
            # a 1-channel file the model uses as alpha only (drawn white, or in the tint the code sets)
            mask = img
            img = PNMImage(mask.getXSize(), mask.getYSize(), 2, mask.getMaxval())
            img.fill(1)
            for y in range(mask.getYSize()):
                for x in range(mask.getXSize()):
                    img.setAlpha(x, y, mask.getGray(x, y))
            alpha_only.add(path)
        images[path] = (img, alpha)
    return path, images[path][0], images[path][1]


def cards(np):
    """(texture, (umin, umax, vmin, vmax)) for every textured geom of a GeomNode."""
    out = []
    node = np.node()
    net = np.getNetState()
    for gi in range(node.getNumGeoms()):
        ta = net.compose(node.getGeomState(gi)).getAttrib(TextureAttrib)
        if ta is None or ta.isOff() or ta.getNumOnStages() == 0:
            continue
        tex = ta.getOnTexture(ta.getOnStage(0))
        vd = node.getGeom(gi).getVertexData()
        if not tex.hasFullpath() or not vd.hasColumn('texcoord'):
            continue
        reader = GeomVertexReader(vd, 'texcoord')
        us, vs = [], []
        while not reader.isAtEnd():
            uv = reader.getData2()
            us.append(uv[0])
            vs.append(uv[1])
        out.append((tex, (min(us), max(us), min(vs), max(vs))))
    return out


def pixel_rect(uv, w, h):
    """UV rectangle -> (x, y, width, height) in image pixels, y counted from the top."""
    umin, umax, vmin, vmax = uv
    if umax - umin >= 0.96 and vmax - vmin >= 0.96:
        return 0, 0, w, h           # the card shows the whole texture, give or take an edge pixel
    x0 = max(0, min(w, int(math.floor(umin * w + 0.5))))
    x1 = max(0, min(w, int(math.floor(umax * w + 0.5))))
    y0 = max(0, min(h, int(math.floor((1.0 - vmax) * h + 0.5))))
    y1 = max(0, min(h, int(math.floor((1.0 - vmin) * h + 0.5))))
    return x0, y0, x1 - x0, y1 - y0


def crop(img, rect):
    x, y, w, h = rect
    out = PNMImage(w, h, img.getNumChannels(), img.getMaxval())
    out.copySubImage(img, 0, 0, x, y, w, h)
    return out


def node_label(np, top):
    """A name for a card: its own node name, else the nearest named parent below the model root."""
    cur = np
    while cur != top and not cur.isEmpty():
        if cur.getName():
            return cur.getName()
        cur = cur.getParent()
    return ''


def write(img, relpath):
    full = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if not img.write(Filename.fromOsSpecific(full)):
        raise RuntimeError('cannot write ' + full)


# ---------------------------------------------------------------- who uses what
texts = {}
for pattern in ('toontown/**/*.py', 'otp/**/*.py', 'resources/phase_*/etc/*.ptf'):
    for path in glob.glob(pattern, recursive=True):
        with open(path, errors='replace') as f:
            texts[path.replace(os.sep, '/')] = f.read()


def short(path):
    return path[len('resources/'):] if path.startswith('resources/') else path


def users(terms, regex=None):
    found = []
    for path in sorted(texts):
        text = texts[path]
        if any(t in text for t in terms) or (regex is not None and regex.search(text)):
            found.append(short(path))
    return found


def join_users(found, limit=10):
    if len(found) > limit:
        return ', '.join(found[:limit]) + ', ... %d files in all' % len(found)
    return ', '.join(found)


# ---------------------------------------------------------------- export
for folder in FOLDERS:                       # start clean so a re-run leaves no stale files
    shutil.rmtree(os.path.join(OUT, folder), ignore_errors=True)

rows = []            # one per written file
missing = []         # (model, reason)
sprites = {}         # (texture path, rect) -> row, so one sprite shared by several nodes is written once
taken = {}           # folder/name.png (lower case) -> key, to keep file names unique
sheets = {}          # texture path -> row


def sheet_row(path, img, alpha):
    if path not in sheets:
        name = 'sheets/%s.png' % os.path.splitext(os.path.basename(path))[0]
        if name.lower() in taken:
            name = 'sheets/%s_%s.png' % (path.split('/')[0], os.path.splitext(os.path.basename(path))[0])
        taken[name.lower()] = path
        write(img, name)
        sheets[path] = dict(out=name, tex=path, alpha=alpha, size=(img.getXSize(), img.getYSize()),
                            channels=img.getNumChannels(), holds=[])
    return sheets[path]


def unique(folder, stem, key):
    name = '%s/%s.png' % (folder, stem)
    n = 2
    while taken.get(name.lower(), key) != key:
        name = '%s/%s_%d.png' % (folder, stem, n)
        n += 1
    taken[name.lower()] = key
    return name


for s in SOURCES:
    model = loader.loadModel(s['model'], okMissing=True)
    if not model:
        missing.append((s['model'], 'model file is not in resources/'))
        continue
    base = os.path.basename(s['model'])
    model_users = users(s['find'])

    if s['mode'] == 'flipbook':
        seq = model.find('**/+SequenceNode')
        frames = []
        for i in range(seq.getNumChildren()):
            got = cards(seq.getChild(i))
            if got:
                frames.append((seq.getChild(i).getName(), got[0]))
        digits = max(2, len(str(len(frames))))
        outs = []
        for i, (name, (tex, uv)) in enumerate(frames):
            path, img, alpha = image_of(tex)
            rect = pixel_rect(uv, img.getXSize(), img.getYSize())
            whole = rect == (0, 0, img.getXSize(), img.getYSize())
            frame = img if whole else crop(img, rect)
            out = 'flipbooks/%s/%s_%0*d.png' % (base, base, digits, i + 1)
            write(frame, out)
            outs.append(frame)
            row = dict(out=out, folder='flipbooks', model=s['model'], tex=path, alpha=alpha, rect=rect, whole=whole,
                       nodes=['frame %d of %d%s' % (i + 1, len(frames), (' "%s"' % name) if name else '')],
                       size=(frame.getXSize(), frame.getYSize()), users=model_users, note=s['note'])
            rows.append(row)
            if not whole:
                sheet_row(path, img, alpha)['holds'].append(out)
        # contact sheet: frames left to right, top to bottom, each centred in a cell of the largest frame
        cw = max(f.getXSize() for f in outs)
        ch = max(f.getYSize() for f in outs)
        cols = int(math.ceil(math.sqrt(len(outs))))
        nrows = int(math.ceil(len(outs) / float(cols)))
        sheet = PNMImage(cw * cols, ch * nrows, 4)
        sheet.fill(0, 0, 0)
        sheet.alphaFill(0)
        for i, f in enumerate(outs):
            cell = PNMImage(f.getXSize(), f.getYSize(), 4)
            cell.alphaFill(1)
            cell.copySubImage(f, 0, 0)
            if f.hasAlpha():
                cell.copyChannel(f, 3, 3)
            sheet.copySubImage(cell, (i % cols) * cw + (cw - f.getXSize()) // 2,
                               (i // cols) * ch + (ch - f.getYSize()) // 2)
        out = 'flipbooks/%s/%s_contact_sheet.png' % (base, base)
        write(sheet, out)
        node = seq.node()
        rows.append(dict(out=out, folder='flipbooks', model=s['model'], tex=None, alpha=None, rect=None, whole=False,
                         nodes=['contact sheet: %d frames, %d columns x %d rows, cells %dx%d; SequenceNode "%s", %g frames per second in the model'
                                % (len(outs), cols, nrows, cw, ch, seq.getName(), node.getFrameRate())],
                         size=(sheet.getXSize(), sheet.getYSize()), users=model_users, note=s['note'],
                         contact=True, frames=len(outs)))
        continue

    multi = None
    found_any = False
    geoms = [np for np in model.findAllMatches('**/+GeomNode')]
    labels = set(node_label(np, model) for np in geoms)
    for np in geoms:
        label = node_label(np, model)
        if label in s['skip'] or np.getName() in s['skip']:
            continue
        for tex, uv in cards(np):
            path, img, alpha = image_of(tex)
            w, h = img.getXSize(), img.getYSize()
            if uv[0] < -0.02 or uv[1] > 1.02 or uv[2] < -0.02 or uv[3] > 1.02:
                # card bigger than the texture by a hair is fine; a repeating texture is not a sprite
                if uv[1] - uv[0] > 1.05 or uv[3] - uv[2] > 1.05:
                    missing.append((s['model'], 'node "%s" repeats its texture %s (UVs outside 0..1), not a sprite' % (label, path)))
                    continue
            rect = pixel_rect(uv, w, h)
            if rect[2] <= 0 or rect[3] <= 0:
                continue
            found_any = True
            whole = rect == (0, 0, w, h)
            key = (path, rect)
            users_here = list(model_users)
            if s['pernode'] and label:
                quoted = re.compile(r'''['"](\*\*/)?%s['"]''' % re.escape(label))
                # the file that merely lists every name (ParticleNames) is not a user
                users_here = [u for u in users([], quoted) if u != 'toontown/battle/BattleParticles.py']
            if key in sprites:
                row = sprites[key]
                ref = '%s :: %s' % (s['model'], label) if label else s['model']
                if ref not in row['refs']:
                    row['refs'].append(ref)
                row['users'] = sorted(set(row['users']) | set(users_here))
                continue
            if whole:
                stem = os.path.splitext(os.path.basename(path))[0]
            elif s['naming'] == 'node' and label:
                stem = label
            elif len(labels) > 1 and label:
                stem = '%s__%s' % (base, label)
            else:
                stem = base
            out = unique(s['folder'], stem, key)
            write(img if whole else crop(img, rect), out)
            row = dict(out=out, folder=s['folder'], model=s['model'], tex=path, alpha=alpha, rect=rect, whole=whole,
                       refs=['%s :: %s' % (s['model'], label) if label else s['model']],
                       size=(rect[2], rect[3]), users=users_here, note=s['note'])
            sprites[key] = row
            rows.append(row)
            if not whole:
                sheet_row(path, img, alpha)['holds'].append(out)
    if not found_any:
        missing.append((s['model'], 'model has no textured card'))

for path, what in NOT_EXPORTED:
    model = loader.loadModel(path, okMissing=True)
    if not model:
        missing.append((path, '%s: model file is not in resources/' % what))
        continue
    textured = [c for np in model.findAllMatches('**/+GeomNode') for c in cards(np)]
    if not textured:
        missing.append((path, '%s: the model has no texture at all (plain coloured geometry), so there is no image to redraw' % what))
    else:
        names = sorted(set(rel(t.getFullpath()) for t, uv in textured))
        missing.append((path, '%s: a 3D model, not a flat card; its geometry is coloured from %s' % (what, ', '.join(names))))

# sprite names the code or the particle files ask for that the model does not have
import ast
names = ast.literal_eval(re.search(r'^ParticleNames = (\(.*?\))$', texts['toontown/battle/BattleParticles.py'], re.M).group(1))
wanted = [('phase_3.5/models/props/suit-particles', n, 'BattleParticles.ParticleNames') for n in names]
for path in sorted(texts):
    for mpath, node in re.findall(r'setTextureFromNode\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]\*\*/([^\'"]+)[\'"]', texts[path]):
        wanted.append((mpath, node, short(path)))
asked = {}
for mpath, node, who in wanted:
    asked.setdefault((mpath, node), []).append(who)
for (mpath, node), who in sorted(asked.items()):
    if node == '*':
        continue
    model = loader.loadModel(mpath, okMissing=True)
    if not model:
        missing.append((mpath, 'named by %s: model file is not in resources/' % ', '.join(sorted(set(who)))))
    elif model.find('**/' + node).isEmpty():
        missing.append((mpath, 'sprite node "%s" is named by %s but the model has no node of that name'
                        % (node, ', '.join(sorted(set(who))))))

# sanity: every written image must hold something
empty = []
for r in rows + list(sheets.values()):
    img = PNMImage()
    img.read(Filename.fromOsSpecific(os.path.join(OUT, r['out'])))
    visible = 0
    for y in range(img.getYSize()):
        for x in range(img.getXSize()):
            if not img.hasAlpha() or img.getAlpha(x, y) > 0.02:
                visible += 1
    r['channels'] = img.getNumChannels()
    r['visible'] = visible / float(img.getXSize() * img.getYSize())
    if visible == 0:
        empty.append(r['out'])

# ---------------------------------------------------------------- README
def alpha_cell(r):
    if r.get('contact'):
        return 'n/a'
    if r['alpha']:
        return '`%s`' % os.path.basename(r['alpha'])
    if r.get('tex') in alpha_only:
        return 'none (the 1-channel file is the alpha; written here as white + alpha)'
    return 'none (alpha inside the file)' if r['channels'] in (2, 4) else 'none (opaque)'


def origin_cell(r):
    if r.get('contact'):
        return '`%s` (all frames)' % r['model']
    refs = r.get('refs')
    if refs is None:
        refs = ['%s :: %s' % (r['model'], r['nodes'][0])]
    where = '; '.join('`%s`' % x for x in refs)
    if r['whole']:
        return '%s -> `%s` (whole texture)' % (where, r['tex'])
    return '%s -> `%s` at x=%d y=%d' % (where, r['tex'], r['rect'][0], r['rect'][1])


def used_cell(r):
    out = join_users(r['users'])
    if r['note']:
        out = (out + '; ' if out else '') + r['note']
    return out or 'no reference found in the code'


count = {f: 0 for f in FOLDERS}
for r in rows:
    count[r['folder']] += 1
count['sheets'] = len(sheets)
flip = [r for r in rows if r.get('contact')]

L = []
L += ['# Effect sprites', '',
      'The 2D images the game draws its visual effects with, written as PNG by',
      '`tools/export_effect_sprites.py` in the open-toontown repository.  These are the original',
      'images from `resources/` (the HD texture pack was not enabled).  Where the game pairs a',
      '`.jpg` colour image with a separate `_a.rgb` alpha image, the two are merged into one RGBA PNG;',
      'the "alpha file" column names the alpha file that was merged.', '',
      'Files written: %d (%s).' % (sum(count.values()), ', '.join('%s %d' % (f, count[f]) for f in FOLDERS)), '',
      '## How the list was collected', '',
      'Every image here comes from a model that the code or a particle definition file names:', '',
      '- `toontown/battle/BattleParticles.py` loads `phase_3.5/models/props/suit-particles` and picks its',
      '  child nodes by name (`ParticleNames`, `getParticle`, `setEffectTexture`); the `*.ptf` particle files',
      '  under `resources/phase_*/etc/` pick sprites with `setTextureFromNode("model", "**/node")`.',
      '  Of the %d `.ptf` files, %d name a sprite that way; the models they name are `suit-particles`,'
      % (sum(1 for p in texts if p.endswith('.ptf')),
         sum(1 for p, t in texts.items() if p.endswith('.ptf') and 'setTextureFromNode' in t)),
      '  `uberSoundEffects` and `snowflake_particle`.  The rest use Panda\'s sparkle, line or geom renderers',
      '  (no image), or are given their sprite by the Python file that loads them',
      '  (`effects/CarSmoke.py`, `Drift.py`, `Sparks.py`, `RocketExplosion.py`).',
      '- `toontown/battle/BattleProps.py` (`Props`, `PropPool`) for the battle props that are flat cards,',
      '  plus `MovieUtil.py` / `GoonDeath.py` for the `explosion` flipbook.',
      '- `toontown/effects/*.py` for the firework and particle cards, smoke, sparks, bubbles, ripples,',
      '  wake, splash and dust cloud; and the files named in the "used by" column for drop shadows,',
      '  lightning, the teleport hole, water spray and the Make-A-Toon smoke.', '',
      'The "used by" column is produced by searching the `.py` files under `toontown/` and `otp/` and the',
      '`.ptf` files for the model path, the `getProp(\'name\')` call, or (for the sprite-set models) the',
      'sprite\'s own quoted name.', '',
      '## How these are used at runtime', '',
      '**Particle sprite models.**  `suit-particles`, `uberSoundEffects`, `tt_m_efx_ext_fireworkCards` and',
      '`tt_m_efx_ext_particleCards` are each a flat list of small cards, one named node per sprite.  The',
      'code never shows the model itself: it finds one node by name and hands it to a particle renderer',
      '(`renderer.setFromNode(node)` / `setTextureFromNode(model, "**/node")`), which copies that card\'s',
      'texture and UV rectangle onto every particle, or it copies the single card and scales / colours /',
      'fades it (`effects/FlashEffect.py`, `RayBurst.py`, `SkullBurst.py` ...).  Many are tinted in code',
      '(`setEffectTexture(effect, name, color=...)`, `setColorScale`), so the art is mostly white or grey',
      'with the shape in the alpha channel.', '',
      '**Cards.**  The battle props (`splat`, `stun`, `glow`, `kapow`, `suit_explosion`, `dust`, `geyser`)',
      'and the world props (drop shadows, bubble, lightning bolt, smoke puff, teleport hole ...) are',
      'models made of one or a few textured quads.  The prop pool or the effect class loads the model and',
      'moves, scales, billboards and fades it; the ones with a `-chan` animation file (`splat`, `stun`,',
      '`kapow`, `suit_explosion`, `dust`, `splashdown`, `portal`) are Actors whose joints scale the quads.', '',
      '**Flipbooks.**  `explosion`, `dust_cloud`, `ripples`, `wake`, `tt_m_efx_ext_fireworkBurst_tflip` and',
      '`tt_m_ara_mat_smoke` hold a `SequenceNode` with one card per frame; Panda shows one child at a',
      'time.  The code plays them with `seqNode.play()` / `loop()` / `pose()` and sets the speed',
      '(`setFrameRate`, or `setPlayRate` on the model\'s own rate, which is the "frames per second" given',
      'in the contact-sheet row).  Frame order is the child order of the `SequenceNode`, which is the',
      'numbering used here (`_01` is the first frame).', '',
      '**Shared sheets.**  Most sprites are not files of their own.  The models\' cards point into',
      '"palette" textures (`*_palette_*.jpg` + `_a.rgb`, or `.rgb` with the alpha inside) that pack many',
      'unrelated images together, each card using only its UV rectangle.  For every such sprite this',
      'folder has the cropped rectangle (in its kind\'s folder) and the whole sheet once (in `sheets/`);',
      'the row gives the sheet and the top-left pixel of the crop, counted from the top-left of the sheet.',
      'Several of these sheets also hold non-effect art (props, scenery, GUI); only the listed rectangles',
      'belong to effects.', '',
      '## What a replacement must keep the same', '',
      '- **File name and path.**  The game loads the texture path stored in the model file, so a redrawn',
      '  image has to go back under the original path given in the table (same base name; the HD pack',
      '  mirrors `resources/` paths).  For a cropped sprite the file that is actually replaced is its',
      '  sheet: the redrawn sprite must be pasted back into the sheet at the same rectangle.',
      '- **Aspect ratio.**  The card geometry is fixed in the model, so the image is stretched to the',
      '  card.  Keep the width:height of the original (any whole multiple of the pixel size is fine).',
      '- **UV layout of a shared sheet.**  UVs are fractions of the sheet, so a sheet may be enlarged by',
      '  any factor, but every sprite must stay at the same fractional position and size.  The cards',
      '  sample right up to the rectangle\'s edge: keep a sprite\'s paint inside its rectangle and leave',
      '  the gaps between rectangles as they are, or neighbours bleed into each other.',
      '- **Alpha.**  Everything here is drawn with transparency; a replacement needs an alpha channel',
      '  with the same meaning (transparent background, soft edges where the original has them).  The',
      '  originals marked with an alpha file are a JPEG plus a separate greyscale `_a.rgb`; a replacement',
      '  must provide alpha in whatever form the loader for the replacement set expects.',
      '- **Colour.**  Sprites that the code tints (most particle sprites, splats, glow, fireworks) are',
      '  multiplied by a colour at runtime; keep them white / greyscale where the original is, or the',
      '  tint will come out wrong.',
      '- **Frame count and order.**  A flipbook must keep the same number of frames in the same order,',
      '  each frame in its own original rectangle (frames are separate rectangles of the sheets, not a',
      '  regular grid; the contact sheets here are for viewing only and are not loaded by the game).',
      '  Frames keep their own sizes: where a flipbook\'s frames differ in size, each is centred in a',
      '  cell of the largest frame in the contact sheet.',
      '- **One image, many users.**  When a row lists several nodes or models, they all show the same',
      '  rectangle; one redraw changes all of them.', '']

L += ['## Named in the code but not exported', '']
for path, why in missing:
    L.append('- `%s`: %s' % (path, why))
L += ['- `resistanceEffectSprite.ptf` (`toontown/chat/ResistanceChat.py`) uses the gag icons of',
      '  `phase_3.5/models/gui/inventory_icons` as particles; those are GUI art and are left out.',
      '  `resistanceEffectBean.ptf` uses a 3D jellybean model, not an image.',
      '- `phase_5/models/props/geyser`, node `hole`: a ground-hole mesh coloured from a scenery palette,',
      '  not an effect card.', '']
if empty:
    L += ['Images that came out with no visible pixel: ' + ', '.join('`%s`' % e for e in empty), '']

TITLES = {'battle-particles': 'Battle particle sprites', 'battle-props': 'Battle prop cards',
          'world-effects': 'World effects', 'shadows': 'Shadows', 'flipbooks': 'Flipbooks'}
for folder in FOLDERS[:-1]:
    these = [r for r in rows if r['folder'] == folder]
    if folder != 'flipbooks':
        these.sort(key=lambda r: r['out'].lower())
    L += ['## %s/ - %s (%d files)' % (folder, TITLES[folder], len(these)), '',
          '| file | original (model :: node -> texture) | size | alpha file | used by |', '|---|---|---|---|---|']
    for r in these:
        L.append('| `%s` | %s | %dx%d | %s | %s |' % (r['out'], origin_cell(r), r['size'][0], r['size'][1],
                                                     alpha_cell(r), used_cell(r)))
    L.append('')
L += ['## sheets/ - shared textures the crops come from (%d files)' % len(sheets), '',
      '| file | original path | size | alpha file | effect sprites cropped from it |', '|---|---|---|---|---|']
for path in sorted(sheets, key=lambda p: sheets[p]['out'].lower()):
    r = sheets[path]
    holds = r['holds']
    shown = ', '.join('`%s`' % h for h in holds[:8]) + (', ... %d in all' % len(holds) if len(holds) > 8 else '')
    L.append('| `%s` | `%s` | %dx%d | %s | %s |' % (r['out'], path, r['size'][0], r['size'][1], alpha_cell(r), shown))
L.append('')
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'README.md'), 'w') as f:
    f.write('\n'.join(L))

print('written', sum(count.values()), count)
print('flipbooks', [(os.path.basename(r['model']), r['frames']) for r in flip])
print('missing / not exported:')
for m in missing:
    print('  ', m)
print('empty images:', empty)
print('mostly transparent (<3% visible):', [r['out'] for r in rows if r['visible'] < 0.03])
