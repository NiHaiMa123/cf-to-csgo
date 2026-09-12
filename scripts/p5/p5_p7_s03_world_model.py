"""P7-S03 — M4A1-雷神 world / dropped model from Bute QV LTB.

Replaces CS:GO M4A4 world and dropped models with the identity-core
QV-M4A1_S_Transformers mesh + QV DTX. Does not touch the P6 viewmodel,
P7-S01 sound, or the parked frozen addon.

QV is one piece (mag welded). Official mag bodygroups are blanked so a
vanilla magazine does not pop out of the CF gun.

Repro:
  python scripts/p5/p5_p7_s03_world_model.py
"""
from __future__ import annotations

import hashlib
import json
import lzma
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "material_recovery"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
import n05a_decoder_provenance_audit as n05a  # noqa: E402
from rez_verified_payload import read_verified_payload  # noqa: E402
from weapon_port.pipeline import mdl_header, smd_prefix  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / "work" / "p5_leishen" / "p7_s03"
STAGING = OUT / "addon"
PNG_DIR = OUT / "_png"
MESH_DIR = OUT / "mesh"
LOG_DIR = OUT / "logs"
SOURCE1 = OUT / "source1"
ISOLATED = OUT / "isolated_game" / "csgo"
VERIFIED_ROOT = OUT / "verified_root"
REF = OUT / "_ref"
IDENTITY = REPO / "work" / "p5_leishen" / "t04" / "identity_review.json"
GRAPH = REPO / "work" / "p5_leishen" / "t03" / "resource_graph.json"
CFREZ = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
STUDIOMDL = GAME / "bin" / "studiomdl.exe"
CROWBAR = REPO / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe"
ADDON_NAME = "p_cf_leishen_m4a4_p6"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
MIGI_ADDONS = GAME / "migi" / "csgo" / "addons"
PARK = GAME / "migi" / "csgo" / "_parked_addons"
MAT_REL = Path("materials/models/weapons/w_models/w_rif_m4a1")
MODEL_REL = Path("models/weapons")

EXPECTED_SHA = {
    "qv_ltb": "3e8479d64e751c1e0270c716e82f16030f6ceb4aaf187e344a15361f0d5ee0b2",
    "qv_dtx": "f883496782dfa41f1118b633ca5809b334114d3d1b1356229ba0bc5960477504",
}
WANTED_KEYS = {
    "qv_ltb": "MODELS/WEAPONS/QV-M4A1_S_TRANSFORMERS.LTB",
    "qv_dtx": "MODELTEXTURES/WEAPONS/QV-M4A1_S_TRANSFORMERS.DTX",
}
INDEX_RELS = (
    "rez2/RF016.REZ",
    "rez/RF016.REZ",
    "rez2/RF017.REZ",
    "rez/rf017.rez",
    "rez3/RF017.REZ",
)
OFFICIAL_FILES = (
    "models/weapons/w_rif_m4a1.mdl",
    "models/weapons/w_rif_m4a1.vvd",
    "models/weapons/w_rif_m4a1.dx90.vtx",
    "models/weapons/w_rif_m4a1.ani",
    "models/weapons/w_rif_m4a1_dropped.mdl",
    "models/weapons/w_rif_m4a1_dropped.vvd",
    "models/weapons/w_rif_m4a1_dropped.dx90.vtx",
    "models/weapons/w_rif_m4a1_dropped.phy",
)
VPK_WORLD = "models/weapons/w_rif_m4a1.mdl"
VPK_DROPPED = "models/weapons/w_rif_m4a1_dropped.mdl"

WORLD_VMT = '''"VertexLitGeneric"
{
	"$basetexture" "models/weapons/w_models/w_rif_m4a1/rif_m4a1"
	"$model" "1"
}
'''


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def logical_key(full_path: str) -> str:
    return full_path.replace("\\", "/").upper()


def maybe_lzma(data: bytes) -> tuple[bytes, bool]:
    if data[:1] != b"\x5d":
        return data, False
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE), True
    except lzma.LZMAError:
        return data, False


def resolve_cf_file(relative: str) -> Path | None:
    direct = CF / relative
    if direct.is_file():
        return direct
    needle = Path(relative.replace("\\", "/"))
    current = CF
    for part in needle.parts:
        if not current.is_dir():
            return None
        matches = [child for child in current.iterdir() if child.name.casefold() == part.casefold()]
        if len(matches) != 1:
            return None
        current = matches[0]
    return current if current.is_file() else None


