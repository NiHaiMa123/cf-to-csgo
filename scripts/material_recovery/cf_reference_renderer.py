"""Generic CF reference software renderer (material reconstruction v2 Phase C).

Implements the recovered CF shader semantics on real mesh/UV/normal data so
the reconstructed formula can be validated *behaviorally* before any Source
translation:

    out.rgb = diffuse_lit
            + SpecularMap.rgb * spec_term * AlphaMap.g
            + CubeSample.rgb * EnvCubeMapBrightness * AlphaMap.b

Design rules (plan.md v2):
- directional cubemap sampling only (view dir, surface normal, reflect,
  refract, face lookup, configurable transform). Never mean(cubemap).
- every formula piece carries an explicit OBSERVED/INFERRED/APPROXIMATED/
  UNKNOWN status in the emitted report;
- no weapon names/paths here; callers pass meshes, maps and CFG values.

Renderer: numpy z-buffer rasterizer (auditable, no Blender fidelity risk).
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image

LUM_WEIGHTS = np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)


# ---------------------------------------------------------------- textures

def load_rgb(path: Path | str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def decode_bc1_block(block: bytes) -> np.ndarray:
    """Decode one 8-byte DXT1/BC1 block -> 4x4x3 float rgb."""
    c0, c1, bits = struct.unpack("<HHI", block)
    r0, g0, b0 = (c0 >> 11) & 31, (c0 >> 5) & 63, c0 & 31
    r1, g1, b1 = (c1 >> 11) & 31, (c1 >> 5) & 63, c1 & 31
    p = np.zeros((4, 3), dtype=np.float32)
    p[0] = (r0 / 31, g0 / 63, b0 / 31)
    p[1] = (r1 / 31, g1 / 63, b1 / 31)
    if c0 > c1:
        p[2] = (2 * p[0] + p[1]) / 3
        p[3] = (p[0] + 2 * p[1]) / 3
    else:
        p[2] = (p[0] + p[1]) / 2
        p[3] = 0.0
    out = np.zeros((4, 4, 3), dtype=np.float32)
    for i in range(16):
        out[i // 4, i % 4] = p[(bits >> (2 * i)) & 3]
    return out


def dds_faces(path: Path | str) -> dict[str, np.ndarray]:
    """Decode a 6-face single-mip DXT1 cubemap DDS -> {face: HxWx3}."""
    data = Path(path).read_bytes()
    if data[:4] != b"DDS ":
        raise ValueError("not a DDS")
    height, width = struct.unpack("<II", data[12:20])
    fourcc = data[84:88]
    caps2 = struct.unpack("<I", data[112:116])[0]
    if fourcc != b"DXT1" or not caps2 & 0x200:
        raise ValueError(f"need 6-face DXT1 cubemap, got {fourcc} caps2={caps2:x}")
    face_names = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
    block_bytes = (width // 4) * (height // 4) * 8
    faces = {}
    off = 128
    for name in face_names:
        img = np.zeros((height, width, 3), dtype=np.float32)
        for by in range(height // 4):
            for bx in range(width // 4):
                block = data[off:off + 8]
                off += 8
                img[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4] = decode_bc1_block(block)
        faces[name] = img
    return faces


def sample_bilinear(arr: np.ndarray, uv: np.ndarray) -> np.ndarray:
    """arr HxWxC, uv Nx2 in [0,1] -> NxC bilinear."""
    h, w = arr.shape[:2]
    x = np.clip(uv[:, 0], 0.0, 1.0) * (w - 1)
    y = np.clip(uv[:, 1], 0.0, 1.0) * (h - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx = (x - x0)[:, None]
    fy = (y - y0)[:, None]
    c00 = arr[y0, x0]
    c10 = arr[y0, x1]
    c01 = arr[y1, x0]
    c11 = arr[y1, x1]
    return (c00 * (1 - fx) * (1 - fy) + c10 * fx * (1 - fy)
            + c01 * (1 - fx) * fy + c11 * fx * fy)


def cube_sample(faces: dict[str, np.ndarray], dirs: np.ndarray) -> np.ndarray:
    """DirectX cubemap lookup: dirs Nx3 -> Nx3 rgb (bilinear)."""
    out = np.zeros((len(dirs), 3), dtype=np.float32)
    ax = np.abs(dirs)
    # face order and uv mapping per DX cubemap spec
    sel = [
        (dirs[:, 0] > 0, "+X", (-dirs[:, 2], -dirs[:, 1]), dirs[:, 0]),
        (dirs[:, 0] <= 0, "-X", (dirs[:, 2], -dirs[:, 1]), -dirs[:, 0]),
        (dirs[:, 1] > 0, "+Y", (dirs[:, 0], dirs[:, 2]), dirs[:, 1]),
        (dirs[:, 1] <= 0, "-Y", (dirs[:, 0], -dirs[:, 2]), -dirs[:, 1]),
        (dirs[:, 2] > 0, "+Z", (dirs[:, 0], -dirs[:, 1]), dirs[:, 2]),
        (dirs[:, 2] <= 0, "-Z", (-dirs[:, 0], -dirs[:, 1]), -dirs[:, 2]),
    ]
    major = np.argmax(ax, axis=1)  # 0=x 1=y 2=z
    for mi, (cond, name, (su, sv), ma) in enumerate(sel):
        axis = mi // 2
        mask = (major == axis) & cond
        if not mask.any():
            continue
        d = dirs[mask]
        if axis == 0:
            u = np.where(d[:, 0] > 0, -d[:, 2], d[:, 2])
            v = -d[:, 1]
        elif axis == 1:
            u = d[:, 0]
            v = np.where(d[:, 1] > 0, d[:, 2], -d[:, 2])
        else:
            u = np.where(d[:, 2] > 0, d[:, 0], -d[:, 0])
            v = -d[:, 1]
        m = np.abs(d[:, axis])
        uu = (u / np.maximum(m, 1e-9) + 1.0) * 0.5
        vv = (v / np.maximum(m, 1e-9) + 1.0) * 0.5
        out[mask] = sample_bilinear(faces[name], np.stack([uu, vv], 1))
    return out


# ---------------------------------------------------------------- geometry

def load_skin_meshes(skin_json: Path | str,
                     skip_prefixes: tuple[str, ...] = ()) -> list[dict]:
    skin = json.loads(Path(skin_json).read_text(encoding="utf-8"))
    meshes = []
    for m in skin["meshes"]:
        if m["name"].lower().startswith(tuple(p.lower() for p in skip_prefixes)):
            continue
        verts = np.asarray(m["vertices"], dtype=np.float32).reshape(-1, 3)
        tris = np.asarray(m["triangles"], dtype=np.int64).reshape(-1, 3)
        uvs = np.asarray(m["uvs"], dtype=np.float32).reshape(-1, 2)
        uvs[:, 1] = 1.0 - uvs[:, 1]  # single global v flip (pipeline 4.2)
        meshes.append({"name": m["name"], "verts": verts, "tris": tris, "uvs": uvs})
    return meshes


def vertex_normals(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    n = np.cross(verts[tris[:, 1]] - verts[tris[:, 0]],
                 verts[tris[:, 2]] - verts[tris[:, 0]])
    area = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.maximum(area, 1e-12)
    vn = np.zeros_like(verts)
    weighted = n * area
    for k in range(3):
        np.add.at(vn, tris[:, k], weighted)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def make_sphere(radius: float, seg: int = 64, rings: int = 32) -> dict:
    verts, uvs = [], []
    for r in range(rings + 1):
        phi = math.pi * r / rings
        for s in range(seg + 1):
            th = 2 * math.pi * s / seg
            verts.append((radius * math.sin(phi) * math.cos(th),
                          radius * math.sin(phi) * math.sin(th),
                          radius * math.cos(phi)))
            uvs.append((s / seg, r / rings))
    tris = []
    for r in range(rings):
        for s in range(seg):
            a = r * (seg + 1) + s
            b = a + seg + 1
            tris += [(a, b, a + 1), (a + 1, b, b + 1)]
    return {"name": "test_sphere", "verts": np.array(verts, np.float32),
            "tris": np.array(tris, np.int64), "uvs": np.array(uvs, np.float32)}


def make_plane(size: float, n: int = 2) -> dict:
    verts, uvs = [], []
    for y in range(n + 1):
        for x in range(n + 1):
            verts.append((size * (x / n - 0.5), 0.0, size * (y / n - 0.5)))
            uvs.append((x / n, y / n))
    tris = []
    for y in range(n):
        for x in range(n):
            a = y * (n + 1) + x
            b = a + n + 1
            tris += [(a, b, a + 1), (a + 1, b, b + 1)]
    return {"name": "test_plane", "verts": np.array(verts, np.float32),
            "tris": np.array(tris, np.int64), "uvs": np.array(uvs, np.float32)}


# ---------------------------------------------------------------- rasterize

def look_at(eye: np.ndarray, target: np.ndarray, up=(0, 0, 1)) -> np.ndarray:
    f = np.asarray(target, np.float32) - np.asarray(eye, np.float32)
    f = f / np.linalg.norm(f)
    r = np.cross(f, np.asarray(up, np.float32))
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    m = np.eye(4, dtype=np.float32)
    m[0, :3], m[1, :3], m[2, :3] = r, u, -f
    m[:3, 3] = (-r @ eye, -u @ eye, f @ eye)
    return m


def project(verts_w: np.ndarray, view: np.ndarray, fov_deg: float,
            size: int) -> np.ndarray:
    """World -> screen. Returns Nx3 (x, y, z_cam_forward)."""
    v = np.concatenate([verts_w, np.ones((len(verts_w), 1), np.float32)], 1)
    c = v @ view.T
    f = 0.5 * size / math.tan(math.radians(fov_deg) / 2)
    z = np.maximum(-c[:, 2], 1e-6)  # camera looks down -z
    x = c[:, 0] * f / z + size / 2
    y = -c[:, 1] * f / z + size / 2
    return np.stack([x, y, z], 1)


def rasterize(meshes: list[dict], view: np.ndarray, fov_deg: float,
              size: int) -> dict:
    """Z-buffer rasterize -> per-pixel tri hit + barycentric + mesh index."""
    depth = np.full((size, size), np.inf, np.float32)
    pix_tri = np.full((size, size), -1, np.int64)
    pix_mesh = np.full((size, size), -1, np.int64)
    pix_bary = np.zeros((size, size, 3), np.float32)
    yy, xx = np.mgrid[0:size, 0:size]
    for mi, mesh in enumerate(meshes):
        pv = project(mesh["verts"], view, fov_deg, size)
        for ti, tri in enumerate(mesh["tris"]):
            p = pv[tri]
            minx = max(0, int(np.floor(p[:, 0].min())))
            maxx = min(size - 1, int(np.ceil(p[:, 0].max())))
            miny = max(0, int(np.floor(p[:, 1].min())))
            maxy = min(size - 1, int(np.ceil(p[:, 1].max())))
            if minx > maxx or miny > maxy:
                continue
            xs = xx[miny:maxy + 1, minx:maxx + 1] + 0.5
            ys = yy[miny:maxy + 1, minx:maxx + 1] + 0.5
            d = ((p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0])
                 + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1]))
            if abs(d) < 1e-12:
                continue
            w0 = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0])
                  + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
            w1 = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0])
                  + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            z = w0 * p[0, 2] + w1 * p[1, 2] + w2 * p[2, 2]
            region = depth[miny:maxy + 1, minx:maxx + 1]
            hit = inside & (z < region)
            region[hit] = z[hit]
            st = pix_tri[miny:maxy + 1, minx:maxx + 1]
            sm = pix_mesh[miny:maxy + 1, minx:maxx + 1]
            sb = pix_bary[miny:maxy + 1, minx:maxx + 1]
            st[hit] = ti
            sm[hit] = mi
            sb[hit] = np.stack([w0, w1, w2], -1)[hit]
    return {"depth": depth, "tri": pix_tri, "mesh": pix_mesh, "bary": pix_bary}


# ---------------------------------------------------------------- CF shader

def reflect(i: np.ndarray, n: np.ndarray) -> np.ndarray:
    return i - 2.0 * (i * n).sum(-1, keepdims=True) * n


def refract(i: np.ndarray, n: np.ndarray, eta: float) -> np.ndarray:
    cosi = -(i * n).sum(-1, keepdims=True)
    k = 1.0 - eta * eta * (1.0 - cosi * cosi)
    k = np.maximum(k, 0.0)
    return eta * i + (eta * cosi - np.sqrt(k)) * n


def rot_y(v: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    out = v.copy()
    out[:, 0] = c * v[:, 0] + s * v[:, 2]
    out[:, 2] = -s * v[:, 0] + c * v[:, 2]
    return out


def cf_cube_ray(view_incident: np.ndarray, normal: np.ndarray,
                params: dict) -> tuple[np.ndarray, str]:
    """Cubemap ray hypotheses for EnvCubeUsage=2 (transformed snell).

    INFERRED primary: refract(I, N, RefractionIndex) blended toward reflect
    by ReflectionIndex, then rotated by CubeMapTransformY about +Y.
    """
    i = view_incident
    r = reflect(i, normal)
    eta = params.get("refraction_index", 0.0)
    t = refract(i, normal, eta if eta > 0 else 1.0)
    mix = params.get("reflection_index", 0.0)
    ray = r * mix + t * (1.0 - mix)
    ray = ray / np.maximum(np.linalg.norm(ray, axis=-1, keepdims=True), 1e-9)
    ray = rot_y(ray, params.get("cubemap_transform_y", 0.0))
    return ray, "mix(reflect,refract,ReflectionIndex)->rotY(CubeMapTransformY)"


def tangent_frames(verts: np.ndarray, uvs: np.ndarray,
                   tris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-triangle tangent/bitangent from UV gradient (LHcoords-free)."""
    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    u0, u1, u2 = uvs[tris[:, 0]], uvs[tris[:, 1]], uvs[tris[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    d1, d2 = u1 - u0, u2 - u0
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    t = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]
    b = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
    t = t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    b = b / np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-12)
    return t, b


