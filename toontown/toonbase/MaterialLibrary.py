"""
Maps the game's textures onto real-world materials.

Toontown's art is flat painted colour with no surface detail.  Each rule
below says "a texture with this kind of name is this kind of material", and
each material names a tiling normal map taken from a scanned-material
library (Poly Haven, Greyscalegorilla).  PostFX projects that normal map
onto the surface in world space, so it does not depend on the model's UVs.

The normal maps live in resources-hd/materials/ and are not part of the
repository.  A material whose file is missing is simply skipped.

Textures whose name contains "palette" are atlases that pack several
unrelated objects into one image; they cannot be given a single material and
are left alone.
"""
import re

# name: (file under materials/, world units per repeat, strength)
#
# The library map only supplies fine surface grain.  The layout of a surface
# (where its tiles, bricks, boards or stones are) is painted into the game's
# own texture and PostFX reads it from there, so the maps used here must not
# have a layout of their own: a brick normal map would draw its bricks
# straight across the painted ones.  That is why brick uses a plaster grain
# and wood uses a bark grain rather than the obvious "brick" and "planks"
# scans.  Directional maps must run vertically in the image.
MATERIALS = {
    'grass':    ('leafy_grass_nor_gl_2k.jpg', 9.0, 0.55),
    'cobble':   ('concrete_floor_02_nor_gl_2k.jpg', 5.0, 0.9),
    'brick':    ('painted_plaster_wall_nor_gl_2k.jpg', 6.0, 0.7),
    'plaster':  ('painted_plaster_wall_nor_gl_2k.jpg', 9.0, 0.6),
    'roof':     ('painted_plaster_wall_nor_gl_2k.jpg', 5.0, 0.6),
    'planks':   ('bark_brown_02_nor_gl_2k.jpg', 7.0, 0.30),
    'bark':     ('bark_brown_02_nor_gl_2k.jpg', 5.0, 0.8),
    'sand':     ('sand_01_nor_gl_2k.jpg', 8.0, 0.6),
    'snow':     ('snow_02_nor_gl_2k.jpg', 10.0, 0.5),
    'concrete': ('concrete_floor_02_nor_gl_2k.jpg', 8.0, 0.7),
    'woodfloor': ('bark_brown_02_nor_gl_2k.jpg', 7.0, 0.20),
    'fabric':   ('GSG_MC032_A010_MicrofiberJerseyLightGreen_normal.png', 0.6, 0.5),
}

# First match wins, so the specific rules come before the general ones.
RULES = [
    (r'palette|shadow|background|gui|icon|font|logo|sky|cloud|water|glass|window|sign', None),
    (r'hedge|grass|lawn|groundcover', 'grass'),
    (r'snow|ice_', 'snow'),
    (r'sand|beach|dirt|dustroad', 'sand'),
    (r'roof|shingle', 'roof'),
    (r'cobble|rockroad|stonewall|stone_wall|fence_stone|rock', 'cobble'),
    (r'brick', 'brick'),
    (r'floor_wood|woodtile|wood_floor|hardwood|parquet', 'woodfloor'),
    (r'boardwalk|plank|fence_wood|wall_fence_wood|wood|crate|barrel|dock', 'planks'),
    (r'bark|trunk', 'bark'),
    (r'sidewalk|curb|pave|plazz|steps|cement|concrete|street|road|tile', 'concrete'),
    (r'stucco|plaster|^wall_|_wall', 'plaster'),
    (r'shirt|sleeve|shorts|skirt|blazer|^c_arm|^c_leg|^c_sleeve|cloth|carpet|fabric|couch', 'fabric'),
]
_RULES = [(re.compile(p, re.I), m) for p, m in RULES]

_byTexture = {}
_loaded = {}


def materialFor(textureName):
    """Returns a material name for a texture name, or None."""
    if textureName in _byTexture:
        return _byTexture[textureName]
    result = None
    for pattern, material in _RULES:
        if pattern.search(textureName):
            result = material
            break
    _byTexture[textureName] = result
    return result


def normalMap(material, loader):
    """Returns (Texture, unitsPerRepeat, strength) or None if unavailable."""
    if material in _loaded:
        return _loaded[material]
    entry = None
    filename, units, strength = MATERIALS[material]
    from panda3d.core import SamplerState
    tex = loader.loadTexture('materials/' + filename, okMissing=True)
    if tex is not None:
        tex.setWrapU(SamplerState.WM_repeat)
        tex.setWrapV(SamplerState.WM_repeat)
        tex.setMinfilter(SamplerState.FT_linear_mipmap_linear)
        tex.setMagfilter(SamplerState.FT_linear)
        tex.setAnisotropicDegree(8)
        entry = (tex, units, strength)
    _loaded[material] = entry
    return entry