def tree_hashes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows[path.relative_to(root).as_posix()] = sha256_file(path)
    return rows


def vec_add(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(a: tuple[float, ...], s: float) -> tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)


def vec_dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vec_len(a: tuple[float, ...]) -> float:
    return math.sqrt(vec_dot(a, a))


def vec_norm(a: tuple[float, ...]) -> tuple[float, float, float]:
    length = vec_len(a)
    return a if length == 0 else vec_scale(a, 1.0 / length)


def mat_vec(m: list[list[float]], p: tuple[float, ...]) -> tuple[float, float, float]:
    return (
        m[0][0] * p[0] + m[0][1] * p[1] + m[0][2] * p[2],
        m[1][0] * p[0] + m[1][1] * p[1] + m[1][2] * p[2],
        m[2][0] * p[0] + m[2][1] * p[1] + m[2][2] * p[2],
    )


def mat_det(m: list[list[float]]) -> float:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def aabb(points: list[tuple[float, float, float]]) -> dict[str, Any]:
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "size": [maxs[i] - mins[i] for i in range(3)],
        "center": [(mins[i] + maxs[i]) / 2.0 for i in range(3)],
        "count": len(points),
    }


def recover_payloads() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    wanted_by_key = {value: role for role, value in WANTED_KEYS.items()}
    found: dict[str, list[dict[str, Any]]] = {role: [] for role in WANTED_KEYS}
    scanned: list[str] = []
    for relative in INDEX_RELS:
        index_path = resolve_cf_file(relative)
        if index_path is None:
            continue
        scanned.append(str(index_path))
        for entry in extract_all.read_index_entries(str(index_path)):
            key = logical_key(str(entry.get("full_path") or ""))
            role = wanted_by_key.get(key)
            if role is None:
                continue
            found[role].append({"index_archive": str(index_path), "entry": entry, "logical_key": key})
    recovered: dict[str, dict[str, Any]] = {}
    for role, expected in EXPECTED_SHA.items():
        errors: list[str] = []
        matched = None
        for candidate in found[role]:
            try:
                data, provenance = read_verified_payload(candidate["index_archive"], candidate["entry"])
            except Exception as exc:
                errors.append(f"{candidate['index_archive']}: {exc}")
                continue
            digest = provenance["sha256"]
            if digest != expected:
                errors.append(f"{candidate['index_archive']} sha {digest} != {expected}")
                continue
            matched = {
                "role": role,
                "logical_key": candidate["logical_key"],
                "full_path": candidate["entry"]["full_path"],
                "raw": data,
                "sha256": digest,
                "size": len(data),
                "routing": provenance["routing"],
                "payload_file": provenance["payload_file"],
                "index_archive": provenance["index_archive"],
                "directory_md5": provenance["directory_md5"],
            }
            break
        if matched is None:
            raise RuntimeError(f"failed to recover {role}: {errors or found[role]}")
        recovered[role] = matched
    return recovered, {"scanned": scanned}


