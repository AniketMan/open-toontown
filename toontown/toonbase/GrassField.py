"""
GrassField: real blades of grass on the playground lawns.

Toontown paints its lawns: in most playgrounds one large texture holds the
grass, the paths and everything between.  So grass is placed by looking at
that painting.  A patch of ground gets blades only where the texture under
it is green, and the blades are tinted with the colour found there, which
keeps each playground's own shade of green.

How it stays cheap in an engine with no geometry instancing shaders:

  - A few square "tiles" of jittered blades (8, 4 and 2 feet wide) are built
    once.  Every patch of lawn shows one of those tiles through its own
    scene node, so the blade geometry itself is shared.
  - Ground is covered by the largest tile that fits: all green underneath
    and flat enough.  Along path edges and on slopes, smaller tiles are
    used, down to 2 feet.
  - Tiles are grouped into blocks that switch off beyond VIEW_DISTANCE, and
    a small shader dissolves blades away before that, so
    nothing pops.  The same shader sways them in the wind.

The tiles are parented under the ground geometry they sit on, so they are
hidden and removed along with their zone.
"""
import math
import random
import time
import re

from panda3d.core import (ConfigVariableDouble, TransformState, BitMask32, Character, TransparencyAttrib, Texture, ColorAttrib, ColorScaleAttrib, BoundingBox, ColorBlendAttrib,
                          CullFaceAttrib, SamplerState, Geom, GeomNode,
                          GeomTriangles, GeomVertexData, GeomVertexFormat,
                          GeomVertexReader, GeomVertexWriter, LODNode,
                          NodePath, PNMImage, Point3, Shader, TextureAttrib,
                          Vec3, Vec4)
from direct.directnotify import DirectNotifyGlobal

TILE_SIZES = (8.0, 4.0, 2.0)
BLADES_PER_SQFT = 12.0
BLADE_HEIGHT = (0.34, 1.35)     # most blades sit near the short end
BLADE_WIDTH = (0.07, 0.13)
WIND_STRENGTH = 0.50
# Level of detail, by distance from the camera in feet.  The lawn thins
# continuously from FADE_NEAR to FADE_FAR: every blade has its own distance
# at which it is gone, and those distances are spread so that each doubling
# of distance removes the same share of blades.  On screen, where far ground
# is squeezed into a thin strip, that reads as one even thinning with no
# band where it starts or stops.  Inside FADE_NEAR the lawn is at full
# density.  Each blade dissolves over the last third or so of
# its own range, turns the colour of the lawn as it goes, and the blades
# still standing widen to keep the ground covered.
#
# A third of the blades last beyond FADE_MID.  Past LOD_SWITCH a block draws
# only those (a lighter mesh of the very same blades, so nothing changes).
FADE_NEAR = 65.0
FADE_MID = 135.0
FADE_FAR = 270.0
KEEP_FRACTION = 1.0 / 3.0
BLOCK_SIZE = 24.0
LOD_SWITCH = FADE_MID + BLOCK_SIZE * 0.75
VIEW_DISTANCE = FADE_FAR       # blades are gone by here
# Grass climbs slopes up to about 60 degrees; steeper is a bank or a wall.
MIN_UP = 0.5
MAX_BUMP = 0.2                 # how far ground may stray from a tile's plane
MAX_TILES = 24000
MAX_LAWN = 800.0       # feet across; anything wider is not planted
# Milliseconds a frame may spend planting grass; 0 plants it all at once.
PLANT_BUDGET = ConfigVariableDouble('grass-plant-ms', 5.0).value
# No grass where something else lies over the lawn within this many feet:
# pond water, sidewalks, steps, hedges.  (Flat decals such as drop shadows,
# which sit a hair above the ground, do not count.)
COVER_HEIGHT = 5.0
SHADOW_CLEARANCE = 0.3  # a see-through sheet this far off the ground is not a painted shadow
COVER_MIN = -0.02       # paving, pads and roads laid flat on the lawn count as cover
SHADOW_NAMES = re.compile(r'shad+ow', re.I)
WATER_NAMES = re.compile(r'water|pond|lake|river|pool|ocean', re.I)   # ...but painted shadows do not
# The baked meadow texture (tools/bake_meadow.py) laid over the painted lawn.
MEADOW_TEXTURE = 'materials/meadow_detail.png'
MEADOW_REPEAT = 22.0           # feet per repeat
MEADOW_STRENGTH = 1.0

# Ground worth examining: by node or texture name.  The green test below is
# what actually decides, so this only has to be generous.
GROUND_NAME = re.compile(r'grass|lawn|floor|ground|terrain|site_plan|field', re.I)
# A sheet of grass texture far below some playgrounds, never seen up close.
SKIP_NAME = re.compile(r'^base_', re.I)
NOT_LAWN = re.compile(r'hedge|tree|leaf|leaves|bush|roof|wall|sky|shadow', re.I)

VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform vec4 p3d_ColorScale;
uniform float osg_FrameTime;
uniform mat4 p3d_ModelViewMatrix;
uniform vec4 grassParams;      // fade near, mid, far, unused
uniform vec4 grassWind;        // strength, share of blades kept at distance, unused, unused
attribute vec4 p3d_Vertex;     // the blade's root
attribute vec3 p3d_Normal;     // from the root to this vertex
attribute vec4 p3d_Color;
attribute vec2 p3d_MultiTexCoord0;   // x: per-blade random, y: 0 at root, 1 at tip
varying vec3 vColor;
varying vec2 vFade;            // x: how visible, y: per-blade random
void main() {
    vec4 root = vec4(p3d_Vertex.xyz, 1.0);
    float dist = length((p3d_ModelViewMatrix * root).xyz);
    // Every blade has its own distance at which it is gone, spread evenly
    // in the logarithm of distance, and dissolves over the last half of the
    // way there.  Blades keep their full size: they dissolve, not shrink.
    float r = p3d_MultiTexCoord0.x;
    float keep = grassWind.y;
    float end;
    if (r >= keep) {
        end = grassParams.x * pow(grassParams.y / grassParams.x, 1.0 - (r - keep) / (1.0 - keep));
    } else {
        end = grassParams.y * pow(grassParams.z / grassParams.y, 1.0 - r / keep);
    }
    float fade = 1.0 - smoothstep(end * 0.62, end, dist);
    // How far through the whole thinning this spot is, 0 near to 1 far.
    float thin = clamp(log(dist / grassParams.x) / log(grassParams.z / grassParams.x), 0.0, 1.0);
    // Fully faded blades are folded away so they cost nothing to draw.
    float grow = step(0.004, fade);
    float widen = 1.0 + 0.8 * thin;
    vec3 world = (p3d_ModelMatrix * root).xyz;
    float t = osg_FrameTime;
    float phase = r * 6.2831853 * 3.0;
    // A slow gust front rolling across the lawn, a steady lean with it,
    // and each blade's own quicker flutter on top.
    float gust = sin(t * 0.55 - world.x * 0.045 - world.y * 0.02) * 0.5 + 0.5;
    gust *= gust;
    float sway = 0.25 + gust * 0.9
               + sin(t * 1.3 + world.x * 0.19 + world.y * 0.15) * 0.35
               + sin(t * 3.1 + phase) * (0.12 + gust * 0.22);
    float cross = sin(t * 2.3 + phase * 1.7) * (0.10 + gust * 0.15);
    // p3d_Color.a carries the blade's height: tall blades swing further.
    float reach = grassWind.x * (0.45 + p3d_Color.a * 1.3);
    vec3 windWorld = (vec3(1.0, 0.4, 0.0) * sway + vec3(-0.4, 1.0, 0.0) * cross) * reach;
    // world -> model for a rotation is the transpose
    vec3 wind = (vec4(windWorld, 0.0) * p3d_ModelMatrix).xyz;
    float tip = p3d_MultiTexCoord0.y;
    vec3 blade = vec3(p3d_Normal.xy * mix(widen, 1.0, tip), p3d_Normal.z);
    vec3 pos = root.xyz + blade * grow + wind * tip * tip * grow;
    pos.z -= dot(wind.xy, wind.xy) * tip * 0.6 * grow;   // bending shortens it
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(pos, 1.0);
    // A fading blade also drifts towards the colour of the lawn under it.
    vec3 lawn = p3d_ColorScale.rgb;
    // So does every blade with distance, so far blades barely stand out
    // from the ground and their going is not noticed.
    vColor = mix(lawn, p3d_Color.rgb * lawn * 1.12, (0.3 + 0.7 * fade) * (1.0 - 0.75 * thin));
    vFade = vec2(fade, r);
}
"""

FRAG = """#version 120
varying vec3 vColor;
varying vec2 vFade;
void main() {
    // Dissolve: a fading blade keeps a shrinking share of its pixels, in a
    // fine pattern that differs from blade to blade.  The anti-aliasing
    // pass afterwards smooths that into an even fade.
    if (vFade.x < 0.999) {
        float n = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));
        if (vFade.x <= fract(n + vFade.y * 7.31)) discard;
    }
    gl_FragColor = vec4(vColor, 1.0);
}
"""


# The meadow layer: the lawn's own geometry drawn a second time with a
# "multiply by two" blend, so 0.5 in the baked texture leaves the lawn as
# painted.  It only acts where the lawn's painting is green (the same test
# that places the blades, done per pixel, so paths keep clean edges).  The
# pattern is laid out by world position; a second, much larger sample breaks
# up the repeat.
GROUND_VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;
uniform mat4 p3d_ModelViewMatrix;
varying vec2 vWorld;
varying vec2 vUv;
varying float vDist;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vWorld = (p3d_ModelMatrix * p3d_Vertex).xy;
    vUv = p3d_MultiTexCoord0;
    vDist = length((p3d_ModelViewMatrix * p3d_Vertex).xyz);
}
"""

