#!/usr/bin/env python
"""
Writes the 2D textures Toons are drawn with as PNG files, alpha merged in.

Collected from two places:
  * every texture referenced by a Toon piece model (heads, dog muzzle sets,
    eyelashes, torsos, legs, at all three levels of detail), and
  * every texture path the code lists for Toons: ToonDNA.Shirts, Sleeves,
    BoyShorts, GirlBottoms, ShoesTextures, and the eye / muzzle textures
    ToonHead loads by name.

Output folder (default ../open-toontown-hd/toon-sprites):
  clothing/   shirts, sleeves, shorts, skirts
  head/       eyes, pupils, eyelashes, muzzles, head palettes
  body/       hands, neck, legs/feet palettes, shoes and boots
  README.md   every file, its original path, pixel size and what uses it

These are the ORIGINAL textures from resources/: the HD texture pack
(toontown.toonbase.HDTextures) is deliberately not switched on.  Nothing is
launched; the offscreen ShowBase is only there to give the loader a context.

Usage (from the repository root, with the game's Python):
    PYTHONPATH=. venv/bin/python tools/export_toon_sprites.py [output folder]
"""
import os
import sys
from panda3d.core import *
loadPrcFile('etc/Configrc.prc')
loadPrcFileData('', 'window-type offscreen\nwin-size 64 64\naudio-library-name null\nwant-postfx 0\n'
                    'notify-level warning\ndefault-directnotify-level warning\n'
                    # keep every image at the size it has on disk
                    'textures-power-2 none\ntexture-scale 1\nmax-texture-dimension -1\n'
                    'compressed-textures 0\n')
from direct.showbase.ShowBase import ShowBase
b = ShowBase()
b.shadowTrav = CollisionTraverser('shadowTrav')
b.wantNametags = False
from toontown.toon import Toon, ToonDNA, ToonHead

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '../open-toontown-hd/toon-sprites')
RESOURCES = os.path.abspath('resources')
vfs = VirtualFileSystem.getGlobalPtr()
search = getModelPath().getValue()

# key: path relative to resources/ -> record
records = {}


def rel(fullpath):
    p = Filename(fullpath).toOsSpecific()
    if p.startswith(RESOURCES + os.sep):
        p = p[len(RESOURCES) + 1:]
    return p.replace(os.sep, '/')


def record(path, alpha):
    r = records.get(path)
    if r is None:
        r = records[path] = {'path': path, 'alpha': alpha, 'models': {}, 'code': []}
    if alpha and not r['alpha']:
        r['alpha'] = alpha
    return r


def resolve(path):
    fn = Filename(path)
    return vfs.resolveFilename(fn, search) and fn


# ---------------------------------------------------------------- textures the models reference
models = []
for prefix in sorted(set(ToonHead.HeadDict.values())):
    models += [('head', 'phase_3' + prefix + lod) for lod in ('1000', '500', '250')]
for prefix in sorted(set(ToonHead.DogMuzzleDict.values())):
    models += [('head', 'phase_3' + prefix + lod) for lod in ('1000', '500')]
for prefix in sorted(set(ToonHead.EyelashDict.values())):
    models.append(('head', 'phase_3' + prefix))
for key in ('ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l'):
    models += [('torso', 'phase_3' + Toon.TorsoDict[key] + lod) for lod in ('1000', '500', '250')]
for key in ('s', 'm', 'l'):
    models += [('legs', 'phase_3' + Toon.LegDict[key] + lod) for lod in ('1000', '500', '250')]

missing_models = []
for kind, path in models:
    m = loader.loadModel(path, okMissing=True)
    if not m:
        missing_models.append(path)
        continue
    short = os.path.basename(path)
    for np in m.findAllMatches('**/+GeomNode'):
        node = np.node()
        name = np.getName() or '(unnamed)'
        net = np.getNetState()
        for gi in range(node.getNumGeoms()):
            ta = net.compose(node.getGeomState(gi)).getAttrib(TextureAttrib)
            if ta is None or ta.isOff():
                continue
            for si in range(ta.getNumOnStages()):
                tex = ta.getOnTexture(ta.getOnStage(si))
                if not tex.hasFullpath():
                    continue
                alpha = rel(tex.getAlphaFullpath()) if tex.hasAlphaFullpath() else None
                r = record(rel(tex.getFullpath()), alpha)
                r['models'].setdefault(short, set()).add(name)
                r.setdefault('kinds', set()).add(kind)