def decode_payload(role: str, row: dict[str, Any], dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = row["raw"]
    suffix = Path(row["full_path"]).suffix.upper()
    if suffix == ".LTB":
        body, lzma_used = maybe_lzma(data)
        dest.write_bytes(body)
        return {
            "ok": True,
            "path": rel(dest),
            "bytes": len(body),
            "lzma": lzma_used,
            "sha256_raw": row["sha256"],
            "sha256_body": sha256_bytes(body),
        }
    if suffix == ".DTX":
        decoded = n05a.decode_repo_pixels(data)
        if not decoded.get("ok"):
            raise RuntimeError(f"DTX decode failed for {role}: {decoded}")
        image = decoded["image"].convert("RGBA")
        image.save(dest)
        return {
            "ok": True,
            "path": rel(dest),
            "size": list(image.size),
            "mode": image.mode,
            "format": decoded.get("format"),
            "png_sha256": sha256_file(dest),
        }
    raise RuntimeError(f"unsupported suffix {suffix} for {role}")


def export_obj(ltb_rel: str, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(CFREZ),
            "--export-obj",
            "--raw-transform",
            "--root",
            str(VERIFIED_ROOT),
            "--model",
            ltb_rel,
            "--output",
            str(dest),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    (LOG_DIR / "cfrez_export.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "cfrez_export.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"CFRezManager OBJ export failed: {(proc.stderr or proc.stdout or '')[:800]}")
    return {"obj": rel(dest), "sha256": sha256_file(dest), "bytes": dest.stat().st_size}


def inspect_ltb(ltb_path: Path, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(CFREZ), "--inspect-ltb", "--input", str(ltb_path), "--output", str(dest)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    (LOG_DIR / "cfrez_inspect.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "cfrez_inspect.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"inspect-ltb failed: {(proc.stderr or proc.stdout or '')[:500]}")
    return json.loads(dest.read_text(encoding="utf-8"))


def parse_obj(path: Path) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, list[tuple[int, int, int]]]],
    dict[str, int],
]:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces: list[tuple[str, list[tuple[int, int, int]]]] = []
    triangles: dict[str, int] = {}
    group = "qv"
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "vt":
            uvs.append((float(parts[1]), float(parts[2])))
        elif parts[0] == "vn":
            normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "g":
            group = parts[1] if len(parts) > 1 else "qv"
        elif parts[0] == "f":
            refs: list[tuple[int, int, int]] = []
            for token in parts[1:]:
                fields = token.split("/")
                if len(fields) != 3 or not all(fields):
                    raise ValueError(f"need v/vt/vn faces, got: {raw}")
                refs.append(tuple(int(value) - 1 for value in fields))
            if len(refs) < 3:
                raise ValueError(f"need at least a triangle in {group}")
            for i in range(1, len(refs) - 1):
                tri = [refs[0], refs[i], refs[i + 1]]
                faces.append((group, tri))
                triangles[group] = triangles.get(group, 0) + 1
    if not faces:
        raise RuntimeError(f"no triangles in {path}")
    return vertices, uvs, normals, faces, triangles


def parse_smd_triangles(path: Path) -> tuple[list[str], list[tuple[int, tuple[float, ...]]]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    prefix = smd_prefix(path)
    verts: list[tuple[int, tuple[float, ...]]] = []
    in_tri = False
    for line in lines:
        if line.strip().lower() == "triangles":
            in_tri = True
            continue
        if not in_tri:
            continue
        if line.strip().lower() == "end":
            break
        parts = line.split()
        if parts and parts[0].lstrip("-").replace(".", "", 1).isdigit():
            bone = int(parts[0])
            nums = tuple(float(value) for value in parts[1:8])
            verts.append((bone, nums))
    return prefix, verts


def smd_nodes(path: Path) -> list[tuple[int, str, int]]:
    nodes: list[tuple[int, str, int]] = []
    in_nodes = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s == "nodes":
            in_nodes = True
            continue
        if s == "end" and in_nodes:
            break
        if in_nodes:
            match = re.match(r'(\d+)\s+"([^"]+)"\s+(-?\d+)', s)
            if match:
                nodes.append((int(match.group(1)), match.group(2), int(match.group(3))))
    return nodes


def orthonormal_frame(p0: tuple[float, ...], p1: tuple[float, ...], p2: tuple[float, ...]) -> list[list[float]]:
    x = vec_norm(vec_sub(p1, p0))
    z = vec_norm(vec_cross(x, vec_sub(p2, p0)))
    y = vec_cross(z, x)
    return [
        [x[0], y[0], z[0]],
        [x[1], y[1], z[1]],
        [x[2], y[2], z[2]],
    ]


def invert3(m: list[list[float]]) -> list[list[float]]:
    det = mat_det(m)
    if abs(det) < 1e-12:
        raise RuntimeError("singular frame")
    a, b, c = m[0][0], m[0][1], m[0][2]
    d, e, f = m[1][0], m[1][1], m[1][2]
    g, h, i = m[2][0], m[2][1], m[2][2]
    inv_det = 1.0 / det
    return [
        [(e * i - f * h) * inv_det, (c * h - b * i) * inv_det, (b * f - c * e) * inv_det],
        [(f * g - d * i) * inv_det, (a * i - c * g) * inv_det, (c * d - a * f) * inv_det],
        [(d * h - e * g) * inv_det, (b * g - a * h) * inv_det, (a * e - b * d) * inv_det],
    ]


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [
        [sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)]
        for r in range(3)
    ]


