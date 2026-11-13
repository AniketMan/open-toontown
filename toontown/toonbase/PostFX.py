"""
PostFX: an optional screen-space post-processing stack for the client.

Stages (all GLSL 1.20, so they run on the legacy OpenGL 2.1 context that
Panda3D gets on macOS as well as on newer drivers):

  1. scene -> colour + depth textures
  2. SSAO   (half res, depth-only, then a depth-aware blur)
  3. sun shadows: the scene's depth is rendered from the sun into a shadow
     map; the composite pass reconstructs each pixel's position from the
     depth buffer and tests it against that map.  Because this is done in
     screen space, no scene material needs a shader of its own.
  4. materials: the scene is drawn once more with a shader that projects
     each surface's real-world normal map (see MaterialLibrary) onto it;
     the composite uses the result to shade surface relief.
  5. composite: colour * AO * sun * relief, gentle grade and vignette
  6. FXAA   -> window

Only the 3D scene (base.cam) is filtered; render2d/aspect2d GUI is untouched.

Config:
  want-postfx    #t/#f   enable at startup (default #t)
  postfx-hotkey  f6      key that toggles the effect at runtime
  postfx-compare-hotkey  f5   saves off/on screenshots of the current view
  postfx-ao / postfx-fxaa / postfx-grade / postfx-shadows / postfx-materials   #t/#f per stage
  postfx-grass / postfx-smooth-characters   #t/#f
  postfx-shadow-size   4096   shadow map resolution
"""
from panda3d.core import (ConfigVariableBool, ConfigVariableString, Shader,
                          ConfigVariableInt, loadPrcFileData,
                          Texture, Vec2, Vec3, Vec4, Point3, SamplerState,
                          FrameBufferProperties, WindowProperties,
                          GraphicsPipe, GraphicsOutput, Camera,
                          OrthographicLens, RenderState, ColorWriteAttrib,
                          AlphaTestAttrib, TransparencyAttrib, RenderAttrib,
                          DepthWriteAttrib, NodePath, LMatrix4,
                          ShaderAttrib, TextureAttrib, GeomNode, Character,
                          GeomVertexReader, GeomVertexWriter, GeomVertexData,
                          InternalName, Geom, BitMask32)
import re

BLOB_SHADOW = re.compile(r'drop.?shadow', re.I)
MATERIAL_CAMERA_BITMASK = BitMask32.bit(7)
from otp.otpbase import OTPRender
from toontown.toonbase import MaterialLibrary
from toontown.toonbase.GrassField import GrassField
from toontown.toonbase.ToonWater import ToonWater
from direct.directnotify import DirectNotifyGlobal
from direct.filter.FilterManager import FilterManager
from direct.showbase.DirectObject import DirectObject

VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
attribute vec4 p3d_Vertex;
varying vec2 uv;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_Vertex.xz * 0.5 + 0.5;
}
"""

# Shared helpers: linear depth and view-space position from the depth buffer.
DEPTH_LIB = """
uniform sampler2D depthTex;
uniform vec4 lensInfo;   // near, far, tan(hfov/2), tan(vfov/2)
uniform vec2 pixel;      // 1 / full-res size
float linearDepth(vec2 c) {
    float d = texture2D(depthTex, c).r * 2.0 - 1.0;
    return 2.0 * lensInfo.x * lensInfo.y /
           (lensInfo.y + lensInfo.x - d * (lensInfo.y - lensInfo.x));
}
vec3 viewPos(vec2 c) {
    // Snap to the centre of the depth texel actually sampled.  Pairing a
    // texel's depth with a slightly different screen position bends flat
    // surfaces into a sawtooth, which shows up as stripes in the AO.
    c = (floor(c / pixel) + 0.5) * pixel;
    float z = linearDepth(c);
    return vec3((c * 2.0 - 1.0) * lensInfo.zw * z, z);
}
"""

SSAO_FRAG = """#version 120
varying vec2 uv;
uniform vec3 aoParams;   // radius (world units), intensity, max distance
""" + DEPTH_LIB + """
float ign(vec2 p) {      // interleaved gradient noise
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}
void main() {
    // Half-res fragment centres sit exactly on full-res texel corners;
    // nudge off the corner so texel snapping is stable.
    vec2 uv = uv + pixel * 0.25;
    vec3 P = viewPos(uv);
    if (P.z > aoParams.z) { gl_FragColor = vec4(1.0); return; }

    // Normal from the nearer of each pair of depth neighbours, so that
    // silhouettes don't produce bogus normals.
    vec3 r = viewPos(uv + vec2(pixel.x, 0.0)) - P;
    vec3 l = P - viewPos(uv - vec2(pixel.x, 0.0));
    vec3 u = viewPos(uv + vec2(0.0, pixel.y)) - P;
    vec3 d = P - viewPos(uv - vec2(0.0, pixel.y));
    vec3 dx = abs(r.z) < abs(l.z) ? r : l;
    vec3 dy = abs(u.z) < abs(d.z) ? u : d;
    vec3 N = normalize(cross(dy, dx));

    float radius = aoParams.x;
    // world radius -> uv radius at this depth
    vec2 rUV = radius / (P.z * lensInfo.zw) * 0.5;
    rUV = min(rUV, vec2(0.08));
    float rot = ign(gl_FragCoord.xy) * 6.2831853;
    float occ = 0.0;
    const int N_SAMPLES = 12;
    for (int i = 0; i < N_SAMPLES; i++) {
        float t = (float(i) + 0.5) / float(N_SAMPLES);
        float a = rot + t * 6.2831853 * 2.618;
        vec2 o = vec2(cos(a), sin(a)) * sqrt(t) * rUV;
        vec3 V = viewPos(uv + o) - P;
        float vv = dot(V, V);
        // Cosine of the angle above the surface: bounded per sample, so
        // close-ups can't over-darken the way a 1/distance weight does.
        float c = dot(V, N) / (sqrt(vv) + 0.0001) - (0.10 + 0.002 * P.z);
        float falloff = max(1.0 - vv / (radius * radius), 0.0);
        occ += max(c, 0.0) * falloff;
    }
    occ = occ / float(N_SAMPLES);
    float fade = 1.0 - smoothstep(aoParams.z * 0.6, aoParams.z, P.z);
    gl_FragColor = vec4(clamp(1.0 - occ * aoParams.y * fade, 0.0, 1.0));
}
"""

# Depth-aware separable blur for the AO buffer.
AOBLUR_FRAG = """#version 120
varying vec2 uv;
uniform sampler2D src;
uniform vec2 dir;        // one texel step along the blur axis
""" + DEPTH_LIB + """
void main() {
    float z = linearDepth(uv);
    float sum = texture2D(src, uv).r * 0.3;
    float wsum = 0.3;
    for (int i = 1; i <= 3; i++) {
        float w0 = 0.35 - 0.08 * float(i);
        for (int s = -1; s <= 1; s += 2) {
            vec2 c = uv + dir * float(i * s);
            float w = w0 * max(0.0, 1.0 - abs(linearDepth(c) - z) / (0.05 * z + 0.05));
            sum += texture2D(src, c).r * w;
            wsum += w;
        }
    }
    gl_FragColor = vec4(sum / wsum);
}
"""

# Material pass.  The scene is drawn a second time with this shader, which
# writes, per pixel, how far the surface tilts away from its flat geometric
# normal.  Two sources are combined:
#   grain - a real-world normal map for the surface's material, from
#           MaterialLibrary, projected along the three world axes
#           (triplanar) so it tiles at a fixed real-world size;
#   shape - the layout painted into the surface's own texture (tile edges,
#           grout, plank gaps), read as a height field in the model's UVs.
# Grain is suppressed inside the gaps that the shape finds.
MATERIAL_VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;
attribute vec4 p3d_Vertex;
attribute vec3 p3d_Normal;
attribute vec2 p3d_MultiTexCoord0;
varying vec3 vView;
varying vec3 vWorld;
varying vec3 vNormal;
varying vec2 vUv;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vView = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
    vWorld = (p3d_ModelMatrix * p3d_Vertex).xyz;
    vNormal = (p3d_ModelMatrix * vec4(p3d_Normal, 0.0)).xyz;
    vUv = p3d_MultiTexCoord0;
}
"""