# ---------------------------------------------------------------- textures the code lists
def listed(path, use, kind, alpha=None):
    if alpha is None:
        guess = os.path.splitext(path)[0] + '_a.rgb'
        if resolve(guess):
            alpha = guess
    r = record(path, alpha)
    r['code'].append(use)
    r.setdefault('kinds', set()).add(kind)


for i, p in enumerate(ToonDNA.Shirts):
    listed(p, 'ToonDNA.Shirts[%d]' % i, 'shirt')
for i, p in enumerate(ToonDNA.Sleeves):
    listed(p, 'ToonDNA.Sleeves[%d]' % i, 'sleeve')
for i, p in enumerate(ToonDNA.BoyShorts):
    listed(p, 'ToonDNA.BoyShorts[%d]' % i, 'shorts')
for i, (p, bottomType) in enumerate(ToonDNA.GirlBottoms):
    listed(p, 'ToonDNA.GirlBottoms[%d] (%s)' % (i, 'skirt' if bottomType == ToonDNA.SKIRT else 'shorts'),
           'skirt' if bottomType == ToonDNA.SKIRT else 'shorts')
for i, p in enumerate(ToonDNA.ShoesTextures):
    listed(p, 'ToonDNA.ShoesTextures[%d]' % i, 'shoes')
    # Toon.generateShoes swaps in "<name>LL.jpg" for long boots on long legs
    ll = p[:-4] + 'LL.jpg'
    if resolve(ll):
        listed(ll, 'ToonDNA.ShoesTextures[%d], long-legs version (Toon.generateShoes)' % i, 'shoes')
for attr in ('EyesOpen', 'EyesClosed', 'EyesSadOpen', 'EyesSadClosed', 'EyesAngryOpen', 'EyesAngryClosed',
             'EyesSurprised', 'Muzzle', 'MuzzleSurprised'):
    tex = getattr(ToonHead.ToonHead, attr)
    alpha = rel(tex.getAlphaFullpath()) if tex.hasAlphaFullpath() else None
    listed(rel(tex.getFullpath()), 'ToonHead.%s' % attr, 'head', alpha or '')


def folder_for(r):
    kinds = r.get('kinds', set())
    base = os.path.basename(r['path']).lower()
    if kinds & {'shirt', 'sleeve', 'shorts', 'skirt'}:
        return 'clothing'
    # a palette shared by the head and the body models goes with the body
    if kinds == {'head'}:
        return 'head'
    return 'body'


# ---------------------------------------------------------------- write the PNGs
written = []
failed = []
names = {}
for path in sorted(records):
    r = records[path]
    fn = resolve(path)
    if not fn:
        failed.append((path, 'file not found on the model path'))
        continue
    tex = Texture()
    alpha_fn = resolve(r['alpha']) if r['alpha'] else None
    ok = tex.read(fn, alpha_fn, 0, 0) if alpha_fn else tex.read(fn)
    img = PNMImage()
    if not ok or not tex.store(img):
        failed.append((path, 'Panda could not read the image'))
        continue
    folder = folder_for(r)
    stem = os.path.splitext(os.path.basename(path))[0]
    key = (folder, stem.lower())
    if key in names and names[key] != path:
        stem = path.split('/')[0] + '_' + stem      # same base name in two phases
    names[key] = path
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    out = os.path.join(OUT, folder, stem + '.png')
    img.write(Filename.fromOsSpecific(out))
    r.update({'out': '%s/%s.png' % (folder, stem), 'size': (img.getXSize(), img.getYSize()),
              'channels': img.getNumChannels()})
    written.append(r)