def rigid_from_triangles(
    src: list[tuple[float, float, float]],
    dst: list[tuple[float, float, float]],
) -> tuple[list[list[float]], tuple[float, float, float], float]:
    src_frame = orthonormal_frame(src[0], src[1], src[2])
    dst_frame = orthonormal_frame(dst[0], dst[1], dst[2])
    rotation = matmul(dst_frame, invert3(src_frame))
    translation = vec_sub(dst[0], mat_vec(rotation, src[0]))
    errors = [
        vec_len(vec_sub(vec_add(mat_vec(rotation, s), translation), d))
        for s, d in zip(src, dst, strict=True)
    ]
    rms = math.sqrt(sum(e * e for e in errors) / len(errors))
    return rotation, translation, rms


def mirror_x_mesh(
    vertices: list[tuple[float, float, float]],
    normals: list[tuple[float, float, float]],
    faces: list[tuple[str, list[tuple[int, int, int]]]],
) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, list[tuple[int, int, int]]]],
]:
    vertices = [(-x, y, z) for x, y, z in vertices]
    normals = [(-nx, ny, nz) for nx, ny, nz in normals]
    faces = [(group, [refs[0], refs[2], refs[1]]) for group, refs in faces]
    return vertices, normals, faces


def apply_linear(
    vertices: list[tuple[float, float, float]],
    normals: list[tuple[float, float, float]],
    matrix: list[list[float]],
    translation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    reverse_faces: bool = False,
    faces: list[tuple[str, list[tuple[int, int, int]]]] | None = None,
) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, list[tuple[int, int, int]]]] | None,
]:
    vertices = [vec_add(mat_vec(matrix, p), translation) for p in vertices]
    rotated = [mat_vec(matrix, n) for n in normals]
    normals = [vec_norm(n) for n in rotated]
    if faces is not None and reverse_faces:
        faces = [(group, [refs[0], refs[2], refs[1]]) for group, refs in faces]
    return vertices, normals, faces


def axis_permutation(src_size: list[float], dst_size: list[float]) -> list[int]:
    src_order = sorted(range(3), key=lambda i: src_size[i], reverse=True)
    dst_order = sorted(range(3), key=lambda i: dst_size[i], reverse=True)
    perm = [0, 0, 0]
    for rank in range(3):
        perm[dst_order[rank]] = src_order[rank]
    return perm


def thinner_end_is_max(points: list[tuple[float, float, float]], axis: int) -> bool:
    coords = [p[axis] for p in points]
    mid = (min(coords) + max(coords)) / 2.0
    low = [p for p in points if p[axis] <= mid]
    high = [p for p in points if p[axis] > mid]
    other = [i for i in range(3) if i != axis]

    def spread(group: list[tuple[float, float, float]]) -> float:
        if not group:
            return 0.0
        total = 0.0
        for i in other:
            vals = [p[i] for p in group]
            total += max(vals) - min(vals)
        return total

    return spread(high) <= spread(low)


def align_qv_to_dropped(
    vertices: list[tuple[float, float, float]],
    normals: list[tuple[float, float, float]],
    faces: list[tuple[str, list[tuple[int, int, int]]]],
    target: dict[str, Any],
) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, list[tuple[int, int, int]]]],
    dict[str, Any],
]:
    vertices, normals, faces = mirror_x_mesh(vertices, normals, faces)
    src = aabb(vertices)
    perm = axis_permutation(src["size"], target["size"])
    matrix = [[0.0, 0.0, 0.0] for _ in range(3)]
    for dst_axis, src_axis in enumerate(perm):
        matrix[dst_axis][src_axis] = 1.0
    vertices, normals, faces = apply_linear(vertices, normals, matrix, reverse_faces=mat_det(matrix) < 0, faces=faces)
    if not thinner_end_is_max(vertices, 0):
        flip = [[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]]
        vertices, normals, faces = apply_linear(vertices, normals, flip, faces=faces)
    after = aabb(vertices)
    if after["center"][2] < target["center"][2] and after["min"][2] < target["min"][2] - 1.0:
        flip_z = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]
        vertices, normals, faces = apply_linear(vertices, normals, flip_z, faces=faces)
        after = aabb(vertices)
    scale = target["size"][0] / after["size"][0] if after["size"][0] else 1.0
    scale_m = [[scale, 0.0, 0.0], [0.0, scale, 0.0], [0.0, 0.0, scale]]
    vertices, normals, faces = apply_linear(vertices, normals, scale_m, faces=faces)
    after = aabb(vertices)
    translation = (
        target["center"][0] - after["center"][0],
        target["center"][1] - after["center"][1],
        target["center"][2] - after["center"][2],
    )
    vertices = [vec_add(p, translation) for p in vertices]
    final = aabb(vertices)
    meta = {
        "mirror_x": True,
        "axis_permutation": perm,
        "uniform_scale": scale,
        "translation": list(translation),
        "raw_aabb": src,
        "aligned_aabb": final,
        "target_aabb": target,
    }
    if not 30.0 <= final["size"][0] <= 42.0:
        raise RuntimeError(f"aligned QV length {final['size'][0]:.3f} is not a rifle")
    if not 1.2 <= final["size"][1] <= 8.0:
        raise RuntimeError(f"aligned QV thickness {final['size'][1]:.3f} is not world-thin")
    if not 6.0 <= final["size"][2] <= 16.0:
        raise RuntimeError(f"aligned QV height {final['size'][2]:.3f} is not a rifle")
    return vertices, normals, faces, meta