GROUND_FRAG = """#version 120
uniform sampler2D p3d_Texture0;
uniform sampler2D meadow;
uniform vec4 meadowParams;     // feet per repeat, strength, calm start, calm end
varying vec2 vWorld;
varying vec2 vUv;
varying float vDist;
void main() {
    vec3 lawn = texture2D(p3d_Texture0, vUv).rgb;
    float green = lawn.g - max(lawn.r * 1.12, lawn.b * 1.25);
    float mask = smoothstep(0.0, 0.07, green) * step(0.25, lawn.g);
    // Up close the ground shows every stroke.  Further off, where no
    // blades stand over it, the fine detail is blurred and turned down so
    // the lawn stays a calm cartoon green with soft patches, not a busy one.
    float calm = smoothstep(meadowParams.z, meadowParams.w, vDist);
    vec3 near = texture2D(meadow, vWorld / meadowParams.x, calm * 5.0).rgb;
    vec3 far = texture2D(meadow, vWorld.yx / (meadowParams.x * 6.3) + 0.37, 2.0 + calm * 2.0).rgb;
    vec3 d = 0.5 + (near - 0.5) * mix(0.8, 0.10, calm) + (far - 0.5) * mix(0.6, 0.45, calm);
    gl_FragColor = vec4(mix(vec3(0.5), d, mask * meadowParams.y), 1.0);
}
"""


def isGreen(c):
    """Is this texture colour lawn?"""
    r, g, b = c[0], c[1], c[2]
    return g > 0.25 and g > r * 1.12 and g > b * 1.25


def geomNodes(root):
    """Every GeomNode under root, as findAllMatches('**/+GeomNode') gives,
    but without walking into planted grass: its thousands of tiles made
    that search take a quarter of a second."""
    found = []
    stack = [root]
    while stack:
        np = stack.pop()
        node = np.node()
        if node.hasTag('postfx-grass'):
            continue
        if node.isGeomNode():
            found.append(np)
        if node.getNumChildren():
            stack.extend(np.getChildren())
    return found


