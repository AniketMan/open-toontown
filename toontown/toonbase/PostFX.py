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
                          GeomVertexReader, GeomVertexWriter, GeomVertexData, LColor,
                          PTA_LVecBase4f, LVecBase4f,
                          InternalName, Geom, BitMask32)
import re

BLOB_SHADOW = re.compile(r'drop.?shadow', re.I)
NOT_BACKDROP = re.compile(r'fence|tree|water|grass|window|door|sign', re.I)
MATERIAL_CAMERA_BITMASK = BitMask32.bit(7)
from otp.otpbase import OTPRender
from toontown.toonbase import MaterialLibrary
from toontown.toonbase import GrassField as GrassFieldModule
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
    gl_ClipVertex = p3d_ModelViewMatrix * p3d_Vertex;   // for clip planes (OpenInteriors)
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
uniform vec4 geomFlags;     // x: 1 if the geometry carries smooth vertex normals; y: 1 if it glows; z: 1 for a painted backdrop
uniform vec3 lightDirWorld; // light used for relief
uniform mat4 worldToView;
varying vec3 vView;
varying vec3 vWorld;
varying vec3 vNormal;
varying vec2 vUv;
void main() {
    // Painted backdrops (far hills on see-through cards) are marked, the
    // see-through part of the card included: they take the light of the
    // day but no shadows or shading, and a shadow falling on the clear
    // part of a card would show its outline against the sky.
    if (geomFlags.z > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 0.5); return; }
    // Cut-out art (leaves, fences) only counts where it is opaque.
    if (texture2D(p3d_Texture0, vUv).a < 0.5) discard;
    // Things that give off light of their own (tagged postfx-glow) are
    // marked with a value no normal can have, and are not lit or shaded.
    if (geomFlags.y > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
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
    // The shading normal itself, in the composite's view space.  (Storing
    // only its tilt from the flat normal made the composite rebuild that
    // flat normal from depth, which goes wrong along every polygon edge
    // and drew the mesh onto rounded characters as thin lines.)
    vec3 d = normalize((worldToView * vec4(bumped, 0.0)).xyz);
    // rgb: shading normal.  alpha: relief, with 0 meaning "no data".
    gl_FragColor = vec4(clamp(d * 0.5 + 0.5, 0.0, 1.0),
                        0.1 + 0.9 * clamp(relief * 0.5 + 0.5, 0.0, 1.0));
}
"""

COMPOSITE_FRAG = """#version 120
varying vec2 uv;
uniform sampler2D sceneTex;
uniform sampler2D aoTex;
uniform sampler2D shadowTex;
uniform sampler2D shadowTexFar;   // a second, wider map for everything further off
uniform sampler2D materialTex;
uniform vec3 lightDirView;  // light used for surface relief (the sun outdoors)
uniform float reliefStrength;
uniform vec4 mix4;          // ao on, grade on, debug view (1 ao, 2 sun), unused
uniform mat4 shadowMat;     // Panda camera space -> shadow clip space
uniform mat4 shadowMatFar;
uniform vec4 shadowFar;     // max distance (0 = no far map), texel (uv), unused, unused
uniform vec3 sunDirView;    // direction to the sun in (right, up, depth) space
uniform vec4 shadowParams;  // strength, shadow texel (uv), max distance, form strength
uniform vec4 hazeColor;     // colour of the air, strongest amount (0 = off)
uniform vec4 hazeParams;    // density per foot, clear distance, glow toward the sun, unused
uniform vec3 hazeUp;        // world up in (right, up, depth) space
uniform vec4 lightKey;      // colour and strength of the sun, moon or lamp
uniform vec4 lightAmbient;  // colour and strength of the fill light; a = 1 when the scene is lit
uniform vec4 lampPos[8];    // room lights in (right, up, depth) view space, reach in feet
uniform vec4 lampCol[8];    // their colour and strength; a = 1 when in use
uniform vec4 indoor;        // 1 under a roof, warmth of the room light, camera height above the floor, falloff
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
    // Shadows come from two maps: a sharp one around the player and a
    // wide one beyond it, so a shadow is already there when it comes
    // into view rather than fading in as the player walks up to it.
    // Form shading and shadows reach as far as the wide map does, so
    // nothing is seen changing as the player walks up to it.  (Painted
    // backdrops are kept out of this altogether: see `painted` in main.)
    float limit = max(shadowParams.z, shadowFar.x);
    float far = smoothstep(limit * 0.80, limit, P.z);
    float nearFade = smoothstep(shadowParams.z * 0.75, shadowParams.z, P.z);
    float form = mix(1.0, smoothstep(-0.10, 0.30, ndl), shadowParams.w * (1.0 - far));
    float grazing = 1.0 - clamp(ndl, 0.0, 1.0);
    float a = ign(gl_FragCoord.xy) * 6.2831853;
    // Push the lookup off the surface along its normal, more at grazing
    // sun angles and with distance, to avoid self-shadowing.
    vec3 Q = P + N * (0.05 + 0.25 * grazing + 0.003 * P.z);
    vec4 clip = shadowMat * vec4(Q.x, Q.z, Q.y, 1.0);
    vec3 sc = clip.xyz / clip.w * 0.5 + 0.5;
    vec2 e = abs(sc.xy - 0.5) * 2.0;
    float nearW = 0.0;
    if (sc.x > 0.0 && sc.x < 1.0 && sc.y > 0.0 && sc.y < 1.0 && sc.z < 1.0)
        nearW = (1.0 - smoothstep(0.85, 1.0, max(e.x, e.y)))
              * (1.0 - nearFade);
    float litNear = 1.0;
    if (nearW > 0.0) {
        litNear = 0.0;
        const int TAPS = 12;
        for (int i = 0; i < TAPS; i++) {
            float t = (float(i) + 0.5) / float(TAPS);
            float b = a + t * 6.2831853 * 2.618;
            vec2 o = vec2(cos(b), sin(b)) * sqrt(t) * shadowParams.y * 2.5;
            litNear += step(sc.z - 0.0006, texture2D(shadowTex, sc.xy + o).r);
        }
        litNear /= float(TAPS);
    }
    float litFar = 1.0;
    if (shadowFar.x > 0.0 && nearW < 1.0) {
        vec3 Q2 = P + N * (0.35 + 0.9 * grazing + 0.004 * P.z);
        vec4 clip2 = shadowMatFar * vec4(Q2.x, Q2.z, Q2.y, 1.0);
        vec3 s2 = clip2.xyz / clip2.w * 0.5 + 0.5;
        if (s2.x > 0.0 && s2.x < 1.0 && s2.y > 0.0 && s2.y < 1.0 && s2.z < 1.0) {
            vec2 e2 = abs(s2.xy - 0.5) * 2.0;
            float lit = 0.0;
            const int FAR_TAPS = 8;
            for (int i = 0; i < FAR_TAPS; i++) {
                float t = (float(i) + 0.5) / float(FAR_TAPS);
                float b = a + t * 6.2831853 * 2.618;
                vec2 o = vec2(cos(b), sin(b)) * sqrt(t) * shadowFar.y * 1.6;
                lit += step(s2.z - 0.0005, texture2D(shadowTexFar, s2.xy + o).r);
            }
            lit /= float(FAR_TAPS);
            float w = (1.0 - smoothstep(0.90, 1.0, max(e2.x, e2.y))) * (1.0 - far);
            litFar = mix(1.0, lit, w);
        }
    }
    return min(form, mix(litFar, litNear, nearW));
}
void main() {
    vec3 c = texture2D(sceneTex, uv).rgb;
    float ao = mix(1.0, texture2D(aoTex, uv).r, mix4.x);
    float sun = 1.0;
    vec3 P = viewPos(uv);
    vec4 mat = texture2D(materialTex, uv);
    vec3 N = vec3(0.0, 0.0, -1.0);
    // Two marks the material pass leaves in place of a normal: a light
    // of its own, and a painted backdrop.
    bool marked = mat.a > 0.4 && dot(mat.rgb, mat.rgb) < 0.03;
    bool glows = marked && mat.a > 0.75;
    bool painted = marked && !glows;
    bool shaped = mat.a > 0.05 && !marked;
    if (shadowParams.x > 0.0 && P.z < lensInfo.y * 0.97 && !painted) {
        float ndl;
        N = viewNormal(P, ndl);
        // The material pass knows the smooth / normal-mapped normal.
        if (shaped) {
            N = normalize(mat.rgb * 2.0 - 1.0);
            ndl = dot(N, sunDirView);
        }
        sun = sunLight(P, N, ndl);
    }
    // Surface relief from the material pass: where the normal map tilts
    // the surface toward the light it brightens, away it darkens.
    float relief = 0.0;
    if (shaped) {
        relief = ((mat.a - 0.1) / 0.9 * 2.0 - 1.0) * reliefStrength;
        relief *= 1.0 - smoothstep(110.0, 230.0, P.z);    // too fine to see far away
        relief *= 0.45 + 0.55 * sun;                      // weaker in shadow
    }
    // The game's art is painted at full brightness.  Here it is treated
    // as the colour of each surface and lit: a dim ambient fill from the
    // sky or the room, plus a key light (sun, moon or lamp) only where
    // that light actually reaches.  Take the key away and the scene is
    // left in its ambient shade.
    float direct = 1.0 - shadowParams.x * (1.0 - sun);
    // A light of its own: shown at full strength wherever it is.
    if (glows) {
        relief = 0.0;
        c = min(c * 1.35 + 0.06, vec3(1.0));
    } else if (lightAmbient.a > 0.5 && P.z < lensInfo.y * 0.97) {
        vec3 key = lightKey.rgb;
        if (indoor.x > 0.5) {
            // The room's own lights: a ceiling fitting, each lamp that
            // stands in it and each window.  Every one lights what faces
            // it and is near it, and fades with distance.
            // Rounded characters carry a smooth normal in the material
            // pass; without it their flat polygons would show as facets.
            vec3 Ns = shaped ? normalize(mat.rgb * 2.0 - 1.0) : N;
            vec3 sum = vec3(0.0);
            for (int i = 0; i < 8; i++) {
                if (lampCol[i].a < 0.5) continue;
                vec3 toLamp = lampPos[i].xyz - P;
                float d = length(toLamp);
                // Light wraps a little past the edge, as it does off pale
                // walls, so nothing turned from a lamp goes fully black.
                float facing = 0.22 + 0.78 * smoothstep(-0.55, 0.60, dot(Ns, toLamp / d));
                float reach = lampPos[i].w;
                float amount = facing / (1.0 + d * d / (reach * reach));
                // Only the ceiling fitting casts the mapped shadows.
                if (i == 0) amount *= direct;
                sum += lampCol[i].rgb * amount;
            }
            key *= sum;
            direct = 1.0;
        }
        // Creases and corners see less of the sky, and a little less of
        // the key light too.
        vec3 ambient = lightAmbient.rgb * mix(vec3(0.62, 0.60, 0.70), vec3(1.0), ao);
        vec3 light = ambient + key * direct * mix(0.80, 1.0, ao);
        // Where several lights overlap, roll off instead of burning out.
        light = min(light, vec3(1.0) + (light - vec3(1.0)) * 0.22);
        // Far backdrops are paintings of scenery with see-through sky
        // above it.  Lighting fades off up their height so the top of a
        // painting never shows as an edge against the real sky.
        float backdrop = smoothstep(250.0, 500.0, length(P)) *
                         smoothstep(0.02, 0.20, dot(normalize(P), hazeUp));
        c *= mix(light, vec3(1.0), backdrop);
    } else {
        // Menus and the sky itself stay as painted.
        c *= mix(vec3(0.42, 0.40, 0.55), vec3(1.0), ao);
    }
    c *= 1.0 + clamp(relief, -0.6, 0.6);
    c = clamp(c, 0.0, 1.0);
    // Aerial perspective: distant scenery drifts toward the colour of
    // the air, losing contrast the way real landscapes do.  The sky gets
    // the same haze along the horizon, so scenery standing against it
    // (and the see-through parts of painted backdrops) never shows an
    // edge, and it thins with height into clear sky.
    if (hazeColor.a > 0.0) {
        vec3 V = normalize(P);
        float isSky = step(lensInfo.y * 0.97, P.z);
        float dist = max(length(P) - hazeParams.y, 0.0);
        float haze = mix(1.0 - exp(-dist * hazeParams.x), 1.0, isSky) * hazeColor.a;
        haze *= 1.0 - smoothstep(0.02, 0.20, dot(V, hazeUp));
        float toward = max(dot(V, sunDirView), 0.0);
        c = mix(c, hazeColor.rgb * (1.0 + hazeParams.z * toward * toward), haze);
    }
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
    SHADOW_EXTENT = 300.0  # width of the area around the player that gets sharp shadows
    # A second, coarser map covers everything out to the haze, so shadows
    # are already there when they come into view.
    SHADOW_FAR_EXTENT = 1100.0
    SHADOW_FAR_DISTANCE = 560.0
    SHADOW_STRENGTH = 0.96 # how completely a cast shadow blocks the key light
    # Light levels.  Ambient + key is a little over 1, so a surface in
    # full light looks as the artists painted it; in shade only the
    # ambient part is left.
    SUN_COLOR = Vec3(0.76, 0.69, 0.55)
    SKY_AMBIENT = 0.42         # daylight fill, tinted by the sky
    MOON_COLOR = Vec3(0.30, 0.34, 0.46)
    NIGHT_AMBIENT = 0.42
    LAMP_COLOR = Vec3(0.86, 0.77, 0.60)
    ROOM_AMBIENT = Vec3(0.19, 0.175, 0.21)
    # Under a roof the light comes from the ceiling instead: almost
    # straight down, softer and weaker than the sun, and warm.
    INDOOR_LIGHT_DIRECTION = Vec3(0.20, 0.30, -0.93)
    INDOOR_SHADOW_STRENGTH = 0.85
    INDOOR_SHADOW_SOFTNESS = 2.4   # times the sun's shadow blur
    INDOOR_FORM_STRENGTH = 0.0     # the lamp does its own facing
    CEILING_STRENGTH = 1.95        # brightness right under a ceiling fitting
    LAMP_STRENGTH = 1.6            # a standing lamp, close to its shade
    LAMP_TINT = Vec3(1.0, 0.86, 0.62)
    WINDOW_STRENGTH = 0.7          # daylight through one window
    WINDOW_TINT = Vec3(0.80, 0.95, 1.20)
    LAMP_GAIN = 1.75               # brightness right under the lamp
    LAMP_MAX_ROOM = 140.0          # bigger spaces get a lamp that follows the toon
    INDOOR_WARMTH = 1.0
    INDOOR_FALLOFF = 0.45          # how much darker the tops of the walls are than the floor
    FORM_STRENGTH = 0.80   # shading of surfaces facing away from the sun
    # The haze begins where the grass blades begin to thin and is half
    # way to its full strength where the last of them are gone, so the
    # two fades read as one.
    HAZE_START = GrassFieldModule.FADE_NEAR
    HAZE_DENSITY = 0.693 / (GrassFieldModule.FADE_FAR - GrassFieldModule.FADE_NEAR)
    HAZE_MAX = 0.52        # the most a far object can fade
    HAZE_SUN_GLOW = 0.12   # extra brightness of the air when looking toward the sun
    HAZE_DAY_COLOR = Vec3(0.74, 0.84, 0.96)   # used when the sky gives no colour
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
        self.wantFarShadows = ConfigVariableBool('postfx-far-shadows', True).value
        self.wantMaterials = ConfigVariableBool('postfx-materials', True).value
        self.wantSmooth = ConfigVariableBool('postfx-smooth-characters', True).value
        self.wantGrass = ConfigVariableBool('postfx-grass', True).value
        self.wantIndoorLight = ConfigVariableBool('postfx-indoor-light', True).value
        self.indoorOn = False
        self.wantHaze = ConfigVariableBool('postfx-haze', True).value
        self._hazeSky = (None, None)
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
        # Switches the sun, moon or lamp off, leaving only the ambient fill.
        self.lightsOff = False
        lightsKey = ConfigVariableString('postfx-lights-hotkey', 'f4').value
        if lightsKey:
            self.accept(lightsKey, self.toggleLights)
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

    def toggleLights(self):
        self.lightsOff = not self.lightsOff
        self.notify.info('Key light %s.' % ('off' if self.lightsOff else 'on'))

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
        self.shadowTexFar = self._tex('postfx-shadow-far', linear=False)
        quad.setShaderInput('shadowTexFar', self.shadowTexFar)
        quad.setShaderInput('shadowMatFar', LMatrix4.identMat())
        quad.setShaderInput('shadowFar', Vec4(0, 0, 0, 0))
        self.shadowBufferFar = None
        quad.setShaderInput('sunDirView', Vec3(0, 1, 0))
        quad.setShaderInput('shadowParams', Vec4(0, 0, 0, 0))
        quad.setShaderInput('hazeColor', Vec4(0, 0, 0, 0))
        quad.setShaderInput('hazeParams', Vec4(0, 0, 0, 0))
        quad.setShaderInput('hazeUp', Vec3(0, 1, 0))
        quad.setShaderInput('indoor', Vec4(0, 0, 0, 0))
        self._lampPos = PTA_LVecBase4f.emptyArray(8)
        self._lampCol = PTA_LVecBase4f.emptyArray(8)
        quad.setShaderInput('lampPos', self._lampPos)
        quad.setShaderInput('lampCol', self._lampCol)
        quad.setShaderInput('lightKey', Vec4(0, 0, 0, 0))
        quad.setShaderInput('lightAmbient', Vec4(1, 1, 1, 0))
        self.sunOn = False
        self.indoorOn = False
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

        # The wide map: same light, same rules, a bigger piece of ground.
        if not self.wantFarShadows:
            return
        farBuf = base.graphicsEngine.makeOutput(
            base.pipe, 'postfx-shadow-far', -99, fbp, WindowProperties.size(size, size),
            GraphicsPipe.BFRefuseWindow, base.win.getGsg(), base.win)
        if farBuf is None:
            self.notify.warning('Could not create the far shadow buffer.')
            return
        farBuf.addRenderTexture(self.shadowTexFar, GraphicsOutput.RTMBindOrCopy,
                                GraphicsOutput.RTPDepth)
        farLens = OrthographicLens()
        farLens.setFilmSize(self.SHADOW_FAR_EXTENT, self.SHADOW_FAR_EXTENT)
        farLens.setNearFar(10.0, 2200.0)
        farCam = Camera('postfx-shadow-far-cam')
        farCam.setLens(farLens)
        farCam.setScene(base.render)
        farCam.setCameraMask(OTPRender.ShadowCameraBitmask)
        farCam.setLodCenter(base.cam)
        farCam.setInitialState(state)
        farCam.setTagStateKey('sky')
        for value in ('Regular', 'Halloween'):
            farCam.setTagState(value, noDraw)
        self.shadowLensFar = farLens
        self.shadowCamFar = self.sunRoot.attachNewNode(farCam)
        farBuf.makeDisplayRegion().setCamera(self.shadowCamFar)
        farBuf.setActive(False)
        self.shadowBufferFar = farBuf

    def _cleanupShadows(self):
        if self.shadowBuffer is not None:
            self.base.graphicsEngine.removeWindow(self.shadowBuffer)
            self.shadowBuffer = None
            if self.shadowBufferFar is not None:
                self.base.graphicsEngine.removeWindow(self.shadowBufferFar)
                self.shadowBufferFar = None
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
        self._scan = None
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

    SCAN_BUDGET = 0.004     # seconds a frame may spend looking at new geometry

    def _bindMaterials(self, everything=False):
        """Runs the scene scan (_scanScene) a few milliseconds at a time,
        so walking into a place full of things not seen before (a shop
        with its keeper, a street's far sections) does not hold a frame
        up.  Returns True when a scan has been finished."""
        if self._scan is None:
            self._scan = self._scanScene()
        end = globalClock.getRealTime() + (1e9 if everything else self.SCAN_BUDGET)
        try:
            while True:
                next(self._scan)
                if globalClock.getRealTime() >= end:
                    return False
        except StopIteration:
            self._scan = None
            return True

    def _scanScene(self):
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
        for np in GrassFieldModule.geomNodes(base.render):
            yield
            if np.isEmpty():
                continue
            node = np.node()
            key = (node.this, node.getNumGeoms())
            if key in seen:
                continue
            seen.add(key)
            if np.hasNetTag('postfx-grass') or np.hasNetTag('postfx-water'):
                continue
            # Geometry that has been through here is marked on the node
            # itself, so it is passed over at once however often the scene
            # is looked at again (walking into a shop looks at it again).
            # Grass grows under the open sky: on the street, and on the
            # street still standing outside a shop the toon is in.
            growing = self.sunOn or np.hasNetTag('postfx-outside')
            done = np.getPythonTag('postfx-done')
            if done is not None and done[0] == node.getNumGeoms() and (done[1] or not growing):
                continue
            np.setPythonTag('postfx-done', (node.getNumGeoms(), growing))
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
                if np.hasNetTag('postfx-glow'):
                    attrib = ShaderAttrib.make().setShaderInput('geomFlags', Vec4(0, 1, 0, 0))
                    node.setGeomState(i, geomState.setAttrib(attrib))
                    bound += 1
                    continue
                if self._isBackdrop(np, net.compose(geomState)):
                    attrib = ShaderAttrib.make().setShaderInput('geomFlags', Vec4(0, 0, 1, 0))
                    node.setGeomState(i, geomState.setAttrib(attrib))
                    bound += 1
                    continue
                entry = None
                if (self.grass is not None and growing and not np.hasTag('postfx-grass-done')
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
        return

    @staticmethod
    def _isBackdrop(np, state):
        """A painting of far scenery: a big, tall, see-through card."""
        trans = state.getAttrib(TransparencyAttrib)
        if trans is None or trans.getMode() == TransparencyAttrib.MNone:
            return False
        if np.hasPythonTag('postfx-backdrop'):
            return np.getPythonTag('postfx-backdrop')
        result = False
        if not NOT_BACKDROP.search(np.getName()):
            bounds = np.getTightBounds()
            if bounds:
                size = bounds[1] - bounds[0]
                result = size[2] >= 12.0 and (max(size[0], size[1]) >= 80.0 or size[2] >= 40.0)
        np.setPythonTag('postfx-backdrop', result)
        return result

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
        hide = self.sunOn or self.indoorOn
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
        if self._scan is not None or now >= self._materialScanAt:
            self._materialScanAt = now + self.MATERIAL_SCAN_INTERVAL
            if self._bindMaterials():
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
        # In a walk-in shop it is the side of the doorway the camera is on
        # that counts, not which place the server has the toon in.
        import sys
        rooms = sys.modules.get('toontown.building.OpenInteriors')
        if rooms is not None and rooms.viewOutdoors is not None:
            return rooms.viewOutdoors
        place = playGame.getPlace()
        if place is None:
            return False
        names = [c.__name__ for c in type(place).__mro__]
        return any(n in names for n in self.OUTDOOR_PLACES)

    LAMP_NAMES = re.compile(r'lamp_?shade|lantern|chandelier|light_?bulb', re.I)
    WINDOW_NAMES = re.compile(r'window', re.I)

    def _roomLights(self):
        """The lights of the room the toon is in, as (world position,
        colour and strength, reach in feet).  The first is always the
        ceiling fitting.  The rest are read off the room itself: one for
        every lamp standing in it and one for every window.  Looked at
        again every couple of seconds because rooms finish loading late."""
        now = globalClock.getRealTime()
        cached = getattr(self, '_lamp', None)
        if cached is not None and now < cached[0]:
            return cached[1]
        base = self.base
        render = base.render
        avatar = getattr(base, 'localAvatar', None)
        if avatar is not None and not avatar.isEmpty():
            feet = avatar.getPos(render)
        else:
            feet = base.cam.getPos(render) - Vec3(0, 0, 5)
        rooms = []
        lo, hi = None, None
        for child in render.getChildren():
            # Rooms are plain model nodes; skip toons, the camera and helpers.
            if (child.isHidden() or child.isStashed() or child.hasTag('postfx-outside')
                    or self._isCharacter(child)):
                continue
            if child.find('**/+GeomNode').isEmpty() or not child.find('**/+Camera').isEmpty():
                continue
            if not child.find('**/+Character').isEmpty():
                continue
            bounds = child.getTightBounds()
            if not bounds:
                continue
            rooms.append(child)
            if lo is None:
                lo, hi = Point3(bounds[0]), Point3(bounds[1])
            else:
                lo = Point3(min(lo[0], bounds[0][0]), min(lo[1], bounds[0][1]), min(lo[2], bounds[0][2]))
                hi = Point3(max(hi[0], bounds[1][0]), max(hi[1], bounds[1][1]), max(hi[2], bounds[1][2]))
        lights = []
        size = (hi - lo) if lo is not None else Vec3(0)
        fitted = lo is not None and max(size[0], size[1]) <= self.LAMP_MAX_ROOM and size[2] > 6.0
        if fitted:
            centre = Point3((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5, lo[2])
            # Standing lamps: a warm pool around each shade.
            for room in rooms:
                for np in room.findAllMatches('**/*'):
                    if not self.LAMP_NAMES.search(np.getName()) or np.isHidden():
                        continue
                    b = np.getTightBounds(render)
                    if b:
                        at = Point3((b[0][0] + b[1][0]) * 0.5, (b[0][1] + b[1][1]) * 0.5, b[1][2] + 0.3)
                        lights.append((at, self.LAMP_TINT * self.LAMP_STRENGTH, 7.5))
            # Windows: cool daylight spilling in from each.
            for room in rooms:
                for np in room.findAllMatches('**/+GeomNode'):
                    if self.WINDOW_NAMES.search(np.getName()) and not np.isHidden():
                        for at in self._windowCentres(np, lo[2]):
                            inward = Vec3(centre[0] - at[0], centre[1] - at[1], 0)
                            if inward.normalize():
                                at = at + inward * 1.5
                            lights.append((at, self.WINDOW_TINT * self.WINDOW_STRENGTH, 9.0))
            # Ceiling fittings: one for a small room, a row or grid for a
            # long or large one.  Dimmer when lamps and windows share the job.
            height = max(min(size[2] * 0.8, 22.0), 9.0)
            nx = max(1, int(round(size[0] / 34.0)))
            ny = max(1, int(round(size[1] / 34.0)))
            share = self.CEILING_STRENGTH * (0.36 if lights else 1.0)
            # Neighbouring fittings in a grid overlap; keep the total level.
            share /= 1.0 + 0.55 * (min(nx * ny, 5) - 1) ** 0.5
            reach = max(height, 0.45 * max(size[0] / nx, size[1] / ny))
            ceiling = []
            for ix in range(nx):
                for iy in range(ny):
                    at = Point3(lo[0] + size[0] * (ix + 0.5) / nx, lo[1] + size[1] * (iy + 0.5) / ny, lo[2] + height)
                    ceiling.append((at, Vec3(1, 1, 1) * share, reach))
            # The fitting nearest the toon is the one that casts shadows.
            ceiling.sort(key=lambda l: (l[0] - feet).lengthSquared())
            lights = ceiling + lights
        else:
            lights = [(Point3(feet[0], feet[1], feet[2] + 16.0), Vec3(1, 1, 1) * self.CEILING_STRENGTH, 26.0)]
        self._lamp = (now + 2.0, lights)
        return lights

    @staticmethod
    def _windowCentres(np, floorZ):
        """World-space centres of the separate panes in a node that holds
        a room's doors and windows as one mesh: groups of connected
        polygons that start well above the floor are windows."""
        render = np.getTop()
        mat = np.getMat(render)
        parent = {}

        def find(k):
            while parent[k] != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        points = {}
        for geom in np.node().getGeoms():
            geom = geom.decompose()
            reader = GeomVertexReader(geom.getVertexData(), 'vertex')
            for prim in geom.getPrimitives():
                for t in range(prim.getNumPrimitives()):
                    keys = []
                    for vi in range(prim.getPrimitiveStart(t), prim.getPrimitiveEnd(t)):
                        reader.setRow(prim.getVertex(vi))
                        p = mat.xformPoint(reader.getData3())
                        k = (round(p[0], 1), round(p[1], 1), round(p[2], 1))
                        points[k] = p
                        parent.setdefault(k, k)
                        keys.append(k)
                    for k in keys[1:]:
                        parent[find(k)] = find(keys[0])
        groups = {}
        for k, p in points.items():
            groups.setdefault(find(k), []).append(p)
        centres = []
        for pts in groups.values():
            zs = [p[2] for p in pts]
            if min(zs) - floorZ < 1.5 or max(zs) - min(zs) < 0.8 or len(pts) < 4:
                continue
            n = float(len(pts))
            c = Point3(sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(zs) / n)
            # Frame, glass and sill are separate pieces of one window.
            if all((c - o).length() > 3.0 for o in centres):
                centres.append(c)
        return centres

    def _hasPlace(self):
        """True once the local toon is standing somewhere in the world."""
        playGame = getattr(getattr(self.base, 'cr', None), 'playGame', None)
        if playGame is None:
            return ConfigVariableBool('postfx-indoor-everywhere', False).value
        return playGame.getPlace() is not None

    def _updateShadows(self):
        if self.shadowBuffer is None:
            return
        base = self.base
        outdoors = self._isOutdoors()
        indoors = self.wantIndoorLight and not outdoors and self._hasPlace()
        if outdoors != self.sunOn or indoors != self.indoorOn:
            if outdoors != self.sunOn:
                # Grass is only grown outdoors; look at the ground again.
                if outdoors and getattr(self, '_materialSeen', None) is not None:
                    self._materialSeen.clear()
                    self._materialScanAt = 0.0
            self.sunOn = outdoors
            self.indoorOn = indoors
            # The shadow maps still hold what the last light saw.  Shadows
            # are left off for the couple of frames it takes to draw them
            # again, or stepping out of a shop would flash dark.
            self._shadowSettle = 3
            self.shadowBuffer.setActive(outdoors or indoors)
            if self.shadowBufferFar is not None:
                self.shadowBufferFar.setActive(outdoors or indoors)
                if not outdoors:
                    self.compositeQuad.setShaderInput('shadowFar', Vec4(0, 0, 0, 0))
            # The ceiling light looks down through the roof: rooms are
            # modelled facing inward, so from above the ceiling and the
            # near walls are back faces and never drawn.
            self.sunRoot.lookAt(Point3(self.INDOOR_LIGHT_DIRECTION if indoors
                                       else self.SUN_DIRECTION))
            if not indoors:
                self.compositeQuad.setShaderInput('indoor', Vec4(0, 0, 0, 0))
            if not (outdoors or indoors):
                self.compositeQuad.setShaderInput('shadowParams', Vec4(0, 0, 0, 0))
        if not (outdoors or indoors):
            return
        direction = self.INDOOR_LIGHT_DIRECTION if indoors else self.SUN_DIRECTION
        if indoors:
            lights = self._roomLights()
            # The eight nearest the camera, always keeping the ceiling fitting first.
            camPos = base.cam.getPos(base.render)
            rest = sorted(lights[1:], key=lambda l: (l[0] - camPos).lengthSquared())[:7]
            chosen = lights[:1] + rest
            for i in range(8):
                if i < len(chosen):
                    pos, color, reach = chosen[i]
                    v = base.cam.getRelativePoint(base.render, pos)
                    self._lampPos[i] = LVecBase4f(v[0], v[2], v[1], reach)
                    self._lampCol[i] = LVecBase4f(color[0], color[1], color[2], 1)
                else:
                    self._lampCol[i] = LVecBase4f(0, 0, 0, 0)
            self.compositeQuad.setShaderInput('lampPos', self._lampPos)
            self.compositeQuad.setShaderInput('lampCol', self._lampCol)
            self.compositeQuad.setShaderInput('indoor', Vec4(1.0, self.INDOOR_WARMTH, 0, 1.0))
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
        toSun = cam.getRelativeVector(render, -direction)
        toSun.normalize()
        quad = self.compositeQuad
        quad.setShaderInput('shadowMat', mat)
        if self.shadowBufferFar is not None and not indoors:
            # Centred on the camera: it turns too slowly to matter, and
            # moves only in whole texels so its shadows don't shimmer.
            local = self.sunRoot.getRelativePoint(render, cam.getPos(render))
            texel = self.SHADOW_FAR_EXTENT / self.shadowSize
            self.shadowCamFar.setPos(round(local[0] / texel) * texel, local[1] - 1100.0,
                                     round(local[2] / texel) * texel)
            quad.setShaderInput('shadowMatFar', cam.getMat(render) * render.getMat(self.shadowCamFar) *
                                self.shadowLensFar.getProjectionMat())
            quad.setShaderInput('shadowFar', Vec4(self.SHADOW_FAR_DISTANCE, 1.0 / self.shadowSize, 0, 0))
        quad.setShaderInput('sunDirView', Vec3(toSun[0], toSun[2], toSun[1]))
        settle = getattr(self, '_shadowSettle', 0)
        if settle > 0:
            self._shadowSettle = settle - 1
            quad.setShaderInput('shadowParams', Vec4(0, 1.0 / self.shadowSize, self.SHADOW_EXTENT * 0.55, 0))
            quad.setShaderInput('shadowFar', Vec4(0, 0, 0, 0))
        elif indoors:
            quad.setShaderInput('shadowParams',
                                Vec4(self.INDOOR_SHADOW_STRENGTH,
                                     self.INDOOR_SHADOW_SOFTNESS / self.shadowSize,
                                     self.SHADOW_EXTENT * 0.55, self.INDOOR_FORM_STRENGTH))
        else:
            quad.setShaderInput('shadowParams',
                                Vec4(self.SHADOW_STRENGTH, 1.0 / self.shadowSize,
                                     self.SHADOW_EXTENT * 0.55, self.FORM_STRENGTH))

    def _skyColor(self):
        """Colour of the current sky near the horizon, or None.  Skies
        are painted domes, so the band of the painting just above the
        horizon says what time of day the neighbourhood is in."""
        hood = getattr(getattr(getattr(self.base, 'cr', None), 'playGame', None), 'hood', None)
        sky = getattr(hood, 'sky', None)
        if sky is None or sky.isEmpty():
            self._hazeSky = (None, None)
            return None
        if self._hazeSky[0] != sky:
            total, weight = Vec3(0), 0.0
            for gnp in sky.findAllMatches('**/+GeomNode'):
                node = gnp.node()
                for i in range(node.getNumGeoms()):
                    vdata = node.getGeom(i).getVertexData()
                    attrib = node.getGeomState(i).getAttrib(TextureAttrib)
                    tex = attrib.getTexture() if attrib else None
                    if tex is None or vdata.getNumRows() != 4 or not vdata.hasColumn('texcoord'):
                        continue
                    peek = tex.peek()
                    if peek is None:
                        continue
                    pos = GeomVertexReader(vdata, 'vertex')
                    uv = GeomVertexReader(vdata, 'texcoord')
                    corners = []
                    while not pos.isAtEnd():
                        v, t = pos.getData3(), uv.getData2()
                        corners.append((v[2] / max(v.length(), 1e-6), Vec2(t)))
                    corners.sort(key=lambda c: c[0])
                    # A wall panel of the dome: bottom edge on the horizon.
                    if corners[0][0] > 0.15 or corners[3][0] < 0.2:
                        continue
                    (l1, l2), (h1, h2) = [c[1] for c in corners[:2]], [c[1] for c in corners[2:]]
                    if (h1 - l1).lengthSquared() > (h2 - l1).lengthSquared():
                        h1, h2 = h2, h1
                    texel = LColor()
                    for step in range(1, 8):
                        f = step / 8.0
                        at = (l1 + (l2 - l1) * f) * 0.85 + (h1 + (h2 - h1) * f) * 0.15
                        peek.lookup(texel, at[0], at[1])
                        total += Vec3(texel[0], texel[1], texel[2]) * texel[3]
                        weight += texel[3]
            self._hazeSky = (sky, total / weight if weight >= 4.0 else None)
        color = self._hazeSky[1]
        if color is None:
            return None
        scale = sky.getColorScale()
        return Vec3(color[0] * scale[0], color[1] * scale[1], color[2] * scale[2])

    def _updateLight(self):
        """Chooses the key and fill light for where the toon is."""
        quad = self.compositeQuad
        if self.indoorOn:
            key, ambient = Vec3(self.LAMP_COLOR), Vec3(self.ROOM_AMBIENT)
        elif self.sunOn:
            sky = self._skyColor()
            if sky is None:
                sky = Vec3(self.HAZE_DAY_COLOR)
            peak = max(sky[0], sky[1], sky[2], 1e-3)
            hue = sky / peak
            # How much daylight there is, judged from the sky's brightness:
            # a noon sky gives full sun, a night sky leaves moonlight.
            lum = sky[0] * 0.299 + sky[1] * 0.587 + sky[2] * 0.114
            day = min(max((lum - 0.22) / 0.45, 0.0), 1.0)
            day = day * day * (3.0 - 2.0 * day)
            # Low suns take on the colour of the sky they shine through.
            sun = Vec3(self.SUN_COLOR[0] * (0.6 + 0.4 * hue[0]),
                       self.SUN_COLOR[1] * (0.6 + 0.4 * hue[1]),
                       self.SUN_COLOR[2] * (0.6 + 0.4 * hue[2]))
            key = self.MOON_COLOR * (1.0 - day) + sun * day
            fill = hue * 0.55 + Vec3(0.45)
            ambient = fill * (self.NIGHT_AMBIENT * (1.0 - day) + self.SKY_AMBIENT * day)
            # Under a plain daytime sky, full light adds up to exactly
            # white, so a sunlit surface is the colour it was painted.
            # Coloured skies (sunset, night) keep their cast.
            saturation = 1.0 - min(sky[0], sky[1], sky[2]) / peak
            neutral = day * min(max(1.0 - (saturation - 0.15) / 0.5, 0.0), 1.0)
            for i in range(3):
                total = key[i] + ambient[i]
                scale = (total + (1.0 - total) * neutral) / total
                key[i] *= scale
                ambient[i] *= scale
        else:
            quad.setShaderInput('lightAmbient', Vec4(1, 1, 1, 0))
            return
        if self.lightsOff:
            key = Vec3(0)
        up = self.base.cam.getRelativeVector(self.base.render, Vec3(0, 0, 1))
        up.normalize()
        quad.setShaderInput('hazeUp', Vec3(up[0], up[2], up[1]))
        quad.setShaderInput('lightKey', Vec4(key[0], key[1], key[2], 1))
        quad.setShaderInput('lightAmbient', Vec4(ambient[0], ambient[1], ambient[2], 1))

    def _updateHaze(self):
        quad = self.compositeQuad
        render = self.base.render
        # Only under an open sky, and not where the game already fogs
        # the scene itself (under water, for instance).
        if not (self.wantHaze and self.sunOn) or render.getFog() is not None:
            quad.setShaderInput('hazeColor', Vec4(0, 0, 0, 0))
            return
        sky = self._skyColor()
        color = Vec3(self.HAZE_DAY_COLOR) if sky is None else sky
        # Air lit by the sky is a little paler than the sky behind it.
        brightness = max(color[0], color[1], color[2])
        color = color * 0.8 + Vec3(brightness) * 0.2
        # Night and other whole-scene tints darken the air with everything else.
        tint = render.getColorScale()
        color = Vec3(color[0] * tint[0], color[1] * tint[1], color[2] * tint[2])
        quad.setShaderInput('hazeColor', Vec4(color[0], color[1], color[2], self.HAZE_MAX))
        up = self.base.cam.getRelativeVector(render, Vec3(0, 0, 1))
        up.normalize()
        quad.setShaderInput('hazeUp', Vec3(up[0], up[2], up[1]))
        quad.setShaderInput('hazeParams', Vec4(self.HAZE_DENSITY, self.HAZE_START,
                                               self.HAZE_SUN_GLOW, 0))

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
        self._updateLight()
        self._updateHaze()
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