def write_smd(
    prefix_lines: list[str],
    dest: Path,
    vertices: list[tuple[float, float, float]],
    uvs: list[tuple[float, float]],
    normals: list[tuple[float, float, float]],
    faces: list[tuple[str, list[tuple[int, int, int]]]],
    bone_index: int,
    material: str = "rif_m4a1",
) -> dict[str, Any]:
    lines = list(prefix_lines)
    if not lines or lines[-1].strip().lower() != "triangles":
        lines.append("triangles")
    for _group, refs in faces:
        lines.append(material)
        for vi, ti, ni in refs:
            pos = vertices[vi]
            norm = normals[ni]
            uv = uvs[ti]
            lines.append(
                f"  {bone_index} "
                + " ".join(f"{value:.6f}" for value in (*pos, *norm, uv[0], uv[1]))
                + f" 1 {bone_index} 1.000000"
            )
    lines.append("end")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"smd": rel(dest), "sha256": sha256_file(dest), "triangles": len(faces), "bone": bone_index}


def blank_bodygroup(qc_text: str, name: str) -> str:
    pattern = rf'(\$bodygroup\s+"{re.escape(name)}"\s*\{{)(.*?)(\}})'

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}\n\tblank\n{match.group(3)}'

    updated, count = re.subn(pattern, repl, qc_text, count=1, flags=re.I | re.S)
    if count != 1:
        raise RuntimeError(f"failed to blank bodygroup {name}")
    return updated


def vtfcmd(png: Path, dest: Path, fmt: str) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(dest.parent), "-format", fmt, "-version", "7.4"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    generated = dest.parent / f"{png.stem}.vtf"
    if proc.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed {png}: {proc.stderr or proc.stdout}")
    if generated != dest:
        if dest.exists():
            dest.unlink()
        generated.replace(dest)
    return {
        "png": rel(png),
        "png_sha256": sha256_file(png),
        "vtf": rel(dest),
        "vtf_sha256": sha256_file(dest),
        "format": fmt,
        "vtf_bytes": dest.stat().st_size,
    }