class GrassField:
    notify = DirectNotifyGlobal.directNotify.newCategory('GrassField')

    def __init__(self, base, hideFrom):
        self.base = base
        self.hideFrom = hideFrom       # camera bits that must not see grass
        self.shader = Shader.make(Shader.SL_GLSL, VERT, FRAG)
        self.tiles = {}
        self.images = {}
        self.tileCount = 0
        self.pending = []              # lawns still being planted
        self.lawns = []                # (holder, [tiles]) of planted lawns
        rng = random.Random(7)
        self.farTiles = {}
        for size in TILE_SIZES:
            self.tiles[size], self.farTiles[size] = self._makeTile(size, rng)
        self.meadow = self.base.loader.loadTexture(MEADOW_TEXTURE, okMissing=True)
        if self.meadow is None:
            self.notify.info('no %s; lawn stays flat (run tools/bake_meadow.py)' % MEADOW_TEXTURE)
        else:
            self.meadow.setWrapU(SamplerState.WM_repeat)
            self.meadow.setWrapV(SamplerState.WM_repeat)
            self.meadow.setMinfilter(SamplerState.FT_linear_mipmap_linear)
            self.meadow.setAnisotropicDegree(8)
            self.meadowShader = Shader.make(Shader.SL_GLSL, GROUND_VERT, GROUND_FRAG)

    def _addMeadow(self, np):
        """Lays the baked meadow texture over a lawn node."""
        if self.meadow is None or not np.find('meadow').isEmpty():
            return
        over = np.attachNewNode(np.node().makeCopy())
        over.setName('meadow')
        over.node().removeAllChildren()
        over.setTag('postfx-grass', '1')
        over.setShader(self.meadowShader, 10)
        over.setShaderInput('meadow', self.meadow)
        over.setShaderInput('meadowParams', Vec4(MEADOW_REPEAT, MEADOW_STRENGTH, 6.0, 45.0))
        # result = lawn * texture * 2
        over.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                             ColorBlendAttrib.OFbufferColor,
                                             ColorBlendAttrib.OIncomingColor), 10)
        over.setDepthWrite(False, 10)
        over.setDepthOffset(1, 10)
        over.setBin('fixed', -100, 10)
        over.hide(self.hideFrom)

    def _makeTile(self, size, rng):
        """A size x size square of blades centred on the origin, z up.
        Returns (full tile, far tile); the far tile is the first
        KEEP_FRACTION of the same blades."""
        count = max(1, int(round(size * size * BLADES_PER_SQFT)))
        vdata = GeomVertexData('grass', GeomVertexFormat.getV3n3c4t2(), Geom.UHStatic)
        vdata.setNumRows(count * 5)
        vw = GeomVertexWriter(vdata, 'vertex')
        nw = GeomVertexWriter(vdata, 'normal')
        cw = GeomVertexWriter(vdata, 'color')
        tw = GeomVertexWriter(vdata, 'texcoord')
        prim = GeomTriangles(Geom.UHStatic)
        farPrim = GeomTriangles(Geom.UHStatic)
        kept = max(1, int(count * KEEP_FRACTION))
        half = size / 2.0
        lo, hi = BLADE_HEIGHT
        # Grass grows in tufts: a few random centres per tile raise the
        # blades around them.
        tufts = [(rng.uniform(-half, half), rng.uniform(-half, half), rng.uniform(0.7, 1.6))
                 for _ in range(max(2, int(size * size / 5.0)))]
        for i in range(count):
            x, y = rng.uniform(-half, half), rng.uniform(-half, half)
            near = 0.0
            for tx, ty, tr in tufts:
                d = math.hypot(x - tx, y - ty) / tr
                if d < 1.0:
                    near = max(near, 1.0 - d * d)
            # Skewed towards short, lifted inside a tuft, with the odd
            # tall stalk anywhere.
            k = rng.random() ** 2.2 * 0.55 + near * rng.uniform(0.15, 0.5)
            if rng.random() < 0.04:
                k += rng.uniform(0.3, 0.5)
            k = min(k, 1.0)
            h = lo + (hi - lo) * k
            w = rng.uniform(*BLADE_WIDTH) / 2.0 * (0.8 + 0.5 * k)
            a = rng.uniform(0, math.pi)
            dx, dy = math.cos(a) * w, math.sin(a) * w
            # Blades arc over rather than standing straight.
            lean = rng.uniform(0.15, 0.6) * h
            la = rng.uniform(0, 2 * math.pi)
            lx, ly = math.cos(la) * lean, math.sin(la) * lean
            shade = rng.uniform(0.80, 1.0) * (1.0 - 0.10 * k)
            # The blades kept at distance get the low end of the range.
            r = rng.uniform(0.0, KEEP_FRACTION) if i < kept else rng.uniform(KEEP_FRACTION, 1.0)
            mz = h * 0.58
            tz = h * (1.0 - 0.12 * lean / h)
            for offset, tip, bright in (((-dx, -dy, 0.0), 0.0, 0.70),
                                        ((dx, dy, 0.0), 0.0, 0.70),
                                        ((lx * 0.3 - dx * 0.7, ly * 0.3 - dy * 0.7, mz), 0.5, 0.88),
                                        ((lx * 0.3 + dx * 0.7, ly * 0.3 + dy * 0.7, mz), 0.5, 0.88),
                                        ((lx, ly, tz), 1.0, 1.0)):
                vw.setData3(x, y, 0.0)
                nw.setData3(*offset)
                cw.setData4(shade * bright, shade * bright, shade * bright, k)
                tw.setData2(r, tip)
            v = i * 5
            prim.addVertices(v, v + 1, v + 2)
            prim.addVertices(v + 1, v + 3, v + 2)
            prim.addVertices(v + 2, v + 3, v + 4)
            if i < kept:
                farPrim.addVertices(v, v + 1, v + 2)
                farPrim.addVertices(v + 1, v + 3, v + 2)
                farPrim.addVertices(v + 2, v + 3, v + 4)
        prim.closePrimitive()
        farPrim.closePrimitive()
        # Culling works from the blade roots; pad for the blades themselves.
        bounds = BoundingBox(Point3(-half - 1.2, -half - 1.2, -0.2),
                             Point3(half + 1.2, half + 1.2, 2.6))
        result = []
        for name, p in (('grass-tile-%d', prim), ('grass-far-%d', farPrim)):
            geom = Geom(vdata)
            geom.addPrimitive(p)
            node = GeomNode(name % int(size))
            node.addGeom(geom)
            node.setBounds(bounds)
            node.setFinal(True)
            result.append(NodePath(node))
        return result

    def _opacity(self, tex):
        """Returns opacity(u, v) for a texture, or None if it is solid.
        Many of the game's textures keep their transparency in a second,
        grey-scale file beside the colour one."""
        key = tex.getName()
        cache = self.__dict__.setdefault('opacities', {})
        if key not in cache:
            fn = None
            mask = PNMImage()
            if tex.hasAlphaFullpath() and mask.read(tex.getAlphaFullpath()):
                w, h = mask.getXSize(), mask.getYSize()
                fn = lambda u, v, m=mask, w=w, h=h: m.getGray(min(int((u % 1.0) * w), w - 1),
                                                              min(int((1.0 - v % 1.0) * h), h - 1))
            else:
                full = PNMImage()
                if tex.hasFullpath() and full.read(tex.getFullpath()) and full.hasAlpha():
                    w, h = full.getXSize(), full.getYSize()
                    fn = lambda u, v, m=full, w=w, h=h: m.getAlpha(min(int((u % 1.0) * w), w - 1),
                                                                   min(int((1.0 - v % 1.0) * h), h - 1))
            cache[key] = fn
        return cache[key]

    def _image(self, tex):
        key = tex.getName()
        if key not in self.images:
            img = PNMImage()
            ok = False
            if tex.hasFullpath():
                ok = img.read(tex.getFullpath())
            if ok and (img.getXSize() > 512 or img.getYSize() > 512):
                small = PNMImage(max(1, img.getXSize() // 4), max(1, img.getYSize() // 4), img.getNumChannels())
                small.quickFilterFrom(img)
                img = small
            self.images[key] = img if ok else None
        return self.images[key]

    def wantsSurface(self, np, tex):
        if tex is None:
            return False
        name = np.getName()
        if SKIP_NAME.search(name) or WATER_NAMES.search(name) or WATER_NAMES.search(tex.getName()):
            return False
        bounds = np.getTightBounds()
        if not bounds:
            return False
        size = bounds[1] - bounds[0]
        if max(size[0], size[1]) > MAX_LAWN:
            return False      # a racetrack's infield: far more than MAX_TILES
        if GROUND_NAME.search(name) or GROUND_NAME.search(tex.getName()):
            return True
        # Many lawns carry no telling name (Daisy Gardens' are "o115_1").
        # Any big, level, solid sheet is a candidate; only its green
        # parts are planted, so paving and sand stay bare.
        if NOT_LAWN.search(name) or NOT_LAWN.search(tex.getName()):
            return False
        trans = np.getNetState().getAttrib(TransparencyAttrib)
        if trans is not None and trans.getMode() != TransparencyAttrib.MNone:
            return False
        return size[2] <= 1.5 and size[0] >= 30.0 and size[1] >= 30.0

    def _isPaintedShadow(self, np, geomIndex):
        """True for the dark see-through decals the artists laid on the
        ground under trees, kerbs and props."""
        node = np.node()
        state = np.getNetState().compose(node.getGeomState(geomIndex))
        attrib = state.getAttrib(TextureAttrib)
        tex = attrib.getTexture() if attrib else None
        if SHADOW_NAMES.search(np.getName()) or (tex is not None and SHADOW_NAMES.search(tex.getName())):
            return True
        trans = state.getAttrib(TransparencyAttrib)
        if trans is None or trans.getMode() == TransparencyAttrib.MNone:
            return False
        # See-through as a whole (a flat colour or scale with low alpha).
        color = state.getAttrib(ColorAttrib)
        if color is not None and color.getColorType() == ColorAttrib.TFlat and color.getColor()[3] < 0.95:
            return True
        scale = state.getAttrib(ColorScaleAttrib)
        if scale is not None and scale.getScale()[3] < 0.95:
            return True
        img = self._image(tex) if tex is not None else None
        vdata = node.getGeom(geomIndex).getVertexData()
        if img is None or not vdata.hasColumn('texcoord'):
            return False
        opacity = self._opacity(tex)
        # Sampled inside its polygons (corners are often see-through even
        # on solid art): a shadow is dark where it shows, and never fully
        # solid anywhere; a painted pad or road is solid and coloured.
        geom = node.getGeom(geomIndex).decompose()
        reader = GeomVertexReader(vdata, 'texcoord')
        vcolor = GeomVertexReader(vdata, 'color') if vdata.hasColumn('color') else None
        bright, weight, solid, count = 0.0, 0.0, 0.0, 0
        for prim in geom.getPrimitives():
            if prim.getNumVerticesPerPrimitive() != 3:
                continue
            total = prim.getNumPrimitives()
            for k in range(0, total, max(1, total // 16)):
                st = prim.getPrimitiveStart(k)
                u = v = tint = fade = 0.0
                for vi in range(3):
                    row = prim.getVertex(st + vi)
                    reader.setRow(row)
                    uv = reader.getData2()
                    u += uv[0] / 3.0
                    v += uv[1] / 3.0
                    if vcolor is not None:
                        vcolor.setRow(row)
                        c = vcolor.getData4()
                        tint += (c[0] + c[1] + c[2]) / 9.0
                        fade += c[3] / 3.0
                if vcolor is None:
                    tint = fade = 1.0
                x = min(max(int((u % 1.0) * img.getXSize()), 0), img.getXSize() - 1)
                y = min(max(int((1.0 - v % 1.0) * img.getYSize()), 0), img.getYSize() - 1)
                a = (opacity(u, v) if opacity is not None else 1.0) * fade
                bright += img.getBright(x, y) * tint * a
                weight += a
                solid = max(solid, a)
                count += 1
        if count == 0:
            return False
        return solid < 0.8 or (weight > 0 and bright / weight < 0.25)

    def _coverTest(self, ground, cell):
        """A generator, so the work can be spread over frames, that
        returns covered(x, y, z): is something lying over the lawn at
        this point?  Looks at every other visible, roughly level surface
        that overlaps the lawn."""
        render = self.base.render
        bounds = ground.getPythonTag('lawn-bounds') or ground.getTightBounds(render)
        if not bounds:
            return lambda x, y, z: False
        gmin, gmax = bounds
        buckets = {}
        for np in geomNodes(render):
            yield
            if np.isEmpty():
                continue
            if np == ground or np.hasNetTag('postfx-grass') or np.isHidden():
                continue
            if any(isinstance(a.node(), Character) for a in np.getAncestors()):
                continue          # toons and other things that move
            # A planted lawn's own extent was noted before its grass went
            # in; measuring it again would walk every tile.
            tb = np.getPythonTag('lawn-bounds') or np.getTightBounds(render)
            if not tb:
                continue
            mn, mx = tb
            if (mx[0] < gmin[0] or mn[0] > gmax[0] or mx[1] < gmin[1] or mn[1] > gmax[1]
                    or mx[2] < gmin[2] + COVER_MIN or mn[2] > gmax[2] + COVER_HEIGHT):
                continue
            mat = np.getMat(render)
            node = np.node()
            # Water covers whatever is under it, however deep.
            isWater = bool(np.hasNetTag('postfx-water') or WATER_NAMES.search(np.getName())
                           or WATER_NAMES.search(np.getParent().getName())
                           or any(WATER_NAMES.search(t.getName()) for t in np.findAllTextures()))
            for gi in range(node.getNumGeoms()):
                # Grass grows under a painted shadow, not around it.  But a
                # shadow lies on the lawn; a see-through sheet standing
                # clear of the ground is water or glass, and covers it.
                kind = 1 if isWater else (2 if self._isPaintedShadow(np, gi) else 0)
                geom = node.getGeom(gi).decompose()
                vdata = geom.getVertexData()
                vr = GeomVertexReader(vdata, 'vertex')
                pos = []
                while not vr.isAtEnd():
                    pos.append(mat.xformPoint(vr.getData3()))
                # Cut-out art (a road with soft painted edges on a square
                # sheet) only covers the lawn where it is actually opaque.
                img, uvs = None, None
                state = np.getNetState().compose(node.getGeomState(gi))
                trans = state.getAttrib(TransparencyAttrib)
                attrib = state.getAttrib(TextureAttrib)
                if (kind == 0 and trans is not None and trans.getMode() != TransparencyAttrib.MNone
                        and attrib is not None and attrib.getTexture() is not None
                        and vdata.hasColumn('texcoord')):
                    img = self._opacity(attrib.getTexture())
                    if img is not None:
                        tr = GeomVertexReader(vdata, 'texcoord')
                        uvs = []
                        while not tr.isAtEnd():
                            uvs.append(tr.getData2())
                for prim in geom.getPrimitives():
                    if prim.getNumVerticesPerPrimitive() != 3:
                        continue
                    for k in range(prim.getNumPrimitives()):
                        st = prim.getPrimitiveStart(k)
                        ia, ib, ic = prim.getVertex(st), prim.getVertex(st + 1), prim.getVertex(st + 2)
                        a, b, c = pos[ia], pos[ib], pos[ic]
                        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                        if abs(det) < 1e-6:
                            continue      # edge-on from above: a wall
                        zlo, zhi = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
                        if zhi < gmin[2] + COVER_MIN or (kind != 1 and zlo > gmax[2] + COVER_HEIGHT):
                            continue
                        n = (b - a).cross(c - a)
                        if not n.normalize() or abs(n[2]) < 0.3:
                            continue
                        tri = (a, b, c, det, img, (uvs[ia], uvs[ib], uvs[ic]) if img is not None else None, kind)
                        x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
                        y0, y1 = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
                        x0, x1 = max(x0, gmin[0]), min(x1, gmax[0])
                        y0, y1 = max(y0, gmin[1]), min(y1, gmax[1])
                        for gx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
                            for gy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                                buckets.setdefault((gx, gy), []).append(tri)

        def covered(x, y, z):
            for a, b, c, det, img, uv, kind in buckets.get((int(math.floor(x / cell)), int(math.floor(y / cell))), ()):
                w0 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / det
                w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / det
                w2 = 1.0 - w0 - w1
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                dz = w0 * a[2] + w1 * b[2] + w2 * c[2] - z
                if kind == 1:
                    if dz > COVER_MIN:
                        return True
                    continue
                if kind == 2 and dz < SHADOW_CLEARANCE:
                    continue
                if COVER_MIN < dz < COVER_HEIGHT:
                    # Only for things lying on the lawn; leaf canopies and
                    # the like overhead keep covering as a whole.
                    if img is not None and dz < 0.3:
                        u = uv[0][0] * w0 + uv[1][0] * w1 + uv[2][0] * w2
                        v = uv[0][1] * w0 + uv[1][1] * w1 + uv[2][1] * w2
                        if img(u, v) < 0.85:    # soft painted edges still show lawn
                            continue
                    return True
            return False
        return covered

    def addSurface(self, np, geomIndex, tex):
        """Queues one ground geom to have its green parts covered with
        grass.  The planting is spread over the following frames, nearest
        the camera first, so walking into a playground does not stall."""
        self.pending.append(self._plant(np, geomIndex, tex))
        if PLANT_BUDGET <= 0:
            self.finish()
        elif not self.base.taskMgr.hasTaskNamed('grass-plant'):
            self.base.taskMgr.add(self._plantTask, 'grass-plant', sort=48)

    def finish(self):
        """Plants everything still queued, now."""
        while self.pending:
            for _ in self.pending.pop(0):
                pass

    def _plantTask(self, task):
        end = time.time() + PLANT_BUDGET / 1000.0
        while self.pending:
            try:
                next(self.pending[0])
            except StopIteration:
                self.pending.pop(0)
            if time.time() >= end:
                break
        return task.cont if self.pending else task.done

    def _prune(self):
        """Stops counting the grass of places that have been unloaded."""
        render = self.base.render
        live = []
        for holder, placed in self.lawns:
            if holder.isEmpty() or not render.isAncestorOf(holder):
                self.tileCount -= placed[0]
            else:
                live.append((holder, placed))
        self.lawns = live

    def _plant(self, np, geomIndex, tex):
        self._prune()
        if self.tileCount >= MAX_TILES:
            return
        img = self._image(tex)
        if img is None:
            return
        yield
        if np.isEmpty():
            return
        render = self.base.render
        node = np.node()
        geom = node.getGeom(geomIndex).decompose()
        vdata = geom.getVertexData()
        if not vdata.hasColumn('texcoord'):
            return
        mat = np.getMat(render)
        vr = GeomVertexReader(vdata, 'vertex')
        tr = GeomVertexReader(vdata, 'texcoord')
        pos, uvs = [], []
        for _ in range(vdata.getNumRows()):
            pos.append(mat.xformPoint(vr.getData3()))
            uvs.append(tr.getData2())

        # Upward-facing triangles, bucketed on a grid for point lookups.
        tris = []
        buckets = {}
        cell = TILE_SIZES[0]
        for prim in geom.getPrimitives():
            if prim.getNumVerticesPerPrimitive() != 3:
                continue
            for k in range(prim.getNumPrimitives()):
                if k % 400 == 399:
                    yield
                s = prim.getPrimitiveStart(k)
                ia, ib, ic = prim.getVertex(s), prim.getVertex(s + 1), prim.getVertex(s + 2)
                a, b, c = pos[ia], pos[ib], pos[ic]
                n = (b - a).cross(c - a)
                if not n.normalize():
                    continue
                if n[2] < 0:
                    n = -n
                if n[2] < MIN_UP:
                    continue
                det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(det) < 1e-9:
                    continue
                ti = len(tris)
                tris.append((a, b, c, uvs[ia], uvs[ib], uvs[ic], n, det))
                x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
                y0, y1 = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
                for gx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
                    for gy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                        buckets.setdefault((gx, gy), []).append(ti)
        if not tris:
            return
        yield
        iw, ih = img.getXSize(), img.getYSize()
        covered = yield from self._coverTest(np, cell)
        bare = (0.0, 0.0, 0.0)
        yield
        if np.isEmpty() or not render.isAncestorOf(np):
            np.clearTag('postfx-grass-done')
            return

        # The grass lives under the ground it grows on, so it is hidden and
        # removed with it, but is laid out in world space.
        if not np.hasPythonTag('lawn-bounds'):
            np.setPythonTag('lawn-bounds', np.getTightBounds(render))
        holder = np.attachNewNode('postfx-grass')
        holder.setTransform(render, TransformState.makeIdentity())
        holder.setTag('postfx-grass', '1')
        holder.setShader(self.shader)
        holder.setShaderInput('grassParams', Vec4(FADE_NEAR, FADE_MID, FADE_FAR, 0))
        holder.setShaderInput('grassWind', Vec4(WIND_STRENGTH, KEEP_FRACTION, 0, 0))
        holder.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        holder.setTextureOff(1)
        holder.setLightOff(1)
        holder.setFogOff(1)
        holder.hide(self.hideFrom | BitMask32.bit(8))    # bit 8: ToonWater's depth camera

        def sample(x, y):
            """(z, colour, normal) of the ground at x, y, or None."""
            for ti in buckets.get((int(math.floor(x / cell)), int(math.floor(y / cell))), ()):
                a, b, c, ua, ub, uc, n, det = tris[ti]
                w0 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / det
                w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / det
                w2 = 1.0 - w0 - w1
                if w0 < -1e-4 or w1 < -1e-4 or w2 < -1e-4:
                    continue
                u = w0 * ua[0] + w1 * ub[0] + w2 * uc[0]
                v = w0 * ua[1] + w1 * ub[1] + w2 * uc[1]
                px = int((u % 1.0) * iw) % iw
                py = int((1.0 - (v % 1.0)) * ih) % ih
                z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                if covered(x, y, z):
                    return (z, bare, n)
                return (z, img.getXel(px, py), n)
            return None

        blocks = {}
        placed = [0]
        self.lawns.append((holder, placed))

        def block(x, y):
            """(near, far) parents for tiles around x, y."""
            key = (int(math.floor(x / BLOCK_SIZE)), int(math.floor(y / BLOCK_SIZE)))
            if key not in blocks:
                lod = LODNode('grass-block')
                lodNp = holder.attachNewNode(lod)
                lodNp.setPos((key[0] + 0.5) * BLOCK_SIZE, (key[1] + 0.5) * BLOCK_SIZE, 0)
                lod.addSwitch(LOD_SWITCH, 0)
                near = lodNp.attachNewNode('near')
                lod.addSwitch(VIEW_DISTANCE + BLOCK_SIZE, LOD_SWITCH)
                far = lodNp.attachNewNode('far')
                blocks[key] = (near, far, lodNp)
            return blocks[key]

        def place(x, y, size, mid):
            z, colour, n = mid
            near, far, _ = block(x, y)
            inst = near.attachNewNode('t')
            inst.setPos(render, x, y, z + 0.02)
            # Stand the tile on the slope, with a random quarter turn so
            # neighbouring tiles don't visibly repeat.
            if n[2] < 0.999:
                inst.lookAt(render, Point3(x, y, z) + n)
                inst.setP(inst, -90)
            inst.setH(inst, 90 * ((int(x * 7.3) + int(y * 3.1)) % 4))
            # Patches differ in length too, in broad drifts across the lawn.
            inst.setSz(0.95 + 0.3 * math.sin(x * 0.11 + y * 0.07) + 0.2 * math.sin(x * 0.31 - y * 0.23))
            inst.setColorScale(colour[0], colour[1], colour[2], 1.0)
            self.tiles[size].instanceTo(inst)
            farInst = far.attachNewNode('t')
            farInst.setTransform(inst.getTransform())
            farInst.setColorScale(colour[0], colour[1], colour[2], 1.0)
            self.farTiles[size].instanceTo(farInst)
            placed[0] += 1
            self.tileCount += 1

        def cover(x, y, size):
            """x, y is the centre of a square patch of this size."""
            if self.tileCount >= MAX_TILES:
                return
            mid = sample(x, y)
            h = size / 2.0
            corners = [sample(x - h, y - h), sample(x + h, y - h),
                       sample(x - h, y + h), sample(x + h, y + h)]
            pts = [mid] + corners
            green = [p is not None and isGreen(p[1]) for p in pts]
            if all(green):
                # Nothing narrow (a path, a kerb) crossing between the corners?
                for ex, ey in ((-h, 0), (h, 0), (0, -h), (0, h)):
                    p = sample(x + ex, y + ey)
                    if p is None or not isGreen(p[1]):
                        green[0] = False
                        break
            if all(green):
                # Flat enough for one tile?
                z, _, n = mid
                flat = True
                for (cx, cy), p in zip(((-h, -h), (h, -h), (-h, h), (h, h)), corners):
                    plane = z - (n[0] * cx + n[1] * cy) / n[2]
                    if abs(p[0] - plane) > MAX_BUMP:
                        flat = False
                        break
                if flat or size <= TILE_SIZES[-1]:
                    place(x, y, size, mid)
                    return
            elif not any(green):
                if size <= TILE_SIZES[1]:
                    return
            if size <= TILE_SIZES[-1]:
                if all(green):
                    place(x, y, size, mid)
                return
            q = size / 4.0
            for ox, oy in ((-q, -q), (q, -q), (-q, q), (q, q)):
                cover(x + ox, y + oy, size / 2.0)

        big = TILE_SIZES[0]
        eye = self.base.camera.getPos(render)
        order = sorted(buckets.keys(), key=lambda k: ((k[0] + 0.5) * big - eye[0]) ** 2
                                                     + ((k[1] + 0.5) * big - eye[1]) ** 2)
        for (gx, gy) in order:
            cover((gx + 0.5) * big, (gy + 0.5) * big, big)
            yield
            if holder.isEmpty() or not render.isAncestorOf(np):
                # The place was unloaded while its lawn was being planted.
                if not holder.isEmpty():
                    holder.removeNode()
                np.clearTag('postfx-grass-done')
                return

        if not blocks:
            holder.removeNode()
            return
        self._addMeadow(np)
        self.notify.info('%d grass tiles on %s' % (placed[0], np.getName()))
