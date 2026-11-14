"""
ToonWater: a cartoon water surface for the playground ponds, with fish.

The game's ponds are one flat, see-through sheet of a single colour.  This
keeps that sheet and its colour and draws on it:

  - drifting white ripple lines (the cell pattern cartoons use for water),
  - a band of white foam where the water meets the bank, the bridge and
    anything else standing in it, with slow rings moving out from the edge,
  - lighter, clearer water in the shallows and deeper colour in the middle.

"Where the water meets the bank" needs to know how deep the pond is at
every point.  That is measured once per pond by rendering the pond bed from
straight above into a small depth texture; nothing is re-measured per frame.

A few of the game's own fish swim under the surface.  They only use water
deep enough to cover them, found with the same one-off measurement done on
the CPU (rays dropped from the surface).

Used by PostFX, which calls consider() on scenery as it loads.
"""
import math
import random
import re

from panda3d.core import (GeomVertexReader, BitMask32, CollisionHandlerQueue, CollisionNode,
                          CollisionRay, CollisionTraverser, ColorAttrib,
                          ConfigVariableBool, ConfigVariableInt,
                          FrameBufferProperties, GeomNode, GraphicsOutput,
                          GraphicsPipe, NodePath, OrthographicLens, Point3,
                          SamplerState, Shader, Texture, TransparencyAttrib,
                          Vec3, Vec4, WindowProperties, Camera)
from direct.actor.Actor import Actor
from direct.directnotify import DirectNotifyGlobal

WATER_NAME = re.compile(r'water|pond|lake', re.I)
NOT_WATER = re.compile(r'shadow|decal|glow|light|ripple|splash', re.I)
MIN_POND_DEPTH = 0.3           # feet; anything shallower is paint on the ground
MAX_DEPTH = 8.0                # feet of pond measured below the surface
DEPTH_MAP_SIZE = 512
DEPTH_CAMERA_BITMASK = BitMask32.bit(8)

FISH_MODEL = 'phase_4/models/props/SZ_fish-mod'
FISH_SWIM = 'phase_4/models/props/SZ_fish-swim'
FISH_GRID = 2.0                # spacing of the depth soundings, feet
FISH_MIN_DEPTH = 0.9             # the playground ponds are only about a foot deep
FISH_SPEED = (1.2, 2.6)        # feet per second
FISH_TURN = 70.0               # degrees per second

VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;
varying vec2 vWorld;
varying vec2 vUv;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vWorld = (p3d_ModelMatrix * p3d_Vertex).xy;
    vUv = p3d_MultiTexCoord0;
}
"""

FRAG = """#version 120
uniform sampler2D p3d_Texture0;
uniform sampler2D depthMap;
uniform vec4 waterRect;        // min x, min y, 1 / width, 1 / height
uniform vec4 waterParams;      // depth range in feet, original opacity, unused, unused
uniform float osg_FrameTime;
varying vec2 vWorld;
varying vec2 vUv;

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// Distance to the nearest cell border of a drifting cell pattern.
float cells(vec2 p, float t) {
    vec2 i = floor(p), f = fract(p);
    float d1 = 8.0, d2 = 8.0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 g = vec2(float(x), float(y));
            vec2 o = hash2(i + g);
            o = 0.5 + 0.42 * sin(t + 6.2831 * o);
            float d = length(g + o - f);
            if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
        }
    }
    return d2 - d1;
}