def shade(frame: dict, meshes: list[dict], maps: dict, params: dict,
          view: np.ndarray, light_dir: np.ndarray, size: int,
          eye: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Evaluate the recovered CF formula per pixel; also returns terms."""
    hit = frame["tri"] >= 0
    idx = np.where(hit)
    n_pix = len(idx[0])
    out = np.zeros((size, size, 3), np.float32)
    components: dict[str, np.ndarray] = {}
    if n_pix == 0:
        return out, components
    P = np.zeros((n_pix, 3), np.float32)
    N = np.zeros((n_pix, 3), np.float32)
    UV = np.zeros((n_pix, 2), np.float32)
    Ttri = np.zeros((n_pix, 3), np.float32)
    Btri = np.zeros((n_pix, 3), np.float32)
    hit_mesh = frame["mesh"][idx]
    hit_tri = frame["tri"][idx]
    hit_bary = frame["bary"][idx]
    for mi, mesh in enumerate(meshes):
        sel = hit_mesh == mi
        if not sel.any():
            continue
        t = hit_tri[sel]
        b = hit_bary[sel]
        tri = mesh["tris"][t]
        P[sel] = (mesh["verts"][tri] * b[:, :, None]).sum(1)
        UV[sel] = (mesh["uvs"][tri] * b[:, :, None]).sum(1)
        vn = vertex_normals(mesh["verts"], mesh["tris"])
        N[sel] = (vn[tri] * b[:, :, None]).sum(1)
        tang, bitan = tangent_frames(mesh["verts"], mesh["uvs"], mesh["tris"])
        Ttri[sel] = tang[t]
        Btri[sel] = bitan[t]
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)

    # tangent-space normal map -> world normal
    if params.get("normal_enabled") and maps.get("normal") is not None:
        nm = sample_bilinear(maps["normal"], UV) * 2.0 - 1.0
        N = (Ttri * nm[:, 0:1] + Btri * nm[:, 1:2] + N * nm[:, 2:3])
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)

    V = eye - P
    V = V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)
    L = np.asarray(light_dir, np.float32)
    L = L / np.linalg.norm(L)

    albedo = sample_bilinear(maps["diffuse"], UV)
    alpha = (sample_bilinear(maps["alpha"], UV)
             if maps.get("alpha") is not None
             else np.ones((n_pix, 3), np.float32))

    lambert = np.maximum((N * L).sum(-1, keepdims=True), 0.0)
    # INFERRED diffuse_lit: albedo * (ambient + LightBrightness*lambert + DiffuseBoost)
    diffuse_lit = albedo * (
        params.get("ambient_light_color", 0.0)
        + params.get("light_brightness", 1.0) * lambert
        + params.get("diffuse_boost", 0.0))

    # INFERRED spec term: Blinn pow(N.H, SpecularPower*0.25)
    H = (L + V) / np.maximum(np.linalg.norm(L + V, axis=1, keepdims=True), 1e-9)
    spec_exp = params.get("specular_power", 1.0) * 0.25
    spec_term = np.maximum((N * H).sum(-1, keepdims=True), 0.0) ** spec_exp
    spec = np.zeros((n_pix, 3), np.float32)
    if params.get("specular_enabled") and maps.get("specular") is not None:
        spec = (sample_bilinear(maps["specular"], UV)
                * spec_term * alpha[:, 1:2])

    cube = np.zeros((n_pix, 3), np.float32)
    if params.get("envcube_enabled") and maps.get("cubemap") is not None:
        ray, _ = cf_cube_ray(-V, N, params)
        cube = (cube_sample(maps["cubemap"], ray)
                * params.get("envcube_brightness", 1.0)
                * alpha[:, 2:3])

    out[idx[0], idx[1]] = diffuse_lit + spec + cube
    components["diffuse_lit"] = np.zeros((size, size, 3), np.float32)
    components["specular"] = np.zeros((size, size, 3), np.float32)
    components["cubemap"] = np.zeros((size, size, 3), np.float32)
    components["diffuse_lit"][idx[0], idx[1]] = diffuse_lit
    components["specular"][idx[0], idx[1]] = spec
    components["cubemap"][idx[0], idx[1]] = cube
    return out, components


def render(meshes: list[dict], maps: dict, params: dict, eye, target,
           light_dir, size: int = 512, fov_deg: float = 45.0,
           up=(0, 0, 1)) -> np.ndarray:
    img, _ = render_full(meshes, maps, params, eye, target, light_dir,
                         size, fov_deg, up)
    return img


def render_full(meshes: list[dict], maps: dict, params: dict, eye, target,
                light_dir, size: int = 512, fov_deg: float = 45.0,
                up=(0, 0, 1)) -> tuple[np.ndarray, dict]:
    eye = np.asarray(eye, np.float32)
    view = look_at(eye, np.asarray(target, np.float32), up)
    frame = rasterize(meshes, view, fov_deg, size)
    img, components = shade(frame, meshes, maps, params, view,
                            np.asarray(light_dir, np.float32), size, eye)
    return np.clip(img, 0.0, 1.0), components


def save_png(arr: np.ndarray, path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.uint8(np.round(np.clip(arr, 0, 1) * 255.0))).save(path)


def params_from_cfg_flat(flat: dict) -> dict:
    """Map raw CFG flat values to renderer params (no semantic change)."""
    g = lambda k, d=0.0: float(flat.get(k, d) or 0.0)
    return {
        "specular_enabled": g("SpecularMappingEnabled") != 0,
        "envcube_enabled": g("EnvCubeMappingEnabled") != 0,
        "normal_enabled": g("NormalMappingEnabled") != 0,
        "diffuse_enabled": g("DiffuseMappingEnabled", 1) != 0,
        "light_brightness": g("LightBrightness", 1.0),
        "envcube_brightness": g("EnvCubeMapBrightness", 1.0),
        "specular_power": g("SpecularPower", 1.0),
        "diffuse_boost": g("DiffuseBoost"),
        "ambient_light_color": g("AmbientLightColor"),
        "refraction_index": g("RefractionIndex"),
        "reflection_index": g("ReflectionIndex"),
        "env_cube_usage": int(g("EnvCubeUsage")),
        "cubemap_transform_y": g("CubeMapTransformY"),
    }