def extract_official() -> dict[str, Any]:
    import vpk  # type: ignore

    pak = vpk.open(str(GAME / "csgo" / "pak01_dir.vpk"))
    source_dir = REF / "source_vpk"
    rows = []
    for relative in OFFICIAL_FILES:
        data = pak.get_file(relative).read()
        dest = source_dir / Path(relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        rows.append({"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)})
    for name, relative in (("w_rif_m4a1", VPK_WORLD), ("w_rif_m4a1_dropped", VPK_DROPPED)):
        mdl = source_dir / Path(relative)
        dest = REF / "decompiled" / name
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [str(CROWBAR), str(mdl), str(dest)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        (LOG_DIR / f"crowbar_{name}.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
        (LOG_DIR / f"crowbar_{name}.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"Crowbar failed {name}: {(proc.stderr or proc.stdout or '')[:500]}")
    return {"files": rows}


def run_studiomdl(qc_path: Path, cwd: Path, expected_mdl: Path, log_stem: str) -> dict[str, Any]:
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(qc_path)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    (LOG_DIR / f"{log_stem}.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / f"{log_stem}.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not expected_mdl.is_file():
        raise RuntimeError(
            f"studiomdl {log_stem} failed ({proc.returncode}): {(proc.stderr or proc.stdout or '')[-1500:]}"
        )
    return {"mdl": rel(expected_mdl), "exit_code": proc.returncode, "sha256": sha256_file(expected_mdl)}


def frozen_status() -> dict[str, Any]:
    frozen = MIGI_ADDONS / FROZEN_NAME
    parked = PARK / FROZEN_NAME
    return {
        "frozen_in_addons": frozen.exists(),
        "frozen_parked": parked.exists(),
        "frozen_modified": False,
        "parked_dst": str(parked),
    }


def deploy_world(staging_hashes: dict[str, str], view_before: dict[str, str]) -> dict[str, Any]:
    target = MIGI_ADDONS / ADDON_NAME
    if not target.exists():
        raise RuntimeError(f"live addon missing: {target}")
    for relative, digest in staging_hashes.items():
        src = STAGING / relative
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256_file(dst) != digest:
            raise RuntimeError(f"deploy hash mismatch {relative}")
    view_after = {}
    for name in view_before:
        path = target / "models" / "weapons" / name
        if not path.is_file():
            raise RuntimeError(f"viewmodel missing after world deploy: {name}")
        view_after[name] = sha256_file(path)
        if view_after[name] != view_before[name]:
            raise RuntimeError(f"viewmodel {name} changed during world deploy")
    return {"target": str(target), "action": "added_world_files", "viewmodel_unchanged": True}


def main() -> int:
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    if not identity.get("identity_confirmed"):
        raise RuntimeError("P5-T04 is not IDENTITY_CONFIRMED")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    if OUT.exists():
        for child in OUT.iterdir():
            if child.name == "_measure_smd.py":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    for path in (OUT, STAGING, PNG_DIR, MESH_DIR, LOG_DIR, SOURCE1, ISOLATED, VERIFIED_ROOT, REF):
        path.mkdir(parents=True, exist_ok=True)

    official = extract_official()
    recovered, scan_meta = recover_payloads()
    ltb_rel = "Models/WEAPONS/QV-M4A1_S_Transformers.LTB"
    ltb_path = VERIFIED_ROOT / Path(ltb_rel)
    decoded = {
        "qv_ltb": decode_payload("qv_ltb", recovered["qv_ltb"], ltb_path),
        "qv_dtx": decode_payload("qv_dtx", recovered["qv_dtx"], PNG_DIR / "qv_diffuse.png"),
    }
    inspect: dict[str, Any] = {"status": "skipped_nan_json"}
    try:
        inspect = inspect_ltb(ltb_path, OUT / "qv_inspect.json")
    except Exception as exc:
        inspect = {"status": "failed", "error": str(exc)[:400]}
        (LOG_DIR / "cfrez_inspect.skip.txt").write_text(str(exc), encoding="utf-8")
    export_info = export_obj(ltb_rel.replace("\\", "/"), MESH_DIR / "QV-M4A1_S_Transformers_raw.obj")
    vertices, uvs, normals, faces, triangles = parse_obj(MESH_DIR / "QV-M4A1_S_Transformers_raw.obj")

    dropped_smd = REF / "decompiled" / "w_rif_m4a1_dropped" / "w_rif_m4a1.smd"
    held_smd = REF / "decompiled" / "w_rif_m4a1" / "w_rif_m4a1.smd"
    dropped_prefix, dropped_verts = parse_smd_triangles(dropped_smd)
    held_prefix, held_verts = parse_smd_triangles(held_smd)
    dropped_pts = [(v[1][0], v[1][1], v[1][2]) for v in dropped_verts]
    held_pts = [(v[1][0], v[1][1], v[1][2]) for v in held_verts]
    if len(dropped_pts) != len(held_pts):
        raise RuntimeError(f"official dropped/held vert count mismatch {len(dropped_pts)} vs {len(held_pts)}")
    dropped_aabb = aabb(dropped_pts)
    rotation, translation, rms = rigid_from_triangles(dropped_pts[:3], held_pts[:3])
    sample = list(range(0, len(dropped_pts), max(1, len(dropped_pts) // 200)))
    sample_rms = math.sqrt(
        sum(
            vec_len(vec_sub(vec_add(mat_vec(rotation, dropped_pts[i]), translation), held_pts[i])) ** 2
            for i in sample
        )
        / len(sample)
    )
    if sample_rms > 0.75:
        raise RuntimeError(f"dropped→held rigid residual {sample_rms:.3f} is too large")

    aligned_v, aligned_n, aligned_f, align_meta = align_qv_to_dropped(vertices, normals, faces, dropped_aabb)
    (MESH_DIR / "QV_aligned_dropped.obj").write_text(
        "\n".join(["o qv"] + [f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in aligned_v]) + "\n",
        encoding="utf-8",
    )

    dropped_nodes = smd_nodes(dropped_smd)
    held_nodes = smd_nodes(held_smd)
    dropped_bone = next(i for i, name, _ in dropped_nodes if name == "weapon_hand_R")
    held_bone = next(i for i, name, _ in held_nodes if name == "weapon_hand_R")

    held_v = [vec_add(mat_vec(rotation, p), translation) for p in aligned_v]
    held_n = [vec_norm(mat_vec(rotation, n)) for n in aligned_n]

    dropped_dir = SOURCE1 / "dropped"
    held_dir = SOURCE1 / "held"
    shutil.copytree(REF / "decompiled" / "w_rif_m4a1_dropped", dropped_dir, dirs_exist_ok=True)
    shutil.copytree(REF / "decompiled" / "w_rif_m4a1", held_dir, dirs_exist_ok=True)
    dropped_smd_info = write_smd(dropped_prefix, dropped_dir / "w_rif_m4a1.smd", aligned_v, uvs, aligned_n, aligned_f, dropped_bone)
    held_smd_info = write_smd(held_prefix, held_dir / "w_rif_m4a1.smd", held_v, uvs, held_n, aligned_f, held_bone)

    dropped_qc = dropped_dir / "w_rif_m4a1_dropped.qc"
    held_qc = held_dir / "w_rif_m4a1.qc"
    dropped_qc.write_text(blank_bodygroup(dropped_qc.read_text(encoding="utf-8", errors="replace"), "mag"), encoding="utf-8")
    held_qc.write_text(blank_bodygroup(held_qc.read_text(encoding="utf-8", errors="replace"), "magazine"), encoding="utf-8")

    shutil.copy2(GAME / "csgo" / "gameinfo.txt", ISOLATED / "gameinfo.txt")
    rgb = PNG_DIR / "qv_diffuse_rgb.png"
    Image.open(PNG_DIR / "qv_diffuse.png").convert("RGB").save(rgb)
    mat_dir = STAGING / MAT_REL
    vtf = vtfcmd(rgb, mat_dir / "rif_m4a1.vtf", "dxt1")
    vmt_path = mat_dir / "rif_m4a1.vmt"
    vmt_path.write_text(WORLD_VMT.replace("\n", "\r\n"), encoding="ascii")
    isolated_mat = ISOLATED / MAT_REL
    isolated_mat.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mat_dir / "rif_m4a1.vtf", isolated_mat / "rif_m4a1.vtf")
    shutil.copy2(vmt_path, isolated_mat / "rif_m4a1.vmt")

    dropped_compile = run_studiomdl(
        dropped_qc, dropped_dir, ISOLATED / "models" / "weapons" / "w_rif_m4a1_dropped.mdl", "studiomdl_dropped"
    )
    held_compile = run_studiomdl(
        held_qc, held_dir, ISOLATED / "models" / "weapons" / "w_rif_m4a1.mdl", "studiomdl_held"
    )
    dropped_header = mdl_header(ISOLATED / "models" / "weapons" / "w_rif_m4a1_dropped.mdl")
    held_header = mdl_header(ISOLATED / "models" / "weapons" / "w_rif_m4a1.mdl")
    if dropped_header["internal_name"].replace("\\", "/") != "weapons/w_rif_m4a1_dropped.mdl":
        raise RuntimeError(dropped_header["internal_name"])
    if held_header["internal_name"].replace("\\", "/") != "weapons/w_rif_m4a1.mdl":
        raise RuntimeError(held_header["internal_name"])

    models_dir = STAGING / MODEL_REL
    models_dir.mkdir(parents=True, exist_ok=True)
    compiled_models: dict[str, str] = {}
    for path in (ISOLATED / "models" / "weapons").glob("w_rif_m4a1*"):
        dest = models_dir / path.name
        shutil.copy2(path, dest)
        compiled_models[path.name] = sha256_file(dest)

    live = MIGI_ADDONS / ADDON_NAME
    view_before = {
        path.name: sha256_file(path)
        for path in (live / "models" / "weapons").glob("v_rif_m4a1.*")
    }
    if not view_before:
        raise RuntimeError("live P6 viewmodel files are missing")
    frozen = frozen_status()
    if frozen["frozen_in_addons"]:
        raise RuntimeError("frozen addon is still in MIGI addons")
    staging_hashes = tree_hashes(STAGING)
    deploy = deploy_world(staging_hashes, view_before)

    recovered_public = {
        role: {
            "full_path": row["full_path"],
            "sha256": row["sha256"],
            "size": row["size"],
            "routing": row["routing"],
            "index_archive": row["index_archive"],
            "payload_file": row["payload_file"],
            "directory_md5": row["directory_md5"],
        }
        for role, row in recovered.items()
    }
    qv_node = next((node for node in graph.get("nodes", []) if node.get("id") == "qv_ltb"), {})
    report = {
        "schema": "cf2.p7.world-model.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P7-S03",
        "result": "P7_WORLD_MODEL_DEPLOYED",
        "identity_confirmed": True,
        "final_target_identity": True,
        "final_cf_material": False,
        "p4_m01": "INCOMPLETE",
        "addon_name": ADDON_NAME,
        "source": {
            "qv_ltb": qv_node.get("path"),
            "qv_ltb_sha256": EXPECTED_SHA["qv_ltb"],
            "qv_dtx_sha256": EXPECTED_SHA["qv_dtx"],
            "bute": "ModelFileName / SkinFileName",
        },
        "official": official,
        "recovered": recovered_public,
        "decoded": decoded,
        "scan": scan_meta,
        "export": export_info,
        "inspect_mesh_count": inspect.get("Meshes") or inspect.get("meshes") or inspect.get("mesh_count"),
        "triangles": triangles,
        "align": align_meta,
        "dropped_to_held": {
            "rms_first_triangle": rms,
            "rms_sample": sample_rms,
            "held_bone": held_bone,
            "dropped_bone": dropped_bone,
        },
        "smd": {"dropped": dropped_smd_info, "held": held_smd_info},
        "compile": {"dropped": dropped_compile, "held": held_compile},
        "mdl_header": {"dropped": dropped_header, "held": held_header},
        "compiled_models": compiled_models,
        "vtf": vtf,
        "vmt_sha256": sha256_file(vmt_path),
        "staging_hashes": staging_hashes,
        "park_frozen": frozen,
        "deploy": {k: v for k, v in deploy.items()},
        "viewmodel_hashes_before": view_before,
        "notes": [
            "World/dropped mesh is Bute QV-M4A1_S_Transformers, not PV and not BornBeast.",
            "QV is one piece; official mag bodygroups were blanked.",
            "Viewmodel v_rif_m4a1 files were not rewritten.",
            "P7-S01 sound was not rewritten.",
            "Frozen addon was not modified.",
            "Not a P4-M01 PASS. Lighting deferred. CF original animation still open.",
        ],
    }
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "mapping.json").write_text(
        json.dumps(
            {
                "addon_name": ADDON_NAME,
                "result": report["result"],
                "triangles": triangles,
                "align": align_meta,
                "compiled_models": compiled_models,
                "vtf": {"vtf": vtf["vtf"], "vtf_sha256": vtf["vtf_sha256"]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# P7-S03 — World / dropped model",
                "",
                "Result: **P7_WORLD_MODEL_DEPLOYED**. Bute `QV-M4A1_S_Transformers` is compiled onto CS:GO M4A4 `w_rif_m4a1` and `w_rif_m4a1_dropped`.",
                "",
                f"Addon: `{ADDON_NAME}` (world files added; viewmodel untouched)",
                f"Dropped internal name `{dropped_header['internal_name']}`, bones `{dropped_header['bone_count']}`.",
                f"Held internal name `{held_header['internal_name']}`, bones `{held_header['bone_count']}`.",
                "",
                "QV is one piece; official mag bodygroups are blank. Skin is QV DTX only (no PV normal/envmap, UVs are not assumed shared).",
                "",
                "P7-S02 inspect remains CS lookat. Finger clipping during F is noted, not fixed. Frozen / P7-S01 sound were not modified.",
                "",
                "Not a P4-M01 PASS. Not CF original animation.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "result": report["result"],
                "addon": ADDON_NAME,
                "dropped": dropped_header["internal_name"],
                "held": held_header["internal_name"],
                "triangles": sum(triangles.values()),
                "groups": sorted(triangles),
                "align_size": align_meta["aligned_aabb"]["size"],
                "out": rel(OUT),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