MATERIAL_FRAG = """#version 120
uniform sampler2D p3d_Texture0;
uniform sampler2D matNormal;
uniform vec4 matParams;     // repeats per world unit, grain strength, 1/texture width, 1/texture height
uniform vec4 shapeParams;   // shape strength, gap sensitivity, unused, unused
uniform vec4 geomFlags;     // 1 if the geometry carries smooth vertex normals
uniform vec3 lightDirWorld; // light used for relief
uniform mat4 worldToView;
varying vec3 vView;
varying vec3 vWorld;
varying vec3 vNormal;
varying vec2 vUv;
void main() {
    // Cut-out art (leaves, fences) only counts where it is opaque.
    if (texture2D(p3d_Texture0, vUv).a < 0.5) discard;
    // Surfaces with nothing to add still have to hide what is behind them.
    if (matParams.y <= 0.0 && geomFlags.x < 0.5) { gl_FragColor = vec4(0.5, 0.5, 0.5, 0.0); return; }
    // Flat world-space normal of this triangle, facing the camera.
    vec3 N = normalize(cross(dFdx(vWorld), dFdy(vWorld)));
    vec3 Nv = normalize(cross(dFdx(vView), dFdy(vView)));
    if (dot(Nv, vView) > 0.0) N = -N;
    // Smooth shading: the triangle's flat normal is replaced by the
    // normal interpolated across it, which rounds off low-polygon shapes.
    vec3 smoothTilt = vec3(0.0);
    if (geomFlags.x > 0.5 && dot(vNormal, vNormal) > 0.0001) {
        vec3 S = normalize(vNormal);
        if (dot(S, N) < 0.0) S = -S;
        smoothTilt = S - N;
    }
    vec3 detail = vec3(0.0);
    if (matParams.y > 0.0) {
        vec3 w = pow(abs(N), vec3(4.0));
        w /= (w.x + w.y + w.z);
        vec3 q = vWorld * matParams.x;
        // Walls use (horizontal, up) for both facings, so a map's vertical
        // direction (wood grain, bark) stays vertical on every wall.
        vec3 tx = texture2D(matNormal, q.yz).xyz * 2.0 - 1.0;
        vec3 ty = texture2D(matNormal, q.xz).xyz * 2.0 - 1.0;
        vec3 tz = texture2D(matNormal, q.xy).xyz * 2.0 - 1.0;
        tx.xy *= matParams.y; ty.xy *= matParams.y; tz.xy *= matParams.y;
        // "Whiteout" blend of each projection with the surface normal.
        tx = vec3(tx.xy + N.yz, abs(tx.z) * N.x);
        ty = vec3(ty.xy + N.xz, abs(ty.z) * N.y);
        tz = vec3(tz.xy + N.xy, abs(tz.z) * N.z);
        vec3 grain = normalize(tx.zxy * w.x + ty.xzy * w.y + tz.xyz * w.z) - N;

        // Shape painted into the texture itself (tile edges, grout lines, plank
        // gaps): treat its brightness as height, darker being deeper, and tilt
        // the surface down the slope.  This lives in the model's own UVs, so
        // the gaps land exactly where the artwork draws them.
        vec2 t = matParams.zw * 1.5;
        float hL = dot(texture2D(p3d_Texture0, vUv - vec2(t.x, 0.0), 1.0).rgb, vec3(0.299, 0.587, 0.114));
        float hR = dot(texture2D(p3d_Texture0, vUv + vec2(t.x, 0.0), 1.0).rgb, vec3(0.299, 0.587, 0.114));
        float hD = dot(texture2D(p3d_Texture0, vUv - vec2(0.0, t.y), 1.0).rgb, vec3(0.299, 0.587, 0.114));
        float hU = dot(texture2D(p3d_Texture0, vUv + vec2(0.0, t.y), 1.0).rgb, vec3(0.299, 0.587, 0.114));
        float h  = dot(texture2D(p3d_Texture0, vUv, 1.0).rgb, vec3(0.299, 0.587, 0.114));
        float hWide = dot(texture2D(p3d_Texture0, vUv, 5.0).rgb, vec3(0.299, 0.587, 0.114));
        // Tangent frame from screen-space derivatives (the models carry none).
        vec3 dp1 = dFdx(vWorld), dp2 = dFdy(vWorld);
        vec2 du1 = dFdx(vUv), du2 = dFdy(vUv);
        if (dot(Nv, vView) > 0.0) { dp1 = -dp1; du1 = -du1; }
        vec3 dp2perp = cross(dp2, N), dp1perp = cross(N, dp1);
        vec3 T = dp2perp * du1.x + dp1perp * du2.x;
        vec3 B = dp2perp * du1.y + dp1perp * du2.y;
        float scale = inversesqrt(max(max(dot(T, T), dot(B, B)), 1e-12));
        vec3 slope = ((hR - hL) * T + (hU - hD) * B) * scale;
        vec3 shape = normalize(N - slope * shapeParams.x) - N;
        // A gap is where the texture is darker than its surroundings; the
        // material's grain belongs on the raised faces, not down in the gaps.
        float gap = clamp((hWide - h) * shapeParams.y, 0.0, 1.0);
        detail = grain * (1.0 - gap) + shape;
    }
    vec3 bumped = normalize(N + smoothTilt + detail);
    // How much the material detail alone turns the surface toward the
    // light.  Kept apart from the smoothing, which must not be "embossed".
    float relief = dot(normalize(N + smoothTilt + detail) - normalize(N + smoothTilt), lightDirWorld);
    // Tilt relative to the flat normal, in the composite's view space.
    vec3 d = (worldToView * vec4(bumped - N, 0.0)).xyz;
    // rgb: tilt of the shading normal.  alpha: relief, with 0 meaning "no data".
    gl_FragColor = vec4(clamp(d * 0.5 + 0.5, 0.0, 1.0),
                        0.1 + 0.9 * clamp(relief * 0.5 + 0.5, 0.0, 1.0));
}
"""