void main() {
    float t = osg_FrameTime;
    vec3 base = texture2D(p3d_Texture0, vUv).rgb;

    vec2 duv = (vWorld - waterRect.xy) * waterRect.zw;
    float depth = texture2D(depthMap, duv).r * waterParams.x;
    if (duv.x < 0.0 || duv.x > 1.0 || duv.y < 0.0 || duv.y > 1.0) depth = waterParams.x;

    // Shallow water is paler and clearer, deep water richer.
    float deep = smoothstep(0.0, 3.5, depth);
    vec3 colour = mix(base * 1.12 + 0.10, base * 0.86, deep);
    float alpha = mix(0.50, min(waterParams.y + 0.12, 0.9), deep);

    // Ripple lines: two layers of cells sliding across each other.
    vec2 flow = vec2(0.035, 0.02) * t;
    vec2 wobble = 0.12 * vec2(sin(vWorld.y * 0.9 + t * 0.8), cos(vWorld.x * 0.8 + t * 0.7));
    float a = cells(vWorld * 0.26 + flow * 3.0 + wobble, t * 0.55);
    float b = cells(vWorld * 0.13 - flow * 2.0 + wobble.yx + 7.3, t * 0.4 + 2.0);
    // The lines break up and re-form instead of making a closed net.
    float gaps = smoothstep(-0.2, 0.5, sin(vWorld.x * 0.55 + t * 0.5) * sin(vWorld.y * 0.6 - t * 0.37)
                                      + 0.6 * sin((vWorld.x + vWorld.y) * 0.23 + t * 0.21));
    float lines = (1.0 - smoothstep(0.02, 0.05, a)) * 0.75 * gaps
                + (1.0 - smoothstep(0.012, 0.03, b)) * 0.35;
    // Fewer lines right at the bank, where the foam is.
    lines *= smoothstep(0.3, 1.2, depth);
    // A soft lighter patch inside some cells, like light on swell.
    float glint = smoothstep(0.45, 0.75, b) * 0.10;

    // Foam hugging everything the water touches, with a wavering edge...
    float wave = 0.16 * sin(t * 1.4 + vWorld.x * 0.7 + vWorld.y * 0.5)
               + 0.10 * sin(t * 2.3 - vWorld.x * 1.3 + vWorld.y * 1.9);
    float foam = 1.0 - smoothstep(0.30 + wave, 0.42 + wave, depth);
    // ...and rings travelling slowly out from it, fading as they go.
    float ring = fract(depth * 0.75 - t * 0.22 + 0.05 * sin(vWorld.x * 1.7 + vWorld.y * 1.3));
    float rings = (1.0 - smoothstep(0.0, 0.05, abs(ring - 0.5))) * (1.0 - smoothstep(0.5, 1.5, depth));

    float white = clamp(max(max(lines, foam), rings * 0.8), 0.0, 1.0);
    colour = mix(colour + glint, vec3(1.0), white);
    alpha = mix(alpha, 0.95, white);
    gl_FragColor = vec4(colour, alpha);
}
"""


class ToonWater:
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonWater')

    def __init__(self, base, hideFrom):
        self.base = base
        self.hideFrom = hideFrom       # camera bits that must not see the water
        self.wantFish = ConfigVariableBool('postfx-fish', True).value
        self.fishCount = ConfigVariableInt('postfx-fish-count', 7).value
        self.shader = Shader.make(Shader.SL_GLSL, VERT, FRAG)
        self.schools = []              # (water NodePath, [fish dicts])
        self.rng = random.Random()
        self.base.taskMgr.add(self._swim, 'toonwater-swim')

    def destroy(self):
        self.base.taskMgr.remove('toonwater-swim')
        for water, fishes in self.schools:
            for fish in fishes:
                fish['actor'].cleanup()
                fish['actor'].removeNode()
        self.schools = []

    # ------------------------------------------------------------------
    # Finding water

    def isWater(self, np):
        """A level, see-through sheet with some size to it, that is not a
        shadow, and that actually has a pond bed some way beneath it.
        (Shadows and other markings painted on the ground are level,
        see-through sheets too; they lie flat on the lawn.)"""
        if np.hasNetTag('postfx-water') or np.hasNetTag('postfx-grass') or np.hasTag('postfx-not-water'):
            return False
        if NOT_WATER.search(np.getName()) or any(NOT_WATER.search(t.getName()) for t in np.findAllTextures()):
            return False
        bounds = np.getTightBounds(self.base.render)
        if not bounds:
            return False
        mn, mx = bounds
        size = mx - mn
        if size[2] > 0.15 or size[0] < 12.0 or size[1] < 12.0:
            return False
        state = np.getNetState().compose(np.node().getGeomState(0))
        transparency = state.getAttrib(TransparencyAttrib)
        named = bool(WATER_NAME.search(np.getName()) or
                     any(WATER_NAME.search(t.getName()) for t in np.findAllTextures()))
        if transparency is None or transparency.getMode() == TransparencyAttrib.MNone:
            # Solid water (a harbour painted as one opaque sheet) has to
            # say so in its own or its texture's name.
            if not named:
                return False
        elif not named:
            colour = state.getAttrib(ColorAttrib)
            if not (colour is not None and colour.getColorType() == ColorAttrib.TFlat
                    and colour.getColor()[3] < 0.95):
                return False
        # The underside of the water, drawn for swimmers looking up, faces
        # down and is never seen from the shore.
        if not self._facesUp(np):
            return False
        # The second of two stacked sheets: one surface is enough.
        for other in self.base.render.findAllMatches('**/=postfx-water'):
            ob = other.getTightBounds(self.base.render)
            if (ob and abs(ob[1][2] - mx[2]) < 0.05 and ob[0][0] < mx[0] and ob[1][0] > mn[0]
                    and ob[0][1] < mx[1] and ob[1][1] > mn[1]):
                np.setTag('postfx-not-water', '1')
                np.hide()
                return False
        # Is there water under it?  Sound the depth on a coarse grid.
        depths = self._soundings(np, mn, mx, mx[2], grid=4.0)
        wet = sum(1 for d in depths.values() if d > MIN_POND_DEPTH)
        if wet < 6 or wet < 0.2 * max(len(depths), 1):
            np.setTag('postfx-not-water', '1')
            return False
        return True

    def consider(self, np):
        """Called for each piece of scenery; dresses it if it is water."""
        if not self.isWater(np):
            return False
        self.apply(np)
        return True

    # ------------------------------------------------------------------

    @staticmethod
    def _facesUp(np):
        geom = np.node().getGeom(0).decompose()
        reader = GeomVertexReader(geom.getVertexData(), 'vertex')
        mat = np.getNetTransform().getMat()
        for prim in geom.getPrimitives():
            if prim.getNumPrimitives() == 0 or prim.getNumVerticesPerPrimitive() != 3:
                continue
            pts = []
            for vi in range(prim.getPrimitiveStart(0), prim.getPrimitiveEnd(0)):
                reader.setRow(prim.getVertex(vi))
                pts.append(mat.xformPoint(reader.getData3()))
            return (pts[1] - pts[0]).cross(pts[2] - pts[0])[2] > 0
        return True

    def apply(self, np):
        base = self.base
        render = base.render
        np.setTag('postfx-water', '1')
        mn, mx = np.getTightBounds(render)
        level = mx[2]
        state = np.getNetState().compose(np.node().getGeomState(0))
        colour = state.getAttrib(ColorAttrib)
        opacity = 0.7
        if colour is not None and colour.getColorType() == ColorAttrib.TFlat:
            opacity = colour.getColor()[3]
        transparency = state.getAttrib(TransparencyAttrib)
        if transparency is None or transparency.getMode() == TransparencyAttrib.MNone:
            # Water painted as a solid sheet: keep the deeps nearly solid,
            # but let the shallows show the bed like the ponds do.
            opacity = 0.85
            np.setTransparency(TransparencyAttrib.MAlpha)

        depthMap = self._measureDepth(np, mn, mx, level)
        np.setShader(self.shader, 20)
        np.setShaderInput('depthMap', depthMap)
        np.setShaderInput('waterRect', Vec4(mn[0], mn[1], 1.0 / (mx[0] - mn[0]), 1.0 / (mx[1] - mn[1])))
        np.setShaderInput('waterParams', Vec4(MAX_DEPTH, opacity, 0, 0))
        np.hide(self.hideFrom | DEPTH_CAMERA_BITMASK)
        self.notify.info('water: %s, %.0f x %.0f ft' % (np.getName() or '(unnamed)',
                                                        mx[0] - mn[0], mx[1] - mn[1]))
        if self.wantFish and self.fishCount > 0:
            self._addFish(np, mn, mx, level)

    def _measureDepth(self, np, mn, mx, level):
        """Renders the pond bed from above, once, into a depth texture:
        0 at the surface, 1 at MAX_DEPTH feet down."""
        base = self.base
        tex = Texture('toonwater-depth')
        tex.setWrapU(SamplerState.WM_clamp)
        tex.setWrapV(SamplerState.WM_clamp)
        tex.setMinfilter(SamplerState.FT_linear)
        tex.setMagfilter(SamplerState.FT_linear)
        fbp = FrameBufferProperties()
        fbp.setRgbColor(True)
        fbp.setDepthBits(24)
        buf = base.graphicsEngine.makeOutput(
            base.pipe, 'toonwater-depth', -200, fbp,
            WindowProperties.size(DEPTH_MAP_SIZE, DEPTH_MAP_SIZE),
            GraphicsPipe.BFRefuseWindow, base.win.getGsg(), base.win)
        if buf is None:
            self.notify.warning('could not measure pond depth; no shore foam')
            return tex
        buf.addRenderTexture(tex, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepth)
        buf.setClearDepth(1.0)
        buf.setOneShot(True)           # render a single frame, keep the texture
        lens = OrthographicLens()
        lens.setFilmSize(mx[0] - mn[0], mx[1] - mn[1])
        lens.setNearFar(0.0, MAX_DEPTH)
        cam = Camera('toonwater-depth-cam', lens)
        cam.setCameraMask(DEPTH_CAMERA_BITMASK)
        camNp = base.render.attachNewNode(cam)
        # Straight down, with the top of the picture towards +y so the
        # texture lines up with world x and y.
        camNp.setPosHpr((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, level, 0, -90, 0)
        buf.makeDisplayRegion().setCamera(camNp)
        base.taskMgr.doMethodLater(1.0, lambda task: camNp.removeNode(), 'toonwater-depth-done')
        return tex

    # ------------------------------------------------------------------
    # Fish

    def _soundings(self, np, mn, mx, level, grid=FISH_GRID):
        """{(i, j): depth} on a FISH_GRID grid: water depth found by dropping
        a ray from high above onto the scenery.  The first thing it meets
        is what counts, so an island or a bridge reads as no water."""
        render = self.base.render
        rays = CollisionNode('toonwater-rays')
        rays.setFromCollideMask(GeomNode.getDefaultCollideMask())
        rays.setIntoCollideMask(BitMask32.allOff())
        index = {}
        nx = int((mx[0] - mn[0]) / grid)
        ny = int((mx[1] - mn[1]) / grid)
        for i in range(nx + 1):
            for j in range(ny + 1):
                index[rays.addSolid(CollisionRay(mn[0] + i * grid, mn[1] + j * grid,
                                                 level + 40.0, 0, 0, -1))] = (i, j)
        raysNp = render.attachNewNode(rays)
        queue = CollisionHandlerQueue()
        trav = CollisionTraverser('toonwater')
        trav.addCollider(raysNp, queue)
        trav.traverse(render)
        depths = {}
        for k in range(queue.getNumEntries()):
            entry = queue.getEntry(k)
            into = entry.getIntoNodePath()
            if into == np or into.hasNetTag('postfx-water') or into.hasNetTag('postfx-grass'):
                continue
            # Which ray?  Solids are in the order they were added.
            origin = entry.getFrom().getOrigin()
            key = (int(round((origin[0] - mn[0]) / grid)), int(round((origin[1] - mn[1]) / grid)))
            d = level - entry.getSurfacePoint(render)[2]
            # Water is often two sheets at the same height, scrolling over
            # each other; the second one is not the bed.
            if abs(d) < 0.03 and (WATER_NAME.search(into.getName()) or
                                  any(WATER_NAME.search(t.getName()) for t in into.findAllTextures())):
                continue
            if key not in depths or d < depths[key]:
                depths[key] = d
        raysNp.removeNode()
        return depths

    def _addFish(self, np, mn, mx, level):
        depths = self._soundings(np, mn, mx, level)
        # Swimmable cells: deep enough, and so are all their neighbours, so
        # a fish never noses into the bank.
        deep = set()
        for (i, j), d in depths.items():
            if d < FISH_MIN_DEPTH:
                continue
            if all(depths.get((i + a, j + b), 0) >= FISH_MIN_DEPTH * 0.7
                   for a in (-1, 0, 1) for b in (-1, 0, 1)):
                deep.add((i, j))
        if len(deep) < 4:
            self.notify.info('pond too shallow for fish')
            return
        cells = sorted(deep)
        try:
            proto = Actor(FISH_MODEL, {'swim': FISH_SWIM})
        except Exception:
            self.notify.warning('fish model missing; no fish')
            return
        fishes = []
        holder = np.getParent().attachNewNode('toonwater-fish')
        holder.setTag('postfx-water', '1')
        holder.hide(DEPTH_CAMERA_BITMASK)
        rng = self.rng
        for k in range(self.fishCount):
            actor = proto if k == 0 else Actor(FISH_MODEL, {'swim': FISH_SWIM})
            actor.reparentTo(holder)
            scale = rng.uniform(0.55, 0.9)
            actor.setScale(scale)
            actor.setPlayRate(rng.uniform(0.8, 1.4), 'swim')
            actor.loop('swim')
            actor.setTime('swim', rng.uniform(0, 1)) if hasattr(actor, 'setTime') else None
            cell = rng.choice(cells)
            d = depths[cell]
            fish = {'actor': actor, 'cell': cell, 'target': None,
                    'speed': rng.uniform(*FISH_SPEED), 'heading': rng.uniform(0, 360),
                    'depth': rng.uniform(0.4, max(0.45, min(d - 0.3, 1.5))), 'pause': 0.0}
            actor.setPos(self.base.render, mn[0] + cell[0] * FISH_GRID, mn[1] + cell[1] * FISH_GRID,
                         level - fish['depth'])
            fishes.append(fish)
        self.schools.append({'water': np, 'holder': holder, 'fishes': fishes, 'cells': cells,
                             'deep': deep, 'depths': depths, 'origin': (mn[0], mn[1]), 'level': level})
        self.notify.info('%d fish in %d swimmable spots' % (len(fishes), len(cells)))

    def _clearPath(self, school, a, b):
        """Is the straight line between two cells over deep water all the way?"""
        steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for s in range(1, steps):
            f = s / float(steps)
            if (int(round(a[0] + (b[0] - a[0]) * f)), int(round(a[1] + (b[1] - a[1]) * f))) not in school['deep']:
                return False
        return True

    def _swim(self, task):
        dt = min(globalClock.getDt(), 0.1)
        render = self.base.render
        rng = self.rng
        for school in list(self.schools):
            if school['water'].isEmpty() or school['holder'].isEmpty():
                # The playground was unloaded.
                for fish in school['fishes']:
                    fish['actor'].cleanup()
                    if not fish['actor'].isEmpty():
                        fish['actor'].removeNode()
                self.schools.remove(school)
                continue
            ox, oy = school['origin']
            for fish in school['fishes']:
                actor = fish['actor']
                if fish['pause'] > 0:
                    fish['pause'] -= dt
                    continue
                if fish['target'] is None:
                    for _ in range(8):
                        cand = rng.choice(school['cells'])
                        if cand != fish['cell'] and self._clearPath(school, fish['cell'], cand):
                            fish['target'] = cand
                            d = school['depths'][cand]
                            fish['targetDepth'] = rng.uniform(0.4, max(0.45, min(d - 0.3, 1.5)))
                            break
                    else:
                        fish['pause'] = 0.5
                        continue
                tx = ox + fish['target'][0] * FISH_GRID
                ty = oy + fish['target'][1] * FISH_GRID
                pos = actor.getPos(render)
                dx, dy = tx - pos[0], ty - pos[1]
                dist = math.hypot(dx, dy)
                if dist < 1.0:
                    fish['cell'] = fish['target']
                    fish['target'] = None
                    if rng.random() < 0.3:
                        fish['pause'] = rng.uniform(0.5, 2.5)     # hang in the water a while
                    continue
                want = math.degrees(math.atan2(-dx, dy))
                turn = (want - fish['heading'] + 180.0) % 360.0 - 180.0
                step = max(-FISH_TURN * dt, min(FISH_TURN * dt, turn))
                fish['heading'] += step
                # Slow down for sharp turns so the fish curves, not skids.
                speed = fish['speed'] * (1.0 - 0.6 * min(abs(turn), 90.0) / 90.0)
                h = math.radians(fish['heading'])
                z = school['level'] - fish['depth']
                fish['depth'] += (fish['targetDepth'] - fish['depth']) * min(1.0, dt * 0.4)
                actor.setPos(render, pos[0] - math.sin(h) * speed * dt, pos[1] + math.cos(h) * speed * dt, z)
                actor.setH(render, fish['heading'] + FISH_HEADING_OFFSET)
        return task.cont


# The fish model's nose points along its -x axis.
FISH_HEADING_OFFSET = -90.0