# ---------------------------------------------------------------- README
def uses(r):
    out = []
    # merge the three levels of detail of one model into one entry
    merged = {}
    for model, nodes in r['models'].items():
        stem = model
        for lod in ('1000', '500', '250'):
            if stem.endswith(lod):
                stem = stem[:-len(lod)].rstrip('-_')
        merged.setdefault(stem, set()).update(nodes)
    for stem in sorted(merged):
        out.append('%s: %s' % (stem, ', '.join(sorted(merged[stem]))))
    code = r['code']
    if len(code) > 6:
        code = code[:6] + ['... %d entries in all' % len(r['code'])]
    out += code
    return '; '.join(out)


lines = ['# Toon sprites', '',
         'The 2D textures the player characters (Toons) are drawn with, written as PNG by',
         '`tools/export_toon_sprites.py` in the open-toontown repository.  These are the original',
         'files from `resources/` (the HD texture pack was not enabled).  Where the game pairs a',
         '`.jpg` colour image with a separate `_a.rgb` alpha image, the two are merged into one RGBA PNG;',
         'the "alpha" column names the alpha file that was merged.  Base names are unchanged.', '',
         'How the list was collected:', '',
         '- every texture referenced by a Toon piece model: the head models in `ToonHead.HeadDict`,',
         '  the dog muzzle sets in `ToonHead.DogMuzzleDict`, the eyelash models in `ToonHead.EyelashDict`,',
         '  the torso models in `Toon.TorsoDict` and the legs models in `Toon.LegDict`, at every level of',
         '  detail that exists (1000 / 500 / 250);',
         '- every path in `ToonDNA.Shirts`, `ToonDNA.Sleeves`, `ToonDNA.BoyShorts`, `ToonDNA.GirlBottoms`',
         '  and `ToonDNA.ShoesTextures`, and the eye and muzzle textures the `ToonHead` class loads by name.', '',
         'Not included: the textures of the hat, glasses and backpack accessory models',
         '(`ToonDNA.HatTextures`, `GlassesTextures`, `BackpackTextures`); those belong to separate',
         'accessory models, not to the head / torso / legs pieces.', '',
         'In the "used by" column, `model: node, node` means those nodes of that model file reference',
         'the texture as stored (levels of detail merged); `ToonDNA.X[i]` means index `i` of that list,',
         'which is the number a Toon\'s DNA stores.  In the game the clothing textures are multiplied',
         'by a `ToonDNA.ClothesColors` entry and the body parts by a `ToonDNA.allColorsList` entry',
         '(see `../toon-turnarounds/README.md`); the PNGs here are the untinted images.',
         'A palette that both head models and torso / legs models reference is filed under `body/`.', '',
         'Files written: %d (clothing %d, head %d, body %d).' % (
             len(written), sum(1 for r in written if r['out'].startswith('clothing/')),
             sum(1 for r in written if r['out'].startswith('head/')),
             sum(1 for r in written if r['out'].startswith('body/'))), '']
if failed or missing_models:
    lines += ['## Not exported', '']
    for path, why in failed:
        lines.append('- `%s`: %s' % (path, why))
    for path in missing_models:
        lines.append('- model `%s` is named by the code but is not in `resources/`, so it contributed no textures' % path)
    lines.append('')
for folder, title in (('clothing', 'clothing/'), ('head', 'head/'), ('body', 'body/')):
    rows = sorted((r for r in written if r['out'].startswith(folder + '/')), key=lambda r: r['out'].lower())
    lines += ['## %s (%d files)' % (title, len(rows)), '',
              '| file | original path | size | alpha | used by |', '|---|---|---|---|---|']
    for r in rows:
        lines.append('| `%s` | `%s` | %dx%d | %s | %s |' % (
            r['out'], r['path'], r['size'][0], r['size'][1],
            ('`%s`' % os.path.basename(r['alpha'])) if r['alpha'] else 'none', uses(r)))
    lines.append('')
with open(os.path.join(OUT, 'README.md'), 'w') as f:
    f.write('\n'.join(lines))
print('written', len(written), 'failed', failed, 'missing models', missing_models)