COMPOSITE_FRAG = """#version 120
varying vec2 uv;
uniform sampler2D sceneTex;
uniform sampler2D aoTex;
uniform sampler2D shadowTex;
uniform sampler2D materialTex;
uniform vec3 lightDirView;  // light used for surface relief (the sun outdoors)
uniform float reliefStrength;
uniform vec4 mix4;          // ao on, grade on, debug view (1 ao, 2 sun), unused
uniform mat4 shadowMat;     // Panda camera space -> shadow clip space
uniform vec3 sunDirView;    // direction to the sun in (right, up, depth) space
uniform vec4 shadowParams;  // strength, shadow texel (uv), max distance, form strength
""" + DEPTH_LIB + """
float ign(vec2 p) {
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}
// Returns the surface normal; ndl receives how directly it faces the sun.
// Normals are rebuilt from depth, which is unreliable on the pixel row
// where two surfaces meet (e.g. the rim of a decal lying on the ground),
// so the facing term takes the most sun-facing of the four candidate
// normals: a real unlit face agrees on all four, an edge does not.
vec3 viewNormal(vec3 P, out float ndl) {
    vec3 r = viewPos(uv + vec2(pixel.x, 0.0)) - P;
    vec3 l = P - viewPos(uv - vec2(pixel.x, 0.0));
    vec3 u = viewPos(uv + vec2(0.0, pixel.y)) - P;
    vec3 d = P - viewPos(uv - vec2(0.0, pixel.y));
    ndl = max(max(dot(normalize(cross(u, r)), sunDirView),
                  dot(normalize(cross(d, l)), sunDirView)),
              max(dot(normalize(cross(u, l)), sunDirView),
                  dot(normalize(cross(d, r)), sunDirView)));
    vec3 dx = abs(r.z) < abs(l.z) ? r : l;
    vec3 dy = abs(u.z) < abs(d.z) ? u : d;
    return normalize(cross(dy, dx));
}
// 1 = fully lit by the sun, 0 = fully shadowed.
float sunLight(vec3 P, vec3 N, float ndl) {
    // Surfaces turned away from the sun get soft form shading.
    // Everything fades out with distance so far scenery and painted
    // backdrops keep their original look.
    float far = smoothstep(shadowParams.z * 0.75, shadowParams.z, P.z);
    float form = mix(1.0, smoothstep(-0.10, 0.30, ndl), shadowParams.w * (1.0 - far));
    // Push the lookup off the surface along its normal, more at grazing
    // sun angles and with distance, to avoid self-shadowing.
    vec3 Q = P + N * (0.05 + 0.25 * (1.0 - clamp(ndl, 0.0, 1.0)) + 0.003 * P.z);
    vec4 clip = shadowMat * vec4(Q.x, Q.z, Q.y, 1.0);
    vec3 sc = clip.xyz / clip.w * 0.5 + 0.5;
    if (sc.x < 0.0 || sc.x > 1.0 || sc.y < 0.0 || sc.y > 1.0 || sc.z > 1.0)
        return form;
    float a = ign(gl_FragCoord.xy) * 6.2831853;
    float lit = 0.0;
    const int TAPS = 12;
    for (int i = 0; i < TAPS; i++) {
        float t = (float(i) + 0.5) / float(TAPS);
        float b = a + t * 6.2831853 * 2.618;
        vec2 o = vec2(cos(b), sin(b)) * sqrt(t) * shadowParams.y * 2.5;
        lit += step(sc.z - 0.0006, texture2D(shadowTex, sc.xy + o).r);
    }
    lit /= float(TAPS);
    // Fade out at the edge of the shadow map too.
    vec2 e = abs(sc.xy - 0.5) * 2.0;
    float fade = max(smoothstep(0.85, 1.0, max(e.x, e.y)), far);
    return min(form, mix(lit, 1.0, fade));
}
void main() {
    vec3 c = texture2D(sceneTex, uv).rgb;
    float ao = mix(1.0, texture2D(aoTex, uv).r, mix4.x);
    float sun = 1.0;
    vec3 P = viewPos(uv);
    vec4 mat = texture2D(materialTex, uv);
    if (shadowParams.x > 0.0 && P.z < lensInfo.y * 0.97) {
        float ndl;
        vec3 N = viewNormal(P, ndl);
        // The material pass knows the smooth / normal-mapped normal.
        if (mat.a > 0.05) ndl += dot(mat.rgb * 2.0 - 1.0, sunDirView);
        sun = sunLight(P, N, ndl);
    }
    // Surface relief from the material pass: where the normal map tilts
    // the surface toward the light it brightens, away it darkens.
    float relief = 0.0;
    if (mat.a > 0.05) {
        relief = ((mat.a - 0.1) / 0.9 * 2.0 - 1.0) * reliefStrength;
        relief *= 1.0 - smoothstep(60.0, 140.0, P.z);     // too fine to see far away
        relief *= 0.45 + 0.55 * sun;                      // weaker in shadow
    }
    // Shade is tinted cool rather than black: it reads as sky-lit shadow
    // on flat-coloured cartoon surfaces instead of dirt.
    c *= mix(vec3(0.42, 0.40, 0.55), vec3(1.0), ao);
    c *= mix(vec3(0.56, 0.58, 0.78), vec3(1.0), 1.0 - shadowParams.x * (1.0 - sun));
    c *= 1.0 + clamp(relief, -0.6, 0.6);
    if (mix4.y > 0.5) {
        float l = dot(c, vec3(0.299, 0.587, 0.114));
        c = mix(vec3(l), c, 1.10);                       // saturation
        c = mix(c, c * c * (3.0 - 2.0 * c), 0.18);       // gentle S-curve
        vec2 v = uv - 0.5;
        c *= 1.0 - dot(v, v) * 0.35;                     // vignette
    }
    if (mix4.z > 2.5) c = mat.a > 0.05 ? vec3(0.5 + relief) : vec3(0.0, 0.0, 0.3);
    else if (mix4.z > 1.5) c = vec3(sun);
    else if (mix4.z > 0.5) c = vec3(texture2D(aoTex, uv).r);
    // luma in alpha for FXAA
    gl_FragColor = vec4(c, dot(clamp(c, 0.0, 1.0), vec3(0.299, 0.587, 0.114)));
}
"""

FXAA_FRAG = """#version 120
varying vec2 uv;
uniform sampler2D src;
uniform vec2 pixel;
uniform float fxaaOn;
void main() {
    vec4 m = texture2D(src, uv);
    if (fxaaOn < 0.5) { gl_FragColor = vec4(m.rgb, 1.0); return; }
    float lNW = texture2D(src, uv + pixel * vec2(-1.0, -1.0)).a;
    float lNE = texture2D(src, uv + pixel * vec2( 1.0, -1.0)).a;
    float lSW = texture2D(src, uv + pixel * vec2(-1.0,  1.0)).a;
    float lSE = texture2D(src, uv + pixel * vec2( 1.0,  1.0)).a;
    float lM = m.a;
    float lMin = min(lM, min(min(lNW, lNE), min(lSW, lSE)));
    float lMax = max(lM, max(max(lNW, lNE), max(lSW, lSE)));
    vec2 dir = vec2(-((lNW + lNE) - (lSW + lSE)), (lNW + lSW) - (lNE + lSE));
    float reduce = max((lNW + lNE + lSW + lSE) * 0.03125, 0.0078125);
    float rcp = 1.0 / (min(abs(dir.x), abs(dir.y)) + reduce);
    dir = clamp(dir * rcp, vec2(-8.0), vec2(8.0)) * pixel;
    vec3 a = 0.5 * (texture2D(src, uv + dir * (1.0 / 3.0 - 0.5)).rgb +
                    texture2D(src, uv + dir * (2.0 / 3.0 - 0.5)).rgb);
    vec3 b = a * 0.5 + 0.25 * (texture2D(src, uv + dir * -0.5).rgb +
                               texture2D(src, uv + dir * 0.5).rgb);
    float lB = dot(b, vec3(0.299, 0.587, 0.114));
    gl_FragColor = vec4((lB < lMin || lB > lMax) ? a : b, 1.0);
}
"""


class PostFX(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('PostFX')

    AO_RADIUS = 1.6        # feet; a toon is roughly 3-4 units tall
    AO_INTENSITY = 2.6
    AO_MAX_DIST = 220.0
    SUN_DIRECTION = Vec3(0.45, 0.55, -0.70)   # direction the sunlight travels
    SHADOW_EXTENT = 160.0  # width of the area around the player that gets shadows
    SHADOW_STRENGTH = 0.85
    FORM_STRENGTH = 0.55   # shading of surfaces facing away from the sun
    RELIEF_STRENGTH = 0.9  # how strongly material normal maps shade a surface
    SHAPE_STRENGTH = 3.0   # depth of shapes painted into a texture (grout, plank gaps)
    GAP_SENSITIVITY = 6.0  # how readily a dark line counts as a gap with no grain
    # Light used for relief where there is no sun (indoors): above and to
    # the left of the camera, in (right, up, depth) view space.
    INDOOR_LIGHT = Vec3(-0.45, 0.65, -0.60)
    MATERIAL_SCAN_INTERVAL = 1.5   # seconds between looks for new geometry
    # Places where a sun makes sense.  Anything else (interiors, cog
    # buildings, boss rooms) has a roof that would shadow everything.
    OUTDOOR_PLACES = ('Playground', 'Street', 'Estate', 'Party',
                      'CogHQExterior', 'FactoryExterior')
    _npotSet = False

    def __init__(self, base):
        self.base = base
        self.manager = None
        self.quads = []
        self.enabled = False
        self.wantAo = ConfigVariableBool('postfx-ao', True).value
        self.wantFxaa = ConfigVariableBool('postfx-fxaa', True).value
        self.wantGrade = ConfigVariableBool('postfx-grade', True).value
        self.wantShadows = ConfigVariableBool('postfx-shadows', True).value
        self.shadowSize = ConfigVariableInt('postfx-shadow-size', 4096).value
        self.wantMaterials = ConfigVariableBool('postfx-materials', True).value
        self.wantSmooth = ConfigVariableBool('postfx-smooth-characters', True).value
        self.wantGrass = ConfigVariableBool('postfx-grass', True).value
        self.grass = None
        self.water = None
        self.wantWater = ConfigVariableBool('postfx-water', True).value
        self.shadowBuffer = None
        self.materialBuffer = None
        self.sunOn = False
        self.debugView = ConfigVariableInt('postfx-debug', 0).value   # 1 AO, 2 sun, 3 relief
        hotkey = ConfigVariableString('postfx-hotkey', 'f6').value
        if hotkey:
            self.accept(hotkey, self.toggle)
        # Our offscreen buffers render through the main window.  If they
        # outlive it, the engine crashes drawing the next frame, so tear
        # everything down the moment the window closes.
        self.accept('window-event', self._windowEvent)
        compareKey = ConfigVariableString('postfx-compare-hotkey', 'f5').value
        if compareKey:
            self.accept(compareKey, self.saveComparison)
        if ConfigVariableBool('want-postfx', True).value:
            self.enable()

    def _windowEvent(self, win):
        if win is self.base.win and self._windowClosed(win):
            self.disable()
            self.ignoreAll()

    @staticmethod
    def _windowClosed(win):
        # Offscreen buffers (used by tests) have no window properties.
        return hasattr(win, 'getProperties') and not win.getProperties().getOpen()

    def supported(self):
        win = self.base.win
        if win is None or win.getGsg() is None or self._windowClosed(win):
            return False
        gsg = win.getGsg()
        return gsg.getSupportsGlsl() and gsg.getSupportsDepthTexture()

    def toggle(self):
        if self.enabled:
            self.disable()
        else:
            self.enable()

    def saveComparison(self):
        """Saves the current view twice, effects off and on, into
        screenshots/ so the two can be compared."""
        import os, time
        from panda3d.core import Filename
        folder = os.path.abspath('screenshots')
        if not os.path.exists(folder):
            os.mkdir(folder)
        stamp = time.strftime('%Y%m%d-%H%M%S')
        wasEnabled = self.enabled
        for label, on in (('off', False), ('on', True)):
            if on:
                self.enable()
            else:
                self.disable()
            # Two frames: one to rebuild the buffers, one with them filled.
            self.base.graphicsEngine.renderFrame()
            self.base.graphicsEngine.renderFrame()
            name = os.path.join(folder, 'postfx-%s-%s.png' % (stamp, label))
            if self.base.win.saveScreenshot(Filename.fromOsSpecific(name)):
                self.notify.info('Saved %s' % name)
            else:
                self.notify.warning('Could not save %s' % name)
        if not wasEnabled:
            self.disable()

    @staticmethod
    def _tex(name, linear=True):
        tex = Texture(name)
        tex.setWrapU(SamplerState.WM_clamp)
        tex.setWrapV(SamplerState.WM_clamp)
        f = SamplerState.FT_linear if linear else SamplerState.FT_nearest
        tex.setMinfilter(f)
        tex.setMagfilter(f)
        return tex

    @staticmethod
    def _shader(frag):
        return Shader.make(Shader.SL_GLSL, VERT, frag)

    def enable(self):
        if self.enabled:
            return True
        if not self.supported():
            self.notify.warning('GLSL/depth textures unavailable; PostFX disabled.')
            return False

        base = self.base
        # Without this Panda pads render targets up to a power of two and
        # the stages would sample the padding.  Every GPU that can run
        # these shaders supports non-power-of-two textures.
        if not PostFX._npotSet:
            loadPrcFileData('postfx', 'textures-power-2 none')
            PostFX._npotSet = True
        mgr = FilterManager(base.win, base.cam)
        sceneTex = self._tex('postfx-scene')
        depthTex = self._tex('postfx-depth', linear=False)
        finalQuad = mgr.renderSceneInto(colortex=sceneTex, depthtex=depthTex)
        if finalQuad is None:
            self.notify.warning('Could not create offscreen buffer; PostFX disabled.')
            mgr.cleanup()
            return False
        self.manager = mgr
        self.quads = []

        def stage(name, frag, div, **inputs):
            tex = self._tex('postfx-' + name)
            quad = mgr.renderQuadInto('postfx-' + name, div=div, colortex=tex)
            quad.setShader(self._shader(frag))
            for k, v in inputs.items():
                quad.setShaderInput(k, v)
            self.quads.append((quad, div))
            return tex

        # AO at half resolution, blurred with depth awareness.
        aoRaw = stage('ao', SSAO_FRAG, 2, depthTex=depthTex)
        aoH = stage('ao-h', AOBLUR_FRAG, 2, src=aoRaw, depthTex=depthTex)
        aoTex = stage('ao-v', AOBLUR_FRAG, 2, src=aoH, depthTex=depthTex)
        self.aoBlurH, self.aoBlurV = self.quads[-2][0], self.quads[-1][0]

        comp = stage('composite', COMPOSITE_FRAG, 1,
                     sceneTex=sceneTex, aoTex=aoTex, depthTex=depthTex)
        self.compositeQuad = self.quads[-1][0]
        self._setupShadows()
        self._setupMaterials()

        finalQuad.setShader(self._shader(FXAA_FRAG))
        finalQuad.setShaderInput('src', comp)
        self.finalQuad = finalQuad
        self.quads.append((finalQuad, 1))

        self.enabled = True
        self._lastState = None
        self.base.taskMgr.add(self._update, 'postfx-update', sort=49)
        self._update()
        self.notify.info('PostFX enabled.')
        return True

    def disable(self):
        if not self.enabled:
            return
        self.base.taskMgr.remove('postfx-update')
        self._cleanupShadows()
        self._cleanupMaterials()
        self.manager.cleanup()
        self.manager = None
        self.quads = []
        self.enabled = False
        self.notify.info('PostFX disabled.')

    def _setupShadows(self):
        """Creates the sun's depth-only view of the scene."""
        base = self.base
        quad = self.compositeQuad
        self.shadowTex = self._tex('postfx-shadow', linear=False)
        quad.setShaderInput('shadowTex', self.shadowTex)
        quad.setShaderInput('shadowMat', LMatrix4.identMat())
        quad.setShaderInput('sunDirView', Vec3(0, 1, 0))
        quad.setShaderInput('shadowParams', Vec4(0, 0, 0, 0))
        self.sunOn = False
        if not self.wantShadows:
            return
        size = self.shadowSize
        fbp = FrameBufferProperties()
        fbp.setRgbColor(True)
        fbp.setRgbaBits(8, 8, 8, 0)
        fbp.setDepthBits(24)
        buf = base.graphicsEngine.makeOutput(
            base.pipe, 'postfx-shadow', -100, fbp, WindowProperties.size(size, size),
            GraphicsPipe.BFRefuseWindow, base.win.getGsg(), base.win)
        if buf is None:
            self.notify.warning('Could not create shadow buffer; shadows disabled.')
            return
        buf.addRenderTexture(self.shadowTex, GraphicsOutput.RTMBindOrCopy,
                             GraphicsOutput.RTPDepth)
        self.shadowBuffer = buf

        lens = OrthographicLens()
        lens.setFilmSize(self.SHADOW_EXTENT, self.SHADOW_EXTENT)
        lens.setNearFar(10.0, 700.0)
        cam = Camera('postfx-shadow-cam')
        cam.setLens(lens)
        cam.setScene(base.render)
        cam.setCameraMask(OTPRender.ShadowCameraBitmask)
        # Characters pick their level of detail by distance from the camera.
        # Measured from the sun's far-off viewpoint they would switch off
        # entirely and cast nothing, so measure from the player's camera.
        cam.setLodCenter(base.cam)
        # Depth only.  Cut-out textures (tree leaves, fences) cast shaped
        # shadows via alpha test rather than blending.  The threshold is
        # high so the soft, semi-transparent shadow decals baked into many
        # props don't themselves cast a shadow.
        state = RenderState.makeEmpty()
        state = state.addAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 1000)
        state = state.addAttrib(AlphaTestAttrib.make(RenderAttrib.MGreater, 0.9), 1000)
        state = state.addAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
        cam.setInitialState(state)
        # The sky dome is parented to the camera and must not cast.
        noDraw = RenderState.makeEmpty()
        noDraw = noDraw.addAttrib(DepthWriteAttrib.make(DepthWriteAttrib.MOff), 2000)
        noDraw = noDraw.addAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 2000)
        cam.setTagStateKey('sky')
        for value in ('Regular', 'Halloween'):
            cam.setTagState(value, noDraw)
        self.shadowLens = lens
        # sunRoot's +Y axis points along the light; the camera slides in
        # its XZ plane so the map can be snapped to whole texels.
        self.sunRoot = base.render.attachNewNode('postfx-sun')
        self.sunRoot.lookAt(Point3(self.SUN_DIRECTION))
        self.shadowCam = self.sunRoot.attachNewNode(cam)
        buf.makeDisplayRegion().setCamera(self.shadowCam)
        buf.setActive(False)

    def _cleanupShadows(self):
        if self.shadowBuffer is not None:
            self.base.graphicsEngine.removeWindow(self.shadowBuffer)
            self.shadowBuffer = None
            self.shadowCam.removeNode()
            self.sunRoot.removeNode()
        self.sunOn = False

    def _setupMaterials(self):
        """Creates the second view of the scene that records material
        normal-map detail (see MATERIAL_FRAG)."""
        base = self.base
        quad = self.compositeQuad
        self.materialTex = self._tex('postfx-material')
        quad.setShaderInput('materialTex', self.materialTex)
        quad.setShaderInput('lightDirView', self.INDOOR_LIGHT)
        quad.setShaderInput('reliefStrength', 0.0)
        if not self.wantMaterials:
            return
        fbp = FrameBufferProperties()
        fbp.setRgbColor(True)
        fbp.setRgbaBits(8, 8, 8, 8)
        fbp.setDepthBits(24)
        win = base.win
        buf = base.graphicsEngine.makeOutput(
            base.pipe, 'postfx-material', -90, fbp,
            WindowProperties.size(win.getXSize(), win.getYSize()),
            GraphicsPipe.BFRefuseWindow | GraphicsPipe.BFResizeable,
            win.getGsg(), win)
        if buf is None:
            self.notify.warning('Could not create material buffer; normal maps disabled.')
            return
        buf.addRenderTexture(self.materialTex, GraphicsOutput.RTMBindOrCopy,
                             GraphicsOutput.RTPColor)
        buf.setClearColor(Vec4(0, 0, 0, 0))
        self.materialBuffer = buf
        self._materialSize = (win.getXSize(), win.getYSize())

        cam = Camera('postfx-material-cam')
        cam.setLens(base.camLens)          # shared, so it tracks FOV changes
        cam.setScene(base.render)
        # Its own bit, so things can be hidden from this pass alone.
        cam.setCameraMask(MATERIAL_CAMERA_BITMASK)
        self.materialCamNode = cam
        self.materialCam = base.cam.attachNewNode(cam)
        self.materialShader = Shader.make(Shader.SL_GLSL, MATERIAL_VERT, MATERIAL_FRAG)
        self.flatNormal = Texture('postfx-flat-normal')
        self.flatNormal.setup2dTexture(1, 1, Texture.TUnsignedByte, Texture.FRgb)
        self.flatNormal.setRamImage(bytes((255, 128, 128)))
        noDraw = RenderState.makeEmpty()
        noDraw = noDraw.addAttrib(DepthWriteAttrib.make(DepthWriteAttrib.MOff), 2000)
        noDraw = noDraw.addAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 2000)
        cam.setTagStateKey('sky')
        for value in ('Regular', 'Halloween'):
            cam.setTagState(value, noDraw)
        buf.makeDisplayRegion().setCamera(self.materialCam)
        self._materialSeen = set()
        if self.wantGrass and self.grass is None:
            self.grass = GrassField(base, MATERIAL_CAMERA_BITMASK | OTPRender.ShadowCameraBitmask)
        if self.wantWater and self.water is None:
            self.water = ToonWater(base, MATERIAL_CAMERA_BITMASK | OTPRender.ShadowCameraBitmask)
        self._blobShadows = []
        self._blobsHidden = False
        self._materialScanAt = 0.0
        self._materialScans = 0
        self._updateMaterialCamera()

    def _cleanupMaterials(self):
        if self.materialBuffer is not None:
            self.sunOn = False
            self._updateBlobShadows()      # give the game its blobs back
            self.base.graphicsEngine.removeWindow(self.materialBuffer)
            self.materialBuffer = None
            self.materialCam.removeNode()

    def _updateMaterialCamera(self):
        """Per-frame inputs for the material pass.  Surfaces with no
        material assigned inherit strength 0 here and are discarded."""
        base = self.base
        attrib = ShaderAttrib.make(self.materialShader)
        attrib = attrib.setShaderInput('matNormal', self.flatNormal)
        attrib = attrib.setShaderInput('matParams', Vec4(1, 0, 0, 0))
        attrib = attrib.setShaderInput('shapeParams', Vec4(self.SHAPE_STRENGTH, self.GAP_SENSITIVITY, 0, 0))
        attrib = attrib.setShaderInput('geomFlags', Vec4(0, 0, 0, 0))
        if self.sunOn:
            light = -self.SUN_DIRECTION
        else:
            v = self.INDOOR_LIGHT
            light = base.render.getRelativeVector(base.cam, Vec3(v[0], v[2], v[1]))
        light.normalize()
        attrib = attrib.setShaderInput('lightDirWorld', light)
        # World -> the composite's (right, up, depth) view space.
        m = LMatrix4(base.render.getMat(base.cam))
        toView = LMatrix4(1, 0, 0, 0,  0, 0, 1, 0,  0, 1, 0, 0,  0, 0, 0, 1)
        attrib = attrib.setShaderInput('worldToView', m * toView)
        state = RenderState.makeEmpty().addAttrib(attrib, 0)
        state = state.addAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
        self.materialCamNode.setInitialState(state)

    def _bindMaterials(self):
        """Prepares scene geometry for the material pass.

        Geometry appears all the time (zones load, toons walk in), so this
        runs every MATERIAL_SCAN_INTERVAL seconds and only looks at nodes it
        hasn't seen.  For each piece it:
          - gives characters smooth vertex normals (the models ship none);
          - tags it with the normal map of its material, if it has one;
          - notes the game's blob drop shadows so they can be hidden while
            real sun shadows are on.
        Tags are shader inputs on the geom's render state; the normal
        fixed-function view of the scene ignores them."""
        base = self.base
        seen = self._materialSeen
        self._materialScans += 1
        if self._materialScans % 20 == 0:
            seen.clear()    # pointers get reused; start over now and then
        bound = 0
        for np in base.render.findAllMatches('**/+GeomNode'):
            node = np.node()
            key = (node.this, node.getNumGeoms())
            if key in seen:
                continue
            seen.add(key)
            if np.hasNetTag('postfx-grass') or np.hasNetTag('postfx-water'):
                continue
            if self.water is not None and node.getNumGeoms() and self.water.consider(np):
                continue
            if self.wantSmooth and self._isCharacter(np):
                self._smoothNormals(node)
            net = np.getNetState()
            grassed = False
            for i in range(node.getNumGeoms()):
                geomState = node.getGeomState(i)
                if geomState.hasAttrib(ShaderAttrib):
                    continue
                hasNormals = node.getGeom(i).getVertexData().hasColumn('normal')
                tex = None
                texAttrib = net.compose(geomState).getAttrib(TextureAttrib)
                if texAttrib is not None and not texAttrib.isOff() and texAttrib.getNumOnStages() > 0:
                    tex = texAttrib.getTexture()
                entry = None
                if (self.grass is not None and self.sunOn and not np.hasTag('postfx-grass-done')
                        and self.grass.wantsSurface(np, tex)):
                    self.grass.addSurface(np, i, tex)
                    grassed = True
                if tex is not None:
                    name = tex.getName()
                    if BLOB_SHADOW.search(name):
                        self._blobShadows.append((np, i))
                        continue
                    material = MaterialLibrary.materialFor(name)
                    if material is not None:
                        entry = MaterialLibrary.normalMap(material, base.loader)
                if entry is None and not hasNormals:
                    continue
                attrib = ShaderAttrib.make()
                attrib = attrib.setShaderInput('geomFlags', Vec4(1 if hasNormals else 0, 0, 0, 0))
                if entry is not None:
                    normalTex, units, strength = entry
                    attrib = attrib.setShaderInput('matNormal', normalTex)
                    attrib = attrib.setShaderInput('matParams', Vec4(1.0 / units, strength,
                                                                     1.0 / max(tex.getXSize(), 1),
                                                                     1.0 / max(tex.getYSize(), 1)))
                node.setGeomState(i, geomState.setAttrib(attrib))
                bound += 1
            if grassed:
                np.setTag('postfx-grass-done', '1')
        return bound

    @staticmethod
    def _isCharacter(np):
        """True for geometry that belongs to an animated character."""
        charType = Character.getClassType()
        p = np
        for _ in range(16):
            if p.isEmpty():
                return False
            if p.node().isOfType(charType):
                return True
            p = p.getParent()
        return False

    def _smoothNormals(self, node):
        """Adds averaged vertex normals to a character's geometry.

        Vertices at the same position share one normal even where the mesh
        is split (UV seams, separate primitives), so the surface shades as
        one smooth skin.  Animation data is untouched; Panda animates the
        new normals along with the vertices."""
        groups = {}
        for i in range(node.getNumGeoms()):
            vdata = node.getGeom(i).getVertexData()
            if vdata.hasColumn('normal') or not vdata.hasColumn('vertex'):
                continue
            groups.setdefault(vdata.this, (vdata, []))[1].append(i)
        for vdata, geomIndices in groups.values():
            rows = vdata.getNumRows()
            if rows == 0 or rows > 60000:
                continue
            reader = GeomVertexReader(vdata, 'vertex')
            pos = []
            for _ in range(rows):
                pos.append(reader.getData3())
            keys = [(round(p[0], 3), round(p[1], 3), round(p[2], 3)) for p in pos]
            sums = {}
            for i in geomIndices:
                geom = node.getGeom(i).decompose()
                for prim in geom.getPrimitives():
                    if prim.getNumVerticesPerPrimitive() != 3:
                        continue
                    for t in range(prim.getNumPrimitives()):
                        s = prim.getPrimitiveStart(t)
                        a, b, c = prim.getVertex(s), prim.getVertex(s + 1), prim.getVertex(s + 2)
                        # Unnormalised, so larger triangles weigh more.
                        n = (pos[b] - pos[a]).cross(pos[c] - pos[a])
                        for v in (a, b, c):
                            k = keys[v]
                            if k in sums:
                                sums[k] += n
                            else:
                                sums[k] = Vec3(n)
            newData = GeomVertexData(vdata.replaceColumn(
                InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CNormal))
            writer = GeomVertexWriter(newData, 'normal')
            up = Vec3(0, 0, 1)
            for k in keys:
                n = sums.get(k)
                if n is None or not n.normalize():
                    n = up
                writer.setData3(n)
            for i in geomIndices:
                node.modifyGeom(i).setVertexData(newData)

    def _updateBlobShadows(self):
        """Hides the game's round drop shadows while real ones are cast."""
        hide = self.sunOn
        render = self.base.render
        off = ColorWriteAttrib.make(ColorWriteAttrib.COff)
        keep = []
        for np, i in self._blobShadows:
            if np.isEmpty() or np.getTop() != render:
                continue
            node = np.node()
            if i >= node.getNumGeoms():
                continue
            keep.append((np, i))
            state = node.getGeomState(i)
            if hide and not state.hasAttrib(ColorWriteAttrib):
                node.setGeomState(i, state.setAttrib(off))
            elif not hide and state.hasAttrib(ColorWriteAttrib):
                node.setGeomState(i, state.removeAttrib(ColorWriteAttrib))
        self._blobShadows = keep

    def _updateMaterials(self):
        if self.materialBuffer is None:
            return
        base = self.base
        win = base.win
        size = (win.getXSize(), win.getYSize())
        if size != self._materialSize and size[0] > 0 and size[1] > 0:
            self._materialSize = size
            self.materialBuffer.setSize(size[0], size[1])
        now = globalClock.getRealTime()
        if now >= self._materialScanAt:
            self._materialScanAt = now + self.MATERIAL_SCAN_INTERVAL
            self._bindMaterials()
            self._updateBlobShadows()
        self._updateMaterialCamera()
        quad = self.compositeQuad
        if self.sunOn:
            toSun = base.cam.getRelativeVector(base.render, -self.SUN_DIRECTION)
            toSun.normalize()
            quad.setShaderInput('lightDirView', Vec3(toSun[0], toSun[2], toSun[1]))
        else:
            light = Vec3(self.INDOOR_LIGHT)
            light.normalize()
            quad.setShaderInput('lightDirView', light)
        quad.setShaderInput('reliefStrength', self.RELIEF_STRENGTH)

    def _isOutdoors(self):
        """True when the local toon is somewhere open to the sky."""
        cr = getattr(self.base, 'cr', None)
        playGame = getattr(cr, 'playGame', None)
        if playGame is None:
            return ConfigVariableBool('postfx-shadows-everywhere', False).value
        place = playGame.getPlace()
        if place is None:
            return False
        names = [c.__name__ for c in type(place).__mro__]
        return any(n in names for n in self.OUTDOOR_PLACES)

    def _updateShadows(self):
        if self.shadowBuffer is None:
            return
        base = self.base
        outdoors = self._isOutdoors()
        if outdoors != self.sunOn:
            self.sunOn = outdoors
            # Grass is only grown outdoors; look at the ground again.
            if outdoors and getattr(self, '_materialSeen', None) is not None:
                self._materialSeen.clear()
                self._materialScanAt = 0.0
            self.shadowBuffer.setActive(outdoors)
            if not outdoors:
                self.compositeQuad.setShaderInput('shadowParams', Vec4(0, 0, 0, 0))
        if not outdoors:
            return
        cam = base.cam
        render = base.render
        # Centre the map a little ahead of the camera, on the ground plane.
        fwd = render.getRelativeVector(cam, Vec3(0, 1, 0))
        fwd.setZ(0)
        if fwd.normalize():
            center = cam.getPos(render) + fwd * (self.SHADOW_EXTENT * 0.30)
        else:
            center = cam.getPos(render)
        local = self.sunRoot.getRelativePoint(render, center)
        texel = self.SHADOW_EXTENT / self.shadowSize
        self.shadowCam.setPos(round(local[0] / texel) * texel, local[1] - 350.0,
                              round(local[2] / texel) * texel)
        mat = (cam.getMat(render) * render.getMat(self.shadowCam) *
               self.shadowLens.getProjectionMat())
        toSun = cam.getRelativeVector(render, -self.SUN_DIRECTION)
        toSun.normalize()
        quad = self.compositeQuad
        quad.setShaderInput('shadowMat', mat)
        quad.setShaderInput('sunDirView', Vec3(toSun[0], toSun[2], toSun[1]))
        quad.setShaderInput('shadowParams',
                            Vec4(self.SHADOW_STRENGTH, 1.0 / self.shadowSize,
                                 self.SHADOW_EXTENT * 0.55, self.FORM_STRENGTH))

    def destroy(self):
        self.disable()
        self.ignoreAll()

    def _update(self, task=None):
        """Keeps uniforms in step with the window size and camera lens,
        both of which the game changes at runtime."""
        base = self.base
        lens = base.camLens
        win = base.win
        if lens is None or win is None:
            return task.cont if task else None
        self._updateShadows()
        self._updateMaterials()
        fov = lens.getFov()
        state = (win.getXSize(), win.getYSize(), lens.getNear(), lens.getFar(),
                 fov[0], fov[1])
        if state != self._lastState and state[0] > 0 and state[1] > 0:
            self._lastState = state
            from math import tan, radians
            w, h = float(state[0]), float(state[1])
            lensInfo = Vec4(state[2], state[3],
                            tan(radians(fov[0]) * 0.5), tan(radians(fov[1]) * 0.5))
            for quad, div in self.quads:
                quad.setShaderInput('pixel', Vec2(1.0 / w, 1.0 / h))
                quad.setShaderInput('lensInfo', lensInfo)
                quad.setShaderInput('aoParams',
                                    (self.AO_RADIUS, self.AO_INTENSITY, self.AO_MAX_DIST))
            self.aoBlurH.setShaderInput('dir', Vec2(2.0 / w, 0))
            self.aoBlurV.setShaderInput('dir', Vec2(0, 2.0 / h))
            self.compositeQuad.setShaderInput(
                'mix4', Vec4(1.0 if self.wantAo else 0.0,
                             1.0 if self.wantGrade else 0.0,
                             float(self.debugView), 0.0))
            self.finalQuad.setShaderInput('fxaaOn', 1.0 if self.wantFxaa else 0.0)
        return task.cont if task else None
